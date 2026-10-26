"""Locked grouped availability ablation with shared source metadata and cached controls."""
from pathlib import Path
import sys,time,hashlib
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from model_lab.common import read,sha,atomic_json,verify_files,runtime
from model_lab.forecast import causal_training
from model_lab.probabilistic import Head,minute_class,check
from model_lab.probability_experiment import features
from model_lab.probability_refresh import load_data,REFRESH
from model_lab.availability_probabilities import attach_availability,EXTRA
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/availability_ablation_2026_10_16';BASE=ROOT/'reports/availability_probabilities_2026_10_16';CACHE=ROOT/'reports/fpl_improvement_2026_10_14/cache';KEY=['season','round','code'];SEASONS=['2023-24','2024-25'];ID='availability-ablation-20261016-v1'
META=['av_snapshot_present','av_snapshot_age_hours'];STATUS=['av_chance','av_chance_missing']+[f'av_status_{v}' for v in ['a','d','i','s','u','n','unknown']];NEWS=['av_news_present','av_news_age_hours','av_news_age_missing']+[f'av_reason_{v}' for v in ['illness','suspension','fitness','injury','transfer','unknown']]
NEW={'context_only':META,'status_chance':META+STATUS,'reason_age':META+NEWS};ARMS=['legacy_control','context_only','status_chance','reason_age','full'];PAIRS=[('context_only','legacy_control'),('status_chance','legacy_control'),('reason_age','legacy_control'),('full','legacy_control'),('status_chance','context_only'),('reason_age','context_only'),('full','status_chance'),('full','reason_age')]
assert set(META+STATUS+NEWS)==set(EXTRA) and len(META+STATUS+NEWS)==len(EXTRA)
def prepare():
 OUT.mkdir(exist_ok=True);old=read(BASE/'proposal.json');files=dict(old['input_hashes'])
 for p in [Path(__file__),BASE/'proposal.json',BASE/'complete.json',BASE/'verification.json',BASE/'predictions_complete.json']+[BASE/(s+'_predictions.csv.gz') for s in SEASONS]+[BASE/f'{s}_fit{gw:02d}.json' for s in SEASONS for gw in REFRESH]:files[str(p.relative_to(ROOT))]=sha(p)
 spec={**old,'id':ID,'candidate_id':'availability_grouped_ablation_v1','hypothesis':'Status/chance and absence-reason/news-age have separable and possibly redundant predictive contributions beyond common archive coverage/freshness metadata.','change':'Fixed 2x2 group ablation around common source metadata, plus original no-availability control. Reuse verified original-control and full-package predictions; train metadata-only, metadata+status/chance, metadata+reason/age.','related_work':['availability-probabilities-20261016-v1','minute-calendar-20261016-v1'],'input_hashes':files,'model_parameters':{**old['model_parameters'],'extra_features':{'shared_metadata':META,'status_chance':STATUS,'reason_age':NEWS},'new_arms':NEW},'resources':{'maximum_head_fits':60,'new_classifier_fits':60,'cached_classifier_arms':['legacy_control','full'],'minute_regression_fits':0,'threads':1,'refresh':REFRESH,'no_search':True},'maximum_runs':1,'evaluation_contract':{**old['evaluation_contract'],'primary_control':'Exact cached original control from availability-probabilities-20261016-v1, same75 origins and same training exclusion; full package also cached without changes.','training':'All new heads use exact same training keys/order/labels/cutoffs/hyperparameters as prior paired trial, including GW15 exclusion; source fields at each historical row origin.','cohorts':'all, team_candidates, established_starters, uncertain_players, uncertain_candidates fixed before outcomes.','contrasts':PAIRS,'attribution':'Within common metadata: status alone vs metadata; news alone vs metadata; full vs status and full vs news. Report nonadditivity and two-group Shapley average MSE contributions descriptively. No causal interpretation; correlated inputs and tree refitting mean contributions can be negative.','selection':'Retain existing full candidate unless a prespecified reduced arm passes unchanged six gates directly versus full. No tolerance or selecting one season. If both reduced arms pass, choose lower equal-season MSE; exact tie prefer status_chance. Passing only legacy control is insufficient to replace full.','uncertainty':'2000 paired four-calendar-round blocks, seed20261015; GW15 zero rows. Same joint draws for every arm/metric/contrast; descriptive95% intervals, no significance claim or override.'},'success_criterion':'For each prespecified candidate/comparator contrast: strictly lower MSE in BOTH seasons and no worse play-Brier and any60-Brier in BOTH seasons. Full replacement requires reduced arm vs full gate as specified.','stop_rule':'Stop on hashes, chronology, training-key mismatch, frozen-mean mismatch, invalid probabilities or support. No tuning, adaptive arms or automatic refits.'}
 atomic_json(OUT/'proposal.json',spec);print('PREPARED',flush=True)
