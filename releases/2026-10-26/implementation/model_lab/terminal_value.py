"""Stage B: current-origin terminal state value; no outcomes or file access."""
import copy
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
from . import manager_policy as base

FEATURES = ['discounted_remaining', 'second_half', 'squad_xp_remaining',
            'bench_xp_remaining', 'bank_remaining', 'free_remaining'] + ['chip_'+c for c in base.CHIPS]


def features(pool, values, state, end):
    if not 1 <= end <= 38: raise ValueError('Invalid terminal round')
    remaining = sum(.9**j for j in range(38-end))
    values = dict(zip(map(int, pool.pid), map(float, values)))
    squad = list(state['owned'])
    row = base.lineup(squad, pool, values)
    xi = sum(values[i] for i in row['starters']) + values[row['captain']]
    bench = sum(values[i] for i in row['bench'])
    half = '1' if end < 19 else '2'
    expiry = 19 if end < 19 else 38
    chip_time = sum(.9**j for j in range(expiry-end)) / 10
    # End GW19: first-half chips expire; second-half inventory is separate.
    chips = [float(c not in state['used_chips'][half])*chip_time for c in base.CHIPS]
    x = [remaining/10, float(end>=19)*remaining/10, xi*remaining/100,
         bench*remaining/100, state['bank']*remaining/10000, state['ft']*remaining/50, *chips]
    if not np.isfinite(x).all(): raise ValueError('Invalid terminal features')
    return x


def fit(samples, cutoff):
    import pandas as pd
    if any(pd.Timestamp(s['label_available_at']) >= pd.Timestamp(cutoff) for s in samples):
        raise ValueError('Future training label')
    x=np.array([s['features'] for s in samples]); y=np.array([s['target'] for s in samples])
    scaler=StandardScaler().fit(x); reg=Ridge(alpha=50.).fit(scaler.transform(x), y)
    # Time-only comparator diagnoses whether state information adds value.
    time_scaler=StandardScaler().fit(x[:,:2]); time_reg=Ridge(alpha=50.).fit(time_scaler.transform(x[:,:2]), y)
    return dict(features=FEATURES, mean=scaler.mean_.tolist(), scale=scaler.scale_.tolist(),
        coef=reg.coef_.tolist(), intercept=float(reg.intercept_), cutoff=cutoff, alpha=50.,
        rows=len(samples), training_seasons=sorted({s['season'] for s in samples}),
        latest_label_available_at=max(s['label_available_at'] for s in samples),
        time_only=dict(mean=time_scaler.mean_.tolist(),scale=time_scaler.scale_.tolist(),
                       coef=time_reg.coef_.tolist(),intercept=float(time_reg.intercept_)))


def predict(model, x, end):
    if end == 38: return 0.
    if model['features'] != FEATURES: raise ValueError('Schema mismatch')
    result=float((np.array(x)-model['mean'])/model['scale'] @ np.array(model['coef']) + model['intercept'])
    if not np.isfinite(result): raise ValueError('Nonfinite terminal value')
    return result


def attach(result, model, pool, xp, state_decoder):
    result=copy.deepcopy(result)
    result['zero_terminal_selected_index']=result['selected_index']
    for branch in result['branches']:
        step=branch['steps'][-1]; end=step['gw']; offset=len(branch['steps'])-1
        x=features(pool,xp[:,offset],state_decoder(step['selected']['after']),end)
        v=predict(model,x,end)
        branch.update(terminal_features=x,terminal_value=v,truncated_score=branch['score'])
        branch['score'] += .9**len(branch['steps'])*v
    best=max(result['branches'],key=lambda b:(b['score'],b['root_index']==result['control_index'],result['options'][b['root_index']]['id']))
    result['selected_index']=best['root_index']; result['selected']=result['options'][best['root_index']]
    return result
