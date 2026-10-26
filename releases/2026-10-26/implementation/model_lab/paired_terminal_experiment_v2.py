"""Paired continuation-value pilot; original experiments remain immutable."""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[k]='1'
import argparse
import copy
import time
import traceback
from datetime import datetime,timezone
import numpy as np
import pandas as pd
from .common import ROOT,read,sha,digest,atomic_json,verify_files,runtime
from .simulation import backend,BENCHMARK
from .manager_learning import Environment,settle,OLD
from . import manager_policy as base,rollout_policy as rollout,paired_terminal as terminal
HERE=ROOT/'reports/paired_terminal_2026_10_16_attempt2'
A=ROOT/'reports/rollout_2026_10_15'
B=ROOT/'reports/terminal_value_2026_10_16'
ID='paired-terminal-h3-20261016-v2'
SEASONS=('2023-24','2024-25')
ORIGINS=(1,4,8,10,13,16,19,22,25,28,31,34)
def stamp(): return datetime.now(timezone.utc).isoformat()
def teacher(season): return OLD/'runs'/f'{season}__{BENCHMARK}'

def bound():
    p=read(HERE/'protocol.json');verify_files(ROOT,p['files'])
    if p['runtime']!=runtime(): raise ValueError('Runtime changed')
    from scripts.research import fingerprint
    reg=read(HERE/'registration.json'); proposal=read(ROOT/reg['proposal'])
    if fingerprint(proposal)!=reg['fingerprint'] or proposal['input_hashes'][str((HERE/'protocol.json').relative_to(ROOT))]!=sha(HERE/'protocol.json'): raise ValueError('Registration mismatch')
    return p


