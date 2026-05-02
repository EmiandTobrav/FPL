# Model Comparison

Rolling-origin validation by season. Lower MAE/RMSE is better; higher Spearman is better.

## Overall Ranking

| model | seasons | mean_mae | mean_rmse | mean_spearman |
| --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 9 | 1.1355 | 2.2977 | 0.6422 |
| CatBoost | 9 | 1.1958 | 2.1419 | 0.6515 |
| XGBoost | 9 | 1.1978 | 2.1410 | 0.6517 |
| HistGradientBoostingRegressor | 9 | 1.2010 | 2.1462 | 0.6497 |
| LightGBM | 9 | 1.2014 | 2.1554 | 0.6477 |
| rolling_5_gameweek_mean | 9 | 1.2033 | 2.2750 | 0.6380 |
| rolling_3_gameweek_mean | 9 | 1.2262 | 2.3591 | 0.6343 |
| RandomForestRegressor | 9 | 1.2323 | 2.1848 | 0.6306 |
| Ridge | 9 | 1.2388 | 2.1537 | 0.6468 |
| ElasticNet | 9 | 1.2403 | 2.1539 | 0.6467 |
| two_stage_minutes_points | 9 | 1.2527 | 2.1596 | 0.6464 |
| previous_gameweek_points | 9 | 1.3362 | 2.7925 | 0.5932 |
| position_average | 6 | 1.5624 | 2.3849 | 0.1053 |

## Two-Stage Versus Best Direct Model

Best direct points model by mean MAE: minutes_adjusted_rolling_mean (1.1355).
Two-stage mean MAE: 1.2527.
MAE delta versus best direct model: 0.1172.

## Results By Validation Season

