"""Outcome-blind stage C feasibility check; never settles a season."""
import os
for name in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'):
    os.environ[name]='1'
import copy
import signal
import time
import traceback
from datetime import datetime, timezone
import numpy as np
from .common import ROOT, read, sha, digest, atomic_json, verify_files, runtime
from .simulation import backend
from .manager_learning import Environment, old
from . import manager_policy as base, horizon_policy as policy

HERE=ROOT/'reports/horizon_c_preflight_2026_10_16'
A=ROOT/'reports/rollout_2026_10_15'
F=ROOT/'reports/forecast_freeze_2026_10_16'
CASES=[('2023-24',1),('2023-24',18),('2023-24',20),
       ('2024-25',1),('2024-25',33),('2024-25',38)]

def stamp(): return datetime.now(timezone.utc).isoformat()

def inputs_only():
    # Do not construct Environment: its initializer reads the outcome bank.
    env=object.__new__(Environment);env.e=old();env.loaded={}
    return env

def protect():
    lock=read(F/'package_lock.json')
    verify_files(ROOT,lock['input_hashes']);verify_files(F,lock['bundle_hashes'])
    return dict(package_sha256=sha(F/'package_lock.json'),
                source_hashes_verified=len(lock['input_hashes']),
                bundle_hashes_verified=len(lock['bundle_hashes']))

def prepare():
    if (HERE/'preflight_plan.json').exists(): raise ValueError('Plan already sealed')
    verify_files(ROOT,read(A/'protocol.json')['files'])
    protected=protect()
    paths=[ROOT/'model_lab/horizon_policy.py',ROOT/'model_lab/horizon_preflight.py',
           ROOT/'model_lab/tests/test_horizon_policy.py',A/'protocol.json',A/'audit.json',
           F/'package_lock.json']
    paths += [A/'runs'/s/f'gw{g:02d}.decision.json' for s,g in CASES]
    files={**read(A/'protocol.json')['files'],**{str(p.relative_to(ROOT)):sha(p) for p in paths}}
    atomic_json(HERE/'preflight_plan.json',dict(created_at_utc=stamp(),files=files,runtime=runtime(),
        cases=CASES,arms=[3,8],node_limit=16,total_call_cap=200,per_proposal_cap=40,
        deadline_seconds_per_decision=120,maximum_decisions=12,maximum_solver_calls=2400,
        reason='Opening, chip-half boundary, new half, late season, and season end; not selected by outcomes.',
        purpose='Technical only; no settlement, fitting, outcome metrics or prospective-period inputs.',
        success='All 12 decisions legal and within caps, all 6 H3 archive parities exact, same root proposals, all source hashes unchanged.',
        failure='Stop immediately; preserve failed ledger. No retry, cap adjustment, fallback or horizon selection.',
        protected=protected))
    print('Preflight plan sealed',flush=True)

def audit_output(out,pool,xp,history,state,gw,adapter):
    checks=0
    def check(o,before,values,g):
        nonlocal checks
        after,choice=adapter.engine.apply_decision(before,copy.deepcopy(o['choice']),pool.to_dict('records'),g)
        assert after==o['after'] and base.identity(choice)==o['id']
        f=base.encode(pool,values,history,before,after,choice,adapter.engine,g)
        np.testing.assert_allclose(f,o['features'],rtol=0,atol=1e-10)
        reserve=0 if choice['chip'] is None else adapter.policy.reserve_value(choice['chip'],g)
        np.testing.assert_allclose(100*f[9]+.9*100*f[14]+.81*100*f[15]-reserve,o['base_score'],atol=1e-9)
        checks+=1;return after
    for o in out['options']:check(o,state,xp,gw)
    assert out['shortlist']==policy.shortlist(out['options'])
    assert out['control_index']==base.select(out['options'],None)[0]
    for branch in out['branches']:
        before=copy.deepcopy(state);score=0.
        assert len(branch['steps'])==out['horizon']
        for offset,step in enumerate(branch['steps']):
            assert step['gw']==gw+offset and step['state_before']==before
            if offset==0: assert step['selected']==out['options'][branch['root_index']]
            else:
                for o in step['options']:check(o,before,xp[:,offset:out['horizon']],gw+offset)
                assert step['selected_index']==base.select(step['options'],None)[0]
                assert step['selected']==step['options'][step['selected_index']]
            before=step['selected']['after']
            reward=policy.reward(step['selected'],pool,xp[:,offset],adapter.policy.reserve_value,gw+offset)
            np.testing.assert_allclose(reward,step['reward'],atol=1e-9)
            score+=.9**offset*reward
        np.testing.assert_allclose(score,branch['score'],atol=1e-8)
    best=max(out['branches'],key=lambda b:(b['score'],b['root_index']==out['control_index'],out['options'][b['root_index']]['id']))
    assert out['selected_index']==best['root_index']
    assert out['selected']==out['options'][out['selected_index']]
    return checks

