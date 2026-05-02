# Supported-Season Filter Report

Minimum season: `2020-21`.

## Seasons

Included: 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26

Excluded:

- `2016-17`: season is earlier than min-season 2020-21
- `2017-18`: season is earlier than min-season 2020-21
- `2018-19`: season is earlier than min-season 2020-21
- `2019-20`: season is earlier than min-season 2020-21

## Team-Strength Feature Coverage

| feature | full_non_null_rate | filtered_non_null_rate |
| --- | --- | --- |
| team_elo_pre_gw | 0.6329 | 1.0000 |
| opponent_elo_pre_gw | 0.6329 | 1.0000 |
| elo_difference | 0.6329 | 1.0000 |
| home_adjusted_elo_difference | 0.6329 | 1.0000 |
| team_goals_scored_mean_last_5 | 0.6182 | 0.9767 |
| team_goals_conceded_mean_last_5 | 0.6182 | 0.9767 |
| opponent_goals_scored_mean_last_5 | 0.6182 | 0.9768 |
| opponent_goals_conceded_mean_last_5 | 0.6182 | 0.9768 |
| team_clean_sheet_rate_last_5 | 0.6182 | 0.9767 |
| opponent_clean_sheet_rate_last_5 | 0.6182 | 0.9768 |

## Best Filtered Models

| metric | best_model | score |
| --- | --- | --- |
| mae | minutes_adjusted_rolling_mean | 1.0572 |
| rmse | residual_Ridge | 2.0612 |
| spearman | minutes_adjusted_rolling_mean | 0.6568 |
| top_10_precision | rolling_3_gameweek_mean | 0.0600 |
| top_20_precision | Ridge | 0.0300 |
| top_50_precision | rolling_5_gameweek_mean | 0.0520 |

## Metric-Level Filtering Impact

| metric | full_best_model | full_score | filtered_best_model | filtered_score | delta | improved |
| --- | --- | --- | --- | --- | --- | --- |
| mae | minutes_adjusted_rolling_mean | 1.1355 | minutes_adjusted_rolling_mean | 1.0572 | -0.0783 | yes |
| rmse | residual_CatBoost | 2.1269 | residual_Ridge | 2.0612 | -0.0657 | yes |
| spearman | residual_CatBoost | 0.6459 | minutes_adjusted_rolling_mean | 0.6568 | 0.0108 | yes |
| top_10_precision | rolling_3_gameweek_mean | 0.0333 | rolling_3_gameweek_mean | 0.0600 | 0.0267 | yes |
| top_20_precision | residual_CatBoost | 0.0278 | Ridge | 0.0300 | 0.0022 | yes |
| top_50_precision | rolling_5_gameweek_mean | 0.0467 | rolling_5_gameweek_mean | 0.0520 | 0.0053 | yes |

## Full-History Versus Supported-Season Models

Positive deltas mean the metric increased after filtering; for MAE/RMSE that is worse, for Spearman and precision that is better.

| model | full_mae | filtered_mae | delta_mae | full_rmse | filtered_rmse | delta_rmse | full_spearman | filtered_spearman | delta_spearman | full_top_10_precision | filtered_top_10_precision | delta_top_10_precision | full_top_20_precision | filtered_top_20_precision | delta_top_20_precision | full_top_50_precision | filtered_top_50_precision | delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| residual_CatBoost | 1.1790 | 1.1035 | -0.0756 | 2.1269 | 2.0615 | -0.0655 | 0.6459 | 0.6485 | 0.0026 | 0.0000 | 0.0000 | 0.0000 | 0.0278 | 0.0100 | -0.0178 | 0.0356 | 0.0240 | -0.0116 |
| residual_LightGBM | 1.1870 | 1.1116 | -0.0755 | 2.1469 | 2.0820 | -0.0649 | 0.6386 | 0.6409 | 0.0023 | 0.0111 | 0.0000 | -0.0111 | 0.0222 | 0.0000 | -0.0222 | 0.0200 | 0.0240 | 0.0040 |
| residual_XGBoost | 1.1800 | 1.1042 | -0.0758 | 2.1288 | 2.0626 | -0.0663 | 0.6441 | 0.6461 | 0.0019 | 0.0111 | 0.0000 | -0.0111 | 0.0222 | 0.0200 | -0.0022 | 0.0333 | 0.0240 | -0.0093 |
| minutes_adjusted_rolling_mean | 1.1355 | 1.0572 | -0.0783 | 2.2977 | 2.2244 | -0.0733 | 0.6422 | 0.6568 | 0.0145 | 0.0111 | 0.0200 | 0.0089 | 0.0222 | 0.0200 | -0.0022 | 0.0400 | 0.0440 | 0.0040 |

## Global Plus Position Interactions

| strategy | full_mae | filtered_mae | delta_mae | full_rmse | filtered_rmse | delta_rmse | full_spearman | filtered_spearman | delta_spearman | full_top_10_precision | filtered_top_10_precision | delta_top_10_precision | full_top_20_precision | filtered_top_20_precision | delta_top_20_precision | full_top_50_precision | filtered_top_50_precision | delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_plus_position_interactions | 1.1251 | 1.1279 | 0.0028 | 2.0564 | 2.0564 | 0.0000 | 0.6329 | 0.6316 | -0.0014 | 0.0200 | 0.0200 | 0.0000 | 0.0200 | 0.0200 | 0.0000 | 0.0360 | 0.0360 | 0.0000 |

## Interpretation

- Filtering removes early seasons where team and position identifiers are unsupported.
- The supported-season run uses fewer training rows, so worse MAE/RMSE can indicate that reduced history hurts more than cleaner team-strength coverage helps.
- Team-strength features are more consistently available after filtering because the retained seasons have reliable normalized team/opponent IDs.
