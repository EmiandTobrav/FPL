from pathlib import Path
import sys,json,gzip,pickle,hashlib,copy,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
import experiment
from decision_specialist.planner import choose
OUT=HERE/'results';MODELS=['constant'];SEASONS=experiment.SEASONS[2:]

def forecasts_for(s):
    return pd.read_csv(OUT/f'forecast_{s}.csv.gz')

def horizon_chips(gw,horizon,mode):
    calendar=experiment.CAL if mode=='fixed_chips' else {}
    if calendar.get(gw)=='free_hit':return ['free_hit']
    end=min(39,gw+horizon)
    for future in range(gw+1,end):
        if calendar.get(future) in ['wildcard','free_hit']:end=future;break
    return [calendar.get(w) for w in range(gw,end)]

def run(task):
    s,model,horizon,mode=task;name=f'{model}_h{horizon}';path=OUT/f'trace_{s}_{name}_{mode}.json.gz'
    if path.exists():return json.loads(gzip.decompress(path.read_bytes()))['summary']
    with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
    predictions=forecasts_for(s);state,opening=experiment.opening(s);handoff=copy.deepcopy(state);rows=[]
    for gw in range(5,39):
        g=games[gw];p=g['frame'];pred=predictions[predictions.gw==gw]
        assert np.array_equal(p.pid,pred.pid) and (pd.to_datetime(pred.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
        xp=pred[[f'{model}_{j}' for j in range(8)]].to_numpy()
        chips=horizon_chips(gw,horizon,mode);chip=chips[0]
        c=choose(p,xp[:,:len(chips)],state['owned'],state['bank'],state['ft'],chips)
        pos=dict(zip(p.pid,p.pos));r=experiment.settle(c['starters'],c['bench'],c['captain'],c['vice'],pos,g['actual'],g['active'],chip)
        before=copy.deepcopy(state)
        if chip!='free_hit':state['owned']={i:state['owned'].get(i,c['prices'][i]) for i in c['squad']};state['bank']=c['bank_after']
        else:assert state==before
        state['ft']=experiment.next_free(state['ft'],c['transfers'],chip)
        assert r['gross']==sum(g['actual'].get(i,0) for i in r['counted'])+r['captain_bonus']
        rows.append(dict(gw=gw,net=r['gross']-4*c['paid'],gross=r['gross'],hits=4*c['paid'],chip=chip or '',bank=state['bank'],ft=state['ft'],transfers=c['transfers'],solver_status=c['solver_status'],solver_gap=c['solver_gap'],squad=sorted(c['squad']),starters=c['starters'],bench=c['bench'],captain=c['captain'],vice=c['vice'],incoming=sorted(c['incoming']),outgoing=sorted(c['outgoing']),planned_horizon=c['planned_horizon'],planned_transfers=[x['transfers'] for x in c['plan']],plan=c['plan'],counted=r['counted'],captain_bonus=r['captain_bonus'],contributions={str(i):g['actual'].get(i,0) for i in r['counted']}))
    summary=dict(season=s,model=name,forecast_model=model,horizon=horizon,mode=mode,points38=sum(r['net'] for r in opening)+sum(r['net'] for r in rows),opening_points=sum(r['net'] for r in opening),hits=sum(r['hits'] for r in rows),transfers=sum(r['transfers'] for r in rows),nonoptimal=sum(r['solver_status']!=0 for r in rows),max_solver_gap=max(r['solver_gap'] for r in rows))
    obj=dict(summary=summary,handoff=dict(owned=handoff['owned'],bank=handoff['bank'],ft=handoff['ft']),opening=opening,trace=rows)
    path.write_bytes(gzip.compress(json.dumps(obj,default=lambda x:x.item() if isinstance(x,np.generic) else list(x)).encode(),mtime=0));return summary

def main():
    import argparse
    parser=argparse.ArgumentParser();parser.add_argument('--stage',choices=['h3','long'],default='h3');args=parser.parse_args()
    matrix=[(m,3) for m in ['count','venue','opponent','full']] if args.stage=='h3' else [(m,h) for m in ['count','full'] for h in [5,8]]
    tasks=[(s,m,h,r) for s in SEASONS for m,h in matrix for r in ['fixed_chips','no_chips']]
    paths=[HERE/n for n in ['build.py','features.py','run.py']]+[HERE/'protocol.json',CURRENT/'benchmark.json',CURRENT/'decision_specialist/planner.py',CURRENT/'experiment.py',CURRENT/'project/season_simulator.py']+list(OUT.glob('forecast_*.csv.gz'))
    manifest={str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    path=OUT/f'manifest_{args.stage}.json'
    if path.exists():assert json.loads(path.read_text())==manifest
    else:path.write_text(json.dumps(manifest,indent=2))
    rows=[];start=time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        for i,f in enumerate(as_completed([ex.submit(run,t) for t in tasks]),1):
            rows.append(f.result());pd.DataFrame(rows).to_csv(OUT/f'seasons_{args.stage}.csv',index=False)
            print('DONE',i,len(tasks),rows[-1],'seconds',round(time.time()-start),flush=True)
if __name__=='__main__':main()
