"""Rebuild the current baseline's exact pre-deadline fixture feature rows.
Training is on older seasons; selection uses the frozen eligible universe, including
non-playing players. No outcome-based candidate pruning is performed.
"""
from pathlib import Path
import sys
import pandas as pd
import numpy as np
CURRENT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(CURRENT/'project'))
sys.path.insert(0,str(CURRENT/'project/tuning_v3'))
import research
from build_inputs import design,BASE,FX,STATS
COLS=BASE+FX

def load_history():
    d,fixtures=research.load_data()
    cache=CURRENT/'project/results/features.pkl'
    if cache.exists():d=pd.read_pickle(cache)
    else:d,_=research.features(d,fixtures)
    states={};rows=[]
    for r in fixtures.sort_values('available').itertuples():
        if pd.isna(r.team_h_score):continue
        for k in [r.home,r.away]:states.setdefault(k,dict(elo=1500.,gf=1.35,ga=1.35))
        h,a=states[r.home],states[r.away]
        delta=20*(float(r.team_h_score>r.team_a_score)+.5*float(r.team_h_score==r.team_a_score)-1/(1+10**((a['elo']-h['elo']-60)/400)))
        h['elo']+=delta;a['elo']-=delta
        for k,gf,ga in [(r.home,r.team_h_score,r.team_a_score),(r.away,r.team_a_score,r.team_h_score)]:
            states[k]['gf']=.85*states[k]['gf']+.15*gf
            states[k]['ga']=.85*states[k]['ga']+.15*ga
            rows.append(dict(club=k,time=r.available,**states[k]))
    return d,fixtures,pd.DataFrame(rows)

def prediction_rows(d,fixtures,th,game,season,gw):
    cut=pd.Timestamp(game['cutoff']);past=d[d.available<cut]
    p=game['frame'].set_index('pid').copy()
    p['last_price']=p.market/10
    p['n_history']=past.groupby('pid').size().reindex(p.index).fillna(0)
    for w in [6,12,38]:
        means=past.sort_values('available').groupby('pid').tail(w).groupby('pid')[STATS].mean()
        for c in STATS:p[f'{c}_m{w}']=means[c].reindex(p.index)
    team=th[th.time<cut].sort_values('time').drop_duplicates('club',keep='last').set_index('club')
    for c in ['gf','ga']:p['team_'+c]=p.club.map(team[c]).fillna(1.35)
    p['elo']=p.club.map(team.elo).fillna(1500)
    batch=[];positions={pid:i for i,pid in enumerate(p.index)}
    for r in fixtures[(fixtures.season==season)&(fixtures.event==gw)].itertuples():
        for club,opp,home in [(r.home,r.away,1),(r.away,r.home,0)]:
            x=p[p.club==club].copy()
            if x.empty:continue
            x['home']=home;x['elo_diff']=x.elo-(team.loc[opp,'elo'] if opp in team.index else 1500)
            for c in ['gf','ga']:x['opp_'+c]=team.loc[opp,c] if opp in team.index else 1.35
            x['_row']=[positions[i] for i in x.index];batch.append(x)
    return (design(pd.concat(batch)) if batch else pd.DataFrame()),p
