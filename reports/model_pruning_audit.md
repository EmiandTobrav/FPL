# Model Pruning Audit

Rich-feature-season rolling-origin audit for model pruning. The audit replays predictions from the current default trimmed modelling dataset; it does not change model code.

## Pruning Summary

- Validation seasons audited: 2023-24, 2024-25, 2025-26.
- Definitely keep: `CatBoost`, `ElasticNet`, `Ridge`, `XGBoost`, `global_plus_position_interactions`, `minutes_adjusted_rolling_mean`, `position_wise_models`, `residual_CatBoost`, `residual_ElasticNet`, `residual_Ridge`, `residual_XGBoost`, `rolling_3_gameweek_mean`, `rolling_5_gameweek_mean`.
- Specialist only: `LightGBM`, `residual_LightGBM`.
- Remove candidates: None.
- Investigate: None.
- No model beats `minutes_adjusted_rolling_mean` in GW1-5 by MAE.
- Residual models remain useful under the trimmed dataset.
- Ridge and ElasticNet are still worth keeping in this audit: `ElasticNet`=keep_core, `Ridge`=keep_core, `residual_ElasticNet`=keep_core, `residual_Ridge`=keep_core.
- LightGBM status: `LightGBM`=keep_specialist; `residual_LightGBM`=keep_specialist.
- Position-wise model status: `position_wise_models`=keep_core.

## Classification

| model | classification | overall_competitive | overall_primary_competitive | early_competitive | position_competitive | season_competitive | ranking_competitive | ever_best | ever_near_best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CatBoost | keep_core | True | True | True | True | True | True | True | True |
| ElasticNet | keep_core | True | True | True | True | True | True | True | True |
| Ridge | keep_core | True | True | True | True | True | True | True | True |
| XGBoost | keep_core | True | True | True | True | True | True | True | True |
| global_plus_position_interactions | keep_core | True | True | True | True | True | True | True | True |
| minutes_adjusted_rolling_mean | keep_core | True | True | True | True | True | True | True | True |
| position_wise_models | keep_core | True | True | True | True | True | True | True | True |
| residual_CatBoost | keep_core | True | True | True | True | True | True | True | True |
| residual_ElasticNet | keep_core | True | True | True | True | True | True | True | True |
| residual_Ridge | keep_core | True | True | True | True | True | True | True | True |
| residual_XGBoost | keep_core | True | True | True | True | True | True | True | True |
| rolling_3_gameweek_mean | keep_core | True | True | True | True | True | True | True | True |
| rolling_5_gameweek_mean | keep_core | True | True | True | True | True | True | True | True |
| LightGBM | keep_specialist | False | False | True | False | True | True | True | True |
| residual_LightGBM | keep_specialist | False | False | True | True | True | True | True | True |

## Best Overall By Metric

| metric | model | value |
| --- | --- | --- |
| mae | minutes_adjusted_rolling_mean | 1.0059 |
| rmse | residual_CatBoost | 2.0051 |
| spearman | minutes_adjusted_rolling_mean | 0.6706 |
| top_10_precision | rolling_3_gameweek_mean | 0.1000 |
| top_20_precision | rolling_3_gameweek_mean | 0.1000 |
| top_50_precision | Ridge | 0.0600 |

## Overall Metrics

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 1.0059 | 2.1534 | 0.6706 | 0.0000 | 0.0500 | 0.0400 | True | True |
| residual_CatBoost | 1.0464 | 2.0051 | 0.6541 | 0.0000 | 0.0500 | 0.0400 | True | True |
| residual_XGBoost | 1.0485 | 2.0066 | 0.6529 | 0.0000 | 0.1000 | 0.0400 | True | True |
| residual_LightGBM | 1.0574 | 2.0289 | 0.6482 | 0.0000 | 0.0000 | 0.0000 | False | False |
| CatBoost | 1.0592 | 2.0133 | 0.6481 | 0.0000 | 0.0500 | 0.0200 | True | False |
| XGBoost | 1.0609 | 2.0149 | 0.6478 | 0.0000 | 0.0500 | 0.0400 | True | False |
| LightGBM | 1.0678 | 2.0347 | 0.6426 | 0.0000 | 0.0000 | 0.0200 | False | False |
| rolling_5_gameweek_mean | 1.0701 | 2.1398 | 0.6655 | 0.0000 | 0.0500 | 0.0400 | True | False |
| residual_Ridge | 1.0812 | 2.0076 | 0.6374 | 0.0000 | 0.0500 | 0.0600 | True | True |
| global_plus_position_interactions | 1.0812 | 2.0185 | 0.6343 | 0.0000 | 0.0500 | 0.0200 | True | False |
| position_wise_models | 1.0875 | 2.0224 | 0.6322 | 0.0000 | 0.0500 | 0.0200 | True | False |
| rolling_3_gameweek_mean | 1.0876 | 2.2135 | 0.6638 | 0.1000 | 0.1000 | 0.0400 | True | True |
| residual_ElasticNet | 1.0888 | 2.0095 | 0.6353 | 0.0000 | 0.0500 | 0.0600 | True | True |
| Ridge | 1.1002 | 2.0226 | 0.6247 | 0.0000 | 0.0500 | 0.0600 | True | True |
| ElasticNet | 1.1036 | 2.0231 | 0.6240 | 0.0000 | 0.0500 | 0.0600 | True | True |

