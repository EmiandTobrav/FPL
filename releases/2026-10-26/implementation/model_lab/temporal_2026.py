"""Season adapter for the immutable forecast-package-20261016-v1 recipe."""
from pathlib import Path
import copy,sys,time,hashlib,inspect
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from model_lab import point_context as pc
from model_lab.common import read,sha,atomic_json,verify_files
R=pc.R;P=R/'reports/temporal_2026_27_2026_10_16';F=R/'reports/forecast_freeze_2026_10_16';KEY=pc.KEY

def points(a,mod,data,test,at):
 tr=pc.prev.training(data,at);played=tr.native_minutes.gt(0).to_numpy();y=tr.target_total_points.to_numpy(float);absent=float(y[~played].mean());out={}
 for arm in ['base','full']:
  names=a.schema['extended_features']+pc.BASE+([] if arm=='base' else pc.CF+pc.ST);sc=copy.deepcopy(a.schema);sc['extended_features']=names
  pipe=a._pipeline.make_pipeline(sc,'catboost','extended',seed=mod.SEED,model_params={'thread_count':1});prep,reg=pipe.named_steps['prepare'],pipe.named_steps['model'];z=prep.fit_transform(tr[names])
  with threadpool_limits(limits=1):reg.fit(z.loc[played],y[played],sample_weight=np.ones(int(played.sum())));v=reg.predict(prep.transform(test[names]))
  out[arm+'_points']=(1-test.candidate_p0.to_numpy())*v+test.candidate_p0.to_numpy()*absent
 audit=dict(training_keys_sha256=pc.prev.keyhash(tr),training_rows=len(tr),played_rows=int(played.sum()),latest_training_origin=str(tr.forecast_at.max()),latest_point_label=str(tr.target_h1_available_at.max()),latest_minute_label=str(tr.available_after_proxy.max()),fit_cutoff=str(at))
 return out,audit

def history():
 d=pc.prev.labeled_inputs();c=pd.read_csv(pc.P/'context.csv.gz');return d.merge(c[c.arm.eq('full')][KEY+pc.CF+pc.ST],on=KEY,how='left',validate='one_to_one')

def parity():
 lock=read(F/'package_lock.json');verify_files(R,lock['input_hashes']);verify_files(F,lock['bundle_hashes']);assert sha(F/'package_lock.json')=='95a860bbf62d21769d6225c11913b1dc6d493c4c267915d8cf4c0b71253eec7a'
 atomic_json(P/'protocol.json',dict(package_id=lock['id'],package_sha256=sha(F/'package_lock.json'),evaluation_plan_sha256=sha(F/'evaluation_plan.json'),arms=['base','full'],gates=lock['gates'],retrospective_rounds=list(range(1,7)),prospective_first_round=7,no_tuning=True,recipe_unchanged=True,parity_rounds=list(range(1,39)),new_season_scores_read=False,created_at=pd.Timestamp.now(tz='UTC').isoformat()))
 mod=pc.prev.adapter();a=mod.CausalCandidateForecaster(R,thread_count=1);d=history();old=pd.read_csv(pc.P/'predictions.csv.gz').set_index(KEY);audits=[]
 for gw in range(1,39):
  t=d[d.season.eq('2025-26')&d['round'].eq(gw)];at=t.forecast_at.iloc[0];out,au=points(a,mod,d,t,at);ix=pd.MultiIndex.from_frame(t[KEY]);diff={k:float(np.max(np.abs(v-old.loc[ix,k].to_numpy()))) for k,v in out.items()}
  for k,v in out.items():assert np.allclose(v,old.loc[ix,k],atol=1e-12,rtol=1e-12),(gw,k,diff)
  au.update(round=gw,max_abs=diff);audits.append(au);atomic_json(P/f'parity_gw{gw:02d}.json',au);print('PARITY',gw,diff,flush=True)
 atomic_json(P/'parity.json',dict(passed=True,origins=38,point_fits=76,adapter_sha256=sha(Path(__file__)),audits=audits))
if __name__=='__main__':globals()[sys.argv[1]]()