def prepare():
    if (HERE/'protocol.json').exists(): raise ValueError('Already frozen')
    env=Environment();checks=[]
    for season,gw in [('2023-24',1),('2023-24',19),('2024-25',38)]:
        lock=read(A/'runs'/season/f'gw{gw:02d}.decision.json');pool,xp,m,h=env.inputs(season,gw);_,ad=backend(16,200)
        out=rollout.choose(ad,pool,xp,h,env.e.state_json(lock['state_before']),gw)
        for key in ('options','branches','selected_index','shortlist'):
            if env.helpers.clean(out[key])!=lock[key]: raise ValueError('Control parity '+key)
        checks.append(dict(season=season,gw=gw,exact_control=True,outcomes_read=False))
    atomic_json(HERE/'preflight.json',dict(status='pass',checks=checks))
    files=dict(read(B/'protocol.json')['files']);verify_files(ROOT,files)
    paths=[ROOT/'model_lab/paired_terminal.py',ROOT/'model_lab/paired_terminal_experiment_v2.py',ROOT/'model_lab/tests/test_paired_terminal.py',HERE/'preflight.json',B/'audit.json',ROOT/'reports/paired_terminal_2026_10_16/protocol.json',ROOT/'reports/paired_terminal_2026_10_16/failure.json',ROOT/'reports/paired_terminal_2026_10_16/technical_diagnosis.json']
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    protocol=dict(id=ID,created_at_utc=stamp(),runtime=runtime(),files=files,seasons=list(SEASONS),origins=list(ORIGINS),
        technical_revision='v1 stopped before fits/evaluation: 17 reported nodes at configured16. Same-state outcome-blind check passed at64. Only TRAINING TAIL node cap changed to64; root/evaluation remain16. Original failure and all81 completed tail rounds retained. No tuning or outcome-driven change.',
        authorization='User requests a terminal value learning differences between alternative actions at the same state, forecasts fixed.',
        intervention='Same A H3 two-branch rollout and old B terminal features. Fit differences rather than absolute state returns. Zero-intercept Ridge alpha50, RMS scaling without centering. No tuning.',
        training='12 fixed benchmark start states in each of 2022-23 and 2023-24. Origins 1,4,8,10,13,16,19,22,25,28,31,34; GW7 avoided because of known 2022 official blank. Generate both unchanged A H3 branches from identical state/current-origin arrays; at H3 end continue each through GW38 with same unlearned proposal policy, forecast archive and actual football outcomes. Each continuation uses only own-deadline inputs; outcomes read after saved decision.',
        target='Branch1 minus branch0 discounted tail net points minus fixed reserve charges, starting strictly after H3. Difference of the same terminal features. No first-H3 realised rewards in target. Potential evaluated independently for each branch; only differences identified.',
        split='2022-23 pairs train eval2023-24; add completed 2023-24 pairs only for eval2024-25. Whole-season label availability before each evaluation cutoff. No new forecast fits or 2025-26/2026-27 outcomes.',
        validation='Chronological 2023-24 pair MSE versus zero difference and sign accuracy using model trained on 2022-23. Descriptive, no tuning/gating after results.',
        primary_control='A bounded_rollout_h3_v1 archived episodes, exact control parity probes. B1 reported only as secondary reference.',
        success='Strict positive net full-season points against A in BOTH evaluation years; otherwise reject. Research only, no automatic promotion.',
        resources=dict(configurations=1,forecast_fits=0,value_fits=2,training_pairs=24,training_root_decisions=24,max_training_tail_rounds=884,evaluation_rounds=76,new_full_seasons=2,node_limit=16,training_tail_node_limit=64,root_call_cap=200,tail_call_cap=40,per_proposal_call_cap=40,threads=1),
        stop='Fail closed on hash/runtime/legality/missing label/solver/resource error. No silent restart, dropped pair, score-driven stopping or parameter search. Preserve failure and create explicit corrected attempt if needed.',
        limitations='Previously studied development years; 24 pairs are not independent seasons. Fixed state sampler and bounded two-action set; Tail suffixes of up to35 rounds overlap. H3 terminal prices/availability frozen as in A. Training continuation policy differs from rollout deployment. Historical football outcomes treated as unaffected by fantasy choices. Limited state features may not identify actual action differences.')
    atomic_json(HERE/'protocol.json',protocol)
    spec=dict(id=ID,candidate_id='paired_terminal_h3_v2',dataset_id='fpl_2026_27_best_effort_v1',benchmark_id=BENCHMARK,clock='operational_proxy_v1',features='pairwise differences of unchanged terminal inventory features',
        hypothesis='Parvis lært sluttverdi gir flere netto sesongpoeng enn A med faste prognoser.',change=protocol['intervention'],related_work=['paired-terminal-h3-20261016-v1','terminal-value-h3-20261016-v1','rollout-h3-20261015-v1'],
        input_hashes={**files,str((HERE/'protocol.json').relative_to(ROOT)):sha(HERE/'protocol.json')},model_parameters=dict(alpha=50.,intercept=False,discount=.9),decision_policy=dict(horizon=3,width=2,continuation='same_proposals_unlearned_v1'),seasons=list(SEASONS),resources=protocol['resources'],maximum_runs=2,success_criterion=protocol['success'],stop_rule=protocol['stop'])
    from scripts.research import validate,exclusive,RECORDS,refresh
    fp=validate(spec);spec.update(fingerprint=fp,registered_at_utc=stamp());dest=RECORDS/(fp+'.proposal.json');exclusive(dest,spec)
    atomic_json(HERE/'registration.json',dict(fingerprint=fp,proposal=str(dest.relative_to(ROOT))));refresh();print('Registered',ID,flush=True)


def tail(env,season,start,state,folder):
    atomic_json(folder/'started.json',dict(season=season,start=start,state=env.helpers.clean(state)))
    total=0.;n=0;calls=0;start_time=time.monotonic()
    for gw in range(start,39):
        pool,xp,m,h=env.inputs(season,gw);_,ad=backend(64,40)
        options=base.proposals(ad,pool,xp,h,state,gw,bool(m.get('official_all_blank_forced_wait')))
        index=base.select(options,None)[0];chosen=options[index]
        lock=env.helpers.clean(dict(season=season,gw=gw,state_before=state,forecast_at=m['forecast_at'],forecast_array_sha256=digest(xp.tolist()),options=options,selected_index=index,selected=chosen,solver_calls=ad.ledger,outcomes_read=False))
        atomic_json(folder/f'gw{gw:02d}.decision.json',lock)
        outcomes,settlement,net=settle(ad,env,season,gw,chosen,pool)
        reserve=0. if chosen['choice']['chip'] is None else ad.policy.reserve_value(chosen['choice']['chip'],gw)
        reward=net-reserve
        atomic_json(folder/f'gw{gw:02d}.json',dict(lock,outcomes_read=True,outcomes=outcomes,settlement=env.helpers.clean(settlement),net_points=net,reserve=reserve,reward=reward))
        total+=.9**(gw-start)*reward;n+=1;calls+=len(ad.ledger);state=chosen['after']
    summary=dict(discounted_return=total,rounds=n,calls=calls,seconds=time.monotonic()-start_time)
    atomic_json(folder/'summary.json',summary);return total


