# Model Pruning Audit

Supported-season rolling-origin audit for model pruning. The audit replays predictions for seasons included by the configured minimum season; it does not change model code.

## Classification

| model | classification | overall_competitive | overall_primary_competitive | early_competitive | position_competitive | season_competitive | ranking_competitive | ever_best | ever_near_best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CatBoost | keep_core | True | True | True | True | True | True | True | True |
| ElasticNet | keep_core | True | True | True | True | True | True | True | True |
| Ridge | keep_core | True | True | True | True | True | True | True | True |
| XGBoost | keep_core | True | True | True | True | True | True | True | True |
| global_model | keep_core | True | True | True | True | True | True | True | True |
| global_plus_position_interactions | keep_core | True | True | True | True | True | True | True | True |
| minutes_adjusted_rolling_mean | keep_core | True | True | True | True | True | True | True | True |
| position_wise_models | keep_core | True | True | True | True | True | True | True | True |
| residual_CatBoost | keep_core | True | True | True | True | True | True | True | True |
| residual_ElasticNet | keep_core | True | True | True | True | True | True | True | True |
| residual_Ridge | keep_core | True | True | True | True | True | True | True | True |
| residual_XGBoost | keep_core | True | True | True | True | True | True | True | True |
| rolling_3_gameweek_mean | keep_core | True | True | True | True | True | True | True | True |
| rolling_5_gameweek_mean | keep_core | True | True | True | True | True | True | True | True |
| LightGBM | keep_specialist | False | False | True | False | False | True | True | True |
| previous_gameweek_points | keep_specialist | False | False | False | True | False | False | False | True |
| residual_LightGBM | keep_specialist | False | False | True | True | True | True | True | True |

## Best Overall By Metric

| metric | model | value |
| --- | --- | --- |
| mae | minutes_adjusted_rolling_mean | 1.0059 |
| rmse | residual_CatBoost | 2.0052 |
| spearman | minutes_adjusted_rolling_mean | 0.6706 |
| top_10_precision | rolling_3_gameweek_mean | 0.1000 |
| top_20_precision | rolling_3_gameweek_mean | 0.1000 |
| top_50_precision | Ridge | 0.0600 |

## Overall Metrics

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 1.0059 | 2.1534 | 0.6706 | 0.0000 | 0.0500 | 0.0400 | True | True |
| residual_XGBoost | 1.0482 | 2.0065 | 0.6530 | 0.0000 | 0.1000 | 0.0400 | True | True |
| residual_CatBoost | 1.0486 | 2.0052 | 0.6539 | 0.0000 | 0.0500 | 0.0400 | True | True |
| residual_LightGBM | 1.0574 | 2.0289 | 0.6482 | 0.0000 | 0.0000 | 0.0000 | False | False |
| XGBoost | 1.0614 | 2.0160 | 0.6476 | 0.0000 | 0.0500 | 0.0200 | True | False |
| CatBoost | 1.0615 | 2.0144 | 0.6483 | 0.0000 | 0.0500 | 0.0600 | True | True |
| LightGBM | 1.0678 | 2.0347 | 0.6426 | 0.0000 | 0.0000 | 0.0200 | False | False |
| rolling_5_gameweek_mean | 1.0701 | 2.1398 | 0.6655 | 0.0000 | 0.0500 | 0.0400 | True | False |
| residual_Ridge | 1.0812 | 2.0076 | 0.6374 | 0.0000 | 0.0500 | 0.0600 | True | True |
| global_plus_position_interactions | 1.0812 | 2.0185 | 0.6343 | 0.0000 | 0.0500 | 0.0200 | True | False |
| position_wise_models | 1.0875 | 2.0224 | 0.6322 | 0.0000 | 0.0500 | 0.0200 | True | False |
| rolling_3_gameweek_mean | 1.0876 | 2.2135 | 0.6638 | 0.1000 | 0.1000 | 0.0400 | True | True |
| residual_ElasticNet | 1.0888 | 2.0095 | 0.6353 | 0.0000 | 0.0500 | 0.0600 | True | True |
| Ridge | 1.1002 | 2.0226 | 0.6247 | 0.0000 | 0.0500 | 0.0600 | True | True |
| global_model | 1.1002 | 2.0226 | 0.6247 | 0.0000 | 0.0500 | 0.0600 | True | True |
| ElasticNet | 1.1036 | 2.0230 | 0.6240 | 0.0000 | 0.0500 | 0.0600 | True | True |
| previous_gameweek_points | 1.1773 | 2.6093 | 0.6267 | 0.0000 | 0.0500 | 0.0400 | False | False |

