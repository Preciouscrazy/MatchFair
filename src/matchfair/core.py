"""Deterministic, region-scoped matchmaking simulation."""
import csv
import itertools
import math
from collections import defaultdict
from statistics import mean

FIELDS = {"player_id", "skill_rating", "wait_seconds", "region"}

def load_players(path):
    players = []
    seen = set()
    with open(path, encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or not FIELDS.issubset(reader.fieldnames):
            raise ValueError("missing required CSV columns")
        for line, row in enumerate(reader, 2):
            try:
                player_id = row["player_id"].strip()
                region = row["region"].strip()
                skill = float(row["skill_rating"])
                wait = float(row["wait_seconds"])
                if not player_id or not region or player_id in seen:
                    raise ValueError("empty region/ID or duplicate player ID")
                if not all(math.isfinite(x) and x >= 0 for x in (skill, wait)):
                    raise ValueError("skill and wait must be finite and nonnegative")
            except (ValueError, TypeError, AttributeError, KeyError) as exc:
                raise ValueError(f"{path}:{line}: {exc}") from exc
            seen.add(player_id)
            players.append({"player_id": player_id, "region": region,
                            "skill_rating": skill, "wait_seconds": wait})
    if not players:
        raise ValueError("no players")
    return players

def balance(group, team_size):
    """Find minimum-skill-gap partition; force first player into A to avoid mirror duplicates."""
    indices = range(1, len(group))
    total = sum(p["skill_rating"] for p in group)
    best = None
    for subset in itertools.combinations(indices, team_size - 1):
        a_idx = (0,) + subset
        a_ids = set(a_idx)
        team_a = [group[i] for i in a_idx]
        team_b = [group[i] for i in range(len(group)) if i not in a_ids]
        a_skill = sum(p["skill_rating"] for p in team_a)
        gap = abs(2 * a_skill - total)
        key = (round(gap, 9), tuple(sorted(p["player_id"] for p in team_a)))
        if best is None or key < best[0]:
            best = (key, team_a, team_b, gap)
    return best[1:]

def simulate(players, team_size=2):
    if not isinstance(team_size, int) or not 1 <= team_size <= 5:
        raise ValueError("team size must be an integer between 1 and 5")
    if not players:
        raise ValueError("no players")
    if len({p["player_id"] for p in players}) != len(players):
        raise ValueError("duplicate player IDs")
    grouped = defaultdict(list)
    for p in players:
        grouped[p["region"]].append(p)
    matches = []
    size = 2 * team_size
    for region in sorted(grouped):
        pool = sorted(grouped[region], key=lambda p: (-p["wait_seconds"], p["player_id"]))
        if len(pool) % size:
            raise ValueError(f"region {region!r}: player count must be multiple of {size}")
        for offset in range(0, len(pool), size):
            group = pool[offset:offset + size]
            team_a, team_b, gap = balance(group, team_size)
            matches.append({
                "region": region,
                "team_a": sorted(p["player_id"] for p in team_a),
                "team_b": sorted(p["player_id"] for p in team_b),
                "team_a_skill": sum(p["skill_rating"] for p in team_a),
                "team_b_skill": sum(p["skill_rating"] for p in team_b),
                "skill_gap": gap,
                "mean_wait_seconds": mean(p["wait_seconds"] for p in group),
                "max_wait_seconds": max(p["wait_seconds"] for p in group),
            })
    return {
        "team_size": team_size, "match_count": len(matches),
        "mean_skill_gap": mean(m["skill_gap"] for m in matches),
        "matches": matches,
        "limitations": "Synthetic offline heuristic; not a real matchmaking system.",
    }
