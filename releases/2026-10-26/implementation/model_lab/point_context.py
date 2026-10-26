"""Locked factorial calendar/point experiment with fixed causal minute forecasts."""
from pathlib import Path
import copy,time,json
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits
from model_lab import duration_to_points as prev
from model_lab.common import read,sha,atomic_json,verify_files,runtime
R=prev.ROOT;P=R/'reports/point_context_2026_10_16';KEY=prev.KEY
CAL=R/'reports/calendar_dataset_2026_10_16';NEW=R/'reports/calendar_reconstruction_2026_10_16'
BASE=prev.ARMS['both'];CF=['ctx_count','ctx_home','ctx_away','ctx_known','ctx_age','ctx_unassigned'];ST=['ctx_own_gf6','ctx_own_ga6','ctx_opp_gf6','ctx_opp_ga6']
ARMS=['base','old_strict','repaired_strict','old_carry','repaired_carry','full'];PAIRS=[('full','base'),('old_carry','old_strict'),('repaired_carry','repaired_strict'),('repaired_strict','old_strict'),('repaired_carry','old_carry'),('full','repaired_carry')]
def context():
 deps=dict(read(prev.OUT/'proposal.json')['input_hashes']);deps[str(prev.OUT.relative_to(R)/'predictions.csv.gz')]=sha(prev.OUT/'predictions.csv.gz')
 old=pd.read_csv(CAL/'fixture_snapshots.csv.gz');new=pd.read_csv(NEW/'fixture_snapshots.csv.gz');players=pd.read_csv(CAL/'player_context.csv.gz')[KEY+['forecast_at','club_code']];teams=pd.read_csv(CAL/'team_context.csv.gz')
 mp=R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz';h=pd.read_csv(mp,usecols=['season','fixture','club_code','opponent_club_code','was_home','team_h_score','team_a_score','fixture_kickoff_time']).drop_duplicates(['season','fixture','club_code']);h['available']=pd.to_datetime(h.fixture_kickoff_time,utc=True)+pd.Timedelta(hours=24);h['gf']=np.where(h.was_home,h.team_h_score,h.team_a_score);h['ga']=np.where(h.was_home,h.team_a_score,h.team_h_score)
 frames=[];audits=[]
 for (s,gw),q in players.groupby(['season','round'],sort=True):
  at=pd.Timestamp(q.forecast_at.iloc[0]);hist=h[h.available.lt(at)&h.gf.notna()&h.ga.notna()].sort_values(['available','season','fixture']).groupby('club_code').tail(6);strength=hist.groupby('club_code')[['gf','ga']].mean();audit=dict(season=s,round=int(gw),forecast_at=str(at),latest_strength_available=str(hist.available.max()));assert hist.available.max()<at;audits.append(audit)
  tc=teams[teams.season.eq(s)&teams['round'].eq(gw)];features=[]
  for arm in ARMS[1:]:
   schedule=new[new['round'].eq(gw)] if s=='2025-26' and arm in ['repaired_strict','repaired_carry','full'] else old[old.season.eq(s)&old['round'].eq(gw)]
   assert pd.to_datetime(schedule.source_time,utc=True).lt(at).all()
   if 'event_evidence_at' in schedule:assert pd.to_datetime(schedule.event_evidence_at,utc=True).lt(at).all()
   for row in tc.itertuples():
    g=schedule[schedule.event.eq(gw)&(schedule.home_code.eq(row.club_code)|schedule.away_code.eq(row.club_code))];unassigned=int((schedule.event.isna()&(schedule.home_code.eq(row.club_code)|schedule.away_code.eq(row.club_code))).sum());known=arm not in ['old_strict','repaired_strict'] or bool(row.calendar_usable and unassigned==0)
    home=int(g.home_code.eq(row.club_code).sum());opps=[int(r.away_code if r.home_code==row.club_code else r.home_code) for r in g.itertuples()];st=strength.reindex(opps)
    v=dict(club_code=row.club_code,arm=arm,ctx_count=len(g) if known else np.nan,ctx_home=home if known else np.nan,ctx_away=len(g)-home if known else np.nan,ctx_known=int(known),ctx_age=row.snapshot_age_days,ctx_unassigned=unassigned,ctx_own_gf6=strength.gf.get(row.club_code,np.nan),ctx_own_ga6=strength.ga.get(row.club_code,np.nan),ctx_opp_gf6=st.gf.mean() if known and st.gf.notna().all() else np.nan,ctx_opp_ga6=st.ga.mean() if known and st.ga.notna().all() else np.nan);features.append(v)
  for arm in ARMS[1:]:
   z=pd.DataFrame(features).query('arm==@arm').drop(columns='arm');v=q.merge(z,on='club_code',how='left',validate='many_to_one');v['arm']=arm;frames.append(v)
 pd.concat(frames,ignore_index=True).to_csv(P/'context.csv.gz',index=False)
 for path in [Path(__file__),CAL/'fixture_snapshots.csv.gz',CAL/'player_context.csv.gz',CAL/'team_context.csv.gz',NEW/'fixture_snapshots.csv.gz',NEW/'feature_lock.json',NEW/'amendments.json',mp,P/'context.csv.gz',R/'reports/point_candidate_diagnosis_2026_10_16_attempt2/predeadline_context.csv.gz'] :deps[str(path.relative_to(R))]=sha(path)
 atomic_json(P/'context_lock.json',dict(dependencies=deps,audits=audits,feature_outcomes_used=False,strength_rule='last6 club matches with kickoff+24h strictly before each historical origin; proxy retained'))
 spec=dict(id='point-context-20261016-v1',candidate='full',arms=ARMS,contrasts=PAIRS,features=dict(base=BASE,calendar=CF,strength=ST),input_hashes=deps,primary='Expected harmonized points MSE,2025/26 development; strict improvement full vs base on all eligible rows AND frozen team candidate list. No tolerance. Brier identical; all original gates unchanged.',secondary='Factorial calendar effects: carry vs strict within each repair state; repair vs old within each availability policy; full vs repaired carry isolates strength. No posthoc arm selection.',training='Same causal saved minute forecasts, exact rows and preprocessing scope as duration-to-points. All inputs at historical row origin; all labels strictly before fit. Same per-GW CatBoost200 depth5 rate.05 seed20261013 thread1. Negative targets retained; absent mean unchanged.',calendar_policy='Strict uses previous calendar_usable (age<=14 and target kickoff valid) and no unassigned club fixtures; repaired strict retains baseline freshness screen. Carry keeps scheduled count regardless of age; age and unassigned visible. Both policies applied identically across all113 training/evaluation origins. Only2025/26 has new official amendments.',uncertainty='2000 paired4-round moving blocks seed20261015, descriptive; multiple comparisons and inspected period acknowledged.',limits=dict(point_fits=228,minute_fits=0,tuning=False),stop='Stop on causal/hash/key/control-parity mismatch; no result-guided reruns.',source_limitations='Git and publication-date proxies; carry-forward is a policy assumption. Strength uses kickoff+24h availability proxy, no historical receipt. Exact future kickoff not used.')
 atomic_json(P/'proposal.json',spec);print('LOCKED',len(deps),flush=True)
