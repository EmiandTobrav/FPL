"""Calendar-conditioned minute means; frozen probabilities and paired controls."""
from pathlib import Path
import sys,time,hashlib,importlib.util
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from threadpoolctl import threadpool_limits
from model_lab.common import read,sha,atomic_json,verify_files,runtime
from model_lab.forecast import causal_training,pipeline_modules
from model_lab.probabilistic import PARAMS,minute_class
from model_lab.probability_experiment import features
from model_lab.probability_refresh import load_data,REFRESH
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'reports/minute_calendar_2026_10_16';PRIOR=ROOT/'reports/probability_refresh_2026_10_15';CACHE=ROOT/'reports/fpl_improvement_2026_10_14/cache'
KEY=['season','round','code'];SEASONS=['2023-24','2024-25'];ID='minute-calendar-20261016-v1';EXTRA=['planned_fixture_count','calendar_known']
class Calendar:
 def __init__(self):
  path=ROOT/'reports/fpl_simulator_2026_10_13/benchmark_forecaster.py';sp=importlib.util.spec_from_file_location('_calendar_frozen_benchmark',path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m)
  self.b=m.BenchmarkForecaster.__new__(m.BenchmarkForecaster);self.b.current=ROOT/'FPL_training_dataset/research/current';self.b.commits=read(self.b.current/'calendar_audit/source_commits.json');self.b.team_codes={};self.names={};self.dependencies={str(path.relative_to(ROOT)):sha(path)}
  p=self.b.current/'calendar_audit/source_commits.json';self.dependencies[str(p.relative_to(ROOT))]=sha(p)
  for s in ['2019-20','2020-21','2021-22','2022-23','2023-24','2024-25']:
   p=self.b.current/f'project/data/{s}_teams.csv.gz';t=pd.read_csv(p);self.b.team_codes[s]=t.set_index('id').code;self.names[s]=t.set_index('name').code.to_dict();self.dependencies[str(p.relative_to(ROOT))]=sha(p)
  self.audit=[]
 def attach(self,f,club_column,kind):
  assert set(KEY+['forecast_at',club_column]).issubset(f.columns)
  frames=[]
  for (s,gw,at),q in f.groupby(['season','round','forecast_at'],sort=False):
   at=pd.Timestamp(at);calendar,a=self.b._calendar(s,at);mapping=dict(self.names[s]);mapping['Ipswich Town']=mapping.get('Ipswich')
   clubs=q[club_column].map(mapping).fillna(pd.to_numeric(q[club_column],errors='coerce'));valid=clubs.isin(self.b.team_codes[s].values)
   v=q[KEY].copy();v['planned_fixture_count']=1;v['calendar_known']=0
   if calendar is not None:
    assert pd.Timestamp(a['calendar_time'])<at
    p=self.b.current/f"calendar_audit/portable/{s}_{a['calendar_sha']}.csv";assert sha(p)==a['calendar_file_sha256'];self.dependencies[str(p.relative_to(ROOT))]=sha(p)
    c=calendar[calendar.event.eq(gw)];counts=pd.concat([c.home,c.away]).value_counts()
    v.loc[valid,'planned_fixture_count']=clubs[valid].map(counts).fillna(0).astype(int);v.loc[valid,'calendar_known']=1
   v['calendar_age_days']=a.get('calendar_age_days');frames.append(v)
   self.audit.append(dict(kind=kind,season=s,round=int(gw),forecast_at=str(at),rows=len(q),known=int(v.calendar_known.sum()),unmapped_clubs=int((~valid).sum()),zero=int((v.calendar_known.eq(1)&v.planned_fixture_count.eq(0)).sum()),double=int((v.calendar_known.eq(1)&v.planned_fixture_count.ge(2)).sum()),**a))
  return pd.concat(frames,ignore_index=True)
def context():
 OUT.mkdir(exist_ok=True);assert not (OUT/'started.json').exists()
 loader,_=pipeline_modules();rows,_=loader.load_rows();f=rows[rows.season.le('2024-25')][KEY+['forecast_at','f_club_last_known']].copy()
 cal=Calendar();v=cal.attach(f,'f_club_last_known','training');assert len(v)==len(f) and not v.duplicated(KEY).any();v.to_csv(OUT/'training_calendar.csv.gz',index=False)
 evaluation=[]
 for s in SEASONS:
  for gw in range(1,39):
   folder=CACHE/s/f'gw{gw:02d}';pool=pd.read_csv(folder/'pool.csv.gz');man=read(folder/'manifest.json');assert sha(folder/'pool.csv.gz')==man['files']['pool.csv.gz']
   assert (pd.to_datetime(pool.club_available_at,utc=True)<pd.Timestamp(man['forecast_at'])).all()
   f=pool[['code','club','forecast_at']].copy();f['season']=s;f['round']=gw;v=cal.attach(f,'club','evaluation')
   archived=read(folder/'minutes_hurdle_fixture_v1.json');assert sha(folder/'minutes_hurdle_fixture_v1.json')==man['files']['minutes_hurdle_fixture_v1.json']
   counts=pd.Series([a[0] for a in archived['match_counts_by_player']],index=archived['player_codes'])
   assert np.array_equal(v.planned_fixture_count,counts.loc[v.code].values),'Archived count parity'
   evaluation.append(v)
 pd.concat(evaluation,ignore_index=True).to_csv(OUT/'evaluation_calendar.csv.gz',index=False)
 atomic_json(OUT/'calendar_audit.json',{'origins':cal.audit,'dependencies':cal.dependencies,'labels_used_for_calendar':False,'preseason_extension':False,'current_stale_allowed':True,'eval_archived_count_parity':True,'training_club_source':'f_club_last_known from frozen causal pipeline, seasonal name-to-identity map; unmapped or promoted/out-of-season club is unknown, never inferred from realized match','evaluation_club_source':'frozen as-of pool.club; club_available_at strictly before origin'})
 print('CONTEXT origins',len(cal.audit),flush=True)
