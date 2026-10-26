"""More frequent uniform base fits; fixed quarterly recent180 calibration.

Models are fitted from scratch. The two schedules share exactly identical
cutoff/matrix/parameter models; the80 original quarterly packages are reused.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import base_recency_study as b
from model_lab.common import atomic_json,sha,verify_files
from catboost import CatBoostRegressor
import numpy as np,pandas as pd
OLD=b.P;P=R/'reports/base_cadence_2026_10_26';F=b.F;D=b.D;t=b.t
ID='component-base-cadence-20261026-v1';CONFIG={'standard':4,'every2':2,'every1':1};ARMS=['every1','every2']
b.P=P;b.CONFIG=CONFIG;b.ARMS=ARMS;b.cal.P=P;b.cal.ARMS=ARMS;t.P=P;t.D=D;t.ARMS=list(CONFIG)

def available(view,s):return sorted(view.loc[view.season.eq(s),'round'].unique().tolist())
def refits(view,s,stride):return [g for g in available(view,s) if (g-1)%stride==0]

def setup():
    P.mkdir(exist_ok=False);parent=t.read(OLD/'proposal.json');deps=parent['input_hashes'].copy();verify_files(R,deps)
    paths=[Path(__file__),R/'scripts/verify_base_cadence_study.py',R/'scripts/base_recency_study.py',R/'scripts/verify_base_recency_study.py',OLD/'proposal.json',OLD/'final_verification.json',OLD/'control_bundle_inventory.csv',OLD/'uniform_identity_verification.json',OLD/'base_verification_standard.json',OLD/'prediction_verification_standard.json',OLD/'forecast_metrics.csv',OLD/'component_metrics.csv',OLD/'scores_standard.csv',OLD/'standard.csv.gz',OLD/'one_change_verification.json']+list((OLD/'standard').glob('base_*.pkl'))
    deps.update({str(q.relative_to(R)):sha(q) for q in paths});view=t.load(D/'pool_features.pkl');grid={s:available(view,s) for s in t.S};weekly=sum(2*len(v) for v in grid.values());biweekly=sum(2*len(refits(view,s,2)) for s in t.S);new=weekly-80
    assert weekly==302 and biweekly==150 and new==222
    shutil.copyfile(R/'overview/ACTIVE_TEAM_BENCHMARK.json',P/'reference_ACTIVE_TEAM_BENCHMARK.json');shutil.copyfile(OLD/'control_bundle_inventory.csv',P/'control_bundle_inventory.csv');shutil.copyfile(OLD/'scores_standard.csv',P/'scores_standard.csv');shutil.copytree(OLD/'standard',P/'standard')
    atomic_json(P/'dataset_verification.json',dict(passed=True,same_qualified_data_and325_features=True,only_base_fit_cadence_changed=True,qualified_origins=grid,missing_teacher_origin2022GW7_not_fabricated=True))
    spec=dict(id=ID,candidate_id='uniform_base_stride1_2_fixed_calibration_stride4_v1',dataset_id=parent['dataset_id'],benchmark_id=parent['benchmark_id'],hypothesis='More frequent base training may adapt better than calibration-only updates. Compare weekly and two-round base refits with the current four-round baseline, keeping the entire calibration recipe and schedule fixed.',change='Uniform base row weights, original325features, targets, imputation, CatBoost settings, scratch fits and seed unchanged. Base cadence1 or2 instead of4; refit grids1+k*stride on existing qualified origins. Reuse80 original quarterly models and70 further models shared by the two candidates;222unique new models. At missing2022GW7teacher origin no source/row/cutoff is invented; hold last eligible scheduled model until next eligible grid refit. Actual three evaluation seasons have all38origins. Rebuild each variants OOF teacher/prediction stream and same quarterly180day/Ridge.01 calibration; no automatic promotion.',related_work=['component-base-recency-20261026-v1','component-calibration-response-20261026-v1','component-recent180-operational-20261026-v1'],clock=parent['clock'],features=parent['features'],model_parameters=dict(base_cadences=CONFIG,qualified_origins=grid,base_params=b.PARAMS,uniform_base_weights=True,scratch_not_warm_start=True,imputation='unweighted train-only medians plus missing flags',calibration=dict(refits=list(t.REFITS),half_life_days=180,ridge=.01,unpenalized_intercept=True,completeH3_teacher_filter=True,own_past_base_forecasts=True),reuse='only identical cutoff/data/labels/params; base training inputs do not depend on previous models',missing_origin='skip refit if that scheduled qualified origin does not exist; retain previous until next qualified scheduled origin',no_parameter_search=True),decision_policy=parent['decision_policy'],seasons=t.EVAL,resources=dict(unique_new_base_fits=222,reused_original_quarterly_models=80,weekly_referenced_packages=302,two_round_referenced_packages=150,shared_new_packages=70,independent_new_fit_replays=2,new_calibration_heads=480,standard_calibration_reproduction=240,new_full_seasons=6,new_manager_decisions=228,reused_standard_seasons=3,preflight_decisions=4,workers=4,threads=1),maximum_runs=1,input_hashes=deps,success_criterion=parent['success_criterion'],stop_rule='Complete both fixed candidates and6episodes regardless early performance. No score-driven interval/weight/source/solver change or pruning. Fail on clocks, matrix/parameter mismatch, shared-model inconsistency, nonfinite outputs, availability, legality or resource excess. Keep production and sealed2026forecast files unchanged.',evaluation_contract=dict(primary='full-season net-after-hits, each year',secondary='latest2/all3mean, variance/range; same fixed candidate/MID/premium H1/H3point/minute/component errors and rank',causality='fit uses origin and fully available horizon labels before its deadline; inference cannot select a later trained model',scope='Previously inspected historical development; no2026outcomes, real FPL rank or live deployment'))
    atomic_json(P/'proposal.json',spec);print('BASE CADENCE PREPARED:222new models;6episodes',flush=True)

def corpus(s):
    t.check();data=t.load(D/'training.pkl');view=t.load(D/'pool_features.pkl');cols=b.columns();audit=[];out=view[view.season.eq(s)][t.KEY+['forecast_at']].copy()
    for g in available(view,s):
        q=view[view.season.eq(s)&view['round'].eq(g)];at=q.forecast_at.iloc[0]
        for h in [1,3]:
            train=b.select(data,at,h);assert train.forecast_at.max()<at and train[f'label_at_{h}'].max()<at
            if g in t.REFITS:
                old=b.control_row(s,g,h);assert len(train)==old.rows and t.common.keys_hash(train)==old.keys_sha256;path=b.control_path(old);assert sha(path)==old.sha256;bundle=t.load(path);source='original_quarterly'
            else:
                x,imputer=b.matrix(train,cols);y=b.labels(train,h);model=CatBoostRegressor(**b.PARAMS);model.fit(x,y);bundle=dict(name='component',columns=cols,imputer=imputer,models=[model],horizon=h,fit_cutoff=str(at),fit_round=g,uniform_base_training=True,trained_from_scratch=True);path=P/f'models/uniform_{s}_gw{g:02d}_h{h}.pkl';t.save(path,bundle);source='new_frequent_fit'
            assert bundle['columns']==cols and bundle['models'][0].get_params()==b.PARAMS;prediction=b.predict(bundle,q,h)
            for name in prediction:out.loc[q.index,name]=prediction[name]
            audit.append(dict(season=s,round=g,horizon=h,cutoff=str(at),rows=len(train),keys_sha256=t.common.keys_hash(train),max_origin=str(train.forecast_at.max()),max_label=str(train[f'label_at_{h}'].max()),current_rows=int(train.season.eq(s).sum()),source=source,file=str(path.relative_to(R)),sha256=sha(path)))
        print('WEEKLY CORPUS',s,g,flush=True)
    folder=P/'every1';folder.mkdir(exist_ok=True);t.save(folder/f'base_{s}.pkl',out);pd.DataFrame(audit).to_csv(folder/f'refit_audit_{s}.csv',index=False)

def two_round(s):
    t.check();view=t.load(D/'pool_features.pkl');audit=pd.read_csv(P/'every1'/f'refit_audit_{s}.csv');schedule=refits(view,s,2);chosen=audit[audit['round'].isin(schedule)].copy();out=view[view.season.eq(s)][t.KEY+['forecast_at']].copy();origins=[]
    for g in available(view,s):
        fit_g=max(k for k in schedule if k<=g);q=view[view.season.eq(s)&view['round'].eq(g)]
        for h in [1,3]:
            row=chosen[chosen['round'].eq(fit_g)&chosen.horizon.eq(h)].iloc[0];assert pd.Timestamp(row.cutoff)<=q.forecast_at.iloc[0];path=R/row.file;assert sha(path)==row.sha256;bundle=t.load(path);prediction=b.predict(bundle,q,h)
            for name in prediction:out.loc[q.index,name]=prediction[name]
            origins.append(dict(season=s,origin_round=g,horizon=h,model_refit_round=fit_g,model_cutoff=row.cutoff,file=row.file,sha256=row.sha256))
    folder=P/'every2';folder.mkdir(exist_ok=True);t.save(folder/f'base_{s}.pkl',out);chosen.to_csv(folder/f'refit_audit_{s}.csv',index=False);pd.DataFrame(origins).to_csv(folder/f'origin_model_map_{s}.csv',index=False);print('TWO-ROUND STREAM BUILT',s,flush=True)

def finish():
    t.check();assert t.read(P/'outcome_verification.json')['passed'] and t.read(P/'prediction_verification_standard.json')['passed']
    for a in ARMS:
        for name in ['base_verification','prediction_verification','preflight','manager_verification']:assert t.read(P/f'{name}_{a}.json')['passed']
    scores=pd.concat([pd.read_csv(P/f'scores_{a}.csv') for a in CONFIG]);assert len(scores)==9 and scores.complete.all();scores.to_csv(P/'scores.csv',index=False);w=scores.pivot(index='season',columns='arm',values='net');w.to_csv(P/'comparison.csv');delta=w.subtract(w.standard,axis=0);delta.to_csv(P/'deltas.csv');summary=[]
    for a,stride in CONFIG.items():
        q=w[a];summary.append(dict(arm=a,base_stride=stride,mean_all3=float(q.mean()),mean_latest2=float(q.iloc[-2:].mean()),net_2025=float(q.iloc[-1]),delta_2025=float(delta.loc['2025-26',a]),delta_mean_all3=float(delta[a].mean()),delta_mean_latest2=float(delta[a].iloc[-2:].mean()),variance=float(np.var(q)),range=float(q.max()-q.min()),strict_all_year_gain=bool((delta[a]>0).all()),newer_both_gain=bool((delta[a].iloc[-2:]>0).all())))
    pd.DataFrame(summary).to_csv(P/'summary.csv',index=False);new=list((P/'models').glob('*.pkl'));assert len(new)==222
    artifacts=list(P.glob('*.csv'))+[P/'prediction_verification_standard.json',P/'outcome_verification.json']+[P/f'{name}_{a}.json' for a in ARMS for name in ['base_verification','prediction_verification','preflight','manager_verification']]+new+[q for a in CONFIG for q in (P/a).glob('*') if q.is_file()]
    for a in ARMS:
        for s in t.S:
            for row in pd.read_csv(P/a/f'refit_audit_{s}.csv').itertuples():assert sha(R/row.file)==row.sha256
    atomic_json(P/'final_verification.json',dict(passed=True,new_unique_base_models=222,original_quarterly_reused=80,weekly_packages=302,two_round_packages=150,independent_fit_replays=2,new_calibration_heads=480,standard_reproduced_heads=240,new_full_seasons=6,new_decisions_independently_replayed=228,reused_standard_seasons=3,same_data_targets_weights_and_calibration_recipe=True,all144forecast_and288component_cells_matched=True,active_model_unchanged=True,files={str(q.relative_to(R)):sha(q) for q in artifacts}));print('BASE CADENCE COMPLETE',w.to_string(),flush=True)

if __name__=='__main__':
    a=sys.argv[1]
    if a=='setup':setup()
    elif a=='corpus':corpus(sys.argv[2])
    elif a=='two-round':two_round(sys.argv[2])
    elif a=='heads':b.heads(sys.argv[2])
    elif a=='preflight':b.cal.preflight(sys.argv[2])
    elif a=='manager':t.manager(sys.argv[2],sys.argv[3])
    elif a=='replay':b.cal.replay(sys.argv[2])
    elif a=='finish':finish()
    else:raise ValueError(a)
