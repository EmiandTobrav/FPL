"""Dispatch only never-started predeclared attempts after a dispatcher error.

No failed/running/completed attempt is resumed or retried. The original
ThreadPoolExecutor.map cancels queued, never-started work when one job fails.
This dispatcher records each return code and allows other independent attempts
to run once, under the unchanged four-process ceiling.
"""
import os,sys,subprocess,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts.common_season_comparison import P,ARMS,CONTROLS,WEATHER,EVAL
from model_lab.common import atomic_json,sha
def main(group='primary'):
    assert group in ['primary','weather'];assert (P/f'{group}_original_dispatcher_stopped.json').exists()
    names=ARMS+CONTROLS if group=='primary' else WEATHER;jobs=[]
    for s in EVAL:
        for a in names:
            folder=P/'manager'/f'{s}_{a}';log=P/'logs'/f'manager_{s}_{a}.log'
            if not folder.exists() and not log.exists():jobs.append((s,a))
    atomic_json(P/f'{group}_unstarted_dispatch.json',dict(jobs=jobs,only_never_started=True,no_retry_or_resume=True,unchanged_four_process_limit=True,source_sha256=sha(Path(__file__))))
    def run(job):
        s,a=job;path=P/'logs'/f'manager_{s}_{a}.log'
        with path.open('x') as f:result=subprocess.run([sys.executable,'scripts/common_season_comparison.py','manager',s,a],cwd=R,env=os.environ.copy(),stdout=f,stderr=subprocess.STDOUT)
        print('ATTEMPT TERMINAL',s,a,'exit',result.returncode,flush=True);return dict(season=s,arm=a,exit_code=result.returncode)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(run,jobs))
    atomic_json(P/f'{group}_unstarted_dispatch_complete.json',dict(results=results,all_attempted_once=True))
if __name__=='__main__':main(*sys.argv[1:])
