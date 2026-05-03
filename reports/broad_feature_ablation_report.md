# Broad Feature Ablation Report

Supported-season feature ablation using rolling-origin validation.

## Best Feature Group By Metric

| metric | best_feature_group | score |
| --- | --- | --- |
| mae | all_safe_candidates | 1.1055 |
| rmse | all_safe_candidates | 2.0761 |
| spearman | ownership_transfers_lagged | 0.6497 |
| top_10_precision | all_safe_candidates | 0.0200 |
| top_20_precision | all_safe_candidates | 0.0240 |
| top_50_precision | ownership_transfers_lagged | 0.0444 |

## Aggregate By Feature Group And Model

| feature_group | model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_safe_candidates | minutes_adjusted_rolling_mean | 1.0572 | 2.2244 | 0.6568 | 0.0200 | 0.0200 | 0.0440 |
| current_stable | minutes_adjusted_rolling_mean | 1.0572 | 2.2244 | 0.6568 | 0.0200 | 0.0200 | 0.0440 |
| elo_only | minutes_adjusted_rolling_mean | 1.0572 | 2.2244 | 0.6568 | 0.0200 | 0.0200 | 0.0440 |
| expected_stats_rolling | minutes_adjusted_rolling_mean | 1.0572 | 2.2244 | 0.6568 | 0.0200 | 0.0200 | 0.0440 |
| fixture_home | minutes_adjusted_rolling_mean | 1.0572 | 2.2244 | 0.6568 | 0.0200 | 0.0200 | 0.0440 |
| ict_rolling | minutes_adjusted_rolling_mean | 1.0572 | 2.2244 | 0.6568 | 0.0200 | 0.0200 | 0.0440 |
| no_team_strength | minutes_adjusted_rolling_mean | 1.0572 | 2.2244 | 0.6568 | 0.0200 | 0.0200 | 0.0440 |
| ownership_transfers_lagged | minutes_adjusted_rolling_mean | 1.0572 | 2.2244 | 0.6568 | 0.0200 | 0.0200 | 0.0440 |
| player_returns_rolling | minutes_adjusted_rolling_mean | 1.0572 | 2.2244 | 0.6568 | 0.0200 | 0.0200 | 0.0440 |
| team_form_only | minutes_adjusted_rolling_mean | 1.0572 | 2.2244 | 0.6568 | 0.0200 | 0.0200 | 0.0440 |
| all_safe_candidates | residual_CatBoost | 1.0937 | 2.0495 | 0.6580 | 0.0200 | 0.0200 | 0.0360 |
| ownership_transfers_lagged | residual_CatBoost | 1.0944 | 2.0501 | 0.6593 | 0.0000 | 0.0200 | 0.0360 |
| ownership_transfers_lagged | residual_XGBoost | 1.0956 | 2.0532 | 0.6572 | 0.0200 | 0.0300 | 0.0480 |
| all_safe_candidates | residual_XGBoost | 1.0957 | 2.0538 | 0.6563 | 0.0400 | 0.0300 | 0.0400 |
| elo_only | residual_CatBoost | 1.0999 | 2.0613 | 0.6487 | 0.0000 | 0.0200 | 0.0400 |
| no_team_strength | residual_CatBoost | 1.1002 | 2.0633 | 0.6533 | 0.0200 | 0.0200 | 0.0400 |
| ict_rolling | residual_CatBoost | 1.1003 | 2.0600 | 0.6479 | 0.0000 | 0.0100 | 0.0240 |
| ict_rolling | residual_XGBoost | 1.1005 | 2.0613 | 0.6455 | 0.0200 | 0.0100 | 0.0320 |
| elo_only | residual_XGBoost | 1.1021 | 2.0632 | 0.6458 | 0.0000 | 0.0000 | 0.0240 |
| no_team_strength | residual_XGBoost | 1.1028 | 2.0633 | 0.6567 | 0.0000 | 0.0100 | 0.0320 |
| current_stable | residual_CatBoost | 1.1035 | 2.0615 | 0.6485 | 0.0000 | 0.0100 | 0.0240 |
| fixture_home | residual_XGBoost | 1.1035 | 2.0617 | 0.6464 | 0.0000 | 0.0000 | 0.0240 |
| player_returns_rolling | residual_CatBoost | 1.1040 | 2.0622 | 0.6486 | 0.0000 | 0.0100 | 0.0200 |
| current_stable | residual_XGBoost | 1.1042 | 2.0626 | 0.6461 | 0.0000 | 0.0200 | 0.0240 |
| fixture_home | residual_CatBoost | 1.1044 | 2.0625 | 0.6484 | 0.0000 | 0.0100 | 0.0320 |
| player_returns_rolling | residual_XGBoost | 1.1046 | 2.0636 | 0.6455 | 0.0200 | 0.0100 | 0.0240 |
| expected_stats_rolling | residual_CatBoost | 1.1046 | 2.0610 | 0.6492 | 0.0000 | 0.0200 | 0.0360 |
| expected_stats_rolling | residual_XGBoost | 1.1048 | 2.0634 | 0.6457 | 0.0200 | 0.0200 | 0.0320 |
| team_form_only | residual_XGBoost | 1.1048 | 2.0657 | 0.6457 | 0.0000 | 0.0200 | 0.0400 |
| team_form_only | residual_CatBoost | 1.1051 | 2.0655 | 0.6484 | 0.0000 | 0.0100 | 0.0360 |
| ownership_transfers_lagged | CatBoost | 1.1076 | 2.0618 | 0.6530 | 0.0000 | 0.0000 | 0.0280 |
| all_safe_candidates | CatBoost | 1.1078 | 2.0604 | 0.6520 | 0.0200 | 0.0300 | 0.0440 |
| ownership_transfers_lagged | XGBoost | 1.1090 | 2.0650 | 0.6513 | 0.0000 | 0.0500 | 0.0320 |
| all_safe_candidates | XGBoost | 1.1099 | 2.0652 | 0.6505 | 0.0400 | 0.0200 | 0.0240 |
| elo_only | CatBoost | 1.1126 | 2.0721 | 0.6438 | 0.0000 | 0.0100 | 0.0320 |
| no_team_strength | CatBoost | 1.1129 | 2.0757 | 0.6470 | 0.0200 | 0.0200 | 0.0320 |
| elo_only | XGBoost | 1.1138 | 2.0730 | 0.6419 | 0.0000 | 0.0200 | 0.0240 |
| ict_rolling | CatBoost | 1.1139 | 2.0688 | 0.6436 | 0.0000 | 0.0100 | 0.0320 |
| ict_rolling | XGBoost | 1.1140 | 2.0727 | 0.6412 | 0.0000 | 0.0100 | 0.0160 |
| no_team_strength | XGBoost | 1.1149 | 2.0744 | 0.6490 | 0.0000 | 0.0100 | 0.0280 |
| fixture_home | XGBoost | 1.1161 | 2.0739 | 0.6416 | 0.0000 | 0.0100 | 0.0280 |
| current_stable | XGBoost | 1.1161 | 2.0742 | 0.6415 | 0.0000 | 0.0200 | 0.0320 |
| current_stable | CatBoost | 1.1161 | 2.0738 | 0.6432 | 0.0000 | 0.0200 | 0.0200 |
| fixture_home | CatBoost | 1.1162 | 2.0722 | 0.6435 | 0.0200 | 0.0200 | 0.0280 |
| expected_stats_rolling | XGBoost | 1.1172 | 2.0742 | 0.6410 | 0.0000 | 0.0100 | 0.0320 |
| player_returns_rolling | CatBoost | 1.1172 | 2.0734 | 0.6431 | 0.0200 | 0.0300 | 0.0200 |
| player_returns_rolling | XGBoost | 1.1174 | 2.0750 | 0.6411 | 0.0200 | 0.0100 | 0.0160 |
| expected_stats_rolling | CatBoost | 1.1177 | 2.0730 | 0.6436 | 0.0200 | 0.0200 | 0.0240 |
| team_form_only | CatBoost | 1.1178 | 2.0764 | 0.6433 | 0.0000 | 0.0300 | 0.0280 |
| team_form_only | XGBoost | 1.1180 | 2.0767 | 0.6415 | 0.0000 | 0.0200 | 0.0320 |
| ownership_transfers_lagged | global_plus_position_interactions | 1.1189 | 2.0478 | 0.6375 | 0.0200 | 0.0300 | 0.0520 |
| all_safe_candidates | residual_Ridge | 1.1196 | 2.0491 | 0.6431 | 0.0000 | 0.0300 | 0.0640 |
| ownership_transfers_lagged | residual_Ridge | 1.1199 | 2.0515 | 0.6422 | 0.0000 | 0.0200 | 0.0680 |
| all_safe_candidates | global_plus_position_interactions | 1.1225 | 2.0465 | 0.6378 | 0.0200 | 0.0100 | 0.0480 |
| ict_rolling | global_plus_position_interactions | 1.1250 | 2.0512 | 0.6323 | 0.0000 | 0.0400 | 0.0440 |
| elo_only | global_plus_position_interactions | 1.1251 | 2.0564 | 0.6329 | 0.0200 | 0.0200 | 0.0360 |
| no_team_strength | global_plus_position_interactions | 1.1254 | 2.0582 | 0.6396 | 0.0200 | 0.0200 | 0.0440 |
| ict_rolling | residual_Ridge | 1.1256 | 2.0574 | 0.6354 | 0.0200 | 0.0300 | 0.0480 |
| no_team_strength | residual_Ridge | 1.1257 | 2.0629 | 0.6428 | 0.0200 | 0.0200 | 0.0440 |
| elo_only | residual_Ridge | 1.1265 | 2.0612 | 0.6365 | 0.0000 | 0.0200 | 0.0400 |
| team_form_only | global_plus_position_interactions | 1.1275 | 2.0580 | 0.6340 | 0.0200 | 0.0200 | 0.0360 |
| fixture_home | global_plus_position_interactions | 1.1279 | 2.0564 | 0.6316 | 0.0200 | 0.0200 | 0.0360 |
| current_stable | global_plus_position_interactions | 1.1279 | 2.0564 | 0.6316 | 0.0200 | 0.0200 | 0.0360 |
| player_returns_rolling | global_plus_position_interactions | 1.1283 | 2.0562 | 0.6315 | 0.0000 | 0.0300 | 0.0400 |
| team_form_only | residual_Ridge | 1.1288 | 2.0629 | 0.6372 | 0.0200 | 0.0200 | 0.0440 |
| expected_stats_rolling | global_plus_position_interactions | 1.1290 | 2.0552 | 0.6323 | 0.0200 | 0.0300 | 0.0320 |
| player_returns_rolling | residual_Ridge | 1.1293 | 2.0620 | 0.6353 | 0.0200 | 0.0200 | 0.0480 |
| expected_stats_rolling | residual_Ridge | 1.1294 | 2.0593 | 0.6368 | 0.0400 | 0.0200 | 0.0400 |
| current_stable | residual_Ridge | 1.1295 | 2.0612 | 0.6358 | 0.0200 | 0.0200 | 0.0320 |
| fixture_home | residual_Ridge | 1.1295 | 2.0612 | 0.6358 | 0.0200 | 0.0200 | 0.0320 |
| all_safe_candidates | Ridge | 1.1345 | 2.0637 | 0.6353 | 0.0000 | 0.0200 | 0.0560 |
| ownership_transfers_lagged | Ridge | 1.1399 | 2.0682 | 0.6349 | 0.0000 | 0.0300 | 0.0640 |
| ict_rolling | Ridge | 1.1404 | 2.0718 | 0.6279 | 0.0200 | 0.0300 | 0.0320 |
| no_team_strength | Ridge | 1.1458 | 2.0797 | 0.6354 | 0.0200 | 0.0200 | 0.0360 |
| elo_only | Ridge | 1.1458 | 2.0781 | 0.6291 | 0.0000 | 0.0200 | 0.0400 |
| player_returns_rolling | Ridge | 1.1484 | 2.0782 | 0.6283 | 0.0200 | 0.0200 | 0.0400 |
| expected_stats_rolling | Ridge | 1.1490 | 2.0760 | 0.6295 | 0.0400 | 0.0200 | 0.0400 |
| current_stable | Ridge | 1.1491 | 2.0779 | 0.6283 | 0.0200 | 0.0300 | 0.0320 |
| fixture_home | Ridge | 1.1491 | 2.0779 | 0.6283 | 0.0200 | 0.0300 | 0.0320 |
| team_form_only | Ridge | 1.1491 | 2.0796 | 0.6302 | 0.0200 | 0.0200 | 0.0400 |

