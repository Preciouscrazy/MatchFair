# MatchFair

**Python 3.10+ | Deterministic matchmaking simulation | Skill-balance and queue-order tradeoffs**

MatchFair is an independent offline simulator for exploring how **skill-balance objectives interact with queue selection**. It groups synthetic players by region, selects match-sized batches in longest-wait-first order, and exhaustively searches small-team partitions to minimize each match's skill-total difference.

**Engineering focus:** deterministic tie-breaking, precise comparisons, strict data validation, safe JSON report generation, and reproducible counterexamples—not real player skill estimates or deployed matchmaking behavior.

[Engineering case study](docs/case-study.md) · [Validation record](evidence/validation.md) · [Synthetic example](examples/players.csv) · [Tradeoff fixture](examples/queue_tradeoff.csv)

MatchFair uses no Riot Games API, live player accounts or production matchmaking systems. All sample players, ratings and wait times are fictional.

## 60-second walkthrough

The [sample report](evidence/sample-match-report.json) shows two 2v2 matches from [eight fictional players](examples/players.csv). Each region’s team totals tie. The sample fixture and tradeoff fixture are both checked against the committed JSON reports in automated tests. The expanded regression suite also covers edge cases, input/output safety, and six Windows/Ubuntu Python combinations; see the [validation record](evidence/validation.md) for verified status.

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

Input columns, in that **exact order**: `player_id,skill_rating,wait_seconds,region`. Player IDs must be unique globally, including across regions. Skill ratings and waits must be finite, nonnegative numbers; region and ID cannot be blank. Extra or missing columns are rejected with a source-line error. By default, teams have 2 players each (`--team-size 2`). Each regional pool must be a multiple of `2 * team_size`. A match is formed only among players in the same region.

The CLI rejects an output path that refers to its input CSV, including hard-link aliases. It serializes JSON completely before staging a temporary file next to the destination and replacing the report; malformed input cannot truncate an existing report. The operation does not coordinate simultaneous writers or guarantee durability after power loss.

## Algorithm

1. Validate IDs and nonnegative finite metrics.
2. Group by region; order players by wait time (descending), then ID.
3. Take consecutive groups of `2 * team_size`.
4. Enumerate unique team assignments and compare the **actual absolute skill-total gap** (no rounding before candidate ranking).
5. Break equal-gap ties deterministically using player IDs.

This exhaustive partitioning is suitable for small teams only (team size <= 5). It is not a production matchmaking algorithm; it does not optimize role fit, latency, parties, uncertainty, or outcomes.

## Metrics

Per match: team skill totals, absolute difference, mean wait seconds, maximum wait seconds. Summary: match count and mean skill difference. Skill rating is an illustrative synthetic input, not an official game rank.

## Ethics and limitations

No real player identities or live game integrations. Fairness is multidimensional: skill-total balance alone is insufficient. Never interpret these metrics as proof of discrimination or actual matchmaking behavior.

## Development

MIT licensed. The implementation passed **all six GitHub Actions combinations** (Python **3.10, 3.11, 3.12** on **Windows and Ubuntu**) in [run #43693709556](https://github.com/Preciouscrazy/MatchFair/actions/runs/43693709556). The [validation record](evidence/validation.md) identifies the exact tested source commit and follow-up CI status. See [the case study](docs/case-study.md) for architecture, complexity, safety and evidence boundaries.
