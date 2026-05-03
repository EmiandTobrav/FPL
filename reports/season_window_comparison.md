# Season Window Comparison

Rolling-origin comparison of season windows. Broad ablation and feature selection remain opt-in and are not run by this experiment.

## Seasons And Folds

| window | validation_season | included_seasons | train_seasons | n_train | n_validation | note |
| --- | --- | --- | --- | --- | --- | --- |
| full_history | 2023-24 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23 | 26505 | 29725 |  |
| full_history | 2024-25 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23, 2023-24 | 56230 | 27283 |  |
| full_history | 2025-26 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23, 2023-24, 2024-25 | 83513 | 22353 |  |
| supported_seasons | 2023-24 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23 | 26505 | 29725 |  |
| supported_seasons | 2024-25 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23, 2023-24 | 56230 | 27283 |  |
| supported_seasons | 2025-26 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23, 2023-24, 2024-25 | 83513 | 22353 |  |
| rich_feature_seasons | 2023-24 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23 | 26505 | 29725 |  |
| rich_feature_seasons | 2024-25 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23, 2023-24 | 56230 | 27283 |  |
| rich_feature_seasons | 2025-26 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23, 2023-24, 2024-25 | 83513 | 22353 |  |

## Best Window By Metric

| metric | best_window | value |
| --- | --- | --- |
| mae | full_history | 1.0098 |
| rmse | full_history | 2.0062 |
| spearman | full_history | 0.6715 |
| top_10_precision | full_history | 0.1000 |
| top_20_precision | full_history | 0.0667 |
| top_50_precision | full_history | 0.0733 |

## Model-By-Model Window Comparison

