# Full Feature Audit

Total columns: 95
Configured model features: 25
Configured model features present in dataset: 19
Excluded columns: 2
Likely leakage columns: 58
Mostly missing columns: 9

## Column Groups

| column_group | columns |
| --- | --- |
| raw current-GW outcome columns | 51 |
| identifiers and metadata | 13 |
| leakage-safe rolling player features | 8 |
| rolling team form features | 6 |
| ownership/transfer features | 4 |
| team-strength Elo features | 4 |
| unavailable or mostly missing features | 4 |
| targets | 2 |
| fixture/home-away features | 1 |
| position features | 1 |
| price/value features | 1 |

## Currently Used Model Features

| column_name | column_group | appears_leakage_safe | recommended_action |
| --- | --- | --- | --- |
| position | position features | True | keep |
| points_last_1 | leakage-safe rolling player features | True | keep |
| points_mean_last_3 | leakage-safe rolling player features | True | keep |
| points_mean_last_5 | leakage-safe rolling player features | True | keep |
| minutes_mean_last_3 | leakage-safe rolling player features | True | keep |
| minutes_mean_last_5 | leakage-safe rolling player features | True | keep |
| starts_last_5 | leakage-safe rolling player features | True | keep |
| bonus_last_5 | leakage-safe rolling player features | True | keep |
| bps_last_5 | leakage-safe rolling player features | True | keep |
| team_elo_pre_gw | team-strength Elo features | True | keep |
| opponent_elo_pre_gw | team-strength Elo features | True | keep |
| elo_difference | team-strength Elo features | True | keep |
| home_adjusted_elo_difference | team-strength Elo features | True | keep |
| team_goals_scored_mean_last_5 | rolling team form features | True | keep |
| team_goals_conceded_mean_last_5 | rolling team form features | True | keep |
| opponent_goals_scored_mean_last_5 | rolling team form features | True | keep |
| opponent_goals_conceded_mean_last_5 | rolling team form features | True | keep |
| team_clean_sheet_rate_last_5 | rolling team form features | True | keep |
| opponent_clean_sheet_rate_last_5 | rolling team form features | True | keep |

## Configured Model Features Not Present In Dataset

| feature | present_in_dataset | column_group |
| --- | --- | --- |
| pred_previous_gameweek_points | False | created during backtest or unavailable |
| pred_rolling_3_gameweek_mean | False | created during backtest or unavailable |
| pred_rolling_5_gameweek_mean | False | created during backtest or unavailable |
| pred_minutes_adjusted_rolling_mean | False | created during backtest or unavailable |
| xG_last_5 | False | created during backtest or unavailable |
| xA_last_5 | False | created during backtest or unavailable |

## Currently Used Features Needing Review

None.

## Safe Unused Candidate Features

| column_name | column_group | recommended_action | missing_pct_overall |
| --- | --- | --- | --- |
| was_home | fixture/home-away features | investigate | 0.0 |

## Features That Should Never Be Used Directly

| column_name | column_group | recommended_action |
| --- | --- | --- |
| name | identifiers and metadata | metadata_only |
| element | identifiers and metadata | metadata_only |
| fixture | identifiers and metadata | metadata_only |
| id | identifiers and metadata | metadata_only |
| kickoff_time | identifiers and metadata | metadata_only |
| kickoff_time_formatted | identifiers and metadata | metadata_only |
| opponent_team | identifiers and metadata | metadata_only |
| round | identifiers and metadata | metadata_only |
| team_a_score | raw current-GW outcome columns | keep_lagged_only |
| team_h_score | raw current-GW outcome columns | keep_lagged_only |
| GW | identifiers and metadata | metadata_only |
| season | identifiers and metadata | metadata_only |
| gw | identifiers and metadata | metadata_only |
| team | identifiers and metadata | metadata_only |
| modified | identifiers and metadata | metadata_only |
| next_gw_points | targets | exclude |
| next_3_gw_points | targets | exclude |

## Features That Should Only Be Lagged Or Rolled

