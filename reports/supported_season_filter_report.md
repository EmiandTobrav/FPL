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
| team_elo_pre_gw | 0.6324 | 1.0000 |
| opponent_elo_pre_gw | 0.6324 | 1.0000 |
| elo_difference | 0.6324 | 1.0000 |
| home_adjusted_elo_difference | 0.6324 | 1.0000 |
| team_goals_scored_mean_last_5 | 0.6177 | 0.9767 |
| team_goals_conceded_mean_last_5 | 0.6177 | 0.9767 |
| opponent_goals_scored_mean_last_5 | 0.6177 | 0.9767 |
| opponent_goals_conceded_mean_last_5 | 0.6177 | 0.9767 |
| team_clean_sheet_rate_last_5 | 0.6177 | 0.9767 |
| opponent_clean_sheet_rate_last_5 | 0.6177 | 0.9767 |

## Best Filtered Models

| metric | best_model | score |
| --- | --- | --- |
| mae | minutes_adjusted_rolling_mean | 1.0469 |
| rmse | residual_CatBoost | 2.0364 |
| spearman | minutes_adjusted_rolling_mean | 0.6616 |
| top_10_precision | rolling_3_gameweek_mean | 0.0600 |
| top_20_precision | rolling_5_gameweek_mean | 0.0500 |
| top_50_precision | rolling_5_gameweek_mean | 0.0560 |

## Metric-Level Filtering Impact

| metric | full_best_model | full_score | filtered_best_model | filtered_score | delta | improved |
| --- | --- | --- | --- | --- | --- | --- |
| mae | minutes_adjusted_rolling_mean | 1.1298 | minutes_adjusted_rolling_mean | 1.0469 | -0.0828 | yes |
| rmse | residual_CatBoost | 2.1150 | residual_CatBoost | 2.0364 | -0.0786 | yes |
| spearman | residual_CatBoost | 0.6463 | minutes_adjusted_rolling_mean | 0.6616 | 0.0153 | yes |
| top_10_precision | rolling_3_gameweek_mean | 0.0333 | rolling_3_gameweek_mean | 0.0600 | 0.0267 | yes |
| top_20_precision | rolling_5_gameweek_mean | 0.0389 | rolling_5_gameweek_mean | 0.0500 | 0.0111 | yes |
| top_50_precision | rolling_5_gameweek_mean | 0.0489 | rolling_5_gameweek_mean | 0.0560 | 0.0071 | yes |

## Full-History Versus Supported-Season Models

Positive deltas mean the metric increased after filtering; for MAE/RMSE that is worse, for Spearman and precision that is better.

| model | full_mae | filtered_mae | delta_mae | full_rmse | filtered_rmse | delta_rmse | full_spearman | filtered_spearman | delta_spearman | full_top_10_precision | filtered_top_10_precision | delta_top_10_precision | full_top_20_precision | filtered_top_20_precision | delta_top_20_precision | full_top_50_precision | filtered_top_50_precision | delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| residual_CatBoost | 1.1755 | 1.0941 | -0.0813 | 2.1150 | 2.0364 | -0.0786 | 0.6463 | 0.6509 | 0.0046 | 0.0000 | 0.0000 | 0.0000 | 0.0222 | 0.0100 | -0.0122 | 0.0378 | 0.0240 | -0.0138 |
| residual_LightGBM | 1.1827 | 1.1018 | -0.0808 | 2.1327 | 2.0551 | -0.0776 | 0.6401 | 0.6443 | 0.0042 | 0.0111 | 0.0000 | -0.0111 | 0.0167 | 0.0000 | -0.0167 | 0.0178 | 0.0240 | 0.0062 |
| residual_XGBoost | 1.1756 | 1.0946 | -0.0810 | 2.1163 | 2.0391 | -0.0772 | 0.6449 | 0.6483 | 0.0034 | 0.0111 | 0.0000 | -0.0111 | 0.0222 | 0.0200 | -0.0022 | 0.0378 | 0.0240 | -0.0138 |
| minutes_adjusted_rolling_mean | 1.1298 | 1.0469 | -0.0828 | 2.2827 | 2.1975 | -0.0853 | 0.6449 | 0.6616 | 0.0167 | 0.0111 | 0.0200 | 0.0089 | 0.0333 | 0.0400 | 0.0067 | 0.0400 | 0.0440 | 0.0040 |

## Global Plus Position Interactions

| strategy | full_mae | filtered_mae | delta_mae | full_rmse | filtered_rmse | delta_rmse | full_spearman | filtered_spearman | delta_spearman | full_top_10_precision | filtered_top_10_precision | delta_top_10_precision | full_top_20_precision | filtered_top_20_precision | delta_top_20_precision | full_top_50_precision | filtered_top_50_precision | delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_plus_position_interactions | 1.1279 | 1.1279 | -0.0000 | 2.0564 | 2.0564 | 0.0000 | 0.6316 | 0.6316 | 0.0000 | 0.0200 | 0.0200 | 0.0000 | 0.0200 | 0.0200 | 0.0000 | 0.0360 | 0.0360 | 0.0000 |

## Interpretation

- Filtering removes early seasons where team and position identifiers are unsupported.
- The supported-season run uses fewer training rows, so worse MAE/RMSE can indicate that reduced history hurts more than cleaner team-strength coverage helps.
- Team-strength features are more consistently available after filtering because the retained seasons have reliable normalized team/opponent IDs.
