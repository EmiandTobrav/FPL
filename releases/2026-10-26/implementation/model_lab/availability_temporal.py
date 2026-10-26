"""One locked temporal replication; frozen 2024/25 minute heads, causal category refresh."""
from pathlib import Path
import sys,hashlib,time,inspect
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from model_lab.common import read,sha,atomic_json,verify_files,runtime
from model_lab.forecast import causal_training
from model_lab.probabilistic import PARAMS,Head,minute_class,check
from model_lab.probability_experiment import features
from model_lab.probability_refresh import load_data,REFRESH
from model_lab.minute_calendar import Calendar
from model_lab import availability_probabilities as prior
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/availability_temporal_2026_10_16';CAL=ROOT/'reports/minute_calendar_2026_10_16';CACHE=ROOT/'reports/fpl_simulator_2026_10_13/cache_manager';KEY=prior.KEY;EXTRA=prior.EXTRA;CE=['planned_fixture_count','calendar_known'];ID='availability-temporal-20261016-v1'
# Exact predecessor encoding; isolated globals avoid modifying the historical module.
_ns=dict(prior.__dict__);_ns['AV']=OUT
exec(inspect.getsource(prior.attach_availability),_ns)
attach=_ns['attach_availability']
def context():
 a=pd.read_csv(OUT/'availability_proxy.csv.gz',keep_default_na=False);old=pd.read_csv(prior.AV/'availability_proxy.csv.gz',keep_default_na=False);pd.concat([old,a],ignore_index=True).to_csv(OUT/'availability_combined.csv.gz',index=False)
 # The predecessor encoder expects this filename: retain new-only evidence separately.
 (OUT/'availability_new_period.csv.gz').write_bytes((OUT/'availability_proxy.csv.gz').read_bytes());(OUT/'availability_proxy.csv.gz').write_bytes((OUT/'availability_combined.csv.gz').read_bytes())
 audit=pd.read_csv(OUT/'snapshot_audit.csv');bad=audit.loc[~audit.proxy_eligible,'gw'].astype(int).tolist();cal=Calendar();p=cal.b.current/'project/data/2025-26_teams.csv.gz';t=pd.read_csv(p);cal.b.team_codes['2025-26']=t.set_index('id').code;cal.names['2025-26']=t.set_index('name').code.to_dict();cal.dependencies[str(p.relative_to(ROOT))]=sha(p);frames=[];deps={}
 for o in read(OUT/'origin_lock.json')['origins']:
  gw=o['gw'];folder=CACHE/'2025-26'/f'gw{gw:02d}';man=read(folder/'manifest.json');assert sha(folder/'manifest.json')==o['manifest_sha256']
  for n in ['pool.csv.gz','features.csv.gz']:
   assert sha(folder/n)==man['files'][n];deps[str((folder/n).relative_to(ROOT))]=sha(folder/n)
  deps.update(man['implementation']);deps[str((folder/'manifest.json').relative_to(ROOT))]=sha(folder/'manifest.json')
  pool=pd.read_csv(folder/'pool.csv.gz');assert (pd.to_datetime(pool.club_available_at,utc=True)<pd.Timestamp(o['origin'])).all();f=pool[['code','club','forecast_at']].copy();f['season']='2025-26';f['round']=gw;frames.append(cal.attach(f,'club','new_period'))
 pd.concat(frames,ignore_index=True).to_csv(OUT/'evaluation_calendar.csv.gz',index=False);deps.update(cal.dependencies);verify_files(ROOT,deps)
 atomic_json(OUT/'context.json',dict(excluded_rounds=bad,calendar_audit=cal.audit,dependencies=deps,strict_receipt_available=False));print('CONTEXT exclusions',bad,flush=True)
