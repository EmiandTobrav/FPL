# 2026/27 scoring: data audit, collection and BPS qualification

**Target: 2026/27. Status: NOT READY for complete historical rescoring.** The previous `historical_points_plus_harmonized_defcon_v1` remains a frozen intermediate, not a complete 2026/27 scoring dataset. No model or benchmark has been changed. Cost: NOK 0.

## Work completed

- Audited all 2660 existing FotMob match responses against their previously frozen SHA-256 hashes. Extracted expanded statistics for 77280 active source player appearances in 2019/20–2025/26, including keepers. This is a provider-row count; it is not the earlier active-outfield FPL denominator.
- Retained explicit missing values. An omitted field or a metric without a numeric value is not automatically an observed zero.
- Retrieved official 2026/27 scoring weights from FPL bootstrap and the actual Rules component served by the FPL application. The rule table and source hashes are in `rules_2026_27.json`. The component contains legacy/unused keys too; the evaluated formula uses the displayed 2026/27 rules, not every key indiscriminately.
- Collected 830 identity-checked primary PL player/match responses: 208 historical observations across seven first-match controls, and all 622 active observations from 2026/27 GW1–2. All collection calls completed without errors. Player ID, Opta code and one-appearance scope are checked; minute differences are audited rather than silently changing FPL minutes.
- Found primary fields for won tackles, non-corner crosses, free-kick crosses, errors leading to shots and goals, and big-chance saves. They are retained alongside original official FPL BPS/bonus for qualification.
- Resolved missing current FPL `pulse_id=0` through the official fixture catalog's Opta match code. Live FPL player fixtures come from the event's `explain` records, avoiding transferred players' current-team misassignment.

## Validation

GW1 was used to debug mappings; it is development data. The candidate was fixed before collecting GW2, with gates stated in `VALIDATION_PROTOCOL.md`.

| Evaluation | Matches | Active rows | Exact BPS | Exact bonus |
|---|---:|---:|---:|---:|
| 2026/27 GW1, development | 10 | 310 | 309 (99.68%) | 310 (100%) |
| 2026/27 GW2, held out | 10 | 312 | 311 (99.68%) | 312 (100%) |

GW2 passes the predeclared 99% BPS/bonus source-qualification gates. There are zero goal-count disagreements; all minute differences are at most one minute. One remaining GW2 BPS discrepancy (Anthony, -3) does not change bonus. These results do not establish full-season or historical accuracy. Six focused formula/tie-handling tests pass.

Important discoveries:

- FPL-assist counts, rather than ordinary Opta `goal_assist` alone, are needed by the successful current candidate. Historical assist harmonization therefore affects the bonus problem too.
- PL names for fouls are `was_fouled` and `fouls`; absent `fk_`-prefixed aliases must not silently erase those contributions.
- `accurate_cross_nocorner` is empirically consistent with the current BPS controls. Subtracting `accurate_freekick_cross` introduced four GW1 discrepancies, despite the public rule's “open play” wording. This semantic issue remains explicitly documented.
- Per-component integer thresholds fit the controls much better than retaining fractional CBI/recovery scores.
- The diagnostic alone treats omitted PL counters as zero. This is a source assumption being tested, not permission to replace missing historical data with zeros.

## Actual data gaps

| Requirement | Evidence/status |
|---|---|
| Pass completions and attempts | Values extracted for every active FotMob source row; definitions still require component-level validation before historical full-BPS use. |
| Core defensive counts | Existing harmonized dataset available. BPS needs won tackles, distinct from the total tackles used for defcon. |
| Chances, shots, dribbles, fouls, offside | Extracted from the full existing corpus, but many UI fields are sparse; `results/raw_field_coverage.csv` reports explicit values separately from omission. |
| Open-play/non-corner crosses, won tackles, errors leading to shots | Primary source now demonstrated and sampled; full historical player/match collection and coverage are NOT complete. |
| Big-chance saves | Absent from all 5381 historical FotMob goalkeeper rows. Primary PL historical season results are absent or suspiciously partial; do not interpret no leaderboard entries as zero saves. |
| Modern historical FPL assists | Not reconstructed. Ordinary assist totals and shot aggregates cannot resolve all deflections, defensive touches and handball cases. |
| Basic points and roster position | Official fields and 2026/27 weights exist. Any later rescoring must recompute basic points as well, including keeper goals, and state which season's FPL position classification is retained. |

The primary `big_chance_saves` season queries returned totals of 0, 0, 2, 0, 3, 144 and 540 for 2019/20–2025/26. These are **returned source totals, not asserted true season totals**. They demonstrate an unacceptable historical coverage discontinuity. 2025/26's leading keeper values match the official 2026/27 announcement, but that does not repair earlier years. The list can include explicit zero/non-keeper rows, so its entry count is not a count of qualified goalkeepers.

A proposed fallback `dispossessed + unsuccessful dribbles` for old “times tackled” matched only 191/208 historical controls under diagnostic sparse-zero treatment. It is not promoted as an exact substitute. This old metric is unnecessary for direct 2026/27 calculation, but would matter in a delta-from-old-BPS approach.

## Source attempts and limitations

- Official PL player/match endpoint yielded the newly collected data. The ranked-player endpoint ignored attempted fixture filters and returned season/all-time aggregates. Those responses were rejected as match data.
- Sofascore returned HTTP 403 challenge. WhoScored's observed public match URL returned HTTP 403 Forbidden. No retry through mirrors, proxies, sessions or access-control workarounds was attempted.
- `jakeyk11/football-data-analytics` references useful WhoScored analyses but contains only a README in its event-data directory. `withqwerty` describes a historical event corpus stored in a database; an accessible complete event export was not obtained. Other discovered PL archives expose aggregates/basic events, not verified complete shot qualifiers for this requirement.
- No purchase, subscription or message to a data owner has been made. A complete alternative historical event feed containing big-chance qualifiers remains unresolved; this is not a claim that none exists.

## Files and reproduction

`data/` contains all expanded historical FotMob observations in plaintext CSV partitions; `data/sha256.json` checks them. The parent harmonized dataset's source manifests identify the corresponding raw-response URLs/hashes. Full source responses remain local caches; they are not required to read the new committed observations.

`primary_data/` preserves all newly collected primary normalized observations and the two diagnostic tables, with checksums. `results/primary_sources*.json` stores raw source URLs/hashes. `results/primary_collection_manifest*.csv` preserves the official comparison fields and identity links. Raw keeper-season leaderboards are summarized with URLs in `results/big_chance_save_season_coverage.json`.

From a fresh checkout:

```bash
python research/current/scoring_2026_27/package_data.py restore
python research/current/scoring_2026_27/test_bps.py
python research/current/scoring_2026_27/validate_bps.py
python research/current/scoring_2026_27/validate_bps.py 2
python research/current/scoring_2026_27/report.py
```

`collect_primary.py` and `collect_primary.py 2` reproduce the respective source-qualification collections, with cached responses and bounded concurrency; these are **pilot scopes**, not full-history collectors. Live data may be revised. `audit_raw.py` reproduces the full historical extraction when the earlier FotMob raw cache has been collected.

`results/readiness.json` deliberately blocks complete historical rescoring. The next action is to secure actual historical big-chance-save/event coverage and resolve modern assists, while completing the remaining primary historical fields. No approximate labels should be silently promoted to an exact 2026/27 target. Keep all post-match statistics behind the decision-time cutoff if later used as lagged features.