## Delta Versus Current Stable

Negative MAE/RMSE deltas help. Positive Spearman and precision deltas help.

| feature_group | model | delta_mae | delta_rmse | delta_spearman | delta_top_10_precision | delta_top_20_precision | delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| all_safe_candidates | minutes_adjusted_rolling_mean | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| elo_only | minutes_adjusted_rolling_mean | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| expected_stats_rolling | minutes_adjusted_rolling_mean | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| fixture_home | minutes_adjusted_rolling_mean | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| ict_rolling | minutes_adjusted_rolling_mean | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| no_team_strength | minutes_adjusted_rolling_mean | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| ownership_transfers_lagged | minutes_adjusted_rolling_mean | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| player_returns_rolling | minutes_adjusted_rolling_mean | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| team_form_only | minutes_adjusted_rolling_mean | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| all_safe_candidates | residual_CatBoost | -0.0098 | -0.0120 | 0.0095 | 0.0200 | 0.0100 | 0.0120 |
| ownership_transfers_lagged | residual_CatBoost | -0.0091 | -0.0113 | 0.0108 | 0.0000 | 0.0100 | 0.0120 |
| ownership_transfers_lagged | residual_XGBoost | -0.0086 | -0.0094 | 0.0111 | 0.0200 | 0.0100 | 0.0240 |
| all_safe_candidates | residual_XGBoost | -0.0085 | -0.0087 | 0.0103 | 0.0400 | 0.0100 | 0.0160 |
| elo_only | residual_CatBoost | -0.0036 | -0.0002 | 0.0001 | 0.0000 | 0.0100 | 0.0160 |
| no_team_strength | residual_CatBoost | -0.0033 | 0.0018 | 0.0047 | 0.0200 | 0.0100 | 0.0160 |
| ict_rolling | residual_CatBoost | -0.0031 | -0.0014 | -0.0006 | 0.0000 | 0.0000 | 0.0000 |
| ict_rolling | residual_XGBoost | -0.0037 | -0.0012 | -0.0005 | 0.0200 | -0.0100 | 0.0080 |
| elo_only | residual_XGBoost | -0.0021 | 0.0006 | -0.0003 | 0.0000 | -0.0200 | 0.0000 |
| no_team_strength | residual_XGBoost | -0.0014 | 0.0007 | 0.0106 | 0.0000 | -0.0100 | 0.0080 |
| fixture_home | residual_XGBoost | -0.0007 | -0.0009 | 0.0003 | 0.0000 | -0.0200 | 0.0000 |
| player_returns_rolling | residual_CatBoost | 0.0006 | 0.0007 | 0.0000 | 0.0000 | 0.0000 | -0.0040 |
| fixture_home | residual_CatBoost | 0.0009 | 0.0010 | -0.0002 | 0.0000 | 0.0000 | 0.0080 |
| player_returns_rolling | residual_XGBoost | 0.0004 | 0.0011 | -0.0006 | 0.0200 | -0.0100 | 0.0000 |
| expected_stats_rolling | residual_CatBoost | 0.0011 | -0.0005 | 0.0007 | 0.0000 | 0.0100 | 0.0120 |
| expected_stats_rolling | residual_XGBoost | 0.0006 | 0.0008 | -0.0004 | 0.0200 | 0.0000 | 0.0080 |
| team_form_only | residual_XGBoost | 0.0006 | 0.0031 | -0.0003 | 0.0000 | 0.0000 | 0.0160 |
| team_form_only | residual_CatBoost | 0.0016 | 0.0040 | -0.0001 | 0.0000 | 0.0000 | 0.0120 |
| ownership_transfers_lagged | CatBoost | -0.0086 | -0.0119 | 0.0098 | 0.0000 | -0.0200 | 0.0080 |
| all_safe_candidates | CatBoost | -0.0083 | -0.0133 | 0.0088 | 0.0200 | 0.0100 | 0.0240 |
| ownership_transfers_lagged | XGBoost | -0.0071 | -0.0092 | 0.0098 | 0.0000 | 0.0300 | 0.0000 |
| all_safe_candidates | XGBoost | -0.0062 | -0.0090 | 0.0091 | 0.0400 | 0.0000 | -0.0080 |
| elo_only | CatBoost | -0.0036 | -0.0017 | 0.0006 | 0.0000 | -0.0100 | 0.0120 |
| no_team_strength | CatBoost | -0.0033 | 0.0020 | 0.0038 | 0.0200 | 0.0000 | 0.0120 |
| elo_only | XGBoost | -0.0023 | -0.0012 | 0.0004 | 0.0000 | 0.0000 | -0.0080 |
| ict_rolling | CatBoost | -0.0023 | -0.0050 | 0.0004 | 0.0000 | -0.0100 | 0.0120 |
| ict_rolling | XGBoost | -0.0021 | -0.0015 | -0.0003 | 0.0000 | -0.0100 | -0.0160 |
| no_team_strength | XGBoost | -0.0012 | 0.0001 | 0.0076 | 0.0000 | -0.0100 | -0.0040 |
| fixture_home | XGBoost | -0.0000 | -0.0003 | 0.0001 | 0.0000 | -0.0100 | -0.0040 |
| fixture_home | CatBoost | 0.0000 | -0.0016 | 0.0003 | 0.0200 | 0.0000 | 0.0080 |
| expected_stats_rolling | XGBoost | 0.0011 | -0.0001 | -0.0005 | 0.0000 | -0.0100 | 0.0000 |
| player_returns_rolling | CatBoost | 0.0011 | -0.0004 | -0.0001 | 0.0200 | 0.0100 | 0.0000 |
| player_returns_rolling | XGBoost | 0.0013 | 0.0008 | -0.0004 | 0.0200 | -0.0100 | -0.0160 |
| expected_stats_rolling | CatBoost | 0.0016 | -0.0007 | 0.0004 | 0.0200 | 0.0000 | 0.0040 |
| team_form_only | CatBoost | 0.0017 | 0.0027 | 0.0001 | 0.0000 | 0.0100 | 0.0080 |
| team_form_only | XGBoost | 0.0018 | 0.0025 | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| ownership_transfers_lagged | global_plus_position_interactions | -0.0090 | -0.0086 | 0.0060 | 0.0000 | 0.0100 | 0.0160 |
| all_safe_candidates | residual_Ridge | -0.0099 | -0.0121 | 0.0072 | -0.0200 | 0.0100 | 0.0320 |
| ownership_transfers_lagged | residual_Ridge | -0.0096 | -0.0097 | 0.0064 | -0.0200 | 0.0000 | 0.0360 |
| all_safe_candidates | global_plus_position_interactions | -0.0054 | -0.0099 | 0.0062 | 0.0000 | -0.0100 | 0.0120 |
| ict_rolling | global_plus_position_interactions | -0.0030 | -0.0052 | 0.0008 | -0.0200 | 0.0200 | 0.0080 |
| elo_only | global_plus_position_interactions | -0.0028 | -0.0000 | 0.0014 | 0.0000 | 0.0000 | 0.0000 |
| no_team_strength | global_plus_position_interactions | -0.0025 | 0.0019 | 0.0080 | 0.0000 | 0.0000 | 0.0080 |
| ict_rolling | residual_Ridge | -0.0039 | -0.0038 | -0.0004 | 0.0000 | 0.0100 | 0.0160 |
| no_team_strength | residual_Ridge | -0.0038 | 0.0017 | 0.0070 | 0.0000 | 0.0000 | 0.0120 |
| elo_only | residual_Ridge | -0.0030 | 0.0000 | 0.0006 | -0.0200 | 0.0000 | 0.0080 |
| team_form_only | global_plus_position_interactions | -0.0004 | 0.0016 | 0.0024 | 0.0000 | 0.0000 | 0.0000 |
| fixture_home | global_plus_position_interactions | -0.0000 | -0.0000 | -0.0000 | 0.0000 | 0.0000 | 0.0000 |
| player_returns_rolling | global_plus_position_interactions | 0.0004 | -0.0002 | -0.0001 | -0.0200 | 0.0100 | 0.0040 |
| team_form_only | residual_Ridge | -0.0008 | 0.0017 | 0.0013 | 0.0000 | 0.0000 | 0.0120 |
| expected_stats_rolling | global_plus_position_interactions | 0.0010 | -0.0011 | 0.0008 | 0.0000 | 0.0100 | -0.0040 |
| player_returns_rolling | residual_Ridge | -0.0002 | 0.0008 | -0.0005 | 0.0000 | 0.0000 | 0.0160 |
| expected_stats_rolling | residual_Ridge | -0.0001 | -0.0019 | 0.0010 | 0.0200 | 0.0000 | 0.0080 |
| fixture_home | residual_Ridge | 0.0000 | 0.0000 | -0.0000 | 0.0000 | 0.0000 | 0.0000 |
| all_safe_candidates | Ridge | -0.0146 | -0.0142 | 0.0070 | -0.0200 | -0.0100 | 0.0240 |
| ownership_transfers_lagged | Ridge | -0.0091 | -0.0096 | 0.0066 | -0.0200 | 0.0000 | 0.0320 |
| ict_rolling | Ridge | -0.0087 | -0.0061 | -0.0005 | 0.0000 | 0.0000 | 0.0000 |
| no_team_strength | Ridge | -0.0033 | 0.0019 | 0.0070 | 0.0000 | -0.0100 | 0.0040 |
| elo_only | Ridge | -0.0032 | 0.0002 | 0.0008 | -0.0200 | -0.0100 | 0.0080 |
| player_returns_rolling | Ridge | -0.0007 | 0.0003 | -0.0000 | 0.0000 | -0.0100 | 0.0080 |
| expected_stats_rolling | Ridge | -0.0001 | -0.0019 | 0.0012 | 0.0200 | -0.0100 | 0.0080 |
| fixture_home | Ridge | 0.0000 | -0.0000 | -0.0000 | 0.0000 | 0.0000 | 0.0000 |
| team_form_only | Ridge | 0.0000 | 0.0018 | 0.0018 | 0.0000 | -0.0100 | 0.0080 |

