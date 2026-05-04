# Ensemble Validation Report

Scope: validation of the opt-in ensemble experiment from `reports/ensemble_results.csv` and `reports/ensemble_report.md`, compared with normal model reports. Default model behavior was not changed.

## Data Availability

- The ensemble output contains season-level metrics and position-specific top-k ranking metrics.
- It does not contain row-level predictions or a `gw` column, so GW1-5, GW6-10, and GW11+ metrics cannot be computed from the current saved reports.
- It also does not contain per-position MAE/RMSE/Spearman, only position-specific top-k precision and average actual points.

## Ensemble Performance By Validation Season

| validation_season | model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-24 | minutes_adjusted_only | 0.9648 | 2.1318 | 0.6578 | 0.0000 | 0.0500 | 0.0400 |
| 2023-24 | baseline_plus_residual_boost_blend | 0.9904 | 2.0149 | 0.6342 | 0.1000 | 0.0500 | 0.0600 |
| 2023-24 | equal_weight_top_models | 0.9938 | 2.0249 | 0.6326 | 0.1000 | 0.0500 | 0.0600 |
| 2023-24 | optimized_mae_blend | 1.0203 | 2.0069 | 0.6343 | 0.1000 | 0.0500 | 0.0400 |
| 2023-24 | optimized_rmse_blend | 1.0203 | 2.0069 | 0.6343 | 0.1000 | 0.0500 | 0.0400 |
| 2023-24 | optimized_spearman_blend | 1.0203 | 2.0069 | 0.6343 | 0.1000 | 0.0500 | 0.0400 |
| 2024-25 | baseline_plus_residual_boost_blend | 1.0093 | 2.0872 | 0.6497 | 0.1000 | 0.1500 | 0.1000 |
| 2024-25 | minutes_adjusted_only | 1.0168 | 2.1315 | 0.6680 | 0.1000 | 0.1500 | 0.1000 |
| 2024-25 | optimized_mae_blend | 1.0168 | 2.1315 | 0.6680 | 0.1000 | 0.1500 | 0.1000 |
| 2024-25 | optimized_spearman_blend | 1.0168 | 2.1315 | 0.6680 | 0.1000 | 0.1500 | 0.1000 |
| 2024-25 | equal_weight_top_models | 1.0261 | 2.0100 | 0.6542 | 0.1000 | 0.0500 | 0.1200 |
| 2024-25 | optimized_rmse_blend | 1.0550 | 1.9851 | 0.6550 | 0.1000 | 0.0500 | 0.1200 |
| 2025-26 | baseline_plus_residual_boost_blend | 1.0288 | 2.1316 | 0.6594 | 0.0000 | 0.0000 | 0.0200 |
| 2025-26 | equal_weight_top_models | 1.0392 | 2.0692 | 0.6611 | 0.0000 | 0.0000 | 0.0200 |
| 2025-26 | minutes_adjusted_only | 1.0478 | 2.2088 | 0.6886 | 0.0000 | 0.0000 | 0.0200 |
| 2025-26 | optimized_mae_blend | 1.0478 | 2.2088 | 0.6886 | 0.0000 | 0.0000 | 0.0200 |
| 2025-26 | optimized_spearman_blend | 1.0478 | 2.2088 | 0.6886 | 0.0000 | 0.0000 | 0.0200 |
| 2025-26 | optimized_rmse_blend | 1.0524 | 2.0224 | 0.6679 | 0.0000 | 0.0000 | 0.0200 |

## Early Gameweek Performance

Not computable from the current artifacts. `reports/ensemble_results.csv` has no gameweek column and no row-level predictions. To validate early-gameweek behavior later, the ensemble experiment should persist prediction rows with `season`, `gw`, `model`, `actual`, and `prediction`, or add GW-bin aggregate rows directly.

## Position Ranking Performance

