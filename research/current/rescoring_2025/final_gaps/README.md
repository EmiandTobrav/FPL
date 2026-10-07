# Remaining gaps and clearance-definition audit — 7 October 2026

All **133 remaining mapped defcon gaps** in 2022/23 and 2023/24 are filled with observed FotMob counts. No cost, no new model training, and no benchmark change.

| Season | Target matches | Missing before | Missing after | Active outfield coverage |
|---|---:|---:|---:|---:|
| 2022/23 | 7 | 119 | 0 | 10575/10575 |
| 2023/24 | 14 | 14 | 0 | 10608/10608 |

The 2022/23 holes are missing recoveries in seven opening-weekend matches; they produce 20 two-point awards. The 2023/24 holes are Yarmoliuk's missing defensive fields; all 14 reconstructed outcomes are zero from observed counts. These are player-population results, not manager season gains.

Together with earlier repairs, all mapped active-outfield defcon gaps in 2019/20–2023/24 are closed. This is **coverage**, not proof that every label matches an official modern FPL counterfactual.

## New-source controls

37 FotMob matches were fetched: 21 target matches plus eight chronologically spaced, complete-fixture controls per season. Dates, teams, league and final score match FPL fixtures. Players join through Opta/FPL code, with team, goals, positive minutes and a two-minute tolerance checked. All 133 targets pass; no sampled active outfield row fails the identity gate.

Controls contain 224 and 231 active outfield rows. Recoveries, tackles, blocks and interceptions agree with the previous archive on **455/455** observations. Clearances agree on 212/224 and 218/231, while derived defcon awards agree on **455/455**.

The five count disagreements inside the target set (one tackle, one interception and three clearances) are explicitly retained in the audit. Known historical counts are preserved in this gap-only version. Replacing all five components with FotMob instead gives the same award for every one of the 133 targets; `target_source_sensitivity.csv` records this check. This does not establish equality of underlying counts.

## Clearance discrepancy identified

A targeted diagnostic fetched complete official Premier League player/match stats using the working `fixtures` filter, not the ineffective `matches` filter tested previously. The sample comprises:

- 30 observations from the previous 2021/22 controls: all four award disagreements, 16 further clearance disagreements, and ten equal-count controls.
- All ten previously identified 2025/26 false-positive awards, plus ten evenly spaced matching controls from the available first-40-match FBref overlap.

In **50/50** observations:

`archived FBref Clr = official PL total_clearance + official PL blocked_cross`

FotMob clearances equal official PL clearances in **30/30** historical comparisons. This is strong empirical evidence that the archived FBref field includes blocked crosses, while the PL/FotMob field used here does not. It is not a universal definition proved for all seasons. An unmeasured blocked-cross count must not be guessed or replaced with an average correction.

Using official PL components removes **7 of the 10** old false-positive awards in the targeted 2025/26 sample; all ten matching controls still match. Three discrepancies remain:

| Player / FPL fixture | Remaining discrepancy |
|---|---|
| Bruno Guimaraes / 19 | Official FPL recoveries 8; current PL feed 9 |
| Maxence Lacroix / 21 | Official FPL CBI 9; current PL components sum to 10 |
| Matthijs de Ligt / 38 | Official FPL CBI 4; current PL components sum to 6 |

The latter two involve interceptions in the current PL response. We have not proved the revision history or exact cause of those three residual differences. Published FPL rules explain that points are locked after a gameweek, so later provider statistics need not be identical to the locked FPL score; that is a plausible explanation, not a confirmed diagnosis of these cases. Official FPL outcomes are therefore retained as ground truth wherever they exist.

The diagnostic was deliberately enriched for disagreements. **Do not report 17/20 or 47/50 as an unbiased accuracy estimate.** Raw official responses, URLs, hashes, component presence flags and the three unresolved cases are saved. Absent keys in those sparse official responses are treated as zero only for this diagnostic reconstruction and compared with known FPL outcomes; they are not used to fill the new target labels.

## Scoring basis and limits

The next harmonized reconstruction should prioritize official FPL fields when available, and otherwise use validated PL/FotMob components: clearances + shot blocks + interceptions + total tackles, plus recoveries for MID/FWD. Do not substitute raw FBref `Clr` for clearances without a separately observed blocked-cross correction. The source policy is recorded in `source_policy.json`.

**The historical corpus is not yet harmonized to that policy.** This checkpoint fills missing cells while preserving frozen prior versions; it does not silently rewrite all earlier known labels. `verified_clearance_observations.csv` records the 30 directly checked historical clearances for the next migration. Many existing FBref-derived labels can still have this count-definition bias.

Historical assists, bonus and other points remain unchanged. This is still historical points plus reconstructed defcon, not a full conversion of every 2025/26 rule. Benchmark `fixture_full_h3_adaptive_tc` and its historical mean 2351.50 remain unchanged.

## Reproduction

Prepare the repository's FPL files and run the earlier historical_fbref/gap_repair builders. The committed normalized source table then suffices:

```sh
python research/current/rescoring_2025/final_gaps/build_labels.py
python research/current/rescoring_2025/final_gaps/verify.py
```

Full rebuilt label tables are generated locally; compact per-season patches and all audits are committed. `collect.py` optionally regenerates the normalized FotMob table from the cached/public source responses. `audit_clearances.py` replays the frozen selection using the committed raw official responses. Source hashes prevent unnoticed revisions. Input hashes and targeted tests cover identities, preservation of known data, missing-not-zero bounds, source sensitivity and the measured clearance relation. No full repository CI or model rerun is claimed.

`raw/league_2023.json` was an exploratory fixture lookup and is not required or committed. A mapping failure was resolved by normalizing AFC Bournemouth and Tottenham names; all actual match metadata was subsequently checked.

Primary references: [Opta definitions](https://www.statsperform.com/opta-event-definitions/), [Premier League data collection](https://www.premierleague.com/en/stats/clarification), [FPL points finalization](https://www.premierleague.com/es/news/4080912). Exact API request URLs are in the two source manifests.

Next: harmonize the defensive components across the complete historical corpus, validate against the full official 2025/26 data, then freeze a shared scoring version before rerunning benchmark and challengers.
