"""Calendar inputs for minute-category probabilities with frozen calendar means."""
from pathlib import Path
import sys,time,hashlib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from model_lab.common import read,sha,atomic_json,verify_files,runtime
from model_lab.forecast import causal_training
from model_lab.probabilistic import PARAMS,Head,minute_class,check
from model_lab.probability_experiment import features
from model_lab.probability_refresh import load_data,REFRESH
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/calendar_probabilities_2026_10_16';CAL=ROOT/'reports/minute_calendar_2026_10_16';PRIOR=ROOT/'reports/probability_refresh_2026_10_15';CACHE=ROOT/'reports/fpl_improvement_2026_10_14/cache'
KEY=['season','round','code'];SEASONS=['2023-24','2024-25'];EXTRA=['planned_fixture_count','calendar_known'];ID='calendar-probabilities-20261016-v1'
def prepare():
 OUT.mkdir(exist_ok=True);old=read(CAL/'proposal.json');files=dict(old['input_hashes'])
 for p in [Path(__file__),CAL/'proposal.json',CAL/'predictions_complete.json',CAL/'verification.json',CAL/'complete.json',CAL/'RESULTATER.md']+[CAL/(s+n) for s in SEASONS for n in ['_predictions.csv.gz','_scores.csv.gz']]:files[str(p.relative_to(ROOT))]=sha(p)
 spec={**old,'id':ID,'candidate_id':'calendar_category_probabilities_fixed_calendar_means_v1','hypothesis':'Planned fixture count and calendar availability improve full minute expectation through category probabilities, with calendar-conditioned minute means fixed, without worsening event Brier.','change':'Only add the same two calendar features to the existing three-category HGB classifier; freeze accepted calendar-conditioned short/long means and point forecasts. Regenerate no-calendar probability control at identical cutoffs.','related_work':['minute-calendar-20261016-v1','probability-refresh-20261015-v1','probability-pilot-20261015-v1'],'input_hashes':files,'model_parameters':{**PARAMS,'classifier':'existing Head(3), HistGradientBoostingClassifier, log_loss','extra_features':EXTRA,'category_definitions':'0=zero total minutes;1=positive minutes but no individual fixture>=60;2=any fixture>=60','mean':'p1*frozen calendar short mean+p2*frozen calendar long mean; no calibration or new clipping'},'resources':{'maximum_head_fits':40,'control_classifier_fits':20,'candidate_classifier_fits':20,'minute_regression_fits':0,'threads':1,'refresh':REFRESH,'no_search':True},'maximum_runs':1,'success_criterion':'Strictly lower full-minute MSE in EACH of2023-24 and2024-25 versus calendar-means/frozen-old-probability control AND Brier(play) and Brier(any60) each no worse in EACH season. No noninferiority tolerance, no average-event or average-season tradeoff.','stop_rule':'Stop on hash/time/key mismatch, failed regenerated probability/control-mean parity, changed fixed means/point forecasts, invalid probabilities or expectation support violation. No automatic retry/tuning.', 'evaluation_contract':{**old['evaluation_contract'],'primary_control':'Accepted minute-calendar-20261016-v1 candidate_minutes: calendar-conditioned means with original periodic probabilities. Regenerated old Head(3) must reproduce all76 archived origins, atol=rtol=1e-10.','associated_probabilities':'Changed play=1-p0 and any60=p2. Evaluate Brier separately for each event and season; neither may worsen. Point probabilities copied unchanged.','training':'Same original causal rows/order, feature matrix, category labels, hyperparameters, seed and cadence. Add ONLY frozen planned_fixture_count/calendar_known to candidate classifier. Reuse independently verified prior calendar context; do not refit minute means.','primary_metric':'MSE for expected total round minutes','probability_guardrails':['Brier(play) candidate<=control per season','Brier(any60) candidate<=control per season'],'diagnosis_design':'User-authorized follow-up to minute-calendar-20261016-v1; no new calendar sources or row-selection changes.','uncertainty':'2000 paired four-origin blocks per season, seed20261015, joint resample for MSE and both Brier deltas; descriptive95% intervals, no gate override.','secondary_probability_diagnostics':'Binary log loss clipped at1e-15 for numerical evaluation only;10 equal-width reliability bins and event counts; class1 Brier and multiclass Brier reported descriptively.','support':'Both mixtures finite, nonnegative, probabilities sum1; E[minutes]>=60*p2 within1e-9. No candidate-only floors.'}}
 atomic_json(OUT/'proposal.json',spec);print('PREPARED',len(files),flush=True)
