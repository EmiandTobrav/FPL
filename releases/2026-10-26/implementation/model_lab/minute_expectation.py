"""Locked mean-target trial: direct squared-error minutes versus frozen mixture."""
from pathlib import Path
import sys,time,hashlib
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from model_lab.common import read,sha,atomic_json,verify_files,runtime
from model_lab.forecast import causal_training
from model_lab.probabilistic import PARAMS
from model_lab.probability_experiment import features
from model_lab.probability_refresh import load_data,REFRESH
ROOT=Path(__file__).resolve().parents[1];PRIOR=ROOT/'reports/probability_refresh_2026_10_15';OUT=ROOT/'reports/minute_expectation_2026_10_15';CACHE=ROOT/'reports/fpl_improvement_2026_10_14/cache'
KEY=['season','round','code'];SEASONS=['2023-24','2024-25'];ID='minute-expectation-20261015-v1'
def prepare():
 OUT.mkdir(exist_ok=True);prior=read(PRIOR/'proposal.json');files=dict(prior['input_hashes'])
 paths=[Path(__file__),ROOT/'overview/FORECAST_OBJECTIVES_V1.json',PRIOR/'proposal.json',PRIOR/'complete.json',PRIOR/'verification.json']
 paths += [PRIOR/(s+suffix) for s in SEASONS for suffix in ['_predictions.csv.gz','_scores.csv.gz']]
 paths += [PRIOR/f'{s}_fit{gw:02d}.json' for s in SEASONS for gw in REFRESH]
 for p in paths:files[str(p.relative_to(ROOT))]=sha(p)
 contract=read(ROOT/'overview/FORECAST_OBJECTIVES_V1.json');active=read(ROOT/'overview/PROJECT.json')['evaluation']['forecast_objective_contract'];assert active['sha256']==sha(ROOT/'overview/FORECAST_OBJECTIVES_V1.json')
 spec={**prior,'id':ID,'candidate_id':'direct_unconditional_minutes_mse_v1','hypothesis':'Direct squared-error regression reduces estimation error of unconditional expected minutes versus the category-weighted conditional-mean model at identical refresh cutoffs.',
 'change':'Replace category-weighted minute expectation with a single HGB squared-error head trained on all eligible rows. Same features, training keys, four-round refreshes and hyperparameters; preserve all archived event probabilities and point forecasts.',
 'related_work':['probability-refresh-20261015-v1','probability-selective-refresh-20261015-v1'],'input_hashes':files,
 'model_parameters':{**PARAMS,'loss':'squared_error','output':'max(0, raw prediction); no upper cap because double rounds may exceed90'},
 'resources':{'new_head_fits':20,'threads':1,'refit_rounds':REFRESH,'no_search':True,'control':'Reuse independently verified frozen periodic mixture; unequal architecture compute disclosed.'},
 'success_criterion':'Strictly lower minute MSE versus full periodic category-mixture control in EACH of2023-24 and2024-25. Associated play/any60 probabilities copied unchanged and must have identical Brier scores. No substitution of MAE/bias or averaged-season gain for this gate.',
 'stop_rule':'Stop on changed input, train-key mismatch, invalid output, temporal violation or resource-cap violation; no automatic retry or hyperparameter search.','maximum_runs':2,
 'evaluation_contract':{'forecast_objectives_id':contract['id'],'target':'Expected total player minutes for next round, including nonappearance and doubles','primary_control':'Archived periodic_combined from probability-refresh-20261015-v1; chosen before this new fit based on disclosed prior exploratory mean diagnostics.','primary_metric':'MSE','reporting':'Per-season MSE and RMSE, equal-season average MSE and sqrt(equal-season MSE); pooled-row MSE labeled secondary.','primary_seasons':SEASONS,'associated_probabilities':'play and any60 carried over unchanged from control; no new probability claims. Point forecasts unchanged.','training':'Same predecessor causal selection, including known point/minute labels for exact comparability; no points used as a feature or training target. Train origin and both label availability clocks strictly before cutoff.','cohorts':'Buyable pool selected at origin; common complete outcome keys. Minutes trend +/-15 with history>=10, no-season-history, positions and unflagged labels are secondary.','uncertainty':'2000 paired four-origin moving-block draws within season,seed20261015; descriptive not an extra gate.','evidence_role':'New candidate on repeatedly inspected development seasons. Not a retrospective promotion of the old full-refresh arm, not an untouched test, not a manager claim.'}}
 atomic_json(OUT/'proposal.json',spec);print('PREPARED')
