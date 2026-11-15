"""Deterministic offline matchmaking, scoped to region and queue order."""

import csv
import itertools
import math
from collections import defaultdict
from statistics import mean

FIELDS = ["player_id", "skill_rating", "wait_seconds", "region"]


def load_players(path):
    """Read a strict four-column CSV and attribute errors to physical line numbers."""
    players = []
    seen = set()
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.reader(handle, strict=True)
        try:
            if next(reader, None) != FIELDS:
                raise ValueError("expected CSV header: " + ",".join(FIELDS))
            for row in reader:
                if not row:
                    continue
                line = reader.line_num
                try:
                    if len(row) != len(FIELDS):
                        raise ValueError("expected exactly four columns")
                    player_id, raw_skill, raw_wait, region = row
                    player_id, region = player_id.strip(), region.strip()
                    skill, wait = float(raw_skill), float(raw_wait)
                    if not player_id or not region:
                        raise ValueError("player ID and region must not be empty")
                    if player_id in seen:
                        raise ValueError("duplicate player ID")
                    if not all(math.isfinite(v) and v >= 0 for v in (skill, wait)):
                        raise ValueError("skill and wait must be finite and nonnegative")
                except (ValueError, TypeError, OverflowError) as exc:
                    raise ValueError(f"{path}:{line}: {exc}") from exc
                seen.add(player_id)
                players.append({
                    "player_id": player_id, "region": region,
                    "skill_rating": skill, "wait_seconds": wait,
                })
        except csv.Error as exc:
            raise ValueError(f"{path}:{reader.line_num}: malformed CSV: {exc}") from exc
    if not players:
        raise ValueError("no players")
    return players


def _checked_players(players):
    """Validate direct Python API input as carefully as CSV input."""
    if not players:
        raise ValueError("no players")
    normalized = []
    seen = set()
    for index, player in enumerate(players, 1):
        try:
            player_id, region = player["player_id"], player["region"]
            raw_skill, raw_wait = player["skill_rating"], player["wait_seconds"]
            if not isinstance(player_id, str) or not isinstance(region, str):
                raise ValueError("player ID and region must be strings")
            player_id, region = player_id.strip(), region.strip()
            if not player_id or not region:
                raise ValueError("player ID and region must not be empty")
            if player_id in seen:
                raise ValueError("duplicate player ID")
            if any(isinstance(value, bool) or not isinstance(value, (int, float))
                   for value in (raw_skill, raw_wait)):
                raise ValueError("skill and wait must be numeric")
            skill, wait = float(raw_skill), float(raw_wait)
            if not all(math.isfinite(v) and v >= 0 for v in (skill, wait)):
                raise ValueError("skill and wait must be finite and nonnegative")
        except (KeyError, TypeError, OverflowError, ValueError) as exc:
            raise ValueError(f"player {index}: {exc}") from exc
        seen.add(player_id)
        normalized.append({
            "player_id": player_id, "region": region,
            "skill_rating": skill, "wait_seconds": wait,
        })
    return normalized


def _skill_total(group):
    try:
        result = math.fsum(p["skill_rating"] for p in group)
    except OverflowError as exc:
        raise ValueError("team skill total exceeds finite numeric range") from exc
    if not math.isfinite(result):
        raise ValueError("team skill total exceeds finite numeric range")
    return result


def balance(group, team_size):
    """Enumerate distinct partitions; first player stays in A to remove mirrors."""
    if not isinstance(team_size, int) or isinstance(team_size, bool) or not 1 <= team_size <= 5:
        raise ValueError("team size must be an integer between 1 and 5")
    if len(group) != 2 * team_size:
        raise ValueError("group must contain exactly two full teams")
    best = None
    for subset in itertools.combinations(range(1, len(group)), team_size - 1):
        a_indices = (0,) + subset
        chosen = set(a_indices)
        team_a = [group[i] for i in a_indices]
        team_b = [group[i] for i in range(len(group)) if i not in chosen]
        a_skill = _skill_total(team_a)
        b_skill = _skill_total(team_b)
        gap = abs(a_skill - b_skill)
        if not math.isfinite(gap):
            raise ValueError("skill gap exceeds finite numeric range")
        # Compare actual gaps; rounding before ranking can prefer an inferior split.
        key = (gap, tuple(sorted(p["player_id"] for p in team_a)))
        if best is None or key < best[0]:
            best = (key, team_a, team_b, a_skill, b_skill, gap)
    return best[1:]


def simulate(players, team_size=2):
    if not isinstance(team_size, int) or isinstance(team_size, bool) or not 1 <= team_size <= 5:
        raise ValueError("team size must be an integer between 1 and 5")
    validated = _checked_players(players)
    grouped = defaultdict(list)
    for player in validated:
        grouped[player["region"]].append(player)

    matches = []
    match_size = 2 * team_size
    for region in sorted(grouped):
        pool = sorted(grouped[region], key=lambda player: (-player["wait_seconds"], player["player_id"]))
        if len(pool) % match_size:
            raise ValueError(f"region {region!r}: player count must be multiple of {match_size}")
        for offset in range(0, len(pool), match_size):
            group = pool[offset:offset + match_size]
            team_a, team_b, a_skill, b_skill, gap = balance(group, team_size)
            try:
                mean_wait = mean(p["wait_seconds"] for p in group)
            except OverflowError as exc:
                raise ValueError("wait-time mean exceeds finite numeric range") from exc
            if not math.isfinite(mean_wait):
                raise ValueError("wait-time mean exceeds finite numeric range")
            matches.append({
                "region": region,
                "team_a": sorted(p["player_id"] for p in team_a),
                "team_b": sorted(p["player_id"] for p in team_b),
                "team_a_skill": a_skill,
                "team_b_skill": b_skill,
                "skill_gap": gap,
                "mean_wait_seconds": mean_wait,
                "max_wait_seconds": max(p["wait_seconds"] for p in group),
            })
    try:
        mean_gap = mean(m["skill_gap"] for m in matches)
    except OverflowError as exc:
        raise ValueError("mean skill gap exceeds finite numeric range") from exc
    if not math.isfinite(mean_gap):
        raise ValueError("mean skill gap exceeds finite numeric range")
    return {
        "team_size": team_size, "match_count": len(matches),
        "mean_skill_gap": mean_gap, "matches": matches,
        "limitations": "Synthetic offline heuristic; not a real matchmaking system.",
    }
