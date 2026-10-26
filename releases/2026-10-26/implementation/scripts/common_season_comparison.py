"""Shared independently fitted H8 projection and legal full-season comparison.

All18 predeclared base variants run, regardless of their forecast rankings.
The same low-dimensional, past-OOF projection is fitted separately for every
future offset. H1 is never simply copied across the manager horizon.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,pickle,time,copy,subprocess,concurrent.futures,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import common_model_retest as common
from scripts import common_season_inputs as inputs
from model_lab.common import sha,atomic_json,verify_files,runtime
from model_lab.simulation import backend
from model_lab.manager_learning import Environment,settle
P=inputs.P;D=common.D;B=R/'reports/common_model_retest_2026_10_25_v3';W=R/'reports/common_weather_proxy_2026_10_25'
GATE=R/'reports/season_role_gate_2026_10_24';ROLE=R/'reports/role_h8_manager_2026_10_25'
ID='common-season-comparison-20261025-v1';ARMS=common.ARMS;WEATHER=['weather_actual','weather_noise_1','weather_noise_2'];CONTROLS=['corrected_fixed','operational_fixed'];EVAL=inputs.EVAL;REFITS=common.REFITS;KEY=common.KEY

def qualify(pool,s,at):
    e=pd.read_csv(R/'reports/loan_history_repair_2026_10_25_v3/evidence.csv');e=e[e.classification.eq('documented_outside_PL')];date=pd.to_datetime(e.effective_at,utc=True,format='mixed');pool=pool.copy();pool.loc[pool.code.isin(e.loc[e.season.eq(s)&date.le(at),'code']),'can_buy']=False;pool['forecast_at']=str(at);return pool

def repair_reference():
    assert not (P/'operational_early.csv.gz').exists()
    module=common.module('_common_original_base_repair',R/'reports/fpl_simulator_2026_10_13/benchmark_forecaster.py');base=module.BenchmarkForecaster(R)
    old=common.read(R/'reports/fpl_simulator_2026_10_13/benchmark_audit.json')['gate_calibrations'];base.gates={s:v['weight_rich'] for s,v in old.items()};base.gate_audits=old
    mask=base.periods.season.eq('2024-25')&base.periods.event.eq(15);base.periods.loc[mask,'cutoff']=inputs.EARLY
    pool=pd.read_csv(inputs.CACHE/'2024-25/gw15/pool.csv.gz');pool=qualify(pool,'2024-25',inputs.EARLY)
    f,audit=base.forecast(dict(season='2024-25',round=15,forecast_at=inputs.EARLY,players=pool),8)
    for c in ['calendar_time','max_native_feature_available','max_team_feature_available']:assert pd.Timestamp(audit[c])<inputs.EARLY
    assert all(pd.Timestamp(a['forecast_at'])<inputs.EARLY and pd.Timestamp(a['max_label_available'])<pd.Timestamp(a['forecast_at']) for a in audit['fits'])
    # Original operational seasonal weighting, with original historical zeros.
    saved=sys.modules.get('season_gate');sys.path.insert(0,str(GATE))
    try:
        gate=common.module('season_gate',GATE/'season_gate.py');recipe=common.module('_operational_fixed_feature_recipe',GATE/'experiment.py')
    finally:
        sys.path.pop(0)
        if saved is not None:sys.modules['season_gate']=saved
    cols=['season','fixture','code','native_minutes','native_goals_scored','native_assists','native_clean_sheets','native_saves','target_total_points','kickoff_time'];m=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=cols);m['available']=pd.to_datetime(m.kickoff_time,utc=True)+pd.Timedelta(hours=24);m=m.rename(columns={'native_minutes':'minutes','native_goals_scored':'goals','native_assists':'assists','native_clean_sheets':'clean','native_saves':'saves','target_total_points':'points'});m['played']=m.minutes.gt(0).astype(float);m['sixty']=m.minutes.ge(60).astype(float)
    q=pool[['code','position','price_tenths']].copy();q['season']='2024-25';q['round']=15;q['forecast_at']=inputs.EARLY;q=q.merge(recipe.make_features(q,m),on=KEY,validate='one_to_one').merge(f,on='code',suffixes=('','_base'),validate='one_to_one')
    out=q[KEY+['forecast_at']].copy()
    for j in range(8):
        out[f'xp_{j}']=np.nan
        for pos in ['GK','DEF','MID','FWD']:
            subset=q[q.position.eq(pos)].copy();subset['xp_0']=subset[f'xp_{j}'];model=common.read(GATE/'models'/f'2024-25_gw13_{pos}_h{j+1}_fixed.json');assert model['theta']==[0.,1.,0.];out.loc[subset.index,f'xp_{j}']=gate.predict(subset,model)[0]
    assert np.isfinite(out[[f'xp_{j}' for j in range(8)]]).all().all();out.to_csv(P/'operational_early.csv.gz',index=False)
    atomic_json(P/'operational_early_audit.json',dict(rebuilt=True,not_relabelled_late_forecast=True,forecast_at=str(inputs.EARLY),base_audit=audit,seasonal_models_refit_round=13,source_history=base.source_hash,native_season_features_latest=str(q.latest_feature_available.max()),original_operational_training_preserved=True))
    print('OPERATIONAL EARLY REFERENCE REBUILT',flush=True)

def preflight():
    manifest=common.read(P/'input_view_manifest.json');verify_files(R,manifest['input_hashes']);verify_files(P,manifest['files']);d=pd.read_pickle(P/'pool_features.pkl');raw=pd.read_pickle(D/'training.pkl');schema=common.read(D/'schema.json');assert not d.duplicated(KEY).any()
    t=pd.read_csv(P/'feature_timing.csv.gz');at=pd.to_datetime(t.forecast_at,utc=True)
    for c in ['latest_native','latest_workload','strength_latest','calendar_latest']:
        v=pd.to_datetime(t[c],utc=True,format='mixed');assert (v.isna()|v.lt(at)).all(),c
    same=d[~d.reconstructed].merge(raw[KEY+schema['features']],on=KEY,suffixes=('_view','_table'),validate='one_to_one')
    for c in schema['features']:np.testing.assert_allclose(same[c+'_view'],same[c+'_table'],equal_nan=True,rtol=0,atol=0)
    for folder,prefix in [('fpl_availability_all_seasons_v1','av'),('fpl_set_piece_roles_v1','sp')]:
        q=pd.read_csv(R/'datasets'/folder/'player_round_context.csv.xz',low_memory=False);q=q[q.season.eq('2024-25')&q['round'].eq(15)];assert pd.to_datetime(q[prefix+'_forecast_at'],utc=True).eq(inputs.EARLY).all()
        if prefix=='av':v=pd.to_datetime(q.av_snapshot_at_proxy,utc=True);assert (v.isna()|v.lt(inputs.EARLY)).all()
    assert d[d.season.eq('2024-25')&d['round'].eq(15)].forecast_at.eq(inputs.EARLY).all()
    if not (P/'operational_early.csv.gz').exists():repair_reference()
    # One legality-only probe; no settlement/outcome access.
    q=pd.read_csv(ROLE/'predictions.csv.gz');q=q[q.season.eq('2023-24')&q['round'].eq(1)].set_index('code');p=pd.read_csv(inputs.CACHE/'2023-24/gw01/pool.csv.gz');at=d[d.season.eq('2023-24')&d['round'].eq(1)].forecast_at.iloc[0];p=qualify(p,'2023-24',at);xp=q.reindex(p.code)[[f'control_{j}' for j in range(8)]].to_numpy(float);mod,a=backend(16,40);state=a.engine.initial_state();choice=copy.deepcopy(a.decide(p,xp,state,1)['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};after,choice=a.engine.apply_decision(state,choice,p.to_dict('records'),1);assert len(choice['squad'])==15 and len(a.ledger)<=40
    atomic_json(P/'preflight.json',dict(passed=True,full_pool_rows=len(d),unchanged_common_feature_rows_checked=len(same),reconstructed_rows=int(d.reconstructed.sum()),strict_feature_timestamps=True,early_GW15_rebuilt=True,initial_squad_legal=True,preflight_solver_calls=len(a.ledger),settlements_read=False))
    print('SEASON PREFLIGHT PASSED',len(d),flush=True)

def prepare():
    assert common.read(P/'preflight.json')['passed'];paths=[Path(__file__),R/'scripts/verify_common_seasons.py',R/'scripts/common_season_inputs.py',P/'input_view_manifest.json',P/'pool_features.pkl',P/'feature_timing.csv.gz',P/'preflight.json',P/'operational_early.csv.gz',P/'operational_early_audit.json',B/'proposal.json',D/'manifest.json',D/'schema.json',D/'training.pkl',R/'datasets/fpl_2026_27_best_effort_v1/manifest.json',R/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz',R/'overview/ACTIVE_TEAM_BENCHMARK.json',R/'overview/FORECAST_OBJECTIVES_V1.json',GATE/'predictions.csv.gz',GATE/'prediction_lock.json',GATE/'season_gate.py',ROLE/'predictions.csv.gz',ROLE/'prediction_lock.json',ROLE/'forecast_verification.json',R/'model_lab/simulation.py',R/'model_lab/manager_learning.py',R/'reports/learned_manager_2026_10_15/experiment.py',W/'weather.pkl',W/'weather_manifest.json',R/'scripts/common_weather_proxy.py']
    paths+=list((R/'model_lab/vendor/fpl_rules_v1').glob('*.py'));deps=dict(common.read(P/'input_view_manifest.json')['input_hashes']);deps.update({str(p.relative_to(R)):sha(p) for p in paths})
    spec=dict(id=ID,candidate_id='common_oof_h8_all_families_manager_v1',hypothesis='The newly retested forecast families produce different net season utility under one identical manager after a shared strictly past-OOF horizon projection; improved point error need not imply improved net points.',change='Run all18 locked base variants, both frozen operational and corrected-history fixed-season references, and three separately labelled hindsight-weather proxy scenarios. Fit independent offset0..7 residual Ridge projections from each family\'s saved H1/H3 point and minute forecasts, archived target-offset fixture counts/home/opponent strength and predeadline position/price. All base models frozen. No repeated H1 trajectory.',related_work=['common-model-retest-20261025-v3','role-h8-manager-20261025-v1','season-role-manager-20261024-v1'],dataset_id='fpl_2026_27_best_effort_v1',benchmark_id='fixed_season_h8_adaptive_v1',clock='common_origin_proxy_with_actual_2024_GW15_11UTC_reconstruction',features=dict(parent='fpl_common_training_v1',pool='same archived pool for every arm, dated departure qualification shared',projection='family H1/H3 point/minute forecasts, current and offset fixture exposure, frozen origin-time own/opponent strength, home share, predeadline price and position; no raw role/availability/set-piece reintroduction into removed-feature arms',future='frozen origin features and archived announced future matches only; never future observed player features'),model_parameters=dict(arms=ARMS,controls=CONTROLS,weather_arms=WEATHER,projection='separate residual Ridge per base family and offset; point residual/6; training median/mean/std and all-feature missing indicators; unpenalized intercept; mean-SSE ridge penalty.01',projection_penalty=.01,refits=REFITS,offsets=list(range(8)),base_models_unchanged=True,anchor='H1 for offset0; equal-weight H1/current-fixture and H3/current-three-fixture per-match means times known offset exposure thereafter; unknown exposure1 with missing flag; independent residual heads, not copied H1',known_blank='force0 only for fresh fully bound announced target-round zero fixture count',weather='one actual-weather projection trained, reused with both synthetic-noise base forecasts; hindsight information tier, never eligible for operational promotion'),decision_policy=dict(stage='H8_projection_and_all_full_season_managers',policy='unchanged existing adaptive manager and chips',opening='empty squad,1000 bank, identical tokens/rules',forecast_horizon=8,planning_horizon=3,node_limit=16,max_calls=40,primary_reference='operational_fixed freshly rerun on common qualified pools; corrected_fixed is a second freshly rerun reference',all_arms_run_regardless_forecast_rank=True),seasons=EVAL,resources=dict(maximum_projection_fits=1520,maximum_full_seasons=46,maximum_decisions=1748,parallel_workers=4,threads_per_fit=1,threads_per_solver=1,preflight_decisions=1,preparatory_operational_base_fit_bundles=2),maximum_runs=1,input_hashes=deps,success_criterion='For each causal candidate separately: strictly more net full-season points after hits than BOTH references in EACH of the two seasons. Report each season and equal-season mean; no automatic model/production promotion. Weather proxy scores are optimistic sensitivity only and cannot pass promotion.',stop_rule='Stop affected stage on changed inputs, feature/label time failure, nonfinite forecasts, illegal decision, unknown selected outcome, native solver failure or exceeded resource cap. No outcome-driven parameter change or blind retry.',evaluation_contract=dict(primary_metric='net GW1–38 points minus4 per paid transfer',projection_training='Only earlier OOF forecast origins and concrete offset labels before refit; same eligible row keys per offset across all base variants. Require completed known H3 teacher horizon before refit for ALL variants so actual-weather teacher covariates are also physically past.',prediction_features='No future observed player stats. Opponent state frozen at origin and queried via dated schedule. Missing full-pool rows and earlier deadline rebuilt from past data.',references='Original operational training preserved for real deployed reference; corrected-history fixed-season reference uses audited existing corrected inputs. Both are external system references, not freshly trained325-feature architecture controls. All manager pools, prices, scoring, starts and caps identical; old totals never transferred.',sealing='Trajectories saved and hashed before decisions; each decision saved before selected outcomes are accessed.',evidence_role='Previously inspected2023/24 and2024/25 development seasons; multiple systems and correlated choices, not untouched confirmation.',weather_information='Actual/noisy target-weather scenarios include hindsight information; roster/rule legality does not establish predeadline information realism.',source_limitations='Historical rosters, calendar receipts and statistical vintages remain documented proxies; legality is under frozen reconstructed inputs and rule engine.'))
    atomic_json(P/'proposal.json',spec);print('SEASON PROPOSAL PREPARED',flush=True)

def base_forecasts(weather=False):
    spec=common.read(P/'proposal.json');verify_files(R,spec['input_hashes']);d=pd.read_pickle(P/'pool_features.pkl');schema=common.read(D/'schema.json');out=d[KEY+['forecast_at']].copy();evidence={};tick=time.monotonic()
    if weather:
        lock=common.read(W/'prediction_lock.json');assert lock['saved_before_scoring'];overlay=pd.read_pickle(W/'weather.pkl');d=d.merge(overlay,on=KEY,how='left',validate='one_to_one');names=['weather_actual','weather_noise_1','weather_noise_2'];folder=P/'weather_base';folder.mkdir(exist_ok=False)
    else:names=ARMS;folder=P/'base';folder.mkdir(exist_ok=False)
    for s in inputs.SEASONS:
        loaded={}
        for gw in range(1,39):
            q=d[d.season.eq(s)&d['round'].eq(gw)];ref=max(v for v in REFITS if v<=gw);cache={}
            for h in [1,3]:
                source=(W if weather else B)/'folds'/f'{s}_h{h}_gw{ref:02d}';assert (source/'lock.json').exists()
                if weather and (ref,h) not in loaded:
                    loaded={k:v for k,v in loaded.items() if k[0]==ref}
                    payload=common.read(source/'lock.json');verify_files(source,payload['files']);path=source/'model.pkl'
                    with path.open('rb') as f:bundle=pickle.load(f)
                    evidence[str(path.relative_to(R))]=sha(path);loaded[(ref,h)]=bundle
                elif not weather and (ref,h) not in loaded:
                    loaded={k:v for k,v in loaded.items() if k[0]==ref}
                    audit=pd.read_csv(source/'fit_audit.csv').set_index('arm');bundles={}
                    for name in ARMS:
                        if name=='ridge_extra_50':continue
                        path=source/(name+'.pkl');assert sha(path)==audit.loc[name,'model_sha256']
                        with path.open('rb') as f:bundles[name]=pickle.load(f)
                        evidence[str(path.relative_to(R))]=sha(path)
                    loaded[(ref,h)]=bundles
                if weather:bundle=loaded[(ref,h)]
                else:bundles=loaded[(ref,h)]
                for name in names:
                    if weather:
                        te=q.copy();scenario=name.removeprefix('weather_')
                        if scenario!='actual':
                            for field in ['temperature','wind','rain','cloud','sun']:te[f'proxy_actual_{field}_h{h}']=te[f'proxy_{scenario}_{field}_h{h}']
                        pred,_,_=common.predict_arm(bundle,te)
                    elif name=='ridge_extra_50':pred=(cache[('ridge',h)]+cache[('extra_trees',h)])/2
                    else:pred,_,_=common.predict_arm(bundles[name],q)
                    cache[(name,h)]=pred;out.loc[q.index,f'{name}_p{h}']=pred[:,0];out.loc[q.index,f'{name}_m{h}']=pred[:,1]
            print('BASE PROJECTION INPUTS',s,gw,'weather' if weather else 'causal','seconds',round(time.monotonic()-tick),flush=True)
    columns=[c for c in out if c.endswith(('p1','p3','m1','m3'))];assert np.isfinite(out[columns]).all().all();out.to_pickle(folder/'predictions.pkl');atomic_json(folder/'lock.json',dict(sha256=sha(folder/'predictions.pkl'),source_model_hashes=evidence,rows=len(out),models=names,saved_before_utility_scoring=True));print('BASE FORECASTS SEALED',folder,flush=True)

def design(d,base,j):
    b1=d[base+'_p1'].to_numpy(float);b3=d[base+'_p3'].to_numpy(float);n1=d.u_count_0.to_numpy(float);n3=d.u_count3.to_numpy(float);future=d[f'u_count_{j}'].to_numpy(float)
    a=np.where(np.isfinite(n1)&(n1>0),b1/np.maximum(np.nan_to_num(n1,nan=1),1),np.nan);b=np.where(np.isfinite(n3)&(n3>0),b3/np.maximum(np.nan_to_num(n3,nan=3),1),np.nan)
    denom=np.isfinite(a).astype(float)+np.isfinite(b).astype(float);per=np.divide(np.nan_to_num(a)+np.nan_to_num(b),denom,out=b1.copy(),where=denom>0);anchor=b1 if j==0 else per*np.where(np.isfinite(future),future,1)
    raw={'base_H1':b1/6,'base_H3':b3/18,'base_minute_H1':d[base+'_m1'].to_numpy(float)/90,'base_minute_H3':d[base+'_m3'].to_numpy(float)/270,'current_fixtures':n1/2,'current_H3_fixtures':n3/4,'future_fixtures':future/2,'future_home':d[f'u_home_{j}'].to_numpy(float),'price':d.price_tenths.to_numpy(float)/100,'remaining_rounds':(39-d['round'].to_numpy(float))/38}
    if base not in ['catboost_without_strength','catboost_history']:
        raw.update(own_attack=d.u_own_attack.to_numpy(float),own_concession=d.u_own_concession.to_numpy(float),opponent_attack=d[f'u_opp_attack_{j}'].to_numpy(float),opponent_concession=d[f'u_opp_concession_{j}'].to_numpy(float))
    for pos in ['GK','DEF','MID','FWD']:
        mask=d.position.eq(pos).to_numpy(float);raw['pos_'+pos]=mask;raw['base1_'+pos]=b1/6*mask;raw['base3_'+pos]=b3/18*mask
    return np.column_stack(list(raw.values())),anchor,list(raw)

def transform(raw,model=None):
    missing=~np.isfinite(raw)
    if model is None:
        median=np.array([np.median(c[np.isfinite(c)]) if np.isfinite(c).any() else 0. for c in raw.T]);filled=np.where(missing,median,raw);mean=filled.mean(0);std=filled.std(0);std=np.where(std<1e-8,1.,std);model={'median':median.tolist(),'mean':mean.tolist(),'std':std.tolist()}
    filled=np.where(missing,np.asarray(model['median']),raw);return np.column_stack([np.ones(len(raw)),(filled-np.asarray(model['mean']))/np.asarray(model['std']),missing.astype(float)]),model

def fit_projection(d,base,j):
    raw,anchor,names=design(d,base,j);x,tr=transform(raw);pen=np.eye(x.shape[1])*.01;pen[0,0]=0;y=(d[f'y_{j}'].to_numpy(float)-anchor)/6;beta=np.linalg.solve(x.T@x/len(x)+pen,x.T@y/len(x));return dict(beta=beta.tolist(),transform=tr,raw_names=names,offset=j,penalty=.01,rows=len(d),base_model=base)

def predict_projection(d,base,model):
    raw,anchor,names=design(d,base,model['offset']);assert names==model['raw_names'];x,_=transform(raw,model['transform']);p=anchor+6*x@np.asarray(model['beta']);known_blank=d[f'u_count_{model["offset"]}'].eq(0).to_numpy();p[known_blank]=0.;assert np.isfinite(p).all();return p

def projection_forecasts(weather=False):
    spec=common.read(P/'proposal.json');verify_files(R,spec['input_hashes']);root=P/('weather_base' if weather else 'base');assert sha(root/'predictions.pkl')==common.read(root/'lock.json')['sha256'];d=pd.read_pickle(P/'pool_features.pkl').merge(pd.read_pickle(root/'predictions.pkl'),on=KEY+['forecast_at'],validate='one_to_one');arms=['weather_actual'] if weather else ARMS;outputs={name:[] for name in (WEATHER if weather else ARMS)};audit=[];count=0
    for s in EVAL:
        for gw in range(1,39):
            q=d[d.season.eq(s)&d['round'].eq(gw)].copy();at=q.forecast_at.iloc[0]
            if gw in REFITS:
                models={}
                for j in range(8):
                    complete=d[[f'y_{v}' for v in range(3)]].notna().all(axis=1);weather_at=d[[f'y_at_{v}' for v in range(3)]].max(axis=1)
                    tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&weather_at.lt(at)].copy();assert len(tr)>=1000
                    for base in arms:
                        model=fit_projection(tr,base,j);models[(base,j)]=model;name=f'{s}_gw{gw:02d}_{base}_j{j}.json';path=P/'projection_models'/name;atomic_json(path,model);count+=1;audit.append(dict(season=s,round=gw,base=base,offset=j,cutoff=str(at),rows=len(tr),training_keys_sha256=common.keys_hash(tr),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'y_at_{j}'].max()),max_H3_teacher_weather=str(weather_at.loc[tr.index].max()),model=str(path.relative_to(P)),model_sha256=sha(path)))
                print('PROJECTOR FIT',s,gw,'weather' if weather else 'causal',count,flush=True)
            for base in arms:
                for scenario in (WEATHER if weather else [base]):
                    out=q[KEY+['forecast_at','can_buy']].copy()
                    for j in range(8):out[f'xp_{j}']=predict_projection(q,scenario,models[(base,j)]) if gw+j<=38 else 0.
                    outputs[scenario].append(out)
    group='weather' if weather else 'causal';files={}
    for name,frames in outputs.items():
        for s in EVAL:
            out=pd.concat([q for q in frames if q.season.eq(s).all()],ignore_index=True);assert out['round'].nunique()==38 and not out.duplicated(KEY).any();path=P/'trajectories'/f'{s}_{name}.csv.gz';path.parent.mkdir(exist_ok=True);out.to_csv(path,index=False);files[str(path.relative_to(P))]=sha(path)
    pd.DataFrame(audit).to_csv(P/f'{group}_projection_audit.csv',index=False);atomic_json(P/f'{group}_prediction_lock.json',dict(fits=count,files=files,saved_before_decisions=True,all_offsets_separately_fitted=True,actual_weather_hindsight=weather));print('H8 SEALED',group,count,flush=True)

def reference_trajectories():
    early=pd.read_csv(P/'operational_early.csv.gz');corrected=pd.read_csv(ROLE/'predictions.csv.gz');original=pd.read_csv(GATE/'predictions.csv.gz');files={};all_meta=pd.read_pickle(P/'pool_features.pkl')
    for s in EVAL:
        for arm in CONTROLS:
            parts=[]
            for gw in range(1,39):
                meta=all_meta[all_meta.season.eq(s)&all_meta['round'].eq(gw)];at=meta.forecast_at.iloc[0]
                source=(original if arm=='operational_fixed' else corrected);q=source[source.season.eq(s)&source['round'].eq(gw)].copy();prefix='fixed' if arm=='operational_fixed' else 'control'
                out=meta[KEY+['forecast_at','can_buy']].copy();q=q.set_index('code')
                for j in range(8):out[f'xp_{j}']=out.code.map(q[f'{prefix}_{j}']) if gw+j<=38 else 0.
                if arm=='operational_fixed' and (s,gw)==('2024-25',15):
                    p=early.set_index('code')
                    for j in range(8):out[f'xp_{j}']=out.code.map(p[f'xp_{j}'])
                else:assert pd.to_datetime(q.forecast_at,utc=True).eq(at).all()
                assert np.isfinite(out[[f'xp_{j}' for j in range(min(8,39-gw))]]).all().all();parts.append(out)
            out=pd.concat(parts,ignore_index=True);path=P/'trajectories'/f'{s}_{arm}.csv.gz';path.parent.mkdir(exist_ok=True);out.to_csv(path,index=False);files[str(path.relative_to(P))]=sha(path)
    atomic_json(P/'reference_prediction_lock.json',dict(files=files,original_early_origin_rebuilt=True,old_season_scores_reused=False));print('REFERENCE TRAJECTORIES SEALED',flush=True)

def manager(season,arm):
    spec=common.read(P/'proposal.json');verify_files(R,spec['input_hashes']);assert season in EVAL and arm in ARMS+CONTROLS+WEATHER
    root='weather' if arm in WEATHER else 'reference' if arm in CONTROLS else 'causal';lock=common.read(P/f'{root}_prediction_lock.json');name=f'trajectories/{season}_{arm}.csv.gz';assert sha(P/name)==lock['files'][name];pred=pd.read_csv(P/name).set_index(['round','code']);env=Environment();folder=P/'manager'/f'{season}_{arm}';folder.mkdir(parents=True,exist_ok=False);atomic_json(folder/'started.json',dict(runtime=runtime(),forecast_sha256=sha(P/name),information_tier='hindsight_weather_proxy' if arm in WEATHER else 'predeadline_proxy'))
    _,initial=backend(16,40);state=initial.engine.initial_state();net=[];hits=[];tick=time.monotonic()
    for gw in range(1,39):
        pool,_,manifest,_=env.inputs(season,gw);at=inputs.EARLY if (season,gw)==('2024-25',15) else pd.Timestamp(manifest['forecast_at']);pool=qualify(pool,season,at)
        for col in ['price_available_at','position_available_at','club_available_at']:assert pd.to_datetime(pool[col],utc=True).lt(at).all()
        q=pred.loc[gw].reindex(pool.code);assert pd.to_datetime(q.forecast_at,utc=True).eq(at).all();assert q.can_buy.tolist()==pool.can_buy.tolist();xp=q[[f'xp_{j}' for j in range(min(8,39-gw))]].to_numpy(float);assert np.isfinite(xp).all();mod,adapter=backend(16,40);choice=copy.deepcopy(adapter.decide(pool,xp,state,gw)['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};after,choice=adapter.engine.apply_decision(state,choice,pool.to_dict('records'),gw)
        atomic_json(folder/f'gw{gw:02d}.decision.json',mod.clean(dict(season=season,round=gw,arm=arm,state_before=state,state_after=after,choice=choice,forecast_at=str(at),solver_calls=adapter.ledger,outcomes_read=False,forecast_input_sha256=hashlib.sha256(xp.tobytes()).hexdigest())))
        outcomes,settlement,n=settle(adapter,env,season,gw,dict(choice=choice),pool);atomic_json(folder/f'gw{gw:02d}.settlement.json',mod.clean(dict(net=n,hits=4*choice['paid'],outcomes=outcomes,settlement=settlement)));net.append(n);hits.append(4*choice['paid']);state=after
        if gw%8==0:print('MANAGER',season,arm,gw,'seconds',round(time.monotonic()-tick),flush=True)
    result=dict(season=season,arm=arm,net=float(sum(net)),hits=int(sum(hits)),rounds=38,seconds=time.monotonic()-tick,information_tier='hindsight_weather_proxy' if arm in WEATHER else 'predeadline_proxy');atomic_json(folder/'summary.json',result);print('SEASON COMPLETE',json.dumps(result),flush=True)

def run_managers(weather=False):
    names=WEATHER if weather else ARMS+CONTROLS;jobs=[(s,a) for s in EVAL for a in names]
    def run(job):
        s,a=job;path=P/'logs'/f'manager_{s}_{a}.log';path.parent.mkdir(exist_ok=True)
        with path.open('x') as f:subprocess.run([sys.executable,str(Path(__file__).resolve()),'manager',s,a],cwd=R,env=os.environ.copy(),stdout=f,stderr=subprocess.STDOUT,check=True)
        return job
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,job in enumerate(pool.map(run,jobs),1):print('FULL SEASON',i,'/',len(jobs),*job,flush=True)

if __name__=='__main__':
    command=sys.argv[1]
    if command=='base':base_forecasts(False)
    elif command=='weather_base':base_forecasts(True)
    elif command=='project':projection_forecasts(False)
    elif command=='weather_project':projection_forecasts(True)
    elif command=='references':reference_trajectories()
    elif command=='managers':run_managers(False)
    elif command=='weather_managers':run_managers(True)
    else:globals()[command](*sys.argv[2:])
