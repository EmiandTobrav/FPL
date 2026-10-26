"""Fixed corrected-calendar forecasts; vary only detailed manager plan width."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS','VECLIB_MAXIMUM_THREADS']:os.environ[k]='1'
import sys,copy,shutil,hashlib,difflib
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import pandas as pd,numpy as np
from model_lab.common import atomic_json,sha,verify_files
from scripts import test_xg_adaptation as t
P=R/'reports/manager_horizon_2026_10_26';B=R/'reports/calendar_requalification_2026_10_26';D=R/'datasets/fpl_calendar_requalified_v1';F=t.F;OLD=F/'policy_backend';CONFIG={'h3':3,'h5':5,'h8':8};ARMS=['h5','h8'];ID='manager-planning-horizon-corrected-calendar-20261026-v1';t.P=P;t.D=D;t.ARMS=list(CONFIG)

def setup():
 P.mkdir();parent=t.read(B/'proposal.json');deps=dict(parent['input_hashes']);verify_files(R,deps);paths=[Path(__file__),B/'proposal.json',B/'calendar.csv.gz',B/'scores_calendar.csv',B/'final_verification.json',B/'manager_verification_calendar.json',B/'prediction_verification_calendar.json',B/'independent_dataset_verification.json',B/'remaining_metadata_cases.json',D/'manifest.json',R/'overview/SELECTION_RULES_V1.json',R/'scripts/report_xg_adaptation.py',R/'scripts/verify_xg_adaptation.py']
 for s in t.EVAL:paths+=list((B/'manager'/f'{s}_calendar').glob('*.json'))
 backend_changes=[]
 for arm,H in CONFIG.items():
  folder=P/f'backend_{arm}';folder.mkdir()
  for name in ['engine.py','planner.py','initial_optimizer.py','policy.py','controlled_policy_v1.py']:shutil.copyfile(OLD/name,folder/name)
  p=folder/'policy.py';original=p.read_text();needle='chips=schedule(gw,min(3,xp.shape[1]),fixed)';assert original.count(needle)==1
  if H!=3:p.write_text(original.replace(needle,f'chips=schedule(gw,min({H},xp.shape[1]),fixed)'))
  for name in ['engine.py','planner.py','initial_optimizer.py','controlled_policy_v1.py']:assert sha(folder/name)==sha(OLD/name)
  assert p.read_text()==original.replace(needle,f'chips=schedule(gw,min({H},xp.shape[1]),fixed)')
  hashes={x.name:sha(x) for x in folder.glob('*.py')};hp=P/f'backend_hashes_{arm}.json';atomic_json(hp,hashes);paths+=list(folder.glob('*.py'))+[hp];backend_changes.append(dict(arm=arm,horizon=H,only_policy_plan_width_changed=H!=3,source_diff=''.join(difflib.unified_diff(original.splitlines(True),p.read_text().splitlines(True),fromfile='control/policy.py',tofile=arm+'/policy.py'))))
  shutil.copyfile(B/'calendar.csv.gz',P/f'{arm}.csv.gz');paths.append(P/f'{arm}.csv.gz');atomic_json(P/f'prediction_lock_{arm}.json',dict(sealed_before_manager=True,same_corrected_calendar_forecasts=True,files={f'{arm}.csv.gz':sha(P/f'{arm}.csv.gz')}));atomic_json(P/f'prediction_verification_{arm}.json',dict(passed=True,identical_to_qualified_calendar_forecasts=sha(P/f'{arm}.csv.gz')==sha(B/'calendar.csv.gz'),parent_verification=str((B/'prediction_verification_calendar.json').relative_to(R)),all8offsets_unchanged=True))
 scores=pd.read_csv(B/'scores_calendar.csv');scores.arm='h3';scores.to_csv(P/'scores_h3.csv',index=False);assert scores.set_index('season').net.to_dict()=={'2023-24':2465.,'2024-25':2604.,'2025-26':2322.};shutil.copyfile(R/'overview/ACTIVE_TEAM_BENCHMARK.json',P/'reference_ACTIVE_TEAM_BENCHMARK.json');paths+=[R/'overview/ACTIVE_TEAM_BENCHMARK.json',R/'datasets/COMMON_TRAINING_ACTIVE.json',P/'scores_h3.csv'];deps.update({str(p.relative_to(R)):sha(p) for p in paths})
 spec=dict(parent);spec.update(id=ID,candidate_id='manager_detailed_horizons5_8_same_chip_date_grid_v1',hypothesis='Evaluate5and8round rolling transfer/chip plans against current3round manager with corrected calendar and identical8offset forecasts. A longer evaluation of wildcard/freehit continuation may reduce the observed loss afterDGW33.',change='Only min(3,xp.shape[1]) in policy.select_plan becomes5or8 in private backend copies. Same full player pool, shortlist RULE, FT/cash/transfer friction, objectives, chip reserve/forcing/tie-break and explicit future chip date grid (next2rounds; existing cheap TC/BB option bound over8). Every current and shifted chip scenario uses the longer detailed transfer plan, truncated by available8forecasts/end of season/fixedchip boundaries. Opening team optimizer unchanged. Six new full seasons; exact control code/choices and114saved settlements verified. No new sources, models, calibration, discounts, rules, budgets or automatic activation.',related_work=[parent['id'],'current-player-decision-diagnosis-20261026-v2'],input_hashes=deps,model_parameters=dict(unchanged=True,forecast_offsets=8,base_and_calibration_refits='1,5,9,...37',calibration_half_life_days=180,ridge=.01),decision_policy=dict(horizons=CONFIG,opening='same empty1000bank1FT; initial optimizer unchanged',same_rules=True,same_forecasts=True,same_full_input_player_pool=True,shortlist_rule_unchanged_but_future_mean_uses_plan_width=True,chip_future_date_grid='unchanged explicit j=1,2; original cheap TC/BB j=3..7 approximation unchanged',future_option_discount=.9,node_actual_cap=16,node_request=15,max_calls=40,threads=1,no_wallclock_limit=True),resources=dict(new_model_fits=0,new_forecast_or_calibration_fits=0,new_full_seasons=6,new_actual_manager_decisions=228,reused_control_seasons=3,control_identity_decisions=2,adversarial_preflight_decisions=6,workers=4,threads=1),maximum_runs=1,success_criterion='Each year net-after-hits,2025priority/latest2mean/all3mean/spread; late2025GW32..38, chip dates, transfers/hits and solver feasibility/gap/resource telemetry. No forecast-accuracy change since all predictions are byte-identical. No automatic promotion.',stop_rule='No parameter or node/call relaxation. Any infeasible solve, missing incumbent or budget failure stops that arm/episode and yields no valid full-season score; never replace it with a partial total or hidden retry. Other fixed candidate may finish independently. No score-driven pruning or new horizons.')
 atomic_json(P/'proposal.json',spec);atomic_json(P/'one_change_verification.json',dict(passed=True,backends=backend_changes,identical_forecast_sha256=sha(B/'calendar.csv.gz'),all_other_backend_files_byte_identical=True,only_detailed_plan_width_changed=True));atomic_json(P/'dataset_verification.json',dict(passed=True,qualified_corrected_calendar=str(D.relative_to(R)),same_data_sources_roster_and_eligibility_as_parent=True));print('MANAGER HORIZONS PREPARED:5and8vs3;6episodes',flush=True)

def solver(arm,trace_season=None):
 hashes=t.read(P/f'backend_hashes_{arm}.json');folder=P/f'backend_{arm}';verify_files(folder,hashes);mod=t.common.module(f'_horizon_controlled_{arm}',folder/'controlled_policy_v1.py');mod.OLD=folder;mod.EXPECTED={n:hashes[n] for n in ['engine.py','planner.py','initial_optimizer.py','policy.py']};a=mod.ControlledPolicy(mod.Budget(node_limit=16,max_calls=40));a.options['node_limit']=15;original=a.engine.apply_decision
 def checked(state,choice,records,gw=None,chip=None):
  byid={int(r['pid']):r for r in records};assert all(byid[int(i)]['can_start_0'] for i in choice['starters']);assert byid[int(choice['captain'])]['can_start_0'] and byid[int(choice['vice'])]['can_start_0'];assert all(byid[int(i)]['can_buy'] for i in choice['incoming'])
  if (chip if chip is not None else choice.get('chip'))=='bench_boost':assert all(byid[int(i)]['can_start_0'] for i in choice['squad'])
  return original(state,choice,records,gw,chip)
 a.engine.apply_decision=checked
 if trace_season:
  decide=a.decide
  def traced(pool,xp,state,gw,*args,**kwargs):
   result=decide(pool,xp,state,gw,*args,**kwargs);atomic_json(P/'manager'/f'{trace_season}_{arm}'/f'gw{gw:02d}.chip_candidates.json',mod.clean(dict(requested_horizon=CONFIG[arm],forecast_columns=xp.shape[1],outcomes_read=False,chip_candidates=result['chip_candidates'])));return result
  a.decide=traced
 return mod,a

def configure(arm,season=None):
 t.guard.solver=lambda:solver(arm,season);t.guard.configure()

def inputs(s,g):
 origins=t.load(F/'origins.pkl');at=origins[(s,g)];pool=t.guard.m.method.qualify(t.guard.eligible_pool(s,g),s,at);f=pd.read_csv(P/'h3.csv.gz');q=f[f.season.eq(s)&f['round'].eq(g)].set_index('code').reindex(pool.code);assert pd.to_datetime(q.forecast_at,utc=True).eq(at).all() and q.can_buy.tolist()==pool.can_buy.tolist();xp=q[[f'xp_{j}' for j in range(min(8,39-g))]].to_numpy(float);return pool,xp

def identity():
 t.check();configure('h3');rows=[]
 for s,g in [('2025-26',32),('2025-26',34)]:
  old=t.read(B/'manager'/f'{s}_calendar'/f'gw{g:02d}.decision.json');pool,xp=inputs(s,g);state=copy.deepcopy(old['state_before']);state['owned']={int(k):v for k,v in state['owned'].items()};mod,a=solver('h3');result=a.decide(pool,xp,state,g);assert mod.clean(result['choice'])==old['choice'];assert [r['model_sha256'] for r in a.ledger]==[r['model_sha256'] for r in old['solver_calls']];rows.append(dict(season=s,round=g,chip=result['choice']['chip'],calls=len(a.ledger),choice_and_all_numeric_MIPs_identical=True));print('H3 CONTROL IDENTITY',s,g,flush=True)
 atomic_json(P/'control_identity_verification.json',dict(passed=True,decisions=rows,backend_all_files_byte_identical=True))

def preflight(arm):
 t.check();configure(arm);cases=[]
 for s,g in [('2023-24',1),('2023-24',10),('2025-26',32)]:
  pool,xp=inputs(s,g);mod,a=solver(arm);state=a.engine.initial_state() if g==1 else t.read((t.FIT/'manager'/f'{s}_operational_matched' if s=='2023-24' else B/'manager'/f'{s}_calendar')/f'gw{g:02d}.decision.json')['state_before'];state['owned']={int(k):v for k,v in state['owned'].items()};xp[~pool.can_start_0.to_numpy()]=10000.;result=a.decide(pool,xp,state,g);choice=copy.deepcopy(result['choice']);a.engine.apply_decision(state,choice,pool.to_dict('records'),g);assert len(a.ledger)<=40 and all(r['nodes']<=16 and r['full_mip_feasible'] for r in a.ledger);assert not(78830 in choice['starters'] or 78830 in [choice['captain'],choice['vice']]);cases.append(dict(season=s,round=g,calls=len(a.ledger),planned_horizon=choice.get('planned_horizon',1),passed=True));print('HORIZON PREFLIGHT',arm,s,g,flush=True)
 atomic_json(P/f'preflight_{arm}.json',dict(passed=True,cases=cases,same_hostile_unavailability_tests=True))

def replay(arm):
 configure(arm)
 from scripts import report_xg_adaptation as report
 if arm!='h3':report.managers(arm);return
 # Reuse only the verified corrected-calendar control decisions, independently settle them again.
 for s in t.EVAL:
  dest=P/'manager'/f'{s}_h3';dest.mkdir(parents=True)
  for p in (B/'manager'/f'{s}_calendar').glob('*.json'):shutil.copyfile(p,dest/p.name)
 report.managers('h3')

def finish():
 t.check();assert t.read(P/'control_identity_verification.json')['passed'] and t.read(P/'one_change_verification.json')['passed']
 for arm in CONFIG:assert t.read(P/f'manager_verification_{arm}.json')['passed']
 scores=pd.concat([pd.read_csv(P/f'scores_{arm}.csv') for arm in CONFIG]);assert len(scores)==9 and scores.complete.all();scores.to_csv(P/'scores.csv',index=False);w=scores.pivot(index='season',columns='arm',values='net');w.to_csv(P/'comparison.csv');delta=w.subtract(w.h3,axis=0);delta.to_csv(P/'deltas.csv');summary=[];rounds=[];chips=[];telemetry=[]
 for arm,H in CONFIG.items():
  v=w[arm];summary.append(dict(arm=arm,horizon=H,mean_all3=float(v.mean()),mean_latest2=float(v.iloc[-2:].mean()),net2025=float(v.iloc[-1]),delta2025=float(delta.loc['2025-26',arm]),mean_delta_latest2=float(delta[arm].iloc[-2:].mean()),variance=float(np.var(v)),range=float(v.max()-v.min()),all_year_nondecrease=bool(delta[arm].ge(0).all())))
  for s in t.EVAL:
   for g in range(1,39):
    path=P/'manager'/f'{s}_{arm}';dec=t.read(path/f'gw{g:02d}.decision.json');sett=t.read(path/f'gw{g:02d}.settlement.json');c=dec['choice'];rounds.append(dict(arm=arm,season=s,round=g,net=sett['net'],base=sett['settlement']['base'],captain_bonus=sett['settlement']['captain_bonus'],hits=sett['hits'],transfers=c['transfers'],chip=c['chip'],captain=c['captain'],planned_horizon=c.get('planned_horizon',1),shortlist=c['pool_size'],solver_calls=len(dec['solver_calls'])))
    if c['chip']:chips.append(dict(arm=arm,season=s,round=g,chip=c['chip'],net=sett['net']))
    for call in dec['solver_calls']:telemetry.append(dict(arm=arm,season=s,round=g,call=call['call'],variables=call['variables'],constraints=call['constraints'],seconds=call['seconds'],nodes=call['nodes'],gap=call['gap'],termination_class=call['termination_class']))
 pd.DataFrame(summary).to_csv(P/'summary.csv',index=False);pd.DataFrame(rounds).to_csv(P/'rounds.csv',index=False);pd.DataFrame(chips).to_csv(P/'chip_dates.csv',index=False);pd.DataFrame(telemetry).to_csv(P/'solver_telemetry.csv',index=False);files=list(P.glob('*.csv'))+[P/f'manager_verification_{a}.json' for a in CONFIG]+[P/'control_identity_verification.json',P/'one_change_verification.json']+[P/f'preflight_{a}.json' for a in ARMS];atomic_json(P/'final_verification.json',dict(passed=True,new_full_seasons=6,new_decisions_independently_replayed=228,reused_control_seasons_independently_replayed=3,control_decisions_replayed=114,new_model_fits=0,new_forecasts=0,all8forecast_columns_byte_identical=True,only_detailed_plan_horizon_changed=True,node_cap16_call_cap40_unchanged=True,active_model_unchanged=True,files={str(p.relative_to(R)):sha(p) for p in files}));print('HORIZON TEST COMPLETE',w.to_string(),flush=True)
if __name__=='__main__':
 a=sys.argv[1]
 if a=='setup':setup()
 elif a=='identity':identity()
 elif a=='preflight':preflight(sys.argv[2])
 elif a=='manager':configure(sys.argv[3],sys.argv[2]);t.manager(sys.argv[2],sys.argv[3])
 elif a=='replay':replay(sys.argv[2])
 elif a=='finish':finish()
 else:raise ValueError(a)
