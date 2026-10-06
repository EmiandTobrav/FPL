from pathlib import Path
import sys,json,hashlib,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from global_horizon import run as engine
OUT=HERE/'results';SEASONS=engine.SEASONS;MODELS=['constant','pos_weight','pos_hgb','hybrid_hgb']

def fingerprint():
    paths=list(HERE.glob('*.py'))+[HERE/'protocol.json',CURRENT/'benchmark.json',CURRENT/'global_horizon/run.py',CURRENT/'decision_specialist/planner.py',CURRENT/'decision_specialist/models.py',CURRENT/'experiment.py',CURRENT/'project/season_simulator.py',OUT/'coefficients.json']
    for folder in ['adaptive_events','upside','project/tuning_v3']:
        paths+=list((CURRENT/folder).glob('*.py'))
    paths+=list(OUT.glob('horizon_*.csv.gz'))+list((CURRENT/'results').glob('games_*.pkl'))
    return {str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def worker(task):
    engine.OUT=OUT
    return engine.run(task)

def main():
    manifest=OUT/'run_manifest.json';sig=fingerprint()
    if manifest.exists():assert json.loads(manifest.read_text())==sig,'Changed code or inputs'
    else:
        assert not list(OUT.glob('trace_*.json.gz'));manifest.write_text(json.dumps(sig,indent=2))
    tasks=[(s,m,3,mode) for s in SEASONS for m in MODELS for mode in ['fixed_chips','no_chips']];rows=[];t=time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        futures=[ex.submit(worker,task) for task in tasks]
        for i,f in enumerate(as_completed(futures),1):
            rows.append(f.result());pd.DataFrame(rows).to_csv(OUT/'season_results.csv',index=False)
            print('DONE',i,len(tasks),rows[-1],'seconds',round(time.time()-t),flush=True)
if __name__=='__main__':main()