def run():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);assert not (OUT/'started.json').exists();atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json'),'started_at_utc':pd.Timestamp.now(tz='UTC').isoformat()})
 rows,cols,_=load_data();ctx=pd.read_csv(CAL/'training_calendar.csv.gz');rows=rows[rows.season.le('2024-25')].merge(ctx,on=KEY,how='left',sort=False,validate='one_to_one');assert rows[EXTRA].notna().all().all();audits=[];parity=0.;fits=0
 for s in SEASONS:
  frozen=pd.read_csv(CAL/(s+'_predictions.csv.gz')).set_index(['round','code']);frames=[]
  for gw in range(1,39):
   folder=CACHE/s/f'gw{gw:02d}';at=pd.Timestamp(read(folder/'manifest.json')['forecast_at'])
   if gw in REFRESH:
    tr,_=causal_training(rows,at,1);tr=tr[tr.native_minutes.notna()&tr.minute_known.eq(True)&tr.available_after_proxy.lt(at)];old=read(PRIOR/f'{s}_fit{gw:02d}.json');h=hashlib.sha256(tr[KEY].to_csv(index=False).encode()).hexdigest();assert h==old['training_keys_sha256'] and len(tr)==old['training_rows'];assert max(tr.forecast_at.max(),tr.target_h1_available_at.max(),tr.available_after_proxy.max())<at
    x=features(tr,cols);xc=x.copy()
    for n in EXTRA:xc[n]=tr[n].to_numpy(float)
    y=minute_class(tr.native_minutes,tr.any60);start=time.monotonic()
    with threadpool_limits(limits=1):models={'control':Head(3).fit(x,y),'candidate':Head(3).fit(xc,y)}
    fits+=2;assert fits<=40;record={**old,'head_fits':2,'seconds':time.monotonic()-start,'calendar_known_training_rows':int(tr.calendar_known.sum()),'class_counts':np.bincount(y,minlength=3).tolist()};audits.append(record);atomic_json(OUT/f'{s}_fit{gw:02d}.json',record);cutoff=at;print('FIT',s,gw,round(record['seconds'],1),flush=True)
   f=pd.read_csv(folder/'features.csv.gz');a=frozen.loc[pd.MultiIndex.from_arrays([[gw]*len(f),f.code])].reset_index();assert np.array_equal(a.code,f.code);assert (pd.to_datetime(f.forecast_at,utc=True)==at).all()
   x=features(f,cols);xc=x.copy()
   for n in EXTRA:xc[n]=a[n].to_numpy(float)
   q=a[KEY+['can_buy','seen_this_season','position','forecast_at','minutes_down','minutes_up']+EXTRA+['calendar_age_days']+[f'periodic_points_{i}' for i in range(5)]].copy();q['fit_cutoff']=str(cutoff);q['frozen_short_mean']=a.candidate_short_mean;q['frozen_long_mean']=a.candidate_long_mean
   with threadpool_limits(limits=1):
    for arm,xx in [('control',x),('candidate',xc)]:
     p=check(models[arm].predict(xx))
     for i in range(3):q[f'{arm}_p{i}']=p[:,i]
     q[arm+'_minutes']=p[:,1]*q.frozen_short_mean+p[:,2]*q.frozen_long_mean
     assert np.isfinite(q[arm+'_minutes']).all() and (q[arm+'_minutes']+1e-9>=60*p[:,2]).all()
   for i in range(3):
    d=np.abs(q[f'control_p{i}']-a[f'periodic_minutes_{i}']);parity=max(parity,float(d.max()));assert np.allclose(q[f'control_p{i}'],a[f'periodic_minutes_{i}'],atol=1e-10,rtol=1e-10)
   assert np.allclose(q.control_minutes,a.candidate_minutes,atol=1e-10,rtol=1e-10)
   path=OUT/f'{s}_gw{gw:02d}.csv.gz';q.to_csv(path,index=False);atomic_json(OUT/f'{s}_gw{gw:02d}.lock.json',{'prediction_sha256':sha(path),'forecast_at':str(at),'fit_cutoff':str(cutoff),'current_outcomes_joined':False});frames.append(q)
  pd.concat(frames,ignore_index=True).to_csv(OUT/(s+'_predictions.csv.gz'),index=False)
 verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'predictions_complete.json',{'fits':audits,'head_fits':fits,'probability_control_max_absolute_difference':parity,'prediction_hashes':{s:sha(OUT/(s+'_predictions.csv.gz')) for s in SEASONS},'fixed_means_source':'minute-calendar-20261016-v1','minute_regression_fits':0});print('PREDICTIONS COMPLETE',fits,parity,flush=True)