def samples(env,season):
    folder=HERE/'pairs'/season
    if (folder/'complete.json').exists():
        done=read(folder/'complete.json');verify_files(folder,done['files']);return read(folder/'samples.json')
    atomic_json(folder/'started.json',dict(at_utc=stamp(),season=season,origins=list(ORIGINS)))
    result=[]
    for gw in ORIGINS:
        path=folder/f'gw{gw:02d}';pool,xp,m,h=env.inputs(season,gw)
        state=env.e.state_json(read(teacher(season)/f'gw{gw:02d}.json')['state_before']);_,ad=backend(16,200);counts=[]
        def limited(*args,**kwargs):
            before=len(ad.ledger);options=base.proposals(*args,**kwargs);n=len(ad.ledger)-before
            if n>40: raise ValueError('Per-proposal cap')
            counts.append(n);return options
        root=rollout.choose(ad,pool,xp,h,state,gw,proposals=limited)
        if len(root['branches'])!=2: raise ValueError('Requires two distinct root afterstates, no silent dropping')
        atomic_json(path/'root.json',env.helpers.clean(dict(root,season=season,gw=gw,state_before=state,forecast_at=m['forecast_at'],forecast_array_sha256=digest(xp.tolist()),solver_calls=ad.ledger,proposal_call_counts=counts,outcomes_read=False)))
        xs=[];returns=[]
        for j,branch in enumerate(root['branches']):
            last=branch['steps'][-1];end=last['gw'];after=env.e.state_json(last['selected']['after'])
            xs.append(terminal.features(pool,xp[:,2],after,end))
            returns.append(tail(env,season,end+1,after,path/f'branch{j}'))
        sample=dict(season=season,origin=gw,end=end,features=(np.array(xs[1])-xs[0]).tolist(),target=returns[1]-returns[0],branch_features=xs,branch_returns=returns,label_available_at=str(env.labels.loc[season]),forecast_at=m['forecast_at'],state_hash=digest(state),root_sha256=sha(path/'root.json'))
        atomic_json(path/'pair.json',sample);result.append(sample)
        print(f'Paired training {season} GW{gw:02d}: both continuations completed',flush=True)
    atomic_json(folder/'samples.json',result)
    files={str(p.relative_to(folder)):sha(p) for p in folder.rglob('*.json')}
    atomic_json(folder/'complete.json',dict(pairs=len(result),files=files));return result