def prepare():
 old=read(ROOT/'reports/minute_expectation_2026_10_15/proposal.json');files=dict(old['input_hashes']);audit=read(OUT/'calendar_audit.json');files.update(audit['dependencies'])
 paths=[Path(__file__),OUT/'training_calendar.csv.gz',OUT/'evaluation_calendar.csv.gz',OUT/'calendar_audit.json',OUT/'verify_context.py',OUT/'context_verification.json',OUT/'training_calendar_coverage.csv',ROOT/'reports/minute_error_diagnosis_2026_10_15/RESULTATER.md',ROOT/'reports/minute_error_diagnosis_2026_10_15/NESTE_FORSAK.md']
 for s in SEASONS:
  for gw in range(1,39):
   for name in ['pool.csv.gz','features.csv.gz','minutes_hurdle_fixture_v1.json','manifest.json']:paths.append(CACHE/s/f'gw{gw:02d}'/name)
 for p in paths:files[str(p.relative_to(ROOT))]=sha(p)
 spec={**old,'id':ID,'candidate_id':'calendar_conditional_minutes_fixed_probabilities_v1','hypothesis':'As-of planned fixture count improves full expected round-minute MSE through conditional minute means with category probabilities fixed.','change':'Only add planned_fixture_count and calendar_known to the two conditional HGB regressors; regenerate paired old regressors and reuse frozen category probabilities.','related_work':['probability-refresh-20261015-v1','minute-expectation-20261015-v1','minute-joint-calibration-20261015-v1','legacy-calendar_counts','campaign1-minutes_hurdle_fixture_v1'],'input_hashes':files,'seasons':SEASONS,'model_parameters':{**PARAMS,'loss':'squared_error','extra_features':EXTRA,'output':'same max(0,raw) per conditional head as control; no upper cap; no candidate-only floor'},'resources':{'maximum_head_fits':80,'paired_control_head_fits':40,'candidate_head_fits':40,'probability_head_fits':0,'threads':1,'refresh':REFRESH,'no_search':True},'maximum_runs':1,'stop_rule':'Stop on hash/time/key mismatch, failed control parity, changed probabilities, invalid output or expectation support violation; document cause before interpretation. No outcome-directed retry.','evaluation_contract':{**old['evaluation_contract'],'primary_control':'Regenerated conditional means must match archived periodic_short_mean/long_mean and periodic_combined at all76 origins at atol=rtol=1e-10.','training':'Identical predecessor causal rows/order/labels and cadence; historical calendar built from feature-only origins before outcome eligibility. Unknown count=1,known=0. Current stale archived schedule allowed as in fixture model; no preseason extension.','support':'Both arms nonnegative and E[minutes]>=60*p(any60) within1e-9; stop if violated, no new clipping.','diagnosis_design':'reports/minute_error_diagnosis_2026_10_15/NESTE_FORSAK.md','cohorts':'all, archived1, archived2plus, unknown_calendar, minutes_up/down, no_season_history, unflagged and flagged. Planned blank rows remain excluded when labels unknown.'}}
 atomic_json(OUT/'proposal.json',spec);print('PREPARED',len(files))