def score():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);done=read(OUT/'predictions_complete.json');_,_,labels=load_data();quality=pd.read_csv(ROOT/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz',usecols=KEY+['quality_flagged_for_sensitivity']);labels=labels.merge(quality,on=KEY,validate='one_to_one');stats=[];coverage=[];intervals=[];reliability=[];rng=np.random.default_rng(20261015)
 for s in SEASONS:
  path=OUT/(s+'_predictions.csv.gz');assert sha(path)==done['prediction_hashes'][s];z=pd.read_csv(path).merge(labels,on=KEY,how='left',validate='one_to_one');mask=z.can_buy&z.native_minutes.notna()&z.target_total_points.notna()&z.minute_known.eq(True);coverage.append(dict(season=s,requested=int(z.can_buy.sum()),known=int(mask.sum()),unknown=int((z.can_buy&~mask).sum())));z=z[mask].copy()
  old=pd.read_csv(CAL/(s+'_scores.csv.gz')).set_index(KEY);idx=pd.MultiIndex.from_frame(z[KEY]);assert set(idx)==set(old.index)
  y=minute_class(z.native_minutes,z.any60);yp=z.native_minutes.gt(0).to_numpy(float);yl=z.any60.to_numpy(float)
  for arm in ['control','candidate']:
   z[arm+'_error']=z[arm+'_minutes']-z.native_minutes;z[arm+'_squared_error']=z[arm+'_error']**2;p=check(z[[f'{arm}_p{i}' for i in range(3)]].to_numpy());z[arm+'_short_brier']=(p[:,1]-(y==1))**2;z[arm+'_multiclass_brier']=np.sum((p-np.eye(3)[y])**2,axis=1)
   for event,prob,actual in [('play',1-p[:,0],yp),('any60',p[:,2],yl)]:
    z[f'{arm}_{event}_brier']=(prob-actual)**2;clipped=np.clip(prob,1e-15,1-1e-15);z[f'{arm}_{event}_logloss']=-(actual*np.log(clipped)+(1-actual)*np.log1p(-clipped));bins=np.minimum((prob*10).astype(int),9)
    for b in range(10):
     m=bins==b
     if m.any():reliability.append(dict(season=s,arm=arm,event=event,bin=b,n=int(m.sum()),predicted=float(prob[m].mean()),actual=float(actual[m].mean()),events=int(actual[m].sum())))
  assert np.allclose(z.control_squared_error,old.loc[idx,'candidate_squared_error'],atol=1e-9,rtol=1e-10)
  assert np.allclose(z.control_play_brier,old.loc[idx,'play_brier'],atol=1e-12) and np.allclose(z.control_any60_brier,old.loc[idx,'any60_brier'],atol=1e-12)
  cohorts={'all':z,'minutes_down':z[z.minutes_down],'minutes_up':z[z.minutes_up],'no_season_history':z[~z.seen_this_season],'unflagged':z[z.quality_flagged_for_sensitivity.eq(False)],'flagged':z[z.quality_flagged_for_sensitivity.eq(True)],'archived1':z[z.calendar_known.eq(1)&z.planned_fixture_count.eq(1)],'archived2plus':z[z.calendar_known.eq(1)&z.planned_fixture_count.ge(2)],'unknown_calendar':z[z.calendar_known.eq(0)]}
  cohorts.update({f'position_{p}':z[z.position.eq(p)] for p in sorted(z.position.unique())})
  for name,q in cohorts.items():
   for arm in ['control','candidate']:
    e=q[arm+'_error'];record=dict(season=s,cohort=name,arm=arm,n=len(q),mse=float((e*e).mean()),rmse=float(np.sqrt((e*e).mean())),mae=float(e.abs().mean()),bias=float(e.mean()),play_events=int(q.native_minutes.gt(0).sum()),any60_events=int(q.any60.sum()))
    for metric in ['play_brier','any60_brier','short_brier','multiclass_brier','play_logloss','any60_logloss']:record[metric]=float(q[arm+'_'+metric].mean())
    stats.append(record)
  scores=['squared_error','play_brier','any60_brier'];z[KEY+['native_minutes','any60']+[arm+'_'+c for arm in ['control','candidate'] for c in scores]].to_csv(OUT/(s+'_scores.csv.gz'),index=False)
  ds=[]
  for metric in scores:ds.append(z.assign(delta=z['candidate_'+metric]-z['control_'+metric]).groupby('round').delta.agg(['sum','count']).reindex(range(1,39),fill_value=0).to_numpy())
  draws=[]
  for _ in range(2000):
   starts=rng.integers(0,35,10);ix=np.concatenate([np.arange(i,i+4) for i in starts])[:38];draws.append([d[ix,0].sum()/d[ix,1].sum() for d in ds])
  draws=np.array(draws)
  for k,metric in enumerate(scores):intervals.append(dict(season=s,metric=metric,difference=float((z['candidate_'+metric]-z['control_'+metric]).mean()),lower=float(np.quantile(draws[:,k],.025)),upper=float(np.quantile(draws[:,k],.975))))
 m=pd.DataFrame(stats);m.to_csv(OUT/'metrics.csv',index=False);pd.DataFrame(coverage).to_csv(OUT/'coverage.csv',index=False);pd.DataFrame(intervals).to_csv(OUT/'intervals.csv',index=False);pd.DataFrame(reliability).to_csv(OUT/'reliability.csv',index=False)
 primary=m[m.cohort.eq('all')];gates={};season_results=[]
 for s,g in primary.groupby('season'):
  g=g.set_index('arm');gate={metric:bool(g.loc['candidate',metric]<g.loc['control',metric]) if metric=='mse' else bool(g.loc['candidate',metric]<=g.loc['control',metric]) for metric in ['mse','play_brier','any60_brier']};gates[s]=gate;season_results.extend(g.reset_index().to_dict('records'))
 summary=[dict(arm=arm,equal_season_mse=float(q.mse.mean()),sqrt_equal_season_mse=float(np.sqrt(q.mse.mean())),secondary_pooled_mse=float(np.average(q.mse,weights=q.n))) for arm,q in primary.groupby('arm')]
 verify_files(ROOT,spec['input_hashes']);passed=all(all(g.values()) for g in gates.values());atomic_json(OUT/'complete.json',{'status':'computed','research_gate_passed':passed,'gates':gates,'primary_results':season_results,'summary':summary,'minute_means_unchanged':True,'manager_promoted':False});print('GATE',passed,gates,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
