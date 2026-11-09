# MatchFair

**Offline matchmaking fairness laboratory** for studying skill balance and queue-wait tradeoffs in simulated multiplayer matches.

MatchFair is an independent educational project, not a Riot Games service or integration. It reads synthetic player data, creates two balanced teams using a deterministic heuristic, and reports skill gaps and waiting-time summaries. It does not use Riot APIs or player accounts.

## 60-second walkthrough

The [sample report](evidence/sample-match-report.json) shows two 2v2 matches from [eight fictional players](examples/players.csv). Each region’s team totals tie. Five unit tests passed in a local run, covering team balance, repeatability, invalid sizes, incomplete pools, and the sample CSV.

### Same pool, different team assignments

The baseline sorts by longest wait within each region, breaking ties by ID, then alternates players between teams. MatchFair uses the same four players per match and searches for the smallest absolute skill-total gap.

| Region | Alternating baseline A / B | Baseline gap | MatchFair A / B | MatchFair gap |
|---|---|---:|---|---:|
| EU | eu-01 + eu-03 (1820) / eu-02 + eu-04 (1860) | 40 | eu-01 + eu-02 (1840) / eu-03 + eu-04 (1840) | 0 |
| NA | na-01 + na-03 (2010) / na-02 + na-04 (2030) | 20 | na-01 + na-02 (2020) / na-03 + na-04 (2020) | 0 |

The mean gap moves from 30 to 0 rating points. The player pools and their wait summaries stay the same. MatchFair fixes the first player on team A to avoid evaluating mirror assignments, then uses player IDs to break ties reproducibly.

### Where the design can struggle

In the [queue-order example](examples/queue_tradeoff.csv), the longest-waiting four players have ratings 100, 100, 100, and 0. The next four have ratings 0, 0, 0, and 100. MatchFair preserves those wait-ordered groups and returns a [100-point gap in each match](evidence/queue-tradeoff-report.json). Swapping p03 (60 seconds waited) with p05 (40 seconds waited) would let both matches reach a zero gap, while admitting a shorter-waiting player to the first group ahead of a longer-waiting one. The simulator optimizes teams within a selected group. It does not simulate arrivals or future queue delays.

## Quick start

Requires Python 3.10+; runtime uses the standard library only.

```bash
python -m pip install -e .
python -m matchfair --input examples/players.csv --output match-report.json
python -m unittest discover -s tests -v
```

Input columns: `player_id,skill_rating,wait_seconds,region`. By default, teams have 2 players each (`--team-size 2`). Each regional pool must be a multiple of `2 * team_size`. A match is formed only among players in the same region.

## Algorithm

1. Validate IDs and nonnegative finite metrics.
2. Group by region; order players by wait time (descending), then ID.
3. Take consecutive groups of `2 * team_size`.
4. Enumerate team assignments and minimize absolute team skill-total difference.
5. Break ties deterministically using player IDs.

This exhaustive partitioning is suitable for small teams only (team size <= 5). It is not a production matchmaking algorithm; it does not optimize role fit, latency, parties, uncertainty, or outcomes.

## Metrics

Per match: team skill totals, absolute difference, mean wait seconds, maximum wait seconds. Summary: match count and mean skill difference. Skill rating is an illustrative synthetic input, not an official game rank.

## Ethics and limitations

No real player identities or live game integrations. Fairness is multidimensional: skill-total balance alone is insufficient. Never interpret these metrics as proof of discrimination or actual matchmaking behavior.

## Development

MIT licensed. CI runs unit tests on Python 3.10–3.12.