| model | window | seasons | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CatBoost | full_history | 3 | 1.0616 | 2.0158 | 0.6496 | 0.0667 | 0.0500 | 0.0733 |
| CatBoost | rich_feature_seasons | 3 | 1.0616 | 2.0158 | 0.6496 | 0.0667 | 0.0500 | 0.0733 |
| CatBoost | supported_seasons | 3 | 1.0616 | 2.0158 | 0.6496 | 0.0667 | 0.0500 | 0.0733 |
| ElasticNet | full_history | 3 | 1.1037 | 2.0254 | 0.6256 | 0.0667 | 0.0667 | 0.0600 |
| ElasticNet | rich_feature_seasons | 3 | 1.1037 | 2.0254 | 0.6256 | 0.0667 | 0.0667 | 0.0600 |
| ElasticNet | supported_seasons | 3 | 1.1037 | 2.0254 | 0.6256 | 0.0667 | 0.0667 | 0.0600 |
| LightGBM | full_history | 3 | 1.0673 | 2.0351 | 0.6442 | 0.0000 | 0.0167 | 0.0400 |
| LightGBM | rich_feature_seasons | 3 | 1.0673 | 2.0351 | 0.6442 | 0.0000 | 0.0167 | 0.0400 |
| LightGBM | supported_seasons | 3 | 1.0673 | 2.0351 | 0.6442 | 0.0000 | 0.0167 | 0.0400 |
| Ridge | full_history | 3 | 1.1003 | 2.0250 | 0.6262 | 0.0667 | 0.0500 | 0.0600 |
| Ridge | rich_feature_seasons | 3 | 1.1003 | 2.0250 | 0.6262 | 0.0667 | 0.0500 | 0.0600 |
| Ridge | supported_seasons | 3 | 1.1003 | 2.0250 | 0.6262 | 0.0667 | 0.0500 | 0.0600 |
| XGBoost | full_history | 3 | 1.0615 | 2.0176 | 0.6487 | 0.0333 | 0.0167 | 0.0533 |
| XGBoost | rich_feature_seasons | 3 | 1.0615 | 2.0176 | 0.6487 | 0.0333 | 0.0167 | 0.0533 |
| XGBoost | supported_seasons | 3 | 1.0615 | 2.0176 | 0.6487 | 0.0333 | 0.0167 | 0.0533 |
| global_plus_position_interactions | full_history | 3 | 1.0819 | 2.0210 | 0.6357 | 0.0333 | 0.0333 | 0.0600 |
| global_plus_position_interactions | rich_feature_seasons | 3 | 1.0819 | 2.0210 | 0.6357 | 0.0333 | 0.0333 | 0.0600 |
| global_plus_position_interactions | supported_seasons | 3 | 1.0819 | 2.0210 | 0.6357 | 0.0333 | 0.0333 | 0.0600 |
| minutes_adjusted_rolling_mean | full_history | 3 | 1.0098 | 2.1574 | 0.6715 | 0.0333 | 0.0667 | 0.0533 |
| minutes_adjusted_rolling_mean | rich_feature_seasons | 3 | 1.0098 | 2.1574 | 0.6715 | 0.0333 | 0.0667 | 0.0533 |
| minutes_adjusted_rolling_mean | supported_seasons | 3 | 1.0098 | 2.1574 | 0.6715 | 0.0333 | 0.0667 | 0.0533 |
| position_wise_models | full_history | 3 | 1.0881 | 2.0250 | 0.6340 | 0.0333 | 0.0333 | 0.0600 |
| position_wise_models | rich_feature_seasons | 3 | 1.0881 | 2.0250 | 0.6340 | 0.0333 | 0.0333 | 0.0600 |
| position_wise_models | supported_seasons | 3 | 1.0881 | 2.0250 | 0.6340 | 0.0333 | 0.0333 | 0.0600 |
| residual_CatBoost | full_history | 3 | 1.0487 | 2.0062 | 0.6549 | 0.0667 | 0.0333 | 0.0667 |
| residual_CatBoost | rich_feature_seasons | 3 | 1.0487 | 2.0062 | 0.6549 | 0.0667 | 0.0333 | 0.0667 |
| residual_CatBoost | supported_seasons | 3 | 1.0487 | 2.0062 | 0.6549 | 0.0667 | 0.0333 | 0.0667 |
| residual_ElasticNet | full_history | 3 | 1.0885 | 2.0112 | 0.6366 | 0.0667 | 0.0667 | 0.0667 |
| residual_ElasticNet | rich_feature_seasons | 3 | 1.0885 | 2.0112 | 0.6366 | 0.0667 | 0.0667 | 0.0667 |
| residual_ElasticNet | supported_seasons | 3 | 1.0885 | 2.0112 | 0.6366 | 0.0667 | 0.0667 | 0.0667 |
| residual_LightGBM | full_history | 3 | 1.0569 | 2.0287 | 0.6496 | 0.0000 | 0.0000 | 0.0333 |
| residual_LightGBM | rich_feature_seasons | 3 | 1.0569 | 2.0287 | 0.6496 | 0.0000 | 0.0000 | 0.0333 |
| residual_LightGBM | supported_seasons | 3 | 1.0569 | 2.0287 | 0.6496 | 0.0000 | 0.0000 | 0.0333 |
| residual_Ridge | full_history | 3 | 1.0809 | 2.0093 | 0.6385 | 0.0667 | 0.0500 | 0.0600 |
| residual_Ridge | rich_feature_seasons | 3 | 1.0809 | 2.0093 | 0.6385 | 0.0667 | 0.0500 | 0.0600 |
| residual_Ridge | supported_seasons | 3 | 1.0809 | 2.0093 | 0.6385 | 0.0667 | 0.0500 | 0.0600 |
| residual_XGBoost | full_history | 3 | 1.0484 | 2.0076 | 0.6538 | 0.0667 | 0.0333 | 0.0400 |
| residual_XGBoost | rich_feature_seasons | 3 | 1.0484 | 2.0076 | 0.6538 | 0.0667 | 0.0333 | 0.0400 |
| residual_XGBoost | supported_seasons | 3 | 1.0484 | 2.0076 | 0.6538 | 0.0667 | 0.0333 | 0.0400 |

## Older Season Effects

Positive MAE/RMSE deltas mean the older window is worse; negative deltas mean it is better. Positive Spearman deltas mean the older window is better.

| model | comparison | mae_delta_old_minus_new | rmse_delta_old_minus_new | spearman_delta_old_minus_new | interpretation |
| --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| minutes_adjusted_rolling_mean | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| Ridge | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| Ridge | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| ElasticNet | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| ElasticNet | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| CatBoost | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| CatBoost | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| XGBoost | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| XGBoost | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| LightGBM | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| LightGBM | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| residual_Ridge | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| residual_Ridge | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| residual_ElasticNet | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| residual_ElasticNet | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| residual_CatBoost | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| residual_CatBoost | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| residual_XGBoost | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| residual_XGBoost | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| residual_LightGBM | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| residual_LightGBM | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| global_plus_position_interactions | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| global_plus_position_interactions | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| position_wise_models | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| position_wise_models | supported_vs_rich | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |

## Rich-Feature Season Reliability

Rich-feature seasons have at least one prior training season for each produced fold, with mean train rows 55416.

## Recommendation

Use `full_history` as the default candidate window for the next modelling pass unless a specific ranking metric in the best-window table justifies a different target.
