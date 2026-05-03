# Season Window Comparison

Rolling-origin comparison of season windows. Broad ablation and feature selection remain opt-in and are not run by this experiment.

## Seasons And Folds

| window | validation_season | included_seasons | train_seasons | n_train | n_validation | note |
| --- | --- | --- | --- | --- | --- | --- |
| full_history | 2017-18 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2016-17 | 23679 | 22467 |  |
| full_history | 2018-19 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2016-17, 2017-18 | 46146 | 21790 |  |
| full_history | 2019-20 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2016-17, 2017-18, 2018-19 | 67936 | 22560 |  |
| full_history | 2020-21 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2016-17, 2017-18, 2018-19, 2019-20 | 90496 | 24365 |  |
| full_history | 2021-22 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21 | 114861 | 25447 |  |
| full_history | 2022-23 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22 | 140308 | 26505 |  |
| full_history | 2023-24 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23 | 166813 | 29725 |  |
| full_history | 2024-25 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24 | 196538 | 27283 |  |
| full_history | 2025-26 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2016-17, 2017-18, 2018-19, 2019-20, 2020-21, 2021-22, 2022-23, 2023-24, 2024-25 | 223821 | 22353 |  |
| supported_seasons | 2021-22 | 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2020-21 | 24365 | 25447 |  |
| supported_seasons | 2022-23 | 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2020-21, 2021-22 | 49812 | 26505 |  |
| supported_seasons | 2023-24 | 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2020-21, 2021-22, 2022-23 | 76317 | 29725 |  |
| supported_seasons | 2024-25 | 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2020-21, 2021-22, 2022-23, 2023-24 | 106042 | 27283 |  |
| supported_seasons | 2025-26 | 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26 | 2020-21, 2021-22, 2022-23, 2023-24, 2024-25 | 133325 | 22353 |  |
| rich_feature_seasons | 2023-24 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23 | 26505 | 29725 |  |
| rich_feature_seasons | 2024-25 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23, 2023-24 | 56230 | 27283 |  |
| rich_feature_seasons | 2025-26 | 2022-23, 2023-24, 2024-25, 2025-26 | 2022-23, 2023-24, 2024-25 | 83513 | 22353 |  |

## Best Window By Metric

| metric | best_window | value |
| --- | --- | --- |
| mae | rich_feature_seasons | 1.0098 |
| rmse | rich_feature_seasons | 2.0062 |
| spearman | rich_feature_seasons | 0.6715 |
| top_10_precision | rich_feature_seasons | 0.1000 |
| top_20_precision | rich_feature_seasons | 0.0667 |
| top_50_precision | rich_feature_seasons | 0.0733 |

## Model-By-Model Window Comparison

