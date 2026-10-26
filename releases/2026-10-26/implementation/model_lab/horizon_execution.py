"""Stage C execution with external process watchdogs and immutable receipts."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[k]='1'
import sys
import json
import time
import signal
import subprocess
import traceback
from pathlib import Path
from .common import ROOT,read,sha,digest,atomic_json,verify_files,runtime
from .simulation import backend
from .manager_learning import Environment,settle
from .horizon_preflight import HERE as DESIGN, inputs_only,protect,stamp
from . import manager_policy as base,horizon_policy as policy

HERE=ROOT/'reports/horizon_c_execution_2026_10_16'
SEASONS=('2023-24','2024-25')

def normalized(v):
    if isinstance(v,list):return [normalized(x) for x in v]
    if isinstance(v,dict):
        return {k:({int(a):normalized(b) for a,b in x.items()} if k in ('owned','ownership_clubs','prices') else normalized(x)) for k,x in v.items()}
    return v

def watch(command,seconds,stdout,stderr,grouped=True):
    """A separate parent process kills the whole child group on timeout."""
    started=time.monotonic()
    with open(stdout,'xb') as out,open(stderr,'xb') as err:
        process=subprocess.Popen(command,stdout=out,stderr=err,start_new_session=grouped,cwd=ROOT)
        def kill():
            if grouped:os.killpg(process.pid,signal.SIGKILL)
            else:process.kill()
        try:code=process.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            kill();process.wait()
            raise TimeoutError(f'External watchdog killed process group after {seconds} seconds')
        except BaseException:
            if process.poll() is None:kill();process.wait()
            raise
    if code:raise RuntimeError(f'Child exit {code}; inspect {stderr}')
    return time.monotonic()-started

def bound(full=True):
    lock=read(HERE/'execution_lock.json');verify_files(ROOT,lock['execution_files'])
    assert sha(DESIGN/'protocol.json')==lock['protocol_sha256']
    assert runtime()==lock['runtime']
    if full:
        reg=read(DESIGN/'registration.json');spec=read(ROOT/reg['proposal'])
        from scripts.research import fingerprint
        assert fingerprint(spec)==reg['fingerprint']
        verify_files(ROOT,spec['input_hashes'])
        assert protect()==lock['protected']
    return lock

def freeze():
    assert read(DESIGN/'preflight.json')['status']=='pass'
    reg=read(DESIGN/'registration.json');spec=read(ROOT/reg['proposal'])
    verify_files(ROOT,spec['input_hashes'])
    tests=read(HERE/'watchdog_tests.json');assert tests['status']=='pass'
    files=[ROOT/'model_lab/horizon_execution.py',ROOT/'model_lab/horizon_execution_audit.py',
           ROOT/'model_lab/tests/test_horizon_execution.py',HERE/'watchdog_tests.json']
    atomic_json(HERE/'execution_lock.json',dict(at_utc=stamp(),protocol_sha256=sha(DESIGN/'protocol.json'),
        registration_sha256=sha(DESIGN/'registration.json'),runtime=runtime(),protected=protect(),
        execution_files={str(p.relative_to(ROOT)):sha(p) for p in files},
        order=[dict(season=s,horizon=h) for s in SEASONS for h in (3,8)],
        external_watchdogs=dict(decision_seconds=120,entire_execution_and_audit_seconds=21600),
        no_resume=True,no_retry=True,full_seasons=4,decisions=152,prospective_rows_allowed=0,
        resources=read(DESIGN/'protocol.json')['resources'],
        authority='User explicitly requests binding execution and running all four locked episodes.',
        decision_boundary='Isolated decision subprocess receives only season/round/state and current-origin inputs; settlement occurs in controller after immutable decision receipt.',
        audit='Separate source recomputes all option legality, score formulas, branch choices, state transitions and settlement.'))
    print('Execution lock created',flush=True)

def worker(request):
    bound(False);req=read(request);s,g,h=req['season'],req['gw'],req['horizon']
    assert s in SEASONS and 1<=g<=38 and h in (3,8)
    folder=Path(request).parent;state=normalized(req['state']);env=inputs_only()
    p,x,m,hist=env.inputs(s,g);assert x.shape[1]>=min(8,39-g)
    mod,ad=backend(16,200);counts=[]
    eventfile=folder/f'gw{g:02d}.solver.jsonl'
    def event(row):
        with eventfile.open('a') as f:f.write(json.dumps(row,allow_nan=False)+'\n');f.flush()
    ad.event_sink=event
    def limited(*args,**kwargs):
        before=len(ad.ledger);options=base.proposals(*args,**kwargs);n=len(ad.ledger)-before
        if n>40:raise ValueError('Per-proposal cap exceeded')
        counts.append(n);return options
    started=time.monotonic()
    try:
        result=policy.choose(ad,p,x,hist,state,g,horizon=h,official_blank=bool(m.get('official_all_blank_forced_wait')),proposals=limited)
        assert len(ad.ledger)<=200 and sum(counts)==len(ad.ledger)
        receipt=mod.clean(dict(**result,season=s,gw=g,requested_horizon=h,state_before=state,
            forecast_at=m['forecast_at'],forecast_array_sha256=digest(x.tolist()),
            solver_calls=ad.ledger,proposal_call_counts=counts,outcomes_read=False,
            execution_lock_sha256=sha(HERE/'execution_lock.json'),decision_seconds=time.monotonic()-started))
        atomic_json(folder/f'gw{g:02d}.decision.json',receipt)
    except BaseException as exc:
        atomic_json(folder/f'gw{g:02d}.failure.json',dict(error=str(exc),traceback=traceback.format_exc(),solver_calls=ad.ledger))
        raise

def execute():
    bound();env=None;_,ad=backend(16,200);total_calls=0;total_nodes=0;completed=0
    try:
        for season in SEASONS:
            for horizon in (3,8):
                folder=HERE/'runs'/f'{season}_h{horizon}';folder.mkdir(parents=True,exist_ok=False)
                state=ad.engine.initial_state();points=0.;seconds=0.;calls=0
                for gw in range(1,39):
                    request=folder/f'gw{gw:02d}.request.json'
                    atomic_json(request,dict(season=season,gw=gw,horizon=horizon,state=state))
                    elapsed=watch([sys.executable,'-B','-m','model_lab.horizon_execution','worker',str(request)],120,
                        folder/f'gw{gw:02d}.stdout.txt',folder/f'gw{gw:02d}.stderr.txt',grouped=False)
                    decision=read(folder/f'gw{gw:02d}.decision.json');assert not decision['outcomes_read']
                    atomic_json(folder/f'gw{gw:02d}.watchdog.json',dict(seconds=elapsed,timeout=False,decision_sha256=sha(folder/f'gw{gw:02d}.decision.json')))
                    total_calls+=len(decision['solver_calls']);total_nodes+=sum(r['nodes'] for r in decision['solver_calls'])
                    assert total_calls<=30400 and total_nodes<=486400
                    # Outcome bank exists only in this controller, after the first decision is saved.
                    if env is None:env=Environment()
                    pool,_,_,_=env.inputs(season,gw)
                    selected=normalized(decision['selected']);outcome,result,net=settle(ad,env,season,gw,selected,pool)
                    atomic_json(folder/f'gw{gw:02d}.settled.json',dict(outcomes=outcome,settlement=env.helpers.clean(result),
                        net_points=net,decision_sha256=sha(folder/f'gw{gw:02d}.decision.json'),outcomes_read=True))
                    points+=net;seconds+=elapsed;calls+=len(decision['solver_calls']);state=selected['after'];completed+=1
                    atomic_json(HERE/'progress'/f'{completed:03d}.json',dict(season=season,gw=gw,horizon=horizon,completed_decisions=completed))
                    print(f'{season} H{horizon} GW{gw:02d} completed ({completed}/152)',flush=True)
                atomic_json(folder/'summary.json',dict(season=season,horizon=horizon,rounds=38,net_points=points,watchdog_seconds=seconds,calls=calls))
        bound();atomic_json(HERE/'execution_complete.json',dict(at_utc=stamp(),decisions=completed,solver_calls=total_calls,nodes=total_nodes))
        from .horizon_execution_audit import audit
        audit()
    except BaseException as exc:
        atomic_json(HERE/'execution_failure.json',dict(at_utc=stamp(),error=str(exc),traceback=traceback.format_exc(),completed_decisions=completed,solver_calls=total_calls,nodes=total_nodes))
        raise

def run():
    bound();atomic_json(HERE/'started.json',dict(at_utc=stamp(),execution_lock_sha256=sha(HERE/'execution_lock.json')))
    try:
        elapsed=watch([sys.executable,'-B','-m','model_lab.horizon_execution','execute'],21600,HERE/'execution.stdout.txt',HERE/'execution.stderr.txt')
        bound();atomic_json(HERE/'supervisor_complete.json',dict(seconds=elapsed,at_utc=stamp(),status='complete_audited'))
    except BaseException as exc:
        atomic_json(HERE/'supervisor_failure.json',dict(error=str(exc),at_utc=stamp(),protected=protect()))
        raise

if __name__=='__main__':
    cmd=sys.argv[1]
    if cmd=='worker':worker(sys.argv[2])
    else:{'freeze':freeze,'run':run,'execute':execute}[cmd]()