def run():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json')})
 rows,cols,_=load_data();audits=[]
 for season in SEASONS:
  old=pd.read_csv(PRIOR/(season+'_predictions.csv.gz')).set_index(['round','code']);frames=[]
  for gw in range(1,39):
   folder=CACHE/season/f'gw{gw:02d}';man=read(folder/'manifest.json');at=pd.Timestamp(man['forecast_at'])
   if gw in REFRESH:
    train,_=causal_training(rows,at,1);train=train[train.native_minutes.notna()&train.minute_known.eq(True)&train.available_after_proxy.lt(at)]
    prior=read(PRIOR/f'{season}_fit{gw:02d}.json');keyhash=hashlib.sha256(train[KEY].to_csv(index=False).encode()).hexdigest()
    assert keyhash==prior['training_keys_sha256'] and len(train)==prior['training_rows']
    assert max(train.forecast_at.max(),train.target_h1_available_at.max(),train.available_after_proxy.max())<at
    x=features(train,cols);fitcols=x.columns[x.notna().any()].tolist();start=time.monotonic()
    with threadpool_limits(limits=1):model=HistGradientBoostingRegressor(loss='squared_error',**PARAMS).fit(x[fitcols],train.native_minutes)
    cutoff=at;record={**{k:prior[k] for k in ['season','round','fit_cutoff','training_rows','max_train_origin','max_label_available','training_keys_sha256']},'seconds':time.monotonic()-start,'head_fits':1,'feature_columns':fitcols}
    audits.append(record);assert len(audits)<=20;atomic_json(OUT/f'{season}_fit{gw:02d}.json',record);print('FIT',season,gw,round(record['seconds'],1),flush=True)
   pool=pd.read_csv(folder/'pool.csv.gz');f=pd.read_csv(folder/'features.csv.gz').set_index('code').loc[pool.code].reset_index()
   assert not pool.code.duplicated().any() and (pd.to_datetime(f.forecast_at,utc=True)==at).all()
   with threadpool_limits(limits=1):raw=model.predict(features(f,cols)[fitcols])
   pred=np.maximum(0,raw);assert np.isfinite(pred).all()
   archived=old.loc[pd.MultiIndex.from_arrays([[gw]*len(pool),pool.code])]
   q=pool[['code','can_buy','seen_this_season','position']].copy();q['season']=season;q['round']=gw;q['forecast_at']=str(at);q['fit_cutoff']=str(cutoff);q['candidate_minutes']=pred;q['candidate_raw_minutes']=raw;q['control_minutes']=archived.periodic_combined.to_numpy()
   q['p_play']=1-archived.periodic_minutes_0.to_numpy();q['p_any60']=archived.periodic_minutes_2.to_numpy()
   q['minutes_down']=(f.f_history_count>=10)&(f.f_trend3_vs10_minutes<=-15);q['minutes_up']=(f.f_history_count>=10)&(f.f_trend3_vs10_minutes>=15)
   path=OUT/f'{season}_gw{gw:02d}.csv.gz';q.to_csv(path,index=False);atomic_json(OUT/f'{season}_gw{gw:02d}.lock.json',{'prediction_sha256':sha(path),'fit_cutoff':str(cutoff),'forecast_at':str(at),'outcomes_joined':False});frames.append(q)
  pd.concat(frames,ignore_index=True).to_csv(OUT/(season+'_predictions.csv.gz'),index=False)
 verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'predictions_complete.json',{'fits':audits,'prediction_hashes':{s:sha(OUT/(s+'_predictions.csv.gz')) for s in SEASONS},'new_head_fits':len(audits)})
 print('PREDICTIONS COMPLETE',flush=True)
