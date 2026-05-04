# Ensemble Experiment

Opt-in rolling-origin experiment for convex weighted blends. Weights are non-negative, sum to 1, and are chosen from prior training-season inner-validation predictions only. The held-out validation season is never used to choose weights.

## Blend Members And Weights

| validation_season | model | blend_members | weights_json | weight_source |
| --- | --- | --- | --- | --- |
| 2023-24 | baseline_plus_residual_boost_blend | minutes_adjusted_rolling_mean, residual_CatBoost, residual_XGBoost | {"minutes_adjusted_rolling_mean": 0.333333, "residual_CatBoost": 0.333333, "residual_XGBoost": 0.333333} | fallback_preset |
| 2023-24 | equal_weight_top_models | minutes_adjusted_rolling_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost | {"minutes_adjusted_rolling_mean": 0.25, "residual_CatBoost": 0.25, "residual_XGBoost": 0.25, "rolling_5_gameweek_mean": 0.25} | fixed |
| 2023-24 | minutes_adjusted_only | minutes_adjusted_rolling_mean | {"minutes_adjusted_rolling_mean": 1.0} | fixed |
| 2023-24 | optimized_mae_blend | minutes_adjusted_rolling_mean, rolling_3_gameweek_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost, residual_Ridge, residual_ElasticNet, CatBoost, XGBoost | {"CatBoost": 0.111111, "XGBoost": 0.111111, "minutes_adjusted_rolling_mean": 0.111111, "residual_CatBoost": 0.111111, "residual_ElasticNet": 0.111111, "residual_Ridge": 0.111111, "residual_XGBoost": 0.111111, "rolling_3_gameweek_mean": 0.111111, "rolling_5_gameweek_mean": 0.111111} | fallback_preset |
| 2023-24 | optimized_rmse_blend | minutes_adjusted_rolling_mean, rolling_3_gameweek_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost, residual_Ridge, residual_ElasticNet, CatBoost, XGBoost | {"CatBoost": 0.111111, "XGBoost": 0.111111, "minutes_adjusted_rolling_mean": 0.111111, "residual_CatBoost": 0.111111, "residual_ElasticNet": 0.111111, "residual_Ridge": 0.111111, "residual_XGBoost": 0.111111, "rolling_3_gameweek_mean": 0.111111, "rolling_5_gameweek_mean": 0.111111} | fallback_preset |
| 2023-24 | optimized_spearman_blend | minutes_adjusted_rolling_mean, rolling_3_gameweek_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost, residual_Ridge, residual_ElasticNet, CatBoost, XGBoost | {"CatBoost": 0.111111, "XGBoost": 0.111111, "minutes_adjusted_rolling_mean": 0.111111, "residual_CatBoost": 0.111111, "residual_ElasticNet": 0.111111, "residual_Ridge": 0.111111, "residual_XGBoost": 0.111111, "rolling_3_gameweek_mean": 0.111111, "rolling_5_gameweek_mean": 0.111111} | fallback_preset |
| 2024-25 | baseline_plus_residual_boost_blend | minutes_adjusted_rolling_mean, residual_CatBoost, residual_XGBoost | {"minutes_adjusted_rolling_mean": 0.841557, "residual_CatBoost": 0.137798, "residual_XGBoost": 0.020645} | inner_validation |
| 2024-25 | equal_weight_top_models | minutes_adjusted_rolling_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost | {"minutes_adjusted_rolling_mean": 0.25, "residual_CatBoost": 0.25, "residual_XGBoost": 0.25, "rolling_5_gameweek_mean": 0.25} | fixed |
| 2024-25 | minutes_adjusted_only | minutes_adjusted_rolling_mean | {"minutes_adjusted_rolling_mean": 1.0} | fixed |
| 2024-25 | optimized_mae_blend | minutes_adjusted_rolling_mean, rolling_3_gameweek_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost, residual_Ridge, residual_ElasticNet, CatBoost, XGBoost | {"CatBoost": 0.0, "XGBoost": 0.0, "minutes_adjusted_rolling_mean": 1.0, "residual_CatBoost": 0.0, "residual_ElasticNet": 0.0, "residual_Ridge": 0.0, "residual_XGBoost": 0.0, "rolling_3_gameweek_mean": 0.0, "rolling_5_gameweek_mean": 0.0} | inner_validation |
| 2024-25 | optimized_rmse_blend | minutes_adjusted_rolling_mean, rolling_3_gameweek_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost, residual_Ridge, residual_ElasticNet, CatBoost, XGBoost | {"CatBoost": 0.091406, "XGBoost": 0.221327, "minutes_adjusted_rolling_mean": 0.068362, "residual_CatBoost": 0.027858, "residual_ElasticNet": 0.106198, "residual_Ridge": 0.406358, "residual_XGBoost": 0.012942, "rolling_3_gameweek_mean": 0.03182, "rolling_5_gameweek_mean": 0.033729} | inner_validation |
| 2024-25 | optimized_spearman_blend | minutes_adjusted_rolling_mean, rolling_3_gameweek_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost, residual_Ridge, residual_ElasticNet, CatBoost, XGBoost | {"CatBoost": 0.0, "XGBoost": 0.0, "minutes_adjusted_rolling_mean": 1.0, "residual_CatBoost": 0.0, "residual_ElasticNet": 0.0, "residual_Ridge": 0.0, "residual_XGBoost": 0.0, "rolling_3_gameweek_mean": 0.0, "rolling_5_gameweek_mean": 0.0} | inner_validation |
| 2025-26 | baseline_plus_residual_boost_blend | minutes_adjusted_rolling_mean, residual_CatBoost, residual_XGBoost | {"minutes_adjusted_rolling_mean": 0.74071, "residual_CatBoost": 0.224345, "residual_XGBoost": 0.034945} | inner_validation |
| 2025-26 | equal_weight_top_models | minutes_adjusted_rolling_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost | {"minutes_adjusted_rolling_mean": 0.25, "residual_CatBoost": 0.25, "residual_XGBoost": 0.25, "rolling_5_gameweek_mean": 0.25} | fixed |
| 2025-26 | minutes_adjusted_only | minutes_adjusted_rolling_mean | {"minutes_adjusted_rolling_mean": 1.0} | fixed |
| 2025-26 | optimized_mae_blend | minutes_adjusted_rolling_mean, rolling_3_gameweek_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost, residual_Ridge, residual_ElasticNet, CatBoost, XGBoost | {"CatBoost": 0.0, "XGBoost": 0.0, "minutes_adjusted_rolling_mean": 1.0, "residual_CatBoost": 0.0, "residual_ElasticNet": 0.0, "residual_Ridge": 0.0, "residual_XGBoost": 0.0, "rolling_3_gameweek_mean": 0.0, "rolling_5_gameweek_mean": 0.0} | inner_validation |
| 2025-26 | optimized_rmse_blend | minutes_adjusted_rolling_mean, rolling_3_gameweek_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost, residual_Ridge, residual_ElasticNet, CatBoost, XGBoost | {"CatBoost": 0.387231, "XGBoost": 0.047124, "minutes_adjusted_rolling_mean": 0.001608, "residual_CatBoost": 0.172986, "residual_ElasticNet": 0.186373, "residual_Ridge": 0.023023, "residual_XGBoost": 0.10723, "rolling_3_gameweek_mean": 0.004116, "rolling_5_gameweek_mean": 0.070308} | inner_validation |
| 2025-26 | optimized_spearman_blend | minutes_adjusted_rolling_mean, rolling_3_gameweek_mean, rolling_5_gameweek_mean, residual_CatBoost, residual_XGBoost, residual_Ridge, residual_ElasticNet, CatBoost, XGBoost | {"CatBoost": 0.0, "XGBoost": 0.0, "minutes_adjusted_rolling_mean": 1.0, "residual_CatBoost": 0.0, "residual_ElasticNet": 0.0, "residual_Ridge": 0.0, "residual_XGBoost": 0.0, "rolling_3_gameweek_mean": 0.0, "rolling_5_gameweek_mean": 0.0} | inner_validation |

