"""Prequential conditional-minute offset calibration; immutable base predictions."""
from pathlib import Path
import sys,hashlib
import numpy as np
import pandas as pd
from model_lab.common import read,sha,atomic_json,verify_files,runtime
from model_lab.probability_refresh import load_data,REFRESH
ROOT=Path(__file__).resolve().parents[1];PRIOR=ROOT/'reports/probability_refresh_2026_10_15';OUT=ROOT/'reports/minute_calibration_2026_10_15';KEY=['season','round','code'];SEASONS=['2023-24','2024-25'];ID='minute-calibration-20261015-v1'
def correction(residual):
 values=np.asarray(residual,float)
 if not np.isfinite(values).all():raise ValueError('Nonfinite calibration residual')
 return float(values.sum()/(len(values)+200)) if len(values)>=100 else 0.
def prepare():
 OUT.mkdir(exist_ok=True);old=read(ROOT/'reports/minute_expectation_2026_10_15/proposal.json');files=dict(old['input_hashes'])
 for p in [Path(__file__),ROOT/'reports/minute_expectation_2026_10_15/complete.json',ROOT/'reports/minute_expectation_2026_10_15/verification.json']:files[str(p.relative_to(ROOT))]=sha(p)
 spec={**old,'id':ID,'candidate_id':'prequential_conditional_minute_offsets_v1','hypothesis':'Shrunk offsets fitted to earlier out-of-sample conditional-minute residuals improve unconditional minute MSE with category probabilities fixed.',
 'change':'At each four-round refresh, fit a separate additive offset for observed short/long categories on the prior8 same-season forecast rounds, only using outcomes available before the refresh. Use stored original forecasts, never in-sample refitted predictions. No new base-head training.',
 'related_work':['minute-expectation-20261015-v1','probability-refresh-20261015-v1'], 'input_hashes':files,
 'model_parameters':{'window_rounds':8,'minimum_rows_per_category':100,'zero_offset_ridge_pseudocount':200,'offset':'sum(actual_minutes-original_conditional_mean)/(n+200); zero if n<100','apply':'max(0,short_mean+short_offset); max(60,long_mean+long_offset); absent mean0','no_upper_cap':'Round totals can exceed90; no match-count assumption introduced.'},
 'resources':{'base_head_fits':0,'maximum_offset_estimates':40,'refresh_rounds':REFRESH,'seasons':2,'no_search':True},
 'success_criterion':'Strictly lower minute MSE than uncalibrated periodic mixture in EACH season, with copied play/any60 probability scores identical. No MAE or bias override.',
 'stop_rule':'Stop on changed hashes, chronology failure, invalid mixtures or copied-probability mismatch. No automatic retry or tuning.', 'maximum_runs':2,
 'evaluation_contract':{**old['evaluation_contract'],'primary_control':'Archived uncalibrated periodic_combined from probability-refresh-20261015-v1','training':'Calibration uses same-season buyable prequential forecasts from rounds max(1,gw-8)..gw-1, original forecast_at<calibration cutoff, original base fit cutoff<=original forecast origin, both minute and pipeline target availability<calibration cutoff, complete labels. Condition on actual historical minute category, never future category.','warmup':'GW1-4 no historical forecasts in this same-season window: zero offsets. Offsets remain fixed until next refresh.','shrinkage':'Minimize category residual SSE plus200*offset^2; at least100 rows, otherwise zero. Parameters fixed for this single candidate.','output_support':'Conditional short mean>=0 and long mean>=60, guaranteeing E[minutes]>=60*p(any60); report whether clipping alone changes zero-offset baseline.','evidence_role':'New calibration fitted causally on previously studied development years. Not untouched confirmation, no manager promotion.'}}
 atomic_json(OUT/'proposal.json',spec);print('PREPARED')
