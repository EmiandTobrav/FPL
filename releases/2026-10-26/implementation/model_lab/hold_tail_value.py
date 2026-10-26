"""Untrained H4-H8 retained-squad terminal evaluator. Current origin only."""
import copy
import numpy as np
from . import manager_policy as base


def tail(pool,xp,state,gw,steps):
    xp=np.asarray(xp,float)
    if xp.ndim!=2 or xp.shape[0]!=len(pool) or not np.isfinite(xp).all():raise ValueError('Invalid frozen forecasts')
    if steps!=min(3,xp.shape[1],39-gw):raise ValueError('Unexpected horizon')
    rows=[];total=0.
    for offset in range(steps,min(8,xp.shape[1],39-gw)):
        values=dict(zip(map(int,pool.pid),map(float,xp[:,offset])))
        row=base.lineup(list(state['owned']),pool,values)
        points=sum(values[i] for i in row['starters'])+values[row['captain']]
        discount=.9**(offset-steps)
        rows.append(dict(gw=gw+offset,forecast_column=offset,lineup=row,xp=float(points),discount=discount))
        total+=discount*points
    return float(total),rows


def attach(result,pool,xp,state_decoder,gw):
    result=copy.deepcopy(result);result['zero_terminal_selected_index']=result['selected_index']
    for branch in result['branches']:
        steps=len(branch['steps']);after=state_decoder(branch['steps'][-1]['selected']['after'])
        # Forced all-blank origins have one action and no lookahead intervention.
        value,rows=(0.,[]) if result.get('official_blank') else tail(pool,xp,after,gw,steps)
        branch.update(truncated_score=branch['score'],terminal_value=value,tail_rows=rows)
        branch['score']+=.9**steps*value
    best=max(result['branches'],key=lambda b:(b['score'],b['root_index']==result['control_index'],result['options'][b['root_index']]['id']))
    result['selected_index']=best['root_index'];result['selected']=result['options'][best['root_index']]
    return result
