from pathlib import Path
import sys,pickle,json,hashlib,traceback,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
import experiment
from adaptive_events.models import MODELS
OUT=HERE/'results';SEASONS=experiment.SEASONS;REF='mix_ridge_extra_50'

def games_for(s):
    with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
    pred=pd.read_csv(OUT/f'predictions_{s}.csv.gz')
    mix=pd.read_csv(CURRENT/f'horizon_upside/results/forecasts_{s}.csv.gz')
    for gw in range(5,39):
        g=games[gw];p=pred[pred.gw==gw];m=mix[mix.gw==gw]
        assert np.array_equal(p.pid,g['frame'].pid) and np.array_equal(m.pid,p.pid)
        assert (pd.to_datetime(p.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
        assert np.max(np.abs(p.control.to_numpy()-g['pred']['hgb']))<1e-7
        assert (p.p_60_sum>=-1e-10).all() and (p.p_60_sum<=p.p_play_sum+1e-10).all()
        assert (p.p_play_sum.to_numpy()<=np.asarray(g['count'])+1e-10).all()
        for name in MODELS[:6]:g['pred'][name]=p[name].to_numpy()
        g['pred']['blend_events_direct']=.5*p.rich_refresh.to_numpy()+.5*p.events_refresh.to_numpy()
        g['pred']['blend_three']=(p.rich_refresh.to_numpy()+p.events_refresh.to_numpy()+m.mixture_0.to_numpy())/3
        g['pred']['blend_reference_mixture']=.5*experiment.xp_for(g,REF)+.5*m.mixture_0.to_numpy()
        g['n_history']=p.n_history.to_numpy()
    return games

def fingerprint():
    paths=[p for p in HERE.glob('*.py') if p.name!='summarize.py']+[HERE/'protocol.json',CURRENT/'experiment.py',CURRENT/'project/season_simulator.py']
    paths+=list((CURRENT/'upside').glob('*.py'))+list((CURRENT/'project/tuning_v3').glob('*.py'))
    paths+=list((CURRENT/'project/tuning_v3').glob('inputs_*.pkl'))+list((CURRENT/'results').glob('games_*.pkl'))
    paths+=list(OUT.glob('predictions_*.csv.gz'))+list((CURRENT/'horizon_upside/results').glob('forecasts_*.csv.gz'))
    return {str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def worker(task):return experiment.run(task,games=games_for(task[0]),trace_dir=OUT)

def main():
    manifest=OUT/'run_manifest.json';sig=fingerprint()
    if manifest.exists():assert json.loads(manifest.read_text())==sig,'Do not reuse stale traces'
    else:
        assert not list(OUT.glob('trace_*.json.gz'));manifest.write_text(json.dumps(sig,indent=2))
    tasks=[(s,m,r) for s in SEASONS for m in MODELS for r in ['no_chips','fixed_chips']];rows=[];t=time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        futures=[ex.submit(worker,task) for task in tasks]
        for i,f in enumerate(as_completed(futures),1):
            try:r=f.result()
            except Exception:
                traceback.print_exc()
                for future in futures:future.cancel()
                raise
            rows.append(r);pd.DataFrame(rows).to_csv(OUT/'new_season_results.csv',index=False)
            print('DONE',i,len(tasks),'seconds',round(time.time()-t),flush=True)
if __name__=='__main__':main()
