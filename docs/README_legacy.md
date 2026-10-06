\# FPL Prediction Project



This project predicts Fantasy Premier League player points using historical FPL data from Vaastav's public dataset.



\## Current modelling setup



The current default pipeline uses rich-feature seasons from 2022-23 onward.



The strongest current model by MAE and Spearman is:



\- `minutes\_adjusted\_rolling\_mean`



Useful specialist models include:



\- `residual\_CatBoost` for RMSE/upside

\- `rolling\_3\_gameweek\_mean` and `rolling\_5\_gameweek\_mean` as ranking/diagnostic baselines



\## Setup



```bash

python -m pip install -e .


