from pathlib import Path
import sys,pickle,json,hashlib,traceback,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
import experiment
from retrained_ensemble.models import NEW,CANDIDATES,combine
OUT=HERE/'results';SEASONS=experiment.SEASONS;REF='mix_ridge_extra_50'

def games_for(s):
    with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
    pred=pd.read_csv(OUT/f'predictions_{s}.csv.gz');rich=pd.read_csv(CURRENT/f'adaptive_events/results/predictions_{s}.csv.gz')
    for gw in range(5,39):
        g=games[gw];p=pred[pred.gw==gw];h=rich[rich.gw==gw]
        assert np.array_equal(p.pid,g['frame'].pid) and np.array_equal(h.pid,p.pid)
        for frame in [p,h]:assert (pd.to_datetime(frame.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
        for name in ['ridge','extra']:assert np.max(np.abs(p[name+'_control'].to_numpy()-g['pred'][name]))<1e-5
        g['pred'].update(combine(p.ridge_refresh.to_numpy(),p.extra_refresh.to_numpy(),h.rich_refresh.to_numpy(),g['pred']['ridge'],g['pred']['extra'],h.rich_frozen.to_numpy()))
        g['pred']['rich_refresh']=h.rich_refresh.to_numpy()
        g['n_history']=h.n_history.to_numpy()
    return games

def fingerprint():
    paths=[p for p in HERE.glob('*.py') if p.name!='summarize.py']+[HERE/'protocol.json',CURRENT/'experiment.py',CURRENT/'project/season_simulator.py']
    paths+=list((CURRENT/'upside').glob('*.py'))+list((CURRENT/'project/tuning_v3').glob('*.py'))
    paths+=list((CURRENT/'project/tuning_v3').glob('inputs_*.pkl'))+list((CURRENT/'results').glob('games_*.pkl'))
    paths+=list(OUT.glob('predictions_*.csv.gz'))+list((CURRENT/'adaptive_events/results').glob('predictions_*.csv.gz'))
    paths+=list((CURRENT/'adaptive_events/results').glob('trace_*_rich_refresh_*.json.gz'))
    return {str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def worker(task):return experiment.run(task,games=games_for(task[0]),trace_dir=OUT)

def main():
    manifest=OUT/'run_manifest.json';sig=fingerprint()
    if manifest.exists():assert json.loads(manifest.read_text())==sig,'Do not reuse stale traces'
    else:
        assert not list(OUT.glob('trace_*.json.gz'));manifest.write_text(json.dumps(sig,indent=2))
    tasks=[(s,m,r) for s in SEASONS for m in NEW for r in ['no_chips','fixed_chips']];rows=[];t=time.time()
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
