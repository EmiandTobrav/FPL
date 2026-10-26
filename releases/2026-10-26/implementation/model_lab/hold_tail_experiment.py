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
from . import manager_policy as base, rollout_policy as rollout, hold_tail_value as terminal

HERE=ROOT/'reports/hold_tail_2026_10_16'
A=ROOT/'reports/rollout_2026_10_15'
ID='hold-tail-h3-20261016-v1'
SEASONS=('2023-24','2024-25')

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
    if (HERE/'protocol.json').exists():raise ValueError('Already frozen')
    env=Environment();probes=[]
    for season,gw in [('2023-24',1),('2023-24',19),('2024-25',38)]:
        lock=read(A/'runs'/season/f'gw{gw:02d}.decision.json');pool,xp,m,h=env.inputs(season,gw);_,ad=backend(16,200)
        out=rollout.choose(ad,pool,xp,h,env.e.state_json(lock['state_before']),gw)
        for key in ('options','branches','selected_index','shortlist'):
            if env.helpers.clean(out[key])!=lock[key]:raise ValueError('Control differs: '+key)
        probes.append(dict(season=season,gw=gw,forecast_columns=xp.shape[1],exact_control=True,outcomes_read=False))
    atomic_json(HERE/'preflight.json',dict(status='pass',probes=probes))
    files=dict(read(A/'protocol.json')['files']);verify_files(ROOT,files)
    paths=[ROOT/'model_lab/hold_tail_value.py',ROOT/'model_lab/hold_tail_experiment.py',ROOT/'model_lab/tests/test_hold_tail.py',HERE/'preflight.json',A/'audit.json',ROOT/'reports/paired_terminal_2026_10_16_attempt2/audit.json']+list((A/'runs').rglob('*.json'))
    files.update({str(p.relative_to(ROOT)):sha(p) for p in paths})
    protocol=dict(id=ID,created_at_utc=stamp(),files=files,runtime=runtime(),seasons=list(SEASONS),
        authorization='User requests another method of calculating value after the planning horizon; fixed-forecast context retained.',
        intervention='Unchanged A H3 width2 branches; add direct discounted value of retained squad using current-origin forecast columns3..7. Best legal XI and captain each future round; no transfers, chips, bank or FT valuation in tail. Existing within-H3 reserves unchanged.',
        formula='V=sum(j=3..min(7,38-gw), 0.9^(j-3)*(XI_xp_j+captain_xp_j)); score=original H3 score+0.9^3*V. Truncate at season end and forecast availability. Use restored squad after FH. No value beyond H8, no fit or constant extrapolation.',
        distinction='Different terminal evaluator, not full H8 action search. Uses more columns of same forecast files than zero-terminal A; no input file changes or new forecasts.',
        primary_control='A bounded_rollout_h3_v1; exact archived episodes and current-origin branch parity probes.',
        resources=dict(configurations=1,new_full_seasons=2,new_decisions=76,forecast_fits=0,value_fits=0,node_limit=16,total_call_cap=200,per_proposal_call_cap=40,threads=1,extra_solver_calls_for_tail=0),
        success='Strict positive net full-season point difference vs A in BOTH 2023-24 and 2024-25. Research only, no promotion.',
        stop='Stop on input/runtime mismatch, invalid transition, missing selected outcome, solver failure or cap violation. No tuning or silent retry. Preserve any failure and document a separate technical amendment before repairs.',
        limitations='Previously studied years. Fixed squad is an approximation; no tail autosubs uncertainty, transfer adaptation or chip exercise. Bank/FT/chip terminal utility omitted. Existing calendar/price/availability proxies. Not evidence of optimal full-season terminal value.')
    atomic_json(HERE/'protocol.json',protocol)
    spec=dict(id=ID,candidate_id='hold_tail_h3_v1',dataset_id='fpl_2026_27_best_effort_v1',benchmark_id=BENCHMARK,clock='operational_proxy_v1',features='unchanged archived current-origin H1-H8 forecasts',hypothesis='Direkte H4-H8-verdi av beholdt tropp gir flere netto sesongpoeng enn A med samme H3-handlingssøk.',change=protocol['intervention'],related_work=['rollout-h3-20261015-v1','terminal-value-h3-20261016-v1','paired-terminal-h3-20261016-v2'],input_hashes={**files,str((HERE/'protocol.json').relative_to(ROOT)):sha(HERE/'protocol.json')},model_parameters=dict(fits=0,discount=.9,tail_max_column=7),decision_policy=dict(action_horizon=3,branch_width=2,tail_policy='retain squad; select XI+captain'),seasons=list(SEASONS),resources=protocol['resources'],maximum_runs=2,success_criterion=protocol['success'],stop_rule=protocol['stop'])
    from scripts.research import validate,exclusive,RECORDS,refresh
    fp=validate(spec);spec.update(fingerprint=fp,registered_at_utc=stamp());dest=RECORDS/(fp+'.proposal.json');exclusive(dest,spec)
    atomic_json(HERE/'registration.json',dict(fingerprint=fp,proposal=str(dest.relative_to(ROOT))));refresh();print('Registered',ID,flush=True)


