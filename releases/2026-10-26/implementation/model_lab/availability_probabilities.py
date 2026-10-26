"""Availability inputs under Git timestamp proxy; fixed calendar minute values."""
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
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/availability_probabilities_2026_10_16';CAL=ROOT/'reports/minute_calendar_2026_10_16';PRIOR=ROOT/'reports/probability_refresh_2026_10_15';CACHE=ROOT/'reports/fpl_improvement_2026_10_14/cache'
KEY=['season','round','code'];SEASONS=['2023-24','2024-25'];EXTRA=['av_snapshot_present','av_chance','av_chance_missing','av_news_present','av_news_age_hours','av_news_age_missing','av_snapshot_age_hours']+[f'av_status_{v}' for v in ['a','d','i','s','u','n','unknown']]+[f'av_reason_{v}' for v in ['illness','suspension','fitness','injury','transfer','unknown']];ID='availability-probabilities-20261016-v1'
AV=ROOT/'reports/availability_dataset_2026_10_16'
def attach_availability(frame):
 a=pd.read_csv(AV/'availability_proxy.csv.gz',keep_default_na=False);a=a[KEY+['forecast_at','snapshot_at_proxy','status_raw','chance_target','news_present','news_age_hours','snapshot_age_hours','reason']].rename(columns={'forecast_at':'av_origin'});q=frame.merge(a,on=KEY,how='left',sort=False,validate='one_to_one');present=q.av_origin.notna();assert (pd.to_datetime(q.loc[present,'snapshot_at_proxy'],utc=True)<pd.to_datetime(q.loc[present,'forecast_at'],utc=True)).all();assert (pd.to_datetime(q.loc[present,'av_origin'],utc=True)==pd.to_datetime(q.loc[present,'forecast_at'],utc=True)).all();q['av_snapshot_present']=present.astype(float);q['av_chance']=pd.to_numeric(q.chance_target,errors='coerce')/100;q['av_chance_missing']=q.av_chance.isna().astype(float);q['av_news_present']=q.news_present.eq(True).astype(float);q['av_news_age_hours']=pd.to_numeric(q.news_age_hours,errors='coerce');q['av_news_age_missing']=q.av_news_age_hours.isna().astype(float);q['av_snapshot_age_hours']=pd.to_numeric(q.snapshot_age_hours,errors='coerce')
 for field,values in [('status',['a','d','i','s','u','n','unknown']),('reason',['illness','suspension','fitness','injury','transfer','unknown'])]:
  raw=q['status_raw' if field=='status' else 'reason'].fillna('unknown');raw=raw.where(raw.isin(values),'unknown')
  for v in values:q[f'av_{field}_{v}']=raw.eq(v).astype(float)
 return q

