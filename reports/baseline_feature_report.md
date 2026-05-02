# Baseline Feature Report

This report compares the backtest immediately before and after adding leakage-safe baseline prediction features to the trained model feature set.

Added features:

- `pred_previous_gameweek_points`
- `pred_rolling_3_gameweek_mean`
- `pred_rolling_5_gameweek_mean`
- `pred_minutes_adjusted_rolling_mean`

Each feature is computed through the existing baseline prediction logic from row-level pre-gameweek features. The strongest baseline, `minutes_adjusted_rolling_mean`, remains evaluated as a standalone baseline.

## Overall Impact

Lower MAE/RMSE is better. Higher Spearman is better.

| model | before_mae | after_mae | mae_delta | before_rmse | after_rmse | rmse_delta | before_spearman | after_spearman | spearman_delta |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Ridge | 1.2388 | 1.2222 | -0.0166 | 2.1537 | 2.1477 | -0.0060 | 0.6468 | 0.6458 | -0.0010 |
| ElasticNet | 1.2403 | 1.2276 | -0.0127 | 2.1539 | 2.1483 | -0.0056 | 0.6467 | 0.6462 | -0.0005 |
| CatBoost | 1.1958 | 1.1963 | 0.0005 | 2.1419 | 2.1422 | 0.0003 | 0.6515 | 0.6516 | 0.0001 |
| XGBoost | 1.1978 | 1.1981 | 0.0003 | 2.1410 | 2.1427 | 0.0017 | 0.6517 | 0.6514 | -0.0003 |
| LightGBM | 1.2014 | 1.2017 | 0.0003 | 2.1554 | 2.1564 | 0.0010 | 0.6477 | 0.6467 | -0.0010 |
| residual_Ridge | 1.3057 | 1.2058 | -0.0999 | 2.2156 | 2.1335 | -0.0821 | 0.5434 | 0.6558 | 0.1124 |
| residual_ElasticNet | 1.3051 | 1.2158 | -0.0893 | 2.2151 | 2.1356 | -0.0795 | 0.5489 | 0.6564 | 0.1075 |
| residual_CatBoost | 1.1837 | 1.1834 | -0.0003 | 2.1298 | 2.1296 | -0.0002 | 0.6611 | 0.6612 | 0.0001 |
| residual_XGBoost | 1.1853 | 1.1847 | -0.0006 | 2.1322 | 2.1311 | -0.0011 | 0.6602 | 0.6607 | 0.0005 |
| residual_LightGBM | 1.1890 | 1.1891 | 0.0001 | 2.1436 | 2.1437 | 0.0001 | 0.6565 | 0.6564 | -0.0001 |

## Best Overall Models After Adding Features

| metric | best_model_after | score |
| --- | --- | ---: |
| MAE | `minutes_adjusted_rolling_mean` | 1.1355 |
| RMSE | `residual_CatBoost` | 2.1296 |
| Spearman | `residual_CatBoost` | 0.6612 |

The baseline features improved the linear residual models substantially and slightly improved the best residual boosted models. They did not make any trained model beat `minutes_adjusted_rolling_mean` on average MAE.

## Best Model By Season After Adding Features

### MAE

| validation_season | best_model | mae |
| --- | --- | ---: |
| 2017-18 | `minutes_adjusted_rolling_mean` | 1.2501 |
| 2018-19 | `minutes_adjusted_rolling_mean` | 1.2896 |
| 2019-20 | `minutes_adjusted_rolling_mean` | 1.2290 |
| 2020-21 | `minutes_adjusted_rolling_mean` | 1.1647 |
| 2021-22 | `minutes_adjusted_rolling_mean` | 1.1390 |
| 2022-23 | `minutes_adjusted_rolling_mean` | 1.0663 |
| 2023-24 | `minutes_adjusted_rolling_mean` | 0.9648 |
| 2024-25 | `minutes_adjusted_rolling_mean` | 1.0682 |
| 2025-26 | `minutes_adjusted_rolling_mean` | 1.0478 |

### RMSE

| validation_season | best_model | rmse |
| --- | --- | ---: |
| 2017-18 | `residual_Ridge` | 2.2310 |
| 2018-19 | `residual_CatBoost` | 2.2756 |
| 2019-20 | `residual_CatBoost` | 2.2108 |
| 2020-21 | `residual_CatBoost` | 2.1424 |
| 2021-22 | `residual_CatBoost` | 2.1501 |
| 2022-23 | `residual_XGBoost` | 2.0334 |
| 2023-24 | `residual_CatBoost` | 1.9935 |
| 2024-25 | `residual_Ridge` | 2.0734 |
| 2025-26 | `residual_CatBoost` | 2.0223 |

### Spearman

| validation_season | best_model | spearman |
| --- | --- | ---: |
| 2017-18 | `residual_XGBoost` | 0.6400 |
| 2018-19 | `residual_XGBoost` | 0.6266 |
| 2019-20 | `residual_CatBoost` | 0.6418 |
| 2020-21 | `residual_CatBoost` | 0.6514 |
| 2021-22 | `residual_CatBoost` | 0.6439 |
| 2022-23 | `residual_CatBoost` | 0.6845 |
| 2023-24 | `residual_CatBoost` | 0.6770 |
| 2024-25 | `residual_CatBoost` | 0.6791 |
| 2025-26 | `residual_CatBoost` | 0.7070 |

## Interpretation

Baseline features help the models that previously lacked direct access to the strong simple predictors, especially residual Ridge and residual ElasticNet. The boosted residual models were already close to the useful signal and only moved slightly.

The main project constraint is still not satisfied for MAE: no trained ML model beats `minutes_adjusted_rolling_mean` by average MAE or by season-level MAE. The next step should focus on MAE calibration, likely by constraining residual corrections, clipping harmful residual adjustments, or optimizing a validation-selected blend between the baseline and the residual model.
