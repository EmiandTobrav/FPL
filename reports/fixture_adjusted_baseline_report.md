# Fixture-Adjusted Minutes Baseline Experiment

Opt-in experiment. The existing `minutes_adjusted_rolling_mean` baseline is unchanged. Fixture multipliers are learned from training seasons only within each rolling-origin fold, then clipped to [0.75, 1.25].

## Overall Results

| model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- |
| minutes_adjusted_rolling_mean | 1.0098 | 2.1574 | 0.6715 | 0.0333 | 0.0667 | 0.0533 |
| minutes_adjusted_team_form | 1.0762 | 2.2275 | 0.6715 | 0.0333 | 0.0667 | 0.0533 |
| minutes_adjusted_fixture_adjusted | 1.0775 | 2.2299 | 0.6715 | 0.0333 | 0.0667 | 0.0600 |
| minutes_adjusted_elo | 1.0849 | 2.2431 | 0.6715 | 0.0333 | 0.0667 | 0.0533 |
| minutes_adjusted_home_away | 1.0882 | 2.2488 | 0.6715 | 0.0333 | 0.0667 | 0.0533 |

## GW-Bin Results

| segment | model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| GW1-5 | minutes_adjusted_rolling_mean | 1.1117 | 2.2882 | 0.6519 | 0.0333 | 0.0667 | 0.1133 |
| GW1-5 | minutes_adjusted_team_form | 1.2097 | 2.4272 | 0.6521 | 0.0333 | 0.0833 | 0.1200 |
| GW1-5 | minutes_adjusted_fixture_adjusted | 1.2106 | 2.4288 | 0.6521 | 0.0333 | 0.1000 | 0.1200 |
| GW1-5 | minutes_adjusted_elo | 1.2277 | 2.4638 | 0.6518 | 0.0333 | 0.0833 | 0.1200 |
| GW1-5 | minutes_adjusted_home_away | 1.2337 | 2.4762 | 0.6518 | 0.0333 | 0.0833 | 0.1067 |
| GW11+ | minutes_adjusted_rolling_mean | 0.9940 | 2.1434 | 0.6698 | 0.1000 | 0.0500 | 0.0533 |
| GW11+ | minutes_adjusted_team_form | 1.0565 | 2.2048 | 0.6698 | 0.1000 | 0.0500 | 0.0533 |
| GW11+ | minutes_adjusted_fixture_adjusted | 1.0578 | 2.2076 | 0.6697 | 0.1000 | 0.0500 | 0.0600 |
| GW11+ | minutes_adjusted_elo | 1.0636 | 2.2172 | 0.6698 | 0.1000 | 0.0500 | 0.0600 |
| GW11+ | minutes_adjusted_home_away | 1.0668 | 2.2223 | 0.6698 | 0.1000 | 0.0500 | 0.0600 |
| GW6-10 | minutes_adjusted_rolling_mean | 1.0222 | 2.1332 | 0.6893 | 0.0000 | 0.1000 | 0.1267 |
| GW6-10 | minutes_adjusted_team_form | 1.0855 | 2.1923 | 0.6893 | 0.0333 | 0.1000 | 0.1333 |
| GW6-10 | minutes_adjusted_fixture_adjusted | 1.0864 | 2.1931 | 0.6893 | 0.0667 | 0.1000 | 0.1333 |
| GW6-10 | minutes_adjusted_elo | 1.0944 | 2.2061 | 0.6893 | 0.0667 | 0.1000 | 0.1333 |
| GW6-10 | minutes_adjusted_home_away | 1.0962 | 2.2093 | 0.6893 | 0.0333 | 0.1000 | 0.1267 |

## Position Results

