"""Technical v3: permit constant output columns in multi-target regression.

No scores were read in v1. Same data, origins and model parameters. Complete
v1 models from the first fold are reused byte-for-byte; incomplete heads are
not reused. Each worker has one thread and owns one separate output folder.
"""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,json,time,pickle,shutil,subprocess,concurrent.futures
from pathlib import Path
import numpy as np
import pandas as pd
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import common_model_retest as core
from model_lab.common import sha,atomic_json,verify_files,runtime
OLD=core.P
core.P=R/'reports/common_model_retest_2026_10_25_v3';core.ID='common-model-retest-20261025-v3'
P=core.P;D=core.D
original_fit=core.fit_arm
original_cbreg=core.cbreg
def constant_safe_cbreg():
    model=original_cbreg();model.set_params(allow_const_label=True);return model
core.cbreg=constant_safe_cbreg

def fit(name,tr,cols,h):
    if name not in ['two_part','role_conditional']:return original_fit(name,tr,cols,h)
    from sklearn.impute import SimpleImputer
    imp=SimpleImputer(strategy='median',keep_empty_features=True)
    a=tr[cols].to_numpy(float);x=np.column_stack([imp.fit_transform(a),(~np.isfinite(a)).astype(float)])
    y=tr[[f'target_points_{h}',f'target_minutes_{h}']].to_numpy(float);y[:,1]/=90
    labels=tr[f'target_minutes_{h}'].gt(0).astype(int).to_numpy() if name=='two_part' else np.where(tr[f'target_starts_{h}'].gt(0),2,np.where(tr[f'target_minutes_{h}'].gt(0),1,0))
    clf=core.cbclass();clf.fit(x,labels)
    bundle=dict(name=name,columns=cols,imputer=imp,models=[],horizon=h,classifier=clf,classes=clf.classes_.tolist(),heads={})
    for label in clf.classes_:
        mask=labels==label;values=y[mask]
        if mask.sum()<100 or np.all(values==values[0]):bundle['heads'][int(label)]=values.mean(0)
        else:
            model=core.cbreg();model.fit(x[mask],values);bundle['heads'][int(label)]=model
    return bundle

def worker(s,h,gw):
    spec=core.read(P/'proposal.json');verify_files(R,spec['input_hashes']);schema=core.read(D/'schema.json');d=pd.read_pickle(D/'training.pkl');tick=time.monotonic()
    q=d[d.season.eq(s)&d['round'].between(gw,min(gw+7,38))&~d.excluded_origin].copy();at=d[d.season.eq(s)&d['round'].eq(gw)].forecast_at.iloc[0]
    targets=[f'target_{t}_{h}' for t in ['points','minutes','starts','attack','appearance','residual']]
    tr=d[d.train_eligible&d.forecast_at.lt(at)&d[f'label_at_{h}'].lt(at)&d[targets].notna().all(axis=1)].copy()
    common=dict(season=s,horizon=h,refit_round=gw,cutoff=str(at),training_rows=len(tr),training_keys_sha256=core.keys_hash(tr),max_origin=str(tr.forecast_at.max()),max_label=str(tr[f'label_at_{h}'].max()),prediction_keys_sha256=core.keys_hash(q))
    folder=P/'folds'/f'{s}_h{h}_gw{gw:02d}';folder.mkdir(parents=True,exist_ok=True);assert not (folder/'lock.json').exists()
    cache={};audits=[];fits=0
    for name in core.ARMS:
        cols=core.features_for(name,schema);old=OLD/'folds'/folder.name
        reused=False
        if s=='2022-23' and h==1 and gw==1 and (old/(name+'.pkl')).exists() and (old/(name+'.csv.gz')).exists():
            with (old/(name+'.pkl')).open('rb') as f:bundle=pickle.load(f)
            assert bundle['columns']==cols
            pred,prob,distribution=core.predict_arm(bundle,q);saved=pd.read_csv(old/(name+'.csv.gz'))
            assert saved.row_id.tolist()==q.row_id.tolist();np.testing.assert_allclose(saved[['predicted_points','predicted_minutes']],pred,atol=1e-9,rtol=1e-9)
            reused=True
        elif name=='ridge_extra_50':bundle=None;pred=(cache['ridge']+cache['extra_trees'])/2;prob=None;distribution=None
        else:bundle=fit(name,tr,cols,h);pred,prob,distribution=core.predict_arm(bundle,q)
        if bundle is not None:fits+=len(bundle['models'])+(1+sum(hasattr(v,'predict') for v in bundle['heads'].values()) if 'classifier' in bundle else 0)
        cache[name]=pred
        out=q[core.KEY+['row_id','forecast_at','eval_eligible','target_quality_flagged',f'target_points_{h}',f'target_minutes_{h}']].copy();out['predicted_points']=pred[:,0];out['predicted_minutes']=pred[:,1];out['p_play_constant']=float(tr[f'target_minutes_{h}'].gt(0).mean())
        if prob is not None:out['p_play']=prob
        if distribution is not None:
            for j in range(5):out[f'p_bin_{j}']=distribution[:,j]
        out.to_csv(folder/(name+'.csv.gz'),index=False)
        if bundle is not None:
            if reused:shutil.copy2(old/(name+'.pkl'),folder/(name+'.pkl'))
            else:
                with (folder/(name+'.pkl')).open('wb') as f:pickle.dump(bundle,f,protocol=5)
        audits.append(dict(common,arm=name,features=len(cols),predictions_sha256=sha(folder/(name+'.csv.gz')),model_sha256=sha(folder/(name+'.pkl')) if bundle is not None else None,reused_from_v1=reused))
        print('FIT',s,'H'+str(h),'GW'+str(gw),name,'n',len(tr),'seconds',round(time.monotonic()-tick),'reused' if reused else '',flush=True)
    pd.DataFrame(audits).to_csv(folder/'fit_audit.csv',index=False)
    atomic_json(folder/'lock.json',dict(common,fits=fits,predictions={n+'.csv.gz':sha(folder/(n+'.csv.gz')) for n in core.ARMS}))
    return str(folder)

