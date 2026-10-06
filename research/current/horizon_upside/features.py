"""Current-deadline forecasts only; never access future game observations."""
import numpy as np
from upside.features import design

def neutral_rows(players,history,cutoff):
    p=players.copy()
    team=history[history.time<cutoff].sort_values('time').drop_duplicates('club',keep='last').set_index('club')
    league=team.reindex(sorted(p.club.unique()))
    p['home']=.5;p['elo_diff']=p.elo-league.elo.fillna(1500).mean()
    p['opp_ga']=league.ga.fillna(1.35).mean()
    return design(p)

def horizon_forecast(current,neutral,count,horizon=4):
    current=np.asarray(current);neutral=np.asarray(neutral);count=np.asarray(count)
    per=np.where(count>0,current/np.maximum(count,1),neutral)
    return np.column_stack([current]+[np.maximum(0,neutral+(per-neutral)*(.5**k)) for k in range(1,horizon)])

def combine(probability,high,low):
    return np.maximum(0,np.asarray(probability)*np.asarray(high)+(1-np.asarray(probability))*np.asarray(low))