| model | window | seasons | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CatBoost | full_history | 9 | 1.1866 | 2.1265 | 0.6391 | 0.0000 | 0.0056 | 0.0311 |
| CatBoost | rich_feature_seasons | 3 | 1.0616 | 2.0158 | 0.6496 | 0.0667 | 0.0500 | 0.0733 |
| CatBoost | supported_seasons | 5 | 1.1065 | 2.0490 | 0.6444 | 0.0000 | 0.0100 | 0.0280 |
| ElasticNet | full_history | 9 | 1.2186 | 2.1366 | 0.6285 | 0.0222 | 0.0222 | 0.0422 |
| ElasticNet | rich_feature_seasons | 3 | 1.1037 | 2.0254 | 0.6256 | 0.0667 | 0.0667 | 0.0600 |
| ElasticNet | supported_seasons | 5 | 1.1457 | 2.0605 | 0.6279 | 0.0400 | 0.0300 | 0.0480 |
| LightGBM | full_history | 9 | 1.1939 | 2.1436 | 0.6329 | 0.0111 | 0.0167 | 0.0267 |
| LightGBM | rich_feature_seasons | 3 | 1.0673 | 2.0351 | 0.6442 | 0.0000 | 0.0167 | 0.0400 |
| LightGBM | supported_seasons | 5 | 1.1144 | 2.0689 | 0.6375 | 0.0000 | 0.0100 | 0.0360 |
| Ridge | full_history | 9 | 1.2137 | 2.1363 | 0.6281 | 0.0222 | 0.0278 | 0.0333 |
| Ridge | rich_feature_seasons | 3 | 1.1003 | 2.0250 | 0.6262 | 0.0667 | 0.0500 | 0.0600 |
| Ridge | supported_seasons | 5 | 1.1407 | 2.0602 | 0.6280 | 0.0400 | 0.0400 | 0.0400 |
| XGBoost | full_history | 9 | 1.1873 | 2.1273 | 0.6377 | 0.0111 | 0.0167 | 0.0378 |
| XGBoost | rich_feature_seasons | 3 | 1.0615 | 2.0176 | 0.6487 | 0.0333 | 0.0167 | 0.0533 |
| XGBoost | supported_seasons | 5 | 1.1065 | 2.0494 | 0.6428 | 0.0000 | 0.0300 | 0.0360 |
| global_plus_position_interactions | full_history | 5 | 1.1279 | 2.0564 | 0.6316 | 0.0200 | 0.0200 | 0.0360 |
| global_plus_position_interactions | rich_feature_seasons | 3 | 1.0819 | 2.0210 | 0.6357 | 0.0333 | 0.0333 | 0.0600 |
| global_plus_position_interactions | supported_seasons | 5 | 1.1279 | 2.0564 | 0.6316 | 0.0200 | 0.0200 | 0.0360 |
| minutes_adjusted_rolling_mean | full_history | 9 | 1.1298 | 2.2827 | 0.6449 | 0.0111 | 0.0333 | 0.0400 |
| minutes_adjusted_rolling_mean | rich_feature_seasons | 3 | 1.0098 | 2.1574 | 0.6715 | 0.0333 | 0.0667 | 0.0533 |
| minutes_adjusted_rolling_mean | supported_seasons | 5 | 1.0469 | 2.1975 | 0.6616 | 0.0200 | 0.0400 | 0.0440 |
| position_wise_models | full_history | 5 | 1.1323 | 2.0594 | 0.6306 | 0.0200 | 0.0200 | 0.0360 |
| position_wise_models | rich_feature_seasons | 3 | 1.0881 | 2.0250 | 0.6340 | 0.0333 | 0.0333 | 0.0600 |
| position_wise_models | supported_seasons | 5 | 1.1323 | 2.0594 | 0.6306 | 0.0200 | 0.0200 | 0.0360 |
| residual_CatBoost | full_history | 9 | 1.1755 | 2.1150 | 0.6463 | 0.0000 | 0.0222 | 0.0378 |
| residual_CatBoost | rich_feature_seasons | 3 | 1.0487 | 2.0062 | 0.6549 | 0.0667 | 0.0333 | 0.0667 |
| residual_CatBoost | supported_seasons | 5 | 1.0941 | 2.0364 | 0.6509 | 0.0000 | 0.0100 | 0.0240 |
| residual_ElasticNet | full_history | 9 | 1.2071 | 2.1242 | 0.6359 | 0.0222 | 0.0278 | 0.0422 |
| residual_ElasticNet | rich_feature_seasons | 3 | 1.0885 | 2.0112 | 0.6366 | 0.0667 | 0.0667 | 0.0667 |
| residual_ElasticNet | supported_seasons | 5 | 1.1309 | 2.0466 | 0.6346 | 0.0400 | 0.0400 | 0.0480 |
| residual_LightGBM | full_history | 9 | 1.1827 | 2.1327 | 0.6401 | 0.0111 | 0.0167 | 0.0178 |
| residual_LightGBM | rich_feature_seasons | 3 | 1.0569 | 2.0287 | 0.6496 | 0.0000 | 0.0000 | 0.0333 |
| residual_LightGBM | supported_seasons | 5 | 1.1018 | 2.0551 | 0.6443 | 0.0000 | 0.0000 | 0.0240 |
| residual_Ridge | full_history | 9 | 1.1992 | 2.1231 | 0.6358 | 0.0111 | 0.0278 | 0.0356 |
| residual_Ridge | rich_feature_seasons | 3 | 1.0809 | 2.0093 | 0.6385 | 0.0667 | 0.0500 | 0.0600 |
| residual_Ridge | supported_seasons | 5 | 1.1217 | 2.0452 | 0.6355 | 0.0400 | 0.0300 | 0.0360 |
| residual_XGBoost | full_history | 9 | 1.1756 | 2.1163 | 0.6449 | 0.0111 | 0.0222 | 0.0378 |
| residual_XGBoost | rich_feature_seasons | 3 | 1.0484 | 2.0076 | 0.6538 | 0.0667 | 0.0333 | 0.0400 |
| residual_XGBoost | supported_seasons | 5 | 1.0946 | 2.0391 | 0.6483 | 0.0000 | 0.0200 | 0.0240 |

