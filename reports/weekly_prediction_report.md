# Weekly Prediction Report

Season: `2025-26`
GW: `37`
Prediction rows: `data/interim/fpl_api/2025-26/prediction_rows_gw37.parquet`
Output: `data/predictions/latest_predictions.csv`
Top overall output: `data/predictions/latest_predictions_top_overall.csv`
By-position output: `data/predictions/latest_predictions_by_position.csv`

| level | rows |
| --- | ---: |
| fixture | 838 |
| player_gw | 838 |

| diagnostic | count |
| --- | ---: |
| negative predictions clipped | 3 |
| zero player-GW predictions | 438 |
| likely active player-GW rows | 407 |

Model: `minutes_adjusted_rolling_mean` only.

Prediction rows are combined with completed historical rows only for leakage-safe rolling feature calculation. Outcome and target columns remain missing for the upcoming rows.

Blank team/player diagnostics are available in `reports/prediction_row_builder_report.md`.

## Top 10 Overall

| position | name | team | value | fixture_count | expected_points_primary | likely_active |
| --- | --- | --- | --- | --- | --- | --- |
| DEF | Mavropanos | West Ham | 45 | 1 | 6.8 | True |
| DEF | Truffert | Bournemouth | 47 | 1 | 6.6 | True |
| DEF | Senesi | Bournemouth | 52 | 1 | 6.4 | True |
| MID | Doku | Man City | 65 | 1 | 6.04 | True |
| MID | Dewsbury-Hall | Everton | 52 | 1 | 6.0 | True |
| MID | Groß | Brighton | 56 | 1 | 6.0 | True |
| FWD | Bowen | West Ham | 77 | 1 | 5.96 | True |
| DEF | Mukiele | Sunderland | 46 | 1 | 5.88 | True |
| DEF | F.Kadıoğlu | Brighton | 44 | 1 | 5.8 | True |
| DEF | Gabriel | Arsenal | 73 | 1 | 5.8 | True |

## Top 10 By Position

| position | name | team | value | fixture_count | expected_points_primary | likely_active |
| --- | --- | --- | --- | --- | --- | --- |
| GK | Raya | Arsenal | 61 | 1 | 5.4 | True |
| GK | Lammens | Man Utd | 51 | 1 | 5.2 | True |
| GK | Leno | Fulham | 49 | 1 | 5.0 | True |
| GK | Verbruggen | Brighton | 46 | 1 | 5.0 | True |
| GK | Donnarumma | Man City | 56 | 1 | 4.6 | True |
| GK | Sels | Nott'm Forest | 46 | 1 | 4.6 | True |
| GK | Kelleher | Brentford | 48 | 1 | 4.2 | True |
| GK | Roefs | Sunderland | 48 | 1 | 4.2 | True |
| GK | Hermansen | West Ham | 42 | 1 | 3.8 | True |
| GK | Darlow | Leeds | 40 | 1 | 3.2 | True |
| DEF | Mavropanos | West Ham | 45 | 1 | 6.8 | True |
| DEF | Truffert | Bournemouth | 47 | 1 | 6.6 | True |
| DEF | Senesi | Bournemouth | 52 | 1 | 6.4 | True |
| DEF | Mukiele | Sunderland | 46 | 1 | 5.88 | True |
| DEF | F.Kadıoğlu | Brighton | 44 | 1 | 5.8 | True |
| DEF | Gabriel | Arsenal | 73 | 1 | 5.8 | True |
| DEF | Guéhi | Man City | 51 | 1 | 5.4 | True |
| DEF | Justin | Leeds | 40 | 1 | 5.2 | True |
| DEF | Van Hecke | Brighton | 47 | 1 | 5.0 | True |
| DEF | Hill | Bournemouth | 42 | 1 | 4.8 | True |
| MID | Doku | Man City | 65 | 1 | 6.04 | True |
| MID | Dewsbury-Hall | Everton | 52 | 1 | 6.0 | True |
| MID | Groß | Brighton | 56 | 1 | 6.0 | True |
| MID | Ampadu | Leeds | 49 | 1 | 5.2 | True |
| MID | Szoboszlai | Liverpool | 70 | 1 | 5.2 | True |
| MID | Hinshelwood | Brighton | 51 | 1 | 5.13 | True |
| MID | Anderson | Nott'm Forest | 56 | 1 | 5.04 | True |
| MID | Gibbs-White | Nott'm Forest | 75 | 1 | 4.87 | True |
| MID | Okafor | Leeds | 55 | 1 | 4.85 | True |
| MID | Casemiro | Man Utd | 59 | 1 | 4.8 | True |
| FWD | Bowen | West Ham | 77 | 1 | 5.96 | True |
| FWD | Osula | Newcastle | 54 | 1 | 5.0 | True |
| FWD | Haaland | Man City | 147 | 1 | 4.96 | True |
| FWD | Watkins | Aston Villa | 87 | 1 | 4.85 | True |
| FWD | Thiago | Brentford | 73 | 1 | 4.8 | True |
| FWD | Calvert-Lewin | Leeds | 58 | 1 | 4.6 | True |
| FWD | Igor Jesus | Nott'm Forest | 59 | 1 | 4.2 | True |
| FWD | Kroupi.Jr | Bournemouth | 46 | 1 | 3.93 | True |
| FWD | Gyökeres | Arsenal | 90 | 1 | 3.39 | True |
| FWD | Flemming | Burnley | 53 | 1 | 3.26 | True |
