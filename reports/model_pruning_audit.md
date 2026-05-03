# Model Pruning Audit

Supported-season rolling-origin audit for model pruning. The audit replays predictions for seasons included by `--min-season 2020-21`; it does not change model code.

## Classification

| model | classification | overall_competitive | overall_primary_competitive | early_competitive | position_competitive | season_competitive | ranking_competitive | ever_best | ever_near_best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CatBoost | keep_core | True | True | True | True | True | True | True | True |
| XGBoost | keep_core | True | True | True | True | True | True | True | True |
| global_plus_position_interactions | keep_core | True | True | True | True | True | True | True | True |
| minutes_adjusted_rolling_mean | keep_core | True | True | True | True | True | True | True | True |
| residual_CatBoost | keep_core | True | True | True | True | True | True | True | True |
| residual_ElasticNet | keep_core | True | True | True | True | True | True | True | True |
| residual_LightGBM | keep_core | True | True | True | True | True | True | True | True |
| residual_Ridge | keep_core | True | True | True | True | True | True | True | True |
| residual_XGBoost | keep_core | True | True | True | True | True | True | True | True |
| rolling_3_gameweek_mean | keep_core | True | True | True | True | True | True | True | True |
| rolling_5_gameweek_mean | keep_core | True | True | True | True | True | True | True | True |
| ElasticNet | keep_specialist | False | False | True | True | True | True | True | True |
| LightGBM | keep_specialist | False | False | True | True | True | True | True | True |
| Ridge | keep_specialist | False | False | True | False | True | True | True | True |
| global_model | keep_specialist | False | False | True | False | True | True | True | True |
| position_wise_models | keep_specialist | False | False | True | True | True | True | True | True |
| previous_gameweek_points | keep_specialist | False | False | True | False | True | True | True | True |

## Best Overall By Metric

| metric | model | value |
| --- | --- | --- |
| mae | minutes_adjusted_rolling_mean | 1.0440 |
| rmse | residual_CatBoost | 2.0357 |
| spearman | minutes_adjusted_rolling_mean | 0.6613 |
| top_10_precision | rolling_3_gameweek_mean | 0.1000 |
| top_20_precision | rolling_3_gameweek_mean | 0.1000 |
| top_50_precision | rolling_3_gameweek_mean | 0.0600 |

## Overall Metrics

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 1.0440 | 2.1952 | 0.6613 | 0.0000 | 0.0000 | 0.0200 | True | True |
| residual_CatBoost | 1.0931 | 2.0357 | 0.6514 | 0.0000 | 0.0000 | 0.0200 | True | True |
| residual_XGBoost | 1.0935 | 2.0383 | 0.6488 | 0.0000 | 0.0000 | 0.0000 | True | False |
| residual_LightGBM | 1.1007 | 2.0549 | 0.6448 | 0.0000 | 0.0000 | 0.0000 | True | False |
| CatBoost | 1.1052 | 2.0480 | 0.6447 | 0.0000 | 0.0000 | 0.0200 | True | False |
| XGBoost | 1.1052 | 2.0483 | 0.6431 | 0.0000 | 0.0000 | 0.0200 | True | False |
| rolling_5_gameweek_mean | 1.1112 | 2.1820 | 0.6552 | 0.0000 | 0.0000 | 0.0200 | True | False |
| LightGBM | 1.1130 | 2.0683 | 0.6378 | 0.0000 | 0.0000 | 0.0000 | False | False |
| residual_Ridge | 1.1205 | 2.0443 | 0.6358 | 0.0000 | 0.0000 | 0.0200 | True | False |
| global_plus_position_interactions | 1.1262 | 2.0548 | 0.6316 | 0.0000 | 0.0000 | 0.0200 | True | False |
| residual_ElasticNet | 1.1297 | 2.0455 | 0.6348 | 0.0000 | 0.0000 | 0.0400 | True | False |
| position_wise_models | 1.1306 | 2.0577 | 0.6304 | 0.0000 | 0.0000 | 0.0200 | False | False |
| rolling_3_gameweek_mean | 1.1319 | 2.2620 | 0.6523 | 0.1000 | 0.1000 | 0.0600 | True | True |
| Ridge | 1.1393 | 2.0588 | 0.6281 | 0.0000 | 0.0000 | 0.0200 | False | False |
| global_model | 1.1393 | 2.0588 | 0.6281 | 0.0000 | 0.0000 | 0.0200 | False | False |
| ElasticNet | 1.1443 | 2.0590 | 0.6279 | 0.0000 | 0.0000 | 0.0400 | False | False |
| previous_gameweek_points | 1.2293 | 2.6776 | 0.6134 | 0.0000 | 0.0000 | 0.0200 | False | False |

