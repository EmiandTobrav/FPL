"""Shared hard availability constraints, using only qualified predeadline facts."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,copy,hashlib,subprocess,concurrent.futures
from pathlib import Path
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import matched_season_retest_v5 as m
OLD=m.P;P=R/'reports/matched_season_retest_2026_10_26_v8';ID='matched-season-retest-20261026-v8';V6=R/'reports/matched_season_retest_2026_10_26_v6';VENDOR=R/'model_lab/vendor/fpl_rules_v1';m.P=P
original_pool=m.pool

def build_backend():
    folder=P/'policy_backend';folder.mkdir()
    for name in ['engine.py','controlled_policy_v1.py','policy.py','planner.py','initial_optimizer.py']:(folder/name).write_bytes((VENDOR/name).read_bytes())
    path=folder/'policy.py';s=path.read_text();needle='def select_plan(p,xp,state,gw,fixed,chip=None):\n';addition='''    p=p.copy()
    origin=int(p.eligibility_origin_round.iloc[0]);offset=gw-origin
    if not 0<=offset<8:raise ValueError('Availability origin mismatch')
    for j in range(8):p[f'eligible_start_{j}']=p[f'can_start_{offset+j}'] if offset+j<8 else True
''';assert needle in s;s=s.replace(needle,needle+addition);path.write_text(s)
    path=folder/'planner.py';s=path.read_text();needle='        upper[x]=p.can_buy.to_numpy()|own\n';addition='''        eligible=p[f'eligible_start_{t}'].to_numpy(dtype=bool)
        upper[l]=eligible;upper[c]=eligible
        if chip=='bench_boost':upper[x]*=eligible
''';assert needle in s;s=s.replace(needle,needle+addition)
    helper='''def _can_keep_with_availability(p,chips):
    for t,chip in enumerate(chips):
        eligible=p[f'eligible_start_{t}'].to_numpy(dtype=bool)
        if chip=='bench_boost' and not eligible.all():return False
        counts=p[eligible].pos.value_counts().to_dict()
        if counts.get(1,0)<1:return False
        possible=any(1<=10-d-m<=min(3,counts.get(4,0)) for d in range(3,min(5,counts.get(2,0))+1) for m in range(2,min(5,counts.get(3,0))+1))
        if not possible:return False
    return True

''';needle='def choose(pool,forecast,owned,bank,ft,chips):';assert needle in s;s=s.replace(needle,helper+needle);s=s.replace("if over and chips[0] is None:","if over and chips[0] is None and _can_keep_with_availability(p[p.pid.isin(owned)],chips):");path.write_text(s)
    path=folder/'initial_optimizer.py';s=path.read_text();needle='    upper[:n]=np.where(p.can_buy.to_numpy()|own,1,0)\n';addition='''    eligible=p['eligible_start_0'].to_numpy(dtype=bool)
    upper[n:2*n]=eligible;upper[2*n:3*n]=eligible
    if chip=='bench_boost':upper[:n]*=eligible
''';assert needle in s;s=s.replace(needle,needle+addition);path.write_text(s)
    m.atomic_json(P/'policy_backend_hashes.json',{p.name:m.sha(p) for p in folder.iterdir()})

def prepare():
    P.mkdir(exist_ok=False);parent=m.common.read(OLD/'delivery.json');m.verify_files(R,parent['files']);old_inputs=m.common.read(OLD/'inputs.json');m.verify_files(R,old_inputs['input_hashes']);m.verify_files(OLD,old_inputs['files']);d=pd.read_pickle(OLD/'pool_features.pkl');outside=pd.read_csv(V6/'player_eligibility.csv.gz');statuspath=R/'datasets/fpl_availability_all_seasons_v1/source_player_status.csv.gz';st=pd.read_csv(statuspath,low_memory=False);st=st[st.season.isin(m.SEASONS)];st['snapshot']=pd.to_datetime(st.snapshot_at_proxy,utc=True,format='mixed');st['origin']=pd.to_datetime(st.forecast_at,utc=True,format='mixed');st=st[st.known&st.snapshot.lt(st.origin)&(st.origin-st.snapshot).le(pd.Timedelta(hours=24))];assert not st.duplicated(m.KEY).any()
    q=d[m.KEY+['forecast_at','can_buy','teacher_eligible']].merge(outside[m.KEY+['known_outside_PL','departure_available_at']],on=m.KEY,validate='one_to_one').merge(st[m.KEY+['status','chance','chance_binding','snapshot','origin','news_added','reason']],on=m.KEY,how='left',validate='one_to_one');at=pd.to_datetime(q.forecast_at,utc=True);assert (q.origin.isna()|q.origin.eq(at)).all();assert (q.snapshot.isna()|q.snapshot.lt(at)).all();bound=q.chance_binding.isin(['next','this']);q['known_departed']=q.known_outside_PL|q.status.eq('u')|(q.status.eq('n')&q.reason.eq('transfer_or_loan'));q['confirmed_out_current']=q.known_departed|(bound&q.chance.eq(0));q['model_can_buy']=q.can_buy&~q.confirmed_out_current
    for j in range(8):q[f'can_start_{j}']=~q.known_departed&(~q.confirmed_out_current if j==0 else True)
    q.to_csv(P/'availability.csv.gz',index=False);build_backend();deps=dict(old_inputs['input_hashes']);paths=[Path(__file__),OLD/'inputs.json',OLD/'proposal.json',OLD/'prediction_lock.json',OLD/'delivery.json',OLD/'eligibility_repair_diagnosis.json',OLD/'post_departure_training_check.json',V6/'player_eligibility.csv.gz',statuspath,R/'datasets/fpl_availability_all_seasons_v1/manifest.json',R/'datasets/fpl_availability_all_seasons_v1/build.py',R/'overview/FORECAST_OBJECTIVES_V1.json',P/'availability.csv.gz',P/'policy_backend_hashes.json']+list((P/'policy_backend').iterdir())
    for a in m.ARMS:paths.append(OLD/f'{a}.csv.gz')
    deps.update({str(p.relative_to(R)):m.sha(p) for p in paths})
    for name in ['training.pkl','pool_features.pkl','head_data.pkl','reference_features.pkl','origins.pkl','calendars.pkl','metadata.pkl','comparability.csv','feature_coverage.csv','calendar.csv','origins.csv','head_audit.csv','rolling_update_summary.csv','review_criteria.json']:os.link(OLD/name,P/name)
    m.atomic_json(P/'inputs.json',dict(input_hashes=deps,files={n:m.sha(P/n) for n in ['training.pkl','pool_features.pkl','origins.pkl','calendars.pkl','metadata.pkl','availability.csv.gz','review_criteria.json']}));spec=m.common.read(OLD/'registered_proposal.json');spec.update(id=ID,candidate_id='component_matched_calendar_hard_current_availability_v8',hypothesis='A fair common-data comparison must prevent buying, starting or captaining a player whose unavailability is confirmed before the deadline. Preserve valid pre-departure history and genuine PL injury-zero outcomes, exclude artificial post-departure performance rows, and enforce availability for both packages independently of learned scores.',change='Technicalv8: preserve optional chip argument in the engine safety callback; v7 stopped in legality preflight before any season decision/score. Same rule and parameters. User-requested common hard-availability layer. V5 source correction removed ghost history but its reference retained Kane37rounds after known departure. All learned weights and four-round updating remain byte-identical. Known departure gives zero all8 forecasts; round-bound confirmed0 chance gives zero H1, no new purchase and no starter/captain/vice. Unknown/doubtful without explicit0 stays eligible. Injured existing holdings may remain benched pending legal transfers. Benchboost requires15 eligible scorers. Private policy copies add variable upper bounds; engine/game rules and all other objectives/resources unchanged. Six fresh episodes, no tuning.',related_work=['matched-season-retest-20261026-v7',m.common.read(OLD/'proposal.json')['id'],'component-confirmation-20261025-v2'],input_hashes=deps,resources=dict(new_model_fits=0,reused_component_packages=80,reused_native_bundles=44,reused_projection_heads=240,reused_positional_heads=960,maximum_season_attempts=6,maximum_decisions=228,legality_preflight_decisions=2,workers=4,threads=1),decision_policy=dict(policy='same frozen adaptive objectives plus shared user-required hard eligibility bounds',opening='empty1000bank1FT',horizon=8,planning=3,node_request=15,node_actual_cap=16,max_calls=40,benchboost='all15 must be currently eligible',temporary_absence='current round only; later projected availability not hard banned; purchase eligibility held at origin until next update'),evaluation_contract=dict(primary_metric='net full-season points after hits',success_gate='unchanged strict component win in all3 seasons; six complete; all checks pass',forecast_objectives_id='forecast-objectives-v1-20261015',source_limits='same known statistical/calendar/market proxies; qualified FPL status snapshots must precede actual deadline, age<=24h, chance target round bound',evidence_role='retrospective development and explicit general eligibility bug repair after observed v5, no model selection/tuning',training='0 qualified rows after departure; valid pre-departure history retained; genuine injury/suspension zeros insidePL remain valid teacher data'),maximum_runs=1);m.atomic_json(P/'proposal.json',spec);m.status('availability_prepared');print('PREPARED HARD AVAILABILITY',q.groupby('season')[['known_departed','confirmed_out_current']].sum().to_string(),flush=True)

_availability=None
def availability():
    global _availability
    if _availability is None:_availability=pd.read_csv(P/'availability.csv.gz')
    return _availability
def eligible_pool(s,g):
    p=original_pool(s,g);a=availability();q=a[a.season.eq(s)&a['round'].eq(g)].set_index('code').reindex(p.code);assert q.model_can_buy.notna().all();p['can_buy']=q.model_can_buy.to_numpy(bool);p['eligibility_origin_round']=g
    for j in range(8):p[f'can_start_{j}']=q[f'can_start_{j}'].to_numpy(bool)
    return p

def solver():
    hashes=m.common.read(P/'policy_backend_hashes.json');m.verify_files(P/'policy_backend',hashes);mod=m.common.module('_hard_availability_controlled_policy',P/'policy_backend/controlled_policy_v1.py');mod.OLD=P/'policy_backend';mod.EXPECTED={k:hashes[k] for k in ['engine.py','planner.py','initial_optimizer.py','policy.py']};a=mod.ControlledPolicy(mod.Budget(node_limit=16,max_calls=40));a.options['node_limit']=15;original=a.engine.apply_decision
    def checked(state,choice,records,gw=None,chip=None):
        byid={int(r['pid']):r for r in records};assert all(byid[int(i)]['can_start_0'] for i in choice['starters']);assert byid[int(choice['captain'])]['can_start_0'] and byid[int(choice['vice'])]['can_start_0'];assert all(byid[int(i)]['can_buy'] for i in choice['incoming'])
        if (chip if chip is not None else choice.get('chip'))=='bench_boost':assert all(byid[int(i)]['can_start_0'] for i in choice['squad'])
        return original(state,choice,records,gw,chip)
    a.engine.apply_decision=checked;return mod,a

def configure():m.pool=eligible_pool;m.solver=solver

def forecasts():
    m.check_inputs();files={};a=availability();assert (pd.to_datetime(a.snapshot,utc=True).isna()|pd.to_datetime(a.snapshot,utc=True).lt(pd.to_datetime(a.forecast_at,utc=True))).all()
    for arm in m.ARMS:
        q=pd.read_csv(OLD/f'{arm}.csv.gz');z=q.merge(a[m.KEY+['known_departed','confirmed_out_current','model_can_buy']],on=m.KEY,validate='one_to_one');q['can_buy']=z.model_can_buy
        for j in range(8):
            mask=z.known_departed|(z.confirmed_out_current if j==0 else False);q.loc[mask,f'xp_{j}']=0.;np.testing.assert_allclose(q.loc[~mask,f'xp_{j}'],z.loc[~mask,f'xp_{j}'],rtol=0,atol=0);assert q.loc[mask,f'xp_{j}'].eq(0).all()
        q.to_csv(P/f'{arm}.csv.gz',index=False);files[f'{arm}.csv.gz']=m.sha(P/f'{arm}.csv.gz')
    files['availability.csv.gz']=m.sha(P/'availability.csv.gz');m.atomic_json(P/'prediction_lock.json',dict(files=files,saved_before_manager=True,learned_weights_unchanged=True,common_hard_unavailability_postprocessing=True));m.atomic_json(P/'forecast_verification.json',dict(passed=True,qualified_status_before_deadline=True,round_bound_zero_chance_only=True,parent_223124_base_values_and1200heads_verified=True,all_unaffected_forecasts_identical=True,post_departure_training_rows=0));m.status('availability_forecasts_verified')

def preflight():
    configure();m.check_inputs();s='2023-24';g=10;p=eligible_pool(s,g);old=m.common.read(OLD/f'manager/{s}_operational_matched/gw{g:02d}.decision.json');state=old['state_before'];state['owned']={int(k):v for k,v in state['owned'].items()};f=pd.read_csv(P/'operational_matched.csv.gz');f=f[f.season.eq(s)&f['round'].eq(g)].set_index('code').reindex(p.code);xp=f[[f'xp_{j}' for j in range(8)]].to_numpy(float);blocked=~p.can_start_0.to_numpy();assert blocked.any() and 78830 in state['owned'];xp[blocked]=10000.;mod,a=solver();choice=copy.deepcopy(a.decide(p,xp,state,g)['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};after,choice=a.engine.apply_decision(state,choice,p.to_dict('records'),g);assert 78830 not in choice['starters'] and 78830 not in [choice['captain'],choice['vice']]
    # Also prove the opening selector cannot purchase any blocked player.
    mod,b=solver();empty=b.engine.initial_state();p1=eligible_pool('2023-24',1);x=np.ones((len(p1),8));x[~p1.can_start_0.to_numpy()]=10000.;c=copy.deepcopy(b.decide(p1,x,empty,1)['choice']);c['prices']={int(k):v for k,v in c['prices'].items()};b.engine.apply_decision(empty,c,p1.to_dict('records'),1);m.atomic_json(P/'preflight.json',dict(passed=True,hostile_high_forecasts_cannot_override_hard_bounds=True,owned_Kane_not_startable=True,initial_purchases_of_confirmed_out_impossible=True,outcomes_read=False,solver_calls=[len(a.ledger),len(b.ledger)]));print('HARD ELIGIBILITY PREFLIGHT PASSED',flush=True)

def manager(s,arm):configure();assert m.common.read(P/'preflight.json')['passed'];m.manager(s,arm)
def managers():
    m.status('simulating');(P/'logs').mkdir(exist_ok=True)
    def run(args):
        s,a=args
        with (P/'logs'/f'manager_{s}_{a}.log').open('x') as f:r=subprocess.run([sys.executable,str(Path(__file__).resolve()),'manager',s,a],cwd=R,env=os.environ.copy(),stdout=f,stderr=subprocess.STDOUT)
        print('HARD AVAILABILITY MANAGER',s,a,r.returncode,flush=True);return dict(season=s,arm=a,exit_code=r.returncode)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(run,[(s,a) for s in m.EVAL for a in m.ARMS]))
    m.atomic_json(P/'manager_attempts.json',results)

def report():
    configure();from scripts import review_matched_season_retest_v5 as review
    review.P=P;pd.DataFrame.to_markdown=lambda self,index=True,**kw:review.table(self,index=index);m.report();review.metrics();m.atomic_json(P/'independent_forecast_verification.json',dict(passed=True,common_availability_upper_bounds=True,all_decisions_replayed_with_predeadline_availability_checks=True,parent_base_and_heads_unchanged=True));score=pd.read_csv(P/'scores.csv');wide=score.pivot(index='season',columns='arm',values='net');wide['delta']=wide.component-wide.operational_matched;complete=bool(score.complete.all());gate=bool(complete and wide.delta.gt(0).all());m.atomic_json(P/'delivery.json',dict(research_gate_passed=gate,complete=complete,files={str(p.relative_to(R)):m.sha(p) for p in [P/'scores.csv',P/'verification.json',P/'forecast_verification.json',P/'independent_forecast_verification.json',P/'forecast_metrics.csv',P/'preflight.json',P/'availability.csv.gz',P/'policy_backend_hashes.json']}));print(wide.to_string(),flush=True);print('CORRECTED RESEARCH GATE',gate,flush=True)

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