def audit_pairs():
    env=Environment();_,ad=backend(16,200);_,tail_ad=backend(64,40);rules=ad.engine;rounds=0;pair_count=0;calls=0
    def option(o,p,x,h,s,g,blank=False):
        c=copy.deepcopy(o['choice']);c['prices']={int(k):v for k,v in c['prices'].items()}
        after,legal=rules.apply_decision(s,c,p.to_dict('records'),g)
        assert after==env.e.state_json(o['after']) and base.identity(legal)==o['id']
        f=base.encode(p,x,h,s,after,legal,rules,g);np.testing.assert_allclose(f,o['features'],atol=1e-10)
        reserve=0. if legal['chip'] is None else ad.policy.reserve_value(legal['chip'],g)
        expected=0. if blank else 100*f[9]+.9*100*f[14]+.81*100*f[15]-reserve
        np.testing.assert_allclose(expected,o['base_score'],atol=1e-9)
    for season in ('2022-23','2023-24'):
        saved=samples(env,season)
        assert [s['origin'] for s in saved]==list(ORIGINS)
        for sample in saved:
            gw=sample['origin'];path=HERE/'pairs'/season/f'gw{gw:02d}';root=read(path/'root.json')
            state=env.e.state_json(read(teacher(season)/f'gw{gw:02d}.json')['state_before']);p,x,m,h=env.inputs(season,gw)
            assert root['state_before']==env.helpers.clean(state) and sample['state_hash']==digest(state) and sample['root_sha256']==sha(path/'root.json')
            assert not root['outcomes_read'] and root['forecast_at']==m['forecast_at'] and root['forecast_array_sha256']==digest(x.tolist())
            assert root['shortlist']==rollout.shortlist(root['options']) and root['control_index']==base.select(root['options'],None)[0]
            assert len(root['solver_calls'])<=200 and sum(root['proposal_call_counts'])==len(root['solver_calls']) and max(root['proposal_call_counts'])<=40
            assert [b['root_index'] for b in root['branches']]==root['shortlist']
            for o in root['options']:option(o,p,x,h,state,gw)
            xs=[];ys=[]
            for j,b in enumerate(root['branches']):
                current=copy.deepcopy(state);score=0.
                assert len(b['steps'])==3
                for offset,step in enumerate(b['steps']):
                    assert step['gw']==gw+offset and env.e.state_json(step['state_before'])==current
                    if offset==0:assert step['selected']==root['options'][b['root_index']]
                    else:
                        for o in step['options']:option(o,p,x[:,offset:3],h,current,gw+offset)
                        assert step['selected_index']==base.select(step['options'],None)[0] and step['selected']==step['options'][step['selected_index']]
                    reward=rollout.reward(step['selected'],p,x[:,offset],ad.policy.reserve_value,gw+offset)
                    np.testing.assert_allclose(reward,step['reward'],atol=1e-9);score+=.9**offset*reward;current=env.e.state_json(step['selected']['after'])
                np.testing.assert_allclose(score,b['score'],atol=1e-9)
                xs.append(terminal.features(p,x[:,2],current,gw+2));total=0.;tailfolder=path/f'branch{j}'
                start=read(tailfolder/'started.json');assert start['start']==gw+3 and env.e.state_json(start['state'])==current
                for k in range(gw+3,39):
                    lock=read(tailfolder/f'gw{k:02d}.decision.json');row=read(tailfolder/f'gw{k:02d}.json');pool,xp,manifest,history=env.inputs(season,k)
                    assert env.e.state_json(lock['state_before'])==current and lock['forecast_at']==manifest['forecast_at'] and lock['forecast_array_sha256']==digest(xp.tolist())
                    assert not lock['outcomes_read'] and row['outcomes_read'] and all(row[q]==v for q,v in lock.items() if q!='outcomes_read')
                    for o in lock['options']:option(o,pool,xp,history,current,k,bool(manifest.get('official_all_blank_forced_wait')))
                    assert lock['selected_index']==base.select(lock['options'],None)[0] and lock['selected']==lock['options'][lock['selected_index']]
                    outcomes,settlement,net=settle(ad,env,season,k,lock['selected'],pool)
                    assert outcomes==row['outcomes'] and env.helpers.clean(settlement)==row['settlement'] and net==row['net_points']
                    reserve=0. if lock['selected']['choice']['chip'] is None else ad.policy.reserve_value(lock['selected']['choice']['chip'],k)
                    np.testing.assert_allclose([reserve,net-reserve],[row['reserve'],row['reward']],atol=1e-10)
                    total+=.9**(k-gw-3)*(net-reserve);current=env.e.state_json(lock['selected']['after']);rounds+=1
                    assert len(lock['solver_calls'])<=40
                    for c in lock['solver_calls']:assert c['options']==tail_ad.options and c['nodes']<=64 and c['full_mip_feasible']
                    calls+=len(lock['solver_calls'])
                summary=read(tailfolder/'summary.json');assert summary['rounds']==36-gw
                np.testing.assert_allclose(total,summary['discounted_return'],atol=1e-8);ys.append(total)
            for c in root['solver_calls']:assert c['options']==ad.options and c['nodes']<=16 and c['full_mip_feasible']
            np.testing.assert_allclose(xs,sample['branch_features'],atol=1e-10);np.testing.assert_allclose(np.array(xs[1])-xs[0],sample['features'],atol=1e-10)
            np.testing.assert_allclose(ys,sample['branch_returns'],atol=1e-8);np.testing.assert_allclose(ys[1]-ys[0],sample['target'],atol=1e-8)
            assert sample['label_available_at']==str(env.labels.loc[season]);pair_count+=1
            print(f'Audited pair {season} GW{gw:02d}',flush=True)
    assert rounds==884 and pair_count==24
    atomic_json(HERE/'pair_audit.json',dict(status='pass',tail_rounds=rounds,pairs=pair_count,tail_calls=calls,same_state_and_origin_verified=True,targets_recomputed=True))


