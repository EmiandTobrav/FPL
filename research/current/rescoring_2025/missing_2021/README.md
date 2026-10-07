# 2021/22 missing-match recovery — 7 October 2026

All **1238 remaining active-outfield defcon gaps** from the preceding repair version are now filled with observed match counts. Coverage is **9722/9722 (100%)**. This is complete coverage of a provisional reconstruction, not proof of exact official FPL scoring. Cost: **NOK 0**. No models were retrained and the active benchmark is unchanged.

## What was recovered

| Missing input | Matches | Player/match labels recovered |
|---|---:|---:|
| Recoveries, with existing CBIT retained | 75 | 1211 |
| Full defensive counts for Brentford–Wolves, 22 January 2022 | 1 | 27 |
| Total | 76 | 1238 |

The fills produce 178 additional two-point defcon awards (356 points across the player population). This is not a manager's season gain. The other 1060 previously unknown labels resolve to zero from observed counts, not from missing-value imputation.

FotMob's public `/api/data/matchDetails?matchId=...` endpoint supplied all 76 target matches and 20 fixed control matches, with zero download errors. The older `/api/matchDetails` route returned 404. Match IDs were resolved from the worldfootballR shot archive using actual date and both teams; its inconsistent parent-season field was deliberately not used. No authentication, paid account or workaround for blocked access was used.

Players join by FotMob's Opta ID to the FPL `code`, then by official fixture. Each match must agree on date, both teams, league and final score. Every inserted row also agrees on team and goals and has positive source minutes within two minutes of FPL. Brighton's two spelling variants are normalized. FPL's GK/GKP spelling variants are normalized for the audit. All 1238 inserted rows pass these gates.

One separate outfield row, Kristoffer Ajer in Brentford–Leeds (fixture 372), has a 14-minute discrepancy and is rejected by the supplementary-source identity gate. It is not a missing defcon target and no data for that row is overwritten. Keeper goals are absent in this source schema; keepers are outside the defcon validation population.

## Validation and limitation

Twenty complete fixtures were selected at evenly spaced positions in chronological order, before comparing outcomes. The overlap contains 509 active outfield observations:

| Statistic | Equal to archived FBref counts |
|---|---:|
| Recoveries | 509/509 |
| Tackles | 509/509 |
| Shot blocks | 509/509 |
| Interceptions | 509/509 |
| Clearances | 447/509 |
| Derived defcon points using all source counts | 505/509 |

The four point differences all arise from clearances (Shaw, Gudmundsson, Xhaka and McGinn in their audited fixtures). This comparison does not establish which provider is correct for every discrepancy. Existing observed FBref counts are preserved; only missing cells receive FotMob values. Thus the 1211 recovery-only fills use the component with perfect agreement in this sample. The 27 full-match fills remain explicitly marked as a different provisional source.

For Brentford–Wolves, summed FotMob player counts exactly match the official Premier League team totals in all ten checks: tackles, blocks, interceptions, clearances and recoveries for both teams. This independently checks the team totals, not each player's allocation. The raw official response and the raw FotMob match response are committed for this check.

Known v2 labels, all original FPL minutes and historical points remain unchanged. Tests check rejection of wrong match IDs/dates, ten official team totals, identity gates, preservation of all previously known counts and labels, and valid 0/2 outputs. These are targeted local checks, not a claim of full repository CI success.

Historical assists, bonus and other point components are unchanged. Full conversion to every 2025/26 rule is still outstanding. The original benchmark mean of 2351.50 cannot be compared directly to new rescored runs.

## Reproduce and resume

Prepare the repository's FPL data and the preceding historical_fbref/gap_repair builds first. Then use the committed normalized source table:

```sh
python research/current/rescoring_2025/missing_2021/build.py
python research/current/rescoring_2025/missing_2021/verify.py
```

`build.py` writes the full `results/2021-22_labels.csv` locally. The committed `2021-22_patch.csv` contains the 1238 fills relative to gap_repair v2; `gap_fill_audit.csv` retains before/after counts and source identities. The full regenerated table is not duplicated in git. Use its `defcon` column and quality flags for the next common-scoring experiment.

`fetch.py` optionally downloads/reparses the original responses using two workers and a cache. It checks frozen hashes where available and refuses changed responses for review. It stops on authorization/rate-limit responses rather than bypassing them. `results/sources.json` pins the 96 match URLs and hashes. `input_sha256.json` pins builder inputs; result CSVs and normalized counts are committed so this checkpoint does not depend on live API availability. Large exploratory downloads are excluded.

Sources:

- [FotMob example match data](https://www.fotmob.com/api/data/matchDetails?matchId=3610151)
- [Official Premier League team statistics](https://footballapi.pulselive.com/football/stats/match/66563)
- [worldfootballR match-ID archive](https://github.com/JaseZiv/worldfootballR_data/releases/tag/fotmob_match_details)
- `source_review.json` records other inspected sources and why they were not used. In particular the GOALS processed data has conflicting historical player/match assignments; it was not ingested.

## Next work

The 2021/22 gap is closed at the provisional-label level. The same source can next be evaluated for the 119 remaining 2022/23 labels and 14 2023/24 labels. Clearance-definition discrepancies should remain a separate audit rather than silently changing the scoring basis in this repair. Once the common dataset is frozen, benchmark and challengers must be rerun with the same scoring version and time-correct training windows.
