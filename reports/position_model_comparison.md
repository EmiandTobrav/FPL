# Position Model Comparison

Base direct model: Ridge. Rolling-origin validation by season.

## Overall

| strategy | seasons | mean_mae | mean_rmse | mean_spearman | mean_top_10_precision | mean_top_10_avg_actual_points | mean_top_20_precision | mean_top_20_avg_actual_points | mean_top_50_precision | mean_top_50_avg_actual_points |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_plus_position_interactions | 3 | 1.0819 | 2.0210 | 0.6357 | 0.0333 | 5.5000 | 0.0333 | 5.1000 | 0.0600 | 5.1800 |
| position_wise_models | 3 | 1.0881 | 2.0250 | 0.6340 | 0.0333 | 5.5000 | 0.0333 | 5.1167 | 0.0600 | 5.1000 |

## By Position

| strategy | position | mean_mae | mean_rmse | mean_spearman | mean_top_10_precision | mean_top_10_avg_actual_points | mean_top_20_precision | mean_top_20_avg_actual_points | mean_top_50_precision | mean_top_50_avg_actual_points |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| global_plus_position_interactions | DEF | 1.1458 | 2.0571 | 0.5484 | 0.0000 | 3.3000 | 0.0500 | 4.6000 | 0.0467 | 4.3400 |
| position_wise_models | DEF | 1.1532 | 2.0614 | 0.5454 | 0.0333 | 3.7000 | 0.0333 | 4.8333 | 0.0467 | 4.2400 |
| global_plus_position_interactions | FWD | 1.2381 | 2.2119 | 0.6683 | 0.0000 | 5.7000 | 0.1167 | 4.9000 | 0.1467 | 4.7333 |
| position_wise_models | FWD | 1.2422 | 2.2138 | 0.6693 | 0.0000 | 5.7000 | 0.1167 | 4.9500 | 0.1400 | 4.6733 |
| global_plus_position_interactions | GK | 0.7321 | 1.5510 | 0.6145 | 0.0000 | 3.0333 | 0.0167 | 3.1333 | 0.0667 | 3.2733 |
| position_wise_models | GK | 0.7395 | 1.5561 | 0.6014 | 0.0000 | 2.4667 | 0.0167 | 2.9500 | 0.0533 | 3.1400 |
| global_plus_position_interactions | MID | 1.0822 | 2.0431 | 0.6676 | 0.0333 | 5.4667 | 0.0500 | 5.3667 | 0.0667 | 4.7667 |
| position_wise_models | MID | 1.0879 | 2.0474 | 0.6678 | 0.0333 | 5.5667 | 0.0500 | 5.3833 | 0.0667 | 4.8533 |

## Diagnostics

- No unknown position labels were found after applying position normalization.


## By Validation Season And Position

