# Position Feature Relevance

Lightweight statistical audit of leakage-safe candidate features on the current trimmed rich-feature modelling dataset. This does not change model logic and does not run wrapper feature selection or broad ablation.

Candidate features audited: 50

## GK

### Top Features

| feature | non_missing_pct | spearman | pearson | mutual_information | mae_delta_vs_baseline | useful_seasons | stable_sign |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_mean_last_3 | 0.9683 | 0.7933 | 0.6169 | 0.3401 | -0.5661 | 3 | True |
| minutes_mean_last_5 | 0.9683 | 0.7801 | 0.6113 | 0.3395 | -0.5565 | 3 | True |
| pred_minutes_adjusted_rolling_mean | 0.9683 | 0.7736 | 0.5577 | 0.3360 | -0.4630 | 3 | True |
| pred_rolling_3_gameweek_mean | 0.9683 | 0.7797 | 0.5503 | 0.3359 | -0.4506 | 3 | True |
| points_mean_last_3 | 0.9683 | 0.7797 | 0.5503 | 0.3359 | -0.4506 | 3 | True |
| influence_mean_last_3 | 0.9683 | 0.7791 | 0.5534 | 0.3304 | -0.4523 | 3 | True |
| ict_index_mean_last_3 | 0.9683 | 0.7794 | 0.5543 | 0.3281 | -0.4525 | 3 | True |
| pred_rolling_5_gameweek_mean | 0.9683 | 0.7683 | 0.5646 | 0.3275 | -0.4815 | 3 | True |
| points_mean_last_5 | 0.9683 | 0.7683 | 0.5646 | 0.3275 | -0.4815 | 3 | True |
| bps_last_5 | 0.9683 | 0.7621 | 0.5727 | 0.3253 | -0.5240 | 3 | True |
| ict_index_mean_last_5 | 0.9683 | 0.7679 | 0.5632 | 0.3253 | -0.4698 | 3 | True |
| influence_mean_last_5 | 0.9683 | 0.7677 | 0.5618 | 0.3252 | -0.4692 | 3 | True |

### Appears Irrelevant

| feature | non_missing_pct | spearman | pearson | useful_seasons |
| --- | --- | --- | --- | --- |
| elo_difference | 1.0000 | 0.0066 | 0.0141 | 0 |
| home_adjusted_elo_difference | 1.0000 | 0.0022 | 0.0087 | 0 |
| opponent_elo_pre_gw | 1.0000 | 0.0008 | 0.0047 | 0 |
| team_elo_pre_gw | 1.0000 | 0.0082 | 0.0251 | 0 |
| was_home | 1.0000 | -0.0033 | -0.0048 | 0 |
| opponent_clean_sheet_rate_last_5 | 0.9753 | -0.0012 | -0.0055 | 0 |
| opponent_goals_conceded_mean_last_5 | 0.9753 | -0.0044 | -0.0016 | 0 |
| opponent_goals_scored_mean_last_5 | 0.9753 | 0.0045 | 0.0103 | 0 |
| team_clean_sheet_rate_last_5 | 0.9753 | 0.0141 | 0.0215 | 0 |
| team_goals_scored_mean_last_5 | 0.9753 | -0.0078 | 0.0143 | 0 |
| goals_scored_mean_last_3 | 0.9683 |  |  | 0 |
| goals_scored_mean_last_5 | 0.9683 |  |  | 0 |

### Unstable Sign Across Seasons

| feature | spearman | useful_seasons | mean_abs_spearman_rank |
| --- | --- | --- | --- |
| transfers_balance_lag_1 | 0.0703 | 2 | 36.6667 |
| expected_goals_mean_last_5 | 0.0632 | 2 | 35.0000 |
| expected_goals_mean_last_3 | 0.0560 | 2 | 37.0000 |
| team_goals_conceded_mean_last_5 | -0.0209 | 1 | 41.3333 |
| team_elo_pre_gw | 0.0082 | 0 | 39.6667 |
| elo_difference | 0.0066 | 0 | 42.6667 |
| team_goals_scored_mean_last_5 | -0.0078 | 0 | 42.0000 |
| home_adjusted_elo_difference | 0.0022 | 0 | 42.0000 |
| was_home | -0.0033 | 0 | 46.0000 |
| opponent_elo_pre_gw | 0.0008 | 0 | 45.6667 |
| opponent_goals_conceded_mean_last_5 | -0.0044 | 0 | 44.0000 |
| opponent_clean_sheet_rate_last_5 | -0.0012 | 0 | 44.0000 |

