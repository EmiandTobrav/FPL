"""Frozen 2x2 minute combination and four-round refitting experiment."""
from pathlib import Path
import sys,time
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from model_lab.common import atomic_json,read,sha,verify_files,runtime
from model_lab.forecast import pipeline_modules,causal_training
from model_lab.probabilistic import Head,PARAMS,minute_class,check,rps,point_class
from model_lab.probability_experiment import features
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/probability_refresh_2026_10_15';PRIOR=ROOT/'reports/probability_pilot_2026_10_15';CACHE=ROOT/'reports/fpl_improvement_2026_10_14/cache'
KEY=['season','round','code'];SEASONS=['2023-24','2024-25'];ID='probability-refresh-20261015-v1'
REFRESH=[1,5,9,13,17,21,25,29,33,37]
class Model:
 def fit(self,x,points,minutes,any60,parity=False):
  c=minute_class(minutes,any60);self.direct=Head(3).fit(x,c);self.points=Head(5).fit(x,point_class(points));self.means=np.array([np.mean(minutes[c==i]) for i in range(3)])
  self.minute_heads=[]
  for i in [1,2]:
   cols=x.columns[x[c==i].notna().any()].tolist();m=HistGradientBoostingRegressor(**PARAMS).fit(x.loc[c==i,cols],minutes[c==i]);self.minute_heads.append((cols,m))
  self.parity=parity
  if parity:self.play=Head(2).fit(x,c>0);self.long=Head(2).fit(x[c>0],c[c>0]==2)
  return self
 def predict(self,x):
  p=self.direct.predict(x);v=[np.clip(m.predict(x[c]),0,None) for c,m in self.minute_heads]
  out={'minutes':p,'points':self.points.predict(x),'short_mean':v[0],'long_mean':v[1],'combined':p[:,1]*v[0]+p[:,2]*v[1],'direct_constant':p@self.means}
  if self.parity:
   play=self.play.predict(x)[:,1];long=self.long.predict(x)[:,1];g=check(np.column_stack([1-play,play*(1-long),play*long]))
   out.update(gated=g,gated_constant=g@self.means,gated_conditional=g[:,1]*v[0]+g[:,2]*v[1])
  return out

def prepare():
 OUT.mkdir(exist_ok=True);old=read(PRIOR/'proposal.json')
 files=dict(old['input_hashes'])
 for p in [Path(__file__),PRIOR/'proposal.json',PRIOR/'complete.json',PRIOR/'verification.json',PRIOR/'metrics.csv']+[PRIOR/(s+n) for s in SEASONS for n in ['_predictions.csv.gz','_prediction_lock.json']]:files[str(p.relative_to(ROOT))]=sha(p)
 spec={**old,'id':ID,'hypothesis':'The two minute improvements combine beneficially; causal four-round refits improve probability forecasts versus identical preseason models.',
 'change':'2x2 category/conditional-minute evaluation followed by fixed versus every-four-round refitting of the SAME combined-minute and direct-point models. Old conditional-point arm excluded because it failed. Preseason refits must reproduce archived controls.',
 'related_work':['probability-pilot-20261015-v1'],'candidate_id':'round_probability_refresh_v1','input_hashes':files,
 'resources':{'threads':1,'maximum_head_fits':84,'refit_rounds':REFRESH,'no_tuning':True,'per_model_hyperparameters':PARAMS,'extra_refitting_cost_charged_to_candidate':True},
 'success_criterion':'Combination: combined minute MAE strictly lower than BOTH archived gated-constant and gated-conditional means in EACH season. Refresh minutes: lower combined minute MAE AND lower mean Brier(play,any60), neither constituent Brier worse, in EACH season versus fixed SAME architecture. Refresh points: lower normalized RPS and no worse 10+ Brier in EACH season versus fixed direct categorical model. Separate research gates; no manager promotion.',
 'stop_rule':'Fail on hash, chronology, invalid probability or preseason parity error; no automatic retries. Run both refresh seasons even if combination gate fails; no outcome-based switching.', 'maximum_runs':2}
 spec['evaluation_contract']={**old['evaluation_contract'],'train':'Same causal filtering and features as prior; strictly earlier origin and label availability at each registered refresh. No weighting, calibration or new inputs.','controls':'Archived preseason heads verified by regeneration at all76 origins; new fixed combined output holds pretrained heads constant; compare periodic against fixed combination. 2x2 recorded.', 'parity_tolerance':'absolute1e-10 relative1e-10','intervals':'Descriptive paired 4-origin moving blocks, 2000 draws, seed20261015, per season; not a gate.'}
 atomic_json(OUT/'proposal.json',spec);print('PREPARED',flush=True)

