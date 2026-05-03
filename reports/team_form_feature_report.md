# Team Form Feature Report

Supported-season comparison uses min-season `2022-23`.

## Features Added

- `team_goals_scored_mean_last_5`
- `team_goals_conceded_mean_last_5`
- `opponent_goals_scored_mean_last_5`
- `opponent_goals_conceded_mean_last_5`
- `team_clean_sheet_rate_last_5`
- `opponent_clean_sheet_rate_last_5`

## Feature Coverage

| feature | full_non_null_rate | supported_non_null_rate |
| --- | --- | --- |
| team_goals_scored_mean_last_5 | 0.9760 | 0.9760 |
| team_goals_conceded_mean_last_5 | 0.9760 | 0.9760 |
| opponent_goals_scored_mean_last_5 | 0.9760 | 0.9760 |
| opponent_goals_conceded_mean_last_5 | 0.9760 | 0.9760 |
| team_clean_sheet_rate_last_5 | 0.9760 | 0.9760 |
| opponent_clean_sheet_rate_last_5 | 0.9760 | 0.9760 |

## Model Comparison

Positive deltas mean the metric increased after adding team form; for MAE/RMSE that is worse, for Spearman and precision that is better.

| model | before_mae | after_mae | delta_mae | before_rmse | after_rmse | delta_rmse | before_spearman | after_spearman | delta_spearman | before_top_10_precision | after_top_10_precision | delta_top_10_precision | before_top_20_precision | after_top_20_precision | delta_top_20_precision | before_top_50_precision | after_top_50_precision | delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| residual_CatBoost | 1.0941 | 1.0487 | -0.0454 | 2.0364 | 2.0062 | -0.0303 | 0.6509 | 0.6549 | 0.0040 | 0.0000 | 0.0667 | 0.0667 | 0.0100 | 0.0333 | 0.0233 | 0.0240 | 0.0667 | 0.0427 |
| residual_XGBoost | 1.0946 | 1.0484 | -0.0462 | 2.0391 | 2.0076 | -0.0315 | 0.6483 | 0.6538 | 0.0055 | 0.0000 | 0.0667 | 0.0667 | 0.0200 | 0.0333 | 0.0133 | 0.0240 | 0.0400 | 0.0160 |
| minutes_adjusted_rolling_mean | 1.0469 | 1.0098 | -0.0371 | 2.1975 | 2.1574 | -0.0401 | 0.6616 | 0.6715 | 0.0099 | 0.0200 | 0.0333 | 0.0133 | 0.0400 | 0.0667 | 0.0267 | 0.0440 | 0.0533 | 0.0093 |

## Global Plus Position Interactions

| strategy | before_mae | after_mae | delta_mae | before_rmse | after_rmse | delta_rmse | before_spearman | after_spearman | delta_spearman | before_top_10_precision | after_top_10_precision | delta_top_10_precision | before_top_20_precision | after_top_20_precision | delta_top_20_precision | before_top_50_precision | after_top_50_precision | delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_plus_position_interactions | 1.0819 | 1.0819 | 0.0000 | 2.0210 | 2.0210 | 0.0000 | 0.6357 | 0.6357 | 0.0000 | 0.0333 | 0.0333 | 0.0000 | 0.0333 | 0.0333 | 0.0000 | 0.0600 | 0.0600 | 0.0000 |

## Notes

- Rolling form is shifted by team-season gameweek, so GW t never uses GW t goals or clean-sheet outcomes.
- Opponent form is joined from the opponent's normalized team ID in the same season and gameweek.
- Unsupported seasons remain missing rather than being imputed from unreliable team identifiers.