## Early-Season Metrics: GW1-5

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 1.1114 | 2.2886 | 0.6533 | 0.1000 | 0.0500 | 0.0800 | True | True |
| residual_CatBoost | 1.1261 | 2.0691 | 0.6340 | 0.0000 | 0.0000 | 0.1000 | True | False |
| residual_XGBoost | 1.1286 | 2.0768 | 0.6322 | 0.0000 | 0.0000 | 0.0800 | False | False |
| residual_Ridge | 1.1398 | 2.0542 | 0.6314 | 0.1000 | 0.0500 | 0.1000 | True | True |
| residual_LightGBM | 1.1418 | 2.1054 | 0.6265 | 0.0000 | 0.0500 | 0.0800 | False | False |
| residual_ElasticNet | 1.1453 | 2.0549 | 0.6300 | 0.1000 | 0.0500 | 0.1200 | True | True |
| rolling_3_gameweek_mean | 1.1701 | 2.3238 | 0.6496 | 0.1000 | 0.0500 | 0.0800 | True | True |
| rolling_5_gameweek_mean | 1.1706 | 2.3141 | 0.6477 | 0.1000 | 0.0500 | 0.1000 | True | True |
| position_wise_models | 1.1738 | 2.1685 | 0.5670 | 0.0000 | 0.0500 | 0.0600 | False | False |
| Ridge | 1.1883 | 2.1750 | 0.5482 | 0.0000 | 0.0500 | 0.0600 | False | False |
| ElasticNet | 1.1887 | 2.1745 | 0.5462 | 0.0000 | 0.0500 | 0.0800 | False | False |
| CatBoost | 1.2007 | 2.1493 | 0.5787 | 0.1000 | 0.0500 | 0.0600 | True | True |
| XGBoost | 1.2043 | 2.1529 | 0.5810 | 0.1000 | 0.1000 | 0.0800 | True | True |
| LightGBM | 1.2141 | 2.1679 | 0.5739 | 0.1000 | 0.1000 | 0.0800 | True | True |
| global_plus_position_interactions | 1.2153 | 2.1433 | 0.5698 | 0.0000 | 0.0500 | 0.0800 | False | False |

## Models Beating Minutes-Adjusted Baseline In GW1-5 By MAE

None.

## Residual Model Early-Season Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| residual_CatBoost | 1.1261 | 2.0691 | 0.6340 | 0.0000 | 0.0000 | 0.1000 | True | False |
| residual_ElasticNet | 1.1453 | 2.0549 | 0.6300 | 0.1000 | 0.0500 | 0.1200 | True | True |
| residual_LightGBM | 1.1418 | 2.1054 | 0.6265 | 0.0000 | 0.0500 | 0.0800 | False | False |
| residual_Ridge | 1.1398 | 2.0542 | 0.6314 | 0.1000 | 0.0500 | 0.1000 | True | True |
| residual_XGBoost | 1.1286 | 2.0768 | 0.6322 | 0.0000 | 0.0000 | 0.0800 | False | False |

## Ridge And ElasticNet Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| ElasticNet | 1.1036 | 2.0231 | 0.6240 | 0.0000 | 0.0500 | 0.0600 | True | True |
| Ridge | 1.1002 | 2.0226 | 0.6247 | 0.0000 | 0.0500 | 0.0600 | True | True |
| residual_ElasticNet | 1.0888 | 2.0095 | 0.6353 | 0.0000 | 0.0500 | 0.0600 | True | True |
| residual_Ridge | 1.0812 | 2.0076 | 0.6374 | 0.0000 | 0.0500 | 0.0600 | True | True |