| validation_season | model | n_train | n_validation | mae | rmse | spearman |
| --- | --- | --- | --- | --- | --- | --- |
| 2017-18 | minutes_adjusted_rolling_mean | 23679 | 21175 | 1.2501 | 2.4062 | 0.6251 |
| 2017-18 | CatBoost | 22996 | 21820 | 1.2973 | 2.2378 | 0.6321 |
| 2017-18 | XGBoost | 22996 | 21820 | 1.3015 | 2.2415 | 0.6314 |
| 2017-18 | HistGradientBoostingRegressor | 22996 | 21820 | 1.3024 | 2.2476 | 0.6271 |
| 2017-18 | LightGBM | 22996 | 21820 | 1.3131 | 2.2729 | 0.6195 |
| 2017-18 | rolling_5_gameweek_mean | 23679 | 21175 | 1.3247 | 2.3900 | 0.6157 |
| 2017-18 | RandomForestRegressor | 22996 | 21820 | 1.3308 | 2.2801 | 0.6079 |
| 2017-18 | Ridge | 22996 | 21820 | 1.3330 | 2.2474 | 0.6300 |
| 2017-18 | ElasticNet | 22996 | 21820 | 1.3338 | 2.2475 | 0.6297 |
| 2017-18 | two_stage_minutes_points | 22996 | 21820 | 1.3444 | 2.2540 | 0.6292 |
| 2017-18 | rolling_3_gameweek_mean | 23679 | 21175 | 1.3513 | 2.4818 | 0.6130 |
| 2017-18 | previous_gameweek_points | 23679 | 21175 | 1.4729 | 2.9323 | 0.5681 |
| 2018-19 | minutes_adjusted_rolling_mean | 46146 | 20550 | 1.2896 | 2.4511 | 0.6120 |
| 2018-19 | CatBoost | 44816 | 21166 | 1.3415 | 2.2859 | 0.6176 |
| 2018-19 | XGBoost | 44816 | 21166 | 1.3420 | 2.2866 | 0.6175 |
| 2018-19 | HistGradientBoostingRegressor | 44816 | 21166 | 1.3485 | 2.2950 | 0.6135 |
| 2018-19 | LightGBM | 44816 | 21166 | 1.3511 | 2.3068 | 0.6107 |
| 2018-19 | rolling_5_gameweek_mean | 46146 | 20550 | 1.3612 | 2.4289 | 0.6035 |
| 2018-19 | Ridge | 44816 | 21166 | 1.3682 | 2.2959 | 0.6156 |
| 2018-19 | ElasticNet | 44816 | 21166 | 1.3687 | 2.2957 | 0.6155 |
| 2018-19 | two_stage_minutes_points | 44816 | 21166 | 1.3791 | 2.3015 | 0.6155 |
| 2018-19 | RandomForestRegressor | 44816 | 21166 | 1.3814 | 2.3340 | 0.5920 |
| 2018-19 | rolling_3_gameweek_mean | 46146 | 20550 | 1.3915 | 2.5211 | 0.5929 |
| 2018-19 | previous_gameweek_points | 46146 | 20550 | 1.5267 | 3.0017 | 0.5509 |
| 2019-20 | minutes_adjusted_rolling_mean | 67936 | 21229 | 1.2290 | 2.3818 | 0.6252 |
| 2019-20 | CatBoost | 65982 | 21894 | 1.2865 | 2.2112 | 0.6331 |
| 2019-20 | XGBoost | 65982 | 21894 | 1.2874 | 2.2113 | 0.6331 |
| 2019-20 | LightGBM | 65982 | 21894 | 1.2893 | 2.2236 | 0.6307 |
| 2019-20 | HistGradientBoostingRegressor | 65982 | 21894 | 1.2917 | 2.2138 | 0.6319 |
| 2019-20 | rolling_5_gameweek_mean | 67936 | 21229 | 1.3034 | 2.3625 | 0.6172 |
| 2019-20 | RandomForestRegressor | 65982 | 21894 | 1.3166 | 2.2527 | 0.6100 |
| 2019-20 | Ridge | 65982 | 21894 | 1.3201 | 2.2218 | 0.6289 |
| 2019-20 | ElasticNet | 65982 | 21894 | 1.3210 | 2.2218 | 0.6289 |
| 2019-20 | rolling_3_gameweek_mean | 67936 | 21229 | 1.3329 | 2.4616 | 0.6115 |
| 2019-20 | two_stage_minutes_points | 65982 | 21894 | 1.3330 | 2.2279 | 0.6283 |
| 2019-20 | previous_gameweek_points | 67936 | 21229 | 1.4480 | 2.8895 | 0.5721 |
| 2020-21 | minutes_adjusted_rolling_mean | 90496 | 22946 | 1.1647 | 2.3183 | 0.6339 |
| 2020-21 | CatBoost | 87876 | 23652 | 1.2311 | 2.1688 | 0.6415 |
| 2020-21 | rolling_5_gameweek_mean | 90496 | 22946 | 1.2322 | 2.2994 | 0.6286 |
| 2020-21 | XGBoost | 87876 | 23652 | 1.2324 | 2.1698 | 0.6416 |
| 2020-21 | HistGradientBoostingRegressor | 87876 | 23652 | 1.2329 | 2.1700 | 0.6403 |
| 2020-21 | LightGBM | 87876 | 23652 | 1.2358 | 2.1797 | 0.6388 |
| 2020-21 | rolling_3_gameweek_mean | 90496 | 22946 | 1.2510 | 2.3767 | 0.6278 |
| 2020-21 | RandomForestRegressor | 87876 | 23652 | 1.2633 | 2.2093 | 0.6198 |
| 2020-21 | Ridge | 87876 | 23652 | 1.2767 | 2.1868 | 0.6360 |
| 2020-21 | ElasticNet | 87876 | 23652 | 1.2777 | 2.1867 | 0.6360 |
| 2020-21 | two_stage_minutes_points | 87876 | 23652 | 1.2901 | 2.1917 | 0.6364 |
| 2020-21 | previous_gameweek_points | 90496 | 22946 | 1.3754 | 2.8278 | 0.5787 |
| 2020-21 | position_average | 90496 | 23648 | 1.6646 | 2.4694 | 0.1169 |
| 2021-22 | minutes_adjusted_rolling_mean | 114861 | 23974 | 1.1390 | 2.3257 | 0.6275 |
| 2021-22 | CatBoost | 111528 | 24710 | 1.2119 | 2.1608 | 0.6344 |
| 2021-22 | rolling_5_gameweek_mean | 114861 | 23974 | 1.2127 | 2.3106 | 0.6201 |
| 2021-22 | XGBoost | 111528 | 24710 | 1.2130 | 2.1615 | 0.6342 |
| 2021-22 | LightGBM | 111528 | 24710 | 1.2160 | 2.1704 | 0.6325 |
| 2021-22 | HistGradientBoostingRegressor | 111528 | 24710 | 1.2187 | 2.1650 | 0.6333 |
| 2021-22 | RandomForestRegressor | 111528 | 24710 | 1.2409 | 2.2004 | 0.6174 |
| 2021-22 | rolling_3_gameweek_mean | 114861 | 23974 | 1.2435 | 2.4114 | 0.6168 |
| 2021-22 | Ridge | 111528 | 24710 | 1.2588 | 2.1789 | 0.6288 |
| 2021-22 | ElasticNet | 111528 | 24710 | 1.2603 | 2.1793 | 0.6286 |
| 2021-22 | two_stage_minutes_points | 111528 | 24710 | 1.2716 | 2.1848 | 0.6289 |
| 2021-22 | previous_gameweek_points | 114861 | 23974 | 1.3599 | 2.8622 | 0.5693 |
| 2021-22 | position_average | 114861 | 24705 | 1.6340 | 2.4487 | 0.1077 |
| 2022-23 | minutes_adjusted_rolling_mean | 140308 | 24952 | 1.0663 | 2.1894 | 0.6659 |
| 2022-23 | rolling_5_gameweek_mean | 140308 | 24952 | 1.1362 | 2.1795 | 0.6578 |
| 2022-23 | CatBoost | 136238 | 25727 | 1.1364 | 2.0479 | 0.6740 |
| 2022-23 | XGBoost | 136238 | 25727 | 1.1372 | 2.0482 | 0.6741 |
| 2022-23 | LightGBM | 136238 | 25727 | 1.1392 | 2.0562 | 0.6734 |
| 2022-23 | HistGradientBoostingRegressor | 136238 | 25727 | 1.1397 | 2.0499 | 0.6736 |
| 2022-23 | rolling_3_gameweek_mean | 140308 | 24952 | 1.1567 | 2.2569 | 0.6517 |
| 2022-23 | RandomForestRegressor | 136238 | 25727 | 1.1665 | 2.0843 | 0.6540 |
| 2022-23 | Ridge | 136238 | 25727 | 1.1807 | 2.0625 | 0.6675 |
| 2022-23 | ElasticNet | 136238 | 25727 | 1.1818 | 2.0625 | 0.6673 |
| 2022-23 | two_stage_minutes_points | 136238 | 25727 | 1.1952 | 2.0679 | 0.6678 |
| 2022-23 | previous_gameweek_points | 140308 | 24952 | 1.2589 | 2.6951 | 0.6168 |
| 2022-23 | position_average | 140308 | 25723 | 1.5608 | 2.3562 | 0.1194 |
| 2023-24 | minutes_adjusted_rolling_mean | 166813 | 27999 | 0.9648 | 2.1318 | 0.6578 |
| 2023-24 | rolling_5_gameweek_mean | 166813 | 27999 | 1.0303 | 2.1198 | 0.6542 |
| 2023-24 | CatBoost | 161965 | 28860 | 1.0465 | 1.9993 | 0.6657 |
| 2023-24 | LightGBM | 161965 | 28860 | 1.0495 | 2.0036 | 0.6644 |
| 2023-24 | rolling_3_gameweek_mean | 166813 | 27999 | 1.0503 | 2.1963 | 0.6500 |
| 2023-24 | XGBoost | 161965 | 28860 | 1.0534 | 1.9997 | 0.6652 |
| 2023-24 | HistGradientBoostingRegressor | 161965 | 28860 | 1.0552 | 1.9991 | 0.6653 |
| 2023-24 | RandomForestRegressor | 161965 | 28860 | 1.0942 | 2.0344 | 0.6510 |
| 2023-24 | Ridge | 161965 | 28860 | 1.1016 | 2.0137 | 0.6585 |
| 2023-24 | ElasticNet | 161965 | 28860 | 1.1053 | 2.0141 | 0.6582 |
| 2023-24 | two_stage_minutes_points | 161965 | 28860 | 1.1180 | 2.0187 | 0.6584 |
| 2023-24 | previous_gameweek_points | 166813 | 27999 | 1.1418 | 2.5994 | 0.6090 |
| 2023-24 | position_average | 166813 | 28856 | 1.4305 | 2.2965 | 0.1046 |
| 2024-25 | minutes_adjusted_rolling_mean | 196538 | 26000 | 1.0682 | 2.2661 | 0.6439 |
| 2024-25 | rolling_5_gameweek_mean | 196538 | 26000 | 1.1192 | 2.1888 | 0.6640 |
| 2024-25 | XGBoost | 190825 | 26801 | 1.1312 | 2.1114 | 0.6731 |
| 2024-25 | CatBoost | 190825 | 26801 | 1.1321 | 2.1266 | 0.6698 |
| 2024-25 | HistGradientBoostingRegressor | 190825 | 26801 | 1.1353 | 2.1317 | 0.6680 |
| 2024-25 | LightGBM | 190825 | 26801 | 1.1359 | 2.1399 | 0.6655 |
| 2024-25 | rolling_3_gameweek_mean | 196538 | 26000 | 1.1448 | 2.2742 | 0.6607 |
| 2024-25 | Ridge | 190825 | 26801 | 1.1686 | 2.1156 | 0.6682 |
| 2024-25 | ElasticNet | 190825 | 26801 | 1.1711 | 2.1170 | 0.6683 |
| 2024-25 | RandomForestRegressor | 190825 | 26801 | 1.1808 | 2.1844 | 0.6450 |
| 2024-25 | two_stage_minutes_points | 190825 | 26801 | 1.1856 | 2.1236 | 0.6675 |
| 2024-25 | previous_gameweek_points | 196538 | 26000 | 1.2371 | 2.6770 | 0.6163 |
| 2024-25 | position_average | 196538 | 26796 | 1.5138 | 2.3670 | 0.1212 |
| 2025-26 | minutes_adjusted_rolling_mean | 224143 | 20714 | 1.0478 | 2.2088 | 0.6886 |
| 2025-26 | CatBoost | 217626 | 21533 | 1.0788 | 2.0388 | 0.6948 |
| 2025-26 | XGBoost | 217626 | 21533 | 1.0817 | 2.0391 | 0.6947 |
| 2025-26 | LightGBM | 217626 | 21533 | 1.0828 | 2.0459 | 0.6937 |
| 2025-26 | HistGradientBoostingRegressor | 217626 | 21533 | 1.0842 | 2.0434 | 0.6943 |
| 2025-26 | rolling_5_gameweek_mean | 224143 | 20714 | 1.1098 | 2.1956 | 0.6812 |
| 2025-26 | rolling_3_gameweek_mean | 224143 | 20714 | 1.1143 | 2.2519 | 0.6845 |
| 2025-26 | RandomForestRegressor | 217626 | 21533 | 1.1159 | 2.0832 | 0.6785 |
| 2025-26 | Ridge | 217626 | 21533 | 1.1417 | 2.0609 | 0.6872 |
| 2025-26 | ElasticNet | 217626 | 21533 | 1.1430 | 2.0604 | 0.6873 |
| 2025-26 | two_stage_minutes_points | 217626 | 21533 | 1.1573 | 2.0666 | 0.6861 |
| 2025-26 | previous_gameweek_points | 224143 | 20714 | 1.2049 | 2.6474 | 0.6578 |
| 2025-26 | position_average | 224143 | 21529 | 1.5706 | 2.3715 | 0.0620 |