| model | GK_top_10_precision | GK_top_20_precision | GK_top_50_precision | DEF_top_10_precision | DEF_top_20_precision | DEF_top_50_precision | MID_top_10_precision | MID_top_20_precision | MID_top_50_precision | FWD_top_10_precision | FWD_top_20_precision | FWD_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_plus_residual_boost_blend | 0.0000 | 0.0167 | 0.0933 | 0.0000 | 0.0000 | 0.0133 | 0.0667 | 0.0833 | 0.0800 | 0.0000 | 0.1000 | 0.1533 |
| equal_weight_top_models | 0.0000 | 0.0167 | 0.0867 | 0.0000 | 0.0000 | 0.0200 | 0.0667 | 0.0500 | 0.0800 | 0.0333 | 0.1167 | 0.1600 |
| minutes_adjusted_only | 0.0000 | 0.0167 | 0.1000 | 0.0000 | 0.0000 | 0.0133 | 0.0667 | 0.0833 | 0.0733 | 0.0000 | 0.1000 | 0.1533 |
| optimized_mae_blend | 0.0000 | 0.0167 | 0.0867 | 0.0000 | 0.0000 | 0.0133 | 0.0667 | 0.0833 | 0.0800 | 0.0000 | 0.1000 | 0.1600 |
| optimized_rmse_blend | 0.0000 | 0.0000 | 0.0733 | 0.0000 | 0.0000 | 0.0200 | 0.0667 | 0.0500 | 0.0867 | 0.0333 | 0.1000 | 0.1667 |
| optimized_spearman_blend | 0.0000 | 0.0167 | 0.0867 | 0.0000 | 0.0000 | 0.0133 | 0.0667 | 0.0833 | 0.0800 | 0.0000 | 0.1000 | 0.1600 |

Position-specific MAE/RMSE/Spearman are not available in the saved ensemble report; the table above covers within-position ranking precision only.

## Baseline Plus Residual Boost Consistency

| validation_season | blend_mae | minutes_mae | mae_delta_vs_minutes | blend_rmse | blend_spearman | minutes_spearman | spearman_delta_vs_minutes | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-24 | 0.9904 | 0.9648 | 0.0255 | 2.0149 | 0.6342 | 0.6578 | -0.0236 | 0.1000 | 0.0500 | 0.0600 |
| 2024-25 | 1.0093 | 1.0168 | -0.0075 | 2.0872 | 0.6497 | 0.6680 | -0.0184 | 0.1000 | 0.1500 | 0.1000 |
| 2025-26 | 1.0288 | 1.0478 | -0.0190 | 2.1316 | 0.6594 | 0.6886 | -0.0292 | 0.0000 | 0.0000 | 0.0200 |

- `baseline_plus_residual_boost_blend` improves MAE in 2024-25 and 2025-26, but hurts MAE in 2023-24.
- The average MAE gain is therefore not season-consistent; it comes from two later-season gains overcoming the first-season loss.
- It materially hurts Spearman versus `minutes_adjusted_only` in every season, with the largest drop in 2025-26.

## Optimized RMSE Blend Consistency

| validation_season | blend_rmse | residual_catboost_rmse | rmse_delta_vs_residual_catboost | blend_mae | blend_spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-24 | 2.0069 | 2.0118 | -0.0049 | 1.0203 | 0.6343 | 0.1000 | 0.0500 | 0.0400 |
| 2024-25 | 1.9851 | 1.9832 | 0.0019 | 1.0550 | 0.6550 | 0.1000 | 0.0500 | 0.1200 |
| 2025-26 | 2.0224 | 2.0231 | -0.0007 | 1.0524 | 0.6679 | 0.0000 | 0.0000 | 0.0200 |

- `optimized_rmse_blend` beats `residual_CatBoost` on RMSE in 2023-24 and 2025-26, but is slightly worse in 2024-25.
- Its average RMSE improvement is not fully consistent by season, though it is directionally useful as an RMSE specialist.
- Its MAE and Spearman are weaker than the strongest baseline, so it should not be treated as the primary expected-points model.

## Weight Stability