def prepare():
 OUT.mkdir(exist_ok=True);old=read(ROOT/'reports/calendar_probabilities_2026_10_16/proposal.json');files=dict(old['input_hashes'])
 for p in [Path(__file__),AV/'complete.json',AV/'availability_proxy.csv.gz',AV/'deadline_discrepancy.json',AV/'readiness.json',ROOT/'reports/minute_simple_references_2026_10_16/predeadline_predictions.csv.gz']:files[str(p.relative_to(ROOT))]=sha(p)
 spec={**old,'id':ID,'candidate_id':'availability_category_probabilities_fixed_calendar_means_v1','hypothesis':'As-of proxy FPL status, target-bound chance, absence reason and news age improve expected minutes and both event probabilities.','change':'Add only availability features to original classifier. Omit 2024-25 GW15 from BOTH classifier training and evaluation. Retrain no-availability control; retain fixed calendar minute heads for BOTH. No calendar features added to classifier.','related_work':['calendar-probabilities-20261016-v1','minute-calendar-20261016-v1','probability-refresh-20261015-v1'],'input_hashes':files,'features':'Original extended numerical history and position indicators; candidate adds fixed availability encoding only.','model_parameters':{**old['model_parameters'],'extra_features':EXTRA},'evaluation_contract':{**old['evaluation_contract'],'primary_control':'Regenerated original classifier excluding 2024-25 GW15 training rows; control parity required before first affected fit (GW17), all2023-24. Frozen calendar minute means for both.','training':'Assert original training keys against archived fit first; then exclude 2024-25 GW15 symmetrically. Add availability at each historical row origin, not at fit time. Missing coverage retained as unknown, never future backfill.','diagnosis_design':'New availability information, not a retry of calendar-only probability input. Git timestamp proxy explicitly retained. No club-training pilot features.','origins':'75 evaluation origins: all2023-24, 2024-25 except GW15. All other deadlines unchanged. GW15 also absent from both classifier fitting sets; frozen means remain unchanged, so no claim of fully corrected historical pipeline.','cohorts':'Existing calendar/error strata plus fixed team_candidates, established_starters, uncertain_players, uncertain_candidates. No outcome-based selection.','uncertainty':'2000 paired four-calendar-round blocks with excluded GW15 represented by zero rows; seed20261015, descriptive only.','availability_encoding':'Status a,d,i,s,u,n,unknown and reason illness,suspension,fitness,injury,transfer,unknown fixed one-hot; chance/100; missing flags; numeric news age and snapshot age; no tuned transforms.','news_age':'Measured at snapshot; separate snapshot age until origin. No news means unknown age; missing chance stays NaN.'},'stop_rule':'Stop on input hash/time/key/support mismatch. Archived control parity required on unaffected origins. Fixed means must match source exactly at all75 origins. No tuning/retries after results.','success_criterion':'Strictly lower MSE in EACH season on the matched75-origin set AND Brier(play), Brier(any60) each no worse in EACH season. No tolerance or tradeoff.','maximum_runs':1}
 atomic_json(OUT/'proposal.json',spec);print('PREPARED',len(files),flush=True)
