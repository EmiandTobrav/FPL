"""Origin-bound forward calendar and takeover inputs. No prediction or outcome lookup."""
import copy
import pandas as pd
import numpy as np

def forward_calendar(pool, fixtures, horizon=8):
    """One origin only. Never advance history using later-origin player rows.

    Unassigned matches make an apparent blank unknown. Counts describe the
    origin's schedule, not a guarantee that a fixture will actually be played.
    """
    required={'season','round','code','club_code','forecast_at'}
    if not required <= set(pool): raise ValueError('Missing origin metadata')
    if not 1<=horizon<=8: raise ValueError('Unsupported horizon')
    if pool.empty or pool.code.duplicated().any(): raise ValueError('Empty/duplicate player pool')
    origins=pool[['season','round','forecast_at']].drop_duplicates()
    if len(origins)!=1: raise ValueError('Mixed origins')
    origin=origins.iloc[0];at=pd.Timestamp(origin.forecast_at)
    if at.tzinfo is None: raise ValueError('Timezone required')
    if fixtures.empty: raise ValueError('No qualified calendar supplied')
    for key in ['source_time','event_evidence_at']:
        if key not in fixtures:
            if key=='source_time': raise ValueError('Missing calendar timestamp')
            continue
        times=pd.to_datetime(fixtures[key],utc=True)
        if times.isna().any() or not times.lt(at).all(): raise ValueError('Unknown/future calendar evidence')
    if fixtures.fixture_id.duplicated().any(): raise ValueError('Duplicate fixture identity')
    if 'round' in fixtures and not fixtures['round'].eq(int(origin['round'])).all(): raise ValueError('Later-origin calendar')
    if 'season' in fixtures and not fixtures.season.eq(origin.season).all(): raise ValueError('Wrong calendar season')
    frames=[]
    known_clubs=set(fixtures.home_code)|set(fixtures.away_code)
    for offset in range(min(horizon,39-int(origin['round']))):
        target=int(origin['round'])+offset;rows=[]
        for p in pool.itertuples():
            games=fixtures[fixtures.home_code.eq(p.club_code)|fixtures.away_code.eq(p.club_code)]
            selected=games[games.event.eq(target)]
            unassigned=int(games.event.isna().sum())
            known=p.club_code in known_clubs and unassigned==0
            rows.append(dict(season=p.season,origin_round=int(origin['round']),target_round=target,offset=offset,
                code=int(p.code),club_code=p.club_code,forecast_at=at,
                calendar_known=bool(known),planned_count=len(selected) if known else np.nan,
                planned_home=int(selected.home_code.eq(p.club_code).sum()) if known else np.nan,
                planned_away=int(selected.away_code.eq(p.club_code).sum()) if known else np.nan,
                unassigned=unassigned,source_time=pd.to_datetime(games.source_time,utc=True).max() if len(games) else pd.NaT,
                opponents=','.join(str(int(r.away_code if r.home_code==p.club_code else r.home_code)) for r in selected.itertuples())))
        frames.append(pd.DataFrame(rows))
    return pd.concat(frames,ignore_index=True)

def attach_targets(origin_rows, labels):
    """Separate training table. Unknown outcomes stay missing, including blanks."""
    keys=['season','target_round','code']
    lab=labels.rename(columns={'round':'target_round','target_h1_available_at':'label_available_at'})
    if lab.duplicated(keys).any(): raise ValueError('Duplicate labels')
    return origin_rows.merge(lab[keys+['target_total_points','label_available_at']],on=keys,how='left',validate='many_to_one')

def causal_training(rows, cutoff):
    cutoff=pd.Timestamp(cutoff)
    if cutoff.tzinfo is None: raise ValueError('Timezone required')
    origin=pd.to_datetime(rows.forecast_at,utc=True);label=pd.to_datetime(rows.label_available_at,utc=True)
    good=origin.lt(cutoff)&label.lt(cutoff)&rows.target_total_points.notna()
    return rows.loc[good].copy()

def copy_takeover_state(state, gw):
    result=copy.deepcopy(state)
    result['owned']={int(k):v for k,v in result['owned'].items()}
    result['ownership_clubs']={int(k):v for k,v in result.get('ownership_clubs',{}).items()}
    if result['next_gw']!=gw or len(result['owned'])!=15: raise ValueError('Invalid takeover state')
    if result['bank']<0 or not 0<=result['ft']<=5: raise ValueError('Invalid finance')
    if set(result['used_chips'])!={'1','2'}: raise ValueError('Missing chip history')
    return result
