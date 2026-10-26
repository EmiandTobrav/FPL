"""Bounded, registered preseason probability pilot. Never modifies old experiments."""
from pathlib import Path
import json,time,sys
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from model_lab.forecast import pipeline_modules,causal_training
from model_lab.common import sha,atomic_json,read,verify_files,runtime
from model_lab.probabilistic import ProbabilityModels,PARAMS,point_class,minute_class,rps,check
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/probability_pilot_2026_10_15'
CACHE=ROOT/'reports/fpl_improvement_2026_10_14/cache';SEASONS=['2023-24','2024-25'];ID='probability-pilot-20261015-v1'
KEY=['season','round','code']
def prepare():
 OUT.mkdir(exist_ok=True)
 paths=[ROOT/'model_lab/probabilistic.py',Path(__file__),ROOT/'model_lab/forecast.py',ROOT/'model_lab/common.py']
 paths += [ROOT/'datasets/fpl_2026_27_best_effort_v1'/n for n in ['manifest.json','player_rounds.csv.xz','player_matches.csv.xz']]
 paths += [ROOT/'datasets/fpl_model_pipeline_v1'/n for n in ['manifest.json','schema.json','loader.py','pipeline.py','operational_proxy_v1.csv.xz']]
 for s in SEASONS:
  for gw in range(1,39):paths += [CACHE/s/f'gw{gw:02d}'/n for n in ['manifest.json','pool.csv.gz','features.csv.gz']]
 spec=dict(id=ID,hypothesis='Separate probability heads and minute-conditioned point distributions improve proper forecast scores on causal preseason folds.',
 change='New outputs and controlled round-level categorical losses, not a repeat of earlier fixture point-regression hurdle. Direct minute categories versus binary-gated categories; minute-conditioned point distribution versus direct categories; conditional minute means versus stratum constants.',related_work=['campaign1-minutes_hurdle_fixture_v1','wave3_selectable_loss','wave4_participation_history'],dataset_id='fpl_2026_27_best_effort_v1',input_hashes={str(p.relative_to(ROOT)):sha(p) for p in paths},clock='operational_proxy_v1',features='Numeric extended historical features; fixed position indicators; excludes club string. Identical features for all heads, no new fixture inputs.',candidate_id='round_probability_hurdle_v1',model_parameters=PARAMS,decision_policy={'mode':'forecast_only','manager_unchanged':True},benchmark_id='fixture_full_h3_adaptive_tc_harmonized_causal_v1',seasons=SEASONS,resources={'threads':1,'maximum_head_fits':18,'season_folds':2,'refresh':'once at preseason cutoff','no_tuning':True},success_criterion='Separate retain gates: direct minute categories lower mean Brier(play,any60) in BOTH seasons versus gated; conditional points lower normalized RPS in BOTH seasons versus direct and no worse p10 Brier in either; conditional minute means lower minute MAE in BOTH seasons versus stratum constants. These are research gates only.',stop_rule='Stop on hash/chronology/probability failure; no automatic retry or hyperparameter search.',maximum_runs=2)
 spec['evaluation_contract']={'points_bins':['<=0','1..2','3..5','6..9','>=10'],'minute_bins':['zero total minutes','positive minutes but no fixture >=60','at least one fixture >=60'],'target_scope':'Player ROUND; p60 is probability any fixture reaches60, not round-sum>=60. p10 includes doubles. Point bins are coarsened distributions, not exact PMF/CRPS.', 'train':'All pipeline rows with feature origin and target availability strictly before preseason cutoff, plus minute source availability before cutoff. Only nonmissing labels. No training-season filters based on test performance.','test':'As-of buyable cache pool, all rounds; save all predictions before joining outcomes. Unknown outcomes excluded equally; coverage reported.','no_claim':'Different training schedule/features from archived fixture model; comparisons among new arms only, not scientific proof of beating archived manager or full FPL forecast.', 'calibration':'No posthoc fitting; save raw probabilities and ten equal-width reliability bins.', 'subgroups':'history>=10, minute trend <=-15 or >=15; no current-season observation. Descriptive, not primary gates.'}
 atomic_json(OUT/'proposal.json',spec)
 print('Prepared',OUT/'proposal.json')
