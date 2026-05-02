# Team-Strength Feature Report

## Identifier Mapping Diagnostics

| diagnostic | value |
| --- | ---: |
| rows with valid normalized team IDs | 63.3% |
| rows with valid normalized opponent IDs | 63.3% |

Seasons where mapping works: 2020-21, 2021-22, 2022-23, 2023-24, 2024-25, 2025-26

Seasons where mapping fails:

- `2016-17`: team/opponent identifier types are unsupported or team names are missing
- `2017-18`: team/opponent identifier types are unsupported or team names are missing
- `2018-19`: team/opponent identifier types are unsupported or team names are missing
- `2019-20`: team/opponent identifier types are unsupported or team names are missing

## Features Added

- `team_elo_pre_gw`
- `opponent_elo_pre_gw`
- `elo_difference`
- `home_adjusted_elo_difference`
- `team_goals_scored_mean_last_5`
- `team_goals_conceded_mean_last_5`
- `opponent_goals_scored_mean_last_5`
- `opponent_goals_conceded_mean_last_5`
- `team_clean_sheet_rate_last_5`
- `opponent_clean_sheet_rate_last_5`

Raw `team` and `opponent_team` are used only as source columns for normalized identifiers and are not model features.

## Rolling Team Form

Rolling team attack and defence features are shifted by team-season gameweek, so GW t uses only gameweeks before GW t. Seasons without reliable normalized team/opponent IDs are left missing.

## Elo Initialization

- `base_elo = 1500`
- `k_factor = 20`
- `home_advantage = 50`
- Optional manual priors are read from `data/manual/team_season_priors.csv` when present.