def run():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json')});rows,cols,_=load_data();rows=attach_availability(rows[rows.season.le('2024-25')]);fits=0
 for season in SEASONS:
  frozen=pd.read_csv(BASE/(season+'_predictions.csv.gz')).set_index(['round','code']);frames=[]
  for gw in range(1,39):
   if season=='2024-25' and gw==15:continue
   folder=CACHE/season/f'gw{gw:02d}';at=pd.Timestamp(read(folder/'manifest.json')['forecast_at'])
   if gw in REFRESH:
    tr,_=causal_training(rows,at,1);tr=tr[tr.native_minutes.notna()&tr.minute_known.eq(True)&tr.available_after_proxy.lt(at)];tr=tr[~(tr.season.eq('2024-25')&tr['round'].eq(15))];prior=read(BASE/f'{season}_fit{gw:02d}.json');h=hashlib.sha256(tr[KEY].to_csv(index=False).encode()).hexdigest();assert h==prior['training_keys_sha256'] and len(tr)==prior['training_rows'];assert max(tr.forecast_at.max(),tr.target_h1_available_at.max(),tr.available_after_proxy.max())<at;x=features(tr,cols);y=minute_class(tr.native_minutes,tr.any60);models={};began=time.monotonic()
    with threadpool_limits(limits=1):
     for arm,extra in NEW.items():
      xx=x.copy()
      for n in extra:xx[n]=tr[n].to_numpy(float)
      models[arm]=Head(3).fit(xx,y);fits+=1
    assert fits<=60;atomic_json(OUT/f'{season}_fit{gw:02d}.json',{**prior,'head_fits':3,'new_arms':NEW,'seconds':time.monotonic()-began,'training_keys_sha256':h});print('FIT',season,gw,round(time.monotonic()-began,1),flush=True)
   f=pd.read_csv(folder/'features.csv.gz');q=frozen.loc[pd.MultiIndex.from_arrays([[gw]*len(f),f.code])].reset_index();assert np.array_equal(q.code,f.code);assert (pd.to_datetime(f.forecast_at,utc=True)==at).all();av=attach_availability(f);x=features(f,cols)
   q=q.rename(columns={**{f'control_p{i}':f'legacy_control_p{i}' for i in range(3)},**{f'candidate_p{i}':f'full_p{i}' for i in range(3)},'control_minutes':'legacy_control_minutes','candidate_minutes':'full_minutes'})
   with threadpool_limits(limits=1):
    for arm,extra in NEW.items():
     xx=x.copy()
     for n in extra:xx[n]=av[n].to_numpy(float)
     probs=check(models[arm].predict(xx))
     for i in range(3):q[f'{arm}_p{i}']=probs[:,i]
     q[arm+'_minutes']=probs[:,1]*q.frozen_short_mean+probs[:,2]*q.frozen_long_mean
     assert np.isfinite(q[arm+'_minutes']).all() and (q[arm+'_minutes']+1e-9>=60*probs[:,2]).all()
   dest=OUT/f'{season}_gw{gw:02d}.csv.gz';q.to_csv(dest,index=False);atomic_json(OUT/f'{season}_gw{gw:02d}.lock.json',{'forecast_at':str(at),'prediction_sha256':sha(dest),'current_outcomes_joined':False});frames.append(q)
  pd.concat(frames,ignore_index=True).to_csv(OUT/f'{season}_predictions.csv.gz',index=False)
 verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'predictions_complete.json',{'head_fits':fits,'minute_regression_fits':0,'prediction_hashes':{s:sha(OUT/f'{s}_predictions.csv.gz') for s in SEASONS}});print('PREDICTIONS COMPLETE',fits,flush=True)