def run():
 spec=read(OUT/'proposal.json');verify_files(ROOT,spec['input_hashes']);assert not (OUT/'started.json').exists(),'No repeat run';atomic_json(OUT/'started.json',{'runtime':runtime(),'proposal_sha256':sha(OUT/'proposal.json')})
 rows,cols,_=load_data();c=pd.read_csv(OUT/'training_calendar.csv.gz');rows=rows[rows.season.le('2024-25')].merge(c,on=KEY,validate='one_to_one',how='left',sort=False);assert rows[EXTRA].notna().all().all()
 ec=pd.read_csv(OUT/'evaluation_calendar.csv.gz');audits=[];maxdiff=0.;headfits=0
 for s in SEASONS:
  old=pd.read_csv(PRIOR/(s+'_predictions.csv.gz')).set_index(['round','code']);frames=[]
  for gw in range(1,39):
   folder=CACHE/s/f'gw{gw:02d}';at=pd.Timestamp(read(folder/'manifest.json')['forecast_at'])
   if gw in REFRESH:
    train,_=causal_training(rows,at,1);train=train[train.native_minutes.notna()&train.minute_known.eq(True)&train.available_after_proxy.lt(at)];prior=read(PRIOR/f'{s}_fit{gw:02d}.json');keyhash=hashlib.sha256(train[KEY].to_csv(index=False).encode()).hexdigest();assert keyhash==prior['training_keys_sha256'];assert len(train)==prior['training_rows'];assert max(train.forecast_at.max(),train.target_h1_available_at.max(),train.available_after_proxy.max())<at
    x=features(train,cols);xc=x.copy()
    for name in EXTRA:xc[name]=train[name].to_numpy(float)
    cat=minute_class(train.native_minutes,train.any60);models={};start=time.monotonic()
    with threadpool_limits(limits=1):
     for arm,xx in [('control',x),('candidate',xc)]:
      models[arm]=[]
      for k in [1,2]:
       used=xx.columns[xx[cat==k].notna().any()].tolist();m=HistGradientBoostingRegressor(**PARAMS).fit(xx.loc[cat==k,used],train.native_minutes.to_numpy()[cat==k]);models[arm].append((used,m));headfits+=1;assert headfits<=80
    rec={**prior,'head_fits':4,'seconds':time.monotonic()-start,'training_calendar_known':int(train.calendar_known.sum()),'training_calendar_double':int((train.calendar_known.eq(1)&train.planned_fixture_count.ge(2)).sum())};audits.append(rec);atomic_json(OUT/f'{s}_fit{gw:02d}.json',rec);cutoff=at;print('FIT',s,gw,round(rec['seconds'],1),flush=True)
   pool=pd.read_csv(folder/'pool.csv.gz');f=pd.read_csv(folder/'features.csv.gz').set_index('code').loc[pool.code].reset_index();assert (pd.to_datetime(f.forecast_at,utc=True)==at).all()
   cc=ec[ec.season.eq(s)&ec['round'].eq(gw)].set_index('code').loc[pool.code];x=features(f,cols);xc=x.copy()
   for name in EXTRA:xc[name]=cc[name].to_numpy(float)
   a=old.loc[pd.MultiIndex.from_arrays([[gw]*len(pool),pool.code])];q=a.reset_index();q['position']=pool.position.to_numpy();q['fit_cutoff']=str(cutoff)
   for name in EXTRA+['calendar_age_days']:q[name]=cc[name].to_numpy()
   with threadpool_limits(limits=1):
    for arm,xx in [('control',x),('candidate',xc)]:
     means=[np.maximum(0,m.predict(xx[used])) for used,m in models[arm]]
     for name,val in zip(['short_mean','long_mean'],means):q[arm+'_'+name]=val
     q[arm+'_minutes']=q.periodic_minutes_1*means[0]+q.periodic_minutes_2*means[1]
     assert np.isfinite(q[arm+'_minutes']).all();assert (q[arm+'_minutes']+1e-9>=60*q.periodic_minutes_2).all(),'Expectation support violation'
   for new,orig in [('control_short_mean','periodic_short_mean'),('control_long_mean','periodic_long_mean'),('control_minutes','periodic_combined')]:
    d=np.abs(q[new]-q[orig]);maxdiff=max(maxdiff,float(d.max()));assert np.allclose(q[new],q[orig],atol=1e-10,rtol=1e-10),'Control parity failure'
   q['p_play']=1-q.periodic_minutes_0;q['p_any60']=q.periodic_minutes_2
   path=OUT/f'{s}_gw{gw:02d}.csv.gz';q.to_csv(path,index=False);atomic_json(OUT/f'{s}_gw{gw:02d}.lock.json',{'prediction_sha256':sha(path),'forecast_at':str(at),'fit_cutoff':str(cutoff),'current_outcomes_joined':False});frames.append(q)
  pd.concat(frames,ignore_index=True).to_csv(OUT/(s+'_predictions.csv.gz'),index=False)
 verify_files(ROOT,spec['input_hashes']);atomic_json(OUT/'predictions_complete.json',{'fits':audits,'prediction_hashes':{s:sha(OUT/(s+'_predictions.csv.gz')) for s in SEASONS},'new_head_fits':headfits,'control_max_absolute_difference':maxdiff,'probabilities_frozen':True});print('PREDICTIONS COMPLETE',headfits,maxdiff,flush=True)

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
  cohorts.update({'archived1':z[z.calendar_known.eq(1)&z.planned_fixture_count.eq(1)],'archived2plus':z[z.calendar_known.eq(1)&z.planned_fixture_count.ge(2)],'unknown_calendar':z[z.calendar_known.eq(0)],'flagged':z[z.quality_flagged_for_sensitivity.eq(True)]})
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
