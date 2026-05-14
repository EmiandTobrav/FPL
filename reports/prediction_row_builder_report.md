# Prediction Row Builder Report

Season: `2025-26`
Target prediction GW: `37`
Output: `data/interim/fpl_api/2025-26/prediction_rows_gw37.parquet`

| diagnostic | value |
| --- | ---: |
| fixtures | 10 |
| player-fixture rows | 838 |
| blank affected players | 0 |

Teams with blanks: None

Teams with double fixtures: None

Required columns present: season, gw, element, name, team, opponent_team, was_home, position, value, selected, transfers_in, transfers_out, total_points, minutes, starts, bonus, bps, fixture

Required columns missing: None

Outcome columns set to missing: total_points, minutes, starts, bonus, bps

Missing versus completed merged_gw_api schema: None

## Assumptions

- Prediction rows contain known fixture/player context only.
- Actual outcome columns are present but set to NA.
- Players on teams without a fixture in the target GW are omitted.
- Double gameweeks naturally create multiple player-fixture rows.