def run():
    bound();atomic_json(HERE/'started.json',dict(at_utc=stamp(),protocol_sha256=sha(HERE/'protocol.json')))
    env=Environment();training=[]
    for previous,season in zip(('2022-23','2023-24'),SEASONS):
        training+=samples(env,previous);cutoff=env.inputs(season,1)[2]['forecast_at']
        model=terminal.fit(training,cutoff);atomic_json(HERE/f'model_{season}.json',model)
        atomic_json(HERE/f'training_{season}.json',training)
        _,initial=backend();state=initial.engine.initial_state();logs=[];start=time.monotonic()
        for gw in range(1,39):
            pool,xp,manifest,history=env.inputs(season,gw);_,adapter=backend(16,200);counts=[]
            def limited(*args,**kwargs):
                before=len(adapter.ledger);options=base.proposals(*args,**kwargs);n=len(adapter.ledger)-before
                if n>40: raise ValueError('Per-proposal cap')
                counts.append(n);return options
            chosen=rollout.choose(adapter,pool,xp,history,state,gw,official_blank=bool(manifest.get('official_all_blank_forced_wait')),proposals=limited)
            chosen=terminal.attach(chosen,model,pool,xp,env.e.state_json)
            lock=env.helpers.clean(dict(**chosen,season=season,gw=gw,state_before=state,forecast_at=manifest['forecast_at'],
                forecast_array_sha256=digest(xp.tolist()),model_sha256=digest(model),solver_calls=adapter.ledger,proposal_call_counts=counts,outcomes_read=False))
            directory=HERE/'runs'/season;atomic_json(directory/f'gw{gw:02d}.decision.json',lock)
            outcomes,result,net=settle(adapter,env,season,gw,chosen['selected'],pool)
            row=dict(lock,outcomes_read=True,outcomes=outcomes,settlement=env.helpers.clean(result),net_points=net)
            atomic_json(directory/f'gw{gw:02d}.json',row);logs.append(row);state=chosen['selected']['after']
            print(f'{season} GW{gw:02d} locked and settled',flush=True)
        atomic_json(directory/'summary.json',dict(season=season,net_points=sum(r['net_points'] for r in logs),seconds=time.monotonic()-start,
            calls=sum(len(r['solver_calls']) for r in logs),rounds=len(logs)))
    bound();atomic_json(HERE/'complete.json',dict(at_utc=stamp(),decisions=76))


