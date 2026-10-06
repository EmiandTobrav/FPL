from pathlib import Path
import sys,json,hashlib,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from global_horizon import run as engine
OUT=HERE/'results';SEASONS=engine.SEASONS

def fingerprint():
    paths=list(HERE.glob('*.py'))+[HERE/'protocol.json',CURRENT/'benchmark.json',CURRENT/'global_horizon/run.py',CURRENT/'decision_specialist/planner.py',CURRENT/'experiment.py',CURRENT/'project/season_simulator.py',CURRENT/'calendar_audit/source_commits.json',CURRENT/'calendar_audit/selector.py',CURRENT/'calendar_audit/selection.csv',CURRENT/'calendar_audit/snapshot_manifest.json']
    paths+=list((CURRENT/'calendar_audit/snapshots').glob('*.csv.gz'))+list(OUT.glob('horizon_*.csv.gz'))+list((CURRENT/'results').glob('games_*.pkl'))+list((CURRENT/'project/tuning_v3').glob('*.py'))
    return {str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def worker(task):
    engine.OUT=OUT
    return engine.run(task)

def main():
    sig=fingerprint();manifest=OUT/'run_manifest.json'
    if manifest.exists():assert json.loads(manifest.read_text())==sig
    else:
        assert not list(OUT.glob('trace*'));manifest.write_text(json.dumps(sig,indent=2))
    tasks=[(s,m,3,mode) for s in SEASONS for m in ['constant','calendar_count'] for mode in ['fixed_chips','no_chips']];rows=[];start=time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        for i,f in enumerate(as_completed([ex.submit(worker,t) for t in tasks]),1):
            rows.append(f.result());pd.DataFrame(rows).to_csv(OUT/'season_results.csv',index=False);print('DONE',i,len(tasks),rows[-1],'seconds',round(time.time()-start),flush=True)
if __name__=='__main__':main()
