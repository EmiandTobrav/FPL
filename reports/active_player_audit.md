# Active Player Audit

Active rule: `minutes_mean_last_3 > 0 OR minutes_mean_last_5 >= 30 OR starts_last_5 > 0`.

## Overall Active Vs Inactive

| active_status | rows | avg_next_gw_points | nonzero_next_gw_points_share |
| --- | --- | --- | --- |
| active | 52235 | 2.0690724609935867 | 0.67194409878434 |
| inactive | 50384 | 0.17666322642108606 | 0.07639329946014607 |

## Counts By Season

| segment | active | inactive |
| --- | --- | --- |
| 2022-23 | 13693 | 12034 |
| 2023-24 | 14055 | 14805 |
| 2024-25 | 14057 | 12442 |
| 2025-26 | 10430 | 11103 |

## Counts By GW Bucket

| segment | active | inactive |
| --- | --- | --- |
| GW1-5 | 5557 | 7561 |
| GW11+ | 39426 | 36956 |
| GW6-10 | 7252 | 5867 |

## Counts By Position

| segment | active | inactive |
| --- | --- | --- |
| DEF | 18289 | 15921 |
| FWD | 6204 | 5857 |
| GK | 3327 | 7955 |
| MID | 24415 | 20651 |

## Inactive Rows In Top Actual Scorers

| segment | rows | inactive_rows_in_top_k | inactive_share_in_top_k |
| --- | --- | --- | --- |
| top_10 | 1637 | 86 | 0.05253512522907758 |
| top_20 | 3253 | 192 | 0.0590224408238549 |
| top_50 | 7945 | 541 | 0.06809314033983638 |

## Recommendation

Test filtering training and weekly candidate rows to likely active players using `minutes_mean_last_3 > 0 OR minutes_mean_last_5 >= 30 OR starts_last_5 > 0`.
