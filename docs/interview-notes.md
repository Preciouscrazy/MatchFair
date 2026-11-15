# MatchFair interview notes

## Explain the project

MatchFair is a deterministic Python simulation that groups fictional players by region and wait order, then searches team assignments within each group to minimize the absolute difference in skill totals.

## Explain one design choice

The simulator fixes the first player to team A. That removes mirror duplicates while retaining all unique partitions. IDs provide a stable tie break so repeated runs produce the same result.

## Explain the tradeoff

The queue-order fixture shows that optimizing teams inside each group does not optimize which players enter a group. A 100-point gap remains in both matches when preserving the longest-wait-first groups. Swapping players across a group boundary could make both gaps zero, but this simulation does not model future arrivals or the impact on wait times.

## A limitation and next improvement

Exhaustive partition search is suitable only for small teams, capped at five players per team. A next step would compare several group-selection policies and explicitly score the tradeoff between skill gap and waiting time.

## Evidence to open

- `evidence/sample-match-report.json`
- `evidence/queue-tradeoff-report.json`
- `examples/queue_tradeoff.csv`

## Validation and detailed walkthrough

The [engineering case study](case-study.md) gives a short interview-ready architecture and tradeoff explanation. The [validation matrix](../evidence/validation.md) records exact Windows/Ubuntu CI runs. The CLI uses strict CSV input and staged output; the simulator checks inputs supplied through the Python API too. The deterministic sample report and queue-order counterexample are compared with their checked-in JSON, not evaluated against real player outcomes.