def prepare():
 old=read(prior.OUT/'proposal.json');files=dict(old['input_hashes']);files.update(read(OUT/'context.json')['dependencies'])
 paths=[Path(__file__),OUT/'origin_lock.json',OUT/'context.json',OUT/'evaluation_calendar.csv.gz',OUT/'availability_proxy.csv.gz',CAL/'training_calendar.csv.gz',CAL/'evaluation_calendar.csv.gz',CAL/'2024-25_fit37.json',CAL/'2024-25_predictions.csv.gz']+list(OUT.glob('*.py'))+list(OUT.glob('*snapshots.json'))+list(OUT.glob('*retrieval.json'))+[OUT/'snapshot_audit.csv',OUT/'build_summary.json']+list((OUT/'raw').glob('2025-26_*.xz'))
 for p in paths:files[str(p.relative_to(ROOT))]=sha(p)
 spec={**old,'id':ID,'candidate_id':'availability_full_package_temporal_2025_26_v1','hypothesis':'The unchanged full availability package improves expected minutes and both Brier scores in the later 2025/26 period.','change':'New temporal replication only; reconstruct and verify 2024/25 GW37 calendar mean heads, then freeze them for entire season. Both probability arms use unchanged four-round causal refresh.','related_work':['availability-probabilities-20261016-v1','availability-ablation-20261016-v1','minute-calendar-20261016-v1'],'input_hashes':files,'seasons':['2025-26'],'resources':{'maximum_head_fits':22,'reconstructed_frozen_mean_heads':2,'probability_head_fits':20,'threads':1,'refresh':REFRESH,'no_search':True},'success_criterion':'2025/26 MSE strictly lower AND Brier(play) and Brier(any fixture>=60) each no worse, on identical eligible origins/players. No tolerance/tradeoff; prior six gates remain unchanged.','evaluation_contract':{'primary_control':'Original history-only category classifier with identical fixed minute means.','training':'Same causal keys/order for both arms. Remove 2024/25 GW15 and disqualified new origins from both classifier training. Historical means reproduced without modifying prior history.','origins':read(OUT/'context.json')['excluded_rounds'],'novelty':'New for availability package, previously used elsewhere; not untouched holdout.','data':'Git max author/committer proxy strictly before origin, <=24h; actual deadline equals origin, target chance binding, no future news. Missing per-player evidence remains unknown.','minute_means':'2024/25 GW37 heads frozen, exact original key hash and prediction parity required.','uncertainty':'2000 paired moving four-calendar-round block draws seed20261015, descriptive only.','cohorts':'all primary; position, seen_this_season, availability present, calendar strata secondary.','scoring':'can_buy and known minutes, points, all fixture minutes; same mask for both arms'},'stop_rule':'Stop on hashes, causality, key, parity, support mismatch; no outcome-guided retry or tuning.','maximum_runs':1}
 atomic_json(OUT/'proposal.json',spec);print('PREPARED',len(files),flush=True)
def eligible(rows,at):
 tr,_=causal_training(rows,at,1);tr=tr[tr.native_minutes.notna()&tr.minute_known.eq(True)&tr.available_after_proxy.lt(at)];assert max(tr.forecast_at.max(),tr.target_h1_available_at.max(),tr.available_after_proxy.max())<at;return tr