### High Missingness

No features exceeded the missingness threshold.

### Suggested Statistical Mask

- `minutes_mean_last_3`
- `minutes_mean_last_5`
- `pred_minutes_adjusted_rolling_mean`
- `pred_rolling_3_gameweek_mean`
- `points_mean_last_3`
- `influence_mean_last_3`
- `ict_index_mean_last_3`
- `pred_rolling_5_gameweek_mean`
- `points_mean_last_5`
- `bps_last_5`
- `ict_index_mean_last_5`
- `influence_mean_last_5`
- `points_last_1`
- `goals_conceded_mean_last_5`
- `goals_conceded_mean_last_3`
- `starts_last_5`
- `expected_goals_conceded_mean_last_3`
- `expected_goals_conceded_mean_last_5`
- `clean_sheets_mean_last_5`
- `selected_lag_1`

## DEF

### Top Features

| feature | non_missing_pct | spearman | pearson | mutual_information | mae_delta_vs_baseline | useful_seasons | stable_sign |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_mean_last_3 | 0.9687 | 0.5854 | 0.4298 | 0.2259 | -0.2518 | 3 | True |
| minutes_mean_last_5 | 0.9687 | 0.5823 | 0.4236 | 0.2159 | -0.2491 | 3 | True |
| ict_index_mean_last_5 | 0.9687 | 0.5738 | 0.4038 | 0.2134 | -0.2051 | 3 | True |
| ict_index_mean_last_3 | 0.9687 | 0.5751 | 0.4010 | 0.2039 | -0.1985 | 3 | True |
| influence_mean_last_3 | 0.9687 | 0.5707 | 0.4002 | 0.2071 | -0.1990 | 3 | True |
| influence_mean_last_5 | 0.9687 | 0.5688 | 0.4029 | 0.1992 | -0.2057 | 3 | True |
| pred_minutes_adjusted_rolling_mean | 0.9687 | 0.5699 | 0.3795 | 0.2105 | -0.1666 | 3 | True |
| bps_last_5 | 0.9687 | 0.5478 | 0.3979 | 0.2108 | -0.2431 | 3 | True |
| pred_rolling_5_gameweek_mean | 0.9687 | 0.5599 | 0.3901 | 0.2015 | -0.1903 | 3 | True |
| points_mean_last_5 | 0.9687 | 0.5599 | 0.3901 | 0.2015 | -0.1903 | 3 | True |
| pred_rolling_3_gameweek_mean | 0.9687 | 0.5528 | 0.3748 | 0.2007 | -0.1709 | 3 | True |
| points_mean_last_3 | 0.9687 | 0.5528 | 0.3748 | 0.2007 | -0.1709 | 3 | True |

### Appears Irrelevant

| feature | non_missing_pct | spearman | pearson | useful_seasons |
| --- | --- | --- | --- | --- |
| home_adjusted_elo_difference | 1.0000 | 0.0100 | 0.0206 | 0 |
| opponent_elo_pre_gw | 1.0000 | 0.0046 | 0.0042 | 0 |
| was_home | 1.0000 | -0.0150 | -0.0198 | 0 |
| opponent_clean_sheet_rate_last_5 | 0.9749 | -0.0016 | -0.0068 | 0 |
| opponent_goals_conceded_mean_last_5 | 0.9749 | -0.0041 | 0.0023 | 0 |
| opponent_goals_scored_mean_last_5 | 0.9749 | 0.0006 | 0.0027 | 0 |

### Unstable Sign Across Seasons

| feature | spearman | useful_seasons | mean_abs_spearman_rank |
| --- | --- | --- | --- |
| home_adjusted_elo_difference | 0.0100 | 0 | 43.6667 |
| team_goals_scored_mean_last_5 | 0.0141 | 0 | 42.6667 |
| opponent_elo_pre_gw | 0.0046 | 0 | 46.6667 |
| opponent_clean_sheet_rate_last_5 | -0.0016 | 0 | 48.6667 |
| opponent_goals_conceded_mean_last_5 | -0.0041 | 0 | 49.3333 |

### High Missingness

No features exceeded the missingness threshold.

### Suggested Statistical Mask