| segment | model | mae | rmse | spearman | top_10_precision | top_20_precision | top_50_precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| DEF | minutes_adjusted_rolling_mean | 1.0842 | 2.1957 | 0.5747 | 0.0000 | 0.0000 | 0.0133 |
| DEF | minutes_adjusted_team_form | 1.1591 | 2.2779 | 0.5748 | 0.0000 | 0.0000 | 0.0133 |
| DEF | minutes_adjusted_fixture_adjusted | 1.1609 | 2.2813 | 0.5747 | 0.0000 | 0.0000 | 0.0133 |
| DEF | minutes_adjusted_elo | 1.1695 | 2.2973 | 0.5747 | 0.0000 | 0.0000 | 0.0133 |
| DEF | minutes_adjusted_home_away | 1.1729 | 2.3029 | 0.5748 | 0.0000 | 0.0000 | 0.0133 |
| FWD | minutes_adjusted_rolling_mean | 1.0981 | 2.3789 | 0.7256 | 0.0000 | 0.1000 | 0.1533 |
| FWD | minutes_adjusted_team_form | 1.1594 | 2.4448 | 0.7257 | 0.0333 | 0.1000 | 0.1467 |
| FWD | minutes_adjusted_fixture_adjusted | 1.1605 | 2.4463 | 0.7258 | 0.0333 | 0.1167 | 0.1533 |
| FWD | minutes_adjusted_elo | 1.1677 | 2.4605 | 0.7257 | 0.0000 | 0.1000 | 0.1600 |
| FWD | minutes_adjusted_home_away | 1.1704 | 2.4661 | 0.7257 | 0.0000 | 0.1000 | 0.1600 |
| GK | minutes_adjusted_rolling_mean | 0.6725 | 1.6550 | 0.7723 | 0.0000 | 0.0167 | 0.1000 |
| GK | minutes_adjusted_team_form | 0.7426 | 1.7524 | 0.7723 | 0.0000 | 0.0167 | 0.1000 |
| GK | minutes_adjusted_fixture_adjusted | 0.7438 | 1.7549 | 0.7723 | 0.0000 | 0.0167 | 0.1133 |
| GK | minutes_adjusted_elo | 0.7515 | 1.7708 | 0.7722 | 0.0000 | 0.0167 | 0.1067 |
| GK | minutes_adjusted_home_away | 0.7547 | 1.7785 | 0.7723 | 0.0000 | 0.0167 | 0.1000 |
| MID | minutes_adjusted_rolling_mean | 1.0176 | 2.1772 | 0.7006 | 0.0667 | 0.0833 | 0.0733 |
| MID | minutes_adjusted_team_form | 1.0782 | 2.2345 | 0.7006 | 0.0333 | 0.0667 | 0.0867 |
| MID | minutes_adjusted_fixture_adjusted | 1.0791 | 2.2363 | 0.7005 | 0.0333 | 0.0833 | 0.0867 |
| MID | minutes_adjusted_elo | 1.0856 | 2.2467 | 0.7006 | 0.0667 | 0.0833 | 0.0800 |
| MID | minutes_adjusted_home_away | 1.0890 | 2.2523 | 0.7007 | 0.0667 | 0.0833 | 0.0800 |

## Learned Multipliers By Validation Season

| validation_season | model | multipliers_json | multiplier_source |
| --- | --- | --- | --- |
| 2023-24 | minutes_adjusted_elo | {"__default__": 1.24947, "favourite": 1.211088, "neutral": 1.210545, "underdog": 1.25} | training_seasons |
| 2023-24 | minutes_adjusted_fixture_adjusted | {"__default__": 1.24947, "difficult": 1.25, "favourable": 1.167465, "neutral": 1.25} | training_seasons |
| 2023-24 | minutes_adjusted_home_away | {"__default__": 1.24947, "away": 1.25, "home": 1.201084} | training_seasons |
| 2023-24 | minutes_adjusted_rolling_mean | {"minutes_adjusted_rolling_mean": 1.0} | original |
| 2023-24 | minutes_adjusted_team_form | {"__default__": 1.24947, "neutral": 1.25, "poor": 1.25, "strong": 1.162945} | training_seasons |
| 2024-25 | minutes_adjusted_elo | {"__default__": 1.25, "favourite": 1.179676, "neutral": 1.25, "underdog": 1.25} | training_seasons |
| 2024-25 | minutes_adjusted_fixture_adjusted | {"__default__": 1.25, "difficult": 1.25, "favourable": 1.151782, "neutral": 1.25} | training_seasons |
| 2024-25 | minutes_adjusted_home_away | {"__default__": 1.25, "away": 1.25, "home": 1.223132} | training_seasons |
| 2024-25 | minutes_adjusted_rolling_mean | {"minutes_adjusted_rolling_mean": 1.0} | original |
| 2024-25 | minutes_adjusted_team_form | {"__default__": 1.25, "neutral": 1.25, "poor": 1.25, "strong": 1.151682} | training_seasons |
| 2025-26 | minutes_adjusted_elo | {"__default__": 1.25, "favourite": 1.188954, "neutral": 1.25, "underdog": 1.25} | training_seasons |
| 2025-26 | minutes_adjusted_fixture_adjusted | {"__default__": 1.25, "difficult": 1.25, "favourable": 1.150834, "neutral": 1.25} | training_seasons |
| 2025-26 | minutes_adjusted_home_away | {"__default__": 1.25, "away": 1.25, "home": 1.238951} | training_seasons |
| 2025-26 | minutes_adjusted_rolling_mean | {"minutes_adjusted_rolling_mean": 1.0} | original |
| 2025-26 | minutes_adjusted_team_form | {"__default__": 1.25, "neutral": 1.25, "poor": 1.25, "strong": 1.140625} | training_seasons |

## Answers

- Best fixture-adjusted baseline by MAE: `minutes_adjusted_rolling_mean` (1.0098).
- Any fixture-adjusted version beats `minutes_adjusted_rolling_mean` on MAE: no.
- Any fixture-adjusted version improves Spearman: yes.
- Best GW1-5 model by MAE: `minutes_adjusted_rolling_mean`.
- Position effects should be judged from the position table above; improvements are not assumed uniform.
- Multiplier stability should be judged from the learned multiplier table; unstable season-to-season movement is a warning against promotion.

## Recommendation

Keep the original minutes-adjusted baseline.