## Early-Season Metrics: GW1-5

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 1.1114 | 2.2886 | 0.6533 | 0.1000 | 0.0500 | 0.0800 | True | True |
| residual_XGBoost | 1.1279 | 2.0756 | 0.6335 | 0.0000 | 0.0000 | 0.0400 | False | False |
| residual_CatBoost | 1.1310 | 2.0734 | 0.6346 | 0.0000 | 0.0000 | 0.0400 | True | False |
| residual_Ridge | 1.1398 | 2.0542 | 0.6314 | 0.1000 | 0.0500 | 0.1000 | True | True |
| residual_LightGBM | 1.1418 | 2.1054 | 0.6265 | 0.0000 | 0.0500 | 0.0800 | False | False |
| residual_ElasticNet | 1.1453 | 2.0549 | 0.6300 | 0.1000 | 0.0500 | 0.1200 | True | True |
| rolling_3_gameweek_mean | 1.1701 | 2.3238 | 0.6496 | 0.1000 | 0.0500 | 0.0800 | True | True |
| rolling_5_gameweek_mean | 1.1706 | 2.3141 | 0.6477 | 0.1000 | 0.0500 | 0.1000 | True | True |
| position_wise_models | 1.1738 | 2.1685 | 0.5670 | 0.0000 | 0.0500 | 0.0600 | False | False |
| Ridge | 1.1883 | 2.1750 | 0.5482 | 0.0000 | 0.0500 | 0.0600 | False | False |
| global_model | 1.1883 | 2.1750 | 0.5482 | 0.0000 | 0.0500 | 0.0600 | False | False |
| ElasticNet | 1.1887 | 2.1745 | 0.5463 | 0.0000 | 0.0500 | 0.0800 | False | False |
| CatBoost | 1.1977 | 2.1469 | 0.5816 | 0.1000 | 0.1000 | 0.1000 | True | True |
| XGBoost | 1.2021 | 2.1529 | 0.5810 | 0.0000 | 0.0500 | 0.0800 | False | False |
| LightGBM | 1.2141 | 2.1679 | 0.5739 | 0.1000 | 0.1000 | 0.0800 | True | True |
| global_plus_position_interactions | 1.2153 | 2.1433 | 0.5698 | 0.0000 | 0.0500 | 0.0800 | False | False |
| previous_gameweek_points | 1.2623 | 2.6610 | 0.6189 | 0.0000 | 0.0500 | 0.0800 | False | False |

## Models Beating Minutes-Adjusted Baseline In GW1-5 By MAE

None.

## Residual Model Early-Season Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| residual_CatBoost | 1.1310 | 2.0734 | 0.6346 | 0.0000 | 0.0000 | 0.0400 | True | False |
| residual_ElasticNet | 1.1453 | 2.0549 | 0.6300 | 0.1000 | 0.0500 | 0.1200 | True | True |
| residual_LightGBM | 1.1418 | 2.1054 | 0.6265 | 0.0000 | 0.0500 | 0.0800 | False | False |
| residual_Ridge | 1.1398 | 2.0542 | 0.6314 | 0.1000 | 0.0500 | 0.1000 | True | True |
| residual_XGBoost | 1.1279 | 2.0756 | 0.6335 | 0.0000 | 0.0000 | 0.0400 | False | False |