def load_data():
 loader,_=pipeline_modules();rows,schema=loader.load_rows();cols=[c for c in schema['extended_features'] if c not in schema['categorical_features']]
 rounds=pd.read_csv(ROOT/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz')
 matches=pd.read_csv(ROOT/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=KEY+['native_minutes']);g=matches.groupby(KEY).native_minutes
 m=g.agg(['max','count','size']).reset_index();m['any60']=m['max'].ge(60);m['minute_known']=m['count'].eq(m['size'])
 labels=rounds[KEY+['native_minutes','target_total_points','available_after_proxy']].merge(m[KEY+['any60','minute_known']],on=KEY,validate='one_to_one');labels.available_after_proxy=pd.to_datetime(labels.available_after_proxy,utc=True)
 rows=rows.merge(labels[KEY+['native_minutes','any60','minute_known','available_after_proxy']],on=KEY,how='left',validate='one_to_one')
 return rows,cols,labels

def run():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json')})
 rows,cols,_=load_data();fits=[];parity_max=0.;fit_count=0
 for s in SEASONS:
  old=pd.read_csv(PRIOR/(s+'_predictions.csv.gz')).set_index(['round','code']);frames=[];fixed=None
  for gw in range(1,39):
   folder=CACHE/s/f'gw{gw:02d}';man=read(folder/'manifest.json');at=pd.Timestamp(man['forecast_at'])
   if gw in REFRESH:
    train,_=causal_training(rows,at,1);train=train[train.native_minutes.notna()&train.minute_known.eq(True)&train.available_after_proxy.lt(at)]
    assert train.forecast_at.max()<at and train.target_h1_available_at.max()<at and train.available_after_proxy.max()<at
    x=features(train,cols);began=time.monotonic()
    with threadpool_limits(limits=1):current=Model().fit(x,train.target_total_points.to_numpy(),train.native_minutes.to_numpy(),train.any60.to_numpy(bool),parity=gw==1)
    if gw==1:fixed=current
    n=6 if gw==1 else 4;fit_count+=n;assert fit_count<=84
    fit_cutoff=at
    audit={'season':s,'round':gw,'fit_cutoff':str(at),'training_rows':len(train),'max_train_origin':str(train.forecast_at.max()),'max_label_available':str(max(train.target_h1_available_at.max(),train.available_after_proxy.max())),'training_keys_sha256':__import__('hashlib').sha256(train[KEY].to_csv(index=False).encode()).hexdigest(),'head_fits':n,'seconds':time.monotonic()-began}
    atomic_json(OUT/f'{s}_fit{gw:02d}.json',audit);fits.append(audit);print('Fit',s,gw,len(train),round(audit['seconds'],1),'seconds',flush=True)
   pool=pd.read_csv(folder/'pool.csv.gz');f=pd.read_csv(folder/'features.csv.gz').set_index('code').loc[pool.code].reset_index()
   assert not pool.code.duplicated().any() and (pd.to_datetime(f.forecast_at,utc=True)==at).all()
   x=features(f,cols)
   with threadpool_limits(limits=1):a=fixed.predict(x);b=a if current is fixed else current.predict(x)
   archived=old.loc[pd.MultiIndex.from_arrays([[gw]*len(pool),pool.code])]
   comparisons=[(a['minutes'],archived[[f'direct_minutes_{i}' for i in range(3)]].to_numpy()),(a['points'],archived[[f'direct_points_{i}' for i in range(5)]].to_numpy()),(a['gated'],archived[[f'gated_minutes_{i}' for i in range(3)]].to_numpy()),(a['gated_constant'],archived.constant_minutes.to_numpy()),(a['gated_conditional'],archived.conditional_expected_minutes.to_numpy())]
   for v,w in comparisons:
    parity_max=max(parity_max,float(np.max(np.abs(v-w))));assert np.allclose(v,w,atol=1e-10,rtol=1e-10),'Preseason parity failed'
   q=pool[['code','can_buy','seen_this_season']].copy();q['season']=s;q['round']=gw;q['forecast_at']=str(at);q['periodic_fit_cutoff']=str(fit_cutoff)
   q['minutes_down']=(f.f_history_count>=10)&(f.f_trend3_vs10_minutes<=-15);q['minutes_up']=(f.f_history_count>=10)&(f.f_trend3_vs10_minutes>=15)
   q['gated_constant']=a['gated_constant'];q['gated_conditional']=a['gated_conditional'];q['direct_constant']=a['direct_constant']
   for arm,result in [('fixed',a),('periodic',b)]:
    for name in ['combined','short_mean','long_mean']:q[arm+'_'+name]=result[name]
    for name in ['minutes','points']:
     for i in range(result[name].shape[1]):q[f'{arm}_{name}_{i}']=result[name][:,i]
   frames.append(q)
   # Each round's predictions are durable before the next origin is processed.
   dest=OUT/f'{s}_gw{gw:02d}.csv.gz';q.to_csv(dest,index=False);atomic_json(OUT/f'{s}_gw{gw:02d}.lock.json',{'prediction_sha256':sha(dest),'fit_cutoff':str(fit_cutoff),'forecast_at':str(at)})
  pd.concat(frames,ignore_index=True).to_csv(OUT/(s+'_predictions.csv.gz'),index=False)
 verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'complete.json',{'status':'predictions_complete','head_fits':fit_count,'parity_max_absolute_difference':parity_max,'fits':fits,'season_predictions':{s:sha(OUT/(s+'_predictions.csv.gz')) for s in SEASONS}})
 print('PREDICTIONS COMPLETE',fit_count,'fits',flush=True)

