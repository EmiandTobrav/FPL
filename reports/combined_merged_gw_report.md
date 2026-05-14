# Combined merged_gw Report

Vaastav rows are used before the boundary season. FPL API rows are used from `2025-26` onward. No season is mixed between sources.

Dropped Vaastav rows at or after boundary: 22353
Dropped Vaastav seasons: ['2025-26']
Skipped pre-boundary FPL API seasons: []

## Seasons By Source

| source | season |
| --- | --- |
| fpl_api_included | 2025-26 |
| vaastav_included | 2016-17 |
| vaastav_included | 2017-18 |
| vaastav_included | 2018-19 |
| vaastav_included | 2019-20 |
| vaastav_included | 2020-21 |
| vaastav_included | 2021-22 |
| vaastav_included | 2022-23 |
| vaastav_included | 2023-24 |
| vaastav_included | 2024-25 |

## Row Counts By Source And Season

| source | season | rows |
| --- | --- | --- |
| vaastav_included | 2016-17 | 23679 |
| vaastav_included | 2017-18 | 22467 |
| vaastav_included | 2018-19 | 21790 |
| vaastav_included | 2019-20 | 22560 |
| vaastav_included | 2020-21 | 24365 |
| vaastav_included | 2021-22 | 25447 |
| vaastav_included | 2022-23 | 26505 |
| vaastav_included | 2023-24 | 29725 |
| vaastav_included | 2024-25 | 27605 |
| vaastav_dropped | 2025-26 | 22353 |
| fpl_api_included | 2025-26 | 28066 |

## Required Column Coverage

| column | present | non_missing_rows | coverage_pct |
| --- | --- | --- | --- |
| season | True | 252209 | 100.0 |
| gw | True | 252209 | 100.0 |
| element | True | 252209 | 100.0 |
| name | True | 252209 | 100.0 |
| team | True | 161713 | 64.12 |
| opponent_team | True | 252209 | 100.0 |
| was_home | True | 252209 | 100.0 |
| position | True | 161713 | 64.12 |
| total_points | True | 252209 | 100.0 |
| minutes | True | 252209 | 100.0 |
| bonus | True | 252209 | 100.0 |
| bps | True | 252209 | 100.0 |

## Schema Normalization

Numeric columns are coerced with `pd.to_numeric(errors="coerce")` before parquet writing.

### Numeric Coercions

| column | non_missing_before | values_coerced_to_na |
| --- | --- | --- |
| gw | 252209 | 0 |
| GW | 252209 | 0 |
| element | 252209 | 0 |
| fixture | 252209 | 0 |
| opponent_team | 252209 | 0 |
| round | 252209 | 0 |
| creativity | 252209 | 0 |
| influence | 252209 | 0 |
| threat | 252209 | 0 |
| ict_index | 252209 | 0 |
| expected_goals | 111901 | 0 |
| expected_assists | 111901 | 0 |
| expected_goal_involvements | 111901 | 0 |
| expected_goals_conceded | 111901 | 0 |
| total_points | 252209 | 0 |
| minutes | 252209 | 0 |
| starts | 111901 | 0 |
| bonus | 252209 | 0 |
| bps | 252209 | 0 |
| selected | 252209 | 0 |
| transfers_in | 252209 | 0 |
| transfers_out | 252209 | 0 |
| transfers_balance | 252209 | 0 |
| value | 252209 | 0 |
| assists | 252209 | 0 |
| clean_sheets | 252209 | 0 |
| goals_conceded | 252209 | 0 |
| goals_scored | 252209 | 0 |
| own_goals | 252209 | 0 |
| penalties_missed | 252209 | 0 |
| penalties_saved | 252209 | 0 |
| red_cards | 252209 | 0 |
| saves | 252209 | 0 |
| team_a_score | 252150 | 0 |
| team_h_score | 252150 | 0 |
| yellow_cards | 252209 | 0 |

### Final Key Dtypes

| column | dtype |
| --- | --- |
| season | string |
| name | string |
| team | string |
| position | string |
| was_home | boolean |
| gw | int64 |
| GW | int64 |
| element | int64 |
| fixture | int64 |
| opponent_team | int64 |
| round | int64 |
| creativity | float64 |
| influence | float64 |
| threat | float64 |
| ict_index | float64 |
| expected_goals | float64 |
| expected_assists | float64 |
| expected_goal_involvements | float64 |
| expected_goals_conceded | float64 |
| total_points | int64 |
| minutes | int64 |
| starts | float64 |
| bonus | int64 |
| bps | int64 |
| selected | int64 |
| transfers_in | int64 |
| transfers_out | int64 |
| transfers_balance | int64 |
| value | int64 |
| assists | int64 |
| clean_sheets | int64 |
| goals_conceded | int64 |
| goals_scored | int64 |
| own_goals | int64 |
| penalties_missed | int64 |
| penalties_saved | int64 |
| red_cards | int64 |
| saves | int64 |
| team_a_score | float64 |
| team_h_score | float64 |
| yellow_cards | int64 |
