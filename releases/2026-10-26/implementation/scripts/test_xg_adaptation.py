"""Two independent changes to the active component: xG only or recency only."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,pickle,copy,hashlib
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import common_model_retest as common
from scripts import common_season_comparison as projection
from scripts import matched_availability_retest_v8 as guard
from model_lab.common import sha,atomic_json,verify_files
P=R/'reports/xg_adaptation_2026_10_26';D=R/'datasets/fpl_common_training_v4';F=R/'reports/matched_season_retest_2026_10_26_v8';FIT=R/'reports/matched_season_retest_2026_10_25_v5'
S=['2022-23','2023-24','2024-25','2025-26'];EVAL=S[1:];REFITS=list(range(1,39,4));KEY=['season','round','code'];ARMS=['xg_only','recent_only'];HALF_LIFE=180.
def read(p):return json.loads(Path(p).read_text())
def load(p):
    with Path(p).open('rb') as f:return pickle.load(f)
def save(p,obj):
    Path(p).parent.mkdir(parents=True,exist_ok=True)
    with Path(p).open('xb') as f:pickle.dump(obj,f,protocol=5)
def check():
    verify_files(R,read(P/'proposal.json')['input_hashes']);verify_files(D,read(D/'manifest.json')['files'])

def base(season):
    check();d=load(D/'training.pkl');view=load(D/'pool_features.pkl');cols=read(D/'schema.json')['features'];out=view[view.season.eq(season)][KEY+['forecast_at']].copy();audit=[]
    original=common.cbreg
    def cb():
        m=original();m.set_params(allow_const_label=True);return m
    common.cbreg=cb
    baseline_audit=pd.read_csv(FIT/f'component_audit_{season}.csv')
    for g in REFITS:
        at=view.loc[view.season.eq(season)&view['round'].eq(g),'forecast_at'].iloc[0];q=view[view.season.eq(season)&view['round'].between(g,min(38,g+3))]
        for h in [1,3]:
            ts=[f'target_{t}_{h}' for t in ['points','minutes','starts','attack','appearance','residual']];tr=d[d.train_eligible&d.forecast_at.lt(at)&d[f'label_at_{h}'].lt(at)&d[ts].notna().all(axis=1)].copy();a=baseline_audit[baseline_audit['round'].eq(g)&baseline_audit.horizon.eq(h)].iloc[0];assert len(tr)==a.rows and common.keys_hash(tr)==a.keys_sha256
            bundle=common.fit_arm('component',tr,cols,h);path=P/f'models/xg_{season}_gw{g:02d}_h{h}.pkl';save(path,bundle);v,_,_=common.predict_arm(bundle,q);out.loc[q.index,f'component_p{h}']=v[:,0];out.loc[q.index,f'component_m{h}']=v[:,1]
            audit.append(dict(season=season,round=g,horizon=h,cutoff=str(at),rows=len(tr),keys_sha256=common.keys_hash(tr),same_teacher_keys_as_control=True,max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'label_at_{h}'].max()),file=str(path.relative_to(R)),sha256=sha(path)))
        print('XG BASE',season,g,flush=True)
    assert np.isfinite(out.filter(regex='component_')).all().all();save(P/f'base_{season}.pkl',out);pd.DataFrame(audit).to_csv(P/f'base_audit_{season}.csv',index=False)

def fit_recent(tr,j,at):
    raw,anchor,names=projection.design(tr,'component',j);x,transform=projection.transform(raw)
    age=(at-tr.forecast_at).dt.total_seconds().to_numpy()/86400;assert np.all(age>0);w=np.exp2(-age/HALF_LIFE);pen=np.eye(x.shape[1])*.01;pen[0,0]=0.;y=(tr[f'y_{j}'].to_numpy(float)-anchor)/6
    beta=np.linalg.solve(x.T@(w[:,None]*x)/w.sum()+pen,x.T@(w*y)/w.sum())
    return dict(beta=beta.tolist(),transform=transform,raw_names=names,offset=j,penalty=.01,rows=len(tr),base_model='component',half_life_days=HALF_LIFE,transform_policy='exact same unweighted training-only transform as control; only residual objective sample weights change',effective_rows=float(w.sum()**2/(w@w))),w

def heads(arm):
    check();assert arm in ARMS;d=load(F/'head_data.pkl')
    if arm=='xg_only':
        comp=pd.concat([load(P/f'base_{s}.pkl') for s in S],ignore_index=True);d=d.drop(columns=['component_p1','component_m1','component_p3','component_m3']).merge(comp,on=KEY+['forecast_at'],validate='one_to_one')
    complete=d[[f'y_{j}' for j in range(3)]].notna().all(axis=1);h3=d[[f'y_at_{j}' for j in range(3)]].max(axis=1);out=[];audits=[];teacher_audit=pd.read_csv(F/'head_audit.csv')
    for s in EVAL:
        for g in range(1,39):
            q=d[d.season.eq(s)&d['round'].eq(g)];at=q.forecast_at.iloc[0]
            if g in REFITS:
                models={}
                for j in range(8):
                    tr=d[d.teacher_eligible&d.forecast_at.lt(at)&d[f'y_{j}'].notna()&d[f'y_at_{j}'].lt(at)&complete&h3.lt(at)].copy();control=teacher_audit[teacher_audit.season.eq(s)&teacher_audit['round'].eq(g)&teacher_audit.offset.eq(j)].iloc[0];assert len(tr)==control.rows and common.keys_hash(tr)==control.keys_sha256
                    if arm=='xg_only':model=projection.fit_projection(tr,'component',j);w=np.ones(len(tr))
                    else:model,w=fit_recent(tr,j,at)
                    model['current_season_weight']=float(w[tr.season.eq(s).to_numpy()].sum()/w.sum());models[j]=model;name=P/f'heads/{arm}_{s}_gw{g:02d}_j{j}.json';atomic_json(name,model)
                    audits.append(dict(arm=arm,season=s,round=g,offset=j,cutoff=str(at),rows=len(tr),keys_sha256=common.keys_hash(tr),same_keys_as_control=True,current_rows=int(tr.season.eq(s).sum()),current_weight=model['current_season_weight'],effective_rows=float(w.sum()**2/(w@w)),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'y_at_{j}'].max()),max_h3_label=str(h3.loc[tr.index].max()),file=str(name.relative_to(R)),sha256=sha(name)))
                print('HEADS',arm,s,g,flush=True)
            z=q[KEY+['forecast_at','can_buy']].copy()
            for j in range(8):z[f'xp_{j}']=projection.predict_projection(q,'component',models[j]) if g+j<=38 else 0.
            out.append(z)
    f=pd.concat(out,ignore_index=True);a=pd.read_csv(F/'availability.csv.gz');f=f.merge(a[KEY+['model_can_buy','known_departed','confirmed_out_current']],on=KEY,validate='one_to_one');f.can_buy=f.model_can_buy
    for j in range(8):f.loc[f.known_departed|(f.confirmed_out_current if j==0 else False),f'xp_{j}']=0.
    f.drop(columns=['model_can_buy','known_departed','confirmed_out_current']).to_csv(P/f'{arm}.csv.gz',index=False);pd.DataFrame(audits).to_csv(P/f'head_audit_{arm}.csv',index=False);save(P/f'head_data_{arm}.pkl',d);atomic_json(P/f'prediction_lock_{arm}.json',dict(files={f'{arm}.csv.gz':sha(P/f'{arm}.csv.gz'),f'head_audit_{arm}.csv':sha(P/f'head_audit_{arm}.csv'),f'head_data_{arm}.pkl':sha(P/f'head_data_{arm}.pkl')},sealed_before_manager=True));print('PREDICTIONS SEALED',arm,flush=True)

def manager(s,arm):
    check();verify_files(P,read(P/f'prediction_lock_{arm}.json')['files']);assert read(P/f'preflight_{arm}.json')['passed'];guard.configure();m=guard.m;origins=load(F/'origins.pkl');env=m.MatchedEnvironment();f=pd.read_csv(P/f'{arm}.csv.gz');f=f[f.season.eq(s)].set_index(['round','code']);folder=P/'manager'/f'{s}_{arm}';folder.mkdir(parents=True,exist_ok=False);_,a=guard.solver();state=a.engine.initial_state();net=hits=0
    for g in range(1,39):
        at=origins[(s,g)];pool=m.method.qualify(guard.eligible_pool(s,g),s,at);q=f.loc[g].reindex(pool.code);assert pd.to_datetime(q.forecast_at,utc=True).eq(at).all() and q.can_buy.tolist()==pool.can_buy.tolist();xp=q[[f'xp_{j}' for j in range(min(8,39-g))]].to_numpy(float);mod,a=guard.solver();choice=copy.deepcopy(a.decide(pool,xp,state,g)['choice']);choice['prices']={int(k):v for k,v in choice['prices'].items()};after,choice=a.engine.apply_decision(state,choice,pool.to_dict('records'),g);atomic_json(folder/f'gw{g:02d}.decision.json',mod.clean(dict(state_before=state,state_after=after,choice=choice,forecast_at=str(at),outcomes_read=False,solver_calls=a.ledger,forecast_input_sha256=hashlib.sha256(xp.tobytes()).hexdigest())))
        outcomes,result,n=m.settle(a,env,s,g,dict(choice=choice),pool);atomic_json(folder/f'gw{g:02d}.settlement.json',mod.clean(dict(net=n,hits=4*choice['paid'],outcomes=outcomes,settlement=result)));net+=n;hits+=4*choice['paid'];state=after
        if g%8==0:print('MANAGER',s,arm,g,flush=True)
    atomic_json(folder/'summary.json',dict(season=s,arm=arm,net=net,hits=hits,rounds=38,complete=True));print('COMPLETE',s,arm,net,flush=True)

if __name__=='__main__':
    action=sys.argv[1]
    if action=='base':base(sys.argv[2])
    elif action=='heads':heads(sys.argv[2])
    elif action=='manager':manager(sys.argv[2],sys.argv[3])
    else:raise ValueError(action)