| validation_season | ensemble | source | CatBoost | XGBoost | minutes_adjusted_rolling_mean | residual_CatBoost | residual_ElasticNet | residual_Ridge | residual_XGBoost | rolling_3_gameweek_mean | rolling_5_gameweek_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-24 | baseline_plus_residual_boost_blend | fallback_preset | 0.0000 | 0.0000 | 0.3333 | 0.3333 | 0.0000 | 0.0000 | 0.3333 | 0.0000 | 0.0000 |
| 2023-24 | equal_weight_top_models | fixed | 0.0000 | 0.0000 | 0.2500 | 0.2500 | 0.0000 | 0.0000 | 0.2500 | 0.0000 | 0.2500 |
| 2023-24 | minutes_adjusted_only | fixed | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2023-24 | optimized_mae_blend | fallback_preset | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 |
| 2023-24 | optimized_rmse_blend | fallback_preset | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 |
| 2023-24 | optimized_spearman_blend | fallback_preset | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 | 0.1111 |
| 2024-25 | baseline_plus_residual_boost_blend | inner_validation | 0.0000 | 0.0000 | 0.8416 | 0.1378 | 0.0000 | 0.0000 | 0.0206 | 0.0000 | 0.0000 |
| 2024-25 | equal_weight_top_models | fixed | 0.0000 | 0.0000 | 0.2500 | 0.2500 | 0.0000 | 0.0000 | 0.2500 | 0.0000 | 0.2500 |
| 2024-25 | minutes_adjusted_only | fixed | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2024-25 | optimized_mae_blend | inner_validation | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2024-25 | optimized_rmse_blend | inner_validation | 0.0914 | 0.2213 | 0.0684 | 0.0279 | 0.1062 | 0.4064 | 0.0129 | 0.0318 | 0.0337 |
| 2024-25 | optimized_spearman_blend | inner_validation | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2025-26 | baseline_plus_residual_boost_blend | inner_validation | 0.0000 | 0.0000 | 0.7407 | 0.2243 | 0.0000 | 0.0000 | 0.0349 | 0.0000 | 0.0000 |
| 2025-26 | equal_weight_top_models | fixed | 0.0000 | 0.0000 | 0.2500 | 0.2500 | 0.0000 | 0.0000 | 0.2500 | 0.0000 | 0.2500 |
| 2025-26 | minutes_adjusted_only | fixed | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2025-26 | optimized_mae_blend | inner_validation | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| 2025-26 | optimized_rmse_blend | inner_validation | 0.3872 | 0.0471 | 0.0016 | 0.1730 | 0.1864 | 0.0230 | 0.1072 | 0.0041 | 0.0703 |
| 2025-26 | optimized_spearman_blend | inner_validation | 0.0000 | 0.0000 | 1.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |

### Weight Summary

| ensemble | member | mean_weight | std_weight | min_weight | max_weight |
| --- | --- | --- | --- | --- | --- |
| baseline_plus_residual_boost_blend | minutes_adjusted_rolling_mean | 0.6385 | 0.2691 | 0.3333 | 0.8416 |
| baseline_plus_residual_boost_blend | residual_CatBoost | 0.2318 | 0.0980 | 0.1378 | 0.3333 |
| baseline_plus_residual_boost_blend | residual_XGBoost | 0.1296 | 0.1765 | 0.0206 | 0.3333 |
| equal_weight_top_models | minutes_adjusted_rolling_mean | 0.2500 | 0.0000 | 0.2500 | 0.2500 |
| equal_weight_top_models | residual_CatBoost | 0.2500 | 0.0000 | 0.2500 | 0.2500 |
| equal_weight_top_models | residual_XGBoost | 0.2500 | 0.0000 | 0.2500 | 0.2500 |
| equal_weight_top_models | rolling_5_gameweek_mean | 0.2500 | 0.0000 | 0.2500 | 0.2500 |
| minutes_adjusted_only | minutes_adjusted_rolling_mean | 1.0000 | 0.0000 | 1.0000 | 1.0000 |
| optimized_mae_blend | CatBoost | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_mae_blend | XGBoost | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_mae_blend | minutes_adjusted_rolling_mean | 0.7037 | 0.5132 | 0.1111 | 1.0000 |
| optimized_mae_blend | residual_CatBoost | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_mae_blend | residual_ElasticNet | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_mae_blend | residual_Ridge | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_mae_blend | residual_XGBoost | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_mae_blend | rolling_3_gameweek_mean | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_mae_blend | rolling_5_gameweek_mean | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_rmse_blend | CatBoost | 0.1966 | 0.1654 | 0.0914 | 0.3872 |
| optimized_rmse_blend | XGBoost | 0.1265 | 0.0881 | 0.0471 | 0.2213 |
| optimized_rmse_blend | minutes_adjusted_rolling_mean | 0.0604 | 0.0552 | 0.0016 | 0.1111 |
| optimized_rmse_blend | residual_CatBoost | 0.1040 | 0.0728 | 0.0279 | 0.1730 |
| optimized_rmse_blend | residual_ElasticNet | 0.1346 | 0.0449 | 0.1062 | 0.1864 |
| optimized_rmse_blend | residual_Ridge | 0.1802 | 0.2008 | 0.0230 | 0.4064 |
| optimized_rmse_blend | residual_XGBoost | 0.0771 | 0.0556 | 0.0129 | 0.1111 |
| optimized_rmse_blend | rolling_3_gameweek_mean | 0.0490 | 0.0555 | 0.0041 | 0.1111 |
| optimized_rmse_blend | rolling_5_gameweek_mean | 0.0717 | 0.0387 | 0.0337 | 0.1111 |
| optimized_spearman_blend | CatBoost | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_spearman_blend | XGBoost | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_spearman_blend | minutes_adjusted_rolling_mean | 0.7037 | 0.5132 | 0.1111 | 1.0000 |
| optimized_spearman_blend | residual_CatBoost | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_spearman_blend | residual_ElasticNet | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_spearman_blend | residual_Ridge | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_spearman_blend | residual_XGBoost | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_spearman_blend | rolling_3_gameweek_mean | 0.0370 | 0.0641 | 0.0000 | 0.1111 |
| optimized_spearman_blend | rolling_5_gameweek_mean | 0.0370 | 0.0641 | 0.0000 | 0.1111 |

