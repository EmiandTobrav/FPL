"""Run new policies in the existing stateful season simulator; isolate all outputs."""
from pathlib import Path
import sys,pickle,json,hashlib,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import pandas as pd
import numpy as np
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent
sys.path.insert(0,str(CURRENT))
import experiment
from upside.models import CANDIDATES,candidate_scores
OUT=HERE/'results'

def games_for(season):
    with open(CURRENT/f'results/games_{season}.pkl','rb') as f:games=pickle.load(f)
    preds=pd.read_csv(OUT/f'predictions_{season}.csv.gz')
    for gw in range(5,39):
        g=games[gw];p=preds[preds.gw==gw]
        assert np.array_equal(p.pid.to_numpy(),g['frame'].pid.to_numpy())
        assert (pd.to_datetime(p.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
        assert np.max(np.abs(p.control.to_numpy()-g['pred']['hgb']))<1e-7
        ref=experiment.xp_for(g,'mix_ridge_extra_50')
        g['pred'].update(candidate_scores(ref,p['tail'].to_numpy(),p.weighted.to_numpy()))
        g['n_history']=p.n_history.to_numpy()
    return games

def fingerprint():
    paths=[HERE/'protocol.json',HERE/'models.py',HERE/'features.py',HERE/'build.py',HERE/'run.py',CURRENT/'experiment.py']
    paths+=list((CURRENT/'project/tuning_v3').glob('*.py'))
    paths+=list((CURRENT/'project/tuning_v3').glob('inputs_*.pkl'))
    paths+=list((CURRENT/'results').glob('games_*.pkl'))
    paths+=list(OUT.glob('predictions_*.csv.gz'))
    return {str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def worker(task):
    return experiment.run(task,games=games_for(task[0]),trace_dir=OUT)

def main():
    manifest=fingerprint();path=OUT/'run_manifest.json'
    if path.exists():
        assert json.loads(path.read_text())==manifest,'Changed code/input: use a new experiment output directory, not stale traces.'
    else:
        assert not list(OUT.glob('trace_*.json.gz')),'Unversioned traces must not be reused'
        path.write_text(json.dumps(manifest,indent=2))
    tasks=[(s,m,r) for s in experiment.SEASONS for m in CANDIDATES for r in ['no_chips','fixed_chips']]
    rows=[];t=time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        futures=[ex.submit(worker,t) for t in tasks]
        for i,f in enumerate(as_completed(futures),1):
            rows.append(f.result())
            pd.DataFrame(rows).to_csv(OUT/'new_season_results.csv',index=False)
            print('DONE',i,len(tasks),'seconds',round(time.time()-t),flush=True)
if __name__=='__main__':main()
