from pathlib import Path
import sys
import numpy as np,pandas as pd
CURRENT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(CURRENT))
from upside.features import COLS,STATS,design,load_history
EXTRA=['minutes_m3','played_m3','long_play_m3','minutes_trend','rest_days','expected_goals_m6','expected_assists_m6','team_ga','opp_gf','saves_m6','bonus_m6']
RICH=COLS+EXTRA

def training_design(d):
    x=design(d);x['minutes_trend']=x.minutes_m3-x.minutes_m12
    return x

def minute_category(minutes):return np.where(np.asarray(minutes)<=0,0,np.where(np.asarray(minutes)<60,1,2))

def residual_target(d):
    appearance=(d.minutes>0).astype(int)+(d.minutes>=60).astype(int)
    return d.historic-appearance-d.goals_scored*d.pos.map({1:6,2:6,3:5,4:4})-3*d.assists-d.clean_sheets*d.pos.map({1:4,2:4,3:1,4:0})

def recent_weights(available,cutoff):
    age=(pd.Timestamp(cutoff)-pd.to_datetime(available,utc=True)).dt.total_seconds()/86400
    assert (age>0).all()
    return np.exp2(-age.to_numpy()/365.)

def prediction_rows(d,fixtures,th,game,season,gw):
    cut=pd.Timestamp(game['cutoff']);past=d[d.available<cut].sort_values('available')
    p=game['frame'].set_index('pid').copy();p['last_price']=p.market/10
    p['n_history']=past.groupby('pid').size().reindex(p.index).fillna(0)
    stats=STATS+['expected_goals','expected_assists','saves','bonus']
    for w in [3,6,12,38]:
        means=past.groupby('pid').tail(w).groupby('pid')[stats].mean()
        for c in stats:p[f'{c}_m{w}']=means[c].reindex(p.index)
    last=past.groupby('pid').available.max().reindex(p.index)
    p['rest_days']=(cut-last).dt.total_seconds()/86400
    p['minutes_trend']=p.minutes_m3-p.minutes_m12
    team=th[th.time<cut].sort_values('time').drop_duplicates('club',keep='last').set_index('club')
    for c in ['gf','ga']:p['team_'+c]=p.club.map(team[c]).fillna(1.35)
    p['elo']=p.club.map(team.elo).fillna(1500)
    batches=[];positions={pid:i for i,pid in enumerate(p.index)}
    for r in fixtures[(fixtures.season==season)&(fixtures.event==gw)].itertuples():
        for club,opp,home in [(r.home,r.away,1),(r.away,r.home,0)]:
            x=p[p.club==club].copy()
            if x.empty:continue
            x['home']=home;x['elo_diff']=x.elo-(team.loc[opp,'elo'] if opp in team.index else 1500)
            for c in ['gf','ga']:x['opp_'+c]=team.loc[opp,c] if opp in team.index else 1.35
            x['_row']=[positions[i] for i in x.index];batches.append(x)
    return (design(pd.concat(batches)) if batches else pd.DataFrame()),p