def score():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);done=read(OUT/'predictions_complete.json');_,_,labels=load_data();groups=pd.read_csv(ROOT/'reports/minute_simple_references_2026_10_16/predeadline_predictions.csv.gz',usecols=KEY+['team_candidates','history_group']);metrics=[];intervals=[];coverage=[];rng=np.random.default_rng(20261015)
 for season in SEASONS:
  path=OUT/f'{season}_predictions.csv.gz';assert sha(path)==done['prediction_hashes'][season];z=pd.read_csv(path).merge(labels,on=KEY,how='left',validate='one_to_one');mask=z.can_buy&z.native_minutes.notna()&z.target_total_points.notna()&z.minute_known.eq(True);coverage.append(dict(season=season,requested=int(z.can_buy.sum()),known=int(mask.sum()),unknown=int((z.can_buy&~mask).sum())));z=z[mask].merge(groups,on=KEY,validate='one_to_one');previous=pd.read_csv(BASE/f'{season}_scores.csv.gz');assert set(map(tuple,z[KEY].values))==set(map(tuple,previous[KEY].values))
  for arm in ARMS:
   probs=check(z[[f'{arm}_p{i}' for i in range(3)]].to_numpy());z[arm+'_mse']=(z[arm+'_minutes']-z.native_minutes)**2;z[arm+'_mae']=(z[arm+'_minutes']-z.native_minutes).abs();z[arm+'_play_brier']=(1-probs[:,0]-z.native_minutes.gt(0).to_numpy(float))**2;z[arm+'_any60_brier']=(probs[:,2]-z.any60.to_numpy(float))**2
  cohorts={'all':z,'team_candidates':z[z.team_candidates],'established_starters':z[z.history_group.eq('established_starters')],'uncertain_players':z[z.history_group.eq('uncertain_players')],'uncertain_candidates':z[z.team_candidates&z.history_group.eq('uncertain_players')]}
  for cohort,g in cohorts.items():
   for arm in ARMS:metrics.append(dict(season=season,cohort=cohort,arm=arm,n=len(g),**{k:float(g[f'{arm}_{k}'].mean()) for k in ['mse','mae','play_brier','any60_brier']}))
  z[KEY+['native_minutes','any60']+[f'{a}_{k}' for a in ARMS for k in ['mse','mae','play_brier','any60_brier']]].to_csv(OUT/f'{season}_scores.csv.gz',index=False)
  pairs=PAIRS+[('status_chance','full'),('reason_age','full')];ds=[];names=[]
  for a,b in pairs:
   for k in ['mse','play_brier','any60_brier']:
    ds.append(z.assign(delta=z[f'{a}_{k}']-z[f'{b}_{k}']).groupby('round').delta.agg(['sum','count']).reindex(range(1,39),fill_value=0).to_numpy());names.append((a,b,k))
  draws=[]
  for _ in range(2000):
   starts=rng.integers(0,35,10);ix=np.concatenate([np.arange(i,i+4) for i in starts])[:38];draws.append([d[ix,0].sum()/d[ix,1].sum() for d in ds])
  draws=np.asarray(draws)
  for i,(a,b,k) in enumerate(names):intervals.append(dict(season=season,candidate=a,comparator=b,metric=k,delta=float((z[f'{a}_{k}']-z[f'{b}_{k}']).mean()),lower=float(np.quantile(draws[:,i],.025)),upper=float(np.quantile(draws[:,i],.975))))
 m=pd.DataFrame(metrics);m.to_csv(OUT/'metrics.csv',index=False);pd.DataFrame(intervals).to_csv(OUT/'intervals.csv',index=False);pd.DataFrame(coverage).to_csv(OUT/'coverage.csv',index=False);primary=m[m.cohort.eq('all')];gates={};attribution=[]
 for a,b in PAIRS+[('status_chance','full'),('reason_age','full')]:
  gates[a+'__vs__'+b]={}
  for season in SEASONS:
   g=primary[primary.season.eq(season)].set_index('arm');gates[a+'__vs__'+b][season]={k:bool(g.loc[a,k]<g.loc[b,k]) if k=='mse' else bool(g.loc[a,k]<=g.loc[b,k]) for k in ['mse','play_brier','any60_brier']}
 for season in SEASONS:
  g=primary[primary.season.eq(season)].set_index('arm').mse;meta=g.legacy_control-g.context_only;s=g.context_only-g.status_chance;n=g.context_only-g.reason_age;conditional_s=g.reason_age-g.full;conditional_n=g.status_chance-g.full;attribution.append(dict(season=season,metadata_gain=meta,status_standalone_gain=s,news_standalone_gain=n,status_conditional_gain=conditional_s,news_conditional_gain=conditional_n,status_shapley=(s+conditional_s)/2,news_shapley=(n+conditional_n)/2,interaction_gain=(g.context_only-g.full)-s-n,total_gain=g.legacy_control-g.full))
 pd.DataFrame(attribution).to_csv(OUT/'attribution.csv',index=False);eligible=[a for a in ['status_chance','reason_age'] if all(all(v.values()) for v in gates[a+'__vs__full'].values())];selected=min(eligible,key=lambda a:(primary[primary.arm.eq(a)].mse.mean(),a!='status_chance')) if eligible else 'full';verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'complete.json',{'status':'computed','gates':gates,'selected_arm':selected,'reduced_arms_passing_vs_full':eligible,'primary_results':primary.to_dict('records'),'attribution':attribution,'manager_promoted':False});print('SELECTED',selected,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
