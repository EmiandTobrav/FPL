"""As-of player history split by actual season, for training and inference.

No fit, automatic weighting or point prediction is performed here. Supply a
qualified history view; real zero appearances remain observations. Older
seasons never pad current-season windows. Missing history stays NaN.
"""
import numpy as np
import pandas as pd

STATS = ('minutes', 'points', 'played', 'sixty', 'goals', 'assists', 'clean', 'saves')
WINDOWS = (3, 6, 12, 38)
KEY = ['season', 'round', 'code']

def make_features(origins, history):
    required = {'season', 'fixture', 'code', 'available', *STATS}
    if not required.issubset(history.columns):
        raise ValueError('Qualified native history schema required')
    if not {*KEY, 'forecast_at'}.issubset(origins.columns):
        raise ValueError('Origin keys and timezone-aware forecast time required')
    if history.duplicated(['season', 'fixture', 'code']).any() or origins.duplicated(KEY).any():
        raise ValueError('Duplicate history or origin keys')
    h = history.copy()
    h['available'] = pd.to_datetime(h.available, utc=True, format='mixed')
    if h.available.isna().any():
        raise ValueError('Unknown history availability')
    histories = {code: g.sort_values(['available', 'fixture']) for code, g in h.groupby('code', sort=False)}
    rows = []
    for r in origins.itertuples(index=False):
        at = pd.Timestamp(r.forecast_at)
        if at.tzinfo is None:
            raise ValueError('Timezone required')
        g = histories.get(r.code, h.iloc[:0])
        g = g[g.available.lt(at)]
        current = g[g.season.eq(r.season)]
        older = g[g.season.lt(r.season)]
        old_season = older.season.max() if len(older) else None
        previous = older[older.season.eq(old_season)] if old_season else older
        row = dict(season=r.season, round=r.round, code=r.code,
                   forecast_at=at, prior_season=old_season,
                   prior_season_gap=(int(r.season[:4])-int(old_season[:4])) if old_season else np.nan)
        for prefix, data in [('current', current), ('prior', previous)]:
            row[f'{prefix}_count'] = len(data)
            row[f'{prefix}_missing'] = not len(data)
            row[f'{prefix}_latest_available'] = data.available.max() if len(data) else pd.NaT
            row[f'{prefix}_age_days'] = (at-data.available.max()).total_seconds()/86400 if len(data) else np.nan
            for window in WINDOWS:
                sample = data.tail(window)
                row[f'{prefix}_count_{window}'] = len(sample)
                for stat in STATS:
                    values = pd.to_numeric(sample[stat], errors='coerce')
                    row[f'{prefix}_{stat}_m{window}'] = values.mean()
                    row[f'{prefix}_{stat}_known_{window}'] = int(values.notna().sum())
        rows.append(row)
    return pd.DataFrame(rows)