def run():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'started.json',dict(runtime=runtime(),proposal_sha256=sha(OUT/'proposal.json'),started_at=str(pd.Timestamp.now(tz='UTC'))));rows,cols,_=load_data();rows=rows[rows.season.le('2025-26')];oldfolder=prior.CACHE/'2024-25/gw37';at=pd.Timestamp(read(oldfolder/'manifest.json')['forecast_at']);tr=eligible(rows[rows.season.le('2024-25')],at);old=read(CAL/'2024-25_fit37.json');keyhash=hashlib.sha256(tr[KEY].to_csv(index=False).encode()).hexdigest();assert keyhash==old['training_keys_sha256'] and len(tr)==old['training_rows'];tr=tr.merge(pd.read_csv(CAL/'training_calendar.csv.gz'),on=KEY,how='left',sort=False,validate='one_to_one');xx=features(tr,cols)
 for n in CE:xx[n]=tr[n].to_numpy(float)
 y=minute_class(tr.native_minutes,tr.any60);means=[]
 with threadpool_limits(limits=1):
  for k in [1,2]:
   used=xx.columns[xx[y==k].notna().any()].tolist();means.append((used,HistGradientBoostingRegressor(**PARAMS).fit(xx.loc[y==k,used],tr.native_minutes.to_numpy()[y==k])))
 def predict_means(f,c):
  x=features(f,cols)
  for n in CE:x[n]=c[n].to_numpy(float)
  with threadpool_limits(limits=1):return [np.maximum(0,m.predict(x[u])) for u,m in means]
 f=pd.read_csv(oldfolder/'features.csv.gz');c=pd.read_csv(CAL/'evaluation_calendar.csv.gz');c=c[c.season.eq('2024-25')&c['round'].eq(37)].set_index('code').loc[f.code];arch=pd.read_csv(CAL/'2024-25_predictions.csv.gz');arch=arch[arch['round'].eq(37)].set_index('code').loc[f.code];diff=0.
 for pred,n in zip(predict_means(f,c),['candidate_short_mean','candidate_long_mean']):
  diff=max(diff,float(np.max(np.abs(pred-arch[n]))));assert np.allclose(pred,arch[n],atol=1e-10,rtol=1e-10)
 atomic_json(OUT/'frozen_mean_verification.json',dict(training_keys_sha256=keyhash,training_rows=len(tr),fit_cutoff=str(at),parity_max_abs=diff,reconstruction_fits=2,new_period_mean_fits=0));print('FROZEN MEANS VERIFIED',diff,flush=True)
 rows=attach(rows);bad=read(OUT/'context.json')['excluded_rounds'];rows=rows[~((rows.season.eq('2024-25')&rows['round'].eq(15))|(rows.season.eq('2025-26')&rows['round'].isin(bad)))];ec=pd.read_csv(OUT/'evaluation_calendar.csv.gz');frames=[];audits=[];fits=0
 for gw in range(1,39):
  folder=CACHE/'2025-26'/f'gw{gw:02d}';at=pd.Timestamp(read(folder/'manifest.json')['forecast_at'])
  if gw in REFRESH:
   tr=eligible(rows,at);x=features(tr,cols);xc=x.copy()
   for n in EXTRA:xc[n]=tr[n].to_numpy(float)
   y=minute_class(tr.native_minutes,tr.any60);start=time.monotonic()
   with threadpool_limits(limits=1):models={'control':Head(3).fit(x,y),'candidate':Head(3).fit(xc,y)}
   fits+=2;assert fits<=20;cutoff=at;rec=dict(round=gw,fit_cutoff=str(at),training_rows=len(tr),training_keys_sha256=hashlib.sha256(tr[KEY].to_csv(index=False).encode()).hexdigest(),latest_label_at=str(tr.available_after_proxy.max()),latest_target_at=str(tr.target_h1_available_at.max()),availability_rows=int(tr.av_snapshot_present.sum()),seconds=time.monotonic()-start);audits.append(rec);atomic_json(OUT/f'fit{gw:02d}.json',rec);print('FIT',gw,round(rec['seconds'],1),flush=True)
  if gw in bad:continue
  pool=pd.read_csv(folder/'pool.csv.gz');f=pd.read_csv(folder/'features.csv.gz').set_index('code').loc[pool.code].reset_index();assert (pd.to_datetime(f.forecast_at,utc=True)==at).all();c=ec[ec['round'].eq(gw)].set_index('code').loc[f.code];av=attach(f);x=features(f,cols);xc=x.copy()
  for n in EXTRA:xc[n]=av[n].to_numpy(float)
  q=f[KEY+['forecast_at']].copy()
  for n in ['can_buy','seen_this_season','position']:q[n]=pool[n].to_numpy()
  for n in CE:q[n]=c[n].to_numpy()
  q['availability_present']=av.av_snapshot_present.to_numpy();q['fit_cutoff']=str(cutoff);q['frozen_short_mean'],q['frozen_long_mean']=predict_means(f,c)
  with threadpool_limits(limits=1):
   for arm,xarm in [('control',x),('candidate',xc)]:
    p=check(models[arm].predict(xarm))
    for k in range(3):q[f'{arm}_p{k}']=p[:,k]
    q[arm+'_minutes']=p[:,1]*q.frozen_short_mean+p[:,2]*q.frozen_long_mean;assert np.isfinite(q[arm+'_minutes']).all() and (q[arm+'_minutes']+1e-9>=60*p[:,2]).all()
  path=OUT/f'gw{gw:02d}.csv.gz';q.to_csv(path,index=False);atomic_json(OUT/f'gw{gw:02d}.lock.json',dict(prediction_sha256=sha(path),forecast_at=str(at),fit_cutoff=str(cutoff),current_outcomes_joined=False));frames.append(q)
 pd.concat(frames,ignore_index=True).to_csv(OUT/'predictions.csv.gz',index=False);verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'predictions_complete.json',dict(prediction_sha256=sha(OUT/'predictions.csv.gz'),probability_head_fits=fits,mean_reconstruction_fits=2,new_period_mean_fits=0,fits=audits));print('PREDICTIONS COMPLETE',flush=True)