def audit():
    bound();read(HERE/'complete.json');audit_pairs();env=Environment();_,adapter=backend(16,200);rules=adapter.engine
    rounds=[];results=[];training=[];checks=0
    def check_option(o,p,x,h,s,g):
        choice=copy.deepcopy(o['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()}
        after,legal=rules.apply_decision(s,choice,p.to_dict('records'),g)
        assert after==env.e.state_json(o['after']) and base.identity(legal)==o['id']
        f=base.encode(p,x,h,s,after,legal,rules,g)
        reserve=0. if legal['chip'] is None else adapter.policy.reserve_value(legal['chip'],g)
        np.testing.assert_allclose(f,o['features'],rtol=0,atol=1e-10)
        np.testing.assert_allclose(100*f[9]+.9*100*f[14]+.81*100*f[15]-reserve,o['base_score'],atol=1e-9)
        return after
    for previous,season in zip(('2022-23','2023-24'),SEASONS):
        training+=samples(env,previous);model=read(HERE/f'model_{season}.json')
        assert training==read(HERE/f'training_{season}.json')
        # Independently reconstruct the closed-form ridge solution, no model search.
        x=np.array([s['features'] for s in training]);y=np.array([s['target'] for s in training]);z=(x-model['mean'])/model['scale']
        coef=np.linalg.solve(z.T@z+50*np.eye(z.shape[1]),z.T@y)
        np.testing.assert_allclose(coef,model['coef'],atol=1e-8)
        assert model['intercept']==0. and model['mean']==[0.]*len(terminal.FEATURES)
        expected_scale=np.sqrt(np.mean(x*x,axis=0));expected_scale[expected_scale==0]=1.
        np.testing.assert_allclose(expected_scale,model['scale'],atol=1e-10)
        assert pd.Timestamp(model['latest_label_available_at'])<pd.Timestamp(env.inputs(season,1)[2]['forecast_at'])
        totals={}
        for label,folder in [('control',A/'runs'/season),('candidate',HERE/'runs'/season)]:
            state=rules.initial_state();total=0.;hits=0;chips={c:[] for c in base.CHIPS};changed=0
            for gw in range(1,39):
                lock=read(folder/f'gw{gw:02d}.decision.json');row=read(folder/f'gw{gw:02d}.json');pool,xp,m,h=env.inputs(season,gw)
                assert not lock['outcomes_read'] and row['outcomes_read']
                assert all(row[k]==v for k,v in lock.items() if k!='outcomes_read')
                assert env.e.state_json(lock['state_before'])==state and lock['forecast_array_sha256']==digest(xp.tolist()) and lock['forecast_at']==m['forecast_at']
                for o in lock['options']: check_option(o,pool,xp,h,state,gw)
                assert lock['control_index']==base.select(lock['options'],None)[0]
                assert lock['shortlist']==rollout.shortlist(lock['options'])
                assert [b['root_index'] for b in lock['branches']]==lock['shortlist']
                pure=[]
                for b in lock['branches']:
                    current=copy.deepcopy(state);score=0.;horizon=min(3,xp.shape[1],39-gw)
                    assert len(b['steps'])==horizon
                    for offset,step in enumerate(b['steps']):
                        assert step['gw']==gw+offset and env.e.state_json(step['state_before'])==current
                        if offset==0: assert step['selected']==lock['options'][b['root_index']]
                        else:
                            for o in step['options']: check_option(o,pool,xp[:,offset:horizon],h,current,gw+offset)
                            assert step['selected_index']==base.select(step['options'],None)[0]
                            assert step['selected']==step['options'][step['selected_index']]
                        current=env.e.state_json(step['selected']['after'])
                        reward=rollout.reward(step['selected'],pool,xp[:,offset],adapter.policy.reserve_value,gw+offset)
                        np.testing.assert_allclose(reward,step['reward'],atol=1e-9);score+=.9**offset*reward
                    pure.append((score,b['root_index']))
                    if label=='candidate':
                        f=terminal.features(pool,xp[:,horizon-1],current,gw+horizon-1)
                        np.testing.assert_allclose(f,b['terminal_features'],atol=1e-10)
                        v=0. if gw+horizon-1==38 else float((np.array(f)-model['mean'])/model['scale']@np.array(model['coef'])+model['intercept'])
                        np.testing.assert_allclose([v,score],[b['terminal_value'],b['truncated_score']],atol=1e-8);score+=.9**horizon*v
                    np.testing.assert_allclose(score,b['score'],atol=1e-8)
                key=lambda b:(b['score'],b['root_index']==lock['control_index'],lock['options'][b['root_index']]['id'])
                assert lock['selected_index']==max(lock['branches'],key=key)['root_index']
                assert lock['selected']==lock['options'][lock['selected_index']]
                assert len(lock['solver_calls'])<=200 and max(lock['proposal_call_counts'])<=40 and sum(lock['proposal_call_counts'])==len(lock['solver_calls'])
                for call in lock['solver_calls']: assert call['options']==adapter.options and call['nodes']<=16 and call['full_mip_feasible']
                outcomes,settlement,net=settle(adapter,env,season,gw,lock['selected'],pool)
                assert outcomes==row['outcomes'] and env.helpers.clean(settlement)==row['settlement'] and net==row['net_points']
                if label=='candidate':
                    pure_index=max(pure,key=lambda t:(t[0],t[1]==lock['control_index'],lock['options'][t[1]]['id']))[1]
                    assert pure_index==lock['zero_terminal_selected_index'] and lock['model_sha256']==digest(model)
                    different=pure_index!=lock['selected_index'];changed+=different
                    rounds.append(dict(season=season,gw=gw,changed_from_same_state_A=different,net_points=net,chip=lock['selected']['choice']['chip'],hits=4*lock['selected']['choice']['paid'],calls=len(lock['solver_calls'])))
                c=lock['selected']['choice'];hits+=4*c['paid']
                if c['chip']: chips[c['chip']].append(gw)
                total+=net;state=env.e.state_json(lock['selected']['after']);checks+=1
            assert total==read(folder/'summary.json')['net_points']
            totals[label]=dict(net_points=total,hits=hits,chips=chips,unused_chips={half:[c for c in base.CHIPS if c not in state['used_chips'][half]] for half in ('1','2')},final_bank=state['bank'],final_ft=state['ft'],changed=changed,**{k:v for k,v in read(folder/'summary.json').items() if k in ('seconds','calls')})
        results.append(dict(season=season,control=totals['control']['net_points'],candidate=totals['candidate']['net_points'],difference=totals['candidate']['net_points']-totals['control']['net_points'],details=totals))
    hold=samples(env,'2023-24');model=read(HERE/'model_2023-24.json')
    y=np.array([s['target'] for s in hold]);pred=np.array([terminal.predict(model,s['features'],s['end']) for s in hold])
    nonzero=np.abs(y)>1e-9
    validation=dict(season='2023-24',training='2022-23',rows=len(hold),paired_mse=float(np.mean((pred-y)**2)),
        zero_difference_mse=float(np.mean(y*y)),direction_accuracy=float(np.mean(np.sign(pred[nonzero])==np.sign(y[nonzero]))) if nonzero.any() else None,
        nonzero_pairs=int(nonzero.sum()),scope='Previously studied historical years and overlapping paired tails; no tuning, no claim of independent observations.')
    success=all(r['difference']>0 for r in results)
    atomic_json(HERE/'audit.json',dict(status='pass',rounds_recomputed=checks,training_closed_form_verified=True,value_validation=validation,results=results,pilot_success=success,forecast_fits=0))
    pd.DataFrame(rounds).to_csv(HERE/'rounds.csv',index=False)
    pd.DataFrame([{k:v for k,v in r.items() if k!='details'} for r in results]).to_csv(HERE/'results.csv',index=False)
    conclusion='Parvis sluttverdi: '+('bestått forskningskrav' if success else 'ikke bestått')+'. Benchmark beholdes.'
    lines=['# Parvis sluttverdi – forskjell mellom handlinger fra samme tilstand','',conclusion,'','| Sesong | A: kontroll | B2: parvis sluttverdi | Forskjell |','|---|---:|---:|---:|']
    lines += [f"| {r['season']} | {r['control']:.0f} | {r['candidate']:.0f} | {r['difference']:+.0f} |" for r in results]
    lines += ['', 'Én låst variant. Samme prognoser, H3, to grener, forslag, videreføringspolicy og chipreserver. En Ridge uten konstantledd (alpha 50) lærer forskjellen i diskontert avkastning etter horisonten mellom to handlinger fra samme tilstand. Egenskapene er forskjeller i tropp, bank, gratisbytter og chips. Samme sluttverdiegenskaper som B1; RMS-skalering uten sentrering sikrer antisymmetri. Sluttverdi ved GW38 er null. Bare tidligere avsluttede sesonger brukes ved trening.', '',
        f"Tidsordnet par-diagnose på 2023/24: MSE {validation['paired_mse']:.3f}, mot {validation['zero_difference_mse']:.3f} ved alltid å anslå null forskjell. Riktig fortegn i {validation['direction_accuracy']:.1%} av {validation['nonzero_pairs']} par med ikke-null faktisk forskjell. Tolv forhåndsvalgte par; overlappende videreføringer. Ingen tuning.", '',
        'Alle 152 kontroll- og kandidatrunder er avregnet på nytt. Lovlige overganger, grenvalg, sluttverdier, prognosehash, treningsgrenser og løsergrenser er kontrollert. Treningens koeffisienter er gjenskapt med en separat lukket Ridge-beregning. Kontrollen fra A gjenbrukes; tre nye utfallsblinde prøver gjenskapte grenene eksakt.', '',
        'Begrensninger: tidligere undersøkte utviklingsår, tolv forhåndsvalgte benchmark-starttilstander per treningsår, to H3-grener per tilstand og overlappende videreføringer. Begge grener fortsetter med samme uendrede forslagspolicy uten sluttverdilæring. Fremtidige arkivprognoser leses bare ved egne historiske frister under trening. Sluttlagene ved H3 bruker frosne priser som i A. Hypotetiske fotballutfall påvirkes ikke av fantasy-handlinger. Begrenset tilstandsdekning og forskjell mellom videreføringspolicy og endelig manager begrenser overføringen. Historiske priser og tilgjengelighet har eksisterende proxyer. Prognosene er uendret og to runder gamle ved terminaltidspunktet. Ingen automatisk oppgradering.', '', '## Ressurser og beslutninger', '', 'Teknisk v2: første forsøk stoppet ved17 rapporterte noder mot grense16 etter81 treningsrunder, før modellfit/evaluering. V2 har grense64 bare for treningsvidereføring; root og evaluering beholder16. Ingen prognose eller læringsregel endret. De81 gamle treningsrundene gjenbrukes ikke og kommer i tillegg til v2-arbeidet.', '', f"Treningskontroll: {read(HERE/'pair_audit.json')['tail_rounds']} videreførte og etterkontrollerte treningsrunder; {read(HERE/'pair_audit.json')['pairs']} par. To parvise modellfit, null prognosefit."]
    for r in results:
        d=r['details'];lines += ['',f"{r['season']}: endret valg mot A på samme tilstand i {d['candidate']['changed']} av 38 runder. Kandidat {d['candidate']['calls']} løserkall / {d['candidate']['seconds']:.1f} sekunder; kontroll {d['control']['calls']} / {d['control']['seconds']:.1f}. Hits: {d['candidate']['hits']} mot {d['control']['hits']}.",f"Chipbruk kandidat: {d['candidate']['chips']}. Kontroll: {d['control']['chips']}.",f"Ubrukte chips kandidat: {d['candidate']['unused_chips']}. Kontroll: {d['control']['unused_chips']}."]
    lines += ['', 'Resultatet gjelder denne sluttverdimodellen. En negativ prøve er ikke en generell avvisning av planlegging med sluttverdi. Ingen nye prognoser eller endringer i den fryste GW7–38-pakken.', '', '[Protokoll](protocol.json) · [Kontroll og fulle detaljer](audit.json) · [Runder](rounds.csv)','']
    (HERE/'RESULTATER.md').write_text('\n'.join(lines))
    evidence=[p for p in HERE.rglob('*') if p.is_file() and p.suffix in ('.json','.csv','.md')]
    result=dict(conclusion=conclusion,decision='retain_for_research' if success else 'reject',results=dict(seasons=results,pilot_success=success,value_validation=validation,benchmark_promoted=False),evidence_hashes={str(p.relative_to(ROOT)):sha(p) for p in evidence})
    atomic_json(HERE/'result.json',result)
    print(conclusion,results,flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('command',choices=['prepare','run','audit']);a=parser.parse_args()
    try: globals()[a.command]()
    except BaseException as exc:
        if a.command=='run' and not (HERE/'failure.json').exists(): atomic_json(HERE/'failure.json',dict(at_utc=stamp(),error=str(exc),traceback=traceback.format_exc()))
        raise
if __name__=='__main__': main()