## Early-Season Metrics: GW1-5

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 1.1761 | 2.3705 | 0.6444 | 0.0000 | 0.0500 | 0.0200 | True | True |
| residual_Ridge | 1.1854 | 2.0975 | 0.6267 | 0.0000 | 0.0000 | 0.0200 | True | False |
| residual_XGBoost | 1.1891 | 2.0961 | 0.6319 | 0.0000 | 0.0000 | 0.0200 | True | False |
| residual_CatBoost | 1.1896 | 2.0923 | 0.6332 | 0.0000 | 0.0000 | 0.0200 | True | True |
| residual_ElasticNet | 1.1933 | 2.0961 | 0.6280 | 0.0000 | 0.0500 | 0.0200 | True | True |
| residual_LightGBM | 1.1965 | 2.1159 | 0.6272 | 0.0000 | 0.0000 | 0.0200 | False | False |
| position_wise_models | 1.2289 | 2.2191 | 0.5648 | 0.0000 | 0.0000 | 0.0400 | True | True |
| rolling_3_gameweek_mean | 1.2378 | 2.4112 | 0.6382 | 0.0000 | 0.0500 | 0.0200 | True | True |
| rolling_5_gameweek_mean | 1.2384 | 2.4021 | 0.6365 | 0.0000 | 0.0500 | 0.0200 | True | True |
| Ridge | 1.2422 | 2.2189 | 0.5661 | 0.0000 | 0.0000 | 0.0200 | False | False |
| global_model | 1.2422 | 2.2189 | 0.5661 | 0.0000 | 0.0000 | 0.0200 | False | False |
| ElasticNet | 1.2443 | 2.2180 | 0.5666 | 0.0000 | 0.0000 | 0.0200 | False | False |
| CatBoost | 1.2724 | 2.1873 | 0.5764 | 0.0000 | 0.0000 | 0.0200 | False | False |
| global_plus_position_interactions | 1.2744 | 2.1992 | 0.5660 | 0.0000 | 0.0000 | 0.0400 | True | True |
| XGBoost | 1.2754 | 2.1909 | 0.5746 | 0.0000 | 0.0000 | 0.0200 | False | False |
| LightGBM | 1.2861 | 2.2076 | 0.5698 | 0.0000 | 0.0000 | 0.0000 | False | False |
| previous_gameweek_points | 1.3294 | 2.7498 | 0.6104 | 0.0000 | 0.0000 | 0.0400 | True | True |

## Models Beating Minutes-Adjusted Baseline In GW1-5 By MAE

None.

## Residual Model Early-Season Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| residual_CatBoost | 1.1896 | 2.0923 | 0.6332 | 0.0000 | 0.0000 | 0.0200 | True | True |
| residual_ElasticNet | 1.1933 | 2.0961 | 0.6280 | 0.0000 | 0.0500 | 0.0200 | True | True |
| residual_LightGBM | 1.1965 | 2.1159 | 0.6272 | 0.0000 | 0.0000 | 0.0200 | False | False |
| residual_Ridge | 1.1854 | 2.0975 | 0.6267 | 0.0000 | 0.0000 | 0.0200 | True | False |
| residual_XGBoost | 1.1891 | 2.0961 | 0.6319 | 0.0000 | 0.0000 | 0.0200 | True | False |

