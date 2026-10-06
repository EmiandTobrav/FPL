from pathlib import Path
import sys,json,gzip,pickle,hashlib,copy,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
import experiment
from decision_specialist.planner import choose
OUT=HERE/'results';MODELS=['constant'];SEASONS=experiment.SEASONS[2:]

def forecasts_for(s):
    return pd.read_csv(OUT/f'horizon_{s}.csv.gz')

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
        xp=pred[[f'{model}_{j}' for j in range(3)]].to_numpy()
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

def fingerprint():
    paths=[p for p in HERE.glob('*.py') if p.name not in ['summarize.py','verify.py']]+[HERE/'protocol.json',CURRENT/'experiment.py',CURRENT/'project/season_simulator.py']
    paths+=[CURRENT/'decision_specialist/planner.py',CURRENT/'decision_specialist/models.py',CURRENT/'decision_specialist/run_horizon.py']
    paths+=list((CURRENT/'decision_specialist/results').glob('gate_20*.csv.gz'))+[CURRENT/'decision_specialist/results/gate_coefficients.json']
    paths+=list((CURRENT/'upside').glob('*.py'))+list((CURRENT/'project/tuning_v3').glob('*.py'))
    paths+=list((CURRENT/'project/tuning_v3').glob('inputs_*.pkl'))+list((CURRENT/'results').glob('games_*.pkl'))+list(OUT.glob('horizon_*.csv.gz'))
    return {str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def main():
    manifest=OUT/'horizon_manifest.json';sig=fingerprint()
    if manifest.exists():assert json.loads(manifest.read_text())==sig,'Changed inputs/code; do not reuse traces'
    else:
        assert not list(OUT.glob('trace_*_h[13]_*.json.gz'));manifest.write_text(json.dumps(sig,indent=2))
    tasks=[(s,m,h,r) for s in SEASONS for m in MODELS for h in [1,3] for r in ['no_chips','fixed_chips']];rows=[];t=time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        futures=[ex.submit(run,task) for task in tasks]
        for i,f in enumerate(as_completed(futures),1):
            try:result=f.result()
            except Exception:
                import traceback
                traceback.print_exc()
                for pending in futures:pending.cancel()
                raise
            rows.append(result);pd.DataFrame(rows).to_csv(OUT/'horizon_seasons.csv',index=False)
            print('DONE',i,len(tasks),result,'seconds',round(time.time()-t),flush=True)
if __name__=='__main__':main()
