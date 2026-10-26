"""Causal base-training time weights, fixed current recent180 calibration."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,shutil,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import calibration_response_sweep as cal
from model_lab.common import atomic_json,sha,verify_files
from sklearn.impute import SimpleImputer
from catboost import CatBoostRegressor,Pool
import numpy as np,pandas as pd
t=cal.t;F=cal.F;D=cal.D;FIT=t.FIT;REF=cal.P
P=R/'reports/base_recency_2026_10_26';ID='component-base-recency-20261026-v1'
CONFIG={'standard':None,'base365':365,'base180':180};ARMS=['base365','base180']
cal.P=P;cal.ARMS=ARMS;t.P=P;t.D=D;t.ARMS=list(CONFIG)
PARAMS=dict(iterations=150,learning_rate=.05,depth=5,l2_leaf_reg=5,loss_function='MultiRMSE',thread_count=1,random_seed=20261025,verbose=False,allow_writing_files=False,allow_const_label=True)

def columns():return t.read(R/'datasets/fpl_common_training_v3/schema.json')['features']
def control_row(s,g,h):return pd.read_csv(FIT/f'component_audit_{s}.csv').query('round==@g and horizon==@h').iloc[0]
def control_path(row):return FIT/row.file
def select(d,at,h):
    targets=[f'target_{name}_{h}' for name in ['points','minutes','starts','attack','appearance','residual']]
    return d[d.train_eligible&d.forecast_at.lt(at)&d[f'label_at_{h}'].lt(at)&d[targets].notna().all(axis=1)].copy()
def matrix(d,cols,imputer=None):
    a=d[cols].to_numpy(float)
    if imputer is None:imputer=SimpleImputer(strategy='median',add_indicator=False,keep_empty_features=True);filled=imputer.fit_transform(a)
    else:filled=imputer.transform(a)
    return np.column_stack([filled,(~np.isfinite(a)).astype(float)]),imputer
def labels(d,h):return np.column_stack([d[f'target_{n}_{h}'].to_numpy(float) for n in ['attack','appearance','residual']]+[d[f'target_minutes_{h}'].to_numpy(float)/90])
def weights(d,at,half):
    age=(at-d.forecast_at).dt.total_seconds().to_numpy()/86400;assert np.all(age>0)
    raw=np.ones(len(d)) if half is None else np.exp2(-age/half)
    return raw/raw.mean(),age
def train_bundle(d,cols,h,at,half):
    x,imp=matrix(d,cols);y=labels(d,h);w,age=weights(d,at,half);pool=Pool(x,label=y,weight=w);actual=np.asarray(pool.get_weight(),dtype=np.float32);np.testing.assert_array_equal(actual,w.astype(np.float32));assert abs(float(actual.sum(dtype=np.float64))/len(d)-1)<1e-7
    model=CatBoostRegressor(**PARAMS);model.fit(pool)
    return dict(name='component',columns=cols,imputer=imp,models=[model],horizon=h,base_half_life_days=half,weight_normalization='mean1',fit_cutoff=str(at),actual_pool_weight_sha256=hashlib.sha256(actual.tobytes()).hexdigest()),w,actual,age
def predict(bundle,q,h):
    x,_=matrix(q,bundle['columns'],bundle['imputer']);raw=bundle['models'][0].predict(x);p,_prob,_dist=t.common.predict_arm(bundle,q)
    return pd.DataFrame({f'component_p{h}':p[:,0],f'component_m{h}':p[:,1],f'base_attack{h}':raw[:,0],f'base_appearance{h}':raw[:,1],f'base_residual{h}':raw[:,2]},index=q.index)

def setup():
    P.mkdir(exist_ok=False);parent=t.read(REF/'proposal.json');deps=parent['input_hashes'].copy();verify_files(R,deps)
    paths=[Path(__file__),R/'scripts/verify_base_recency_study.py',D/'training.pkl',D/'pool_features.pkl',D/'schema.json',R/'datasets/fpl_common_training_v3/schema.json',REF/'proposal.json',REF/'final_verification.json',REF/'standard.csv.gz',REF/'scores_standard.csv',REF/'head_audit_standard.csv',REF/'forecast_metrics.csv',R/'reports/calibration_weight_sweep_2026_10_26/result.json']
    inventory=[]
    for s in t.S:
        path=FIT/f'component_audit_{s}.csv';paths.append(path)
        for row in pd.read_csv(path).itertuples():
            bundle=control_path(row);assert sha(bundle)==row.sha256;paths.append(bundle);inventory.append(dict(season=s,round=row.round,horizon=row.horizon,cutoff=row.cutoff,rows=row.rows,keys_sha256=row.keys_sha256,file=str(bundle.relative_to(R)),sha256=row.sha256))
    deps.update({str(path.relative_to(R)):sha(path) for path in paths});pd.DataFrame(inventory).to_csv(P/'control_bundle_inventory.csv',index=False)
    shutil.copyfile(R/'overview/ACTIVE_TEAM_BENCHMARK.json',P/'reference_ACTIVE_TEAM_BENCHMARK.json');shutil.copyfile(REF/'scores_standard.csv',P/'scores_standard.csv')
    proof=t.read(cal.REF/'dataset_verification.json');assert proof['passed'];verify_files(R,proof['files']);atomic_json(P/'dataset_verification.json',dict(passed=True,same_qualified_training_rows_and325_features=True,no_xg=True,base_models_retrained_only_with_time_weights=True))
    spec=dict(id=ID,candidate_id='component_base_half365_180_calibration180_fixed_v1',dataset_id=parent['dataset_id'],benchmark_id=parent['benchmark_id'],hypothesis='Uniform old/new base-training rows may limit adaptation that post-calibration cannot repair. Change only base row-age loss weights, with current calibration recipe fixed, and test all three matched seasons.',change='Two fixed base-training candidates365/180day half-life versus uniform baseline. Exact same325features, training rows, unweighted median imputation, four-target scaling, CatBoost parameters and quarterly cadence. Weights based on past forecast-origin age and normalized to mean1 before Pool construction, preserving overall loss/L2 scale. Rebuild all80base packages per arm including2022teacher year; refit480calibration heads on each arms own causal OOF bases with the existing180day/.01 recipe. No xG, extra candidate weights, new half-life search, different cadence or automatic deployment.',related_work=['component-calibration-ridge-candidates-20261026-v1','component-calibration-response-20261026-v1','component-recent180-operational-20261026-v1'],clock=parent['clock'],features=parent['features'],model_parameters=dict(base_half_life_days=CONFIG,base_params=PARAMS,base_loss='MultiRMSE attack/appearance/residual/normalized_minutes',minutes_scale='minutes/90 unchanged',normalization='exp2(-age_seconds/86400/half)/mean(exp2(...))',age='fit cutoff minus row.forecast_at',imputation='same unweighted training-only medians plus missing indicators',refits=list(t.REFITS),calibration=dict(half_life_days=180,ridge=.01,intercept_unpenalized=True,teacher_completeH3=True,offsets=list(range(8)),transform='unweighted train-only median/mean/std',candidate_multiplier=1),no_hyperparameter_search=True),decision_policy=parent['decision_policy'],seasons=t.EVAL,resources=dict(new_weighted_base_fits=160,uniform_control_identity_refits=2,independent_weighted_replay_refits=2,new_calibration_heads=480,standard_calibration_reproduction=240,new_full_seasons=6,new_manager_decisions=228,reused_standard_seasons=3,preflight_decisions=4,workers=4,threads=1),maximum_runs=1,input_hashes=deps,success_criterion='Report both arms and each year net-after-hits, latest2/all3means and variance/range. Robust upgrade flag only if strictly more net in all3; newer-season gains described separately per explicit user preference. Separately evaluate final H1/H3points, base minutes and attack/appearance/residual/basepoint errors, fixed common candidate/MID/premium rank and bias. No automatic model promotion; no global optimum, new-season holdout or winning-FPL claim.',stop_rule='Complete160weighted packages and6episodes without score-driven pruning, extra half-lives, solver/source relaxations or reruns. Stop affected stages on mismatch in original row keys/params/clocks, weight round-trip, numerical reproduction, availability or legality. Preserve original files and active model.',evaluation_contract=dict(primary='full-season net points after hits per season',secondary='same4fixed evaluation groups; H1/H3point/minute/component errors; MIDrank; latest2means and spread',control='80 frozen uniform base bundles and selected recent180calibration; reconstruct control forecasts and component outputs; reuse3verified manager episodes',replay='two uniform identity refits before new candidates; independently rebuild one2025GW1H1 weighted model per arm',evidence_role='Retrospective development over already-inspected seasons; no2026/27outcomes or live recommendation'))
    atomic_json(P/'proposal.json',spec);print('BASE RECENCY PLAN PREPARED:160weighted packages;6episodes',flush=True)

def identity():
    t.check();d=t.load(D/'training.pkl');view=t.load(D/'pool_features.pkl');cols=columns();checks=[]
    for s,g,h in [('2023-24',1,1),('2025-26',37,3)]:
        row=control_row(s,g,h);at=pd.Timestamp(row.cutoff);tr=select(d,at,h);assert len(tr)==row.rows and t.common.keys_hash(tr)==row.keys_sha256;bundle,w,actual,age=train_bundle(tr,cols,h,at,None);old=t.load(control_path(row));assert old['models'][0].get_params()==PARAMS;np.testing.assert_allclose(bundle['imputer'].statistics_,old['imputer'].statistics_,atol=1e-10,rtol=1e-10);q=view[view.season.eq(s)&view['round'].between(g,min(g+3,38))];x,_=matrix(q,cols,bundle['imputer']);np.testing.assert_allclose(bundle['models'][0].predict(x),old['models'][0].predict(x),atol=1e-9,rtol=1e-10);assert np.all(actual==1);checks.append(dict(season=s,round=g,horizon=h,rows=len(tr),raw_four_target_predictions_match=True))
        print('UNIFORM IDENTITY REPLAY',s,g,h,'passed',flush=True)
    atomic_json(P/'uniform_identity_verification.json',dict(passed=True,refits=2,explicit_unit_weights_match_original_no_weight_models=True,checks=checks))

def bases(arm,s):
    t.check();d=t.load(D/'training.pkl');view=t.load(D/'pool_features.pkl');cols=columns();assert len(cols)==325;out=view[view.season.eq(s)][t.KEY+['forecast_at']].copy();audit=[]
    for g in t.REFITS:
        q=view[view.season.eq(s)&view['round'].between(g,min(g+3,38))]
        for h in [1,3]:
            row=control_row(s,g,h);at=q.loc[q['round'].eq(g),'forecast_at'].iloc[0];assert at==pd.Timestamp(row.cutoff)
            if arm=='standard':bundle=t.load(control_path(row));assert sha(control_path(row))==row.sha256 and bundle['columns']==cols
            else:
                tr=select(d,at,h);assert len(tr)==row.rows and t.common.keys_hash(tr)==row.keys_sha256;bundle,w,actual,age=train_bundle(tr,cols,h,at,CONFIG[arm]);old=t.load(control_path(row));np.testing.assert_allclose(bundle['imputer'].statistics_,old['imputer'].statistics_,atol=1e-10,rtol=1e-10)
                modelpath=P/f'models/{arm}_{s}_gw{g:02d}_h{h}.pkl';t.save(modelpath,bundle);wp=P/f'weights/{arm}_{s}_gw{g:02d}_h{h}.npz';wp.parent.mkdir(exist_ok=True);np.savez_compressed(wp,requested_weights=w,actual_pool_weights=actual)
                audit.append(dict(arm=arm,season=s,round=g,horizon=h,cutoff=str(at),half_life_days=CONFIG[arm],rows=len(tr),keys_sha256=t.common.keys_hash(tr),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'label_at_{h}'].max()),current_rows=int(tr.season.eq(s).sum()),current_weight=float(w[tr.season.eq(s)].sum()/w.sum()),effective_rows=float(w.sum()**2/(w@w)),weight_min=float(actual.min()),weight_max=float(actual.max()),weight_mean=float(actual.mean(dtype=np.float64)),file=str(modelpath.relative_to(R)),sha256=sha(modelpath),weight_file=str(wp.relative_to(R)),weight_sha256=sha(wp)))
            prediction=predict(bundle,q,h)
            for name in prediction:out.loc[q.index,name]=prediction[name]
        print('BASE',arm,s,g,flush=True)
    assert np.isfinite(out.drop(columns=t.KEY+['forecast_at'])).all().all();folder=P/arm;folder.mkdir(exist_ok=True);t.save(folder/f'base_{s}.pkl',out)
    if arm!='standard':pd.DataFrame(audit).to_csv(folder/f'base_audit_{s}.csv',index=False)

def teacher_data(arm):
    d=t.load(F/'head_data.pkl');pred=pd.concat([t.load(P/arm/f'base_{s}.pkl') for s in t.S],ignore_index=True);return d.drop(columns=['component_p1','component_m1','component_p3','component_m3']).merge(pred,on=t.KEY+['forecast_at'],validate='one_to_one')

def heads(arm):
    t.check();d=teacher_data(arm);t.save(P/f'head_data_{arm}.pkl',d);complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);control=pd.read_csv(F/'head_audit.csv');out=[];audits=[]
    for s in t.EVAL:
        for g in range(1,39):
            q=d[d.season.eq(s)&d['round'].eq(g)];at=q.forecast_at.iloc[0]
            if g in t.REFITS:
                models={}
                for j in range(8):
                    tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)];old=control[control.season.eq(s)&control['round'].eq(g)&control.offset.eq(j)].iloc[0];assert len(tr)==old.rows and t.common.keys_hash(tr)==old.keys_sha256;model,w=t.fit_recent(tr,j,at);models[j]=model;path=P/f'heads/{arm}_{s}_gw{g:02d}_j{j}.json';atomic_json(path,model);audits.append(dict(arm=arm,season=s,round=g,offset=j,cutoff=str(at),rows=len(tr),keys_sha256=t.common.keys_hash(tr),current_rows=int(tr.season.eq(s).sum()),current_weight=float(w[tr.season.eq(s)].sum()/w.sum()),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'y_at_{j}'].max()),max_h3_label=str(h3.loc[tr.index].max()),file=str(path.relative_to(R)),sha256=sha(path)))
                print('HEADS',arm,s,g,flush=True)
            z=q[t.KEY+['forecast_at','can_buy']].copy()
            for j in range(8):z[f'xp_{j}']=t.projection.predict_projection(q,'component',models[j]) if g+j<=38 else 0.
            out.append(z)
    f=pd.concat(out,ignore_index=True);av=pd.read_csv(F/'availability.csv.gz');f=f.merge(av[t.KEY+['model_can_buy','known_departed','confirmed_out_current']],on=t.KEY,validate='one_to_one');f.can_buy=f.model_can_buy
    for j in range(8):f.loc[f.known_departed|(f.confirmed_out_current if j==0 else False),f'xp_{j}']=0.
    f.drop(columns=['model_can_buy','known_departed','confirmed_out_current']).to_csv(P/f'{arm}.csv.gz',index=False);pd.DataFrame(audits).to_csv(P/f'head_audit_{arm}.csv',index=False);atomic_json(P/f'prediction_lock_{arm}.json',dict(sealed_before_manager=True,files={n:sha(P/n) for n in [f'{arm}.csv.gz',f'head_audit_{arm}.csv',f'head_data_{arm}.pkl']}))

def finish():
    t.check();assert t.read(P/'uniform_identity_verification.json')['passed'] and t.read(P/'prediction_verification_standard.json')['passed']
    assert t.read(P/'outcome_verification.json')['passed']
    for arm in ARMS:
        for name in ['base_verification','prediction_verification','preflight','manager_verification']:assert t.read(P/f'{name}_{arm}.json')['passed']
    scores=pd.concat([pd.read_csv(P/f'scores_{a}.csv') for a in CONFIG]);assert len(scores)==9 and scores.complete.all();scores.to_csv(P/'scores.csv',index=False);w=scores.pivot(index='season',columns='arm',values='net');w.to_csv(P/'comparison.csv');delta=w.subtract(w.standard,axis=0);delta.to_csv(P/'deltas.csv');summary=[]
    for a in CONFIG:
        q=w[a];summary.append(dict(arm=a,base_half_life_days=CONFIG[a],mean_all3=float(q.mean()),mean_latest2=float(q.iloc[-2:].mean()),net_2025=float(q.iloc[-1]),delta_2025=float(delta.loc['2025-26',a]),delta_mean_all3=float(delta[a].mean()),delta_mean_latest2=float(delta[a].iloc[-2:].mean()),variance=float(np.var(q)),range=float(q.max()-q.min()),strict_all_year_gain=bool((delta[a]>0).all()),newer_both_gain=bool((delta[a].iloc[-2:]>0).all())))
    pd.DataFrame(summary).to_csv(P/'summary.csv',index=False)
    for arm in ARMS:
        for s in t.S:
            for row in pd.read_csv(P/arm/f'base_audit_{s}.csv').itertuples():assert sha(R/row.file)==row.sha256 and sha(R/row.weight_file)==row.weight_sha256
    artifacts=list(P.glob('*.csv'))+[P/'uniform_identity_verification.json',P/'prediction_verification_standard.json',P/'outcome_verification.json']+[P/f'{name}_{a}.json' for a in ARMS for name in ['base_verification','prediction_verification','preflight','manager_verification']]+list((P/'models').glob('*.pkl'))+list((P/'weights').glob('*.npz'))+[q for arm in CONFIG for q in (P/arm).glob('*') if q.is_file()]
    atomic_json(P/'final_verification.json',dict(passed=True,new_weighted_base_packages=160,uniform_identity_refits=2,independent_weighted_replays=2,new_calibration_heads=480,standard_reproduced_heads=240,new_full_seasons=6,new_decisions_independently_replayed=228,reused_standard_seasons=3,active_model_unchanged=True,same_rows_features_imputation_params_and_calibration_recipe=True,all144_forecast_and288_component_metric_cells_matched=True,files={str(path.relative_to(R)):sha(path) for path in artifacts}));print('BASE RECENCY COMPLETE',w.to_string(),flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='setup':setup()
    elif action=='identity':identity()
    elif action=='base':bases(sys.argv[2],sys.argv[3])
    elif action=='heads':heads(sys.argv[2])
    elif action=='preflight':cal.preflight(sys.argv[2])
    elif action=='manager':t.manager(sys.argv[2],sys.argv[3])
    elif action=='replay':cal.replay(sys.argv[2])
    elif action=='finish':finish()
    else:raise ValueError(action)
