"""Independent base-weight, prediction, clock and outcome checks."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import base_recency_study as b
from model_lab.common import atomic_json,sha,verify_files
from catboost import CatBoostRegressor,Pool
import pandas as pd,numpy as np
t=b.t;P=b.P;D=b.D;F=b.F

def bases(arm):
    t.check();data=t.load(D/'training.pkl');view=t.load(D/'pool_features.pkl');cols=b.columns();count=0;roundtrip=0;replay=None
    for s in t.S:
        saved=t.load(P/arm/f'base_{s}.pkl').set_index(t.KEY)
        if arm=='standard':audit=pd.read_csv(P/'control_bundle_inventory.csv');audit=audit[audit.season.eq(s)]
        else:audit=pd.read_csv(P/arm/f'base_audit_{s}.csv')
        for row in audit.itertuples():
            at=pd.Timestamp(row.cutoff);h=row.horizon;targets=[f'target_{name}_{h}' for name in ['points','minutes','starts','attack','appearance','residual']];train=data[data.train_eligible&data.forecast_at.lt(at)&data[f'label_at_{h}'].lt(at)&data[targets].notna().all(axis=1)];control=b.control_row(s,row.round,h);assert len(train)==row.rows==control.rows and t.common.keys_hash(train)==row.keys_sha256==control.keys_sha256;assert train.forecast_at.max()<at and train[f'label_at_{h}'].max()<at;model=t.load(R/row.file);assert sha(R/row.file)==row.sha256 and model['columns']==cols and model['models'][0].get_params()==b.PARAMS
            raw=train[cols].to_numpy(float);median=np.array([np.median(c[np.isfinite(c)]) if np.isfinite(c).any() else 0. for c in raw.T]);np.testing.assert_allclose(model['imputer'].statistics_,median,atol=1e-10,rtol=1e-10)
            if arm!='standard':
                age=(at-train.forecast_at).dt.total_seconds().to_numpy()/86400;assert np.all(age>0);decay=2.**(-age/b.CONFIG[arm]);expected=decay*len(train)/decay.sum();weights=np.load(R/row.weight_file);assert sha(R/row.weight_file)==row.weight_sha256;np.testing.assert_allclose(weights['requested_weights'],expected,atol=1e-11,rtol=1e-11);np.testing.assert_array_equal(weights['actual_pool_weights'],weights['requested_weights'].astype(np.float32));assert abs(expected.mean()-1)<1e-12;assert abs(weights['actual_pool_weights'].mean(dtype=np.float64)-1)<1e-7;assert hashlib.sha256(weights['actual_pool_weights'].tobytes()).hexdigest()==model['actual_pool_weight_sha256'];np.testing.assert_allclose(row.current_weight,expected[train.season.eq(s)].sum()/expected.sum(),atol=1e-10,rtol=1e-10);roundtrip+=1
            q=view[view.season.eq(s)&view['round'].between(row.round,min(row.round+3,38))];filled=np.where(np.isfinite(q[cols].to_numpy(float)),q[cols].to_numpy(float),median);x=np.column_stack([filled,(~np.isfinite(q[cols].to_numpy(float))).astype(float)]);rawpred=model['models'][0].predict(x);got=np.column_stack([rawpred[:,:3].sum(1),np.maximum(0,rawpred[:,3]*90),rawpred[:,:3]]);names=[f'component_p{h}',f'component_m{h}',f'base_attack{h}',f'base_appearance{h}',f'base_residual{h}'];np.testing.assert_allclose(got,saved.reindex(pd.MultiIndex.from_frame(q[t.KEY]))[names].to_numpy(),atol=1e-9,rtol=1e-10)
            if arm!='standard' and s=='2025-26' and row.round==1 and h==1:
                # Actual weighted training replay, constructed separately from
                # the implementation and original imputer/Pandas matrix path.
                filled=np.where(np.isfinite(raw),raw,median);train_x=np.column_stack([filled,(~np.isfinite(raw)).astype(float)]);train_y=train[[f'target_attack_{h}',f'target_appearance_{h}',f'target_residual_{h}',f'target_minutes_{h}']].to_numpy(float);train_y[:,3]/=90;direct=CatBoostRegressor(**b.PARAMS);direct.fit(Pool(train_x,label=train_y,weight=expected));np.testing.assert_allclose(direct.predict(x),rawpred,atol=1e-9,rtol=1e-10);replay=dict(season=s,round=1,horizon=1,rows=len(train),prediction_match=True);print('INDEPENDENT WEIGHTED REFIT MATCHED',arm,flush=True)
            count+=1
        if arm=='standard':
            ref=t.load(F/'head_data.pkl').set_index(t.KEY);names=['component_p1','component_m1','component_p3','component_m3'];np.testing.assert_allclose(saved[names],ref.reindex(saved.index)[names],atol=1e-9,rtol=1e-10)
        print('BASES VERIFIED',arm,s,flush=True)
    assert count==80 and (arm=='standard' or (roundtrip==80 and replay is not None))
    atomic_json(P/f'base_verification_{arm}.json',dict(passed=True,packages=80,weight_roundtrips=roundtrip,all_original_row_keys_params_and_unweighted_medians_match=True,all_prediction_components_replayed=True,base_clock_strict=True,weighted_replay=replay));print('ALL80 BASE PACKAGES VERIFIED',arm,flush=True)

def heads(arm):
    t.check();assert t.read(P/f'base_verification_{arm}.json')['passed'];verify_files(P,t.read(P/f'prediction_lock_{arm}.json')['files']);d=t.load(P/f'head_data_{arm}.pkl');original=t.load(F/'head_data.pkl');unchanged=[c for c in original if c not in ['component_p1','component_m1','component_p3','component_m3']];pd.testing.assert_frame_equal(d[unchanged].reset_index(drop=True),original[unchanged].reset_index(drop=True));a=pd.read_csv(P/f'head_audit_{arm}.csv');f=pd.read_csv(P/f'{arm}.csv.gz').set_index(t.KEY);av=pd.read_csv(F/'availability.csv.gz').set_index(t.KEY);complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);control=pd.read_csv(F/'head_audit.csv').set_index(['season','round','offset']);grad=[];count=0
    for row in a.itertuples():
        at=pd.Timestamp(row.cutoff);j=row.offset;train=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)];ref=control.loc[(row.season,row.round,j)];assert len(train)==row.rows==ref.rows and t.common.keys_hash(train)==row.keys_sha256==ref.keys_sha256;assert train.forecast_at.max()<at and train[f'y_at_{j}'].max()<at and h3.loc[train.index].max()<at
        model=t.read(R/row.file);assert sha(R/row.file)==row.sha256 and model['half_life_days']==180 and model['penalty']==.01;raw,anchor,names=t.projection.design(train,'component',j);x,trans=t.projection.transform(raw)
        for field in ['median','mean','std']:np.testing.assert_allclose(model['transform'][field],trans[field],atol=1e-10,rtol=1e-10)
        w=2.**(-((at-train.forecast_at).dt.total_seconds().to_numpy()/86400)/180);beta=np.array(model['beta']);pen=.01*beta;pen[0]=0;gradient=x.T@(w*(x@beta-(train[f'y_{j}'].to_numpy()-anchor)/6))/w.sum()+pen;assert abs(gradient).max()<1e-8;grad.append(float(abs(gradient).max()))
        q=d[d.season.eq(row.season)&d['round'].between(row.round,min(row.round+3,38))];q=q[q['round']+j<=38];prediction=t.projection.predict_projection(q,'component',model);status=av.reindex(pd.MultiIndex.from_frame(q[t.KEY]));prediction[status.known_departed.to_numpy()|(status.confirmed_out_current.to_numpy() if j==0 else False)]=0;np.testing.assert_allclose(prediction,f.reindex(pd.MultiIndex.from_frame(q[t.KEY]))[f'xp_{j}'],atol=1e-9,rtol=1e-10);count+=len(q)
    assert len(a)==240 and np.isfinite(f[[f'xp_{j}' for j in range(8)]]).all().all()
    if arm=='standard':
        ref=pd.read_csv(b.REF/'standard.csv.gz').set_index(t.KEY);pd.testing.assert_index_equal(f.index,ref.index);np.testing.assert_allclose(f[[f'xp_{j}' for j in range(8)]],ref[[f'xp_{j}' for j in range(8)]],atol=1e-9,rtol=1e-10);assert f.can_buy.equals(ref.can_buy)
    atomic_json(P/f'prediction_verification_{arm}.json',dict(passed=True,heads=240,replayed_values=count,same_calibration_recipe_and_teacher_keys=True,all_actual_transforms_train_only=True,completeH3_and_offset_clock_checked=True,max_gradient=max(grad),standard_reproduced=arm=='standard'));print('HEADS VERIFIED',arm,flush=True)

def metrics():
    t.check();d=t.load(F/'head_data.pkl');av=pd.read_csv(F/'availability.csv.gz');d=d.merge(av[t.KEY+['model_can_buy']],on=t.KEY,validate='one_to_one');source=R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz';raw=pd.read_csv(source,usecols=t.KEY+['position','native_goals_scored','native_assists','native_minutes','target_total_points']);raw=raw[raw.season.isin(t.EVAL)].copy()
    assert raw[['native_goals_scored','native_assists','native_minutes','target_total_points']].notna().all().all();raw['actual_attack']=raw.native_goals_scored*raw.position.map(dict(GK=10,DEF=6,MID=5,FWD=4)).fillna(4)+3*raw.native_assists;raw['actual_appearance']=raw.native_minutes.ge(60)*2+(raw.native_minutes.gt(0)&raw.native_minutes.lt(60));raw['actual_residual']=raw.target_total_points-raw.actual_attack-raw.actual_appearance;raw['actual_points']=raw.target_total_points;raw['actual_minutes']=raw.native_minutes;fields=['actual_attack','actual_appearance','actual_residual','actual_points','actual_minutes'];truth=raw.groupby(t.KEY)[fields].sum(min_count=1).reset_index()
    for h in [1,3]:
        pieces=[]
        for j in range(h):
            q=truth.copy();q['round']-=j;pieces.append(d[t.KEY].merge(q,on=t.KEY,how='left',validate='one_to_one'))
        for f in fields:d[f'{f}_{h}']=pd.concat([q[f] for q in pieces],axis=1).sum(axis=1,min_count=h)
    known=d.season.isin(t.EVAL)&d.y_0.notna();np.testing.assert_allclose(d.loc[known,'actual_points_1'],d.loc[known,'y_0'],atol=1e-6,rtol=1e-6)
    # Check raw component decomposition against all common supervised targets
    # where qualified, while retaining excluded-origin outcomes for evaluation.
    train=t.load(D/'training.pkl');check=train[t.KEY+[f'target_{x}_1' for x in ['attack','appearance','residual']]].merge(truth,on=t.KEY,validate='one_to_one');checked=0
    for name in ['attack','appearance','residual']:
        z=check[check[f'target_{name}_1'].notna()];np.testing.assert_allclose(z[f'target_{name}_1'],z[f'actual_{name}'],atol=1e-5,rtol=1e-6);checked+=len(z)
    ref=pd.read_csv(F/'operational_matched.csv.gz').set_index(t.KEY);d['common_rank']=ref.reindex(pd.MultiIndex.from_frame(d[t.KEY])).xp_0.to_numpy();d['common_top']=False
    for (_,_,pos),q in d[d.model_can_buy&d.season.isin(t.EVAL)].groupby(['season','round','position']):d.loc[q.nlargest(dict(GK=5,DEF=20,MID=20,FWD=10)[pos],'common_rank').index,'common_top']=True
    predictions={a:pd.read_csv(P/f'{a}.csv.gz').set_index(t.KEY) for a in b.CONFIG};bases={a:pd.concat([t.load(P/a/f'base_{s}.pkl') for s in t.S]).set_index(t.KEY) for a in b.CONFIG};rows=[];component_rows=[];ranks=[]
    def record(err,actual,s,scope,a,target,h):return dict(season=s,scope=scope,arm=a,target=target,horizon=h,n=len(err),mse=float(np.mean(err**2)),mae=float(np.mean(abs(err))),bias=float(np.mean(err)),actual_variance=float(np.var(actual)))
    for s in t.EVAL:
        q=d[d.season.eq(s)&d.model_can_buy]
        for scope,sub in [('all_buyable',q),('common_top',q[q.common_top]),('common_MID',q[q.common_top&q.position.eq('MID')]),('premium9plus',q[q.price_tenths.ge(90)])]:
            for a in b.CONFIG:
                p=predictions[a].reindex(pd.MultiIndex.from_frame(sub[t.KEY]));z=sub.copy();z['point_prediction']=p.xp_0.to_numpy()
                for h in [1,3]:
                    good=z[[f'y_{j}' for j in range(h)]].notna().all(axis=1)&(z['round']+h<=39);v=z[good];actual=v[[f'y_{j}' for j in range(h)]].sum(axis=1).to_numpy();prediction=p.loc[good.to_numpy(),[f'xp_{j}' for j in range(h)]].sum(axis=1).to_numpy();rows.append(record(prediction-actual,actual,s,scope,a,'points',h));rawbase=bases[a].reindex(pd.MultiIndex.from_frame(v[t.KEY]))
                    valid=v[f'actual_minutes_{h}'].notna().to_numpy();actual_min=v.loc[valid,f'actual_minutes_{h}'].to_numpy();rows.append(record(rawbase.loc[valid,f'component_m{h}'].to_numpy()-actual_min,actual_min,s,scope,a,'minutes',h))
                    for name in ['attack','appearance','residual','points']:
                        col=f'component_p{h}' if name=='points' else f'base_{name}{h}';truth=v[f'actual_{name}_{h}'].to_numpy();assert np.isfinite(truth).all();component_rows.append(record(rawbase[col].to_numpy()-truth,truth,s,scope,a,name,h))
                for g,v in z[z.y_0.notna()].groupby('round'):
                    if v.point_prediction.nunique()>1 and v.y_0.nunique()>1:ranks.append(dict(season=s,scope=scope,arm=a,round=g,n=len(v),spearman=v.point_prediction.corr(v.y_0,method='spearman')))
    m=pd.DataFrame(rows);cm=pd.DataFrame(component_rows);assert len(m)==144 and len(cm)==288
    for frame in [m,cm]:assert frame.groupby(['season','scope','target','horizon']).n.nunique().eq(1).all() and np.isfinite(frame[['mse','mae','bias']]).all().all()
    old=pd.read_csv(b.REF/'forecast_metrics.csv');old=old[old.arm.eq('standard')];sort=['season','scope','arm','target','horizon'];pd.testing.assert_frame_equal(m[m.arm.eq('standard')].sort_values(sort).reset_index(drop=True),old.sort_values(sort).reset_index(drop=True),check_exact=False,atol=1e-9,rtol=1e-9)
    m.to_csv(P/'forecast_metrics.csv',index=False);cm.to_csv(P/'component_metrics.csv',index=False);pd.DataFrame(ranks).to_csv(P/'ranking_by_round.csv',index=False);pd.DataFrame(ranks).groupby(['season','scope','arm']).spearman.mean().to_csv(P/'ranking.csv');atomic_json(P/'outcome_verification.json',dict(passed=True,raw_component_targets_match_training_cells=checked,raw_point_outcomes_match_existing_truth=True,excluded_training_origin2024GW15_kept_in_evaluation=True,forecast_cells=144,component_cells=288,matched_denominators=True,standard48metric_cells_reproduced=True));print('FORECAST AND COMPONENT METRICS VERIFIED',flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='base':bases(sys.argv[2])
    elif action=='heads':heads(sys.argv[2])
    elif action=='metrics':metrics()
    else:raise ValueError(action)
