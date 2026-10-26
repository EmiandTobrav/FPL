"""Independent schedule, train clock, matrix and fresh-fit verification."""
from scripts import base_cadence_study as c
from scripts import verify_base_recency_study as v
import sys
import pandas as pd
import numpy as np
from catboost import CatBoostRegressor
from model_lab.common import atomic_json,sha
b=c.b;t=c.t;P=c.P;R=c.R

def bases(arm):
    if arm=='standard':return v.bases(arm)
    t.check();data=t.load(c.D/'training.pkl');view=t.load(c.D/'pool_features.pkl');cols=b.columns();count=0;origins=0;replays=0
    stride=c.CONFIG[arm]
    for s in t.S:
        audit=pd.read_csv(P/arm/f'refit_audit_{s}.csv');saved=t.load(P/arm/f'base_{s}.pkl').set_index(t.KEY)
        available=sorted(view.loc[view.season.eq(s),'round'].unique());grid=[g for g in available if (g-1)%stride==0]
        assert sorted(audit['round'].unique())==grid and len(audit)==2*len(grid)
        models={}
        for row in audit.itertuples():
            at=pd.Timestamp(row.cutoff);h=row.horizon;targets=[f'target_{n}_{h}' for n in ['points','minutes','starts','attack','appearance','residual']]
            train=data[data.train_eligible&data.forecast_at.lt(at)&data[f'label_at_{h}'].lt(at)&data[targets].notna().all(axis=1)]
            assert len(train)==row.rows and t.common.keys_hash(train)==row.keys_sha256
            assert train.forecast_at.max()<at and train[f'label_at_{h}'].max()<at
            model=t.load(R/row.file);assert sha(R/row.file)==row.sha256 and model['columns']==cols and model['models'][0].get_params()==b.PARAMS
            raw=train[cols].to_numpy(float);median=np.array([np.median(x[np.isfinite(x)]) if np.isfinite(x).any() else 0. for x in raw.T]);np.testing.assert_allclose(model['imputer'].statistics_,median,atol=1e-10,rtol=1e-10)
            if row.round in t.REFITS:
                original=b.control_row(s,row.round,h);assert row.sha256==original.sha256 and row.keys_sha256==original.keys_sha256
            else:assert model['uniform_base_training'] and model['trained_from_scratch']
            if arm=='every2':
                weekly=pd.read_csv(P/'every1'/f'refit_audit_{s}.csv');link=weekly[weekly['round'].eq(row.round)&weekly.horizon.eq(h)].iloc[0];assert link.file==row.file and link.sha256==row.sha256
            models[(row.round,h)]=(model,median,row)
            replay=(arm=='every1' and row.round==2 and h==1) or (arm=='every2' and row.round==15 and h==3)
            if s=='2025-26' and replay:
                x=np.column_stack([np.where(np.isfinite(raw),raw,median),(~np.isfinite(raw)).astype(float)]);y=train[[f'target_{n}_{h}' for n in ['attack','appearance','residual','minutes']]].to_numpy(float);y[:,3]/=90
                direct=CatBoostRegressor(**b.PARAMS);direct.fit(x,y);q=view[view.season.eq(s)&view['round'].eq(row.round)];qr=q[cols].to_numpy(float);qx=np.column_stack([np.where(np.isfinite(qr),qr,median),(~np.isfinite(qr)).astype(float)])
                np.testing.assert_allclose(direct.predict(qx),model['models'][0].predict(qx),atol=1e-9,rtol=1e-10);replays+=1
            count+=1
        mapping=pd.read_csv(P/arm/f'origin_model_map_{s}.csv') if arm=='every2' else None
        for g in available:
            fit_g=max(k for k in grid if k<=g);q=view[view.season.eq(s)&view['round'].eq(g)];qr=q[cols].to_numpy(float)
            for h in [1,3]:
                model,median,row=models[(fit_g,h)];assert pd.Timestamp(row.cutoff)<=q.forecast_at.iloc[0]
                if mapping is not None:
                    m=mapping[mapping.origin_round.eq(g)&mapping.horizon.eq(h)].iloc[0];assert m.model_refit_round==fit_g and m.file==row.file and m.sha256==row.sha256
                x=np.column_stack([np.where(np.isfinite(qr),qr,median),(~np.isfinite(qr)).astype(float)]);pred=model['models'][0].predict(x);actual=np.column_stack([pred[:,:3].sum(1),np.maximum(0,pred[:,3]*90),pred[:,:3]])
                names=[f'component_p{h}',f'component_m{h}',f'base_attack{h}',f'base_appearance{h}',f'base_residual{h}'];np.testing.assert_allclose(actual,saved.reindex(pd.MultiIndex.from_frame(q[t.KEY]))[names],atol=1e-9,rtol=1e-10);origins+=1
        print('BASE CADENCE VERIFIED',arm,s,flush=True)
    assert count==({'every1':302,'every2':150}[arm]) and origins==302 and replays==1
    atomic_json(P/f'base_verification_{arm}.json',dict(passed=True,packages=count,origin_horizon_predictions_replayed=origins,independent_fresh_uniform_fit_replays=replays,all_original_quarterly_models_identical=True,all_medians_train_only=True,strict_labels_before_deadline=True,no_future_model_selection=True,only_base_cadence_changed=True))

if __name__=='__main__':
    if sys.argv[1]=='base':bases(sys.argv[2])
    elif sys.argv[1]=='heads':v.heads(sys.argv[2])
    elif sys.argv[1]=='metrics':v.metrics()
    else:raise ValueError(sys.argv[1])