def score():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);done=read(OUT/'predictions_complete.json');assert sha(OUT/'predictions.csv.gz')==done['prediction_sha256'];_,_,labels=load_data();z=pd.read_csv(OUT/'predictions.csv.gz').merge(labels,on=KEY,how='left',validate='one_to_one');mask=z.can_buy&z.native_minutes.notna()&z.target_total_points.notna()&z.minute_known.eq(True);coverage=dict(origins=int(z['round'].nunique()),requested=int(z.can_buy.sum()),known=int(mask.sum()),unknown=int((z.can_buy&~mask).sum()));z=z[mask].copy()
 for arm in ['control','candidate']:
  p=check(z[[f'{arm}_p{k}' for k in range(3)]].to_numpy());z[arm+'_error']=z[arm+'_minutes']-z.native_minutes;z[arm+'_mse']=z[arm+'_error']**2;z[arm+'_play_brier']=(1-p[:,0]-z.native_minutes.gt(0).astype(float))**2;z[arm+'_any60_brier']=(p[:,2]-z.any60.astype(float))**2
 stats=[];cohorts={'all':z,'no_season_history':z[~z.seen_this_season],'availability_present':z[z.availability_present.eq(1)],'availability_missing':z[z.availability_present.eq(0)],'archived1':z[z.calendar_known.eq(1)&z.planned_fixture_count.eq(1)],'archived2plus':z[z.calendar_known.eq(1)&z.planned_fixture_count.ge(2)],'unknown_calendar':z[z.calendar_known.eq(0)]};cohorts.update({f'position_{p}':z[z.position.eq(p)] for p in sorted(z.position.unique())})
 for name,q in cohorts.items():
  if q.empty:continue
  for arm in ['control','candidate']:
   stats.append(dict(cohort=name,arm=arm,n=len(q),mse=float(q[arm+'_mse'].mean()),rmse=float(np.sqrt(q[arm+'_mse'].mean())),mae=float(q[arm+'_error'].abs().mean()),bias=float(q[arm+'_error'].mean()),play_brier=float(q[arm+'_play_brier'].mean()),any60_brier=float(q[arm+'_any60_brier'].mean())))
 m=pd.DataFrame(stats);m.to_csv(OUT/'metrics.csv',index=False);z.to_csv(OUT/'scores.csv.gz',index=False);m0=m[m.cohort.eq('all')].set_index('arm');gates={k:bool(m0.loc['candidate',k]<m0.loc['control',k]) if k=='mse' else bool(m0.loc['candidate',k]<=m0.loc['control',k]) for k in ['mse','play_brier','any60_brier']};rng=np.random.default_rng(20261015);metrics=['mse','play_brier','any60_brier'];ds=[z.assign(delta=z['candidate_'+k]-z['control_'+k]).groupby('round').delta.agg(['sum','count']).reindex(range(1,39),fill_value=0).to_numpy() for k in metrics];draws=[]
 for _ in range(2000):
  ix=np.concatenate([np.arange(i,i+4) for i in rng.integers(0,35,10)])[:38];draws.append([d[ix,0].sum()/d[ix,1].sum() for d in ds])
 draws=np.array(draws);intervals=[dict(metric=k,difference=float((z['candidate_'+k]-z['control_'+k]).mean()),lower=float(np.quantile(draws[:,i],.025)),upper=float(np.quantile(draws[:,i],.975))) for i,k in enumerate(metrics)];pd.DataFrame(intervals).to_csv(OUT/'intervals.csv',index=False);atomic_json(OUT/'complete.json',dict(status='computed',research_gate_passed=all(gates.values()),gates=gates,primary_results=m0.reset_index().to_dict('records'),coverage=coverage,intervals=intervals,minute_means_fixed=True,manager_promoted=False));print('GATES',gates,flush=True);print(m0.to_string(),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
