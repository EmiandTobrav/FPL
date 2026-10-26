"""Diagnostic single-intervention bridge: permit same-season teacher updates.
No recipe tuning, improved calendar, source replacement or live activation.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,json,subprocess,concurrent.futures,copy
from pathlib import Path
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import component_confirmation_v2 as cf
from model_lab.common import atomic_json,sha,verify_files
BASE=cf.P;A=R/'reports/season_comparability_audit_2026_10_25';P=A/'rolling_reference_v2';ID='season-comparability-rolling-reference-20261025-v2';ARM='reference_rolling_archive'
def prepare():
    P.mkdir();assert cf.common.read(A/'audit.json')['passed'];paths=[Path(__file__),R/'scripts/verify_audit_rolling_reference_v2.py',R/'scripts/audit_season_comparability.py',A/'audit.json',A/'input_manifest.json',BASE/'proposal.json',BASE/'result.json',BASE/'pool_features.pkl',BASE/'operational_fixed.csv.gz',R/'model_lab/fixed_season_forecaster.py',cf.fixed.RECIPE/'data.pkl',cf.fixed.RECIPE/'data_lock.json',cf.fixed.RECIPE/'season_gate.py',cf.fixed.RECIPE/'experiment.py',R/'overview/ACTIVE_TEAM_BENCHMARK.json',R/'overview/FORECAST_OBJECTIVES_V1.json',R/'datasets/fpl_2026_27_best_effort_v1/manifest.json',R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',R/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz'];deps=dict(cf.common.read(BASE/'proposal.json')['input_hashes']);deps.update({str(p.relative_to(R)):sha(p) for p in paths});spec=dict(id=ID,candidate_id='reference_current_year_archive_diagnostic_v2',hypothesis='The original2025 reference calibration did not ingest current-season teacher rows. Restoring the same expanding as-of teacher rule as in2023/24 and2024/25 changes forecasts and season outcomes; direction is not preselected.',change='Technicalv2: select only label join keys/value/time columns to avoid duplicate unused metadata; no fits or scores in v1. Append explicitly reconstructed historical2025 teacher origins to a NEW diagnostic archive, never the live archive. Same original native feature recipe, underlying base predictions, all coefficients/penalties/refit schedule, metadata/pools, outcome labels, adaptive manager and resources. Component forecasts/decisions unchanged and not rerun.',related_work=['season-comparability-rolling-reference-20261025-v1','component-confirmation-20261025-v2','common-season-comparison-20261025-v1'],dataset_id='fpl_2026_27_best_effort_v1',benchmark_id='fixed_season_h8_adaptive_v1',clock='unchanged dated2025 operational_proxy origins and +24h labels',features=dict(reference='original fixed-season features, original structural-zero weakness retained; only addition is same-season teacher rows with both origin and complete target before refit',calendar='exact original base forecast calendar unchanged; no final schedule substitution',evidence='post-result methodological audit, not independent confirmation or operational active model'),model_parameters=dict(fixed_theta=[0,1,0],ridge_penalty=.01,refits=list(range(1,39,4)),offsets=list(range(8)),positions=['GK','DEF','MID','FWD'],no_parameter_search=True),decision_policy=dict(settings=cf.SETTINGS,arms=[ARM],same_policy=True,horizon=8,planning=3,node_limit=16,max_calls=40,opening='empty1000bank1FT, chips enabled or all disabled exactly as original setting'),seasons=[cf.S],resources=dict(maximum_head_fits=320,maximum_full_season_attempts=2,maximum_manager_decisions=76,workers=2,threads_per_solver=1),maximum_runs=1,input_hashes=deps,success_criterion='Causal archive/transform checks, exact equality to original forecasts before current-year labels become eligible, complete independent decision/settlement replay. Report signed changes whatever their direction. No promotion or sign-based recipe choice.',stop_rule='Stop affected attempt on unknown selected outcome, native resource failure, changed source, nonfinite values or future information. No blind retry, relaxed budget or parameter search.',evaluation_contract=dict(actual_live_archive_preserved=True,original_results_preserved=True,retrospective_reconstruction_not_prospective=True,source_limits='Old calendar and roster proxies retained. This isolates archive updating, not calendar quality or intrinsic season difficulty.'))
    atomic_json(P/'proposal.json',spec)

def forecasts():
    verify_files(R,cf.common.read(P/'proposal.json')['input_hashes']);archive=cf.fixed.load_training_archive();history=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=['season','fixture','code','native_minutes','native_goals_scored','native_assists','native_clean_sheets','native_saves','target_total_points','kickoff_time']);history['available']=pd.to_datetime(history.kickoff_time,utc=True)+pd.Timedelta(hours=24);history=history.rename(columns=dict(native_minutes='minutes',native_goals_scored='goals',native_assists='assists',native_clean_sheets='clean',native_saves='saves',target_total_points='points'));history['played']=history.minutes.gt(0).astype(float);history['sixty']=history.minutes.ge(60).astype(float);labels=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz',usecols=cf.KEY+['target_total_points','source_latest_kickoff']);labels['available']=pd.to_datetime(labels.source_latest_kickoff,utc=True)+pd.Timedelta(hours=24);parts=[];features={}
    for gw in range(1,39):
        folder=cf.C/cf.S/f'gw{gw:02d}';pool=pd.read_csv(folder/'pool.csv.gz');at=pd.Timestamp(cf.common.read(folder/'manifest.json')['forecast_at']);base=pd.read_csv(folder/(cf.BENCH+'.csv.gz'))
        for j in range(8):
            if f'xp_{j}' not in base:assert gw+j>38;base[f'xp_{j}']=0.
        q=pool[['code','position','price_tenths','can_buy']].assign(season=cf.S,round=gw,forecast_at=at).merge(base.drop(columns='forecast_at'),on='code',validate='one_to_one');q=cf.fixed.make_features(q,history);assert (q.latest_feature_available.isna()|q.latest_feature_available.lt(at)).all();features[gw]=q.copy()
        for j in range(8):
            lab=labels[cf.KEY+['target_total_points','available']].copy();lab['round']-=j;lab=lab.rename(columns={'target_total_points':f'y_{j}','available':f'label_at_{j}'});q=q.merge(lab,on=cf.KEY,how='left',validate='one_to_one')
        parts.append(q)
    added=pd.concat(parts,ignore_index=True);data=pd.concat([archive,added],ignore_index=True);assert not data.duplicated(cf.KEY).any();data.to_pickle(P/'diagnostic_archive.pkl');out=[];audit=[];_,recipe=cf.fixed.recipe();original=pd.read_csv(BASE/'operational_fixed.csv.gz').set_index(cf.KEY)
    for gw in range(1,39):
        q=features[gw];at=q.forecast_at.iloc[0]
        if gw in range(1,39,4):
            bundle=cf.fixed.fit_models(data,at,cf.S,gw);atomic_json(P/'models'/f'gw{gw:02d}.json',bundle)
            for pos in ['GK','DEF','MID','FWD']:
                for j in range(8):
                    tr=recipe.training(data,at,pos,j);audit.append(dict(round=gw,position=pos,offset=j,rows=len(tr),current_season_rows=int(tr.season.eq(cf.S).sum()),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'label_at_{j}'].max()),training_keys_sha256=cf.common.keys_hash(tr)))
        pred=cf.fixed.forecast(q,bundle);pred=pred[cf.KEY+['forecast_at']+[f'xp_{j}' for j in range(8)]];pool=cf.method.qualify(pd.read_csv(cf.C/cf.S/f'gw{gw:02d}/pool.csv.gz'),cf.S,at);pred=pred.merge(pool[['code','can_buy']],on='code',validate='one_to_one')
        if gw<=4:
            a=pred.set_index(cf.KEY);np.testing.assert_allclose(a[[f'xp_{j}' for j in range(8)]],original.reindex(a.index)[[f'xp_{j}' for j in range(8)]],rtol=0,atol=1e-9)
        out.append(pred)
    pd.concat(out,ignore_index=True).to_csv(P/(ARM+'.csv.gz'),index=False);pd.DataFrame(audit).to_csv(P/'fit_audit.csv',index=False);atomic_json(P/'prediction_lock.json',dict(files={n:sha(P/n) for n in [ARM+'.csv.gz','diagnostic_archive.pkl','fit_audit.csv']},saved_before_decisions=True,original_first4_forecasts_reproduced=True));print('ROLLING DIAGNOSTIC FORECASTS SEALED',flush=True)

def manager(setting):
    cf.P=P;cf.ARMS=[ARM];cf.manager(ARM,setting)
def managers():
    def job(setting):
        path=P/'logs'/f'{setting}.log';path.parent.mkdir(exist_ok=True)
        with path.open('x') as f:r=subprocess.run([sys.executable,str(Path(__file__).resolve()),'manager',setting],cwd=R,env=os.environ.copy(),stdout=f,stderr=subprocess.STDOUT)
        print('ROLLING DIAGNOSTIC ATTEMPT',setting,r.returncode,flush=True);return dict(setting=setting,exit_code=r.returncode)
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:rows=list(ex.map(job,cf.SETTINGS))
    atomic_json(P/'attempts.json',dict(results=rows,no_retries=True))
if __name__=='__main__':globals()[sys.argv[1]](*sys.argv[2:])
