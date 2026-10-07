# Historical gap repair, 2026-10-07

This is a versioned data repair, not a new model or benchmark. Frozen v1 inputs and prior experiments remain unchanged. Cost: NOK 0; the user's total ceiling for any future data purchase remains NOK 500.

## Results

Missing labels among active outfield player/match rows:

| Season | Before | After | Coverage after |
|---|---:|---:|---:|
| 2019/20 | 2 | 0 | 100% |
| 2020/21 | 0 | 0 | 100% |
| 2021/22 | 1245 | 1238 | 87.27% |
| 2022/23 | 155 | 119 | 98.87% |
| 2023/24 | 57 | 14 | 99.87% |

Three crosswalk errors were repaired using stable FPL/Opta codes, exact source names, and fixture-team consistency checks: Harvey Elliott (444884, c8387671 → b9e1436c), Luke Harris (515024, 42dd1b56 → 8c3078cd), Hjalmar Ekdal (478969, f503ea63 → 3d554589). The archived Master.csv is untouched.

All 59 duplicate player/fixture keys in 2019/20 refer to postponed Manchester City–Arsenal (fixture 275). Official kickoff and event select GW39 on 17 June, not the stale March/GW29 row. There were 32 contradictory minute/point keys. Restoring actual appearances increases active outfield rows from 9814 to 9844; this is separate from filling the two missing labels. Both versions and the selection are audited.

Four further defcon outcomes are determined without imputing counts: known nonnegative counts already reach the threshold (two in each of 2021/22 and 2022/23). A missing recovery value cannot reverse those outcomes.

## Remaining holes and source investigation

- 2021/22: 1211 player/match rows missing recoveries, plus 27 rows from the absent Brentford–Wolves defensive match on 22 January 2022.
- 2022/23: 119 rows missing recoveries.
- 2023/24: 14 Yegor/Yehor Yarmoliuk rows missing defensive fields; his stable player identity is correct.

The alternate worldfootballR RDS misc archive was downloaded, hashed and parsed. All 81,328 rows join the CSV on season, match URL and player URL, with zero recovery differences including matching missing values. It provides no additional observations. A direct FBref attempt for Leicester–Chelsea on 20 November 2021 returned HTTP 403. Additional free-source searches did not yield verified replacement match counts; season aggregates cannot identify per-match threshold crossings. This is not a claim that every possible archive has been exhausted.

Sources: [worldfootballR release](https://github.com/JaseZiv/worldfootballR_data/releases/tag/fb_advanced_match_stats), [ID map](https://github.com/ChrisMusson/FPL-ID-Map). Input hashes and alternate-source evidence are in source_audit.json. Remaining matches and exact player rows are supplied as CSV worklists.

## Uncertainty and benchmark exposure

Unknown eligible rows retain a missing target and a [0,2] defcon interval. Missing does not become zero. Player totals aggregate using stable element IDs, including name changes. Bounds are conditional on the provider's observed counts: they do not cover measurement error in those counts. The earlier validation remains provisional (10 false positives in 1129 rows); complete coverage does not imply an exact official reconstruction.

Replay of the archived benchmark's fixed counted players in GW5–38 gives zero exposure to remaining holes in both 2022/23 and 2023/24. Captain fallback, Triple Captain multiplicity and historical contributions were checked against the archived trace. Defcon adds 52 and 54 points to those fixed partial-season decisions respectively. This is not a reoptimized strategy, not a full-season result, and does not establish rankings between models. GW1–4 lacks the same counted-player trace and is excluded. Unknown players might enter new strategies.

Historical assists, bonus and other components are retained. This still is not a full conversion to all 2025/26 scoring rules. Benchmark fixture_full_h3_adaptive_tc and its historical mean 2351.50 remain unchanged and cannot be compared directly with rescored results.

## Reproduction and files

After preparing the repository's project/data inputs:

```sh
python research/current/rescoring_2025/historical_fbref/download.py
python research/current/rescoring_2025/historical_fbref/build.py
python research/current/rescoring_2025/gap_repair/repair.py
python research/current/rescoring_2025/gap_repair/exposure.py
```

repair.py runs threshold/unknown/duplicate checks, validates source hashes and identity consistency, and writes full v2 labels locally. Compact per-season patches are committed instead of duplicating all five full tables. Patches describe changed v1 rows; use the builder for a full v2 schema including bounds on unchanged rows. Summary, remaining gaps, match worklist, player bounds, duplicate audit and exposure results are committed. The two small benchmark traces are pinned copies from commit a990c287c7b03fc0990e6cdda43c785c63b4d026 under fixture_strategy/portable/trace_SEASON_full_h3_adaptive_triple_captain.json.

audit_alternate.py optionally reproduces the RDS/CSV comparison using rdata (tested with 1.1.0). Large downloaded alternate files are not committed.

## Next use

Prioritize actual 2021/22 match-level recovery data using remaining_matches.csv; no paid service has yet demonstrated the needed coverage. For training, mask missing defcon targets while retaining usable historical components. Do not discard an entire season or impute training targets as observed truth. Evaluate all candidate decisions under the same reconstructed scoring version and inspect their exposure before drawing model-ranking conclusions. Reoptimization, opening-round exposure, statistical imputation experiments and full modern bonus/assist reconstruction remain outstanding.
