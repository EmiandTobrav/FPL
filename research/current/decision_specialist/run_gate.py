from pathlib import Path
import sys,pickle,json,hashlib,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
import experiment
OUT=HERE/'results';SEASONS=experiment.SEASONS[2:]

def games_for(s):
    with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
    pred=pd.read_csv(OUT/f'gate_{s}.csv.gz')
    for gw in range(5,39):
        rows=pred[pred.gw==gw];g=games[gw]
        assert np.array_equal(rows.pid,g['frame'].pid)
        assert (pd.to_datetime(rows.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
        for m in ['gate','constant']:g['pred'][m]=rows[m].to_numpy()
    return games

def fingerprint():
    paths=[HERE/n for n in ['models.py','build.py','run_gate.py','protocol.json']]+[CURRENT/'experiment.py',CURRENT/'project/season_simulator.py',CURRENT/'project/tuning_v3/decision.py']
    paths+=[OUT/f'gate_{s}.csv.gz' for s in SEASONS]+[OUT/'gate_training_audit.csv']+[OUT/'gate_coefficients.json']+list((CURRENT/'results').glob('games_*.pkl'))+list((CURRENT/'project/tuning_v3').glob('inputs_*.pkl'))
    paths+=list((CURRENT/'behavior_diagnostics/results').glob('scenario_inputs_*.csv.gz'))+list((CURRENT/'retrained_ensemble/results').glob('predictions_*.csv.gz'))+list((CURRENT/'adaptive_events/results').glob('predictions_*.csv.gz'))
    return {str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)}

def worker(task):return experiment.run(task,games=games_for(task[0]),trace_dir=OUT)

def main():
    manifest=OUT/'gate_manifest.json';sig=fingerprint()
    if manifest.exists():assert json.loads(manifest.read_text())==sig,'Stale gate inputs/source'
    else:
        assert not list(OUT.glob('trace_*_gate_*.json.gz')) and not list(OUT.glob('trace_*_constant_*.json.gz'));manifest.write_text(json.dumps(sig,indent=2))
    tasks=[(s,m,r) for s in SEASONS for m in ['gate','constant'] for r in ['fixed_chips','no_chips']];rows=[]
    with ProcessPoolExecutor(max_workers=4) as ex:
        for f in as_completed([ex.submit(worker,t) for t in tasks]):rows.append(f.result())
    pd.DataFrame(rows).to_csv(OUT/'gate_seasons.csv',index=False);print('GATE DONE',len(rows))
if __name__=='__main__':main()
