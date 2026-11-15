# MatchFair — CI validation and reproducibility

**Upgrade branch:** `improve/matchfair-validation-ci-case-study`  
**Baseline main commit:** [`fb9bdf9103d12abd24aeecfb2ecde58f330a6224`](https://github.com/Preciouscrazy/MatchFair/commit/fb9bdf9103d12abd24aeecfb2ecde58f330a6224)

## Existing evidence

The earlier [Ubuntu CI run #42587124107](https://github.com/Preciouscrazy/MatchFair/actions/runs/42587124107) passed Python 3.10, 3.11 and 3.12 with five original unit tests. The repository contains two unchanged synthetic evidence reports:

- [Sample balanced 2v2 matches](sample-match-report.json)
- [Queue-order tradeoff with 100-point gaps](queue-tradeoff-report.json)

## Upgrade checks

The new GitHub Actions matrix runs **Windows and Ubuntu** with **Python 3.10, 3.11 and 3.12**. Both algorithm/CSV unit tests and real CLI subprocess tests run in every job.

| Check | Expected | Hosted result |
| --- | --- | --- |
| Python 3.10 on Ubuntu and Windows | Passing tests | Pending first branch workflow |
| Python 3.11 on Ubuntu and Windows | Passing tests | Pending first branch workflow |
| Python 3.12 on Ubuntu and Windows | Passing tests | Pending first branch workflow |
| Golden sample + queue-order JSON | Parsed JSON matches committed evidence | Pending |
| Input/output file aliases and invalid inputs | Rejected without source-data loss | Pending |

Do not treat configured matrix jobs as verified results until GitHub Actions reports success on the same source commit.

## Reproduction commands

```bash
python -m pip install -e .
python -m unittest discover -s tests -v
python -m matchfair --input examples/players.csv --output match-report.json
python -m matchfair --input examples/queue_tradeoff.csv --output tradeoff-report.json
```

Generated reports are local artifacts. `match-report.json` is ignored, while the canonical examples are versioned in `evidence/`. The fixtures are fictional and do not establish production performance or actual player fairness.
