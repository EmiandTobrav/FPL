# Harmonized defensive counts, 2019/20–2025/26

Version: `historical_points_plus_harmonized_defcon_v1`. The authoritative freeze decision is in `results/manifest.json`; a candidate must not be called frozen unless every gate passes.

## Frozen results, 7 October 2026

All eight quality gates pass. Seven seasons × 380 fixtures = **2660 matches**, covering **71898 active-outfield player appearances**, including 61173 historical appearances. There are **zero unresolved historical defensive-award labels** and zero missing contemporary validation labels.

| Season | Active outfield appearances | Two-point awards | Changed awards vs preceding version |
|---|---:|---:|---:|
| 2019-20 | 9844 | 1615 | 131 |
| 2020-21 | 9628 | 1432 | 69 |
| 2021-22 | 9722 | 1482 | 73 |
| 2022-23 | 10575 | 1317 | 56 |
| 2023-24 | 10608 | 1265 | 75 |
| 2024-25 | 10796 | 1253 | 0 |
| 2025-26 | 10725 | 1417 | official FPL |

The harmonization removes 404 previously reconstructed historical awards (808 points across the entire player population); none is a manager-season gain/loss. 2024/25 award labels are unchanged. All 38 source-vs-FPL minute/goal flags remain visible in the audit and do not silently change FPL outcomes.

Full 2025/26 validation: **10698/10725 awards agree (99.748%)**. There are 22 false positives and 5 false negatives. Positive-award precision is **98.466%**, recall **99.647%**; the raw reconstructed population point error is +34. Exact defensive-count agreement is **10388/10725 (96.858%)**. By position, award disagreements are DEF 18/3950, MID 9/5347, FWD 0/1428 (only nine actual forward awards). These are full-season observations, not a selected audit sample, but they do not prove equivalent historical accuracy.

All 2660 raw hashes and parsed cache records were verified. Partition restoration and label rebuilding produce byte-identical copies of all 14 per-season count/label files. Six transformation tests pass. Exact duplicate input rows are removed only when every column agrees; conflicting fixture duplicates are resolved using official kickoff/event metadata and audited.

## Scope

One defensive-statistic definition across seven Premier League seasons: total tackles, shot blocks, interceptions, clearances, and recoveries from FotMob. Stable Opta/FPL player codes join to fixtures validated by date, both clubs and final score. Goalkeepers and zero-minute appearances are ineligible. DEF needs ten tackles/blocks/interceptions/clearances; MID/FWD needs twelve including recoveries. Unknowns are not zero: incomplete nonnegative counts can only establish an award when the known subtotal already reaches the threshold.

Historical total points are original FPL points plus reconstructed defensive contribution awards. **Historical assists and bonus remain historical. This is not a complete conversion to every 2025/26 rule.** For 2025/26, official FPL awards and original total points are authoritative; defcon is never added a second time. Public source counts can differ from frozen FPL outcomes. The exact reasons for the remaining differences are not established.

The source change removes the earlier FBref clearance definition's inclusion of blocked crosses. Previously frozen versions remain available. `results/changed_awards.csv` records each changed award; the sum is a player-population point change, not a manager's season gain.

## Reuse from a fresh checkout

Requires Python, pandas and numpy. From the repository root:

```bash
python research/current/rescoring_2025/harmonized/package_data.py restore
python research/current/rescoring_2025/harmonized/test_harmonized.py
```

`restore` verifies every committed partition checksum before reconstructing per-season `results/YYYY-YY_counts.csv` and `results/YYYY-YY_labels.csv`. No fresh network request or prior chat/ZIP file is needed. The expensive observations, derived labels and original response URLs/SHA-256 hashes are retained as plaintext partitions in `dataset/`.

To rebuild labels from frozen counts and the repository's FPL inputs (the builder automatically unpacks the existing `.csv.gz` inputs when needed and checks their frozen SHA-256 hashes):

```bash
python research/current/rescoring_2025/harmonized/build_labels.py --skip-prior-comparison
python research/current/rescoring_2025/harmonized/audit.py
```

The skip flag avoids needing locally regenerated older label versions. It affects comparison summaries only, not the generated new labels. For exact archived summary reproduction, regenerate previous versions first and omit the flag; keep the committed reports as the original freeze record. Input SHA-256 hashes in the manifest identify the FPL snapshots used. Never treat later live downloads as byte-identical historical snapshots.

To fetch all source responses again (optional, resumable):

```bash
python research/current/rescoring_2025/harmonized/collect.py
```

The collector verifies match metadata, uses bounded concurrency, records exceptions, and stops on access/rate-limit responses. Each match has a local checkpoint. Optional comma-separated season arguments select a subset. Do not use a partially collected export for training or evaluation. Full raw responses are not committed; normalized observations and raw-response hashes are retained.

## Audits

- `results/coverage.csv`: source fixtures, active-outfield coverage, awards and changes by season.
- `results/validation_summary.json`, `validation_breakdown.csv`: full official 2025/26 agreement, false positives/negatives, precision/recall, and position/gameweek breakdowns.
- `results/award_discrepancies_2025.csv`: all award disagreements, including component differences.
- `results/missing_rows.csv`: unresolved active-outfield source labels; must be empty at freeze.
- `results/stat_disagreements.csv`: minutes/goals differences after identity is established. They are retained as flags, not silent edits to FPL inputs.
- `results/duplicate_audit.csv`: exact input duplicates and official-fixture resolution of conflicting fixture rows.
- `results/manifest.json`: gates, scope, input/output hashes and zero cost.
- `PROTOCOL.md`: acceptance criteria declared before full-season validation.

## Model boundary and next experiment

These are post-match targets, never same-match pre-deadline features. Lag and cut off all derived features and rolling training labels at the appropriate decision time. There is no point-in-time provider revision archive for these historical reconstructions; do not claim perfect reconstruction of the information available on each past deadline.

The active model benchmark remains `fixture_full_h3_adaptive_tc`; its archived 2351.50 mean belongs to its existing scoring basis. No model has been retrained or promoted in this data task. Next, rerun this benchmark on the frozen scoring version with matching season windows, squad/chip rules, budgets and solver limits, then compare a separate defcon component with time-based retraining under those same conditions. Scores from different scoring versions must not be interpreted as model improvement.

Cost: NOK 0. No purchase or subscription.
