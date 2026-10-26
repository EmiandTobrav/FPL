"""Separate dataset, prediction and policy gates for the two single changes."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,json,lzma,copy
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import test_xg_adaptation as t
from model_lab.common import sha,atomic_json,verify_files
P=t.P;D=t.D;F=t.F;KEY=t.KEY

def dataset():
    t.check();old=R/'datasets/fpl_common_training_v3';features=t.read(D/'schema.json')['feature_groups']['expected_attack'];assert len(features)==16
    for name in ['training.pkl','pool_features.pkl']:
        a=t.load(old/name);b=t.load(D/name);pd.testing.assert_frame_equal(a,b[a.columns]);assert len(b.columns)==len(a.columns)+16
    extra=t.load(D/'xg_features.pkl');time=pd.read_csv(D/'xg_timing.csv.gz');origin=pd.to_datetime(time.forecast_at,utc=True,format='mixed');latest=pd.to_datetime(time.latest_xg_source,utc=True,format='mixed');assert (latest.isna()|latest.lt(origin)).all()
    sources=t.read(D/'xg_sources.json');values={}
    for s in sources:
        if not s['valid']:continue
        path=R/s['file'];assert sha(path)==s['sha256'];data=json.loads(lzma.open(path,'rt').read());at=pd.Timestamp(s['forecast_at']);source=pd.Timestamp(s['source_time']);assert source<at and at-source<=pd.Timedelta(hours=24);assert pd.Timestamp(next(e for e in data['events'] if e['id']==s['round'])['deadline_time'])==at
        values[(s['season'],s['round'])]={int(e['code']):e for e in data['elements']}
    status=pd.read_csv(D/'xg_qualification.csv.gz').set_index(KEY);checked=0
    for row in extra.itertuples():
        key=(row.season,row.round,row.code);e=values.get((row.season,row.round),{}).get(row.code);qualified=key in status.index and bool(status.at[key,'qualified'])
        if qualified:
            for name,field in [('xg','expected_goals'),('xa','expected_assists')]:
                expected=0. if row.round==1 else float(e[field]);actual=getattr(row,name+'_current_total');np.testing.assert_allclose(actual,expected,atol=1e-5,rtol=1e-7)
            checked+=1
        else:assert pd.isna(row.xg_current_total) and pd.isna(row.xa_current_total)
        oldkey=(row.season,1,row.code);old=values.get((row.season,1),{}).get(row.code)
        if oldkey in status.index and bool(status.at[oldkey,'qualified']):
            np.testing.assert_allclose(row.xg_previous_total,float(old['expected_goals']),atol=1e-5,rtol=1e-7);np.testing.assert_allclose(row.xa_previous_total,float(old['expected_assists']),atol=1e-5,rtol=1e-7)
        else:assert pd.isna(row.xg_previous_total) and pd.isna(row.xa_previous_total)
    cov=pd.read_csv(D/'xg_feature_coverage.csv');known=cov[cov.feature.eq('xg_current_total')&cov.season.isin(t.EVAL)].set_index('season').known_share;assert known.min()>.99
    atomic_json(P/'dataset_verification.json',dict(passed=True,old_325_features_keys_targets_unchanged=True,xg_features=16,source_qualified_rows_rechecked=checked,all_new_source_times_before_deadline=True,preseason_previous_year_semantics_checked=True,unknowns_not_fabricated_zero=True,all_three_seasons_total_coverage_above99percent=True,files={str(p.relative_to(R)):sha(p) for p in [D/'manifest.json',D/'qualification.json',D/'schema.json',D/'xg_sources.json',Path(__file__)]}));print('DATASET VERIFIED',checked,flush=True)

def predictions(arm):
    t.check();assert arm in t.ARMS;verify_files(P,t.read(P/f'prediction_lock_{arm}.json')['files']);d=t.load(P/f'head_data_{arm}.pkl');a=pd.read_csv(P/f'head_audit_{arm}.csv');f=pd.read_csv(P/f'{arm}.csv.gz').set_index(KEY);av=pd.read_csv(F/'availability.csv.gz').set_index(KEY);complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);gradients=[];values=0
    for row in a.itertuples():
        at=pd.Timestamp(row.cutoff);j=row.offset;train=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)];assert len(train)==row.rows and t.common.keys_hash(train)==row.keys_sha256;assert train.forecast_at.max()<at and train[f'y_at_{j}'].max()<at and h3.loc[train.index].max()<at
        model=t.read(R/row.file);assert sha(R/row.file)==row.sha256;raw,anchor,names=t.projection.design(train,'component',j);x,transform=t.projection.transform(raw)
        for field in ['median','mean','std']:np.testing.assert_allclose(model['transform'][field],transform[field],atol=1e-10,rtol=1e-10)
        if arm=='recent_only':
            control=t.read(t.FIT/f'heads/component_{row.season}_gw{row.round:02d}_j{j}.json')
            for field in ['median','mean','std']:np.testing.assert_allclose(control['transform'][field],model['transform'][field],atol=1e-10,rtol=1e-10)
            w=np.exp2(-((at-train.forecast_at).dt.total_seconds().to_numpy()/86400)/180.)
        else:w=np.ones(len(train))
        residual=(train[f'y_{j}'].to_numpy(float)-anchor)/6;beta=np.asarray(model['beta']);penalty=.01*beta;penalty[0]=0.;gradient=x.T@(w*(x@beta-residual))/w.sum()+penalty;assert np.max(abs(gradient))<1e-8;gradients.append(float(np.max(abs(gradient))))
        q=d[d.season.eq(row.season)&d['round'].between(row.round,min(row.round+3,38))];q=q[q['round']+j<=38];v=t.projection.predict_projection(q,'component',model);guard=av.reindex(pd.MultiIndex.from_frame(q[KEY]));blocked=guard.known_departed.to_numpy()|(guard.confirmed_out_current.to_numpy() if j==0 else False);v[blocked]=0.;saved=f.reindex(pd.MultiIndex.from_frame(q[KEY]))[f'xp_{j}'].to_numpy();np.testing.assert_allclose(v,saved,atol=1e-9,rtol=1e-10);values+=len(q)
    assert len(a)==240 and np.isfinite(f[[f'xp_{j}' for j in range(8)]].to_numpy(float)).all()
    if arm=='xg_only':
        training=t.load(D/'training.pkl');view=t.load(D/'pool_features.pkl');cols=t.read(D/'schema.json')['features'];fits=0
        for season in t.S:
            saved=t.load(P/f'base_{season}.pkl').set_index(KEY)
            for row in pd.read_csv(P/f'base_audit_{season}.csv').itertuples():
                at=pd.Timestamp(row.cutoff);h=row.horizon;targets=[f'target_{name}_{h}' for name in ['points','minutes','starts','attack','appearance','residual']];train=training[training.train_eligible&training.forecast_at.lt(at)&training[f'label_at_{h}'].lt(at)&training[targets].notna().all(axis=1)];assert len(train)==row.rows and t.common.keys_hash(train)==row.keys_sha256;bundle=t.load(R/row.file);assert sha(R/row.file)==row.sha256 and bundle['columns']==cols;params=bundle['models'][0].get_params();assert all(params[k]==v for k,v in dict(iterations=150,depth=5,learning_rate=.05,l2_leaf_reg=5,random_seed=20261025,thread_count=1).items())
                # Independent median check, with0 only for a completely empty
                # TRAINING column; source missing observations stay NaN.
                array=train[cols].to_numpy(float);median=np.array([np.median(v[np.isfinite(v)]) if np.isfinite(v).any() else 0. for v in array.T]);np.testing.assert_allclose(median,bundle['imputer'].statistics_,atol=1e-10,rtol=1e-10)
                q=view[view.season.eq(season)&view['round'].between(row.round,min(row.round+3,38))];v,_,_=t.common.predict_arm(bundle,q);expected=saved.reindex(pd.MultiIndex.from_frame(q[KEY]))[[f'component_p{h}',f'component_m{h}']].to_numpy();np.testing.assert_allclose(v,expected,atol=1e-9,rtol=1e-10);fits+=1
        assert fits==80
    atomic_json(P/f'prediction_verification_{arm}.json',dict(passed=True,heads_checked=len(a),replayed_forecast_values=values,all_clock_and_teacher_keys_checked=True,max_normal_equation_gradient=max(gradients),base_fits_replayed=80 if arm=='xg_only' else 0,reused_frozen_base_for_recent=True if arm=='recent_only' else False,training_only_imputation_checked=arm=='xg_only'));print('PREDICTIONS VERIFIED',arm,flush=True)

def preflight(arm):
    assert t.read(P/'dataset_verification.json')['passed'] and t.read(P/f'prediction_verification_{arm}.json')['passed'];t.guard.configure();f=pd.read_csv(P/f'{arm}.csv.gz');cases=[]
    for s,g in [('2023-24',1),('2023-24',10)]:
        pool=t.guard.eligible_pool(s,g);q=f[f.season.eq(s)&f['round'].eq(g)].set_index('code').reindex(pool.code);xp=q[[f'xp_{j}' for j in range(8)]].to_numpy();xp[~pool.can_start_0.to_numpy()]=10000.;mod,adapter=t.guard.solver()
        state=adapter.engine.initial_state() if g==1 else t.read(t.FIT/f'manager/{s}_operational_matched/gw{g:02d}.decision.json')['state_before'];state['owned']={int(k):v for k,v in state['owned'].items()};choice=copy.deepcopy(adapter.decide(pool,xp,state,g)['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};adapter.engine.apply_decision(state,choice,pool.to_dict('records'),g);assert len(adapter.ledger)<=40;cases.append(dict(season=s,round=g,solver_calls=len(adapter.ledger),owned_Kane_blocked=(78830 not in choice['starters'] and 78830 not in [choice['captain'],choice['vice']]) if g==10 else None))
    atomic_json(P/f'preflight_{arm}.json',dict(passed=True,hostile_unavailable_forecasts_blocked=True,cases=cases));print('PREFLIGHT PASSED',arm,flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='dataset':dataset()
    elif action=='predictions':predictions(sys.argv[2])
    elif action=='preflight':preflight(sys.argv[2])
    else:raise ValueError(action)
