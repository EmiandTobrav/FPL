# Current Model Findings

Source files:

- `reports/model_results.csv`
- `reports/model_comparison.md`

## 1. Models That Ran Successfully

The current result files contain successful rows for these models:

- Baselines:
  - `previous_gameweek_points`
  - `rolling_3_gameweek_mean`
  - `rolling_5_gameweek_mean`
  - `minutes_adjusted_rolling_mean`
  - `position_average` for 6 validation seasons
- Trained direct ML models:
  - `Ridge`
  - `ElasticNet`
  - `RandomForestRegressor`
  - `HistGradientBoostingRegressor`
  - `XGBoost`
  - `LightGBM`
  - `CatBoost`
- Trained two-stage model:
  - `two_stage_minutes_points`

## 2. Models Skipped

The result files do not include explicit skip diagnostics. Based on the rows present:

- `position_average` only appears for 6 seasons, while the other baseline and model families appear for 9 seasons.
- `position_average` is missing for the first three validation seasons: `2017-18`, `2018-19`, and `2019-20`.
- No trained ML model is missing from the result table; each trained ML model has results for all 9 validation seasons.

The likely reason for the missing `position_average` rows is insufficient usable historical position data in the earliest validation windows.

## 3. Best Model By Average MAE

Best average MAE:

| model | seasons | mean_mae |
| --- | ---: | ---: |
| `minutes_adjusted_rolling_mean` | 9 | 1.1355 |

Best trained ML model by average MAE:

| model | seasons | mean_mae |
| --- | ---: | ---: |
| `CatBoost` | 9 | 1.1958 |

The strongest MAE model is still a baseline, not a trained ML model.

## 4. Best Model By Average RMSE

Best average RMSE:

| model | seasons | mean_rmse |
| --- | ---: | ---: |
| `XGBoost` | 9 | 2.1410 |

The best baseline by average RMSE is `rolling_5_gameweek_mean` at 2.2750, so trained ML improves RMSE.

## 5. Best Model By Average Spearman

Best average Spearman correlation:

| model | seasons | mean_spearman |
| --- | ---: | ---: |
| `XGBoost` | 9 | 0.6517 |

The best baseline by average Spearman is `minutes_adjusted_rolling_mean` at 0.6422, so trained ML improves ranking quality.

## 6. Best Model By Season

By MAE, `minutes_adjusted_rolling_mean` is best in every validation season:

| validation_season | best_mae_model | mae |
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

By RMSE, trained ML models are best in every validation season:

| validation_season | best_rmse_model | rmse |
| --- | --- | ---: |
| 2017-18 | `CatBoost` | 2.2378 |
| 2018-19 | `CatBoost` | 2.2859 |
| 2019-20 | `CatBoost` | 2.2112 |
| 2020-21 | `CatBoost` | 2.1688 |
| 2021-22 | `CatBoost` | 2.1608 |
| 2022-23 | `CatBoost` | 2.0479 |
| 2023-24 | `HistGradientBoostingRegressor` | 1.9991 |
| 2024-25 | `XGBoost` | 2.1114 |
| 2025-26 | `CatBoost` | 2.0388 |

By Spearman, trained ML models are best in every validation season:

| validation_season | best_spearman_model | spearman |
| --- | --- | ---: |
| 2017-18 | `CatBoost` | 0.6321 |
| 2018-19 | `CatBoost` | 0.6176 |
| 2019-20 | `CatBoost` | 0.6331 |
| 2020-21 | `XGBoost` | 0.6416 |
| 2021-22 | `CatBoost` | 0.6344 |
| 2022-23 | `XGBoost` | 0.6741 |
| 2023-24 | `CatBoost` | 0.6657 |
| 2024-25 | `XGBoost` | 0.6731 |
| 2025-26 | `CatBoost` | 0.6948 |

## 7. Do Trained ML Models Beat The Strongest Baseline?

Yes, but only on some metrics.

Average metric comparison:

| metric | strongest_baseline | baseline_score | best_trained_ml | ml_score | ml_beats_baseline |
| --- | --- | ---: | --- | ---: | --- |
| MAE | `minutes_adjusted_rolling_mean` | 1.1355 | `CatBoost` | 1.1958 | no |
| RMSE | `rolling_5_gameweek_mean` | 2.2750 | `XGBoost` | 2.1410 | yes |
| Spearman | `minutes_adjusted_rolling_mean` | 0.6422 | `XGBoost` | 0.6517 | yes |

Season-level pattern:

- No trained ML model beats `minutes_adjusted_rolling_mean` on MAE in any validation season.
- A trained ML model beats the strongest baseline on RMSE in every validation season.
- A trained ML model beats the strongest baseline on Spearman in every validation season.

The current ML models are better at reducing large errors and ranking players, but worse at average absolute error.

## 8. Does The Two-Stage Model Help?

The two-stage model hurts MAE relative to the strongest direct model.

Overall:

- Best direct model by mean MAE: `minutes_adjusted_rolling_mean` at 1.1355.
- Two-stage mean MAE: 1.2527.
- MAE delta: +0.1172.

By validation season, the two-stage model is worse than the best direct model every time:

| validation_season | two_stage_mae | best_direct_mae | delta |
| --- | ---: | ---: | ---: |
| 2017-18 | 1.3444 | 1.2501 | 0.0943 |
| 2018-19 | 1.3791 | 1.2896 | 0.0895 |
| 2019-20 | 1.3330 | 1.2290 | 0.1040 |
| 2020-21 | 1.2901 | 1.1647 | 0.1254 |
| 2021-22 | 1.2716 | 1.1390 | 0.1326 |
| 2022-23 | 1.1952 | 1.0663 | 0.1290 |
| 2023-24 | 1.1180 | 0.9648 | 0.1532 |
| 2024-25 | 1.1856 | 1.0682 | 0.1174 |
| 2025-26 | 1.1573 | 1.0478 | 0.1095 |

The current two-stage setup does not justify replacing direct point prediction.

## 9. Do Results Differ By Validation Season?

Yes. Absolute error generally improves in later seasons:

- The best MAE falls from 1.2501 in `2017-18` to 0.9648 in `2023-24`, then remains near 1.05 in `2024-25` and `2025-26`.
- Spearman is also stronger in recent seasons, reaching 0.6948 in `2025-26`.
- The ML-versus-baseline shape is stable across seasons: ML wins RMSE and Spearman, while the minutes-adjusted rolling baseline wins MAE.

This suggests the train/validation setup is stable, but the objective being optimized by ML models is not aligned with the MAE baseline target.

## 10. Implications For The Next Modelling Step

The next modelling step should focus on beating `minutes_adjusted_rolling_mean` on MAE without giving up the ML gains in RMSE and Spearman.

Recommended next steps:

- Treat `minutes_adjusted_rolling_mean` as the primary baseline gate for MAE.
- Add residual modeling: train ML to predict the residual over the minutes-adjusted rolling baseline instead of raw points.
- Add the baseline predictions themselves as explicit model features, especially `minutes_adjusted_rolling_mean`, `rolling_5_gameweek_mean`, and `rolling_3_gameweek_mean`.
- Optimize and select models by rolling-origin MAE first, then use RMSE and Spearman as secondary metrics.
- Investigate why tree/boosting models improve RMSE and ranking but miss MAE; this may indicate overprediction of high-upside players or poor calibration around common low-score outcomes.
- Keep the two-stage model as an experiment only unless its minutes component can be improved; it currently hurts the main metric in every season.
