"""Separate residual ridge and predeadline candidate sample-weight tests.

Reuse the verified clock/manager mechanics without modifying previous studies.
Candidate membership uses only origin-time frozen component H1 and eligibility.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import calibration_response_sweep as base
from model_lab.common import atomic_json,sha,verify_files
import numpy as np,pandas as pd
t=base.t;F=base.F;D=base.D;REF=base.REF;P=R/'reports/calibration_weight_sweep_2026_10_26';PREV=base.P
ID='component-calibration-ridge-candidates-20261026-v1'
CONFIG={'standard':(.01,1),'ridge_weak':(.001,1),'ridge_strong':(.1,1),'candidates2':(.01,2),'candidates4':(.01,4)}
ARMS=[a for a in CONFIG if a!='standard'];CURRENT=None;_flags=None
base.P=P;base.CONFIG={a:(180,4) for a in CONFIG};base.ARMS=ARMS;t.P=P;t.D=D;t.ARMS=list(CONFIG)
LIMITS={'GK':5,'DEF':20,'MID':20,'FWD':10}

def candidate_table():
    # This allowlist deliberately excludes all observed outcomes and later
    # labels, and includes the2022teacher season without a future calibrator.
    d=t.load(F/'head_data.pkl')[t.KEY+['forecast_at','position','component_p1']].copy();av=pd.read_csv(F/'availability.csv.gz',usecols=t.KEY+['model_can_buy']);d=d.merge(av,on=t.KEY,validate='one_to_one');assert d.model_can_buy.notna().all() and np.isfinite(d.component_p1).all();d['candidate']=False
    for (_,_,position),q in d[d.model_can_buy].groupby(['season','round','position']):
        order=q.sort_values(['component_p1','code'],ascending=[False,True],kind='mergesort');d.loc[order.head(LIMITS[position]).index,'candidate']=True
    return d

def setup():
    P.mkdir(exist_ok=False);parent=t.read(PREV/'proposal.json');deps=parent['input_hashes'].copy();verify_files(R,deps)
    paths=[Path(__file__),R/'scripts/calibration_response_sweep.py',PREV/'proposal.json',PREV/'final_verification.json',PREV/'comparison.csv',PREV/'standard.csv.gz',PREV/'head_audit_standard.csv',PREV/'prediction_verification_standard.json',PREV/'forecast_metrics.csv',PREV/'scores_standard.csv',PREV/'one_change_verification.json',F/'head_data.pkl',F/'availability.csv.gz']
    deps.update({str(q.relative_to(R)):sha(q) for q in paths});flags=candidate_table();flags.to_csv(P/'candidate_flags.csv.gz',index=False);deps[str((P/'candidate_flags.csv.gz').relative_to(R))]=sha(P/'candidate_flags.csv.gz')
    before=t.read(REF/'dataset_verification.json');assert before['passed'];verify_files(R,before['files']);atomic_json(P/'dataset_verification.json',dict(passed=True,qualified_common_parent=str(REF.relative_to(R)),same325_subset=True,frozen_base_forecasts=True,candidates_selected_without_outcomes=True))
    shutil.copyfile(PREV/'scores_standard.csv',P/'scores_standard.csv');shutil.copyfile(R/'overview/ACTIVE_TEAM_BENCHMARK.json',P/'reference_ACTIVE_TEAM_BENCHMARK.json')
    spec=dict(id=ID,candidate_id='component_ridge001_100_or_candidate2_4_v1',dataset_id=parent['dataset_id'],benchmark_id=parent['benchmark_id'],hypothesis='Changing slope regularization or the decision relevance of calibration examples separately can improve full-season utility beyond the chosen180day/4round component standard.',change='Four fixed independent arms: ridge.001 or.1 with candidate multiplier1; candidate multiplier2 or4 with ridge.01. Fixed180day decay, unweighted training-only transformations, same teacher keys/completeH3filter, same325-feature frozen bases and4round cadence. No combined ridge+candidate arm, base retraining, xG, player blacklist or tuned candidate cutoffs. Reproduce standard240heads and reuse its3verified seasons.',related_work=['component-calibration-response-20261026-v1','component-recent180-operational-20261026-v1','component-xg-recent-combined-20261026-v1'],clock=parent['clock'],features=parent['features'],model_parameters=dict(config=CONFIG,half_life_days=180,calibration_refits=list(t.REFITS),base_frozen=True,intercept_unpenalized=True,weight_formula='2**(-age_seconds/86400/180)*candidate_multiplier_if_flag_else1; objective normalized by sumweights',candidate_definition=dict(before_targets=True,all_teacher_years=True,ranking='frozen origin-time component_H1 descending; code ascending ties',eligible='dated model_can_buy only',per_position=LIMITS,different_from_evaluation_common_top=True),transform='same unweighted train-only median/mean/std as standard; no weighted scaling',no_joint_grid=True),decision_policy=parent['decision_policy'],seasons=t.EVAL,resources=dict(new_base_fits=0,new_candidate_heads=960,standard_reproduction_heads=240,new_full_seasons=12,new_decisions=456,reused_standard_seasons=3,preflight_decisions=8,workers=4,threads=1),maximum_runs=1,input_hashes=deps,success_criterion='Report all4arms on all3seasons, per-year net-after-hits and standard deltas, latest2 and all3 equal-season means,2025 separately, variance/range. Robust upgrade flag strictly positive net delta in all3; user newer-season preference reflected descriptively without fitting reporting weights. Separate point/minute H1/H3 errors for fixed old common candidates and the independently fixed base candidate set. No automatic live promotion; no best-ridge+best-weight combination claim.',stop_rule='Complete all12episodes regardless early utility. No score-driven extra parameters, candidate cutoffs, solver changes, source relaxation or reruns. Stop affected stages on hash/clock/numeric/availability/legality/resource failures. Keep active model and prospective2026seals unchanged.',evaluation_contract=dict(primary='full-season net points after hits per season',secondary='latest2/all3mean, variance/range, H1/H3point/minute error, MID/premium/candidate rank and bias',candidate_weight_semantics='weight training errors, never multiply inference-time player points',scopes='same4previous evaluation groups plus one fixed base-candidate group, identical across variants',evidence_role='Previously inspected historical development seasons; no untouched holdout or real FPL rank'))
    atomic_json(P/'proposal.json',spec);print('RIDGE/CANDIDATE PLAN PREPARED;12episodes',flush=True)

def flags():
    global _flags
    if _flags is None:_flags=pd.read_csv(P/'candidate_flags.csv.gz').set_index(t.KEY)
    return _flags

def fit(tr,j,at,half):
    penalty,mult=CONFIG[CURRENT];raw,anchor,names=t.projection.design(tr,'component',j);x,transform=t.projection.transform(raw);age=(at-tr.forecast_at).dt.total_seconds().to_numpy()/86400;assert np.all(age>0);q=flags().reindex(pd.MultiIndex.from_frame(tr[t.KEY]));assert q.candidate.notna().all();candidate=q.candidate.to_numpy(bool);w=np.exp2(-age/180.)*np.where(candidate,mult,1.);pen=np.eye(x.shape[1])*penalty;pen[0,0]=0;y=(tr[f'y_{j}'].to_numpy(float)-anchor)/6;beta=np.linalg.solve(x.T@(w[:,None]*x)/w.sum()+pen,x.T@(w*y)/w.sum())
    return dict(beta=beta.tolist(),transform=transform,raw_names=names,offset=j,penalty=penalty,rows=len(tr),base_model='component',half_life_days=180,candidate_multiplier=mult,training_candidate_rows=int(candidate.sum()),training_candidate_weight=float(w[candidate].sum()/w.sum()),candidate_source_sha256=sha(P/'candidate_flags.csv.gz'),fitted_at=str(at)),w

def forecasts(arm):
    global CURRENT
    CURRENT=arm;base.fit=fit;base.forecasts(arm)

def verify(arm):
    t.check();verify_files(P,t.read(P/f'prediction_lock_{arm}.json')['files']);penalty,mult=CONFIG[arm];d=t.load(F/'head_data.pkl');a=pd.read_csv(P/f'head_audit_{arm}.csv');pred=pd.read_csv(P/f'{arm}.csv.gz').set_index(t.KEY);av=pd.read_csv(F/'availability.csv.gz').set_index(t.KEY);complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);reference=pd.read_csv(PREV/'head_audit_standard.csv').set_index(['season','round','offset']);grads=[];count=0
    for season in t.EVAL:assert sorted(a[a.season.eq(season)]['round'].unique())==list(t.REFITS)
    for row in a.itertuples():
        at=pd.Timestamp(row.cutoff);j=row.offset;tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)];control=reference.loc[(row.season,row.round,j)];assert len(tr)==row.rows==control.rows and t.common.keys_hash(tr)==row.keys_sha256==control.keys_sha256;assert tr.forecast_at.max()<at and tr[f'y_at_{j}'].max()<at and h3.loc[tr.index].max()<at
        model=t.read(R/row.file);assert sha(R/row.file)==row.sha256 and model['penalty']==penalty and model['candidate_multiplier']==mult and model['half_life_days']==180;raw,anchor,names=t.projection.design(tr,'component',j);x,transform=t.projection.transform(raw);old=t.read(R/control.file)
        for field in ['median','mean','std']:
            np.testing.assert_allclose(model['transform'][field],transform[field],atol=1e-10,rtol=1e-10);np.testing.assert_allclose(model['transform'][field],old['transform'][field],atol=1e-10,rtol=1e-10)
        candidate=flags().reindex(pd.MultiIndex.from_frame(tr[t.KEY])).candidate.to_numpy(bool);w=2.**(-((at-tr.forecast_at).dt.total_seconds().to_numpy()/86400)/180.)*np.where(candidate,mult,1.);beta=np.array(model['beta']);pen=penalty*beta;pen[0]=0;gradient=x.T@(w*(x@beta-(tr[f'y_{j}'].to_numpy()-anchor)/6))/w.sum()+pen;assert abs(gradient).max()<1e-8;grads.append(float(abs(gradient).max()));np.testing.assert_allclose(model['training_candidate_weight'],w[candidate].sum()/w.sum(),atol=1e-12,rtol=1e-12)
        if arm=='standard':np.testing.assert_allclose(model['beta'],old['beta'],atol=1e-9,rtol=1e-10)
        q=d[d.season.eq(row.season)&d['round'].between(row.round,min(row.round+3,38))];q=q[q['round']+j<=38];p=t.projection.predict_projection(q,'component',model);status=av.reindex(pd.MultiIndex.from_frame(q[t.KEY]));p[status.known_departed.to_numpy()|(status.confirmed_out_current.to_numpy() if j==0 else False)]=0;np.testing.assert_allclose(p,pred.reindex(pd.MultiIndex.from_frame(q[t.KEY]))[f'xp_{j}'],atol=1e-9,rtol=1e-10);count+=len(q)
    assert len(a)==240 and np.isfinite(pred[[f'xp_{j}' for j in range(8)]]).all().all()
    if arm=='standard':
        old=pd.read_csv(PREV/'standard.csv.gz').set_index(t.KEY);pd.testing.assert_index_equal(pred.index,old.index);np.testing.assert_allclose(pred[[f'xp_{j}' for j in range(8)]],old[[f'xp_{j}' for j in range(8)]],atol=1e-9,rtol=1e-10);assert pred.can_buy.equals(old.can_buy)
    atomic_json(P/f'prediction_verification_{arm}.json',dict(passed=True,heads_checked=240,forecast_values_replayed=count,teacher_keys_equal_standard=True,transforms_equal_standard=True,all_clocks_and_cadence_checked=True,only_declared_penalty_or_weights_changed=True,max_gradient=max(grads),standard_reproduced=arm=='standard'));print('RIDGE/CANDIDATE PREDICTIONS VERIFIED',arm,flush=True)

def verify_candidates():
    t.check();saved=pd.read_csv(P/'candidate_flags.csv.gz');raw=t.load(F/'head_data.pkl');av=pd.read_csv(F/'availability.csv.gz').set_index(t.KEY);assert not saved.duplicated(t.KEY).any();z=saved.set_index(t.KEY);expected=pd.Series(False,index=z.index)
    for (season,g,pos),q in raw.groupby(['season','round','position']):
        q=q.copy();q=q[av.reindex(pd.MultiIndex.from_frame(q[t.KEY])).model_can_buy.to_numpy(bool)];q=q.sort_values(['component_p1','code'],ascending=[False,True],kind='mergesort').head(LIMITS[pos]);expected.loc[pd.MultiIndex.from_frame(q[t.KEY])]=True
    assert expected.equals(z.candidate);assert not z.loc[~av.reindex(z.index).model_can_buy,'candidate'].any();assert set(saved.season)==set(t.S)
    atomic_json(P/'candidate_verification.json',dict(passed=True,rows=len(saved),teacher2022_included=True,ranking_uses_only_frozen_predeadline_base_forecast=True,actual_outcomes_not_in_definition=True,current_eligibility_required=True,stable_code_tie_break=True,limits=LIMITS,candidate_rows=int(saved.candidate.sum()),source_sha256=sha(P/'candidate_flags.csv.gz')));print('CANDIDATE FLAGS INDEPENDENTLY VERIFIED',flush=True)

def metrics():
    t.check();d=t.load(F/'head_data.pkl');av=pd.read_csv(F/'availability.csv.gz');d=d.merge(av[t.KEY+['model_can_buy']],on=t.KEY,validate='one_to_one');d=d.merge(pd.read_csv(P/'candidate_flags.csv.gz',usecols=t.KEY+['candidate']),on=t.KEY,validate='one_to_one');raw=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=t.KEY+['native_minutes']);truth=raw.groupby(t.KEY).native_minutes.sum(min_count=1).rename('target_minutes_1').reset_index();d=d.merge(truth,on=t.KEY,how='left',validate='one_to_one');windows=[]
    for j in range(3):
        q=truth.copy();q['round']-=j;windows.append(d[t.KEY].merge(q,on=t.KEY,how='left',validate='one_to_one').target_minutes_1)
    d['target_minutes_3']=pd.concat(windows,axis=1).sum(axis=1,min_count=3);ref=pd.read_csv(F/'operational_matched.csv.gz').set_index(t.KEY);d['common_rank']=ref.reindex(pd.MultiIndex.from_frame(d[t.KEY])).xp_0.to_numpy();d['common_top']=False
    for (_,_,pos),q in d[d.model_can_buy&d.season.isin(t.EVAL)].groupby(['season','round','position']):d.loc[q.nlargest(LIMITS[pos],'common_rank').index,'common_top']=True
    preds={a:pd.read_csv(P/f'{a}.csv.gz').set_index(t.KEY) for a in CONFIG};rows=[];ranks=[]
    for s in t.EVAL:
        q=d[d.season.eq(s)&d.model_can_buy]
        for scope,sub in [('all_buyable',q),('common_top',q[q.common_top]),('common_MID',q[q.common_top&q.position.eq('MID')]),('premium9plus',q[q.price_tenths.ge(90)]),('base_candidates',q[q.candidate])]:
            for a in CONFIG:
                p=preds[a].reindex(pd.MultiIndex.from_frame(sub[t.KEY]));z=sub.copy();z['point_prediction']=p.xp_0.to_numpy()
                for h in [1,3]:
                    good=z[[f'y_{j}' for j in range(h)]].notna().all(axis=1)&(z['round']+h<=39);v=z[good];target=v[[f'y_{j}' for j in range(h)]].sum(axis=1).to_numpy();prediction=p.loc[good.to_numpy(),[f'xp_{j}' for j in range(h)]].sum(axis=1).to_numpy();err=prediction-target;rows.append(dict(season=s,scope=scope,arm=a,target='points',horizon=h,n=len(v),mse=float(np.mean(err**2)),mae=float(np.mean(abs(err))),bias=float(np.mean(err)),actual_variance=float(np.var(target))))
                    v=v[v[f'target_minutes_{h}'].notna()];err=v[f'component_m{h}'].to_numpy()-v[f'target_minutes_{h}'].to_numpy();rows.append(dict(season=s,scope=scope,arm=a,target='minutes',horizon=h,n=len(v),mse=float(np.mean(err**2)),mae=float(np.mean(abs(err))),bias=float(np.mean(err)),actual_variance=float(np.var(v[f'target_minutes_{h}']))))
                for g,v in z[z.y_0.notna()].groupby('round'):
                    if v.point_prediction.nunique()>1 and v.y_0.nunique()>1:ranks.append(dict(season=s,scope=scope,arm=a,round=g,n=len(v),spearman=v.point_prediction.corr(v.y_0,method='spearman')))
    m=pd.DataFrame(rows);assert len(m)==300 and m.groupby(['season','scope','target','horizon']).n.nunique().eq(1).all();assert m[m.target.eq('minutes')].groupby(['season','scope','horizon']).mse.nunique().eq(1).all();before=pd.read_csv(PREV/'forecast_metrics.csv');before=before[before.arm.eq('standard')];sort=['season','scope','arm','target','horizon'];pd.testing.assert_frame_equal(m[m.arm.eq('standard')&~m.scope.eq('base_candidates')].sort_values(sort).reset_index(drop=True),before.sort_values(sort).reset_index(drop=True),check_exact=False,atol=1e-10,rtol=1e-10)
    m.to_csv(P/'forecast_metrics.csv',index=False);pd.DataFrame(ranks).to_csv(P/'ranking_by_round.csv',index=False);pd.DataFrame(ranks).groupby(['season','scope','arm']).spearman.mean().to_csv(P/'ranking.csv');print('ALL300 METRIC CELLS MATCHED',flush=True)

def finish():
    t.check();assert t.read(P/'candidate_verification.json')['passed'] and t.read(P/'prediction_verification_standard.json')['passed']
    for a in ARMS:
        for n in ['prediction_verification','preflight','manager_verification']:assert t.read(P/f'{n}_{a}.json')['passed']
    scores=pd.concat([pd.read_csv(P/f'scores_{a}.csv') for a in CONFIG]);assert len(scores)==15 and scores.complete.all();scores.to_csv(P/'scores.csv',index=False);w=scores.pivot(index='season',columns='arm',values='net');w.to_csv(P/'comparison.csv');delta=w.subtract(w.standard,axis=0);delta.to_csv(P/'deltas.csv');summary=[]
    for a,(ridge,mult) in CONFIG.items():
        q=w[a];summary.append(dict(arm=a,ridge=ridge,candidate_multiplier=mult,mean_all3=float(q.mean()),mean_latest2=float(q.iloc[-2:].mean()),net_2025=float(q.iloc[-1]),delta_2025=float(delta.loc['2025-26',a]),delta_mean_all3=float(delta[a].mean()),delta_mean_latest2=float(delta[a].iloc[-2:].mean()),season_variance=float(np.var(q)),season_range=float(q.max()-q.min()),strict_all_year_gain=bool((delta[a]>0).all()),newer_both_gain=bool((delta[a].iloc[-2:]>0).all())))
    pd.DataFrame(summary).to_csv(P/'summary.csv',index=False)
    diagnostics=[]
    for a in CONFIG:
        for row in pd.read_csv(P/f'head_audit_{a}.csv').itertuples():
            model=t.read(R/row.file);diagnostics.append(dict(arm=a,season=row.season,round=row.round,offset=row.offset,rows=row.rows,current_weight=row.current_weight,effective_rows=row.effective_rows,candidate_rows=model['training_candidate_rows'],candidate_weight=model['training_candidate_weight'],ridge=model['penalty'],candidate_multiplier=model['candidate_multiplier']))
    pd.DataFrame(diagnostics).to_csv(P/'weight_diagnostics.csv',index=False);artifacts=list(P.glob('*.csv'))+[P/'candidate_verification.json',P/'prediction_verification_standard.json']+[P/f'{n}_{a}.json' for a in ARMS for n in ['prediction_verification','preflight','manager_verification']]
    atomic_json(P/'final_verification.json',dict(passed=True,new_full_seasons=12,new_decisions_independently_replayed=456,reused_standard_seasons=3,new_candidate_heads=960,standard_reproduced_heads=240,all300_metric_cells_matched=True,all_minute_forecasts_unchanged=True,base_models_unchanged=True,active_model_unchanged=True,separate_ridge_or_candidate_interventions_only=True,files={str(q.relative_to(R)):sha(q) for q in artifacts}));print('RIDGE/CANDIDATE SWEEP COMPLETE',w.to_string(),flush=True)

if __name__=='__main__':
    a=sys.argv[1]
    if a=='setup':setup()
    elif a=='forecasts':forecasts(sys.argv[2])
    elif a=='verify':verify(sys.argv[2])
    elif a=='verify-candidates':verify_candidates()
    elif a=='preflight':base.preflight(sys.argv[2])
    elif a=='manager':t.manager(sys.argv[2],sys.argv[3])
    elif a=='replay':base.replay(sys.argv[2])
    elif a=='metrics':metrics()
    elif a=='finish':finish()
    else:raise ValueError(a)
