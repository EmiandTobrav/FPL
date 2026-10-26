"""Preregistered selective update ablation using frozen probability components."""
from pathlib import Path
import sys
import numpy as np
import pandas as pd
from model_lab.common import read,sha,atomic_json,verify_files,runtime
ROOT=Path(__file__).resolve().parents[1];PRIOR=ROOT/'reports/probability_refresh_2026_10_15';OUT=ROOT/'reports/probability_selective_refresh_2026_10_15'
ID='probability-selective-refresh-20261015-v1';KEY=['season','round','code'];SEASONS=['2023-24','2024-25']
def prepare():
 OUT.mkdir(exist_ok=True);old=read(PRIOR/'proposal.json');files=dict(old['input_hashes'])
 for path in [Path(__file__),PRIOR/'proposal.json',PRIOR/'complete.json',PRIOR/'verification.json',PRIOR/'metrics.csv']+[PRIOR/(s+suffix) for s in SEASONS for suffix in ['_predictions.csv.gz','_scores.csv.gz']]:files[str(path.relative_to(ROOT))]=sha(path)
 spec={**old,'id':ID,'hypothesis':'Updating category probabilities every four rounds while retaining preseason conditional minute values lowers minute MAE in each development season versus the fixed combined model.',
 'change':'No new fitting: cross saved fixed/periodic probabilities with fixed/periodic conditional minute predictions. Selective probability update is the sole primary candidate; reverse cross is diagnostic only.',
 'related_work':['probability-refresh-20261015-v1','probability-pilot-20261015-v1'],'candidate_id':'round_probability_selective_refresh_v1','input_hashes':files,
 'model_parameters':{'inherited':'Frozen predecessor heads; no new parameters','combination':'p(short)*conditional_short_minutes + p(any60)*conditional_long_minutes'},
 'resources':{'new_fits':0,'manager_runs':0,'seasons':2,'resampling_draws':2000,'seed':20261015},
 'success_criterion':'Primary: selective probability update strictly lowers minute MAE versus fixed combined model in EACH season, with neither play nor any60 Brier worse in either. Full-refresh comparison is secondary, separately report whether candidate wins both years. Reverse-cross arm is diagnostic only and cannot be promoted here.',
 'stop_rule':'Stop on changed hashes, invalid probabilities, prediction formula or control mismatch. No threshold tuning or automatic retry.', 'maximum_runs':2}
 spec['evaluation_contract']={**old['evaluation_contract'],'controls':'Primary fixed combined; secondary full periodic; reverse-cross diagnostic preregistered. All share identical known outcome keys.','intervals':'2000 paired moving-block draws of four consecutive rounds within season; seed20261015; descriptive only, no multiple-testing-adjusted claims.','selection_warning':'Hypothesis chosen after predecessor results on same development years; not an untouched confirmatory test.'}
 atomic_json(OUT/'proposal.json',spec);print('PREPARED',flush=True)
def blend(p,short,long):
 if not np.isfinite(p).all() or (p<0).any() or not np.allclose(p.sum(1),1):raise ValueError('Invalid probabilities')
 value=p[:,1]*short+p[:,2]*long
 if not np.isfinite(value).all() or (value<0).any():raise ValueError('Invalid minutes')
 return value

