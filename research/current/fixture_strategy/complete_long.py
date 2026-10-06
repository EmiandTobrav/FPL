"""Feasibility-only repair after observed 10s incumbent failure, not score tuning.
Keep feasible original traces. Apply the same conditional 60s retry to every
missing count/full H5/H8 run. Never overwrite a completed trace.
"""
from pathlib import Path
import sys,json,time,hashlib,traceback
from concurrent.futures import ProcessPoolExecutor,as_completed
import pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from fixture_strategy import run as engine
from decision_specialist import planner
OUT=HERE/'results'

def worker(task):
    retries=[];original=planner.milp;calls=0
    def guarded(*args,**kwargs):
        nonlocal calls
        calls+=1;r=original(*args,**kwargs)
        if r.x is None and r.status==1:
            options=dict(kwargs.get('options',{}));options['time_limit']=60
            r=original(*args,**dict(kwargs,options=options))
            retries.append(dict(call=calls,retry_seconds=60,status=int(r.status),feasible=r.x is not None,gap=float(r.mip_gap) if r.x is not None else None))
            print('FEASIBILITY_RETRY',task,retries[-1],flush=True)
        return r
    planner.milp=guarded
    try:
        result=engine.run(task)
        return dict(ok=True,task=task,summary=result,retries=retries,calls=calls)
    except Exception:
        return dict(ok=False,task=task,error=traceback.format_exc(),retries=retries,calls=calls)
    finally:planner.milp=original

def main():
    tasks=[(s,m,h,r) for s in engine.SEASONS for m in ['count','full'] for h in [5,8] for r in ['fixed_chips','no_chips']]
    paths=[HERE/'complete_long.py',HERE/'run.py',HERE/'protocol.json',CURRENT/'decision_specialist/planner.py']+list(OUT.glob('forecast_*.csv.gz'))
    manifest=dict(reason='10-second solver returned no incumbent; confirmed in isolated diagnostic. Conditional retry chosen solely for feasibility.',policy='Retain any feasible 10s result, retry at 60s only if status=1 and x=None; all models/horisons use same policy.',sources={str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths})
    p=OUT/'feasibility_policy.json'
    if p.exists():assert json.loads(p.read_text())==manifest
    else:p.write_text(json.dumps(manifest,indent=2))
    audits=[];rows=[];start=time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        for i,f in enumerate(as_completed([ex.submit(worker,t) for t in tasks]),1):
            z=f.result();audits.append(z)
            if z['ok']:rows.append(z['summary'])
            (OUT/'feasibility_runs.json').write_text(json.dumps(audits,indent=2));pd.DataFrame(rows).to_csv(OUT/'seasons_long.csv',index=False)
            print('DONE',i,len(tasks),z['task'],'ok',z['ok'],'retries',len(z['retries']),'seconds',round(time.time()-start),flush=True)
            if not z['ok']:print(z['error'],flush=True)
    assert all(x['ok'] for x in audits),'Some long runs failed; inspect feasibility_runs.json'
if __name__=='__main__':main()