def train():
    spec=core.read(P/'proposal.json');verify_files(R,spec['input_hashes']);assert not (P/'started.json').exists()
    atomic_json(P/'started.json',dict(started_at=str(pd.Timestamp.now(tz='UTC')),runtime=runtime(),proposal_sha256=sha(P/'proposal.json'),parallel_workers=4,continuation_of=core.read(OLD/'proposal.json')['id']))
    jobs=[(s,h,gw) for s in core.SEASONS for h in [1,3] for gw in core.REFITS];tick=time.monotonic()
    def launch(job):
        s,h,gw=job;log=P/'logs'/f'{s}_h{h}_gw{gw:02d}.log';log.parent.mkdir(exist_ok=True)
        with log.open('x') as f:
            subprocess.run([sys.executable,str(Path(__file__).resolve()),'worker',s,str(h),str(gw)],stdout=f,stderr=subprocess.STDOUT,check=True,cwd=R,env=os.environ.copy())
        return job
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        futures={pool.submit(launch,job):job for job in jobs}
        for i,future in enumerate(concurrent.futures.as_completed(futures),1):
            job=future.result();print('FOLD',i,'/',len(jobs),*job,'seconds',round(time.monotonic()-tick),flush=True)
    folders=[P/'folds'/f'{s}_h{h}_gw{gw:02d}' for s,h,gw in jobs];audit=pd.concat([pd.read_csv(p/'fit_audit.csv') for p in folders],ignore_index=True);audit.to_csv(P/'fit_audit.csv',index=False)
    fits=sum(core.read(p/'lock.json')['fits'] for p in folders);assert fits<=spec['resources']['maximum_fits'];verify_files(R,spec['input_hashes'])
    atomic_json(P/'prediction_lock.json',dict(fits=fits,folds=40,arms=core.ARMS,audit_sha256=sha(P/'fit_audit.csv'),saved_before_scoring=True,seconds=time.monotonic()-tick,parallel_workers=4,reused_complete_v1_models=int(audit.reused_from_v1.sum()),extra_failed_v1_attempts_not_counted_as_completed_fits=2,discarded_v2_saved_model_files=len(list((R/'reports/common_model_retest_2026_10_25_v2/folds').glob('*/*.pkl')))));print('SEALED',fits,flush=True)

if __name__=='__main__':
    command=sys.argv[1]
    if command=='worker':worker(sys.argv[2],int(sys.argv[3]),int(sys.argv[4]))
    elif command=='train':train()
    elif command=='prepare':core.prepare()
    elif command=='score':core.score()
    elif command=='verify':
        from scripts import verify_common_model_retest as verification
        verification.models()
    elif command=='anchor':
        from scripts import common_operational_anchor as anchor
        anchor.main()
    elif command=='report':
        from scripts import report_common_model_retest as report
        report.main()