## Feature Groups That Consistently Help Or Hurt

| feature_group | mean_delta_mae | mean_delta_rmse | mean_delta_spearman | mean_delta_top_10_precision | mean_delta_top_20_precision | mean_delta_top_50_precision |
| --- | --- | --- | --- | --- | --- | --- |
| all_safe_candidates | -0.0084 | -0.0108 | 0.0086 | 0.0120 | 0.0080 | 0.0128 |
| ownership_transfers_lagged | -0.0081 | -0.0093 | 0.0088 | -0.0020 | 0.0080 | 0.0148 |
| ict_rolling | -0.0033 | -0.0031 | -0.0003 | 0.0020 | 0.0020 | 0.0036 |
| no_team_strength | -0.0027 | 0.0012 | 0.0066 | 0.0040 | -0.0020 | 0.0044 |
| elo_only | -0.0026 | 0.0000 | 0.0004 | -0.0040 | -0.0020 | 0.0020 |
| fixture_home | 0.0001 | -0.0001 | 0.0001 | 0.0020 | -0.0030 | -0.0004 |
| team_form_only | 0.0005 | 0.0018 | 0.0009 | 0.0000 | 0.0010 | 0.0060 |
| player_returns_rolling | 0.0005 | 0.0004 | -0.0003 | 0.0040 | -0.0010 | 0.0000 |
| expected_stats_rolling | 0.0010 | -0.0005 | 0.0003 | 0.0080 | 0.0000 | 0.0056 |

## All Safe Candidates

Compare `all_safe_candidates` against `current_stable` in the delta table. A lower MAE/RMSE with stable or higher ranking metrics suggests improvement; worse error with mixed ranking suggests overfitting or redundant features.

## Recommended Default Feature Set

Use the lowest-error feature group that does not materially reduce Spearman or top-k precision. Keep `minutes_adjusted_rolling_mean` as the baseline reference.