| column_name | column_group | missing_pct_overall |
| --- | --- | --- |
| assists | raw current-GW outcome columns | 0.0 |
| attempted_passes | raw current-GW outcome columns | 72.44 |
| big_chances_created | raw current-GW outcome columns | 72.44 |
| big_chances_missed | raw current-GW outcome columns | 72.44 |
| bonus | raw current-GW outcome columns | 0.0 |
| bps | raw current-GW outcome columns | 0.0 |
| clean_sheets | raw current-GW outcome columns | 0.0 |
| clearances_blocks_interceptions | raw current-GW outcome columns | 63.37 |
| completed_passes | raw current-GW outcome columns | 72.44 |
| creativity | raw current-GW outcome columns | 0.0 |
| dribbles | raw current-GW outcome columns | 72.44 |
| errors_leading_to_goal | raw current-GW outcome columns | 72.44 |
| errors_leading_to_goal_attempt | raw current-GW outcome columns | 72.44 |
| fouls | raw current-GW outcome columns | 72.44 |
| goals_conceded | raw current-GW outcome columns | 0.0 |
| goals_scored | raw current-GW outcome columns | 0.0 |
| ict_index | raw current-GW outcome columns | 0.0 |
| influence | raw current-GW outcome columns | 0.0 |
| key_passes | raw current-GW outcome columns | 72.44 |
| minutes | raw current-GW outcome columns | 0.0 |
| offside | raw current-GW outcome columns | 72.44 |
| open_play_crosses | raw current-GW outcome columns | 72.44 |
| own_goals | raw current-GW outcome columns | 0.0 |
| penalties_conceded | raw current-GW outcome columns | 72.44 |
| penalties_missed | raw current-GW outcome columns | 0.0 |
| penalties_saved | raw current-GW outcome columns | 0.0 |
| recoveries | raw current-GW outcome columns | 63.37 |
| red_cards | raw current-GW outcome columns | 0.0 |
| saves | raw current-GW outcome columns | 0.0 |
| selected | ownership/transfer features | 0.0 |
| tackled | raw current-GW outcome columns | 72.44 |
| tackles | raw current-GW outcome columns | 63.37 |
| target_missed | raw current-GW outcome columns | 72.44 |
| team_a_score | raw current-GW outcome columns | 0.02 |
| team_h_score | raw current-GW outcome columns | 0.02 |
| threat | raw current-GW outcome columns | 0.0 |
| total_points | raw current-GW outcome columns | 0.0 |
| transfers_balance | ownership/transfer features | 0.0 |
| transfers_in | ownership/transfer features | 0.0 |
| transfers_out | ownership/transfer features | 0.0 |
| winning_goals | raw current-GW outcome columns | 72.44 |
| yellow_cards | raw current-GW outcome columns | 0.0 |
| expected_assists | raw current-GW outcome columns | 56.92 |
| expected_goal_involvements | raw current-GW outcome columns | 56.92 |
| expected_goals | raw current-GW outcome columns | 56.92 |
| expected_goals_conceded | raw current-GW outcome columns | 56.92 |
| starts | raw current-GW outcome columns | 56.92 |
| mng_clean_sheets | raw current-GW outcome columns | 94.55 |
| mng_draw | raw current-GW outcome columns | 94.55 |
| mng_goals_scored | raw current-GW outcome columns | 94.55 |
| mng_loss | raw current-GW outcome columns | 94.55 |
| mng_underdog_draw | raw current-GW outcome columns | 94.55 |
| mng_underdog_win | raw current-GW outcome columns | 94.55 |
| mng_win | raw current-GW outcome columns | 94.55 |
| defensive_contribution | raw current-GW outcome columns | 90.93 |

## Recommendations

- Keep the current stable feature list unchanged until ablations are run.
- Treat raw current-GW outcomes as source columns only; add them through lagged or rolling transformations.
- Run the next ablation on supported seasons only: current stable set, then remove team form, remove Elo, and remove baseline prediction features.
- Investigate `was_home`, `value`, and transfer/ownership timing before using them directly.
