"""User-requested actual-weather proxy study, separate from causal main batch.

Historical reconstructed target-match weather is an explicitly optimistic
proxy for live weather forecasts. Synthetic errors are sensitivity scenarios,
not measured forecast accuracy. Existing main data/model contracts are intact.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,pickle,time,subprocess,concurrent.futures
from pathlib import Path
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import common_model_retest as core
from scripts import common_model_retest_v3 as repaired
from model_lab.common import sha,atomic_json,verify_files
D=core.D;BASE=R/'reports/common_model_retest_2026_10_25_v3'
P=R/'reports/common_weather_proxy_2026_10_25'
FIELDS={'temperature':'weather_temperature_2m_mean','wind':'weather_wind_speed_10m_mean','rain':'weather_precipitation_sum','cloud':'weather_cloud_cover_mean','sun':'weather_sunshine_minutes_daylight_capped'}
SIGMA={'temperature':2.,'wind':1.5,'rain':1.,'cloud':15.,'sun':15.}
ID='common-weather-proxy-20261025-v1'

def prepare():
    P.mkdir(exist_ok=True);assert not (P/'weather.pkl').exists()
    verify_files(D,core.read(D/'manifest.json')['files'])
    m=pd.read_csv(core.MASTER,usecols=core.KEY+['fixture','weather_daylight_minutes']+list(FIELDS.values()));d=pd.read_pickle(D/'training.pkl');keys=d[core.KEY]
    for col in FIELDS.values():assert m.groupby(['season','fixture'])[col].nunique(dropna=False).le(1).all()
    fixture=m[['season','fixture','weather_daylight_minutes']+list(FIELDS.values())].drop_duplicates(['season','fixture']).sort_values(['season','fixture']).copy();rng=np.random.default_rng(20261025)
    errors={name:rng.normal(0,SIGMA[name],len(fixture)) for name in FIELDS}
    scenarios={}
    for scenario,scale in [('actual',0.),('noise_1',1.),('noise_2',2.)]:
        f=fixture.copy()
        for name,col in FIELDS.items():
            if scale:
                f[col]=f[col]+errors[name]*scale
                if name in ['wind','rain','cloud','sun']:f[col]=f[col].clip(lower=0)
                if name=='cloud':f[col]=f[col].clip(upper=100)
                if name=='sun':f[col]=np.minimum(f[col],f.weather_daylight_minutes)
        # One forecast-error realization per physical match, shared by all players.
        mm=m[core.KEY+['fixture']].merge(f,on=['season','fixture'],validate='many_to_one')
        roundmean=mm.groupby(core.KEY)[list(FIELDS.values())].mean().reset_index()
        out=keys.copy()
        for h in [1,3]:
            arrays=[]
            for j in range(h):
                z=roundmean.copy();z['round']-=j;z=keys.merge(z,on=core.KEY,how='left',validate='one_to_one');arrays.append(z[list(FIELDS.values())].to_numpy(float))
            # Complete-label cohorts have every target round. No future match
            # count or additional fixture-selection label is supplied to X.
            values=np.mean(np.stack(arrays),axis=0)
            for k,name in enumerate(FIELDS):out[f'proxy_{scenario}_{name}_h{h}']=values[:,k]
        scenarios[scenario]=out
    merged=keys.copy()
    for out in scenarios.values():merged=merged.merge(out,on=core.KEY,validate='one_to_one')
    merged.to_pickle(P/'weather.pkl');atomic_json(P/'weather_manifest.json',dict(input_master_sha256=sha(core.MASTER),rows=len(merged),overlay_sha256=sha(P/'weather.pkl'),fields=FIELDS,noise_std=SIGMA,noise_levels={'noise_1':1,'noise_2':2},shared_fixture_errors=True,same_base_error_scaled_across_levels=True,sunshine_capped_to_astronomical_daylight=True,strict_predeadline=False,user_authorization='User explicitly requested training/evaluating with actual historical weather as a proxy for live forecasts. Keep separate from causal main model comparison.'))
    deps=[Path(__file__),R/'scripts/common_model_retest.py',R/'scripts/common_model_retest_v3.py',P/'weather.pkl',P/'weather_manifest.json',D/'manifest.json',D/'training.pkl',D/'schema.json',R/'datasets/fpl_2026_27_best_effort_v1/manifest.json',core.MASTER,R/'overview/FORECAST_OBJECTIVES_V1.json',R/'overview/ACTIVE_TEAM_BENCHMARK.json']
    spec=dict(id=ID,candidate_id='actual_weather_proxy_catboost_v1',hypothesis='Actual historical match weather provides incremental forecast signal beyond the same enriched CatBoost, and the signal is not entirely lost under predeclared synthetic forecast-error scenarios.',change='User-requested separate optimistic target-weather proxy. Same common train/eval rows, H1/H3 and refits; full CatBoost plus five target-weather means. Train on reconstructed actual weather; predict using actual weather or two fixed synthetic error levels. No claim of realistic historical forecast availability.',related_work=['common-model-retest-20261025-v3'],dataset_id='fpl_2026_27_best_effort_v1',benchmark_id='fixed_season_h8_adaptive_v1',clock='main_operational_origins_plus_explicit_actual_weather_proxy_not_strictly_predeadline',features=dict(core=core.read(D/'schema.json')['features'],weather=list(FIELDS),scenarios=['actual','noise_1','noise_2']),model_parameters=dict(catboost=core.read(BASE/'proposal.json')['model_parameters']['catboost'],noise_std=SIGMA,noise_scales=[1,2],refits=core.REFITS,seed=20261025),decision_policy=dict(stage='forecast_only_weather_proxy',control='identical full CatBoost from common main batch',training='same past origins and known labels; actual historical target weather allowed for completed training origins',prediction='test-target actual weather is intentional optimistic information; synthetic errors model hypothetical live forecast mismatch'),seasons=core.SEASONS,resources=dict(maximum_fits=40,parallel_workers=4,threads_per_fit=1,maximum_runs=1),maximum_runs=1,input_hashes={str(p.relative_to(R)):sha(p) for p in deps},success_criterion='Per horizon separately, lower point MSE in each2022/23–2024/25 development season than full common CatBoost. Minute MSE separately.2025/26 reported separately. Synthetic sensitivity cannot establish actual forecast performance; no operational promotion.',stop_rule='Stop on input/time/key mismatch or nonfinite output. No tuning weather selection, noise strengths or parameters after scoring.',evaluation_contract=dict(primary_metric='Per-season point and minute MSE on exactly the main known eligible keys',evidence_role='Optimistic reconstructed-actual-weather proxy, not a causal predeadline backtest. Noise assumptions are illustrative and uncalibrated.',unchanged='Original main experiment and prospective forecasts remain immutable.'))
    atomic_json(P/'proposal.json',spec);print('WEATHER PROXY PREPARED',len(merged),flush=True)

def worker(s,h,gw):
    spec=core.read(P/'proposal.json');verify_files(R,spec['input_hashes']);d=pd.read_pickle(D/'training.pkl').merge(pd.read_pickle(P/'weather.pkl'),on=core.KEY,validate='one_to_one');schema=core.read(D/'schema.json')
    actual=[f'proxy_actual_{name}_h{h}' for name in FIELDS];columns=schema['features']+actual
    q=d[d.season.eq(s)&d['round'].between(gw,min(gw+7,38))&~d.excluded_origin].copy();at=d[d.season.eq(s)&d['round'].eq(gw)].forecast_at.iloc[0]
    targets=[f'target_{t}_{h}' for t in ['points','minutes','starts','attack','appearance','residual']];tr=d[d.train_eligible&d.forecast_at.lt(at)&d[f'label_at_{h}'].lt(at)&d[targets].notna().all(axis=1)].copy()
    reference=core.read(BASE/'folds'/f'{s}_h{h}_gw{gw:02d}'/'lock.json');assert core.keys_hash(tr)==reference['training_keys_sha256'];assert core.keys_hash(q)==reference['prediction_keys_sha256']
    bundle=core.fit_arm('catboost',tr,columns,h);folder=P/'folds'/f'{s}_h{h}_gw{gw:02d}';folder.mkdir(parents=True,exist_ok=True)
    with (folder/'model.pkl').open('wb') as f:pickle.dump(bundle,f,protocol=5)
    for scenario in ['actual','noise_1','noise_2']:
        te=q.copy()
        if scenario!='actual':
            for name in FIELDS:te[f'proxy_actual_{name}_h{h}']=te[f'proxy_{scenario}_{name}_h{h}']
        pred,_,_=core.predict_arm(bundle,te);out=q[core.KEY+['row_id','eval_eligible',f'target_points_{h}',f'target_minutes_{h}']].copy();out['predicted_points']=pred[:,0];out['predicted_minutes']=pred[:,1];out.to_csv(folder/(scenario+'.csv.gz'),index=False)
    atomic_json(folder/'lock.json',dict(training_keys_sha256=core.keys_hash(tr),prediction_keys_sha256=core.keys_hash(q),training_rows=len(tr),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'label_at_{h}'].max()),cutoff=str(at),files={p.name:sha(p) for p in folder.iterdir() if p.is_file()}));print('WEATHER FOLD',s,h,gw,flush=True)

def train():
    verify_files(R,core.read(P/'proposal.json')['input_hashes']);assert not (P/'started.json').exists();atomic_json(P/'started.json',dict(started_at=str(pd.Timestamp.now(tz='UTC')),saved_before_scoring=True))
    jobs=[(s,h,gw) for s in core.SEASONS for h in [1,3] for gw in core.REFITS]
    def launch(job):
        s,h,gw=job;log=P/f'{s}_h{h}_gw{gw:02d}.log'
        with log.open('x') as f:subprocess.run([sys.executable,str(Path(__file__).resolve()),'worker',s,str(h),str(gw)],cwd=R,env=os.environ.copy(),stdout=f,stderr=subprocess.STDOUT,check=True)
        return job
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for i,job in enumerate(pool.map(launch,jobs),1):print('WEATHER',i,'/40',*job,flush=True)
    atomic_json(P/'prediction_lock.json',dict(fits=40,scenarios=3,saved_before_scoring=True,strict_predeadline=False))

def score():
    assert core.read(P/'prediction_lock.json')['saved_before_scoring'];records=[];checks=[]
    for s in core.SEASONS:
        for h in [1,3]:
            data={x:[] for x in ['control','actual','noise_1','noise_2']}
            for gw in core.REFITS:
                folder=P/'folds'/f'{s}_h{h}_gw{gw:02d}';lock=core.read(folder/'lock.json');verify_files(folder,lock['files'])
                assert pd.Timestamp(lock['max_origin'])<pd.Timestamp(lock['cutoff']);assert pd.Timestamp(lock['max_label'])<pd.Timestamp(lock['cutoff'])
                data['control'].append(pd.read_csv(BASE/'folds'/folder.name/'catboost.csv.gz'))
                with (folder/'model.pkl').open('rb') as f:bundle=pickle.load(f)
                d=pd.read_pickle(D/'training.pkl').merge(pd.read_pickle(P/'weather.pkl'),on=core.KEY,validate='one_to_one');te=d[d.season.eq(s)&d['round'].between(gw,min(gw+7,38))&~d.excluded_origin].copy()
                for scenario in ['actual','noise_1','noise_2']:
                    q=pd.read_csv(folder/(scenario+'.csv.gz'));assert q.row_id.tolist()==te.row_id.tolist()
                    test=te.copy()
                    if scenario!='actual':
                        for name in FIELDS:test[f'proxy_actual_{name}_h{h}']=test[f'proxy_{scenario}_{name}_h{h}']
                    pred,_,_=core.predict_arm(bundle,test);np.testing.assert_allclose(pred,q[['predicted_points','predicted_minutes']],rtol=1e-9,atol=1e-9);data[scenario].append(q)
                checks.append(dict(season=s,horizon=h,round=gw,training_keys_sha256=lock['training_keys_sha256'],predictions_replayed=True))
            ids=None
            for scenario,parts in data.items():
                q=pd.concat(parts,ignore_index=True);q=q[q.eval_eligible&q[f'target_points_{h}'].notna()&q[f'target_minutes_{h}'].notna()]
                if ids is None:ids=q.row_id.tolist()
                else:assert ids==q.row_id.tolist()
                records.append(dict(season=s,horizon=h,scenario=scenario,n=len(q),point_mse=float(((q.predicted_points-q[f'target_points_{h}'])**2).mean()),minute_mse=float(((q.predicted_minutes-q[f'target_minutes_{h}'])**2).mean())))
    m=pd.DataFrame(records);m.to_csv(P/'metrics.csv',index=False);atomic_json(P/'verification.json',dict(passed=True,folds=40,models=40,prediction_files_replayed=120,same_main_training_and_eval_keys=True,strict_predeadline=False,proxy_weather_authorized_by_user=True,checks=checks))
    atomic_json(P/'result.json',dict(conclusion='Separat faktisk-vær-proxy er testet på samme rader som hovedforsøket, med to forhåndsvalgte syntetiske feilscenarioer. Ingen realistisk historisk værvarseleffekt eller produksjonsoppgradering påstås.',decision='retain_for_research',results=m.to_dict('records'),evidence_hashes={str(p.relative_to(R)):sha(p) for p in [P/'metrics.csv',P/'verification.json',P/'prediction_lock.json']}));print(m.to_string(index=False))

if __name__=='__main__':
    if sys.argv[1]=='worker':worker(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
    else:globals()[sys.argv[1]]()