## Tree/Boosting Model Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| CatBoost | 1.0592 | 2.0133 | 0.6481 | 0.0000 | 0.0500 | 0.0200 | True | False |
| LightGBM | 1.0678 | 2.0347 | 0.6426 | 0.0000 | 0.0000 | 0.0200 | False | False |
| XGBoost | 1.0609 | 2.0149 | 0.6478 | 0.0000 | 0.0500 | 0.0400 | True | False |
| residual_CatBoost | 1.0464 | 2.0051 | 0.6541 | 0.0000 | 0.0500 | 0.0400 | True | True |
| residual_LightGBM | 1.0574 | 2.0289 | 0.6482 | 0.0000 | 0.0000 | 0.0000 | False | False |
| residual_XGBoost | 1.0485 | 2.0066 | 0.6529 | 0.0000 | 0.1000 | 0.0400 | True | True |

## Position Strategy Check

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision | is_near_best_any_metric | is_best_any_metric |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_plus_position_interactions | 1.0812 | 2.0185 | 0.6343 | 0.0000 | 0.0500 | 0.0200 | True | False |
| position_wise_models | 1.0875 | 2.0224 | 0.6322 | 0.0000 | 0.0500 | 0.0200 | True | False |

## Season-By-Season Performance

| model | segment | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 2023-24 | 0.9648 | 2.1318 | 0.6578 | 0.0000 | 0.0500 | 0.0400 |
| rolling_5_gameweek_mean | 2023-24 | 1.0303 | 2.1198 | 0.6542 | 0.0000 | 0.0500 | 0.0400 |
| residual_CatBoost | 2023-24 | 1.0393 | 2.0118 | 0.6356 | 0.0000 | 0.0000 | 0.0400 |
| residual_XGBoost | 2023-24 | 1.0420 | 2.0079 | 0.6341 | 0.1000 | 0.0500 | 0.0400 |
| rolling_3_gameweek_mean | 2023-24 | 1.0503 | 2.1963 | 0.6500 | 0.1000 | 0.0500 | 0.0600 |
| CatBoost | 2023-24 | 1.0528 | 2.0110 | 0.6299 | 0.0000 | 0.0000 | 0.0600 |
| XGBoost | 2023-24 | 1.0565 | 2.0095 | 0.6299 | 0.0000 | 0.0500 | 0.0600 |
| residual_LightGBM | 2023-24 | 1.0583 | 2.0462 | 0.6268 | 0.0000 | 0.0000 | 0.0600 |
| LightGBM | 2023-24 | 1.0674 | 2.0445 | 0.6214 | 0.0000 | 0.0500 | 0.0200 |
| global_plus_position_interactions | 2023-24 | 1.0786 | 2.0048 | 0.6158 | 0.0000 | 0.0000 | 0.0200 |
| position_wise_models | 2023-24 | 1.0835 | 2.0065 | 0.6141 | 0.0000 | 0.0000 | 0.0200 |
| residual_Ridge | 2023-24 | 1.0838 | 2.0037 | 0.6182 | 0.1000 | 0.0500 | 0.0400 |
| residual_ElasticNet | 2023-24 | 1.0930 | 2.0057 | 0.6153 | 0.1000 | 0.0500 | 0.0600 |
| Ridge | 2023-24 | 1.0994 | 2.0089 | 0.6096 | 0.1000 | 0.0500 | 0.0400 |
| ElasticNet | 2023-24 | 1.1040 | 2.0095 | 0.6089 | 0.1000 | 0.0500 | 0.0400 |
| minutes_adjusted_rolling_mean | 2024-25 | 1.0168 | 2.1315 | 0.6680 | 0.1000 | 0.1500 | 0.1000 |
| residual_CatBoost | 2024-25 | 1.0551 | 1.9832 | 0.6593 | 0.1000 | 0.0500 | 0.0800 |
| residual_XGBoost | 2024-25 | 1.0553 | 1.9886 | 0.6588 | 0.1000 | 0.0500 | 0.1000 |
| residual_LightGBM | 2024-25 | 1.0619 | 2.0059 | 0.6544 | 0.0000 | 0.0000 | 0.0200 |
| CatBoost | 2024-25 | 1.0646 | 1.9964 | 0.6536 | 0.1000 | 0.0500 | 0.0800 |
| XGBoost | 2024-25 | 1.0665 | 2.0000 | 0.6533 | 0.1000 | 0.0500 | 0.1000 |
| LightGBM | 2024-25 | 1.0747 | 2.0150 | 0.6478 | 0.0000 | 0.0000 | 0.0800 |
| global_plus_position_interactions | 2024-25 | 1.0769 | 2.0040 | 0.6406 | 0.1000 | 0.1000 | 0.1200 |
| residual_Ridge | 2024-25 | 1.0812 | 1.9922 | 0.6441 | 0.1000 | 0.1000 | 0.1000 |
| rolling_5_gameweek_mean | 2024-25 | 1.0815 | 2.1158 | 0.6629 | 0.1000 | 0.1500 | 0.1200 |
| position_wise_models | 2024-25 | 1.0849 | 2.0089 | 0.6382 | 0.1000 | 0.1000 | 0.1200 |
| residual_ElasticNet | 2024-25 | 1.0862 | 1.9932 | 0.6425 | 0.1000 | 0.1500 | 0.1000 |
| Ridge | 2024-25 | 1.1006 | 2.0104 | 0.6308 | 0.1000 | 0.1000 | 0.1000 |
| ElasticNet | 2024-25 | 1.1022 | 2.0104 | 0.6302 | 0.1000 | 0.1500 | 0.1000 |
| rolling_3_gameweek_mean | 2024-25 | 1.1068 | 2.2010 | 0.6596 | 0.1000 | 0.1000 | 0.1000 |
| residual_CatBoost | 2025-26 | 1.0454 | 2.0231 | 0.6703 | 0.0000 | 0.0000 | 0.0400 |
| minutes_adjusted_rolling_mean | 2025-26 | 1.0478 | 2.2088 | 0.6886 | 0.0000 | 0.0000 | 0.0200 |
| residual_XGBoost | 2025-26 | 1.0487 | 2.0270 | 0.6684 | 0.0000 | 0.0000 | 0.0000 |
| residual_LightGBM | 2025-26 | 1.0504 | 2.0339 | 0.6675 | 0.0000 | 0.0000 | 0.0200 |
| LightGBM | 2025-26 | 1.0597 | 2.0457 | 0.6633 | 0.0000 | 0.0000 | 0.0200 |
| XGBoost | 2025-26 | 1.0600 | 2.0401 | 0.6638 | 0.0000 | 0.0000 | 0.0200 |
| CatBoost | 2025-26 | 1.0611 | 2.0370 | 0.6646 | 0.0000 | 0.0000 | 0.0200 |
| residual_Ridge | 2025-26 | 1.0777 | 2.0319 | 0.6532 | 0.0000 | 0.0000 | 0.0400 |
| residual_ElasticNet | 2025-26 | 1.0863 | 2.0347 | 0.6519 | 0.0000 | 0.0000 | 0.0400 |
| global_plus_position_interactions | 2025-26 | 1.0900 | 2.0541 | 0.6507 | 0.0000 | 0.0000 | 0.0400 |
| position_wise_models | 2025-26 | 1.0959 | 2.0596 | 0.6496 | 0.0000 | 0.0000 | 0.0400 |
| Ridge | 2025-26 | 1.1009 | 2.0556 | 0.6382 | 0.0000 | 0.0000 | 0.0400 |
| ElasticNet | 2025-26 | 1.1049 | 2.0564 | 0.6378 | 0.0000 | 0.0000 | 0.0400 |
| rolling_5_gameweek_mean | 2025-26 | 1.1098 | 2.1956 | 0.6812 | 0.0000 | 0.0000 | 0.0400 |
| rolling_3_gameweek_mean | 2025-26 | 1.1143 | 2.2519 | 0.6845 | 0.0000 | 0.0000 | 0.0000 |