| validation_season | n_train | n_validation | mae | rmse | spearman | top_10_precision | top_10_avg_actual_points | top_20_precision | top_20_avg_actual_points | top_50_precision | top_50_avg_actual_points | strategy | position |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2023-24 | 25727 | 28860 | 1.0786 | 2.0048 | 0.6158 | 0.0000 | 3.5000 | 0.0000 | 4.3000 | 0.0200 | 5.2000 | global_plus_position_interactions | ALL |
| 2023-24 | 25727 | 9333 | 1.1616 | 2.0196 | 0.5116 | 0.0000 | 3.4000 | 0.1000 | 5.4000 | 0.0400 | 4.5800 | global_plus_position_interactions | DEF |
| 2023-24 | 25727 | 3741 | 1.2280 | 2.2126 | 0.6299 | 0.0000 | 3.8000 | 0.0000 | 3.9000 | 0.1600 | 4.6200 | global_plus_position_interactions | FWD |
| 2023-24 | 25727 | 3313 | 0.7400 | 1.4990 | 0.6046 | 0.0000 | 2.3000 | 0.0000 | 2.5500 | 0.0600 | 3.0000 | global_plus_position_interactions | GK |
| 2023-24 | 25727 | 12473 | 1.0616 | 2.0452 | 0.6641 | 0.0000 | 5.6000 | 0.0500 | 5.8500 | 0.0400 | 5.0400 | global_plus_position_interactions | MID |
| 2023-24 | 25727 | 28860 | 1.0835 | 2.0065 | 0.6141 | 0.0000 | 3.5000 | 0.0000 | 4.3000 | 0.0200 | 5.0200 | position_wise_models | ALL |
| 2023-24 | 25727 | 9333 | 1.1688 | 2.0213 | 0.5070 | 0.1000 | 5.3000 | 0.0500 | 5.5000 | 0.0400 | 4.3800 | position_wise_models | DEF |
| 2023-24 | 25727 | 3741 | 1.2278 | 2.2128 | 0.6309 | 0.0000 | 3.8000 | 0.0000 | 3.6500 | 0.1600 | 4.7000 | position_wise_models | FWD |
| 2023-24 | 25727 | 3313 | 0.7485 | 1.5048 | 0.5915 | 0.0000 | 1.9000 | 0.0000 | 2.4000 | 0.0400 | 2.9200 | position_wise_models | GK |
| 2023-24 | 25727 | 12473 | 1.0654 | 2.0466 | 0.6648 | 0.0000 | 6.3000 | 0.0500 | 5.9000 | 0.0400 | 5.1200 | position_wise_models | MID |
| 2024-25 | 54587 | 26499 | 1.0769 | 2.0040 | 0.6406 | 0.1000 | 8.3000 | 0.1000 | 7.1500 | 0.1200 | 6.4600 | global_plus_position_interactions | ALL |
| 2024-25 | 54587 | 8878 | 1.0632 | 1.9167 | 0.5533 | 0.0000 | 4.1000 | 0.0500 | 4.9000 | 0.0400 | 4.2400 | global_plus_position_interactions | DEF |
| 2024-25 | 54587 | 2931 | 1.3047 | 2.3125 | 0.6742 | 0.0000 | 7.9000 | 0.1000 | 5.0500 | 0.1000 | 4.9000 | global_plus_position_interactions | FWD |
| 2024-25 | 54587 | 2787 | 0.8045 | 1.6802 | 0.6064 | 0.0000 | 3.6000 | 0.0000 | 2.9500 | 0.0800 | 3.1800 | global_plus_position_interactions | GK |
| 2024-25 | 54587 | 11903 | 1.0949 | 2.0549 | 0.6729 | 0.1000 | 8.0000 | 0.1000 | 7.2000 | 0.1400 | 6.3400 | global_plus_position_interactions | MID |
| 2024-25 | 54587 | 26499 | 1.0849 | 2.0089 | 0.6382 | 0.1000 | 8.3000 | 0.1000 | 7.2000 | 0.1200 | 6.3600 | position_wise_models | ALL |
| 2024-25 | 54587 | 8878 | 1.0711 | 1.9211 | 0.5502 | 0.0000 | 3.3000 | 0.0500 | 4.9000 | 0.0400 | 4.1400 | position_wise_models | DEF |
| 2024-25 | 54587 | 2931 | 1.3132 | 2.3163 | 0.6738 | 0.0000 | 7.9000 | 0.1000 | 5.4500 | 0.0800 | 4.6400 | position_wise_models | FWD |
| 2024-25 | 54587 | 2787 | 0.8111 | 1.6835 | 0.5923 | 0.0000 | 2.3000 | 0.0000 | 2.5500 | 0.0600 | 2.9800 | position_wise_models | GK |
| 2024-25 | 54587 | 11903 | 1.1032 | 2.0609 | 0.6720 | 0.1000 | 7.6000 | 0.1000 | 7.2000 | 0.1400 | 6.3400 | position_wise_models | MID |
| 2025-26 | 81086 | 21533 | 1.0900 | 2.0541 | 0.6507 | 0.0000 | 4.7000 | 0.0000 | 3.8500 | 0.0400 | 3.8800 | global_plus_position_interactions | ALL |
| 2025-26 | 81086 | 7078 | 1.2127 | 2.2350 | 0.5802 | 0.0000 | 2.4000 | 0.0000 | 3.5000 | 0.0600 | 4.2000 | global_plus_position_interactions | DEF |
| 2025-26 | 81086 | 2369 | 1.1818 | 2.1106 | 0.7009 | 0.0000 | 5.4000 | 0.2500 | 5.7500 | 0.1800 | 4.6800 | global_plus_position_interactions | FWD |
| 2025-26 | 81086 | 2476 | 0.6517 | 1.4737 | 0.6324 | 0.0000 | 3.2000 | 0.0500 | 3.9000 | 0.0600 | 3.6400 | global_plus_position_interactions | GK |
| 2025-26 | 81086 | 9610 | 1.0900 | 2.0292 | 0.6658 | 0.0000 | 2.8000 | 0.0000 | 3.0500 | 0.0200 | 2.9200 | global_plus_position_interactions | MID |
| 2025-26 | 81086 | 21533 | 1.0959 | 2.0596 | 0.6496 | 0.0000 | 4.7000 | 0.0000 | 3.8500 | 0.0400 | 3.9200 | position_wise_models | ALL |
| 2025-26 | 81086 | 7078 | 1.2197 | 2.2417 | 0.5789 | 0.0000 | 2.5000 | 0.0000 | 4.1000 | 0.0600 | 4.2000 | position_wise_models | DEF |
| 2025-26 | 81086 | 2369 | 1.1855 | 2.1122 | 0.7033 | 0.0000 | 5.4000 | 0.2500 | 5.7500 | 0.1800 | 4.6800 | position_wise_models | FWD |
| 2025-26 | 81086 | 2476 | 0.6589 | 1.4800 | 0.6204 | 0.0000 | 3.2000 | 0.0500 | 3.9000 | 0.0600 | 3.5200 | position_wise_models | GK |
| 2025-26 | 81086 | 9610 | 1.0952 | 2.0346 | 0.6668 | 0.0000 | 2.8000 | 0.0000 | 3.0500 | 0.0200 | 3.1000 | position_wise_models | MID |
