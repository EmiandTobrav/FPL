"""Read-only current-model attribution and fixed-path hindsight diagnostics."""
import os
for k in ['OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS']:os.environ[k]='1'
import sys,copy,itertools,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
import pandas as pd,numpy as np
from model_lab.common import sha,atomic_json,verify_files
from scripts import matched_availability_retest_v8 as guard
P=R/'reports/current_model_loss_diagnosis_2026_10_26_v3';B=R/'reports/base_cadence_2026_10_26';E=R/'reports/xg_adaptation_2026_10_26_v2';S=['2023-24','2024-25','2025-26'];KEY=['season','round','code']
read=lambda p:json.loads(Path(p).read_text())
def setup():
 P.mkdir();parent=read(B/'proposal.json');files=[Path(__file__),R/'overview/ACTIVE_TEAM_BENCHMARK.json',B/'standard.csv.gz',B/'forecast_metrics.csv',B/'component_metrics.csv',B/'ranking.csv',B/'scores_standard.csv',guard.P/'head_data.pkl',guard.P/'availability.csv.gz',guard.P/'policy_backend_hashes.json',R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',R/'datasets/fpl_2026_27_best_effort_v1/manifest.json',R/'datasets/fpl_common_training_v5/manifest.json']+list((guard.P/'policy_backend').glob('*.py'))
 for s in S:files+=list((E/'manager'/f'{s}_recent_only').glob('*.json'))
 deps={str(f.relative_to(R)):sha(f) for f in files};spec=dict(parent);spec.update(id='current-component-loss-diagnosis-20261026-v3',candidate_id='frozen_current_model_fixed_path_loss_diagnosis_v3',hypothesis='Locate the current models2025/26 weakness using exact scoring bridges, forecast errors, captain ranking, fixed-squad lineup hindsight, ordinary transfer hold comparisons and fixed-path TC/BB timing bounds.',change='Read-only diagnosis of existing current-standard episodes. No model fitting, new source, operational decision, full policy search or production update. Compare all3seasons. Hindsight is labelled nondeployable and overlapping diagnostics are never added. WC/FH effects are only local comparisons, not full opportunity values.',related_work=['current-component-loss-diagnosis-20261026-v2','current-component-loss-diagnosis-20261026-v1',parent['id'],'component-recent180-operational-20261026-v1'],model_parameters=dict(unchanged=True),resources=dict(new_model_fits=0,new_full_manager_episodes=0,existing_decisions=114,local_enumeration_squad15=True,local_hold_comparisons_max111=True,fixed_path_chip_replays=3,new_optimizer_calls=0),input_hashes=deps,success_criterion='All114 original settlements, forecast inputs and selected captain forecasts checked. Additive scoring identity exact. All fixed-path chip choices legal in independent engine replay. Unknown outcomes never fabricated.',stop_rule='Stop on score/input mismatch; missing local counterfactual outcomes are recorded as unknown, not0. Technical v3 excludes unavailable15-player hold BB counterfactuals; v2 stopped before results. No parameter tuning or automatic activation.',maximum_runs=1)
 atomic_json(P/'proposal.json',spec)

def lineup(ids,pv,values,engine):
 ids=list(map(int,ids));pos=pv.pos.to_dict();legal=[]
 for xi in itertools.combinations(ids,11):
  if all(bool(pv.at[i,'can_start_0']) for i in xi) and engine.legal_positions(xi,pos):legal.append(xi)
 if not legal:return None
 xi=max(legal,key=lambda x:(sum(values[i] for i in x),tuple(-i for i in x)));rest=set(ids)-set(xi);bench=sorted([i for i in rest if pos[i]==1])+sorted([i for i in rest if pos[i]!=1],key=lambda i:(-values[i],i));rank=sorted(xi,key=lambda i:(-values[i],i));return dict(squad=sorted(ids),starters=list(xi),bench=bench,captain=rank[0],vice=rank[1])

def run():
 verify_files(R,read(P/'proposal.json')['input_hashes']);guard.configure();mod,adapter=guard.solver();engine=adapter.engine;env=guard.m.MatchedEnvironment();pred=pd.read_csv(B/'standard.csv.gz').set_index(KEY);raw=pd.read_csv(R/'datasets/fpl_2026_27_best_effort_v1/player_matches.csv.xz',usecols=KEY+['name','target_total_points','native_minutes']);names=raw.groupby('code')['name'].last().to_dict();truth=raw.groupby(KEY).target_total_points.sum(min_count=1);weeks=[];captains=[];transfers=[];chips=[];players=[];hold=[];chip_replays=[]
 for s in S:
  caches={};total=0
  for g in range(1,39):
   dec=read(E/'manager'/f'{s}_recent_only'/f'gw{g:02d}.decision.json');saved=read(E/'manager'/f'{s}_recent_only'/f'gw{g:02d}.settlement.json');c=dec['choice'];state=copy.deepcopy(dec['state_before']);state['owned']={int(k):v for k,v in state['owned'].items()};state['ownership_clubs']={int(k):v for k,v in state.get('ownership_clubs',{}).items()};pool=guard.m.method.qualify(guard.eligible_pool(s,g),s,guard.m.load('origins.pkl')[(s,g)]);pv=pool.set_index('pid');q=pred.xs((s,g),level=['season','round']);xp=q.xp_0.to_dict();pos=pv.pos.to_dict();pts={int(v['code']):float(v['points']) for v in saved['outcomes']};active={int(v['code']):bool(v['appeared']) for v in saved['outcomes']};params=[c[k] for k in ['starters','bench','captain','vice']];sett=engine.settle(*params,pos,pts,active,c['chip']);normal=engine.settle(*params,pos,pts,active,None)
   assert mod.clean(sett)==saved['settlement'] and sett['gross']-saved['hits']==saved['net'];assert not dec['outcomes_read'];x=q.reindex(pool.code)[[f'xp_{j}' for j in range(min(8,39-g))]].to_numpy(float)
   import hashlib
   assert hashlib.sha256(x.tobytes()).hexdigest()==dec['forecast_input_sha256'];total+=saved['net'];cap=c['captain'];weight=2 if c['chip']=='triple_captain' else 1;bestcap=max(c['starters'],key=lambda i:(pts[i] if active[i] else 0,-i));bestcappts=pts[bestcap] if active[bestcap] else 0;cappts=normal['captain_bonus'];capgap=bestcappts-cappts;capbestxp=max(xp[i] for i in c['starters']);chipincrement=sett['gross']-normal['gross'];bestline=normal['base'];bestxi=None
   for xi in itertools.combinations(c['squad'],11):
    if not all(bool(pv.at[i,'can_start_0']) for i in xi) or not engine.legal_positions(xi,pos):continue
    rest=set(c['squad'])-set(xi);bgk=[i for i in rest if pos[i]==1];bout=[i for i in rest if pos[i]!=1]
    orders=itertools.permutations(bout) if any(not active[i] for i in xi) else [tuple(bout)]
    for order in orders:
     z=engine.settle(list(xi),bgk+list(order),xi[0],xi[1],pos,pts,active,None)
     if z['base']>bestline:bestline=z['base'];bestxi=xi
   bbextra=engine.settle(*params,pos,pts,active,'bench_boost')['gross']-normal['gross'];tc_extra=cappts;bb_legal=all(bool(pv.at[i,'can_start_0']) for i in c['squad']);expectbase=sum(xp[i] for i in c['starters']);expectedcap=xp[cap];row=dict(season=s,round=g,net=saved['net'],base=sett['base'],captain_bonus=sett['captain_bonus'],hits=saved['hits'],normal_base=normal['base'],normal_captain=cappts,BB_increment=chipincrement if c['chip']=='bench_boost' else 0,TC_increment=chipincrement if c['chip']=='triple_captain' else 0,chip=c['chip'],transfers=c['transfers'],captain=cap,captain_name=names.get(cap),captain_actual=cappts,captain_xp=expectedcap,captain_argmax_xp_gap=capbestxp-xp[cap],captain_normal_hindsight_gap=capgap,captain_fixed_chip_hindsight_gap=(1+int(c['chip']=='triple_captain'))*capgap,best_captain_name=names.get(bestcap),best_captain_points=bestcappts,lineup_hindsight_gain=bestline-normal['base'],expected_XI=expectbase,XI_actual_minus_expected=normal['base']-expectbase,captain_actual_minus_expected=cappts-expectedcap,autosub_gain=normal['autosub_gain'],starting_nonappearances=sum(not active[i] for i in c['starters']),BB_opportunity=bbextra,BB_legal=bb_legal,TC_opportunity=tc_extra)
   assert row['normal_base']+row['normal_captain']+row['BB_increment']+row['TC_increment']-row['hits']==row['net'];weeks.append(row);captains.append({k:row[k] for k in ['season','round','captain_name','captain_actual','captain_xp','best_captain_name','best_captain_points','captain_normal_hindsight_gap','captain_argmax_xp_gap']})
   for i in c['squad']:players.append(dict(season=s,round=g,code=i,name=names.get(i),position=pv.at[i,'pos'],starter=i in c['starters'],captain=i==cap,xp=xp[i],points=pts[i],appeared=active[i],contribution=sett['contributions'][i]))
   if state['owned']:
    ids=list(state['owned']);candidate=lineup(ids,pv,xp,engine)
    if candidate is not None:
     candidate['incoming']=[];candidate['chip']=c['chip'] if c['chip'] in ['triple_captain','bench_boost'] else None
     try:
      if candidate['chip']=='bench_boost' and not all(bool(pv.at[i,'can_start_0']) for i in ids):raise engine.RuleError('Hold BB would contain a confirmed unavailable player')
      _,legal=engine.apply_decision(state,candidate,pool.to_dict('records'),g);out=env.outcomes(s,g,legal,pool);y={int(v['code']):float(v['points']) for v in out};a={int(v['code']):bool(v['appeared']) for v in out};keep=engine.settle(*[legal[k] for k in ['starters','bench','captain','vice']],pos,y,a,legal['chip']);hold.append(dict(season=s,round=g,chip=c['chip'],transfers=c['transfers'],actual_net=saved['net'],hold_net=keep['gross'],actual_minus_hold=saved['net']-keep['gross'],same_prestate=True,hold_chosen_on_forecasts=True))
     except (ValueError,KeyError,engine.RuleError) as err:hold.append(dict(season=s,round=g,chip=c['chip'],transfers=c['transfers'],excluded=str(err)))
    else:hold.append(dict(season=s,round=g,chip=c['chip'],transfers=c['transfers'],excluded='No legal hold XI under current hard availability'))
    if c['chip'] not in ['free_hit','wildcard'] and c['transfers']:
     for h in [1,3]:
      if g+h>39:continue
      def future_sum(ids):
       keys=[(s,j,int(i)) for j in range(g,g+h) for i in ids];v=truth.reindex(pd.MultiIndex.from_tuples(keys,names=KEY));return float(v.sum()) if v.notna().all() else np.nan
      incoming=future_sum(c['incoming']);outgoing=future_sum(c['outgoing']);transfers.append(dict(season=s,round=g,horizon=h,transfers=c['transfers'],incoming_names='; '.join(names.get(i,str(i)) for i in c['incoming']),outgoing_names='; '.join(names.get(i,str(i)) for i in c['outgoing']),incoming_points=incoming,outgoing_points=outgoing,raw_delta=incoming-outgoing,hits=saved['hits'],unknown=not(np.isfinite(incoming) and np.isfinite(outgoing))))
   if c['chip']:chips.append(dict(season=s,round=g,chip=c['chip'],direct_increment_vs_same_team_no_chip=chipincrement,captain_name=names.get(cap),captain_points=cappts,net=saved['net']))
   caches[g]=(dec,c,pool,pos,pts,active)
  assert total==read(E/'manager'/f'{s}_recent_only'/'summary.json')['net'];year=pd.DataFrame([r for r in weeks if r['season']==s]);schedule={}
  for start,end in [(1,19),(20,38)]:
   allowed=year[year['round'].between(start,end)&~year.chip.isin(['wildcard','free_hit'])];opts=[None]+allowed['round'].tolist();best=(0,None,None)
   for bb in opts:
    if bb is not None and not bool(year.set_index('round').at[bb,'BB_legal']):continue
    for tc in opts:
     if bb is not None and bb==tc:continue
     gain=(float(year.set_index('round').at[bb,'BB_opportunity']) if bb is not None else 0)+(float(year.set_index('round').at[tc,'TC_opportunity']) if tc is not None else 0)
     if gain>best[0]:best=(gain,bb,tc)
   if best[1] is not None:schedule[best[1]]='bench_boost'
   if best[2] is not None:schedule[best[2]]='triple_captain'
  newstate=engine.initial_state();net=0
  for g,(dec,c,pool,pos,pts,active) in caches.items():
   chip=c['chip'] if c['chip'] in ['wildcard','free_hit'] else schedule.get(g);candidate={k:c[k] for k in ['squad','starters','bench','captain','vice']};candidate['chip']=chip;candidate['incoming']=sorted(set(candidate['squad'])-set(newstate['owned']));after,legal=engine.apply_decision(newstate,candidate,pool.to_dict('records'),g);z=engine.settle(*[legal[k] for k in ['starters','bench','captain','vice']],pos,pts,active,chip);net+=z['gross']-4*legal['paid'];newstate=after
  expected=total-year.BB_increment.sum()-year.TC_increment.sum()+sum(year.set_index('round').at[g,'BB_opportunity' if chip=='bench_boost' else 'TC_opportunity'] for g,chip in schedule.items());assert net==expected
  chip_replays.append(dict(season=s,actual_net=total,fixed_path_hindsight_net=net,gain=net-total,schedule=schedule,full_legal_replay=True));print('CURRENT DIAGNOSIS',s,total,'CHIP BOUND',net-total,flush=True)
 for name,rows in [('rounds',weeks),('captains',captains),('players',players),('transfers',transfers),('hold',hold),('chips',chips)]:pd.DataFrame(rows).to_csv(P/f'{name}.csv',index=False)
 w=pd.DataFrame(weeks);fields=['net','normal_base','normal_captain','BB_increment','TC_increment','hits','captain_normal_hindsight_gap','captain_fixed_chip_hindsight_gap','lineup_hindsight_gain','expected_XI','XI_actual_minus_expected','captain_actual_minus_expected','autosub_gain','starting_nonappearances','transfers'];w.groupby('season')[fields].sum().to_csv(P/'decomposition.csv');w.assign(block=pd.cut(w['round'],[0,4,12,24,38],labels=['GW1_4','GW5_12','GW13_24','GW25_38'])).groupby(['season','block'],observed=True)[fields].sum().to_csv(P/'periods.csv');atomic_json(P/'chip_timing_bounds.json',dict(fixed_actual_team_and_captain_path=True,WC_FH_dates_fixed=True,not_a_deployable_strategy=True,results=chip_replays));verify_files(R,read(P/'proposal.json')['input_hashes']);atomic_json(P/'verification.json',dict(passed=True,original_decisions_checked=114,all_original_settlements_exact=True,all_forecast_input_hashes_match=True,exact_additive_score_identity=True,new_models=0,new_policy_optimizer_calls=0,chip_fixed_path_legal_replays=3,unknown_transfer_outcomes_excluded=True,active_model_unchanged=True,files={str(p.relative_to(R)):sha(p) for p in P.glob('*.csv')}))
if __name__=='__main__':setup() if sys.argv[1]=='setup' else run()