def features(frame,columns):
 x=frame.reindex(columns=columns).apply(pd.to_numeric,errors='raise').astype(float)
 pos=frame.f_position_last_known
 for name in ['GK','DEF','MID','FWD']:x['position_'+name]=pos.eq(name).astype(float)
 if np.isinf(x.to_numpy()).any():raise ValueError('Infinite features')
 return x

def run():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json')})
 loader,_=pipeline_modules();rows,schema=loader.load_rows()
 cols=[c for c in schema['extended_features'] if c not in schema['categorical_features']]
 rounds=pd.read_csv(ROOT/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz')
 matches=pd.read_csv(ROOT/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=KEY+['native_minutes'])
 g=matches.groupby(KEY).native_minutes
 match_minutes=g.agg(['max','count','size']).reset_index();match_minutes['any60']=match_minutes['max'].ge(60);match_minutes['minute_known']=match_minutes['count'].eq(match_minutes['size'])
 labels=rounds[KEY+['native_minutes','target_total_points','available_after_proxy']].merge(match_minutes[KEY+['any60','minute_known']],on=KEY,validate='one_to_one')
 labels['available_after_proxy']=pd.to_datetime(labels.available_after_proxy,utc=True)
 rows=rows.merge(labels[KEY+['native_minutes','any60','minute_known','available_after_proxy']],on=KEY,how='left',validate='one_to_one')
 allmetrics=[];reliability=[];audits=[];coverage=[]
 for season in SEASONS:
  cutoff=pd.Timestamp(read(CACHE/season/'gw01/manifest.json')['forecast_at'])
  train,_=causal_training(rows,cutoff,1)
  train=train[train.native_minutes.notna()&train.minute_known.eq(True)&train.available_after_proxy.lt(cutoff)].copy()
  assert train.forecast_at.max()<cutoff and train.target_h1_available_at.max()<cutoff
  x=features(train,cols)
  t=time.monotonic()
  with threadpool_limits(limits=1):model=ProbabilityModels().fit(x,train.target_total_points.to_numpy(),train.native_minutes.to_numpy(),train.any60.to_numpy(bool))
  print('Fit',season,len(train),'rows',round(time.monotonic()-t,1),'seconds',flush=True)
  pred_frames=[]
  for gw in range(1,39):
   folder=CACHE/season/f'gw{gw:02d}';man=read(folder/'manifest.json')
   for n in ['pool.csv.gz','features.csv.gz']:assert sha(folder/n)==man['files'][n]
   pool=pd.read_csv(folder/'pool.csv.gz');f=pd.read_csv(folder/'features.csv.gz')
   assert not pool.code.duplicated().any() and not f.code.duplicated().any()
   f=f.set_index('code').loc[pool.code].reset_index();assert (pd.to_datetime(f.forecast_at,utc=True)==pd.Timestamp(man['forecast_at'])).all()
   with threadpool_limits(limits=1):p=model.predict(features(f,cols))
   q=pool[['code','can_buy','seen_this_season']].copy();q['season']=season;q['round']=gw;q['forecast_at']=man['forecast_at'];q['fit_cutoff']=str(cutoff)
   q['minutes_down']=(f.f_history_count>=10)&(f.f_trend3_vs10_minutes<=-15);q['minutes_up']=(f.f_history_count>=10)&(f.f_trend3_vs10_minutes>=15)
   for name,values in p.items():
    if values.ndim==1:q[name]=values
    else:
     for i in range(values.shape[1]):q[name+'_'+str(i)]=values[:,i]
   pred_frames.append(q)
  predictions=pd.concat(pred_frames,ignore_index=True)
  dest=OUT/(season+'_predictions.csv.gz');predictions.to_csv(dest,index=False)
  atomic_json(OUT/(season+'_prediction_lock.json'),{'sha256':sha(dest),'fit_cutoff':str(cutoff),'training_rows':len(train),'max_train_origin':str(train.forecast_at.max()),'max_label_available':str(max(train.target_h1_available_at.max(),train.available_after_proxy.max())),'features':list(x.columns),'no_test_labels_passed_to_predict':True})
  # Outcome scoring occurs only after prediction artifact has been locked.
  z=predictions.merge(labels,on=KEY,how='left',validate='one_to_one');eligible=z.can_buy&z.native_minutes.notna()&z.target_total_points.notna()&z.minute_known.eq(True)
  coverage.append(dict(season=season,requested=int(z.can_buy.sum()),known=int(eligible.sum()),unknown=int((z.can_buy&~eligible).sum())))
  z=z[eligible].copy();z['minute_class']=minute_class(z.native_minutes,z.any60);z['point_class']=point_class(z.target_total_points)
  for arm in ['gated_minutes','direct_minutes']:
   p=z[[arm+'_'+str(i) for i in range(3)]].to_numpy();check(p)
   z[arm+'_play_brier']=(p[:,1:].sum(axis=1)-(z.native_minutes>0))**2
   z[arm+'_60_brier']=(p[:,2]-z.any60.astype(float))**2
   z[arm+'_primary']=(z[arm+'_play_brier']+z[arm+'_60_brier'])/2
   z[arm+'_logloss']=-np.log(np.maximum(p[np.arange(len(z)),z.minute_class],1e-12))
   for event,prob,actual in [('play',p[:,1:].sum(axis=1),(z.native_minutes>0).to_numpy()),('60',p[:,2],z.any60.to_numpy(bool))]:
    z[arm+'_'+event+'_probability']=prob
    for b in range(10):
     mask=(prob>=b/10)&((prob<(b+1)/10) if b<9 else (prob<=1))
     if mask.any():reliability.append(dict(season=season,arm=arm,event=event,bin=b,n=int(mask.sum()),predicted=float(prob[mask].mean()),observed=float(actual[mask].mean())))
  for arm in ['direct_points','conditional_points']:
   p=z[[arm+'_'+str(i) for i in range(5)]].to_numpy();check(p)
   z[arm+'_primary']=rps(p,z.point_class);z[arm+'_10_brier']=(p[:,4]-z.target_total_points.ge(10))**2
   z[arm+'_logloss']=-np.log(np.maximum(p[np.arange(len(z)),z.point_class],1e-12))
   for b in range(10):
    mask=(p[:,4]>=b/10)&((p[:,4]<(b+1)/10) if b<9 else (p[:,4]<=1))
    if mask.any():reliability.append(dict(season=season,arm=arm,event='10+',bin=b,n=int(mask.sum()),predicted=float(p[mask,4].mean()),observed=float(z.target_total_points.ge(10).to_numpy()[mask].mean())))
  for arm in ['constant_minutes','conditional_expected_minutes']:z[arm+'_mae']=(z[arm]-z.native_minutes).abs()
  scorecols=[c for c in z if c.endswith(('_brier','_primary','_logloss','_mae'))]
  for cohort,sub in [('all',z),('minutes_down',z[z.minutes_down]),('minutes_up',z[z.minutes_up]),('no_season_history',z[~z.seen_this_season])]:
   for c in scorecols:allmetrics.append(dict(season=season,cohort=cohort,metric=c,n=len(sub),value=float(sub[c].mean())))
  z[KEY+scorecols].to_csv(OUT/(season+'_scores.csv.gz'),index=False)
  audits.append(dict(season=season,training_rows=len(train),seconds=time.monotonic()-t,head_fits=9,cutoff=str(cutoff)))
  print('Locked and scored',season,len(z),flush=True)
 metrics=pd.DataFrame(allmetrics);metrics.to_csv(OUT/'metrics.csv',index=False);pd.DataFrame(reliability).to_csv(OUT/'reliability.csv',index=False);pd.DataFrame(coverage).to_csv(OUT/'coverage.csv',index=False)
 def value(s,c):return float(metrics[(metrics.season==s)&(metrics.cohort=='all')&(metrics.metric==c)].value.iloc[0])
 gates={'direct_minutes':all(value(s,'direct_minutes_primary')<value(s,'gated_minutes_primary') for s in SEASONS),'conditional_points':all(value(s,'conditional_points_primary')<value(s,'direct_points_primary') and value(s,'conditional_points_10_brier')<=value(s,'direct_points_10_brier') for s in SEASONS),'conditional_expected_minutes':all(value(s,'conditional_expected_minutes_mae')<value(s,'constant_minutes_mae') for s in SEASONS)}
 verify_files(ROOT,spec['input_hashes'])
 atomic_json(OUT/'complete.json',{'status':'pass','gates':gates,'folds':audits,'no_manager_promotion':True})
 print('GATES',gates,flush=True)
if __name__=='__main__':
 if sys.argv[1]=='prepare':prepare()
 elif sys.argv[1]=='run':run()