## Ridge And ElasticNet Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ElasticNet | 1.1443 | 2.0590 | 0.6279 | 0.0000 | 0.0000 | 0.0400 | False | False |
| Ridge | 1.1393 | 2.0588 | 0.6281 | 0.0000 | 0.0000 | 0.0200 | False | False |
| residual_ElasticNet | 1.1297 | 2.0455 | 0.6348 | 0.0000 | 0.0000 | 0.0400 | True | False |
| residual_Ridge | 1.1205 | 2.0443 | 0.6358 | 0.0000 | 0.0000 | 0.0200 | True | False |

## Tree/Boosting Model Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CatBoost | 1.1052 | 2.0480 | 0.6447 | 0.0000 | 0.0000 | 0.0200 | True | False |
| LightGBM | 1.1130 | 2.0683 | 0.6378 | 0.0000 | 0.0000 | 0.0000 | False | False |
| XGBoost | 1.1052 | 2.0483 | 0.6431 | 0.0000 | 0.0000 | 0.0200 | True | False |
| residual_CatBoost | 1.0931 | 2.0357 | 0.6514 | 0.0000 | 0.0000 | 0.0200 | True | True |
| residual_LightGBM | 1.1007 | 2.0549 | 0.6448 | 0.0000 | 0.0000 | 0.0000 | True | False |
| residual_XGBoost | 1.0935 | 2.0383 | 0.6488 | 0.0000 | 0.0000 | 0.0000 | True | False |

## Position Strategy Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_model | 1.1393 | 2.0588 | 0.6281 | 0.0000 | 0.0000 | 0.0200 | False | False |
| global_plus_position_interactions | 1.1262 | 2.0548 | 0.6316 | 0.0000 | 0.0000 | 0.0200 | True | False |
| position_wise_models | 1.1306 | 2.0577 | 0.6304 | 0.0000 | 0.0000 | 0.0200 | False | False |

## Season-By-Season Performance

