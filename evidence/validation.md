# MatchFair — Cross-platform validation record

**Date:** 2026-11-15  
**Upgrade PR:** [#2 — reliability, CI, case study](https://github.com/Preciouscrazy/MatchFair/pull/2)  
**Implementation commit verified:** [`cd7c60f57a0739cd4a61dc49004eb44e9731e12b`](https://github.com/Preciouscrazy/MatchFair/commit/cd7c60f57a0739cd4a61dc49004eb44e9731e12b)  
**Workflow:** [GitHub Actions run #43693709556](https://github.com/Preciouscrazy/MatchFair/actions/runs/43693709556)

## Verified implementation results

Run **#43693709556** completed all six jobs successfully for the implementation commit cited above. The workflow installs the package in editable mode and runs `python -m unittest discover -s tests -v` on each runner.

| Python version | Ubuntu 24.04 | Windows latest |
| --- | --- | --- |
| 3.10 | **PASS** | **PASS** |
| 3.11 | **PASS** | **PASS** |
| 3.12 | **PASS** | **PASS** |

The upgraded suite contains **30 unit tests** and **12 CLI subprocess tests** (42 test methods in total). It covers strict four-column CSV validation, duplicate IDs, malformed and non-finite values, regional pooling, exact skill-gap minimization, deterministic tie breaks, all supported small team sizes, report-file overwrite safeguards, process exit codes, and parsed JSON comparisons to the two committed fixtures. A hard-link CLI test may skip on platforms unable to create hard links; check individual job logs before claiming that specific case ran on all environments.

## Compared evidence

- [Balanced example JSON](sample-match-report.json): two 2v2 synthetic matches (EU and NA), both with zero skill-total gap under the current heuristic
- [Queue-order tradeoff JSON](queue-tradeoff-report.json): fixed longest-wait-first groups produce two 100-point skill gaps; different cross-batch selection could change that outcome
- [Previous Ubuntu baseline run #42587124107](https://github.com/Preciouscrazy/MatchFair/actions/runs/42587124107): five original unit tests across Python 3.10–3.12

Both report files remain the exact canonical golden fixtures. The redundant root `match-report.json` and four tracked Python 3.15 bytecode files have been deleted from the proposed branch.

## Reproduce

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m matchfair --input examples/players.csv --output match-report.json
python -m matchfair --input examples/queue_tradeoff.csv --output tradeoff-report.json
```

**Evidence boundary:** Successful CI proves these defined checks on the cited hosted environments, not production readiness, performance under a live queue, or fairness of real-world matchmaking outcomes. Tests use synthetic player data only. A newer documentation-only commit will run its own CI checks; the cited implementation run does not automatically verify every future commit.
