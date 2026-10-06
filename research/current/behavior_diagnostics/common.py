from pathlib import Path
import sys,json,gzip,copy
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
import experiment
from retrained_ensemble.run import games_for as load_games
OUT=HERE/'results';REF='mix_ridge_extra_50';SEASONS=experiment.SEASONS
MODELS=[REF,'ridge','extra','ridge_refresh','extra_refresh','re_refresh','rich_refresh','three_refresh','three_frozen']
PRED_MODELS=MODELS+['hgb','hgb_refresh','rich_frozen']
COMPARISONS=json.loads((HERE/'protocol.json').read_text())['comparisons']

def games_for(s):
    games=load_games(s);pred=pd.read_csv(CURRENT/f'adaptive_events/results/predictions_{s}.csv.gz')
    for gw in range(5,39):
        rows=pred[pred.gw==gw];g=games[gw];assert np.array_equal(rows.pid,g['frame'].pid)
        for name in ['hgb_refresh','rich_frozen']:g['pred'][name]=rows[name].to_numpy()
    return games

def trace(s,m,mode):
    root=CURRENT/'results'
    if m=='rich_refresh':root=CURRENT/'adaptive_events/results'
    elif m in ['ridge_refresh','extra_refresh','re_refresh','three_refresh','three_frozen']:root=CURRENT/'retrained_ensemble/results'
    return json.loads(gzip.decompress((root/f'trace_{s}_{m}_{mode}.json.gz').read_bytes()))

def states_before(obj):
    state=copy.deepcopy(obj['handoff']);state['owned']={int(k):int(v) for k,v in state['owned'].items()};out={}
    for row in obj['trace']:
        out[row['gw']]=copy.deepcopy(state)
        state=dict(owned={int(k):int(v) for k,v in row['purchase_prices'].items()},bank=row['bank'],ft=row['ft'])
    return out

def components(row,game):
    pos=dict(zip(game['frame'].pid,game['frame'].pos))
    r=experiment.settle(row['starters'],row['bench'],row['captain'],row['vice'],pos,game['actual'],game['active'],None)
    extra=row['gross']-r['gross'];chip=row['chip']
    assert chip in ['bench_boost','triple_captain'] or extra==0
    out=dict(xi=r['gross']-r['captain_bonus'],captain=r['captain_bonus'],tc=extra if chip=='triple_captain' else 0,bb=extra if chip=='bench_boost' else 0,hits=-row['hits'])
    assert sum(out.values())==row['net']
    return out

def summarize_pairs(frame,keys,metrics):
    rows=[]
    for a,b in COMPARISONS:
        z=frame[frame.model==a].merge(frame[frame.model==b],on=keys,suffixes=('_a','_b'),validate='one_to_one')
        for metric in metrics:
            q=z[keys].copy();q['comparison']=a+' - '+b;q['metric']=metric;q['difference']=z[metric+'_a']-z[metric+'_b'];rows.append(q)
    return pd.concat(rows,ignore_index=True)