def run():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);assert not (OUT/'started.json').exists();atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json'),'started_at_utc':pd.Timestamp.now(tz='UTC').isoformat()})
 rows,cols,_=load_data();rows=attach_availability(rows[rows.season.le('2024-25')]);audits=[];parity=0.;fits=0
 for s in SEASONS:
  frozen=pd.read_csv(CAL/(s+'_predictions.csv.gz')).set_index(['round','code']);frames=[]
  for gw in range(1,39):
   if s=='2024-25' and gw==15:continue
   folder=CACHE/s/f'gw{gw:02d}';at=pd.Timestamp(read(folder/'manifest.json')['forecast_at'])
   if gw in REFRESH:
    tr,_=causal_training(rows,at,1);tr=tr[tr.native_minutes.notna()&tr.minute_known.eq(True)&tr.available_after_proxy.lt(at)];old=read(PRIOR/f'{s}_fit{gw:02d}.json');h=hashlib.sha256(tr[KEY].to_csv(index=False).encode()).hexdigest();assert h==old['training_keys_sha256'] and len(tr)==old['training_rows'];assert max(tr.forecast_at.max(),tr.target_h1_available_at.max(),tr.available_after_proxy.max())<at;original_n=len(tr);tr=tr[~(tr.season.eq('2024-25')&tr['round'].eq(15))];removed=original_n-len(tr)
    x=features(tr,cols);xc=x.copy()
    for n in EXTRA:xc[n]=tr[n].to_numpy(float)
    y=minute_class(tr.native_minutes,tr.any60);start=time.monotonic()
    with threadpool_limits(limits=1):models={'control':Head(3).fit(x,y),'candidate':Head(3).fit(xc,y)}
    fits+=2;assert fits<=40;record={**old,'head_fits':2,'seconds':time.monotonic()-start,'availability_training_rows':int(tr.av_snapshot_present.sum()),'excluded_gw15_training_rows':removed,'training_rows':len(tr),'original_training_keys_sha256':h,'training_keys_sha256':hashlib.sha256(tr[KEY].to_csv(index=False).encode()).hexdigest(),'class_counts':np.bincount(y,minlength=3).tolist()};audits.append(record);atomic_json(OUT/f'{s}_fit{gw:02d}.json',record);cutoff=at;print('FIT',s,gw,round(record['seconds'],1),flush=True)
   f=pd.read_csv(folder/'features.csv.gz');a=frozen.loc[pd.MultiIndex.from_arrays([[gw]*len(f),f.code])].reset_index();assert np.array_equal(a.code,f.code);assert (pd.to_datetime(f.forecast_at,utc=True)==at).all()
   av=attach_availability(f);x=features(f,cols);xc=x.copy()
   for n in EXTRA:xc[n]=av[n].to_numpy(float)
   q=a[KEY+['can_buy','seen_this_season','position','forecast_at','minutes_down','minutes_up']+['planned_fixture_count','calendar_known','calendar_age_days']+[f'periodic_points_{i}' for i in range(5)]].copy();q['fit_cutoff']=str(cutoff);q['frozen_short_mean']=a.candidate_short_mean;q['frozen_long_mean']=a.candidate_long_mean
   with threadpool_limits(limits=1):
    for arm,xx in [('control',x),('candidate',xc)]:
     p=check(models[arm].predict(xx))
     for i in range(3):q[f'{arm}_p{i}']=p[:,i]
     q[arm+'_minutes']=p[:,1]*q.frozen_short_mean+p[:,2]*q.frozen_long_mean
     assert np.isfinite(q[arm+'_minutes']).all() and (q[arm+'_minutes']+1e-9>=60*p[:,2]).all()
   if s=='2023-24' or gw<17:
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
  old=pd.read_csv(CAL/(s+'_scores.csv.gz'));old=old[~(old.season.eq('2024-25')&old['round'].eq(15))].set_index(KEY);idx=pd.MultiIndex.from_frame(z[KEY]);assert set(idx)==set(old.index)
  y=minute_class(z.native_minutes,z.any60);yp=z.native_minutes.gt(0).to_numpy(float);yl=z.any60.to_numpy(float)
  for arm in ['control','candidate']:
   z[arm+'_error']=z[arm+'_minutes']-z.native_minutes;z[arm+'_squared_error']=z[arm+'_error']**2;p=check(z[[f'{arm}_p{i}' for i in range(3)]].to_numpy());z[arm+'_short_brier']=(p[:,1]-(y==1))**2;z[arm+'_multiclass_brier']=np.sum((p-np.eye(3)[y])**2,axis=1)
   for event,prob,actual in [('play',1-p[:,0],yp),('any60',p[:,2],yl)]:
    z[f'{arm}_{event}_brier']=(prob-actual)**2;clipped=np.clip(prob,1e-15,1-1e-15);z[f'{arm}_{event}_logloss']=-(actual*np.log(clipped)+(1-actual)*np.log1p(-clipped));bins=np.minimum((prob*10).astype(int),9)
    for b in range(10):
     m=bins==b
     if m.any():reliability.append(dict(season=s,arm=arm,event=event,bin=b,n=int(m.sum()),predicted=float(prob[m].mean()),actual=float(actual[m].mean()),events=int(actual[m].sum())))
  unchanged=z if s=='2023-24' else z[z['round'].lt(17)];u=pd.MultiIndex.from_frame(unchanged[KEY]);assert np.allclose(unchanged.control_squared_error,old.loc[u,'candidate_squared_error'],atol=1e-9,rtol=1e-10)
  groups=pd.read_csv(ROOT/'reports/minute_simple_references_2026_10_16/predeadline_predictions.csv.gz',usecols=KEY+['team_candidates','history_group']);z=z.merge(groups,on=KEY,validate='one_to_one')
  cohorts={'all':z,'minutes_down':z[z.minutes_down],'minutes_up':z[z.minutes_up],'no_season_history':z[~z.seen_this_season],'unflagged':z[z.quality_flagged_for_sensitivity.eq(False)],'flagged':z[z.quality_flagged_for_sensitivity.eq(True)],'archived1':z[z.calendar_known.eq(1)&z.planned_fixture_count.eq(1)],'archived2plus':z[z.calendar_known.eq(1)&z.planned_fixture_count.ge(2)],'unknown_calendar':z[z.calendar_known.eq(0)]}
  cohorts.update(team_candidates=z[z.team_candidates],established_starters=z[z.history_group.eq('established_starters')],uncertain_players=z[z.history_group.eq('uncertain_players')],uncertain_candidates=z[z.team_candidates&z.history_group.eq('uncertain_players')])
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