def run():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json')})
 # Assemble and lock BOTH seasons before opening outcome files.
 for season in SEASONS:
  src=PRIOR/(season+'_predictions.csv.gz');q=pd.read_csv(src);assert not q.duplicated(KEY).any()
  p0=q[[f'fixed_minutes_{i}' for i in range(3)]].to_numpy();p1=q[[f'periodic_minutes_{i}' for i in range(3)]].to_numpy()
  z=q[KEY+['forecast_at','periodic_fit_cutoff','can_buy','seen_this_season','minutes_down','minutes_up']].copy()
  for arm,p,v in [('fixed',p0,'fixed'),('probability_only',p1,'fixed'),('values_only',p0,'periodic'),('full',p1,'periodic')]:
   z[arm+'_minutes']=blend(p,q[v+'_short_mean'].to_numpy(),q[v+'_long_mean'].to_numpy())
   z[arm+'_play']=1-p[:,0];z[arm+'_60']=p[:,2]
  assert np.allclose(z.fixed_minutes,q.fixed_combined,atol=1e-10,rtol=1e-10)
  assert np.allclose(z.full_minutes,q.periodic_combined,atol=1e-10,rtol=1e-10)
  path=OUT/(season+'_predictions.csv.gz');z.to_csv(path,index=False)
  atomic_json(OUT/(season+'_lock.json'),{'prediction_sha256':sha(path),'source_sha256':sha(src),'outcomes_joined':False})
 labels=pd.read_csv(ROOT/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz')
 matches=pd.read_csv(ROOT/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=KEY+['native_minutes'])
 g=matches.groupby(KEY).native_minutes.agg(['max','count','size']).reset_index();labels=labels.merge(g,on=KEY,validate='one_to_one')
 stats=[];coverage=[];intervals=[];rng=np.random.default_rng(20261015)
 for season in SEASONS:
  path=OUT/(season+'_predictions.csv.gz');assert sha(path)==read(OUT/(season+'_lock.json'))['prediction_sha256']
  z=pd.read_csv(path).merge(labels[KEY+['native_minutes','target_total_points','quality_flagged_for_sensitivity','max','count','size']],on=KEY,how='left',validate='one_to_one')
  mask=z.can_buy&z.native_minutes.notna()&z.target_total_points.notna()&z['count'].eq(z['size'])
  coverage.append({'season':season,'requested':int(z.can_buy.sum()),'known':int(mask.sum()),'unknown':int((z.can_buy&~mask).sum())});z=z[mask].copy()
  for arm in ['fixed','probability_only','values_only','full']:
   z[arm+'_mae']=(z[arm+'_minutes']-z.native_minutes).abs()
   z[arm+'_bias']=z[arm+'_minutes']-z.native_minutes
   z[arm+'_play_brier']=(z[arm+'_play']-z.native_minutes.gt(0))**2
   z[arm+'_60_brier']=(z[arm+'_60']-z['max'].ge(60))**2
  scores=[c for c in z if c.endswith(('_mae','_bias','_brier'))]
  for cohort,q in [('all',z),('minutes_down',z[z.minutes_down]),('minutes_up',z[z.minutes_up]),('no_season_history',z[~z.seen_this_season]),('unflagged',z[z.quality_flagged_for_sensitivity.eq(False)])]:
   for name in scores:stats.append({'season':season,'cohort':cohort,'metric':name,'n':len(q),'value':float(q[name].mean())})
  z[KEY+scores].to_csv(OUT/(season+'_scores.csv.gz'),index=False)
  for reference in ['fixed','full']:
   d=z.assign(delta=z.probability_only_mae-z[reference+'_mae']).groupby('round').delta.agg(['sum','count']).reindex(range(1,39),fill_value=0).to_numpy();draw=[]
   for _ in range(2000):
    start=rng.integers(0,35,size=10);ix=np.concatenate([np.arange(i,i+4) for i in start])[:38];total=d[ix].sum(0);draw.append(total[0]/total[1])
   intervals.append({'season':season,'reference':reference,'mae_difference':float((z.probability_only_mae-z[reference+'_mae']).mean()),'lower':float(np.quantile(draw,.025)),'upper':float(np.quantile(draw,.975))})
  old=pd.read_csv(PRIOR/(season+'_scores.csv.gz')).set_index(KEY);idx=pd.MultiIndex.from_frame(z[KEY]);assert set(old.index)==set(idx)
  for arm,prior in [('fixed','fixed'),('full','periodic')]:
   for suffix,old_suffix in [('mae','combined_mae'),('play_brier','play_brier'),('60_brier','60_brier')]:assert np.allclose(z[arm+'_'+suffix],old.loc[idx,prior+'_'+old_suffix],atol=1e-12)
 m=pd.DataFrame(stats);m.to_csv(OUT/'metrics.csv',index=False);pd.DataFrame(coverage).to_csv(OUT/'coverage.csv',index=False);pd.DataFrame(intervals).to_csv(OUT/'intervals.csv',index=False)
 def value(s,c):return float(m[(m.season==s)&(m.cohort=='all')&(m.metric==c)].value.iloc[0])
 gate=all(value(s,'probability_only_mae')<value(s,'fixed_mae') and all(value(s,'probability_only_'+c)<=value(s,'fixed_'+c) for c in ['play_brier','60_brier']) for s in SEASONS)
 secondary=all(value(s,'probability_only_mae')<value(s,'full_mae') for s in SEASONS)
 verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'complete.json',{'status':'pass','primary_gate':gate,'secondary_beats_full_both_seasons':secondary,'new_fits':0,'manager_promoted':False})
 print('GATES',gate,secondary,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
