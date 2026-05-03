# Supported-Season Filter Report

Minimum season: `2022-23`.

## Seasons

Included: 2022-23, 2023-24, 2024-25, 2025-26

Excluded:

- None

## Team-Strength Feature Coverage

| feature | full_non_null_rate | filtered_non_null_rate |
| --- | --- | --- |
| team_elo_pre_gw | 1.0000 | 1.0000 |
| opponent_elo_pre_gw | 1.0000 | 1.0000 |
| elo_difference | 1.0000 | 1.0000 |
| home_adjusted_elo_difference | 1.0000 | 1.0000 |
| team_goals_scored_mean_last_5 | 0.9760 | 0.9760 |
| team_goals_conceded_mean_last_5 | 0.9760 | 0.9760 |
| opponent_goals_scored_mean_last_5 | 0.9760 | 0.9760 |
| opponent_goals_conceded_mean_last_5 | 0.9760 | 0.9760 |
| team_clean_sheet_rate_last_5 | 0.9760 | 0.9760 |
| opponent_clean_sheet_rate_last_5 | 0.9760 | 0.9760 |

## Best Filtered Models

| metric | best_model | score |
| --- | --- | --- |
| mae | minutes_adjusted_rolling_mean | 1.0098 |
| rmse | residual_CatBoost | 2.0062 |
| spearman | minutes_adjusted_rolling_mean | 0.6715 |
| top_10_precision | two_stage_minutes_points | 0.1000 |
| top_20_precision | ElasticNet | 0.0667 |
| top_50_precision | CatBoost | 0.0733 |

## Metric-Level Filtering Impact

| metric | full_best_model | full_score | filtered_best_model | filtered_score | delta | improved |
| --- | --- | --- | --- | --- | --- | --- |
| mae | minutes_adjusted_rolling_mean | 1.0098 | minutes_adjusted_rolling_mean | 1.0098 | 0.0000 | no |
| rmse | residual_CatBoost | 2.0062 | residual_CatBoost | 2.0062 | 0.0000 | no |
| spearman | minutes_adjusted_rolling_mean | 0.6715 | minutes_adjusted_rolling_mean | 0.6715 | 0.0000 | no |
| top_10_precision | two_stage_minutes_points | 0.1000 | two_stage_minutes_points | 0.1000 | 0.0000 | no |
| top_20_precision | ElasticNet | 0.0667 | ElasticNet | 0.0667 | 0.0000 | no |
| top_50_precision | CatBoost | 0.0733 | CatBoost | 0.0733 | 0.0000 | no |

## Full-History Versus Supported-Season Models

Positive deltas mean the metric increased after filtering; for MAE/RMSE that is worse, for Spearman and precision that is better.

| model | full_mae | filtered_mae | delta_mae | full_rmse | filtered_rmse | delta_rmse | full_spearman | filtered_spearman | delta_spearman | full_top_10_precision | filtered_top_10_precision | delta_top_10_precision | full_top_20_precision | filtered_top_20_precision | delta_top_20_precision | full_top_50_precision | filtered_top_50_precision | delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| residual_CatBoost | 1.0487 | 1.0487 | 0.0000 | 2.0062 | 2.0062 | 0.0000 | 0.6549 | 0.6549 | 0.0000 | 0.0667 | 0.0667 | 0.0000 | 0.0333 | 0.0333 | 0.0000 | 0.0667 | 0.0667 | 0.0000 |
| residual_XGBoost | 1.0484 | 1.0484 | 0.0000 | 2.0076 | 2.0076 | 0.0000 | 0.6538 | 0.6538 | 0.0000 | 0.0667 | 0.0667 | 0.0000 | 0.0333 | 0.0333 | 0.0000 | 0.0400 | 0.0400 | 0.0000 |
| minutes_adjusted_rolling_mean | 1.0098 | 1.0098 | 0.0000 | 2.1574 | 2.1574 | 0.0000 | 0.6715 | 0.6715 | 0.0000 | 0.0333 | 0.0333 | 0.0000 | 0.0667 | 0.0667 | 0.0000 | 0.0533 | 0.0533 | 0.0000 |

## Global Plus Position Interactions

| strategy | full_mae | filtered_mae | delta_mae | full_rmse | filtered_rmse | delta_rmse | full_spearman | filtered_spearman | delta_spearman | full_top_10_precision | filtered_top_10_precision | delta_top_10_precision | full_top_20_precision | filtered_top_20_precision | delta_top_20_precision | full_top_50_precision | filtered_top_50_precision | delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_plus_position_interactions | 1.0819 | 1.0819 | 0.0000 | 2.0210 | 2.0210 | 0.0000 | 0.6357 | 0.6357 | 0.0000 | 0.0333 | 0.0333 | 0.0000 | 0.0333 | 0.0333 | 0.0000 | 0.0600 | 0.0600 | 0.0000 |

## Interpretation

- Filtering removes early seasons where team and position identifiers are unsupported.
- The supported-season run uses fewer training rows, so worse MAE/RMSE can indicate that reduced history hurts more than cleaner team-strength coverage helps.
- Team-strength features are more consistently available after filtering because the retained seasons have reliable normalized team/opponent IDs.