## Ridge And ElasticNet Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ElasticNet | 1.1036 | 2.0230 | 0.6240 | 0.0000 | 0.0500 | 0.0600 | True | True |
| Ridge | 1.1002 | 2.0226 | 0.6247 | 0.0000 | 0.0500 | 0.0600 | True | True |
| residual_ElasticNet | 1.0888 | 2.0095 | 0.6353 | 0.0000 | 0.0500 | 0.0600 | True | True |
| residual_Ridge | 1.0812 | 2.0076 | 0.6374 | 0.0000 | 0.0500 | 0.0600 | True | True |

## Tree/Boosting Model Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CatBoost | 1.0615 | 2.0144 | 0.6483 | 0.0000 | 0.0500 | 0.0600 | True | True |
| LightGBM | 1.0678 | 2.0347 | 0.6426 | 0.0000 | 0.0000 | 0.0200 | False | False |
| XGBoost | 1.0614 | 2.0160 | 0.6476 | 0.0000 | 0.0500 | 0.0200 | True | False |
| residual_CatBoost | 1.0486 | 2.0052 | 0.6539 | 0.0000 | 0.0500 | 0.0400 | True | True |
| residual_LightGBM | 1.0574 | 2.0289 | 0.6482 | 0.0000 | 0.0000 | 0.0000 | False | False |
| residual_XGBoost | 1.0482 | 2.0065 | 0.6530 | 0.0000 | 0.1000 | 0.0400 | True | True |

## Position Strategy Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_model | 1.1002 | 2.0226 | 0.6247 | 0.0000 | 0.0500 | 0.0600 | True | True |
| global_plus_position_interactions | 1.0812 | 2.0185 | 0.6343 | 0.0000 | 0.0500 | 0.0200 | True | False |
| position_wise_models | 1.0875 | 2.0224 | 0.6322 | 0.0000 | 0.0500 | 0.0200 | True | False |

## Season-By-Season Performance