- `minutes_mean_last_3`
- `minutes_mean_last_5`
- `ict_index_mean_last_5`
- `ict_index_mean_last_3`
- `influence_mean_last_3`
- `influence_mean_last_5`
- `pred_minutes_adjusted_rolling_mean`
- `bps_last_5`
- `pred_rolling_5_gameweek_mean`
- `points_mean_last_5`
- `pred_rolling_3_gameweek_mean`
- `points_mean_last_3`
- `creativity_mean_last_3`
- `creativity_mean_last_5`
- `starts_last_5`
- `goals_conceded_mean_last_5`
- `threat_mean_last_5`
- `points_last_1`
- `goals_conceded_mean_last_3`
- `threat_mean_last_3`

## MID

### Top Features

| feature | non_missing_pct | spearman | pearson | mutual_information | mae_delta_vs_baseline | useful_seasons | stable_sign |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_mean_last_5 | 0.9685 | 0.7035 | 0.4964 | 0.3441 | -0.4079 | 3 | True |
| minutes_mean_last_3 | 0.9685 | 0.7080 | 0.4966 | 0.3346 | -0.4025 | 3 | True |
| ict_index_mean_last_5 | 0.9685 | 0.7006 | 0.5008 | 0.3304 | -0.3684 | 3 | True |
| ict_index_mean_last_3 | 0.9685 | 0.7011 | 0.4875 | 0.3331 | -0.3449 | 3 | True |
| pred_rolling_5_gameweek_mean | 0.9685 | 0.6957 | 0.4858 | 0.3332 | -0.3575 | 3 | True |
| points_mean_last_5 | 0.9685 | 0.6957 | 0.4858 | 0.3332 | -0.3575 | 3 | True |
| pred_minutes_adjusted_rolling_mean | 0.9685 | 0.7043 | 0.4650 | 0.3433 | -0.3027 | 3 | True |
| influence_mean_last_5 | 0.9685 | 0.6942 | 0.4699 | 0.3344 | -0.3342 | 3 | True |
| bps_last_5 | 0.9685 | 0.6857 | 0.4740 | 0.3374 | -0.3309 | 3 | True |
| pred_rolling_3_gameweek_mean | 0.9685 | 0.6944 | 0.4665 | 0.3295 | -0.3273 | 3 | True |
| points_mean_last_3 | 0.9685 | 0.6944 | 0.4665 | 0.3295 | -0.3273 | 3 | True |
| influence_mean_last_3 | 0.9685 | 0.6923 | 0.4483 | 0.3199 | -0.3022 | 3 | True |

### Appears Irrelevant

| feature | non_missing_pct | spearman | pearson | useful_seasons |
| --- | --- | --- | --- | --- |
| opponent_elo_pre_gw | 1.0000 | -0.0000 | 0.0019 | 0 |
| was_home | 1.0000 | -0.0058 | -0.0160 | 0 |
| opponent_clean_sheet_rate_last_5 | 0.9753 | 0.0033 | 0.0007 | 0 |
| opponent_goals_conceded_mean_last_5 | 0.9753 | -0.0061 | -0.0017 | 0 |
| opponent_goals_scored_mean_last_5 | 0.9753 | -0.0021 | 0.0019 | 0 |
| team_clean_sheet_rate_last_5 | 0.9753 | 0.0176 | 0.0272 | 0 |

### Unstable Sign Across Seasons

| feature | spearman | useful_seasons | mean_abs_spearman_rank |
| --- | --- | --- | --- |
| transfers_balance_lag_1 | -0.0071 | 1 | 43.0000 |
| opponent_clean_sheet_rate_last_5 | 0.0033 | 0 | 48.0000 |
| opponent_elo_pre_gw | -0.0000 | 0 | 49.3333 |
| opponent_goals_conceded_mean_last_5 | -0.0061 | 0 | 47.0000 |
| opponent_goals_scored_mean_last_5 | -0.0021 | 0 | 46.0000 |

### High Missingness

No features exceeded the missingness threshold.

### Suggested Statistical Mask

- `minutes_mean_last_5`
- `minutes_mean_last_3`
- `ict_index_mean_last_5`
- `ict_index_mean_last_3`
- `pred_rolling_5_gameweek_mean`
- `points_mean_last_5`
- `pred_minutes_adjusted_rolling_mean`
- `influence_mean_last_5`
- `bps_last_5`
- `pred_rolling_3_gameweek_mean`
- `points_mean_last_3`
- `influence_mean_last_3`
- `creativity_mean_last_5`
- `creativity_mean_last_3`
- `threat_mean_last_5`
- `threat_mean_last_3`
- `points_last_1`
- `expected_goal_involvements_mean_last_5`
- `expected_goal_involvements_mean_last_3`
- `goals_conceded_mean_last_5`

## FWD

### Top Features