| model | segment | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 2021-22 | 1.1390 | 2.3257 | 0.6275 | 0.0000 | 0.0000 | 0.0400 |
| residual_CatBoost | 2021-22 | 1.1946 | 2.1581 | 0.6191 | 0.0000 | 0.0500 | 0.0200 |
| residual_XGBoost | 2021-22 | 1.1975 | 2.1637 | 0.6156 | 0.0000 | 0.0000 | 0.0200 |
| XGBoost | 2021-22 | 1.2105 | 2.1723 | 0.6101 | 0.0000 | 0.0500 | 0.0200 |
| CatBoost | 2021-22 | 1.2118 | 2.1724 | 0.6127 | 0.0000 | 0.0500 | 0.0200 |
| rolling_5_gameweek_mean | 2021-22 | 1.2127 | 2.3106 | 0.6201 | 0.0000 | 0.0000 | 0.0400 |
| residual_LightGBM | 2021-22 | 1.2197 | 2.2033 | 0.6048 | 0.0000 | 0.0000 | 0.0000 |
| residual_Ridge | 2021-22 | 1.2222 | 2.1602 | 0.6084 | 0.0000 | 0.0000 | 0.0000 |
| residual_ElasticNet | 2021-22 | 1.2302 | 2.1629 | 0.6082 | 0.0000 | 0.0000 | 0.0400 |
| global_plus_position_interactions | 2021-22 | 1.2328 | 2.1723 | 0.6056 | 0.0000 | 0.0000 | 0.0000 |
| position_wise_models | 2021-22 | 1.2355 | 2.1741 | 0.6040 | 0.0000 | 0.0000 | 0.0000 |
| Ridge | 2021-22 | 1.2396 | 2.1728 | 0.6017 | 0.0000 | 0.0000 | 0.0200 |
| global_model | 2021-22 | 1.2396 | 2.1728 | 0.6017 | 0.0000 | 0.0000 | 0.0200 |
| LightGBM | 2021-22 | 1.2397 | 2.2261 | 0.5943 | 0.0000 | 0.0000 | 0.0200 |
| rolling_3_gameweek_mean | 2021-22 | 1.2435 | 2.4114 | 0.6168 | 0.0000 | 0.0000 | 0.0400 |
| ElasticNet | 2021-22 | 1.2437 | 2.1737 | 0.6019 | 0.0000 | 0.0000 | 0.0400 |
| previous_gameweek_points | 2021-22 | 1.3599 | 2.8622 | 0.5693 | 0.0000 | 0.0000 | 0.0000 |
| minutes_adjusted_rolling_mean | 2022-23 | 1.0663 | 2.1894 | 0.6659 | 0.0000 | 0.0000 | 0.0200 |
| residual_XGBoost | 2022-23 | 1.1122 | 2.0295 | 0.6604 | 0.0000 | 0.0500 | 0.0200 |
| residual_CatBoost | 2022-23 | 1.1149 | 2.0274 | 0.6618 | 0.0000 | 0.0000 | 0.0000 |
| residual_LightGBM | 2022-23 | 1.1191 | 2.0435 | 0.6551 | 0.0000 | 0.0000 | 0.0000 |
| CatBoost | 2022-23 | 1.1255 | 2.0421 | 0.6550 | 0.0000 | 0.0000 | 0.0000 |
| XGBoost | 2022-23 | 1.1265 | 2.0444 | 0.6541 | 0.0000 | 0.0000 | 0.0200 |
| LightGBM | 2022-23 | 1.1315 | 2.0550 | 0.6502 | 0.0000 | 0.0000 | 0.0400 |
| rolling_5_gameweek_mean | 2022-23 | 1.1362 | 2.1795 | 0.6578 | 0.0000 | 0.0500 | 0.0400 |
| residual_Ridge | 2022-23 | 1.1376 | 2.0399 | 0.6472 | 0.0000 | 0.0000 | 0.0200 |
| residual_ElasticNet | 2022-23 | 1.1450 | 2.0394 | 0.6470 | 0.0000 | 0.0000 | 0.0200 |
| global_plus_position_interactions | 2022-23 | 1.1490 | 2.0508 | 0.6394 | 0.0000 | 0.0000 | 0.0200 |
| position_wise_models | 2022-23 | 1.1550 | 2.0546 | 0.6384 | 0.0000 | 0.0000 | 0.0200 |
| rolling_3_gameweek_mean | 2022-23 | 1.1567 | 2.2569 | 0.6517 | 0.1000 | 0.0500 | 0.0200 |
| Ridge | 2022-23 | 1.1580 | 2.0576 | 0.6396 | 0.0000 | 0.0000 | 0.0200 |
| global_model | 2022-23 | 1.1580 | 2.0576 | 0.6396 | 0.0000 | 0.0000 | 0.0200 |
| ElasticNet | 2022-23 | 1.1620 | 2.0570 | 0.6399 | 0.0000 | 0.0000 | 0.0200 |
| previous_gameweek_points | 2022-23 | 1.2589 | 2.6951 | 0.6168 | 0.0000 | 0.0000 | 0.0000 |
| minutes_adjusted_rolling_mean | 2023-24 | 0.9648 | 2.1318 | 0.6578 | 0.0000 | 0.0500 | 0.0400 |
| rolling_5_gameweek_mean | 2023-24 | 1.0303 | 2.1198 | 0.6542 | 0.0000 | 0.0500 | 0.0400 |
| residual_XGBoost | 2023-24 | 1.0375 | 1.9950 | 0.6382 | 0.0000 | 0.0500 | 0.0400 |
| residual_CatBoost | 2023-24 | 1.0389 | 1.9956 | 0.6416 | 0.0000 | 0.0000 | 0.0200 |
| residual_LightGBM | 2023-24 | 1.0430 | 2.0101 | 0.6364 | 0.0000 | 0.0000 | 0.0600 |
| XGBoost | 2023-24 | 1.0464 | 1.9974 | 0.6340 | 0.0000 | 0.0500 | 0.0600 |
| CatBoost | 2023-24 | 1.0478 | 1.9989 | 0.6344 | 0.0000 | 0.0000 | 0.0600 |
| rolling_3_gameweek_mean | 2023-24 | 1.0503 | 2.1963 | 0.6500 | 0.1000 | 0.0500 | 0.0600 |
| LightGBM | 2023-24 | 1.0511 | 2.0141 | 0.6302 | 0.0000 | 0.0000 | 0.0600 |
| global_plus_position_interactions | 2023-24 | 1.0684 | 2.0005 | 0.6221 | 0.0000 | 0.0000 | 0.0400 |
| residual_Ridge | 2023-24 | 1.0695 | 2.0018 | 0.6235 | 0.1000 | 0.0500 | 0.0200 |
| position_wise_models | 2023-24 | 1.0717 | 2.0018 | 0.6210 | 0.0000 | 0.0000 | 0.0400 |
| residual_ElasticNet | 2023-24 | 1.0821 | 2.0031 | 0.6216 | 0.1000 | 0.0500 | 0.0400 |
| Ridge | 2023-24 | 1.0851 | 2.0067 | 0.6172 | 0.1000 | 0.0500 | 0.0200 |
| global_model | 2023-24 | 1.0851 | 2.0067 | 0.6172 | 0.1000 | 0.0500 | 0.0200 |
| ElasticNet | 2023-24 | 1.0933 | 2.0072 | 0.6166 | 0.1000 | 0.0500 | 0.0400 |
| previous_gameweek_points | 2023-24 | 1.1418 | 2.5994 | 0.6090 | 0.0000 | 0.0500 | 0.0400 |
| minutes_adjusted_rolling_mean | 2024-25 | 1.0168 | 2.1315 | 0.6680 | 0.1000 | 0.1500 | 0.1000 |
| residual_CatBoost | 2024-25 | 1.0662 | 1.9830 | 0.6605 | 0.0000 | 0.0000 | 0.0600 |
| residual_XGBoost | 2024-25 | 1.0672 | 1.9862 | 0.6587 | 0.0000 | 0.0000 | 0.0200 |
| residual_LightGBM | 2024-25 | 1.0688 | 1.9940 | 0.6567 | 0.0000 | 0.0000 | 0.0200 |
| CatBoost | 2024-25 | 1.0758 | 1.9965 | 0.6550 | 0.0000 | 0.0000 | 0.0400 |
| LightGBM | 2024-25 | 1.0769 | 2.0074 | 0.6503 | 0.0000 | 0.0000 | 0.0200 |
| XGBoost | 2024-25 | 1.0783 | 1.9976 | 0.6525 | 0.0000 | 0.0000 | 0.0400 |
| rolling_5_gameweek_mean | 2024-25 | 1.0815 | 2.1158 | 0.6629 | 0.1000 | 0.1500 | 0.1200 |
| global_plus_position_interactions | 2024-25 | 1.0867 | 2.0036 | 0.6408 | 0.1000 | 0.1000 | 0.1200 |
| residual_Ridge | 2024-25 | 1.0902 | 1.9924 | 0.6446 | 0.1000 | 0.1000 | 0.1000 |
| position_wise_models | 2024-25 | 1.0926 | 2.0073 | 0.6400 | 0.1000 | 0.1000 | 0.1000 |
| residual_ElasticNet | 2024-25 | 1.0972 | 1.9931 | 0.6431 | 0.1000 | 0.1500 | 0.1000 |
| rolling_3_gameweek_mean | 2024-25 | 1.1068 | 2.2010 | 0.6596 | 0.1000 | 0.1000 | 0.1000 |
| Ridge | 2024-25 | 1.1092 | 2.0095 | 0.6367 | 0.1000 | 0.1000 | 0.1000 |
| global_model | 2024-25 | 1.1092 | 2.0095 | 0.6367 | 0.1000 | 0.1000 | 0.1000 |
| ElasticNet | 2024-25 | 1.1125 | 2.0095 | 0.6364 | 0.1000 | 0.1000 | 0.1000 |
| previous_gameweek_points | 2024-25 | 1.1938 | 2.5890 | 0.6180 | 0.0000 | 0.0500 | 0.0600 |
| minutes_adjusted_rolling_mean | 2025-26 | 1.0478 | 2.2088 | 0.6886 | 0.0000 | 0.0000 | 0.0200 |
| residual_CatBoost | 2025-26 | 1.0561 | 2.0182 | 0.6716 | 0.0000 | 0.0000 | 0.0200 |
| residual_LightGBM | 2025-26 | 1.0586 | 2.0246 | 0.6687 | 0.0000 | 0.0000 | 0.0400 |
| residual_XGBoost | 2025-26 | 1.0587 | 2.0212 | 0.6686 | 0.0000 | 0.0000 | 0.0200 |
| XGBoost | 2025-26 | 1.0706 | 2.0355 | 0.6632 | 0.0000 | 0.0500 | 0.0400 |
| CatBoost | 2025-26 | 1.0715 | 2.0353 | 0.6647 | 0.0000 | 0.0000 | 0.0200 |
| LightGBM | 2025-26 | 1.0729 | 2.0417 | 0.6625 | 0.0000 | 0.0500 | 0.0400 |
| residual_Ridge | 2025-26 | 1.0892 | 2.0319 | 0.6540 | 0.0000 | 0.0000 | 0.0400 |
| residual_ElasticNet | 2025-26 | 1.0997 | 2.0342 | 0.6530 | 0.0000 | 0.0000 | 0.0400 |
| global_plus_position_interactions | 2025-26 | 1.1028 | 2.0546 | 0.6499 | 0.0000 | 0.0000 | 0.0000 |
| position_wise_models | 2025-26 | 1.1067 | 2.0590 | 0.6498 | 0.0000 | 0.0000 | 0.0200 |
| rolling_5_gameweek_mean | 2025-26 | 1.1098 | 2.1956 | 0.6812 | 0.0000 | 0.0000 | 0.0400 |
| Ridge | 2025-26 | 1.1119 | 2.0543 | 0.6447 | 0.0000 | 0.0500 | 0.0400 |
| global_model | 2025-26 | 1.1119 | 2.0543 | 0.6447 | 0.0000 | 0.0500 | 0.0400 |
| rolling_3_gameweek_mean | 2025-26 | 1.1143 | 2.2519 | 0.6845 | 0.0000 | 0.0000 | 0.0000 |
| ElasticNet | 2025-26 | 1.1169 | 2.0551 | 0.6446 | 0.0000 | 0.0000 | 0.0400 |
| previous_gameweek_points | 2025-26 | 1.2049 | 2.6474 | 0.6578 | 0.0000 | 0.0000 | 0.0000 |