def run():
 spec=read(P/'proposal.json');verify_files(R,spec['input_hashes']);assert not (P/'started.json').exists();atomic_json(P/'started.json',dict(runtime=runtime(),proposal_sha256=sha(P/'proposal.json')))
 mod=prev.adapter();a=mod.CausalCandidateForecaster(R,thread_count=1);schema=a.schema;names=schema['extended_features'];data=prev.labeled_inputs();ctx=pd.read_csv(P/'context.csv.gz');expanded={arm:data.merge(ctx[ctx.arm.eq(arm)][KEY+CF+ST],on=KEY,how='left',validate='one_to_one') for arm in ARMS[1:]};expanded['base']=data
 retained=pd.read_csv(prev.OUT/'predictions.csv.gz').set_index(KEY);frames=[]
 for gw in range(1,39):
  at=pd.Timestamp(read(prev.folder('2025-26',gw)/'manifest.json')['forecast_at']);tr=prev.training(data,at);played=tr.native_minutes.gt(0).to_numpy();y=tr.target_total_points.to_numpy(float);absent=float(y[~played].mean());test=data[data.season.eq('2025-26')&data['round'].eq(gw)];q=test[KEY+['forecast_at','can_buy','seen_this_season','position','candidate_p0','candidate_p1','candidate_p2','candidate_minutes']].copy();q['retained_points']=retained.loc[pd.MultiIndex.from_frame(q[KEY]),'both_points'].to_numpy();start=time.monotonic()
  for arm in ARMS:
   v=expanded[arm];t=prev.training(v,at);f=v[v.season.eq('2025-26')&v['round'].eq(gw)];assert prev.keyhash(t)==prev.keyhash(tr);assert prev.keyhash(f)==prev.keyhash(test);extra=BASE+([] if arm=='base' else CF)+(ST if arm=='full' else []);sc=copy.deepcopy(schema);sc['extended_features']=names+extra;pipe=a._pipeline.make_pipeline(sc,'catboost','extended',seed=mod.SEED,model_params={'thread_count':1});prep,reg=pipe.named_steps['prepare'],pipe.named_steps['model'];Z=prep.fit_transform(t[names+extra])
   with threadpool_limits(limits=1):reg.fit(Z.loc[played],y[played],sample_weight=np.ones(int(played.sum())));conditional=reg.predict(prep.transform(f[names+extra]))
   q[arm+'_points']=(1-q.candidate_p0)*conditional+q.candidate_p0*absent;assert np.isfinite(q[arm+'_points']).all()
   if arm=='base':assert np.allclose(q.base_points,q.retained_points,rtol=1e-12,atol=1e-12),'control parity'
  path=P/f'gw{gw:02d}.csv.gz';q.to_csv(path,index=False);atomic_json(P/f'gw{gw:02d}.lock.json',dict(sha256=sha(path),training_keys_sha256=prev.keyhash(tr),training_rows=len(tr),played_rows=int(played.sum()),latest_training_origin=str(tr.forecast_at.max()),latest_point_label=str(tr.target_h1_available_at.max()),latest_minute_label=str(tr.available_after_proxy.max()),fit_cutoff=str(at),minute_fits=0,arms=ARMS));frames.append(q);print('GW',gw,'seconds',round(time.monotonic()-start,1),flush=True)
 pd.concat(frames,ignore_index=True).to_csv(P/'predictions.csv.gz',index=False);verify_files(R,spec['input_hashes']);atomic_json(P/'predictions_complete.json',dict(sha256=sha(P/'predictions.csv.gz'),point_fits=228,minute_fits=0))
