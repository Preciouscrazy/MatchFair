# MatchFair

**Offline matchmaking fairness laboratory** for studying skill balance and queue-wait tradeoffs in simulated multiplayer matches.

MatchFair is an independent educational project, not a Riot Games service or integration. It reads synthetic player data, creates two balanced teams using a deterministic heuristic, and reports skill gaps and waiting-time summaries. It does not use Riot APIs or player accounts.

## Quick start

Requires Python 3.10+; runtime uses the standard library only.

```bash
python -m pip install -e .
python -m matchfair --input examples/players.csv --output match-report.json
python -m unittest discover -s tests -v
```

Input columns: `player_id,skill_rating,wait_seconds,region`. Each region must have an even number of players to form matches. By default, teams have 2 players each (`--team-size 2`), and the pool size must be a multiple of `2 * team_size`. A match is formed only among players in the same region.

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
