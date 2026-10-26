"""Locked stage B pilot. python -m model_lab.terminal_experiment prepare|run|audit"""
import os
for k in ('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS'): os.environ[k]='1'
import argparse
import copy
import time
import traceback
from datetime import datetime, timezone
import numpy as np
import pandas as pd
from .common import ROOT,read,sha,digest,atomic_json,verify_files,runtime
from .simulation import backend,BENCHMARK
from .manager_learning import Environment,settle,OLD
from . import manager_policy as base, rollout_policy as rollout, terminal_value as terminal

HERE=ROOT/'reports/terminal_value_2026_10_16'
A=ROOT/'reports/rollout_2026_10_15'
ID='terminal-value-h3-20261016-v1'
SEASONS=('2023-24','2024-25')

def stamp(): return datetime.now(timezone.utc).isoformat()
def teacher(season): return OLD/'runs'/f'{season}__{BENCHMARK}'

def samples(env, season):
    _,adapter=backend(); logs=[read(teacher(season)/f'gw{gw:02d}.json') for gw in range(1,39)]
    result=[]
    for gw in range(1,37):
        pool,xp,manifest,_=env.inputs(season,gw); end=gw+2
        state=env.e.state_json(logs[end-1]['state_after'])
        x=terminal.features(pool,xp[:,2],state,end)
        target=0.
        for j,row in enumerate(logs[end:]):
            reserve=0. if row['chip'] is None else adapter.policy.reserve_value(row['chip'],row['gw'])
            target += .9**j*(row['net_points']-reserve)
        result.append(dict(season=season,origin=gw,end=end,features=x,target=target,
            label_available_at=str(env.labels.loc[season]),forecast_at=manifest['forecast_at']))
    return result


def bound():
    p=read(HERE/'protocol.json');verify_files(ROOT,p['files'])
    if p['runtime']!=runtime(): raise ValueError('Runtime changed')
    from scripts.research import fingerprint
    reg=read(HERE/'registration.json'); proposal=read(ROOT/reg['proposal'])
    if fingerprint(proposal)!=reg['fingerprint'] or proposal['input_hashes'][str((HERE/'protocol.json').relative_to(ROOT))]!=sha(HERE/'protocol.json'): raise ValueError('Registration mismatch')
    return p