def score():
 verify_files(R,read(P/'proposal.json')['input_hashes']);assert sha(P/'predictions.csv.gz')==read(P/'predictions_complete.json')['sha256'];q=pd.read_csv(P/'predictions.csv.gz');_,_,lab=prev.load_data();z=q.merge(lab,on=KEY,how='left',validate='one_to_one');c=pd.read_csv(R/'reports/point_candidate_diagnosis_2026_10_16_attempt2/predeadline_context.csv.gz')[KEY+['team_candidates']];z=z.merge(c,on=KEY,validate='one_to_one');z=z[z.can_buy&z.native_minutes.notna()&z.target_total_points.notna()&z.minute_known.eq(True)].copy();prior=pd.read_csv(prev.OUT/'scores.csv.gz');assert set(map(tuple,z[KEY].to_numpy()))==set(map(tuple,prior[KEY].to_numpy()));assert len(z)==29144 and z.team_candidates.sum()==2070
 for k in ['candidate_p0','candidate_p1','candidate_p2','candidate_minutes']:assert np.array_equal(z.set_index(KEY)[k].sort_index(),prior.set_index(KEY)[k].sort_index())
 stats=[];intervals=[]
 for arm in ARMS:z[arm+'_se']=(z[arm+'_points']-z.target_total_points)**2
 for cohort,g in [('all',z),('team_candidates',z[z.team_candidates])]:
  for arm in ARMS:
   e=g[arm+'_points']-g.target_total_points;stats.append(dict(cohort=cohort,arm=arm,n=len(g),mse=float((e*e).mean()),mae=float(e.abs().mean()),bias=float(e.mean())))
  rng=np.random.default_rng(20261015);ds=[g.assign(delta=g[a+'_se']-g[b+'_se']).groupby('round').delta.agg(['sum','count']).reindex(range(1,39),fill_value=0).to_numpy() for a,b in PAIRS];draw=[]
  for _ in range(2000):
   ix=np.concatenate([np.arange(i,i+4) for i in rng.integers(0,35,10)])[:38];draw.append([d[ix,0].sum()/d[ix,1].sum() for d in ds])
  draw=np.array(draw)
  for i,(a,b) in enumerate(PAIRS):intervals.append(dict(cohort=cohort,candidate=a,control=b,difference=float((g[a+'_se']-g[b+'_se']).mean()),lower=float(np.quantile(draw[:,i],.025)),upper=float(np.quantile(draw[:,i],.975))))
 m=pd.DataFrame(stats);m.to_csv(P/'metrics.csv',index=False);pd.DataFrame(intervals).to_csv(P/'intervals.csv',index=False);z.to_csv(P/'scores.csv.gz',index=False);gates={cohort:bool(m.query('cohort==@cohort and arm=="full"').mse.iloc[0]<m.query('cohort==@cohort and arm=="base"').mse.iloc[0]) for cohort in ['all','team_candidates']};gates['fixed_minutes_probabilities']=True;atomic_json(P/'complete.json',dict(gates=gates,passed=all(gates.values()),model_fits=228,minute_fits=0,production_promoted=False,intervals=intervals));print(m.to_string(index=False));print(gates)
if __name__=='__main__':import sys;globals()[sys.argv[1]]()