## Position-Specific Performance

| model | segment | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | DEF | 1.0738 | 2.1857 | 0.5736 | 0.0000 | 0.0000 | 0.0000 |
| residual_Ridge | DEF | 1.1237 | 2.0373 | 0.5607 | 0.0000 | 0.0000 | 0.0200 |
| residual_ElasticNet | DEF | 1.1296 | 2.0380 | 0.5598 | 0.0000 | 0.0000 | 0.0200 |
| residual_XGBoost | DEF | 1.1296 | 2.0394 | 0.5693 | 0.0000 | 0.0000 | 0.0000 |
| residual_CatBoost | DEF | 1.1334 | 2.0397 | 0.5696 | 0.0000 | 0.0000 | 0.0000 |
| XGBoost | DEF | 1.1351 | 2.0405 | 0.5660 | 0.0000 | 0.0000 | 0.0000 |
| residual_LightGBM | DEF | 1.1359 | 2.0625 | 0.5611 | 0.0000 | 0.0000 | 0.0000 |
| Ridge | DEF | 1.1378 | 2.0484 | 0.5506 | 0.0000 | 0.0000 | 0.0200 |
| CatBoost | DEF | 1.1380 | 2.0404 | 0.5650 | 0.0000 | 0.0000 | 0.0000 |
| global_plus_position_interactions | DEF | 1.1414 | 2.0477 | 0.5435 | 0.0000 | 0.0000 | 0.0400 |
| LightGBM | DEF | 1.1420 | 2.0618 | 0.5581 | 0.0000 | 0.0000 | 0.0000 |
| ElasticNet | DEF | 1.1435 | 2.0484 | 0.5504 | 0.0000 | 0.0000 | 0.0200 |
| position_wise_models | DEF | 1.1487 | 2.0518 | 0.5396 | 0.0000 | 0.0500 | 0.0400 |
| rolling_5_gameweek_mean | DEF | 1.1488 | 2.1901 | 0.5642 | 0.0000 | 0.0000 | 0.0000 |
| rolling_3_gameweek_mean | DEF | 1.1659 | 2.2643 | 0.5582 | 0.0000 | 0.0500 | 0.0200 |
| minutes_adjusted_rolling_mean | FWD | 1.0946 | 2.3818 | 0.7233 | 0.0000 | 0.0000 | 0.0400 |
| residual_XGBoost | FWD | 1.1613 | 2.2146 | 0.6923 | 0.0000 | 0.0500 | 0.0800 |
| residual_CatBoost | FWD | 1.1613 | 2.2136 | 0.6918 | 0.0000 | 0.0500 | 0.0600 |
| CatBoost | FWD | 1.1682 | 2.2124 | 0.6862 | 0.0000 | 0.0000 | 0.1000 |
| rolling_5_gameweek_mean | FWD | 1.1742 | 2.3555 | 0.7170 | 0.0000 | 0.0000 | 0.0600 |
| residual_LightGBM | FWD | 1.1751 | 2.2401 | 0.6860 | 0.0000 | 0.0000 | 0.0600 |
| XGBoost | FWD | 1.1805 | 2.2186 | 0.6858 | 0.0000 | 0.0000 | 0.0600 |
| LightGBM | FWD | 1.1842 | 2.2416 | 0.6794 | 0.0000 | 0.0000 | 0.0800 |
| rolling_3_gameweek_mean | FWD | 1.1935 | 2.4450 | 0.7172 | 0.0000 | 0.0000 | 0.0200 |
| global_plus_position_interactions | FWD | 1.2407 | 2.2196 | 0.6631 | 0.0000 | 0.0000 | 0.0400 |
| position_wise_models | FWD | 1.2444 | 2.2214 | 0.6628 | 0.0000 | 0.0000 | 0.0400 |
| residual_ElasticNet | FWD | 1.2516 | 2.2215 | 0.6766 | 0.0000 | 0.0000 | 0.0600 |
| residual_Ridge | FWD | 1.2519 | 2.2170 | 0.6797 | 0.0000 | 0.0000 | 0.0600 |
| ElasticNet | FWD | 1.2573 | 2.2247 | 0.6676 | 0.0000 | 0.0000 | 0.0800 |
| Ridge | FWD | 1.2674 | 2.2236 | 0.6686 | 0.0000 | 0.0000 | 0.0400 |
| minutes_adjusted_rolling_mean | GK | 0.6723 | 1.6569 | 0.7683 | 0.0000 | 0.0000 | 0.0000 |
| rolling_5_gameweek_mean | GK | 0.6941 | 1.6516 | 0.7630 | 0.0000 | 0.0000 | 0.0000 |
| rolling_3_gameweek_mean | GK | 0.6984 | 1.7025 | 0.7747 | 0.0000 | 0.0000 | 0.0400 |
| residual_CatBoost | GK | 0.7203 | 1.5331 | 0.6269 | 0.0000 | 0.0000 | 0.0200 |
| residual_XGBoost | GK | 0.7327 | 1.5369 | 0.6287 | 0.0000 | 0.0000 | 0.0200 |
| global_plus_position_interactions | GK | 0.7355 | 1.5532 | 0.6139 | 0.0000 | 0.0000 | 0.0400 |
| residual_LightGBM | GK | 0.7412 | 1.5540 | 0.6262 | 0.0000 | 0.0000 | 0.0600 |
| position_wise_models | GK | 0.7430 | 1.5583 | 0.6005 | 0.0000 | 0.0000 | 0.0200 |
| CatBoost | GK | 0.7453 | 1.5558 | 0.6240 | 0.0000 | 0.0000 | 0.0000 |
| XGBoost | GK | 0.7498 | 1.5542 | 0.6251 | 0.0000 | 0.0000 | 0.0200 |
| residual_Ridge | GK | 0.7521 | 1.5304 | 0.6251 | 0.0000 | 0.0000 | 0.0000 |
| LightGBM | GK | 0.7531 | 1.5663 | 0.6198 | 0.0000 | 0.0000 | 0.0000 |
| residual_ElasticNet | GK | 0.7689 | 1.5324 | 0.6251 | 0.0000 | 0.0000 | 0.0000 |
| Ridge | GK | 0.7788 | 1.5549 | 0.6169 | 0.0000 | 0.0000 | 0.0000 |
| ElasticNet | GK | 0.7953 | 1.5562 | 0.6166 | 0.0000 | 0.0000 | 0.0000 |
| minutes_adjusted_rolling_mean | MID | 1.0159 | 2.1760 | 0.7016 | 0.1000 | 0.0500 | 0.0800 |
| residual_CatBoost | MID | 1.0335 | 2.0259 | 0.6873 | 0.1000 | 0.1000 | 0.0400 |
| residual_XGBoost | MID | 1.0378 | 2.0284 | 0.6858 | 0.2000 | 0.1000 | 0.0400 |
| residual_LightGBM | MID | 1.0474 | 2.0504 | 0.6829 | 0.0000 | 0.0000 | 0.0000 |
| CatBoost | MID | 1.0507 | 2.0396 | 0.6801 | 0.1000 | 0.0500 | 0.0200 |
| XGBoost | MID | 1.0525 | 2.0416 | 0.6799 | 0.1000 | 0.1000 | 0.0400 |
| LightGBM | MID | 1.0610 | 2.0610 | 0.6763 | 0.0000 | 0.0000 | 0.0000 |
| rolling_5_gameweek_mean | MID | 1.0788 | 2.1508 | 0.6936 | 0.1000 | 0.0500 | 0.0800 |
| global_plus_position_interactions | MID | 1.0813 | 2.0441 | 0.6689 | 0.1000 | 0.0500 | 0.0600 |
| position_wise_models | MID | 1.0871 | 2.0482 | 0.6691 | 0.1000 | 0.0500 | 0.0600 |
| residual_Ridge | MID | 1.0873 | 2.0328 | 0.6748 | 0.1000 | 0.1000 | 0.0800 |
| residual_ElasticNet | MID | 1.0958 | 2.0348 | 0.6732 | 0.1000 | 0.1000 | 0.0800 |
| rolling_3_gameweek_mean | MID | 1.0994 | 2.2246 | 0.6934 | 0.2000 | 0.1000 | 0.0800 |
| Ridge | MID | 1.1089 | 2.0513 | 0.6625 | 0.1000 | 0.1000 | 0.0800 |
| ElasticNet | MID | 1.1109 | 2.0517 | 0.6621 | 0.1000 | 0.1000 | 0.0800 |

## Classification Rules

- `keep_core`: competitive overall and best or ranking-competitive somewhere.
- `keep_specialist`: not core, but near-best in at least one early, position, season, or ranking context.
- `remove_candidate`: not competitive overall, early-season, by position, by season, or on ranking metrics.
- `investigate`: incomplete or invalid metric coverage.

Near-best thresholds: within 1% of best MAE/RMSE, within 0.01 Spearman, or within 0.01 precision for top-k metrics.
