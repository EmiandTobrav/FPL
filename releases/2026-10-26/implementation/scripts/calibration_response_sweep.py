"""Bounded independent half-life and calibration-cadence tests; fixed bases."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import test_xg_adaptation as t
from model_lab.common import atomic_json,sha,verify_files
import pandas as pd,numpy as np
P=R/'reports/calibration_response_sweep_2026_10_26';D=R/'datasets/fpl_common_training_v5';F=t.F;REF=R/'reports/xg_adaptation_2026_10_26_v2'
CONFIG={'standard':(180,4),'half60':(60,4),'half90':(90,4),'half365':(365,4),'every1':(180,1),'every2':(180,2),'every8':(180,8)}
ARMS=[a for a in CONFIG if a!='standard'];ID='component-calibration-response-20261026-v1'
t.P=P;t.D=D;t.ARMS=list(CONFIG)

def setup():
    P.mkdir(exist_ok=False);old=t.read(F/'inputs.json');deps=old['input_hashes'].copy()
    # The only changed upstream source is the explicitly selected active model.
    for n,h in deps.items():
        if n!='overview/ACTIVE_TEAM_BENCHMARK.json':assert sha(R/n)==h,n
    deps['overview/ACTIVE_TEAM_BENCHMARK.json']=sha(R/'overview/ACTIVE_TEAM_BENCHMARK.json')
    paths=[Path(__file__),R/'scripts/test_xg_adaptation.py',R/'scripts/report_xg_adaptation.py',R/'scripts/verify_xg_adaptation.py',R/'scripts/common_season_comparison.py',R/'model_lab/recent_component_forecaster.py',R/'model_lab/active.py',R/'datasets/fpl_2026_27_best_effort_v1/manifest.json',D/'manifest.json',D/'release.json',R/'datasets/fpl_common_training_v3/manifest.json',F/'inputs.json',F/'head_data.pkl',F/'head_audit.csv',F/'operational_matched.csv.gz',F/'availability.csv.gz',F/'policy_backend_hashes.json',REF/'recent_only.csv.gz',REF/'head_audit_recent_only.csv',REF/'scores_recent_only.csv',REF/'manager_verification_recent_only.json',REF/'prediction_verification_recent_only.json',REF/'final_verification.json',R/'reports/component_recent180_activation_2026_10_26/activation_review.json',R/'reports/component_recent180_activation_2026_10_26/verification.json']+[F/n for n in old['files']]+list((F/'policy_backend').glob('*.py'))
    for s in t.EVAL:paths+=list((REF/'manager'/f'{s}_recent_only').glob('*.json'))
    deps.update({str(p.relative_to(R)):sha(p) for p in paths})
    active=t.read(R/'overview/ACTIVE_TEAM_BENCHMARK.json')
    spec=dict(id=ID,candidate_id='component_calibration_half60_90_365_or_stride1_2_8_v1',dataset_id='fpl_2026_27_best_effort_v1',benchmark_id=active['id'],hypothesis='Calibration response speed can change net team utility. Isolate decay age and refit interval separately against the now-selected180day/4round standard on the identical three historical seasons.',change='Six fixed one-variable candidates: half-life60/90/365days each with4round calibration; stride1/2/8rounds each with180day half-life. Standard180/4 independently reproduced and its3verified episodes reused. No joint grid, base retraining, feature/xG change, season multiplier, shrinkage change or outcome-driven second-stage combination.',related_work=['component-recent180-operational-20261026-v1','component-xg-adaptation-20261026-v2','component-xg-recent-combined-20261026-v1'],clock='Same qualified official origin deadlines, old statistical/calendar/market proxies. Forecast origin, offset target and all completedH3 teacher outcomes strictly before each calibration fit. No2026/27 outcomes.',features=dict(raw=325,shared_common_dataset='qualifiedV5; original325subset',projection='unchanged component H1/H3 point/minute forecasts and original projection design'),model_parameters=dict(config=CONFIG,base_refits=list(t.REFITS),base_frozen=True,calibration_refits='1+k*stride through38',penalty=.01,intercept_unpenalized=True,transform='unweighted training-only median/mean/std; decay changes only mean residual objective weights',weight_formula='2**(-(fit_cutoff-teacher_forecast_at).days/half_life)',completed_H3_teacher_filter=True,forecasts=8,no_joint_grid=True,no_parameter_search_beyond_fixed_six=True),decision_policy=t.read(REF/'proposal.json')['decision_policy'],seasons=t.EVAL,resources=dict(new_base_fits=0,new_candidate_heads=sum(3*len(range(1,39,CONFIG[a][1]))*8 for a in ARMS),standard_reproduction_heads=240,new_full_seasons=18,new_manager_decisions=684,reused_standard_seasons=3,preflight_decisions=12,workers=4,threads=1),maximum_runs=1,input_hashes=deps,success_criterion='Report every candidate and every season, standard-relative deltas, all3 and latest2 equal-season means,2025/26 separately, dispersion, points/minute error and candidate ranking. Robust all-year upgrade flag only if strictly more net points every season. User newer-season preference reflected descriptively; no automatic live replacement or tuning of season aggregation weights. Any forecast improvement claim also needs yearly improvement for that target. Never report a winning combination from these one-variable tests.',stop_rule='Stop affected stage on input/hash/clock/numerical/legality/resource failure. No score-driven rerun, extra half-life/interval, source relaxation or candidate pruning. Complete all18episodes even when early results disappoint. Keep active model and sealed2026forecasts unchanged.',evaluation_contract=dict(primary='net full-season points after hits per season',secondary='latest2mean, all3mean, descriptive season variance/range, H1/H3 mean errors, fixed common candidate/MID/premium rank and bias',scope='Retrospective development sweep over previously inspected seasons; no untouched holdout and no competitive-rank claim',cadence_scope='Only post-calibration timing; user explicitly chose to leave base retraining every4rounds'))
    spec['model_parameters']['weight_formula']='2**(-((fit_cutoff-teacher_forecast_at).total_seconds()/86400)/half_life_days)'
    atomic_json(P/'proposal.json',spec);scores=pd.read_csv(REF/'scores_recent_only.csv');scores.arm='standard';scores.to_csv(P/'scores_standard.csv',index=False)
    proof=t.read(REF/'dataset_verification.json');assert proof['passed'];verify_files(R,proof['files']);atomic_json(P/'dataset_verification.json',dict(passed=True,qualified_common_parent=str(REF.relative_to(R)),same325_subset=True,base_forecasts_frozen=True))
    print('SWEEP PREPARED',spec['resources'],flush=True)

def fit(tr,j,at,half):
    raw,anchor,names=t.projection.design(tr,'component',j);x,transform=t.projection.transform(raw);age=(at-tr.forecast_at).dt.total_seconds().to_numpy()/86400;assert np.all(age>0);w=np.exp2(-age/half);pen=np.eye(x.shape[1])*.01;pen[0,0]=0;y=(tr[f'y_{j}'].to_numpy(float)-anchor)/6;beta=np.linalg.solve(x.T@(w[:,None]*x)/w.sum()+pen,x.T@(w*y)/w.sum())
    return dict(beta=beta.tolist(),transform=transform,raw_names=names,offset=j,penalty=.01,rows=len(tr),base_model='component',half_life_days=half,fitted_at=str(at)),w

def forecasts(arm):
    t.check();half,stride=CONFIG[arm];d=t.load(F/'head_data.pkl');complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);out=[];audit=[];old_audit=pd.read_csv(F/'head_audit.csv')
    for s in t.EVAL:
        prior=f'{int(s[:4])-1}-{int(s[:4])%100:02d}'
        for g in range(1,39):
            q=d[d.season.eq(s)&d['round'].eq(g)];at=q.forecast_at.iloc[0]
            if (g-1)%stride==0:
                models={}
                for j in range(8):
                    tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)].copy();model,w=fit(tr,j,at,half);models[j]=model;path=P/f'heads/{arm}_{s}_gw{g:02d}_j{j}.json';atomic_json(path,model)
                    if g in t.REFITS:
                        control=old_audit[old_audit.season.eq(s)&old_audit['round'].eq(g)&old_audit.offset.eq(j)].iloc[0];assert len(tr)==control.rows and t.common.keys_hash(tr)==control.keys_sha256
                    audit.append(dict(arm=arm,season=s,round=g,offset=j,half_life_days=half,stride=stride,cutoff=str(at),rows=len(tr),keys_sha256=t.common.keys_hash(tr),current_rows=int(tr.season.eq(s).sum()),current_weight=float(w[tr.season.eq(s).to_numpy()].sum()/w.sum()),prior_season_weight=float(w[tr.season.eq(prior).to_numpy()].sum()/w.sum()),effective_rows=float(w.sum()**2/(w@w)),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'y_at_{j}'].max()),max_h3_label=str(h3.loc[tr.index].max()),file=str(path.relative_to(R)),sha256=sha(path)))
                print('CALIBRATION',arm,s,g,flush=True)
            z=q[t.KEY+['forecast_at','can_buy']].copy()
            for j in range(8):z[f'xp_{j}']=t.projection.predict_projection(q,'component',models[j]) if g+j<=38 else 0.
            out.append(z)
    f=pd.concat(out,ignore_index=True);av=pd.read_csv(F/'availability.csv.gz');f=f.merge(av[t.KEY+['model_can_buy','known_departed','confirmed_out_current']],on=t.KEY,validate='one_to_one');f.can_buy=f.model_can_buy
    for j in range(8):f.loc[f.known_departed|(f.confirmed_out_current if j==0 else False),f'xp_{j}']=0.
    f.drop(columns=['model_can_buy','known_departed','confirmed_out_current']).to_csv(P/f'{arm}.csv.gz',index=False);pd.DataFrame(audit).to_csv(P/f'head_audit_{arm}.csv',index=False);atomic_json(P/f'prediction_lock_{arm}.json',dict(sealed_before_manager=True,files={f'{arm}.csv.gz':sha(P/f'{arm}.csv.gz'),f'head_audit_{arm}.csv':sha(P/f'head_audit_{arm}.csv')}))

def verify(arm):
    t.check();verify_files(P,t.read(P/f'prediction_lock_{arm}.json')['files']);half,stride=CONFIG[arm];d=t.load(F/'head_data.pkl');audit=pd.read_csv(P/f'head_audit_{arm}.csv');f=pd.read_csv(P/f'{arm}.csv.gz').set_index(t.KEY);av=pd.read_csv(F/'availability.csv.gz').set_index(t.KEY);complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);last=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);grad=[];values=0
    for s in t.EVAL:assert sorted(audit[audit.season.eq(s)]['round'].unique())==list(range(1,39,stride))
    for row in audit.itertuples():
        at=pd.Timestamp(row.cutoff);j=row.offset;tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&last.lt(at)];assert len(tr)==row.rows and t.common.keys_hash(tr)==row.keys_sha256;assert tr.forecast_at.max()<at and tr[f'y_at_{j}'].max()<at and last.loc[tr.index].max()<at
        model=t.read(R/row.file);assert sha(R/row.file)==row.sha256 and model['half_life_days']==half;raw,anchor,names=t.projection.design(tr,'component',j);x,trans=t.projection.transform(raw)
        for field in ['median','mean','std']:np.testing.assert_allclose(model['transform'][field],trans[field],atol=1e-10,rtol=1e-10)
        age=(at-tr.forecast_at).dt.total_seconds().to_numpy()/86400;w=2.**(-age/half);beta=np.array(model['beta']);pen=.01*beta;pen[0]=0;g=x.T@(w*(x@beta-(tr[f'y_{j}'].to_numpy()-anchor)/6))/w.sum()+pen;assert abs(g).max()<1e-8;grad.append(float(abs(g).max()))
        np.testing.assert_allclose(row.current_weight,w[tr.season.eq(row.season)].sum()/w.sum(),atol=1e-12,rtol=1e-12)
        prior=f'{int(row.season[:4])-1}-{int(row.season[:4])%100:02d}'
        np.testing.assert_allclose(row.prior_season_weight,w[tr.season.eq(prior)].sum()/w.sum(),atol=1e-12,rtol=1e-12);np.testing.assert_allclose(row.effective_rows,w.sum()**2/(w@w),atol=1e-8,rtol=1e-12)
        q=d[d.season.eq(row.season)&d['round'].between(row.round,min(row.round+stride-1,38))];q=q[q['round']+j<=38];v=t.projection.predict_projection(q,'component',model);status=av.reindex(pd.MultiIndex.from_frame(q[t.KEY]));v[status.known_departed.to_numpy()|(status.confirmed_out_current.to_numpy() if j==0 else False)]=0.;np.testing.assert_allclose(v,f.reindex(pd.MultiIndex.from_frame(q[t.KEY]))[f'xp_{j}'].to_numpy(),atol=1e-9,rtol=1e-10);values+=len(q)
    expected=3*len(range(1,39,stride))*8;assert len(audit)==expected and np.isfinite(f[[f'xp_{j}' for j in range(8)]]).all().all()
    if arm=='standard':
        parent=pd.read_csv(REF/'recent_only.csv.gz').set_index(t.KEY);pd.testing.assert_index_equal(parent.index,f.index);np.testing.assert_allclose(f[[f'xp_{j}' for j in range(8)]],parent[[f'xp_{j}' for j in range(8)]],atol=1e-9,rtol=1e-10);assert f.can_buy.equals(parent.can_buy)
    atomic_json(P/f'prediction_verification_{arm}.json',dict(passed=True,heads_checked=expected,replayed_forecast_values=values,all_clocks_and_cadence_checked=True,transform_train_only=True,held_between_own_refits=True,max_gradient=max(grad),standard_reproduced=arm=='standard'));print('PREDICTIONS VERIFIED',arm,expected,flush=True)

def preflight(arm):
    # Same proven dataset/source gate; only learned calibration coefficients vary.
    if not (P/'dataset_verification.json').exists():
        proof=t.read(REF/'dataset_verification.json');assert proof['passed'];verify_files(R,proof['files']);atomic_json(P/'dataset_verification.json',dict(passed=True,qualified_common_parent=str(REF.relative_to(R)),same325_subset=True,base_forecasts_frozen=True))
    from scripts import verify_xg_adaptation as v
    v.preflight(arm)

def replay(arm):
    from scripts import report_xg_adaptation as r
    r.managers(arm)

def metrics():
    t.check();d=t.load(F/'head_data.pkl');av=pd.read_csv(F/'availability.csv.gz');d=d.merge(av[t.KEY+['model_can_buy']],on=t.KEY,validate='one_to_one');source=R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz';raw=pd.read_csv(source,usecols=t.KEY+['native_minutes']);truth=raw.groupby(t.KEY).native_minutes.sum(min_count=1).rename('target_minutes_1').reset_index();d=d.merge(truth,on=t.KEY,how='left',validate='one_to_one');windows=[]
    for j in range(3):
        q=truth.copy();q['round']-=j;windows.append(d[t.KEY].merge(q,on=t.KEY,how='left',validate='one_to_one').target_minutes_1)
    d['target_minutes_3']=pd.concat(windows,axis=1).sum(axis=1,min_count=3);ref=pd.read_csv(F/'operational_matched.csv.gz').set_index(t.KEY);d['common_rank']=ref.reindex(pd.MultiIndex.from_frame(d[t.KEY])).xp_0.to_numpy();d['common_top']=False
    for (_,_,pos),q in d[d.model_can_buy&d.season.isin(t.EVAL)].groupby(['season','round','position']):d.loc[q.nlargest(dict(GK=5,DEF=20,MID=20,FWD=10)[pos],'common_rank').index,'common_top']=True
    preds={a:pd.read_csv(P/f'{a}.csv.gz').set_index(t.KEY) for a in CONFIG};rows=[];ranks=[]
    for s in t.EVAL:
        q=d[d.season.eq(s)&d.model_can_buy]
        for scope,sub in [('all_buyable',q),('common_top',q[q.common_top]),('common_MID',q[q.common_top&q.position.eq('MID')]),('premium9plus',q[q.price_tenths.ge(90)])]:
            for a in CONFIG:
                p=preds[a].reindex(pd.MultiIndex.from_frame(sub[t.KEY]));z=sub.copy();z['point_prediction']=p.xp_0.to_numpy()
                for h in [1,3]:
                    good=z[[f'y_{j}' for j in range(h)]].notna().all(axis=1)&(z['round']+h<=39);v=z[good];target=v[[f'y_{j}' for j in range(h)]].sum(axis=1).to_numpy();pred=p.loc[good.to_numpy(),[f'xp_{j}' for j in range(h)]].sum(axis=1).to_numpy();err=pred-target;rows.append(dict(season=s,scope=scope,arm=a,target='points',horizon=h,n=len(v),mse=float(np.mean(err**2)),mae=float(np.mean(abs(err))),bias=float(np.mean(err)),actual_variance=float(np.var(target))))
                    v=v[v[f'target_minutes_{h}'].notna()];err=v[f'component_m{h}'].to_numpy()-v[f'target_minutes_{h}'].to_numpy();rows.append(dict(season=s,scope=scope,arm=a,target='minutes',horizon=h,n=len(v),mse=float(np.mean(err**2)),mae=float(np.mean(abs(err))),bias=float(np.mean(err)),actual_variance=float(np.var(v[f'target_minutes_{h}']))))
                for g,v in z[z.y_0.notna()].groupby('round'):
                    if v.point_prediction.nunique()>1 and v.y_0.nunique()>1:ranks.append(dict(season=s,scope=scope,arm=a,round=g,n=len(v),spearman=v.point_prediction.corr(v.y_0,method='spearman')))
    m=pd.DataFrame(rows);assert len(m)==336 and m.groupby(['season','scope','target','horizon']).n.nunique().eq(1).all();assert m[m.target.eq('minutes')].groupby(['season','scope','horizon']).mse.nunique().eq(1).all()
    before=pd.read_csv(REF/'forecast_metrics.csv');before=before[before.arm.eq('recent_only')].copy();before.arm='standard';sort=['season','scope','arm','target','horizon'];pd.testing.assert_frame_equal(m[m.arm.eq('standard')].sort_values(sort).reset_index(drop=True),before.sort_values(sort).reset_index(drop=True),check_exact=False,atol=1e-10,rtol=1e-10)
    m.to_csv(P/'forecast_metrics.csv',index=False);pd.DataFrame(ranks).to_csv(P/'ranking_by_round.csv',index=False);pd.DataFrame(ranks).groupby(['season','scope','arm']).spearman.mean().to_csv(P/'ranking.csv');print('ALL336 METRIC CELLS MATCHED',flush=True)

def finish():
    t.check();assert t.read(P/'prediction_verification_standard.json')['passed']
    for arm in ARMS:
        for name in ['prediction_verification','preflight','manager_verification']:assert t.read(P/f'{name}_{arm}.json')['passed']
    scores=pd.concat([pd.read_csv(P/f'scores_{a}.csv') for a in CONFIG]);scores.to_csv(P/'scores.csv',index=False);w=scores.pivot(index='season',columns='arm',values='net');w.to_csv(P/'comparison.csv');delta=w.subtract(w.standard,axis=0);delta.to_csv(P/'deltas.csv');summary=[]
    for a,(half,stride) in CONFIG.items():
        q=w[a];summary.append(dict(arm=a,half_life_days=half,calibration_stride=stride,mean_all3=float(q.mean()),mean_latest2=float(q.iloc[-2:].mean()),net_2025=float(q.iloc[-1]),delta_2025=float(delta.loc['2025-26',a]),delta_all3_mean=float(delta[a].mean()),delta_latest2_mean=float(delta[a].iloc[-2:].mean()),season_population_variance=float(np.var(q)),season_range=float(q.max()-q.min()),strict_all_year_gain=bool((delta[a]>0).all()),newer_both_gain=bool((delta[a].iloc[-2:]>0).all())))
    pd.DataFrame(summary).to_csv(P/'summary.csv',index=False);weights=pd.concat([pd.read_csv(P/f'head_audit_{a}.csv') for a in CONFIG]);weights.to_csv(P/'weight_diagnostics.csv',index=False)
    artifacts=list(P.glob('*.csv'))+[P/f'{name}_{a}.json' for a in ARMS for name in ['prediction_verification','preflight','manager_verification']]+[P/'prediction_verification_standard.json']
    atomic_json(P/'final_verification.json',dict(passed=True,new_full_seasons=18,new_decisions_independently_replayed=684,reused_standard_seasons=3,standard_reproduction_heads=240,new_candidate_heads=sum(3*len(range(1,39,CONFIG[a][1]))*8 for a in ARMS),base_models_unchanged=True,active_model_unchanged=True,six_separate_changes_only=True,all336_metric_cells_same_denominators=True,all_minute_predictions_unchanged=True,files={str(p.relative_to(R)):sha(p) for p in artifacts}));print('SWEEP COMPLETE',w.to_string(),flush=True)

if __name__=='__main__':
    a=sys.argv[1]
    if a=='setup':setup()
    elif a=='forecasts':forecasts(sys.argv[2])
    elif a=='verify':verify(sys.argv[2])
    elif a=='preflight':preflight(sys.argv[2])
    elif a=='manager':t.manager(sys.argv[2],sys.argv[3])
    elif a=='replay':replay(sys.argv[2])
    elif a=='metrics':metrics()
    elif a=='finish':finish()
    else:raise ValueError(a)