| feature | non_missing_pct | spearman | pearson | mutual_information | mae_delta_vs_baseline | useful_seasons | stable_sign |
| --- | --- | --- | --- | --- | --- | --- | --- |
| minutes_mean_last_5 | 0.9681 | 0.7086 | 0.4964 | 0.3299 | -0.4086 | 3 | True |
| minutes_mean_last_3 | 0.9681 | 0.7130 | 0.4938 | 0.3196 | -0.3980 | 3 | True |
| pred_minutes_adjusted_rolling_mean | 0.9681 | 0.7113 | 0.4597 | 0.3318 | -0.3094 | 3 | True |
| pred_rolling_5_gameweek_mean | 0.9681 | 0.7049 | 0.4855 | 0.3041 | -0.3906 | 3 | True |
| points_mean_last_5 | 0.9681 | 0.7049 | 0.4855 | 0.3041 | -0.3906 | 3 | True |
| pred_rolling_3_gameweek_mean | 0.9681 | 0.7022 | 0.4675 | 0.3240 | -0.3587 | 3 | True |
| points_mean_last_3 | 0.9681 | 0.7022 | 0.4675 | 0.3240 | -0.3587 | 3 | True |
| ict_index_mean_last_5 | 0.9681 | 0.7008 | 0.4829 | 0.3084 | -0.3911 | 3 | True |
| ict_index_mean_last_3 | 0.9681 | 0.7002 | 0.4673 | 0.3051 | -0.3624 | 3 | True |
| threat_mean_last_5 | 0.9681 | 0.6848 | 0.4613 | 0.3011 | -0.3653 | 3 | True |
| influence_mean_last_5 | 0.9681 | 0.6857 | 0.4535 | 0.2878 | -0.3181 | 3 | True |
| bps_last_5 | 0.9681 | 0.6644 | 0.4463 | 0.3020 | -0.2925 | 3 | True |

### Appears Irrelevant

| feature | non_missing_pct | spearman | pearson | useful_seasons |
| --- | --- | --- | --- | --- |
| opponent_elo_pre_gw | 1.0000 | 0.0054 | -0.0091 | 0 |
| was_home | 1.0000 | -0.0099 | -0.0224 | 0 |
| opponent_clean_sheet_rate_last_5 | 0.9758 | 0.0080 | -0.0010 | 0 |
| opponent_goals_conceded_mean_last_5 | 0.9758 | -0.0196 | -0.0084 | 0 |
| opponent_goals_scored_mean_last_5 | 0.9758 | -0.0111 | -0.0076 | 0 |

### Unstable Sign Across Seasons

| feature | spearman | useful_seasons | mean_abs_spearman_rank |
| --- | --- | --- | --- |
| transfers_balance_lag_1 | 0.0367 | 2 | 42.6667 |
| team_goals_conceded_mean_last_5 | -0.0446 | 1 | 45.0000 |
| team_clean_sheet_rate_last_5 | 0.0316 | 1 | 45.6667 |
| home_adjusted_elo_difference | 0.0256 | 1 | 44.3333 |
| opponent_goals_scored_mean_last_5 | -0.0111 | 0 | 44.3333 |
| opponent_elo_pre_gw | 0.0054 | 0 | 45.0000 |
| opponent_clean_sheet_rate_last_5 | 0.0080 | 0 | 45.3333 |

### High Missingness

No features exceeded the missingness threshold.

### Suggested Statistical Mask

- `minutes_mean_last_5`
- `minutes_mean_last_3`
- `pred_minutes_adjusted_rolling_mean`
- `pred_rolling_5_gameweek_mean`
- `points_mean_last_5`
- `pred_rolling_3_gameweek_mean`
- `points_mean_last_3`
- `ict_index_mean_last_5`
- `ict_index_mean_last_3`
- `threat_mean_last_5`
- `influence_mean_last_5`
- `bps_last_5`
- `threat_mean_last_3`
- `creativity_mean_last_5`
- `creativity_mean_last_3`
- `influence_mean_last_3`
- `points_last_1`
- `goals_conceded_mean_last_5`
- `expected_goal_involvements_mean_last_5`
- `expected_goals_conceded_mean_last_3`

## Recommended Next Test

| position | suggested_feature_count |
| --- | --- |
| GK | 20 |
| DEF | 20 |
| MID | 20 |
| FWD | 20 |

Test these masks as a separate modelling experiment, starting with the position-specific masks for GK and FWD where role-specific signal is usually most distinct. Keep the current global feature set as the control and continue using rolling-origin validation.