| model | segment | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 2023-24 | 0.9648 | 2.1318 | 0.6578 | 0.0000 | 0.0500 | 0.0400 |
| rolling_5_gameweek_mean | 2023-24 | 1.0303 | 2.1198 | 0.6542 | 0.0000 | 0.0500 | 0.0400 |
| residual_XGBoost | 2023-24 | 1.0407 | 2.0079 | 0.6351 | 0.1000 | 0.0500 | 0.0400 |
| residual_CatBoost | 2023-24 | 1.0431 | 2.0106 | 0.6358 | 0.1000 | 0.0500 | 0.0600 |
| rolling_3_gameweek_mean | 2023-24 | 1.0503 | 2.1963 | 0.6500 | 0.1000 | 0.0500 | 0.0600 |
| CatBoost | 2023-24 | 1.0565 | 2.0115 | 0.6305 | 0.1000 | 0.1000 | 0.0800 |
| XGBoost | 2023-24 | 1.0572 | 2.0112 | 0.6298 | 0.0000 | 0.0000 | 0.0600 |
| residual_LightGBM | 2023-24 | 1.0583 | 2.0462 | 0.6268 | 0.0000 | 0.0000 | 0.0600 |
| LightGBM | 2023-24 | 1.0674 | 2.0445 | 0.6214 | 0.0000 | 0.0500 | 0.0200 |
| global_plus_position_interactions | 2023-24 | 1.0786 | 2.0048 | 0.6158 | 0.0000 | 0.0000 | 0.0200 |
| position_wise_models | 2023-24 | 1.0835 | 2.0065 | 0.6141 | 0.0000 | 0.0000 | 0.0200 |
| residual_Ridge | 2023-24 | 1.0838 | 2.0037 | 0.6182 | 0.1000 | 0.0500 | 0.0400 |
| residual_ElasticNet | 2023-24 | 1.0930 | 2.0057 | 0.6153 | 0.1000 | 0.0500 | 0.0600 |
| Ridge | 2023-24 | 1.0994 | 2.0089 | 0.6096 | 0.1000 | 0.0500 | 0.0400 |
| global_model | 2023-24 | 1.0994 | 2.0089 | 0.6096 | 0.1000 | 0.0500 | 0.0400 |
| ElasticNet | 2023-24 | 1.1040 | 2.0094 | 0.6089 | 0.1000 | 0.0500 | 0.0400 |
| previous_gameweek_points | 2023-24 | 1.1418 | 2.5994 | 0.6090 | 0.0000 | 0.0500 | 0.0400 |
| minutes_adjusted_rolling_mean | 2024-25 | 1.0168 | 2.1315 | 0.6680 | 0.1000 | 0.1500 | 0.1000 |
| residual_CatBoost | 2024-25 | 1.0549 | 1.9833 | 0.6585 | 0.1000 | 0.0500 | 0.1000 |
| residual_XGBoost | 2024-25 | 1.0566 | 1.9888 | 0.6585 | 0.1000 | 0.0500 | 0.0800 |
| residual_LightGBM | 2024-25 | 1.0619 | 2.0059 | 0.6544 | 0.0000 | 0.0000 | 0.0200 |
| CatBoost | 2024-25 | 1.0672 | 1.9985 | 0.6533 | 0.1000 | 0.0500 | 0.1000 |
| XGBoost | 2024-25 | 1.0673 | 2.0013 | 0.6528 | 0.1000 | 0.0500 | 0.0800 |
| LightGBM | 2024-25 | 1.0747 | 2.0150 | 0.6478 | 0.0000 | 0.0000 | 0.0800 |
| global_plus_position_interactions | 2024-25 | 1.0769 | 2.0040 | 0.6406 | 0.1000 | 0.1000 | 0.1200 |
| residual_Ridge | 2024-25 | 1.0812 | 1.9922 | 0.6441 | 0.1000 | 0.1000 | 0.1000 |
| rolling_5_gameweek_mean | 2024-25 | 1.0815 | 2.1158 | 0.6629 | 0.1000 | 0.1500 | 0.1200 |
| position_wise_models | 2024-25 | 1.0849 | 2.0089 | 0.6382 | 0.1000 | 0.1000 | 0.1200 |
| residual_ElasticNet | 2024-25 | 1.0862 | 1.9931 | 0.6425 | 0.1000 | 0.1500 | 0.1000 |
| Ridge | 2024-25 | 1.1006 | 2.0104 | 0.6308 | 0.1000 | 0.1000 | 0.1000 |
| global_model | 2024-25 | 1.1006 | 2.0104 | 0.6308 | 0.1000 | 0.1000 | 0.1000 |
| ElasticNet | 2024-25 | 1.1022 | 2.0104 | 0.6303 | 0.1000 | 0.1500 | 0.1000 |
| rolling_3_gameweek_mean | 2024-25 | 1.1068 | 2.2010 | 0.6596 | 0.1000 | 0.1000 | 0.1000 |
| previous_gameweek_points | 2024-25 | 1.1938 | 2.5890 | 0.6180 | 0.0000 | 0.0500 | 0.0600 |
| minutes_adjusted_rolling_mean | 2025-26 | 1.0478 | 2.2088 | 0.6886 | 0.0000 | 0.0000 | 0.0200 |
| residual_XGBoost | 2025-26 | 1.0479 | 2.0262 | 0.6679 | 0.0000 | 0.0000 | 0.0000 |
| residual_CatBoost | 2025-26 | 1.0481 | 2.0247 | 0.6703 | 0.0000 | 0.0000 | 0.0400 |
| residual_LightGBM | 2025-26 | 1.0504 | 2.0339 | 0.6675 | 0.0000 | 0.0000 | 0.0200 |
| LightGBM | 2025-26 | 1.0597 | 2.0457 | 0.6633 | 0.0000 | 0.0000 | 0.0200 |
| XGBoost | 2025-26 | 1.0600 | 2.0404 | 0.6637 | 0.0000 | 0.0000 | 0.0200 |
| CatBoost | 2025-26 | 1.0610 | 2.0375 | 0.6650 | 0.0000 | 0.0000 | 0.0400 |
| residual_Ridge | 2025-26 | 1.0777 | 2.0319 | 0.6532 | 0.0000 | 0.0000 | 0.0400 |
| residual_ElasticNet | 2025-26 | 1.0863 | 2.0346 | 0.6519 | 0.0000 | 0.0000 | 0.0400 |
| global_plus_position_interactions | 2025-26 | 1.0900 | 2.0541 | 0.6507 | 0.0000 | 0.0000 | 0.0400 |
| position_wise_models | 2025-26 | 1.0959 | 2.0596 | 0.6496 | 0.0000 | 0.0000 | 0.0400 |
| Ridge | 2025-26 | 1.1009 | 2.0556 | 0.6382 | 0.0000 | 0.0000 | 0.0400 |
| global_model | 2025-26 | 1.1009 | 2.0556 | 0.6382 | 0.0000 | 0.0000 | 0.0400 |
| ElasticNet | 2025-26 | 1.1048 | 2.0564 | 0.6378 | 0.0000 | 0.0000 | 0.0400 |
| rolling_5_gameweek_mean | 2025-26 | 1.1098 | 2.1956 | 0.6812 | 0.0000 | 0.0000 | 0.0400 |
| rolling_3_gameweek_mean | 2025-26 | 1.1143 | 2.2519 | 0.6845 | 0.0000 | 0.0000 | 0.0000 |
| previous_gameweek_points | 2025-26 | 1.2049 | 2.6474 | 0.6578 | 0.0000 | 0.0000 | 0.0000 |

