"""Player-level frozen exposure, component-error and legal single-swap diagnosis."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,json,itertools
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import pandas as pd,numpy as np
from model_lab.common import atomic_json,sha,verify_files
from scripts import matched_availability_retest_v8 as guard
P=R/'reports/player_decision_diagnosis_2026_10_26_v2';OLD=R/'reports/current_model_loss_diagnosis_2026_10_26_v3';B=R/'reports/base_cadence_2026_10_26';E=R/'reports/xg_adaptation_2026_10_26_v2';D=R/'datasets/fpl_common_training_v5';S=['2023-24','2024-25','2025-26'];K=['season','round','code'];read=lambda p:json.loads(Path(p).read_text())
def setup():
 P.mkdir();parent=read(OLD/'proposal.json');deps=dict(parent['input_hashes']);paths=[Path(__file__),OLD/'players.csv',OLD/'rounds.csv',OLD/'hold.csv',OLD/'transfers.csv',OLD/'verification.json',D/'pool_features.pkl',guard.P/'calendar.csv',R/'FPL_training_dataset/research/current/calendar_audit/source_commits.json',R/'reports/calendar_dataset_2026_10_16/old_selection.json']+[B/'standard'/f'base_{s}.pkl' for s in S]+list((R/'datasets/fpl_all_competitions_context_v1/raw').glob('calendar_commits_*.json'))
 cal=pd.read_csv(guard.P/'calendar.csv');paths+=list({R/f for f in cal.file});deps.update({str(f.relative_to(R)):sha(f) for f in paths});spec=dict(parent);spec.update(id='current-player-decision-diagnosis-20261026-v2',candidate_id='current_player_errors_components_calendar_legal_swaps_v2',hypothesis='Technical v2 retains existing source-qualified blank zeros instead of treating absence of a native match row as unknown; no analytical scope or outputs tuned. Trace2025/26 failures to specific players and legal local lineup/transfer/captain choices, distinguishing base attack, appearance, residual, minutes and calibration from missing fixture exposure.',change='Read-only forensic extension of existing114 current model episodes. Reproduce native components and actual fixture counts, compare all3 calendars and available prior fixture snapshots; inspect already observed player histories. Enumerate legal single bench/start swaps, no forecast fit, source refresh, external order or new season policy. Actual fixture counts and outcomes are hindsight diagnosis only; never repair frozen forecasts with them.',related_work=['current-player-decision-diagnosis-20261026-v1',parent['id'],'component-base-cadence-20261026-v1'],resources=dict(new_model_fits=0,new_policy_optimizer_calls=0,existing_decisions=114,local_single_swaps_max60per_round=True),input_hashes=deps,success_criterion='Native point/component/minute totals match selected outcomes, component plus calibration errors sum exactly to final point error, all cases preserve availability and formations, no production/input changes.',stop_rule='Stop on mismatched keys/actual points; unknown source exposure remains unknown. No automatic model change, score-driven scenario selection or posterior replacement of calendar inputs.',maximum_runs=1)
 atomic_json(P/'proposal.json',spec)
def run():
 verify_files(R,read(P/'proposal.json')['input_hashes']);poolfeatures=pd.read_pickle(D/'pool_features.pkl');av=pd.read_csv(guard.P/'availability.csv.gz');bases=pd.concat([pd.read_pickle(B/'standard'/f'base_{s}.pkl') for s in S]);pred=pd.read_csv(B/'standard.csv.gz');raw=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=K+['fixture','position','native_goals_scored','native_assists','native_minutes','target_total_points']);raw=raw[raw.season.isin(S)].copy();raw['actual_attack']=raw.native_goals_scored*raw.position.map(dict(GK=10,DEF=6,MID=5,FWD=4))+3*raw.native_assists;raw['actual_appearance']=2*raw.native_minutes.ge(60)+(raw.native_minutes.gt(0)&raw.native_minutes.lt(60));raw['actual_residual']=raw.target_total_points-raw.actual_attack-raw.actual_appearance
 truth=raw.groupby(K).agg(actual_points=('target_total_points',lambda z:z.sum(min_count=1)),actual_minutes=('native_minutes',lambda z:z.sum(min_count=1)),actual_attack=('actual_attack',lambda z:z.sum(min_count=1)),actual_appearance=('actual_appearance',lambda z:z.sum(min_count=1)),actual_residual=('actual_residual',lambda z:z.sum(min_count=1)),actual_fixtures=('fixture','nunique')).reset_index()
 # Known blank outcomes have no native match row. Preserve their existing
 # qualified zero, with source-hash verification; never fill unknown outcomes.
 known_blanks=[]
 for season in S:
  for gw in range(1,39):
   saved=read(E/'manager'/f'{season}_recent_only'/f'gw{gw:02d}.settlement.json')
   for row in saved['outcomes']:
    if not row.get('blank_derived'):continue
    assert row['known'] and row['points_known'] and row['points']==0 and row['minutes']==0 and not row['appeared']
    assert sha(Path(row['blank_fixtures_source']))==row['blank_fixtures_sha256']
    known_blanks.append(dict(season=season,round=gw,code=row['code'],actual_points=0.,actual_minutes=0.,actual_attack=0.,actual_appearance=0.,actual_residual=0.,actual_fixtures=0))
 blanks=pd.DataFrame(known_blanks);existing=pd.MultiIndex.from_frame(truth[K]);blanks=blanks[~pd.MultiIndex.from_frame(blanks[K]).isin(existing)];truth=pd.concat([truth,blanks],ignore_index=True);assert not truth.duplicated(K).any();blanks.to_csv(P/'verified_selected_blank_outcomes.csv',index=False)
 allrows=poolfeatures[poolfeatures.season.isin(S)].merge(av[K+['model_can_buy']],on=K,validate='one_to_one').merge(truth,on=K,how='left',validate='one_to_one').merge(bases.drop(columns='forecast_at'),on=K,validate='one_to_one').merge(pred[K+['xp_0']],on=K,validate='one_to_one');allrows['forecast_error']=allrows.xp_0-allrows.actual_points;allrows['calibration_adjustment']=allrows.xp_0-allrows.component_p1
 for name in ['attack','appearance','residual']:allrows[f'{name}_error']=allrows[f'base_{name}1']-allrows[f'actual_{name}']
 valid=allrows.actual_points.notna();np.testing.assert_allclose(allrows.loc[valid,'forecast_error'],allrows.loc[valid,['attack_error','appearance_error','residual_error','calibration_adjustment']].sum(axis=1),atol=1e-9,rtol=1e-9);allrows['minute_error']=allrows.component_m1-allrows.actual_minutes;allrows['exposure_over']=allrows.u_count_0.notna()&allrows.actual_fixtures.notna()&allrows.u_count_0.gt(allrows.actual_fixtures);allrows['exposure_under']=allrows.u_count_0.notna()&allrows.actual_fixtures.notna()&allrows.u_count_0.lt(allrows.actual_fixtures);allrows['actual_double']=allrows.actual_fixtures.gt(1);allrows['actual_minutes_per_fixture']=allrows.actual_minutes/allrows.actual_fixtures;allrows['missing_exposure_minutes']=(allrows.actual_fixtures-allrows.u_count_0)*allrows.actual_minutes_per_fixture;allrows['within_exposure_minutes_error']=allrows.u_count_0*allrows.actual_minutes_per_fixture-allrows.component_m1
 selected=pd.read_csv(OLD/'players.csv');extra=[c for c in allrows if c not in selected.columns or c in K];z=selected.merge(allrows[extra],on=K,how='left',validate='one_to_one');np.testing.assert_allclose(z.points,z.actual_points,atol=1e-9,rtol=1e-9);assert len(z)==1710
 sums=['xp','points','forecast_error','actual_minutes','component_m1','minute_error','attack_error','appearance_error','residual_error','calibration_adjustment'];groups=z[z.starter].groupby(['season','code','name']);summary=groups[sums].sum();summary['starts']=groups.size();summary['nonappearances']=groups.appeared.apply(lambda v:int((~v).sum()));summary.reset_index().to_csv(P/'starter_player_errors.csv',index=False);z.to_csv(P/'player_round_details.csv',index=False)
 features=['h_cur_3_points','h_cur_3_minutes','h_old_3_points','h_fixed_points','pr_last3_start_rate','pr_last3_minutes_mean','pr_last_role_none','av_reported_chance','u_count_0','cal_PL_round_bindings_complete']
 fields=K+['name','starter','captain','xp','points','component_p1','component_m1','actual_minutes','actual_fixtures','base_attack1','actual_attack','base_appearance1','actual_appearance','base_residual1','actual_residual','calibration_adjustment']+features
 z[z.season.eq('2025-26')&z.code.isin([118748,448047,244851,212319,465351,560262])][fields].to_csv(P/'focus_player_histories.csv',index=False)
 exposure=allrows[allrows.model_can_buy&allrows.actual_fixtures.gt(0)].copy();exposure.groupby('season').agg(observed_buyable_rows=('code','size'),actual_double_rows=('actual_double','sum'),underestimated_exposure_rows=('exposure_under','sum')).to_csv(P/'exposure_summary.csv');exposure[exposure.exposure_under].groupby(['season','round']).agg(rows=('code','size'),actual_count_max=('actual_fixtures','max'),forecast_count_min=('u_count_0','min')).to_csv(P/'exposure_rounds.csv');z[z.exposure_under|z.exposure_over].to_csv(P/'selected_exposure_mismatches.csv',index=False)
 calendar=pd.read_csv(guard.P/'calendar.csv');calendar[calendar.season.isin(S)].groupby('season').age_days.agg(['median','max']).to_csv(P/'calendar_age.csv');cases=[];guard.configure();mod,adapter=guard.solver();engine=adapter.engine
 for s in S:
  for g in range(1,39):
   dec=read(E/'manager'/f'{s}_recent_only'/f'gw{g:02d}.decision.json');sett=read(E/'manager'/f'{s}_recent_only'/f'gw{g:02d}.settlement.json');c=dec['choice'];pv=guard.eligible_pool(s,g).set_index('pid');pos=pv.pos.to_dict();pts={int(r['code']):float(r['points']) for r in sett['outcomes']};active={int(r['code']):bool(r['appeared']) for r in sett['outcomes']};expected=pred[pred.season.eq(s)&pred['round'].eq(g)].set_index('code').xp_0.to_dict();names=z[z.season.eq(s)&z['round'].eq(g)].set_index('code').name.to_dict();base=engine.settle(c['starters'],c['bench'],c['captain'],c['vice'],pos,pts,active,None)['base']
   for incoming in c['bench']:
    if not pv.at[incoming,'can_start_0']:continue
    for outgoing in c['starters']:
     xi=[incoming if i==outgoing else i for i in c['starters']];bench=[outgoing if i==incoming else i for i in c['bench']]
     if not engine.legal_positions(xi,pos) or pos[bench[0]]!=1 or sum(pos[i]==1 for i in bench)!=1:continue
     test=engine.settle(xi,bench,xi[0],xi[1],pos,pts,active,None);gain=test['base']-base
     if gain<=0:continue
     cases.append(dict(season=s,round=g,benched_code=incoming,benched_name=names[incoming],started_code=outgoing,started_name=names[outgoing],benched_points=pts[incoming],started_points=pts[outgoing],benched_xp=expected[incoming],started_xp=expected[outgoing],actual_base_gain=gain,forecast_XI_gain=expected[incoming]-expected[outgoing],same_squad=True,chip_held_out_of_base=True))
  print('PLAYER DECISIONS VERIFIED',s,flush=True)
 swaps=pd.DataFrame(cases);swaps.to_csv(P/'legal_single_swaps.csv',index=False);swaps.sort_values(['season','round','actual_base_gain'],ascending=[True,True,False]).drop_duplicates(['season','round']).to_csv(P/'best_single_swap_per_round.csv',index=False)
 # Concrete transfers and captain pairs use IDs and the exact same archived forecasts.
 cap=[];trs=[]
 for g in range(1,39):
  s='2025-26';dec=read(E/'manager'/f'{s}_recent_only'/f'gw{g:02d}.decision.json');c=dec['choice'];data=z[z.season.eq(s)&z['round'].eq(g)].set_index('code');actual=data.points.to_dict();current=c['captain'];best=max(c['starters'],key=lambda i:actual[i]);a=data.loc[current];b=data.loc[best];cap.append(dict(round=g,captain=a['name'],captain_points=a.points,captain_xp=a.xp,alternative=b['name'],alternative_points=b.points,alternative_xp=b.xp,forecast_advantage=a.xp-b.xp,missed_normal_bonus=b.points-a.points,cap_minutes_forecast=a.component_m1,cap_minutes_actual=a.actual_minutes,alt_minutes_forecast=b.component_m1,alt_minutes_actual=b.actual_minutes,cap_fixture_forecast=a.u_count_0,cap_fixtures_actual=a.actual_fixtures,alt_fixture_forecast=b.u_count_0,alt_fixtures_actual=b.actual_fixtures))
  if dec['state_before']['owned'] and c['transfers']:
   for direction in ['incoming','outgoing']:
    for code in c[direction]:
     row=allrows[allrows.season.eq(s)&allrows['round'].eq(g)&allrows.code.eq(code)].iloc[0];trs.append(dict(round=g,chip=c['chip'],direction=direction,code=code,xp=row.xp_0,actual_points=row.actual_points,minutes_forecast=row.component_m1,minutes_actual=row.actual_minutes,attack_forecast=row.base_attack1,attack_actual=row.actual_attack,fixture_forecast=row.u_count_0,fixtures_actual=row.actual_fixtures,h_cur_3_points=row.h_cur_3_points,h_fixed_points=row.h_fixed_points,pr_last3_start_rate=row.pr_last3_start_rate))
 pd.DataFrame(cap).to_csv(P/'captain_pairs.csv',index=False);pd.DataFrame(trs).to_csv(P/'transfer_player_details.csv',index=False)
 # Check the two identified schedules against physically archived prior sources.
 schedule=[]
 for g in [33,36]:
  ca=calendar[calendar.season.eq('2025-26')&calendar['round'].eq(g)].iloc[0];f=pd.read_csv(R/ca.file);actual=raw[raw.season.eq('2025-26')&raw['round'].eq(g)&raw.code.isin([465351,560262])]
  for fixture in actual.fixture.unique():
   fr=f[f.id.eq(fixture)].iloc[0];schedule.append(dict(round=g,fixture=int(fixture),snapshot_event=None if pd.isna(fr.event) else int(fr.event),snapshot_kickoff=fr.kickoff_time,source_time=ca.source_time,forecast_at=ca.forecast_at,source_age_days=ca.age_days,source_file=ca.file))
 pd.DataFrame(schedule).to_csv(P/'specific_calendar_fixture_evidence.csv',index=False)
 verify_files(R,read(P/'proposal.json')['input_hashes']);atomic_json(P/'verification.json',dict(passed=True,selected_player_rounds=1710,all_selected_actual_points_match=True,all_observed_component_error_identities_match=True,all114_round_single_swaps_formation_and_availability_checked=True,original_models_forecasts_and_episodes_unchanged=True,no_actual_calendar_retrofit=True,files={str(p.relative_to(R)):sha(p) for p in P.glob('*.csv')}))
if __name__=='__main__':setup() if sys.argv[1]=='setup' else run()