def score():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);done=read(OUT/'predictions_complete.json');_,_,labels=load_data();quality=pd.read_csv(ROOT/'datasets/fpl_2026_27_best_effort_v1/player_rounds.csv.xz',usecols=KEY+['quality_flagged_for_sensitivity']);labels=labels.merge(quality,on=KEY,validate='one_to_one')
 stats=[];coverage=[];intervals=[];rng=np.random.default_rng(20261015)
 for s in SEASONS:
  path=OUT/(s+'_predictions.csv.gz');assert sha(path)==done['prediction_hashes'][s]
  z=pd.read_csv(path).merge(labels,on=KEY,how='left',validate='one_to_one');mask=z.can_buy&z.native_minutes.notna()&z.target_total_points.notna()&z.minute_known.eq(True)
  coverage.append({'season':s,'requested':int(z.can_buy.sum()),'known':int(mask.sum()),'unknown':int((z.can_buy&~mask).sum())});z=z[mask].copy()
  for arm in ['control','candidate']:
   z[arm+'_error']=z[arm+'_minutes']-z.native_minutes;z[arm+'_squared_error']=z[arm+'_error']**2
  z['play_brier']=(z.p_play-z.native_minutes.gt(0))**2;z['any60_brier']=(z.p_any60-z.any60.astype(float))**2
  cohorts={'all':z,'minutes_down':z[z.minutes_down],'minutes_up':z[z.minutes_up],'no_season_history':z[~z.seen_this_season],'unflagged':z[z.quality_flagged_for_sensitivity.eq(False)]}
  cohorts.update({f'position_{p}':z[z.position.eq(p)] for p in sorted(z.position.unique())})
  for name,q in cohorts.items():
   for arm in ['control','candidate']:
    e=q[arm+'_error'];stats.append({'season':s,'cohort':name,'arm':arm,'n':len(q),'mse':float((e*e).mean()),'rmse':float(np.sqrt((e*e).mean())),'mae':float(e.abs().mean()),'bias':float(e.mean()),'play_brier':float(q.play_brier.mean()),'any60_brier':float(q.any60_brier.mean())})
  z[KEY+['native_minutes','control_error','candidate_error','control_squared_error','candidate_squared_error','play_brier','any60_brier']].to_csv(OUT/(s+'_scores.csv.gz'),index=False)
  old=pd.read_csv(PRIOR/(s+'_scores.csv.gz')).set_index(KEY);idx=pd.MultiIndex.from_frame(z[KEY]);assert set(idx)==set(old.index)
  assert np.allclose(z.play_brier,old.loc[idx,'periodic_play_brier'],atol=1e-12) and np.allclose(z.any60_brier,old.loc[idx,'periodic_60_brier'],atol=1e-12)
  d=z.assign(delta=z.candidate_squared_error-z.control_squared_error).groupby('round').delta.agg(['sum','count']).reindex(range(1,39),fill_value=0).to_numpy();draw=[]
  for _ in range(2000):
   starts=rng.integers(0,35,10);ix=np.concatenate([np.arange(i,i+4) for i in starts])[:38];tot=d[ix].sum(0);draw.append(tot[0]/tot[1])
  intervals.append({'season':s,'mse_difference':float((z.candidate_squared_error-z.control_squared_error).mean()),'lower':float(np.quantile(draw,.025)),'upper':float(np.quantile(draw,.975))})
 m=pd.DataFrame(stats);m.to_csv(OUT/'metrics.csv',index=False);pd.DataFrame(coverage).to_csv(OUT/'coverage.csv',index=False);pd.DataFrame(intervals).to_csv(OUT/'intervals.csv',index=False)
 primary=m[m.cohort.eq('all')];pivot=primary.pivot(index='season',columns='arm',values='mse');passed=bool((pivot.candidate<pivot.control).all());summary=[]
 for arm,q in primary.groupby('arm'):
  avg=float(q.mse.mean());summary.append({'arm':arm,'equal_season_mse':avg,'sqrt_equal_season_mse':float(np.sqrt(avg)),'secondary_pooled_row_mse':float(np.average(q.mse,weights=q.n))})
 atomic_json(OUT/'complete.json',{'status':'pass','research_gate_passed':passed,'associated_probability_scores_identical':True,'seasons':pivot.reset_index().to_dict('records'),'summary':summary,'manager_promoted':False});print('GATE',passed,flush=True)
if __name__=='__main__':globals()[sys.argv[1]]()
