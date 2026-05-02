# Team-Strength Feature Report

## Features Added

The processed modelling dataset now includes these leakage-safe dynamic team-strength features:

| feature | description |
| --- | --- |
| `team_elo_pre_gw` | Team Elo before the current gameweek result is applied |
| `opponent_elo_pre_gw` | Opponent Elo before the current gameweek result is applied |
| `elo_difference` | `team_elo_pre_gw - opponent_elo_pre_gw` |
| `home_adjusted_elo_difference` | Elo difference plus temporary home advantage for home teams, minus it for away teams |

These features are included in the trained-model stable feature list. Raw `team` and `opponent_team` are still not model features.

## Features Skipped

The rolling team goal-form features were skipped for the modelling dataset:

- `team_goals_scored_mean_last_5`
- `team_goals_conceded_mean_last_5`
- `opponent_goals_scored_mean_last_5`
- `opponent_goals_conceded_mean_last_5`
- `team_clean_sheet_rate_last_5`
- `opponent_clean_sheet_rate_last_5`

Reason: in the Vaastav processed rows, `team` is a team name while `opponent_team` is a numeric code. Because those identifiers are not in the same namespace, opponent rolling form cannot be joined back reliably yet. The lower-level framework can still derive team-gameweek goals when score/home columns exist, but those rolling goal-form features are intentionally not integrated into the modelling dataset until opponent identity mapping is made reliable.

## Elo Initialization

Elo uses:

- `base_elo = 1500`
- `k_factor = 20`
- `home_advantage = 50`

Manual priors are supported through `data/manual/team_season_priors.csv` when present. No manual prior file was required for this run, so teams initialize from safe defaults:

- returning or unknown teams: `1500`
- promoted teams, if explicitly identifiable in priors: rank 1 = `1470`, rank 2 = `1455`, rank 3 = `1440`, unknown rank = `1450`

Previous-season final Elo and previous-season table-position priors are supported but only used when the optional manual prior data is available.

## Focused Model Comparison

Comparison is against the immediately prior cleaned run before team-strength features.

| model | metric | before | after | delta | improved |
| --- | --- | ---: | ---: | ---: | --- |
| `global_plus_position_interactions` | MAE | 1.1254 | 1.1244 | -0.0010 | yes |
| `global_plus_position_interactions` | RMSE | 2.0582 | 2.0582 | 0.0000 | no |
| `global_plus_position_interactions` | Spearman | 0.6396 | 0.6369 | -0.0027 | no |
| `global_plus_position_interactions` | top-10 precision | 0.0200 | 0.0200 | 0.0000 | no |
| `global_plus_position_interactions` | top-20 precision | 0.0200 | 0.0200 | 0.0000 | no |
| `global_plus_position_interactions` | top-50 precision | 0.0440 | 0.0360 | -0.0080 | no |
| `residual_CatBoost` | MAE | 1.1820 | 1.1822 | 0.0002 | no |
| `residual_CatBoost` | RMSE | 2.1285 | 2.1284 | -0.0001 | yes |
| `residual_CatBoost` | Spearman | 0.6482 | 0.6395 | -0.0087 | no |
| `residual_CatBoost` | top-10 precision | 0.0000 | 0.0000 | 0.0000 | no |
| `residual_CatBoost` | top-20 precision | 0.0222 | 0.0222 | 0.0000 | no |
| `residual_CatBoost` | top-50 precision | 0.0333 | 0.0378 | 0.0045 | yes |
| `residual_LightGBM` | MAE | 1.1873 | 1.1878 | 0.0005 | no |
| `residual_LightGBM` | RMSE | 2.1440 | 2.1440 | 0.0000 | no |
| `residual_LightGBM` | Spearman | 0.6466 | 0.6334 | -0.0132 | no |
| `residual_LightGBM` | top-10 precision | 0.0111 | 0.0111 | 0.0000 | no |
| `residual_LightGBM` | top-20 precision | 0.0278 | 0.0222 | -0.0056 | no |
| `residual_LightGBM` | top-50 precision | 0.0289 | 0.0356 | 0.0067 | yes |
| `residual_XGBoost` | MAE | 1.1836 | 1.1837 | 0.0001 | no |
| `residual_XGBoost` | RMSE | 2.1295 | 2.1304 | 0.0009 | no |
| `residual_XGBoost` | Spearman | 0.6470 | 0.6378 | -0.0092 | no |
| `residual_XGBoost` | top-10 precision | 0.0000 | 0.0333 | 0.0333 | yes |
| `residual_XGBoost` | top-20 precision | 0.0222 | 0.0333 | 0.0111 | yes |
| `residual_XGBoost` | top-50 precision | 0.0378 | 0.0444 | 0.0066 | yes |

## Best Model After Adding Team-Strength Features

| metric | best model | score |
| --- | --- | ---: |
| MAE | `minutes_adjusted_rolling_mean` | 1.1355 |
| RMSE | `residual_CatBoost` | 2.1284 |
| Spearman | `minutes_adjusted_rolling_mean` | 0.6422 |
| top-10 precision | `residual_XGBoost` | 0.0333 |
| top-20 precision | `residual_XGBoost` | 0.0333 |
| top-50 precision | `rolling_5_gameweek_mean` | 0.0467 |

## Data-Quality Issues

- Elo features are missing for 36.7% of rows because early seasons lack reliable team/opponent data in the processed source.
- Unknown position label `AM` remains excluded from position-aware outputs.
- `RandomForestRegressor` and `HistGradientBoostingRegressor` still skip during the full backtest on this Windows environment with `[WinError 5] Ingen tilgang`.
- Team-strength features did not materially improve the main MAE target. The largest useful movement is in ranking precision for `residual_XGBoost`.