## Position-Specific Performance

| model | segment | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | DEF | 1.1212 | 2.2400 | 0.5634 | 0.0000 | 0.0000 | 0.0000 |
| residual_Ridge | DEF | 1.1943 | 2.0845 | 0.5555 | 0.0000 | 0.0000 | 0.0000 |
| residual_XGBoost | DEF | 1.1962 | 2.0794 | 0.5656 | 0.0000 | 0.0000 | 0.0000 |
| residual_LightGBM | DEF | 1.1976 | 2.0955 | 0.5606 | 0.0000 | 0.0000 | 0.0000 |
| residual_ElasticNet | DEF | 1.2022 | 2.0848 | 0.5553 | 0.0000 | 0.0000 | 0.0000 |
| rolling_5_gameweek_mean | DEF | 1.2022 | 2.2457 | 0.5528 | 0.0000 | 0.0000 | 0.0000 |
| residual_CatBoost | DEF | 1.2043 | 2.0783 | 0.5662 | 0.0000 | 0.0000 | 0.0000 |
| XGBoost | DEF | 1.2069 | 2.0890 | 0.5608 | 0.0000 | 0.0000 | 0.0000 |
| LightGBM | DEF | 1.2082 | 2.1095 | 0.5541 | 0.0000 | 0.0000 | 0.0000 |
| CatBoost | DEF | 1.2097 | 2.0881 | 0.5609 | 0.0000 | 0.0000 | 0.0000 |
| Ridge | DEF | 1.2099 | 2.1000 | 0.5483 | 0.0000 | 0.0000 | 0.0000 |
| global_model | DEF | 1.2099 | 2.1000 | 0.5483 | 0.0000 | 0.0000 | 0.0000 |
| ElasticNet | DEF | 1.2166 | 2.0999 | 0.5486 | 0.0000 | 0.0000 | 0.0200 |
| global_plus_position_interactions | DEF | 1.2168 | 2.0968 | 0.5375 | 0.0000 | 0.0000 | 0.0000 |
| position_wise_models | DEF | 1.2214 | 2.1003 | 0.5368 | 0.0000 | 0.0000 | 0.0000 |
| rolling_3_gameweek_mean | DEF | 1.2233 | 2.3289 | 0.5471 | 0.0000 | 0.0000 | 0.0200 |
| previous_gameweek_points | DEF | 1.3290 | 2.7481 | 0.4926 | 0.0000 | 0.0000 | 0.0000 |
| minutes_adjusted_rolling_mean | FWD | 1.1341 | 2.4263 | 0.7010 | 0.0000 | 0.0000 | 0.0400 |
| residual_CatBoost | FWD | 1.1830 | 2.2430 | 0.6831 | 0.0000 | 0.0000 | 0.0400 |
| residual_XGBoost | FWD | 1.1835 | 2.2473 | 0.6808 | 0.0000 | 0.0000 | 0.0400 |
| residual_LightGBM | FWD | 1.1967 | 2.2675 | 0.6754 | 0.0000 | 0.0000 | 0.0200 |
| XGBoost | FWD | 1.2008 | 2.2523 | 0.6734 | 0.0000 | 0.0000 | 0.0000 |
| CatBoost | FWD | 1.2030 | 2.2511 | 0.6740 | 0.0000 | 0.0000 | 0.0000 |
| LightGBM | FWD | 1.2214 | 2.2802 | 0.6637 | 0.0000 | 0.0000 | 0.0000 |
| rolling_5_gameweek_mean | FWD | 1.2232 | 2.4032 | 0.6932 | 0.0000 | 0.0000 | 0.0400 |
| rolling_3_gameweek_mean | FWD | 1.2342 | 2.4738 | 0.6917 | 0.1000 | 0.0500 | 0.0200 |
| residual_ElasticNet | FWD | 1.2579 | 2.2599 | 0.6702 | 0.0000 | 0.0000 | 0.0200 |
| global_plus_position_interactions | FWD | 1.2584 | 2.2651 | 0.6572 | 0.0000 | 0.0000 | 0.0200 |
| residual_Ridge | FWD | 1.2597 | 2.2580 | 0.6710 | 0.0000 | 0.0000 | 0.0000 |
| position_wise_models | FWD | 1.2609 | 2.2652 | 0.6597 | 0.0000 | 0.0000 | 0.0200 |
| ElasticNet | FWD | 1.2738 | 2.2680 | 0.6638 | 0.0000 | 0.0000 | 0.0200 |
| Ridge | FWD | 1.2819 | 2.2681 | 0.6634 | 0.0000 | 0.0000 | 0.0000 |
| global_model | FWD | 1.2819 | 2.2681 | 0.6634 | 0.0000 | 0.0000 | 0.0000 |
| previous_gameweek_points | FWD | 1.3338 | 2.9326 | 0.6567 | 0.0000 | 0.0000 | 0.0200 |
| minutes_adjusted_rolling_mean | GK | 0.7150 | 1.7175 | 0.7775 | 0.0000 | 0.0000 | 0.0000 |
| rolling_5_gameweek_mean | GK | 0.7371 | 1.7114 | 0.7728 | 0.0000 | 0.0000 | 0.0000 |
| rolling_3_gameweek_mean | GK | 0.7451 | 1.7694 | 0.7845 | 0.0000 | 0.0000 | 0.0000 |
| residual_CatBoost | GK | 0.7579 | 1.5810 | 0.6405 | 0.0000 | 0.0000 | 0.0400 |
| global_plus_position_interactions | GK | 0.7714 | 1.6092 | 0.6341 | 0.0000 | 0.0000 | 0.0200 |
| residual_XGBoost | GK | 0.7785 | 1.5831 | 0.6401 | 0.0000 | 0.0000 | 0.0400 |
| CatBoost | GK | 0.7789 | 1.6066 | 0.6379 | 0.0000 | 0.0000 | 0.0200 |
| position_wise_models | GK | 0.7793 | 1.6163 | 0.6180 | 0.0000 | 0.0000 | 0.0200 |
| residual_LightGBM | GK | 0.7810 | 1.5966 | 0.6370 | 0.0000 | 0.0000 | 0.0000 |
| XGBoost | GK | 0.7977 | 1.6070 | 0.6375 | 0.0000 | 0.0000 | 0.0400 |
| LightGBM | GK | 0.7988 | 1.6230 | 0.6339 | 0.1000 | 0.1000 | 0.0400 |
| residual_Ridge | GK | 0.8102 | 1.5884 | 0.6366 | 0.0000 | 0.0000 | 0.0000 |
| previous_gameweek_points | GK | 0.8238 | 2.1066 | 0.7713 | 0.0000 | 0.0000 | 0.0000 |
| residual_ElasticNet | GK | 0.8267 | 1.5899 | 0.6369 | 0.0000 | 0.0000 | 0.0000 |
| Ridge | GK | 0.8333 | 1.6166 | 0.6333 | 0.0000 | 0.0000 | 0.0000 |
| global_model | GK | 0.8333 | 1.6166 | 0.6333 | 0.0000 | 0.0000 | 0.0000 |
| ElasticNet | GK | 0.8498 | 1.6177 | 0.6335 | 0.0000 | 0.0000 | 0.0000 |
| minutes_adjusted_rolling_mean | MID | 1.0434 | 2.2014 | 0.6924 | 0.0000 | 0.0500 | 0.0200 |
| residual_CatBoost | MID | 1.0680 | 2.0451 | 0.6826 | 0.0000 | 0.0000 | 0.0200 |
| residual_XGBoost | MID | 1.0697 | 2.0485 | 0.6806 | 0.0000 | 0.0000 | 0.0400 |
| XGBoost | MID | 1.0787 | 2.0577 | 0.6747 | 0.0000 | 0.0000 | 0.0400 |
| CatBoost | MID | 1.0807 | 2.0580 | 0.6748 | 0.0000 | 0.0000 | 0.0400 |
| residual_LightGBM | MID | 1.0810 | 2.0651 | 0.6759 | 0.0000 | 0.0000 | 0.0000 |
| LightGBM | MID | 1.0898 | 2.0758 | 0.6690 | 0.0000 | 0.0000 | 0.0200 |
| residual_Ridge | MID | 1.1043 | 2.0538 | 0.6715 | 0.0000 | 0.0500 | 0.0400 |
| rolling_5_gameweek_mean | MID | 1.1055 | 2.1748 | 0.6843 | 0.0000 | 0.0500 | 0.0400 |
| global_plus_position_interactions | MID | 1.1103 | 2.0619 | 0.6627 | 0.0000 | 0.0500 | 0.0200 |
| position_wise_models | MID | 1.1141 | 2.0644 | 0.6624 | 0.0000 | 0.0500 | 0.0200 |
| residual_ElasticNet | MID | 1.1156 | 2.0557 | 0.6706 | 0.0000 | 0.0500 | 0.0400 |
| Ridge | MID | 1.1235 | 2.0663 | 0.6626 | 0.0000 | 0.0500 | 0.0400 |
| global_model | MID | 1.1235 | 2.0663 | 0.6626 | 0.0000 | 0.0500 | 0.0400 |
| ElasticNet | MID | 1.1279 | 2.0668 | 0.6627 | 0.0000 | 0.0500 | 0.0400 |
| rolling_3_gameweek_mean | MID | 1.1318 | 2.2602 | 0.6817 | 0.1000 | 0.1000 | 0.0600 |
| previous_gameweek_points | MID | 1.2270 | 2.6785 | 0.6469 | 0.0000 | 0.0000 | 0.0200 |

## Classification Rules

- `keep_core`: competitive overall and best or ranking-competitive somewhere.
- `keep_specialist`: not core, but near-best in at least one early, position, season, or ranking context.
- `remove_candidate`: not competitive overall, early-season, by position, by season, or on ranking metrics.
- `investigate`: incomplete or invalid metric coverage.

Near-best thresholds: within 1% of best MAE/RMSE, within 0.01 Spearman, or within 0.01 precision for top-k metrics.