## Position-Specific Performance

| model | segment | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | DEF | 1.0738 | 2.1857 | 0.5736 | 0.0000 | 0.0000 | 0.0000 |
| residual_Ridge | DEF | 1.1237 | 2.0373 | 0.5607 | 0.0000 | 0.0000 | 0.0200 |
| residual_XGBoost | DEF | 1.1282 | 2.0376 | 0.5694 | 0.0000 | 0.0000 | 0.0000 |
| residual_ElasticNet | DEF | 1.1296 | 2.0380 | 0.5598 | 0.0000 | 0.0000 | 0.0200 |
| residual_CatBoost | DEF | 1.1354 | 2.0406 | 0.5699 | 0.0000 | 0.0000 | 0.0000 |
| residual_LightGBM | DEF | 1.1359 | 2.0625 | 0.5611 | 0.0000 | 0.0000 | 0.0000 |
| XGBoost | DEF | 1.1360 | 2.0413 | 0.5663 | 0.0000 | 0.0000 | 0.0000 |
| Ridge | DEF | 1.1378 | 2.0484 | 0.5506 | 0.0000 | 0.0000 | 0.0200 |
| global_model | DEF | 1.1378 | 2.0484 | 0.5506 | 0.0000 | 0.0000 | 0.0200 |
| global_plus_position_interactions | DEF | 1.1414 | 2.0477 | 0.5435 | 0.0000 | 0.0000 | 0.0400 |
| CatBoost | DEF | 1.1416 | 2.0426 | 0.5651 | 0.0000 | 0.0000 | 0.0000 |
| LightGBM | DEF | 1.1420 | 2.0618 | 0.5581 | 0.0000 | 0.0000 | 0.0000 |
| ElasticNet | DEF | 1.1434 | 2.0484 | 0.5504 | 0.0000 | 0.0000 | 0.0200 |
| position_wise_models | DEF | 1.1487 | 2.0518 | 0.5396 | 0.0000 | 0.0500 | 0.0400 |
| rolling_5_gameweek_mean | DEF | 1.1488 | 2.1901 | 0.5642 | 0.0000 | 0.0000 | 0.0000 |
| rolling_3_gameweek_mean | DEF | 1.1659 | 2.2643 | 0.5582 | 0.0000 | 0.0500 | 0.0200 |
| previous_gameweek_points | DEF | 1.2698 | 2.6683 | 0.5020 | 0.0000 | 0.0000 | 0.0200 |
| minutes_adjusted_rolling_mean | FWD | 1.0946 | 2.3818 | 0.7233 | 0.0000 | 0.0000 | 0.0400 |
| residual_CatBoost | FWD | 1.1584 | 2.2087 | 0.6922 | 0.0000 | 0.0500 | 0.0600 |
| residual_XGBoost | FWD | 1.1633 | 2.2151 | 0.6925 | 0.0000 | 0.0500 | 0.0800 |
| CatBoost | FWD | 1.1732 | 2.2151 | 0.6863 | 0.0000 | 0.0500 | 0.1000 |
| rolling_5_gameweek_mean | FWD | 1.1742 | 2.3555 | 0.7170 | 0.0000 | 0.0000 | 0.0600 |
| residual_LightGBM | FWD | 1.1751 | 2.2401 | 0.6860 | 0.0000 | 0.0000 | 0.0600 |
| XGBoost | FWD | 1.1790 | 2.2160 | 0.6858 | 0.0000 | 0.0000 | 0.0800 |
| LightGBM | FWD | 1.1842 | 2.2416 | 0.6794 | 0.0000 | 0.0000 | 0.0800 |
| rolling_3_gameweek_mean | FWD | 1.1935 | 2.4450 | 0.7172 | 0.0000 | 0.0000 | 0.0200 |
| global_plus_position_interactions | FWD | 1.2407 | 2.2196 | 0.6631 | 0.0000 | 0.0000 | 0.0400 |
| position_wise_models | FWD | 1.2444 | 2.2214 | 0.6628 | 0.0000 | 0.0000 | 0.0400 |
| residual_ElasticNet | FWD | 1.2516 | 2.2215 | 0.6766 | 0.0000 | 0.0000 | 0.0600 |
| residual_Ridge | FWD | 1.2519 | 2.2170 | 0.6797 | 0.0000 | 0.0000 | 0.0600 |
| ElasticNet | FWD | 1.2573 | 2.2247 | 0.6676 | 0.0000 | 0.0000 | 0.0800 |
| Ridge | FWD | 1.2674 | 2.2236 | 0.6686 | 0.0000 | 0.0000 | 0.0400 |
| global_model | FWD | 1.2674 | 2.2236 | 0.6686 | 0.0000 | 0.0000 | 0.0400 |
| previous_gameweek_points | FWD | 1.2791 | 2.8667 | 0.6881 | 0.0000 | 0.0000 | 0.0200 |
| minutes_adjusted_rolling_mean | GK | 0.6723 | 1.6569 | 0.7683 | 0.0000 | 0.0000 | 0.0000 |
| rolling_5_gameweek_mean | GK | 0.6941 | 1.6516 | 0.7630 | 0.0000 | 0.0000 | 0.0000 |
| rolling_3_gameweek_mean | GK | 0.6984 | 1.7025 | 0.7747 | 0.0000 | 0.0000 | 0.0400 |
| residual_CatBoost | GK | 0.7239 | 1.5357 | 0.6260 | 0.0000 | 0.0000 | 0.0200 |
| residual_XGBoost | GK | 0.7290 | 1.5363 | 0.6281 | 0.0000 | 0.0000 | 0.0000 |
| global_plus_position_interactions | GK | 0.7355 | 1.5532 | 0.6139 | 0.0000 | 0.0000 | 0.0400 |
| residual_LightGBM | GK | 0.7412 | 1.5540 | 0.6262 | 0.0000 | 0.0000 | 0.0600 |
| position_wise_models | GK | 0.7430 | 1.5583 | 0.6005 | 0.0000 | 0.0000 | 0.0200 |
| CatBoost | GK | 0.7461 | 1.5539 | 0.6238 | 0.0000 | 0.0000 | 0.0200 |
| XGBoost | GK | 0.7512 | 1.5546 | 0.6249 | 0.0000 | 0.0000 | 0.0000 |
| residual_Ridge | GK | 0.7521 | 1.5304 | 0.6251 | 0.0000 | 0.0000 | 0.0000 |
| LightGBM | GK | 0.7531 | 1.5663 | 0.6198 | 0.0000 | 0.0000 | 0.0000 |
| previous_gameweek_points | GK | 0.7593 | 2.0082 | 0.7703 | 0.0000 | 0.0000 | 0.0200 |
| residual_ElasticNet | GK | 0.7689 | 1.5324 | 0.6251 | 0.0000 | 0.0000 | 0.0000 |
| Ridge | GK | 0.7788 | 1.5549 | 0.6169 | 0.0000 | 0.0000 | 0.0000 |
| global_model | GK | 0.7788 | 1.5549 | 0.6169 | 0.0000 | 0.0000 | 0.0000 |
| ElasticNet | GK | 0.7952 | 1.5561 | 0.6166 | 0.0000 | 0.0000 | 0.0000 |
| minutes_adjusted_rolling_mean | MID | 1.0159 | 2.1760 | 0.7016 | 0.1000 | 0.0500 | 0.0800 |
| residual_CatBoost | MID | 1.0367 | 2.0262 | 0.6872 | 0.1000 | 0.1000 | 0.0400 |
| residual_XGBoost | MID | 1.0387 | 2.0293 | 0.6858 | 0.2000 | 0.1000 | 0.0400 |
| residual_LightGBM | MID | 1.0474 | 2.0504 | 0.6829 | 0.0000 | 0.0000 | 0.0000 |
| CatBoost | MID | 1.0517 | 2.0399 | 0.6804 | 0.1000 | 0.0500 | 0.0200 |
| XGBoost | MID | 1.0529 | 2.0442 | 0.6795 | 0.1000 | 0.0500 | 0.0200 |
| LightGBM | MID | 1.0610 | 2.0610 | 0.6763 | 0.0000 | 0.0000 | 0.0000 |
| rolling_5_gameweek_mean | MID | 1.0788 | 2.1508 | 0.6936 | 0.1000 | 0.0500 | 0.0800 |
| global_plus_position_interactions | MID | 1.0813 | 2.0441 | 0.6689 | 0.1000 | 0.0500 | 0.0600 |
| position_wise_models | MID | 1.0871 | 2.0482 | 0.6691 | 0.1000 | 0.0500 | 0.0600 |
| residual_Ridge | MID | 1.0873 | 2.0328 | 0.6748 | 0.1000 | 0.1000 | 0.0800 |
| residual_ElasticNet | MID | 1.0958 | 2.0348 | 0.6732 | 0.1000 | 0.1000 | 0.0800 |
| rolling_3_gameweek_mean | MID | 1.0994 | 2.2246 | 0.6934 | 0.2000 | 0.1000 | 0.0800 |
| Ridge | MID | 1.1089 | 2.0513 | 0.6625 | 0.1000 | 0.1000 | 0.0800 |
| global_model | MID | 1.1089 | 2.0513 | 0.6625 | 0.1000 | 0.1000 | 0.0800 |
| ElasticNet | MID | 1.1109 | 2.0517 | 0.6621 | 0.1000 | 0.1000 | 0.0800 |
| previous_gameweek_points | MID | 1.1869 | 2.6271 | 0.6616 | 0.0000 | 0.0500 | 0.0400 |

## Classification Rules

- `keep_core`: competitive overall and best or ranking-competitive somewhere.
- `keep_specialist`: not core, but near-best in at least one early, position, season, or ranking context.
- `remove_candidate`: not competitive overall, early-season, by position, by season, or on ranking metrics.
- `investigate`: incomplete or invalid metric coverage.

Near-best thresholds: within 1% of best MAE/RMSE, within 0.01 Spearman, or within 0.01 precision for top-k metrics.