def run():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json')})
 rows,_,labels=load_data();availability=rows[KEY+['target_h1_available_at']];labels=labels.merge(availability,on=KEY,how='left',validate='one_to_one')
 quality=pd.read_csv(ROOT/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz',usecols=KEY+['quality_flagged_for_sensitivity']);labels=labels.merge(quality,on=KEY,validate='one_to_one')
 for s in SEASONS:
  base=pd.read_csv(PRIOR/(s+'_predictions.csv.gz'));base.forecast_at=pd.to_datetime(base.forecast_at,utc=True);base.periodic_fit_cutoff=pd.to_datetime(base.periodic_fit_cutoff,utc=True)
  assert (base.periodic_fit_cutoff<=base.forecast_at).all()
  joined=base.merge(labels,on=KEY,how='left',validate='one_to_one');frames=[]
  for gw in range(1,39):
   q=base[base['round'].eq(gw)].copy();assert q.forecast_at.nunique()==1;at=q.forecast_at.iloc[0]
   if gw in REFRESH:
    eligible=joined[joined['round'].between(max(1,gw-8),gw-1)&joined.can_buy&joined.forecast_at.lt(at)&joined.available_after_proxy.lt(at)&joined.target_h1_available_at.lt(at)&joined.native_minutes.notna()&joined.target_total_points.notna()&joined.minute_known.eq(True)]
    delta={};audit={'season':s,'round':gw,'cutoff':str(at),'categories':{}}
    for name,mask in [('short',eligible.native_minutes.gt(0)&~eligible.any60.eq(True)),('long',eligible.any60.eq(True))]:
     e=eligible[mask];residual=e.native_minutes-e['periodic_'+name+'_mean'];delta[name]=correction(residual)
     audit['categories'][name]={'n':len(e),'residual_sum':float(residual.sum()),'offset':delta[name],'keys_sha256':hashlib.sha256(e[KEY].to_csv(index=False).encode()).hexdigest(),'max_outcome_available':str(max(e.available_after_proxy.max(),e.target_h1_available_at.max())) if len(e) else None}
    atomic_json(OUT/f'{s}_cal{gw:02d}.json',audit);cutoff=at
   short=np.maximum(0,q.periodic_short_mean+delta['short']);long=np.maximum(60,q.periodic_long_mean+delta['long'])
   q['candidate_minutes']=q.periodic_minutes_1*short+q.periodic_minutes_2*long;q['control_minutes']=q.periodic_combined;q['calibrated_short_mean']=short;q['calibrated_long_mean']=long
   q['short_offset']=delta['short'];q['long_offset']=delta['long'];q['calibration_cutoff']=str(cutoff)
   assert np.isfinite(q.candidate_minutes).all() and (q.candidate_minutes+1e-9>=60*q.periodic_minutes_2).all()
   path=OUT/f'{s}_gw{gw:02d}.csv.gz';q.to_csv(path,index=False);atomic_json(OUT/f'{s}_gw{gw:02d}.lock.json',{'sha256':sha(path),'calibration_cutoff':str(cutoff),'forecast_at':str(at),'current_outcomes_used':False});frames.append(q)
  pd.concat(frames,ignore_index=True).to_csv(OUT/(s+'_predictions.csv.gz'),index=False)
 # Score only after all candidate predictions are durable. Earlier outcomes used only by causal calibration above.
 stats=[];coverage=[];intervals=[];rng=np.random.default_rng(20261015)
 for s in SEASONS:
  z=pd.read_csv(OUT/(s+'_predictions.csv.gz')).merge(labels,on=KEY,how='left',validate='one_to_one');mask=z.can_buy&z.native_minutes.notna()&z.target_total_points.notna()&z.minute_known.eq(True)
  coverage.append({'season':s,'requested':int(z.can_buy.sum()),'known':int(mask.sum()),'unknown':int((z.can_buy&~mask).sum())});z=z[mask].copy()
  for arm in ['control','candidate']:z[arm+'_error']=z[arm+'_minutes']-z.native_minutes;z[arm+'_squared_error']=z[arm+'_error']**2
  z['play_brier']=(1-z.periodic_minutes_0-z.native_minutes.gt(0))**2;z['any60_brier']=(z.periodic_minutes_2-z.any60.astype(float))**2
  for cohort,q in [('all',z),('minutes_up',z[z.minutes_up]),('minutes_down',z[z.minutes_down]),('no_season_history',z[~z.seen_this_season]),('unflagged',z[z.quality_flagged_for_sensitivity.eq(False)])]:
   for arm in ['control','candidate']:
    e=q[arm+'_error'];stats.append({'season':s,'cohort':cohort,'arm':arm,'n':len(q),'mse':float((e*e).mean()),'rmse':float(np.sqrt((e*e).mean())),'mae':float(e.abs().mean()),'bias':float(e.mean()),'play_brier':float(q.play_brier.mean()),'any60_brier':float(q.any60_brier.mean())})
  z[KEY+['control_error','candidate_error','control_squared_error','candidate_squared_error','play_brier','any60_brier']].to_csv(OUT/(s+'_scores.csv.gz'),index=False)
  prior=pd.read_csv(PRIOR/(s+'_scores.csv.gz')).set_index(KEY);idx=pd.MultiIndex.from_frame(z[KEY]);assert set(idx)==set(prior.index)
  assert np.allclose(z.play_brier,prior.loc[idx,'periodic_play_brier']) and np.allclose(z.any60_brier,prior.loc[idx,'periodic_60_brier'])
  d=z.assign(delta=z.candidate_squared_error-z.control_squared_error).groupby('round').delta.agg(['sum','count']).reindex(range(1,39),fill_value=0).to_numpy();draw=[]
  for _ in range(2000):
   start=rng.integers(0,35,10);ix=np.concatenate([np.arange(i,i+4) for i in start])[:38];v=d[ix].sum(0);draw.append(v[0]/v[1])
  intervals.append({'season':s,'mse_difference':float((z.candidate_squared_error-z.control_squared_error).mean()),'lower':float(np.quantile(draw,.025)),'upper':float(np.quantile(draw,.975))})
 m=pd.DataFrame(stats);m.to_csv(OUT/'metrics.csv',index=False);pd.DataFrame(coverage).to_csv(OUT/'coverage.csv',index=False);pd.DataFrame(intervals).to_csv(OUT/'intervals.csv',index=False)
 primary=m[m.cohort.eq('all')];v=primary.pivot(index='season',columns='arm',values='mse');summary=[]
 for arm,q in primary.groupby('arm'):summary.append({'arm':arm,'equal_season_mse':float(q.mse.mean()),'sqrt_equal_season_mse':float(np.sqrt(q.mse.mean())),'secondary_pooled_mse':float(np.average(q.mse,weights=q.n))})
 verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'complete.json',{'status':'pass','research_gate_passed':bool((v.candidate<v.control).all()),'probabilities_unchanged':True,'summary':summary,'manager_promoted':False});print('GATE',bool((v.candidate<v.control).all()),flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