## Older Season Effects

Positive MAE/RMSE deltas mean the older window is worse; negative deltas mean it is better. Positive Spearman deltas mean the older window is better.

| model | comparison | mae_delta_old_minus_new | rmse_delta_old_minus_new | spearman_delta_old_minus_new | interpretation |
| --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | full_vs_supported | 0.0828 | 0.0853 | -0.0167 | older window hurts MAE |
| minutes_adjusted_rolling_mean | supported_vs_rich | 0.0371 | 0.0401 | -0.0099 | older window hurts MAE |
| Ridge | full_vs_supported | 0.0730 | 0.0761 | 0.0001 | older window hurts MAE |
| Ridge | supported_vs_rich | 0.0404 | 0.0353 | 0.0018 | older window hurts MAE |
| ElasticNet | full_vs_supported | 0.0729 | 0.0760 | 0.0006 | older window hurts MAE |
| ElasticNet | supported_vs_rich | 0.0420 | 0.0351 | 0.0022 | older window hurts MAE |
| CatBoost | full_vs_supported | 0.0801 | 0.0775 | -0.0053 | older window hurts MAE |
| CatBoost | supported_vs_rich | 0.0449 | 0.0332 | -0.0052 | older window hurts MAE |
| XGBoost | full_vs_supported | 0.0808 | 0.0778 | -0.0050 | older window hurts MAE |
| XGBoost | supported_vs_rich | 0.0450 | 0.0318 | -0.0060 | older window hurts MAE |
| LightGBM | full_vs_supported | 0.0795 | 0.0747 | -0.0046 | older window hurts MAE |
| LightGBM | supported_vs_rich | 0.0472 | 0.0338 | -0.0067 | older window hurts MAE |
| residual_Ridge | full_vs_supported | 0.0775 | 0.0778 | 0.0003 | older window hurts MAE |
| residual_Ridge | supported_vs_rich | 0.0408 | 0.0360 | -0.0030 | older window hurts MAE |
| residual_ElasticNet | full_vs_supported | 0.0762 | 0.0777 | 0.0013 | older window hurts MAE |
| residual_ElasticNet | supported_vs_rich | 0.0424 | 0.0354 | -0.0020 | older window hurts MAE |
| residual_CatBoost | full_vs_supported | 0.0813 | 0.0786 | -0.0046 | older window hurts MAE |
| residual_CatBoost | supported_vs_rich | 0.0454 | 0.0303 | -0.0040 | older window hurts MAE |
| residual_XGBoost | full_vs_supported | 0.0810 | 0.0772 | -0.0034 | older window hurts MAE |
| residual_XGBoost | supported_vs_rich | 0.0462 | 0.0315 | -0.0055 | older window hurts MAE |
| residual_LightGBM | full_vs_supported | 0.0808 | 0.0776 | -0.0042 | older window hurts MAE |
| residual_LightGBM | supported_vs_rich | 0.0450 | 0.0264 | -0.0052 | older window hurts MAE |
| global_plus_position_interactions | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| global_plus_position_interactions | supported_vs_rich | 0.0461 | 0.0354 | -0.0041 | older window hurts MAE |
| position_wise_models | full_vs_supported | 0.0000 | 0.0000 | 0.0000 | older window hurts MAE |
| position_wise_models | supported_vs_rich | 0.0442 | 0.0343 | -0.0034 | older window hurts MAE |

## Rich-Feature Season Reliability

Rich-feature seasons have at least one prior training season for each produced fold, with mean train rows 55416.

## Recommendation

Use `rich_feature_seasons` as the default candidate window for the next modelling pass unless a specific ranking metric in the best-window table justifies a different target.