def run():
    bound();atomic_json(HERE/'started.json',dict(at_utc=stamp(),protocol_sha256=sha(HERE/'protocol.json')))
    env=Environment()
    for season in SEASONS:
        _,initial=backend();state=initial.engine.initial_state();logs=[];start=time.monotonic()
        for gw in range(1,39):
            pool,xp,manifest,history=env.inputs(season,gw);_,adapter=backend(16,200);counts=[]
            def limited(*args,**kwargs):
                before=len(adapter.ledger);options=base.proposals(*args,**kwargs);n=len(adapter.ledger)-before
                if n>40: raise ValueError('Per-proposal cap')
                counts.append(n);return options
            chosen=rollout.choose(adapter,pool,xp,history,state,gw,official_blank=bool(manifest.get('official_all_blank_forced_wait')),proposals=limited)
            chosen=terminal.attach(chosen,pool,xp,env.e.state_json,gw)
            lock=env.helpers.clean(dict(**chosen,season=season,gw=gw,state_before=state,forecast_at=manifest['forecast_at'],
                forecast_array_sha256=digest(xp.tolist()),terminal_method=ID,solver_calls=adapter.ledger,proposal_call_counts=counts,outcomes_read=False))
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
    rounds=[];results=[];checks=0
    def check_option(o,p,x,h,s,g):
        choice=copy.deepcopy(o['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()}
        after,legal=rules.apply_decision(s,choice,p.to_dict('records'),g)
        assert after==env.e.state_json(o['after']) and base.identity(legal)==o['id']
        f=base.encode(p,x,h,s,after,legal,rules,g)
        reserve=0. if legal['chip'] is None else adapter.policy.reserve_value(legal['chip'],g)
        np.testing.assert_allclose(f,o['features'],rtol=0,atol=1e-10)
        np.testing.assert_allclose(100*f[9]+.9*100*f[14]+.81*100*f[15]-reserve,o['base_score'],atol=1e-9)
        return after
    for season in SEASONS:
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
                        # Independent direct summation, legal XI/captain recomputed each tail round.
                        expected=[];v=0.
                        for offset in range(horizon,min(8,xp.shape[1],39-gw)):
                            values=dict(zip(map(int,pool.pid),map(float,xp[:,offset])))
                            lineup=base.lineup(list(current['owned']),pool,values)
                            points=sum(values[i] for i in lineup['starters'])+values[lineup['captain']]
                            discount=.9**(offset-horizon);v+=discount*points
                            expected.append(dict(gw=gw+offset,forecast_column=offset,lineup=lineup,xp=float(points),discount=discount))
                        assert b['tail_rows']==env.helpers.clean(expected)
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
                    assert pure_index==lock['zero_terminal_selected_index'] and lock['terminal_method']==ID
                    different=pure_index!=lock['selected_index'];changed+=different
                    rounds.append(dict(season=season,gw=gw,changed_from_same_state_A=different,net_points=net,chip=lock['selected']['choice']['chip'],hits=4*lock['selected']['choice']['paid'],calls=len(lock['solver_calls'])))
                c=lock['selected']['choice'];hits+=4*c['paid']
                if c['chip']: chips[c['chip']].append(gw)
                total+=net;state=env.e.state_json(lock['selected']['after']);checks+=1
            assert total==read(folder/'summary.json')['net_points']
            totals[label]=dict(net_points=total,hits=hits,chips=chips,unused_chips={half:[c for c in base.CHIPS if c not in state['used_chips'][half]] for half in ('1','2')},final_bank=state['bank'],final_ft=state['ft'],changed=changed,**{k:v for k,v in read(folder/'summary.json').items() if k in ('seconds','calls')})
        results.append(dict(season=season,control=totals['control']['net_points'],candidate=totals['candidate']['net_points'],difference=totals['candidate']['net_points']-totals['control']['net_points'],details=totals))
    validation=dict(method='direct retained-squad H4-H8 sum',forecast_fits=0,value_fits=0,tail_choices='legal XI and captain only',new_transfer_or_chip_search=False)
    success=all(r['difference']>0 for r in results)
    atomic_json(HERE/'audit.json',dict(status='pass',rounds_recomputed=checks,tail_values_independently_recomputed=True,value_validation=validation,results=results,pilot_success=success,forecast_fits=0))
    pd.DataFrame(rounds).to_csv(HERE/'rounds.csv',index=False)
    pd.DataFrame([{k:v for k,v in r.items() if k!='details'} for r in results]).to_csv(HERE/'results.csv',index=False)
    conclusion='Direkte sluttverdi: '+('bestått forskningskrav' if success else 'ikke bestått')+'. Benchmark beholdes.'
    lines=['# Direkte sluttverdi fra fast tropp og H4–H8-prognoser','',conclusion,'','| Sesong | A: kontroll | B3: fast tropp etter H3 | Forskjell |','|---|---:|---:|---:|']
    lines += [f"| {r['season']} | {r['control']:.0f} | {r['candidate']:.0f} | {r['difference']:+.0f} |" for r in results]
    lines += ['', 'Én forhåndsregistrert variant uten læring. Samme H3-rollout, to grener, prognoser, forslag, chipreserver og løsergrenser som A. Etter H3 beholdes den gjenstående troppen. Beste lovlige ellever og kaptein beregnes fra dagens lagrede prognoser for rundene H4–H8. Diskonterte poeng summeres; ingen nye bytter eller chipvalg etter H3. Free Hit bruker tilbakeført tropp. Ingen ekstrapolering etter H8 eller sesongslutt.', '',
        'Dette er en terminal approksimasjon med fast tropp, ikke en full H8-planlegger. Den bruker flere av de allerede tilgjengelige prognosekolonnene enn A; prognosefilene er uendret. Bank, gratisbytter og ubrukte chips får ingen ny direkte sluttverdi. Ingen prognose- eller verdimodeller trenes.', '',
        'Alle 152 kontroll- og kandidatrunder er avregnet på nytt. Lovlige overganger, alle H3-grener, haleverdier, prognosehash og løsergrenser er kontrollert. Kontrollens forslag og grener gjenskapes eksakt i tre utfallsblinde prøver. Kandidaten bruker ingen ekstra MILP-kall for sluttverdien; ulike sesongtilstander kan likevel gi ulikt antall totale kall.', '',
        'Begrensninger: tidligere studerte utviklingsår, deterministiske punktprognoser, fast tropp etter H3 og ingen direkte ressursverdi. Faktiske senere bytter vil kunne endre verdien. Kalender, priser og tilgjengelighet følger tidligere proxyer. Ingen automatisk oppgradering.', '', '## Ressurser og beslutninger']
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