def score():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);complete=read(OUT/'complete.json');_,_,labels=load_data();metrics=[];coverage=[];intervals=[];reliability=[];rng=np.random.default_rng(20261015)
 for s in SEASONS:
  path=OUT/(s+'_predictions.csv.gz');assert sha(path)==complete['season_predictions'][s]
  q=pd.read_csv(path);z=q.merge(labels,on=KEY,how='left',validate='one_to_one');mask=z.can_buy&z.native_minutes.notna()&z.target_total_points.notna()&z.minute_known.eq(True)
  coverage.append({'season':s,'requested':int(z.can_buy.sum()),'known':int(mask.sum()),'unknown':int((z.can_buy&~mask).sum())});z=z[mask].copy()
  for name in ['gated_constant','gated_conditional','direct_constant','fixed_combined','periodic_combined']:z[name+'_mae']=(z[name]-z.native_minutes).abs()
  for arm in ['fixed','periodic']:
   p=check(z[[f'{arm}_minutes_{i}' for i in range(3)]].to_numpy());v=check(z[[f'{arm}_points_{i}' for i in range(5)]].to_numpy())
   z[arm+'_play_brier']=(1-p[:,0]-z.native_minutes.gt(0))**2;z[arm+'_60_brier']=(p[:,2]-z.any60.astype(float))**2
   z[arm+'_minute_brier']=(z[arm+'_play_brier']+z[arm+'_60_brier'])/2
   z[arm+'_rps']=rps(v,point_class(z.target_total_points));z[arm+'_10_brier']=(v[:,4]-z.target_total_points.ge(10))**2
   for event,prob,y in [('play',1-p[:,0],z.native_minutes.gt(0).to_numpy()),('60',p[:,2],z.any60.to_numpy(bool)),('10',v[:,4],z.target_total_points.ge(10).to_numpy())]:
    for bin in range(10):
     selected=(prob>=bin/10)&((prob<(bin+1)/10) if bin<9 else (prob<=1))
     if selected.any():reliability.append({'season':s,'arm':arm,'event':event,'bin':bin,'n':int(selected.sum()),'predicted':float(prob[selected].mean()),'observed':float(y[selected].mean())})
  scores=[c for c in z if c.endswith(('_mae','_brier','_rps'))]
  for cohort,g in [('all',z),('minutes_down',z[z.minutes_down]),('minutes_up',z[z.minutes_up]),('no_season_history',z[~z.seen_this_season])]:
   for c in scores:metrics.append({'season':s,'cohort':cohort,'metric':c,'n':len(g),'value':float(g[c].mean())})
  z[KEY+scores].to_csv(OUT/(s+'_scores.csv.gz'),index=False)
  for name,a,b in [('combination','fixed_combined_mae','gated_conditional_mae'),('refresh_minutes','periodic_combined_mae','fixed_combined_mae'),('refresh_probability','periodic_minute_brier','fixed_minute_brier'),('refresh_points','periodic_rps','fixed_rps')]:
   d=z.assign(delta=z[a]-z[b]).groupby('round').delta.agg(['sum','count']).reindex(range(1,39),fill_value=0).to_numpy();draw=[]
   for _ in range(2000):
    starts=rng.integers(0,35,10);ix=np.concatenate([np.arange(i,i+4) for i in starts])[:38];v=d[ix].sum(0);draw.append(v[0]/v[1])
   intervals.append({'season':s,'comparison':name,'delta':float((z[a]-z[b]).mean()),'lower':float(np.quantile(draw,.025)),'upper':float(np.quantile(draw,.975))})
 m=pd.DataFrame(metrics);m.to_csv(OUT/'metrics.csv',index=False);pd.DataFrame(coverage).to_csv(OUT/'coverage.csv',index=False);pd.DataFrame(intervals).to_csv(OUT/'intervals.csv',index=False);pd.DataFrame(reliability).to_csv(OUT/'reliability.csv',index=False)
 def v(s,c):return float(m[(m.season==s)&(m.cohort=='all')&(m.metric==c)].value.iloc[0])
 gates={'combination':all(v(s,'fixed_combined_mae')<min(v(s,'gated_constant_mae'),v(s,'gated_conditional_mae')) for s in SEASONS),'refresh_minutes':all(v(s,'periodic_combined_mae')<v(s,'fixed_combined_mae') and v(s,'periodic_minute_brier')<v(s,'fixed_minute_brier') and all(v(s,'periodic_'+c)<=v(s,'fixed_'+c) for c in ['play_brier','60_brier']) for s in SEASONS),'refresh_points':all(v(s,'periodic_rps')<v(s,'fixed_rps') and v(s,'periodic_10_brier')<=v(s,'fixed_10_brier') for s in SEASONS)}
 atomic_json(OUT/'scored.json',{'gates':gates,'no_manager_promotion':True});print('GATES',gates,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
