# Position Feature Mask Experiment

Opt-in comparison of the current feature setup against a model-specific position mask policy derived from `reports/position_feature_relevance.csv` and the relevance report. No wrapper search, broad ablation, or default model logic changes are performed.

Masks are applied only to linear and position-strategy models because the previous mask experiment showed gains for Ridge, ElasticNet, residual linear models, `global_plus_position_interactions`, and `position_wise_models`, while CatBoost/XGBoost results were mixed or harmful. Boosted models and the minutes-adjusted rolling-mean baseline therefore keep the current feature setup in this experiment.

## Model-Specific Policy

| policy | models |
| --- | --- |
| masked | Ridge, ElasticNet, residual_Ridge, residual_ElasticNet, global_plus_position_interactions, position_wise_models |
| unmasked_current_features | CatBoost, XGBoost, residual_CatBoost, residual_XGBoost, minutes_adjusted_rolling_mean |

## Position Masks

| position | feature_count | features |
| --- | --- | --- |
| GK | 20 | minutes_mean_last_3, minutes_mean_last_5, pred_minutes_adjusted_rolling_mean, pred_rolling_3_gameweek_mean, points_mean_last_3, influence_mean_last_3, ict_index_mean_last_3, pred_rolling_5_gameweek_mean, points_mean_last_5, bps_last_5, ict_index_mean_last_5, influence_mean_last_5, points_last_1, goals_conceded_mean_last_5, goals_conceded_mean_last_3, starts_last_5, expected_goals_conceded_mean_last_3, expected_goals_conceded_mean_last_5, clean_sheets_mean_last_5, selected_lag_1 |
| DEF | 20 | minutes_mean_last_3, minutes_mean_last_5, ict_index_mean_last_5, ict_index_mean_last_3, influence_mean_last_3, influence_mean_last_5, pred_minutes_adjusted_rolling_mean, bps_last_5, pred_rolling_5_gameweek_mean, points_mean_last_5, pred_rolling_3_gameweek_mean, points_mean_last_3, creativity_mean_last_3, creativity_mean_last_5, starts_last_5, goals_conceded_mean_last_5, threat_mean_last_5, points_last_1, goals_conceded_mean_last_3, threat_mean_last_3 |
| MID | 20 | minutes_mean_last_5, minutes_mean_last_3, ict_index_mean_last_5, ict_index_mean_last_3, pred_rolling_5_gameweek_mean, points_mean_last_5, pred_minutes_adjusted_rolling_mean, influence_mean_last_5, bps_last_5, pred_rolling_3_gameweek_mean, points_mean_last_3, influence_mean_last_3, creativity_mean_last_5, creativity_mean_last_3, threat_mean_last_5, threat_mean_last_3, points_last_1, expected_goal_involvements_mean_last_5, expected_goal_involvements_mean_last_3, goals_conceded_mean_last_5 |
| FWD | 20 | minutes_mean_last_5, minutes_mean_last_3, pred_minutes_adjusted_rolling_mean, pred_rolling_5_gameweek_mean, points_mean_last_5, pred_rolling_3_gameweek_mean, points_mean_last_3, ict_index_mean_last_5, ict_index_mean_last_3, threat_mean_last_5, influence_mean_last_5, bps_last_5, threat_mean_last_3, creativity_mean_last_5, creativity_mean_last_3, influence_mean_last_3, points_last_1, goals_conceded_mean_last_5, expected_goal_involvements_mean_last_5, expected_goals_conceded_mean_last_3 |

## Aggregate Comparison

Negative MAE/RMSE deltas are better. Positive Spearman and top-k deltas are better.

| model | current_mae | current_rmse | current_spearman | current_top_10_precision | current_top_20_precision | current_top_50_precision | policy_mae | policy_rmse | policy_spearman | policy_top_10_precision | policy_top_20_precision | policy_top_50_precision | delta_mae | delta_rmse | delta_spearman | delta_top_10_precision | delta_top_20_precision | delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Ridge | 1.1003 | 2.0250 | 0.6262 | 0.0667 | 0.0500 | 0.0600 | 1.0774 | 2.0188 | 0.6463 | 0.0333 | 0.0667 | 0.0733 | -0.0229 | -0.0061 | 0.0201 | -0.0333 | 0.0167 | 0.0133 |
| residual_Ridge | 1.0809 | 2.0093 | 0.6385 | 0.0667 | 0.0500 | 0.0600 | 1.0612 | 2.0052 | 0.6560 | 0.0333 | 0.0500 | 0.0733 | -0.0197 | -0.0041 | 0.0175 | -0.0333 | 0.0000 | 0.0133 |
| ElasticNet | 1.1037 | 2.0254 | 0.6256 | 0.0667 | 0.0667 | 0.0600 | 1.0845 | 2.0192 | 0.6476 | 0.0333 | 0.0333 | 0.0733 | -0.0192 | -0.0063 | 0.0220 | -0.0333 | -0.0333 | 0.0133 |
| residual_ElasticNet | 1.0885 | 2.0112 | 0.6366 | 0.0667 | 0.0667 | 0.0667 | 1.0698 | 2.0049 | 0.6564 | 0.0333 | 0.0500 | 0.0733 | -0.0187 | -0.0063 | 0.0199 | -0.0333 | -0.0167 | 0.0067 |
| position_wise_models | 1.0881 | 2.0250 | 0.6340 | 0.0333 | 0.0333 | 0.0600 | 1.0774 | 2.0188 | 0.6463 | 0.0333 | 0.0667 | 0.0733 | -0.0107 | -0.0062 | 0.0123 | 0.0000 | 0.0333 | 0.0133 |
| global_plus_position_interactions | 1.0819 | 2.0210 | 0.6357 | 0.0333 | 0.0333 | 0.0600 | 1.0737 | 2.0172 | 0.6469 | 0.0333 | 0.0500 | 0.0733 | -0.0082 | -0.0038 | 0.0112 | 0.0000 | 0.0167 | 0.0133 |
| CatBoost | 1.0595 | 2.0148 | 0.6494 | 0.0333 | 0.0167 | 0.0533 | 1.0595 | 2.0148 | 0.6494 | 0.0333 | 0.0167 | 0.0533 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| XGBoost | 1.0610 | 2.0166 | 0.6490 | 0.0333 | 0.0333 | 0.0600 | 1.0610 | 2.0166 | 0.6490 | 0.0333 | 0.0333 | 0.0600 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| minutes_adjusted_rolling_mean | 1.0098 | 2.1574 | 0.6715 | 0.0333 | 0.0667 | 0.0533 | 1.0098 | 2.1574 | 0.6715 | 0.0333 | 0.0667 | 0.0533 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| residual_CatBoost | 1.0466 | 2.0060 | 0.6551 | 0.0333 | 0.0167 | 0.0533 | 1.0466 | 2.0060 | 0.6551 | 0.0333 | 0.0167 | 0.0533 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| residual_XGBoost | 1.0487 | 2.0078 | 0.6537 | 0.0667 | 0.0333 | 0.0467 | 1.0487 | 2.0078 | 0.6537 | 0.0667 | 0.0333 | 0.0467 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

## Recommendation

Use this as a screening experiment only. Promote a mask only if it improves the target metric across rolling validation seasons and does not degrade the baseline comparison.
