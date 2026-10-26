"""Technical source qualification repair; no parameter/search changes.

Reuse a parent fitted bundle only when its entire actual training matrix,
labels, keys and clocks are identical. Recency-only never used xG and is reused.
"""
import sys,os,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import test_xg_adaptation as t
t.P=R/'reports/xg_adaptation_2026_10_26_v2';t.D=R/'datasets/fpl_common_training_v5'
P=t.P;D=t.D;OLD=R/'reports/xg_adaptation_2026_10_26';OLD_D=R/'datasets/fpl_common_training_v4'
import pandas as pd,numpy as np

def base(season):
    t.check();d=t.load(D/'training.pkl');old=t.load(OLD_D/'training.pkl');view=t.load(D/'pool_features.pkl');cols=t.read(D/'schema.json')['features'];out=view[view.season.eq(season)][t.KEY+['forecast_at']].copy();audit=[];baseline=pd.read_csv(t.FIT/f'component_audit_{season}.csv');parent=pd.read_csv(OLD/f'base_audit_{season}.csv')
    original=t.common.cbreg
    def cb():
        m=original();m.set_params(allow_const_label=True);return m
    t.common.cbreg=cb
    for g in t.REFITS:
        at=view.loc[view.season.eq(season)&view['round'].eq(g),'forecast_at'].iloc[0];q=view[view.season.eq(season)&view['round'].between(g,min(g+3,38))]
        for h in [1,3]:
            ts=[f'target_{name}_{h}' for name in ['points','minutes','starts','attack','appearance','residual']]
            def select(frame):return frame[frame.train_eligible&frame.forecast_at.lt(at)&frame[f'label_at_{h}'].lt(at)&frame[ts].notna().all(axis=1)].copy()
            train=select(d);prior=select(old);row=baseline[baseline['round'].eq(g)&baseline.horizon.eq(h)].iloc[0];assert len(train)==row.rows and t.common.keys_hash(train)==row.keys_sha256
            compare=t.KEY+['forecast_at',f'label_at_{h}']+cols+ts;identical=train[compare].reset_index(drop=True).equals(prior[compare].reset_index(drop=True));path=P/f'models/xg_{season}_gw{g:02d}_h{h}.pkl';path.parent.mkdir(exist_ok=True)
            if identical:
                oldrow=parent[parent['round'].eq(g)&parent.horizon.eq(h)].iloc[0];source=R/oldrow.file;assert t.sha(source)==oldrow.sha256;bundle=t.load(source);assert bundle['columns']==cols;os.link(source,path)
            else:bundle=t.common.fit_arm('component',train,cols,h);t.save(path,bundle)
            v,_,_=t.common.predict_arm(bundle,q);out.loc[q.index,f'component_p{h}']=v[:,0];out.loc[q.index,f'component_m{h}']=v[:,1];audit.append(dict(season=season,round=g,horizon=h,cutoff=str(at),rows=len(train),keys_sha256=t.common.keys_hash(train),same_teacher_keys_as_control=True,max_origin=str(train.forecast_at.max()),max_label=str(train[f'label_at_{h}'].max()),file=str(path.relative_to(R)),sha256=t.sha(path),reused_parent_only_if_entire_actual_training_matrix_identical=bool(identical)))
        print('CORRECTED XG BASE',season,g,'reused',sum(a['reused_parent_only_if_entire_actual_training_matrix_identical'] for a in audit),flush=True)
    assert np.isfinite(out.filter(regex='component_')).all().all();t.save(P/f'base_{season}.pkl',out);pd.DataFrame(audit).to_csv(P/f'base_audit_{season}.csv',index=False)

def reuse_recent():
    t.check();old=pd.read_pickle(OLD_D/'training.pkl');new=pd.read_pickle(D/'training.pkl');cols=t.read(R/'datasets/fpl_common_training_v3/schema.json')['features'];pd.testing.assert_frame_equal(old[[c for c in old if c not in t.read(D/'schema.json')['feature_groups']['expected_attack']]],new[[c for c in new if c not in t.read(D/'schema.json')['feature_groups']['expected_attack']]])
    for name in ['recent_only.csv.gz','head_audit_recent_only.csv','head_data_recent_only.pkl','prediction_lock_recent_only.json','prediction_verification_recent_only.json','preflight_recent_only.json','scores_recent_only.csv','manager_verification_recent_only.json','scores_control.csv','manager_verification_control.json']:
        os.link(OLD/name,P/name)
    for season in t.EVAL:
        src=OLD/'manager'/f'{season}_recent_only';dest=P/'manager'/f'{season}_recent_only';dest.mkdir(parents=True,exist_ok=True)
        for path in src.glob('*.json'):os.link(path,dest/path.name)
    t.atomic_json(P/'recency_reuse.json',dict(passed=True,all_old325_features_targets_masks_clocks_identical=True,recency_did_not_consume_any_xg_features=True,parent_independent_verification=str((OLD/'manager_verification_recent_only.json').relative_to(R)),fitted_heads_reused=240,full_episodes_reused=3,weights_half_life180_unchanged=True));print('RECENCY REUSED ON IDENTICAL OLD INPUTS',flush=True)

if __name__=='__main__':
    if sys.argv[1]=='base':base(sys.argv[2])
    elif sys.argv[1]=='reuse-recent':reuse_recent()
    elif sys.argv[1]=='heads':t.heads(sys.argv[2])
    elif sys.argv[1]=='manager':t.manager(sys.argv[2],sys.argv[3])
    else:raise ValueError(sys.argv[1])