def run():
    plan=read(HERE/'preflight_plan.json');verify_files(ROOT,plan['files'])
    assert runtime()==plan['runtime']
    atomic_json(HERE/'started.json',dict(at_utc=stamp(),plan_sha256=sha(HERE/'preflight_plan.json')))
    env=inputs_only();inventory=[];rows=[];adapter=None
    def timeout(*args):raise TimeoutError('120-second decision safety limit; no retry')
    signal.signal(signal.SIGALRM,timeout)
    try:
        for season in ('2023-24','2024-25'):
            for gw in range(1,39):
                p,x,m,h=env.inputs(season,gw)
                assert x.shape[1]>=min(8,39-gw) and np.isfinite(x).all()
                inventory.append(dict(season=season,gw=gw,players=len(p),columns=x.shape[1],forecast_at=m['forecast_at'],forecast_sha256=digest(x.tolist())))
        atomic_json(HERE/'input_inventory.json',dict(origins=inventory,origins_checked=76,outcomes_loaded=False))
        for season,gw in CASES:
            saved=read(A/'runs'/season/f'gw{gw:02d}.decision.json')
            pool,xp,m,h=env.inputs(season,gw);state=env.e.state_json(saved['state_before'])
            roots=None
            for horizon in (3,8):
                mod,adapter=backend(16,200);counts=[];started=time.monotonic()
                def limited(*args,**kwargs):
                    n=len(adapter.ledger);out=base.proposals(*args,**kwargs)
                    count=len(adapter.ledger)-n
                    if count>40:raise ValueError('Proposal exceeds 40 calls')
                    counts.append(count);return out
                signal.alarm(120)
                out=policy.choose(adapter,pool,xp,h,state,gw,horizon=horizon,
                    official_blank=bool(m.get('official_all_blank_forced_wait')),proposals=limited)
                signal.alarm(0);elapsed=time.monotonic()-started
                cleaned=mod.clean(out)
                parity=None
                if horizon==3:
                    for k in ('options','branches','selected_index','shortlist','control_index','horizon'):
                        assert cleaned[k]==saved[k],('H3 archive mismatch',season,gw,k)
                    parity=True;roots=cleaned['options']
                else:assert cleaned['options']==roots
                checked=audit_output(out,pool,xp,h,state,gw,adapter)
                assert len(adapter.ledger)<=200 and sum(counts)==len(adapter.ledger)
                assert all(r['nodes']<=16 and r['full_mip_feasible'] for r in adapter.ledger)
                row=dict(season=season,gw=gw,requested_horizon=horizon,effective_horizon=out['horizon'],
                    seconds=elapsed,calls=len(adapter.ledger),nodes=sum(r['nodes'] for r in adapter.ledger),
                    max_nodes=max((r['nodes'] for r in adapter.ledger),default=0),proposal_counts=counts,
                    legal_options_checked=checked,h3_archive_parity=parity,same_root_options=True,
                    outcomes_loaded=False,selected_id=out['selected']['id'])
                atomic_json(HERE/f'{season}_gw{gw:02d}_h{horizon}.json',dict(summary=row,decision=cleaned,solver_ledger=adapter.ledger))
                rows.append(row);print({k:row[k] for k in ('season','gw','requested_horizon','seconds','calls','max_nodes')},flush=True)
        verify_files(ROOT,plan['files']);protected=protect();assert protected==plan['protected']
        atomic_json(HERE/'preflight.json',dict(status='pass',completed_at_utc=stamp(),rows=rows,protected=protected,
            outcomes_loaded=False,prospective_rows_used=0,model_fits=0,full_seasons_run=0,
            input_origins_checked=76,legal_options_checked=sum(r['legal_options_checked'] for r in rows)))
    except BaseException as exc:
        signal.alarm(0)
        atomic_json(HERE/'failure.json',dict(at_utc=stamp(),error=str(exc),traceback=traceback.format_exc(),
            completed_rows=rows,failed_ledger=[] if adapter is None else adapter.ledger,outcomes_loaded=False))
        raise

if __name__=='__main__':
    import sys
    {'prepare':prepare,'run':run}[sys.argv[1]]()