## Aggregate Results

| blend_type | model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| base_model_reference | minutes_adjusted_rolling_mean | 1.0098 | 2.1574 | 0.6715 | 0.0333 | 0.0667 | 0.0533 |
| base_model_reference | residual_CatBoost | 1.0466 | 2.0060 | 0.6551 | 0.0333 | 0.0167 | 0.0533 |
| base_model_reference | residual_XGBoost | 1.0487 | 2.0078 | 0.6537 | 0.0667 | 0.0333 | 0.0467 |
| base_model_reference | CatBoost | 1.0595 | 2.0148 | 0.6494 | 0.0333 | 0.0167 | 0.0533 |
| base_model_reference | XGBoost | 1.0610 | 2.0166 | 0.6490 | 0.0333 | 0.0333 | 0.0600 |
| base_model_reference | rolling_5_gameweek_mean | 1.0739 | 2.1438 | 0.6661 | 0.0333 | 0.0667 | 0.0667 |
| base_model_reference | residual_Ridge | 1.0809 | 2.0093 | 0.6385 | 0.0667 | 0.0500 | 0.0600 |
| base_model_reference | residual_ElasticNet | 1.0885 | 2.0112 | 0.6366 | 0.0667 | 0.0667 | 0.0667 |
| base_model_reference | rolling_3_gameweek_mean | 1.0904 | 2.2164 | 0.6647 | 0.0667 | 0.0500 | 0.0533 |
| ensemble | baseline_plus_residual_boost_blend | 1.0095 | 2.0779 | 0.6478 | 0.0667 | 0.0667 | 0.0600 |
| ensemble | minutes_adjusted_only | 1.0098 | 2.1574 | 0.6715 | 0.0333 | 0.0667 | 0.0533 |
| ensemble | equal_weight_top_models | 1.0197 | 2.0347 | 0.6493 | 0.0667 | 0.0333 | 0.0667 |
| ensemble | optimized_mae_blend | 1.0283 | 2.1158 | 0.6637 | 0.0667 | 0.0667 | 0.0533 |
| ensemble | optimized_spearman_blend | 1.0283 | 2.1158 | 0.6637 | 0.0667 | 0.0667 | 0.0533 |
| ensemble | optimized_rmse_blend | 1.0425 | 2.0048 | 0.6524 | 0.0667 | 0.0333 | 0.0600 |

## Best Ensembles

| metric | best_ensemble | value |
| --- | --- | --- |
| mae | baseline_plus_residual_boost_blend | 1.0095 |
| rmse | optimized_rmse_blend | 2.0048 |
| spearman | minutes_adjusted_only | 0.6715 |
| top_10_precision | baseline_plus_residual_boost_blend | 0.0667 |
| top_20_precision | baseline_plus_residual_boost_blend | 0.0667 |
| top_50_precision | equal_weight_top_models | 0.0667 |

## Checks

- Any ensemble beats `minutes_adjusted_rolling_mean` on MAE: yes.
- Any ensemble beats `residual_CatBoost` on RMSE: yes.
- Any ensemble improves top-k precision over the best base candidate: no.

## Recommendation

Consider the best MAE ensemble for a follow-up default-model test.
