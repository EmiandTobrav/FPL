"""Read prepared data and select causal training rows; no fitting or imputation."""
from pathlib import Path
import json
import pandas as pd

KEY=['season','round','code']
def load_rows(root=None,clock='operational_proxy_v1'):
    root=Path(root) if root else Path(__file__).resolve().parent
    schema=json.loads((root/'schema.json').read_text())
    if clock not in schema['clock_policies']:raise ValueError('Unknown clock')
    rows=pd.read_csv(root/f'{clock}.csv.xz',low_memory=False)
    for col in ['forecast_at']+[c for c in rows if c.startswith('target_h')]:
        rows[col]=pd.to_datetime(rows[col],utc=True)
    return rows,schema

def select_training_rows(rows,forecast_at,horizon=1,window_days=None):
    if horizon not in [1,3,6]:raise ValueError('horizon must be 1, 3 or 6')
    forecast_at=pd.Timestamp(forecast_at)
    if forecast_at.tzinfo is None:raise ValueError('forecast_at must include timezone')
    target='target_total_points' if horizon==1 else f'target_points_h{horizon}'
    mask=(rows.forecast_at<forecast_at)&(rows[f'target_h{horizon}_available_at']<forecast_at)&rows[target].notna()
    if window_days is not None:
        if window_days<=0:raise ValueError('window_days must be positive')
        mask &= rows.forecast_at >= forecast_at-pd.Timedelta(days=window_days)
    return rows.loc[mask].copy()

def model_view(rows,schema,feature_set='baseline',horizon=1,require_target=False):
    if feature_set not in ['baseline','extended']:raise ValueError('Unknown feature set')
    if horizon not in [1,3,6]:raise ValueError('Unknown horizon')
    features=schema[f'{feature_set}_features'];target=schema['target_columns'][str(horizon)]
    selected=rows[rows[target].notna()] if require_target else rows
    return {'X':selected[features].copy(),'y':selected[target].copy(),'keys':selected[KEY].copy(),'feature_names':features,'missing_values_preserved':True}

def walk_forward_rows(rows,start_season='2022-23',end_season='2025-26',horizon=1,window_days=None):
    periods=rows[rows.season.between(start_season,end_season)][['season','round','forecast_at']].drop_duplicates().sort_values('forecast_at')
    for period in periods.itertuples(index=False):
        prediction=rows[(rows.season==period.season)&(rows['round']==period.round)].copy()
        training=select_training_rows(rows,period.forecast_at,horizon,window_days)
        yield {'season':period.season,'round':period.round,'forecast_at':period.forecast_at,'training_rows':training,'prediction_rows':prediction}
