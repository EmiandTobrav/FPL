"""Fixed component-v-active 2025/26 confirmation, with separate no-chip stress.
Reuse locked out-of-fold base models; generate new H8 heads and new manager
episodes. No original evidence, operational selection or live forecast changed.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,pickle,copy,hashlib,subprocess,concurrent.futures,time
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import common_season_comparison as method
from scripts import common_model_retest as common
from scripts import component_confirmation_inputs as inputs
from model_lab.common import atomic_json,sha,verify_files,runtime
from model_lab.simulation import backend
from model_lab.manager_learning import Environment,settle
from model_lab import fixed_season_forecaster as fixed
P=inputs.P.with_name(inputs.P.name+'_v2');OLD=method.P;B=method.B;D=method.D;C=inputs.CACHE;KEY=common.KEY
S='2025-26';ID='component-confirmation-20261025-v2';BENCH='fixture_full_h3_adaptive_tc_harmonized_causal_v1'
ARMS=['component','operational_fixed'];SETTINGS=['adaptive_chips','no_chips']

def prepare():
    verify_files(R,common.read(P/'input_view_manifest.json')['input_hashes']);verify_files(P,common.read(P/'input_view_manifest.json')['files']);d=pd.read_pickle(P/'pool_features.pkl');assert len(d['round'].unique())==38
    rows=[];deps=dict(common.read(P/'input_view_manifest.json')['input_hashes'])
    for gw in range(1,39):
        folder=C/S/f'gw{gw:02d}';m=common.read(folder/'manifest.json');bm=common.read(folder/'benchmark_manifest.json');verify_files(folder,m['files']);verify_files(folder,bm['files']);verify_files(R,bm['implementation']);q=pd.read_csv(folder/'pool.csv.gz');at=pd.Timestamp(m['forecast_at']);assert pd.to_datetime(q.forecast_at,utc=True).eq(at).all();assert bm['shared_pool_sha256']==sha(folder/'pool.csv.gz')
        for col in ['price_available_at','position_available_at','club_available_at']:assert pd.to_datetime(q[col],utc=True).lt(at).all()
        audit=common.read(folder/(BENCH+'.json'))
        for col in ['max_native_feature_available','max_team_feature_available']:assert pd.Timestamp(audit[col])<at
        for a in audit['fits']:assert pd.Timestamp(a['max_label_available'])<pd.Timestamp(a['forecast_at'])<=at
        for name in ['pool.csv.gz','manifest.json','benchmark_manifest.json',BENCH+'.csv.gz',BENCH+'.json','snapshot_audit.json']:deps[str((folder/name).relative_to(R))]=sha(folder/name)
        rows.append(dict(round=gw,forecast_at=str(at),players=len(q),buyable=int(q.can_buy.sum()),all_metadata_before_origin=True))
    times=pd.read_csv(P/'feature_timing.csv.gz');at=pd.to_datetime(times.forecast_at,utc=True)
    for col in ['latest_native','latest_workload','strength_latest','calendar_latest']:
        t=pd.to_datetime(times[col],utc=True,format='mixed');assert (t.isna()|t.lt(at)).all()
    pd.DataFrame(rows).to_csv(P/'readiness.csv',index=False);atomic_json(P/'preflight.json',dict(passed=True,rounds=38,pool_rows=len(d),reconstructed_rows=int(d.reconstructed.sum()),all_pool_metadata_and_known_feature_times_past=True,forecast_results_scored=False,season_untouched=False,preseason_roster_proxy_not_official_complete_market=True))
    paths=[Path(__file__),R/'scripts/component_confirmation_inputs.py',R/'scripts/verify_component_confirmation_v2.py',P/'input_view_manifest.json',P/'pool_features.pkl',P/'preflight.json',OLD/'pool_features.pkl',OLD/'base/predictions.pkl',OLD/'base/lock.json',OLD/'proposal.json',OLD/'result.json',R/'scripts/common_season_comparison.py',R/'scripts/common_model_retest.py',R/'scripts/common_model_retest_v3.py',R/'model_lab/fixed_season_forecaster.py',R/'overview/ACTIVE_TEAM_BENCHMARK.json',R/'overview/FORECAST_OBJECTIVES_V1.json',R/'model_lab/manager_learning.py',R/'model_lab/simulation.py',R/'reports/learned_manager_2026_10_15/experiment.py',R/'datasets/fpl_2026_27_best_effort_v1/manifest.json',R/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz',D/'manifest.json',D/'schema.json',D/'training.pkl']
    paths+=list(fixed.RECIPE.glob('*.py'))+[fixed.RECIPE/'proposal.json',fixed.RECIPE/'data_lock.json',fixed.RECIPE/'data.pkl'];paths+=list((R/'model_lab/vendor/fpl_rules_v1').glob('*.py'))
    for h in [1,3]:
        for gw in common.REFITS:
            folder=B/'folds'/f'{S}_h{h}_gw{gw:02d}';audit=pd.read_csv(folder/'fit_audit.csv').set_index('arm');assert sha(folder/'component.pkl')==audit.loc['component','model_sha256'];paths += [folder/'component.pkl',folder/'fit_audit.csv',folder/'lock.json']
    deps.update({str(p.relative_to(R)):sha(p) for p in paths})
    spec=dict(id=ID,candidate_id='common_component_2025_manager_confirmation_v2',hypothesis='The preselected common component package improves net2025/26 points over the active fixed-season system with identical pools and manager, and does not lose its advantage when chips are disabled.',change='Technicalv2: pad absent beyond-season reference forecast columns only; all scientifically valid horizons unchanged. No scores read in v1. Reuse32 component projection models and256 reference heads byte-for-byte; fit remaining8 and64. New manager-evaluation season2025/26, two packages only, original325-feature component recipe and H8 residual heads unchanged. Active operational fixed calibration rebuilt from its immutable prior2022–24 archive on its original4-round schedule; accepted component H1/H3 OOF models reused, H8 heads fitted on strictly past OOF origins. Separately repeat same paired season without chips. No tuning.',related_work=['component-confirmation-20261025-v1','common-season-comparison-20261025-v1','common-model-retest-20261025-v3'],dataset_id='fpl_2026_27_best_effort_v1',benchmark_id='fixed_season_h8_adaptive_v1',clock='same archived operational_proxy origins for both systems',features=dict(component='same325features, same H8 structural adapter; qualified native history, zero minutes retained',reference='actual active fixed-season recipe, original historical training/input defect preserved as documented; complete historical2025 source observations',weather='lagged historical weather only; no target-weather oracle',pool='immutable preseason roster plus observed players, same dated departure restrictions for both arms'),model_parameters=dict(component='reuse locked150iter depth5 component base models; separate H1/H3, no changes',projection='same0.01 mean-SSE residual Ridge, independent offsets0..7, same training-only transforms, refits1,9,17,25,33; completed H3 teacher window required',reference='fixed-season theta[0,1,0], originalbeta fitting and training archive, refits1,5,...37'),decision_policy=dict(policy='unchanged adaptive manager, forecast8/planning3',settings=SETTINGS,arms=ARMS,opening='empty squad,1000bank,1FT',no_chips='all four chip types disabled in both halves for both systems',node_limit=16,max_calls=40),seasons=[S],resources=dict(maximum_full_season_attempts=4,maximum_decisions=152,projection_fits=40,fixed_season_calibration_heads=320,reused_component_base_bundles=10,maximum_new_component_base_fits=0,reused_projection_models=32,maximum_new_projection_models=8,reused_reference_heads=256,maximum_new_reference_heads=64,workers=4,threads_per_solver=1),maximum_runs=1,input_hashes=deps,success_criterion='Both systems complete both settings, all causal/legality checks pass, component strictly exceeds active net points after hits in adaptive-chips primary AND no-chip robustness setting. Report deltas separately; previously seen season, not untouched confirmation. Passing makes candidate eligible for live integration review, never fakes forward evidence or activates an unverified live model.',stop_rule='Stop affected attempt on native solver/cap error, unknown selected outcome, nonfinite forecast, changed input or information-time failure. No retry, relaxed resource cap, refit after scoring or adaptive choice of setting.',evaluation_contract=dict(evidence='2025/26 has already been studied for forecast quality and older models. New preselected-package manager comparison; historical temporal/robustness check.',prospective='Future before-deadline storage and live input/runtime checks remain distinct deployment gates; retrospective2026/27 predictions cannot be called prospective.',reference='Cached causal underlying base forecasts may be reused byte-for-byte after manifest/past-time checks, then active fixed calibration is freshly applied. No cached season totals reused.',rules='identical existing frozen rules, including5FT bank and common chip policy; historical outcomes under that rulebook, not exact historical rule reproduction.'))
    atomic_json(P/'proposal.json',spec);print('CONFIRMATION PREFLIGHT PASSED AND PROPOSAL PREPARED',len(d),flush=True)

def forecasts():
    verify_files(R,common.read(P/'proposal.json')['input_hashes']);d=pd.read_pickle(P/'pool_features.pkl');names=[f'component_{k}{h}' for h in [1,3] for k in ['p','m']];audits=[]
    for gw in common.REFITS:
        te=d[d['round'].between(gw,min(gw+7,38))]
        for h in [1,3]:
            folder=B/'folds'/f'{S}_h{h}_gw{gw:02d}';a=pd.read_csv(folder/'fit_audit.csv');a=a[a.arm.eq('component')].iloc[0];at=d[d['round'].eq(gw)].forecast_at.iloc[0];assert pd.Timestamp(a.cutoff)==at and pd.Timestamp(a.max_label)<at
            with (folder/'component.pkl').open('rb') as f:bundle=pickle.load(f)
            pred,_,_=common.predict_arm(bundle,te);d.loc[te.index,f'component_p{h}']=pred[:,0];d.loc[te.index,f'component_m{h}']=pred[:,1]
    old=pd.read_pickle(OLD/'pool_features.pkl').merge(pd.read_pickle(OLD/'base/predictions.pkl')[KEY+['forecast_at']+names],on=KEY+['forecast_at'],validate='one_to_one');teacher=pd.concat([old,d],ignore_index=True);assert not teacher.duplicated(KEY).any();teacher.to_pickle(P/'projection_data.pkl');d.to_pickle(P/'base_predictions.pkl');projections=[];refs=[];models={};history=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=['season','fixture','code','native_minutes','native_goals_scored','native_assists','native_clean_sheets','native_saves','target_total_points','kickoff_time']);history['available']=pd.to_datetime(history.kickoff_time,utc=True)+pd.Timedelta(hours=24);history=history.rename(columns=dict(native_minutes='minutes',native_goals_scored='goals',native_assists='assists',native_clean_sheets='clean',native_saves='saves',target_total_points='points'));history['played']=history.minutes.gt(0).astype(float);history['sixty']=history.minutes.ge(60).astype(float);archive=fixed.load_training_archive()
    for gw in range(1,39):
        q=d[d['round'].eq(gw)].copy();at=q.forecast_at.iloc[0]
        if gw in common.REFITS:
            complete=teacher[[f'y_{j}' for j in range(3)]].notna().all(axis=1);weather_at=teacher[[f'y_at_{j}' for j in range(3)]].max(axis=1)
            for j in range(8):
                tr=teacher[teacher.teacher_eligible&teacher.forecast_at.lt(at)&teacher[f'y_{j}'].notna()&teacher[f'y_at_{j}'].lt(at)&complete&weather_at.lt(at)].copy();path=P/'models'/f'gw{gw:02d}_j{j}.json';model=common.read(path) if path.exists() else method.fit_projection(tr,'component',j);models[j]=model;
                if not path.exists():atomic_json(path,model)
                audits.append(dict(round=gw,offset=j,cutoff=str(at),rows=len(tr),training_keys_sha256=common.keys_hash(tr),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'y_at_{j}'].max()),model=str(path.relative_to(P)),model_sha256=sha(path)))
        out=q[KEY+['forecast_at','can_buy']].copy()
        for j in range(8):out[f'xp_{j}']=method.predict_projection(q,'component',models[j]) if gw+j<=38 else 0.
        projections.append(out)
        folder=C/S/f'gw{gw:02d}';base=pd.read_csv(folder/(BENCH+'.csv.gz'));p=pd.read_csv(folder/'pool.csv.gz');assert pd.to_datetime(base.forecast_at,utc=True).eq(at).all()
        for j in range(8):
            if f'xp_{j}' not in base:
                assert gw+j>38; base[f'xp_{j}']=0.
        features=fixed.make_features(p[['code','position','price_tenths']].assign(season=S,round=gw,forecast_at=at).merge(base.drop(columns='forecast_at'),on='code',validate='one_to_one'),history)
        if gw in range(1,39,4):
            path=P/'reference_models'/f'gw{gw:02d}.json';control=common.read(path) if path.exists() else fixed.fit_models(archive,at,S,gw)
            if not path.exists():atomic_json(path,control)
        result=fixed.forecast(features,control);result=result[KEY+['forecast_at']+[f'xp_{j}' for j in range(8)]];result=result.merge(q[KEY+['can_buy']],on=KEY,validate='one_to_one');refs.append(result);print('CONFIRMATION FORECAST',gw,flush=True)
    pd.DataFrame(audits).to_csv(P/'projection_audit.csv',index=False);files={}
    for arm,parts in [('component',projections),('operational_fixed',refs)]:
        out=pd.concat(parts,ignore_index=True);assert not out.duplicated(KEY).any();path=P/f'{arm}.csv.gz';out.to_csv(path,index=False);files[path.name]=sha(path)
    files['projection_data.pkl']=sha(P/'projection_data.pkl');files['projection_audit.csv']=sha(P/'projection_audit.csv');atomic_json(P/'prediction_lock.json',dict(files=files,saved_before_decisions=True,original_recipe_unchanged=True,component_projection_fits=40,production_changed=False))

class ConfirmationEnvironment(Environment):
    def inputs(self,season,gw):
        assert season==S;folder=C/S/f'gw{gw:02d}';pool=pd.read_csv(folder/'pool.csv.gz');m=common.read(folder/'manifest.json');return pool,None,m,None

def manager(arm,setting):
    assert arm in ARMS and setting in SETTINGS;verify_files(R,common.read(P/'proposal.json')['input_hashes']);verify_files(P,common.read(P/'prediction_lock.json')['files']);assert common.read(P/'forecast_verification.json')['passed'];pred=pd.read_csv(P/(arm+'.csv.gz')).set_index(['round','code']);folder=P/'manager'/f'{arm}_{setting}';folder.mkdir(parents=True,exist_ok=False);mod,adapter=backend(16,40);state=adapter.engine.initial_state()
    if setting=='no_chips':state['used_chips']={h:list(adapter.engine.CHIPS) for h in ['1','2']}
    atomic_json(folder/'started.json',dict(runtime=runtime(),forecast_sha256=sha(P/(arm+'.csv.gz')),setting=setting,arm=arm));env=ConfirmationEnvironment();net=hits=0
    for gw in range(1,39):
        p,_,m,_=env.inputs(S,gw);at=pd.Timestamp(m['forecast_at']);p=method.qualify(p,S,at);q=pred.loc[gw].reindex(p.code);assert q.can_buy.tolist()==p.can_buy.tolist();assert pd.to_datetime(q.forecast_at,utc=True).eq(at).all();xp=q[[f'xp_{j}' for j in range(min(8,39-gw))]].to_numpy(float);assert np.isfinite(xp).all();mod,a=backend(16,40);choice=copy.deepcopy(a.decide(p,xp,state,gw)['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};after,choice=a.engine.apply_decision(state,choice,p.to_dict('records'),gw)
        if setting=='no_chips':assert not choice['chip']
        atomic_json(folder/f'gw{gw:02d}.decision.json',mod.clean(dict(state_before=state,state_after=after,choice=choice,forecast_at=str(at),outcomes_read=False,solver_calls=a.ledger,forecast_input_sha256=hashlib.sha256(xp.tobytes()).hexdigest())));outcomes,result,n=settle(a,env,S,gw,dict(choice=choice),p);atomic_json(folder/f'gw{gw:02d}.settlement.json',mod.clean(dict(net=n,hits=4*choice['paid'],outcomes=outcomes,settlement=result)));net+=n;hits+=4*choice['paid'];state=after
        if gw%8==0:print('CONFIRMATION MANAGER',arm,setting,gw,flush=True)
    atomic_json(folder/'summary.json',dict(arm=arm,setting=setting,net=net,hits=hits,rounds=38));print('COMPLETE',arm,setting,net,flush=True)

def managers():
    jobs=[(a,s) for a in ARMS for s in SETTINGS]
    def run(job):
        a,s=job;path=P/'logs'/f'{a}_{s}.log';path.parent.mkdir(exist_ok=True)
        with path.open('x') as f:r=subprocess.run([sys.executable,str(Path(__file__).resolve()),'manager',a,s],cwd=R,env=os.environ.copy(),stdout=f,stderr=subprocess.STDOUT)
        print('ATTEMPT',a,s,'exit',r.returncode,flush=True);return dict(arm=a,setting=s,exit_code=r.returncode)
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:results=list(ex.map(run,jobs))
    atomic_json(P/'attempts.json',dict(results=results,no_retries=True))

if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