- Weights are stable only for fixed blends and for optimized MAE/Spearman after inner validation chooses `minutes_adjusted_rolling_mean` exclusively in 2024-25 and 2025-26.
- `optimized_rmse_blend` weights are not stable: CatBoost, XGBoost, residual Ridge/ElasticNet, and residual boosting weights shift substantially between 2024-25 and 2025-26.
- 2023-24 optimized blends use fallback equal weights because there is insufficient prior inner-validation history inside the trimmed dataset.

## Spearman Risk

| model | mean_spearman_delta | worst_spearman_delta |
| --- | --- | --- |
| baseline_plus_residual_boost_blend | -0.0237 | -0.0292 |
| equal_weight_top_models | -0.0222 | -0.0275 |
| optimized_mae_blend | -0.0078 | -0.0235 |
| optimized_rmse_blend | -0.0191 | -0.0235 |
| optimized_spearman_blend | -0.0078 | -0.0235 |
| minutes_adjusted_only | 0.0000 | 0.0000 |

- All non-trivial blends reduce Spearman versus `minutes_adjusted_only` on average.
- The largest average drops are around 0.02-0.024 for `baseline_plus_residual_boost_blend`, `equal_weight_top_models`, and `optimized_rmse_blend`, which is material for a ranking-oriented FPL model.

## Best Ensembles

| metric | best_ensemble | value |
| --- | --- | --- |
| mae | baseline_plus_residual_boost_blend | 1.0095 |
| rmse | optimized_rmse_blend | 2.0048 |
| spearman | minutes_adjusted_only | 0.6715 |
| top_10_precision | baseline_plus_residual_boost_blend | 0.0667 |
| top_20_precision | baseline_plus_residual_boost_blend | 0.0667 |
| top_50_precision | equal_weight_top_models | 0.0667 |

## Interpretation

- No ensemble should become the primary expected-points model yet. The best MAE ensemble improves only narrowly and not in every season, while Spearman deteriorates materially.
- `baseline_plus_residual_boost_blend` is the most plausible secondary expected-points/risk-adjusted candidate because it has the best ensemble MAE and improves RMSE versus the pure minutes-adjusted baseline.
- `optimized_rmse_blend` is an RMSE specialist only; it should not replace the primary model because MAE and Spearman are weaker.
- `equal_weight_top_models` can be kept as a simple ranking-diversification reference, but it does not improve top-k beyond the best base candidate.

## Recommended Final Model Set For Weekly Predictions

- Primary expected-points/ranking model: `minutes_adjusted_rolling_mean` until a model beats it consistently on MAE and Spearman.
- RMSE specialist: `residual_CatBoost`, with `optimized_rmse_blend` as an experiment-only comparator.
- Secondary/risk-adjusted candidate: `baseline_plus_residual_boost_blend`, not default yet.
- Keep modelling candidates for next session: `CatBoost`, `XGBoost`, `residual_CatBoost`, `residual_XGBoost`, `Ridge`, `ElasticNet`, `residual_Ridge`, `residual_ElasticNet`, `global_plus_position_interactions`, and `position_wise_models` for the mask follow-up.
- Keep baselines: `minutes_adjusted_rolling_mean`, `rolling_5_gameweek_mean`, and `rolling_3_gameweek_mean` for diagnostics and ranking comparisons.

## Validation Commands

- `python -m pytest`: passed, 103 tests.
- `python -m ruff check src tests`: passed.
