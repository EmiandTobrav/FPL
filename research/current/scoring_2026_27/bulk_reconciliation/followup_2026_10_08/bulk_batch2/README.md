# Batch 2: primary archive-gap recovery and defensive-possession assist bounds

The ledger moves from **28,934 to 24,285 open fields**, a **4,649 / 16.07%**
reduction. It covers the same 77,280 player-matches and 2,660 fixtures. There are
22,496 uniquely affected player-matches, **54,784 complete player-matches** (+2,220)
and **489 complete whole fixtures** (+10). Availability is not qualified scoring.

| Field | Newly available |
|---|---:|
| Assists under target rules | 2,304 |
| Goal-line clearances | 548 |
| Times tackled | 455 |
| Won tackles | 330 |
| Signed legacy net tackles | 330 |
| Fouls won | 322 |
| Shots on target | 320 |
| Clearances + blocks + interceptions | 40 |

`build.py` combines disjoint overlays from `primary_gap_recovery` and
`assist_possession_bounds`. It asserts every changed destination was open and
missing and preserves all other rows and protected columns unchanged at
the dataframe value level. No raw FPL, approved keeper/event corrections, historical
compatible values, frozen controls, locked labels, models or benchmark are changed.
No BPS/bonus calculation or model training occurs.

The penalty-foul pilot is withheld for insufficient control coverage. The new
competition-total endpoint probe failed with 404. These are documented negative
results, not new zero-valued observations. Historical source failures remain valid.

`results/requirements.csv.xz` is the cumulative ledger; `remaining_fields.csv.gz`
is the open queue. `summary.json`, field/season summaries and deduplicated player/
fixture readiness files are generated from exactly the same rows. Internal
`published:false` describes execution before Git publication, not scoring status.

Python 3.12 and pandas 2.2.3 suffice; no external raw parquet archives are needed.
From the repository, first run the enclosing snapshot's `bootstrap.py` to restore
two earlier frozen input gzip files. Then run:

```sh
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/bulk_batch2/reproduce.py
```

This copies committed inputs to a separate temporary directory, restores and
verifies the new raw responses, runs all new predictors and controls without
network, rebuilds the cumulative ledger and checks exact output hashes.
`replay_verification.json` records the result. The 22 new focused tests cover
candidate-chain guards, missing-parent/residual/conservation rules, incomplete CBI
and signed legacy arithmetic. Full repository tests and GitHub CI are not claimed.