def prepare():
    if (HERE/'protocol.json').exists(): raise ValueError('Already registered')
    env=Environment();probes=[]
    # Historical array/schema and causal cutoff checks, without fitting or scoring targets.
    for season in ('2022-23','2023-24'):
        for gw in range(1,37):
            pool,xp,m,h=env.inputs(season,gw)
            state=env.e.state_json(read(teacher(season)/f'gw{gw+2:02d}.json')['state_after'])
            terminal.features(pool,xp[:,2],state,gw+2)
    for season,gw in [('2023-24',1),('2023-24',19),('2024-25',38)]:
        lock=read(A/'runs'/season/f'gw{gw:02d}.decision.json')
        pool,xp,m,h=env.inputs(season,gw);state=env.e.state_json(lock['state_before']);_,adapter=backend(16,200)
        r=rollout.choose(adapter,pool,xp,h,state,gw)
        for k in ('options','branches','selected_index','shortlist'):
            if env.helpers.clean(r[k])!=lock[k]: raise ValueError('Control parity: '+k)
        probes.append(dict(season=season,gw=gw,control_exact=True,outcomes_read=False))
    # Hand-check terminal expiry, no residual value at season end, and transfer resources.
    pool,xp,m,h=env.inputs('2023-24',19)
    state=env.e.state_json(read(A/'runs'/'2023-24'/'gw19.decision.json')['selected']['after'])
    used=copy.deepcopy(state);used['used_chips']['1']=list(base.CHIPS)
    assert terminal.features(pool,xp[:,0],state,19)==terminal.features(pool,xp[:,0],used,19)
    assert terminal.features(pool,xp[:,0],state,38)==[0.]*len(terminal.FEATURES)
    more=copy.deepcopy(state);more['ft']+=1
    assert terminal.features(pool,xp[:,0],more,20)[5]>terminal.features(pool,xp[:,0],state,20)[5]
    # Synthetic ranking: useful terminal state can reverse choice; discount and zero-end enforced.
    fake=dict(features=terminal.FEATURES,mean=[0.]*10,scale=[1.]*10,coef=[0.]*10,intercept=999.)
    assert terminal.predict(fake,[0.]*10,38)==0.
    atomic_json(HERE/'preflight.json',dict(status='pass',probes=probes,training_schema_rows=72,
        checks=['season-end zero','half-season chip expiry','free-transfer inventory','control branch exact parity']))
    files=dict(read(A/'protocol.json')['files'])
    # Old source hashes must remain valid. New code is added, no old code edited.
    verify_files(ROOT,files)
    paths=[ROOT/'model_lab/terminal_value.py',ROOT/'model_lab/terminal_experiment.py',HERE/'preflight.json',A/'audit.json']
    paths+=list((A/'runs').rglob('*.json'))
    for s in ('2022-23','2023-24'): paths+=list(teacher(s).glob('*.json'))
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    protocol=dict(id=ID,created_at_utc=stamp(),runtime=runtime(),files=files,seasons=list(SEASONS),
        authorization='User explicitly requests stage B with fixed forecasts and full-season points.',
        intervention='Add discounted learned after-horizon value to unchanged H3 width-two rollout. Same proposals, continuation policy, reserve charges and forecasts as A.',
        training='One historical benchmark trajectory per completed season; 2022-23 for eval2023-24; 2022-23+2023-24 for eval2024-25. 36 samples per season. End-state at origin+2 encoded using original origin col2 forecasts and prices. No evaluation-season labels at fit.',
        target='Discounted realised net points minus unchanged chip reserves AFTER terminal round through GW38, discount .9. GW38 terminal exactly zero. Regularized Ridge alpha50 with standardized state features, no tuning.',
        validation='Chronological 2023-24 teacher value prediction using 2022-23 fit; report MSE versus time-only fit. Diagnostic, not a second tuning loop or automatic gate.',
        resources=dict(configurations=1,forecast_fits=0,value_fits=2,time_only_diagnostic_fits=2,new_full_seasons=2,new_decisions=76,node_limit=16,max_calls=200,per_proposal_calls=40,threads=1),
        primary_control='A bounded_rollout_h3_v1, archived exact forecasts and branches verified at three origins; zero terminal value with original reserve heuristic.',
        success='Strict positive net season-point difference against A in BOTH 2023-24 and 2024-25. Research only; no automatic promotion.',
        stop='Stop on integrity, legality, solver, availability or resource failure. No tuning or silent retry. Technical repair requires documented version; no score-based stopping.',
        limitations='Previously studied development years; only one teacher trajectory per year and overlapping returns, not independent samples. Teacher is historical benchmark, not rollout; terminal states of hypothetical branches differ from teacher. Forecasts stale by two rounds at terminal. Price/availability proxies inherited. This is an estimated continuation surrogate, no guaranteed improved value.')
    atomic_json(HERE/'protocol.json',protocol)
    proposal=dict(id=ID,candidate_id='learned_terminal_h3_v1',dataset_id='fpl_2026_27_best_effort_v1',benchmark_id=BENCHMARK,
        clock='operational_proxy_v1',features='unchanged current-origin forecasts plus terminal inventory',hypothesis='Lært verdi etter H3 gir flere netto sesongpoeng enn samme rollout uten sluttverdi.',
        change=protocol['intervention'],related_work=['rollout-h3-20261015-v1','season-manager-20261015-v1'],
        input_hashes={**files,str((HERE/'protocol.json').relative_to(ROOT)):sha(HERE/'protocol.json')},model_parameters=dict(alpha=50.,discount=.9),
        decision_policy=dict(horizon=3,width=2),seasons=list(SEASONS),resources=protocol['resources'],maximum_runs=2,success_criterion=protocol['success'],stop_rule=protocol['stop'])
    from scripts.research import validate,exclusive,RECORDS,refresh
    fp=validate(proposal);proposal.update(fingerprint=fp,registered_at_utc=stamp());dest=RECORDS/(fp+'.proposal.json');exclusive(dest,proposal)
    atomic_json(HERE/'registration.json',dict(fingerprint=fp,proposal=str(dest.relative_to(ROOT))));refresh()
    print('Registered',ID,flush=True)


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
    bound();read(HERE/'complete.json');env=Environment();_,adapter=backend(16,200);rules=adapter.engine
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
        coef=np.linalg.solve(z.T@z+50*np.eye(z.shape[1]),z.T@(y-y.mean()))
        np.testing.assert_allclose(coef,model['coef'],atol=1e-8)
        np.testing.assert_allclose(y.mean(),model['intercept'],atol=1e-8)
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
    hold=samples(env,'2023-24');model=read(HERE/'model_2023-24.json');x=np.array([s['features'] for s in hold]);y=np.array([s['target'] for s in hold]);pred=np.array([terminal.predict(model,s['features'],s['end']) for s in hold]);t=model['time_only'];tp=(x[:,:2]-t['mean'])/t['scale']@np.array(t['coef'])+t['intercept'];tp[-1]=0.
    validation=dict(season='2023-24',training='2022-23',rows=len(hold),state_value_mse=float(np.mean((pred-y)**2)),time_only_mse=float(np.mean((tp-y)**2)),zero_value_mse=float(np.mean(y*y)),scope='Overlapping teacher returns, descriptive temporal check only; no tuning.')
    success=all(r['difference']>0 for r in results)
    atomic_json(HERE/'audit.json',dict(status='pass',rounds_recomputed=checks,training_closed_form_verified=True,value_validation=validation,results=results,pilot_success=success,forecast_fits=0))
    pd.DataFrame(rounds).to_csv(HERE/'rounds.csv',index=False)
    pd.DataFrame([{k:v for k,v in r.items() if k!='details'} for r in results]).to_csv(HERE/'results.csv',index=False)
    conclusion='Trinn B: '+('bestått forskningskrav' if success else 'ikke bestått')+'. Benchmark beholdes.'
    lines=['# Trinn B – verdi etter planhorisonten','',conclusion,'','| Sesong | A: kontroll | B: sluttverdi | Forskjell |','|---|---:|---:|---:|']
    lines += [f"| {r['season']} | {r['control']:.0f} | {r['candidate']:.0f} | {r['difference']:+.0f} |" for r in results]
    lines += ['', 'Én låst variant. Samme prognoser, H3, to grener, forslag, videreføringspolicy og chipreserver. En standardisert Ridge (alpha 50) anslår diskontert verdi etter horisonten fra tropp, bank, gratisbytter og gjenværende chips. Sluttverdi ved GW38 er null. Bare tidligere avsluttede sesonger brukes ved trening.', '',
        f"Tidsordnet verdi-diagnose på 2023/24: MSE {validation['state_value_mse']:.2f}, mot {validation['time_only_mse']:.2f} med bare sesongtid og {validation['zero_value_mse']:.2f} med null sluttverdi. Dette er overlappende avkastninger fra én lærerbane, ikke uavhengige prøver eller dokumentasjon av kontrafaktisk verdi.", '',
        'Alle 152 kontroll- og kandidatrunder er avregnet på nytt. Lovlige overganger, grenvalg, sluttverdier, prognosehash, treningsgrenser og løsergrenser er kontrollert. Treningens koeffisienter er gjenskapt med en separat lukket Ridge-beregning. Kontrollen fra A gjenbrukes; tre nye utfallsblinde prøver gjenskapte grenene eksakt.', '',
        'Begrensninger: tidligere undersøkte utviklingsår, én lærerbane per treningsår (36 overlappende rader), læreren er benchmark og ikke rollout, og hypotetiske sluttlag kan avvike fra treningsfordelingen. Historiske priser og tilgjengelighet har eksisterende proxyer. Prognosene er uendret og to runder gamle ved terminaltidspunktet. Ingen automatisk oppgradering.', '', '## Ressurser og beslutninger']
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
