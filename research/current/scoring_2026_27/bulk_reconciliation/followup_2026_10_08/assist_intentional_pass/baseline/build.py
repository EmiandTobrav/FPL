"""Aggregate goal evidence without filling missing observations with zero."""
from pathlib import Path
import hashlib,json
import pandas as pd
from rules import evaluate
P=Path(__file__).resolve().parent;S=P.parent;KEY=['season','fixture','code']
OPEN={'missing_data','external_conflict','rule_recalculation','fpl_extract_exception'}
def read(path):return pd.read_csv(path,low_memory=False)
def save(df,name):df.to_csv(P/name,index=False,compression={'method':'gzip','mtime':0} if name.endswith('.gz') else None)
def contribution(goal,player,denials=()):
 if goal['status']=='awarded':return int(player==goal['recipient_player_id'])
 if goal['status']=='no_assist':return 0
 if not goal['own_goal'] and player==goal['scorer_player_id']:return 0
 if (int(goal['event_id']),player) in denials:return 0
 return None

def aggregate(goals,player,expected_goals,coverage_ok,denials=()):
 if expected_goals==0:return dict(value=0,lower_bound=0,unknown_goals=0,unresolved_goal_ids='',reason='official_team_zero_goals')
 if not coverage_ok or len(goals)!=expected_goals:return dict(value=None,lower_bound=None,unknown_goals=expected_goals,unresolved_goal_ids='',reason='goal_coverage_or_identity_gap')
 values=[contribution(g,player,denials) for g in goals]
 missing=[str(int(g['event_id'])) for g,v in zip(goals,values) if v is None]
 return dict(value=None if missing else sum(values),lower_bound=sum(v for v in values if v is not None),unknown_goals=len(missing),unresolved_goal_ids='|'.join(missing),reason='unresolved_goal_facts' if missing else 'all_player_goal_contributions_resolved')

def main():
 raw=read(P/'raw_goal_decisions.csv.gz');goals=raw.copy()
 validation=json.loads((P/'validation_summary.json').read_text())
 goals['raw_status']=goals.status;goals['source_url']='https://github.com/peteowen1/pannadata/releases/tag/opta-latest'
 goals['evidence_scope']='frozen_event_certificate_with_route_control'
 rejected=goals.status.ne('unresolved')&~goals.route.isin(validation['qualified_routes'])
 goals.loc[rejected,['status','reason','missing']]=['unresolved','route_lacks_successful_control','separate_route_validation']
 people=read(P/'inputs/participants.csv.gz')
 baseline=read(S/'fpl_authority/fpl_baseline.csv.gz')[KEY+['assists','goals_scored','own_goals']]
 people=people.merge(baseline,on=KEY,validate='one_to_one')
 # Apply only the eight already approved goal/own-goal revisions to this derived audit.
 corrections=read(S/'official_revision/counter_supplement.csv')
 for r in corrections.itertuples():
  mask=people.season.eq(r.season)&people.fixture.eq(r.fixture)&people.code.eq(r.code)
  people.loc[mask,'goals_scored' if r.field=='goals' else 'own_goals']=r.revised_value
 by_team={k:g for k,g in people.dropna(subset=['team_id']).groupby(['match_id','team_id'])}
 source_goals=raw.groupby(['match_id','scorer_player_id','own_goal']).size().to_dict()
 scorer_audit=[];bad_matches=set();conflict_matches=set()
 fixture_coverage=read(S/'bps_recovery/goal_match_coverage.csv')
 fixture_coverage['coverage_status']='goal_inventory_complete'
 fixture_coverage.loc[fixture_coverage.match_id.isna(),'coverage_status']='missing_archive_fixture'
 fixture_coverage.loc[fixture_coverage.match_id.notna()&~fixture_coverage.goal_count_matches_score,'coverage_status']='missing_goal_events'
 save(fixture_coverage,'fixture_coverage.csv')
 incomplete=set(fixture_coverage.loc[fixture_coverage.coverage_status.ne('goal_inventory_complete'),'match_id'].dropna())
 for r in people[people.player_id.notna()].itertuples():
  for field,own in [('goals_scored',False),('own_goals',True)]:
   observed=None if r.match_id in incomplete else source_goals.get((r.match_id,r.player_id,own),0)
   expected=getattr(r,field)
   ok=pd.notna(expected) and observed==expected
   if not ok:
    bad_matches.add(r.match_id)
    if r.match_id not in incomplete:conflict_matches.add(r.match_id)
   if observed or expected or not ok:scorer_audit.append(dict(season=r.season,fixture=r.fixture,code=r.code,field=field,expected=expected,observed=observed,agrees=ok,audit_status='missing_goal_inventory' if r.match_id in incomplete else ('equal' if ok else 'source_conflict')))
 save(pd.DataFrame(scorer_audit),'scorer_identity_audit.csv')
 # Unique FPL-linked identity for every source scorer, not just every assist recipient.
 identities=people.dropna(subset=['player_id']).groupby(['match_id','player_id']).size().to_dict()
 for r in goals.itertuples():
  if identities.get((r.match_id,r.scorer_player_id),0)!=1:
   bad_matches.add(r.match_id);conflict_matches.add(r.match_id)
 # Official narrative decisions are separately labelled adjudications, never predictor inputs.
 cases=json.loads((S/'assist_rules/inputs/cases.json').read_text())
 facts=json.loads((S/'assist_rules/inputs/official_facts.json').read_text())
 official=[];denials=set()
 for c in cases:
  mask=goals.match_id.eq(c['match_id'])&goals.event_id.eq(c['goal_event_id'])
  if mask.sum()!=1:raise ValueError('Official example goal missing')
  person=people[people.season.eq(c['season'])&people.fixture.eq(c['fixture'])&people.code.eq(c['code'])]
  if len(person)!=1 or person.player_id.iloc[0]!=c['candidate_player_id'] or person.team_id.iloc[0]!=goals.loc[mask,'scoring_team_id'].iloc[0]:raise ValueError('Official recipient identity mismatch')
  f=facts[c['case_id']]['facts'];decision=evaluate(f)
  official.append({**c,'facts_only_rule_decision':decision.awarded,'facts_only_reason':decision.reason,'facts_missing':'|'.join(decision.missing),'adjudication_basis':'published official decision; development evidence, not holdout'})
  if c['expected_award']:
   goals.loc[mask,['status','recipient_player_id','reason','missing','source_url','evidence_scope']]=['awarded',c['candidate_player_id'],'official_target_rule_example','',c['source_url'],'published_official_goal_adjudication']
  else:
   denials.add((c['goal_event_id'],c['candidate_player_id']))
   if f.get('scorer_own_rebound') is True:
    goals.loc[mask,['status','recipient_player_id','reason','missing','source_url','evidence_scope']]=['no_assist',None,'official_scorer_own_rebound','',c['source_url'],'published_official_goal_adjudication']
 save(pd.DataFrame(official),'official_adjudications.csv')
 # Quarantine automatic conclusions when source goal identities/counts disagree.
 bad=goals.match_id.isin(bad_matches)&goals.evidence_scope.eq('frozen_event_certificate_with_route_control')
 goals.loc[bad,['status','reason','missing']]=['unresolved','source_scorer_or_goal_count_conflict','official_goal_identity_reconciliation']
 coverage=[]
 for (mid,team),p in by_team.items():
  g=goals[goals.match_id.eq(mid)&goals.scoring_team_id.eq(team)]
  expected=p.own_team_goals.unique()
  ok=len(expected)==1 and len(g)==expected[0] and mid not in bad_matches
  coverage.append(dict(season=p.season.iloc[0],fixture=int(p.fixture.iloc[0]),match_id=mid,team_id=team,expected_goals=expected[0],observed_goals=len(g),coverage_ok=bool(ok),source_scorer_conflict=mid in conflict_matches))
  # Compatible 2025/26 FPL totals can uniquely adjudicate all-zero teams or single goals.
  if p.season.iloc[0]=='2025-26' and ok and not p.assists.isna().any():
   if p.assists.sum()==0:
    goals.loc[g.index,['status','recipient_player_id','reason','missing','evidence_scope','source_url']]=['no_assist',None,'fpl_team_zero_assists','', 'authoritative_2025_26_fpl','fpl_authority/fpl_baseline.csv.gz']
   elif len(g)==1 and p.assists.sum()==1:
    recipient=p.loc[p.assists.eq(1),'player_id'].iloc[0]
    goals.loc[g.index,['status','recipient_player_id','reason','missing','evidence_scope','source_url']]=['awarded',recipient,'fpl_single_goal_unique_assist','', 'authoritative_2025_26_fpl','fpl_authority/fpl_baseline.csv.gz']
 coverage=pd.DataFrame(coverage);save(coverage,'team_goal_coverage.csv')
 coverage_map=coverage.set_index(['match_id','team_id']).coverage_ok.to_dict()
 goal_map={k:g.to_dict('records') for k,g in goals.groupby(['match_id','scoring_team_id'])}
 totals=[]
 for r in people.to_dict('records'):
  if r['season']=='2025-26':
   result=dict(value=r['assists'],lower_bound=r['assists'],unknown_goals=0,unresolved_goal_ids='',reason='fpl_authoritative_unchanged_assist_rules')
  else:
   key=(r['match_id'],r['team_id']);result=aggregate(goal_map.get(key,[]),r['player_id'],r['own_team_goals'],coverage_map.get(key,False),denials)
  totals.append({**{k:r[k] for k in KEY+['name','match_id','team_id','player_id','own_team_goals']},'historical_fpl_assists':r['assists'],**result})
 totals=pd.DataFrame(totals);totals['resolved']=totals.value.notna();totals['assist_delta']=totals.value-totals.historical_fpl_assists
 save(totals,'player_match_totals.csv.gz')
 goals['required_for_historical_assist_recalculation']=goals.season.ne('2025-26')
 save(goals,'goal_decisions.csv.gz')
 save(goals[goals.status.eq('unresolved')&goals.required_for_historical_assist_recalculation],'remaining_goals.csv.gz')
 save(goals.groupby(['season','route','status','reason'],dropna=False).size().rename('goals').reset_index(),'goal_summary.csv')
 # Overlay only previously open assist requirements; all other cells are immutable.
 before=read(S/'delta_input_audit/requirements.csv.gz');req=before.copy()
 req['assist_previous_status']=req.status;req['assist_previous_value']=req.value
 req['assist_reason']=''
 assist=req.field.eq('assists_2026_27');target=totals.set_index(KEY)
 keys=pd.MultiIndex.from_frame(req.loc[assist,KEY]);values=target.value.reindex(keys).to_numpy()
 idx=req.index[assist]
 req.loc[idx,'assist_reason']=target.reason.reindex(keys).to_numpy()
 gaps=idx[req.loc[idx,'is_open'].to_numpy()&req.loc[idx,'assist_reason'].eq('goal_coverage_or_identity_gap').to_numpy()]
 req.loc[gaps,'status']='missing_data'
 req.loc[gaps,'quality_status']='missing_goal_inventory'
 can=idx[req.loc[idx,'is_open'].to_numpy()&pd.notna(values)]
 req.loc[can,'value']=target.value.reindex(pd.MultiIndex.from_frame(req.loc[can,KEY])).to_numpy()
 req.loc[can,'status']='documented_assist_reconstruction'
 req.loc[can,'quality_status']='goal_evidence_qualified_routes_or_official_adjudication'
 req.loc[can,'provenance']='assist_reconciliation/player_match_totals.csv.gz + goal_decisions.csv.gz'
 req['is_open']=req.status.isin(OPEN);req['is_zero']=req.value.eq(0)&~req.is_open
 pd.testing.assert_frame_equal(req.loc[~assist,before.columns],before.loc[~assist],check_dtype=False)
 protected=assist&~before.is_open
 pd.testing.assert_frame_equal(req.loc[protected,before.columns],before.loc[protected],check_dtype=False)
 save(req,'requirements.csv.gz');pending=req[req.is_open];save(pending,'remaining_fields.csv.gz')
 fields=req.groupby('field').agg(required=('field','size'),open_cells=('is_open','sum'),external_quality_cells=('needs_external_quality_review','sum'))
 for status in sorted(req.status.unique()):fields[status]=req.status.eq(status).groupby(req.field).sum()
 fields['unique_affected_player_matches']=pending.groupby('field').size()
 fields['unique_affected_player_matches']=fields.unique_affected_player_matches.fillna(0).astype(int)
 save(fields.reset_index(),'field_summary.csv')
 save(req.groupby(['season','field','status']).size().rename('cells').reset_index(),'field_summary_by_season.csv')
 players=pending.groupby(KEY).agg(name=('name','first'),open_fields=('field','size'),fields=('field',lambda s:'|'.join(sorted(s)))).reset_index()
 save(players,'remaining_player_matches.csv.gz')
 save(pending.groupby(['season','fixture']).agg(date=('date','first'),home=('home','first'),away=('away','first'),open_fields=('field','size'),unique_affected_player_matches=('code','nunique')).reset_index(),'match_summary.csv')
 save(players.groupby(['season','code']).agg(name=('name','first'),open_fields=('open_fields','sum'),unique_affected_player_matches=('fixture','size')).reset_index(),'player_summary.csv')
 save(req.groupby(['field','assist_previous_status','status']).size().rename('cells').reset_index(),'transitions.csv')
 quality=req.needs_external_quality_review;work=req.is_open|quality
 save(req[quality],'external_quality_queue.csv.gz')
 save(req[work].groupby(KEY).agg(name=('name','first'),open_fields=('is_open','sum'),external_quality_fields=('needs_external_quality_review','sum')).reset_index(),'all_work_player_matches.csv.gz')
 historic=totals.season.ne('2025-26');changed=totals[historic&totals.resolved&totals.assist_delta.ne(0)]
 save(changed,'resolved_assist_changes.csv')
 summary=dict(historical_population=len(totals),goal_events=len(goals),new_control_goals=40,control_resolved=validation['resolved'],control_errors=validation['incorrect'],newly_resolved_assist_cells=len(can),remaining_assist_cells=int(req.loc[assist,'is_open'].sum()),assist_missing_goal_inventory_cells=len(gaps),assist_unresolved_causal_or_rule_cells=int((req.loc[assist,'status']=='rule_recalculation').sum()),old_open_cells=int(before.is_open.sum()),open_cells=int(req.is_open.sum()),unique_affected_player_matches=len(players),old_unique_affected_player_matches=len(before.loc[before.is_open,KEY].drop_duplicates()),status_counts=req.status.value_counts().to_dict(),goal_status_counts=goals.status.value_counts().to_dict(),pre_2025_goal_status_counts=goals[goals.season.ne('2025-26')].status.value_counts().to_dict(),resolved_historical_changed_totals=len(changed),resolved_historical_net_assist_delta=float(changed.assist_delta.sum()),external_quality_cells=int(quality.sum()),external_quality_unique_player_matches=len(req.loc[quality,KEY].drop_duplicates()),unique_open_or_external_quality_player_matches=len(req.loc[work,KEY].drop_duplicates()),source_scorer_conflict_matches=len(conflict_matches),missing_archive_fixtures=int(fixture_coverage.coverage_status.eq('missing_archive_fixture').sum()),additional_event_gap_fixtures=int(fixture_coverage.coverage_status.eq('missing_goal_events').sum()),inferred_sparse_zeros=0,fpl_values_modified=False,keeper_values_modified=False,locked_labels_modified=False,all_assists_resolved=False,full_historical_harmonization_complete=False,cost_nok=0)
 (P/'findings.json').write_text(json.dumps(summary,indent=2)+'\n')
 inputs=list(P.glob('*.py'))+[S/'bps_recovery/goal_match_coverage.csv',S/'delta_input_audit/requirements.csv.gz',S/'fpl_authority/fpl_baseline.csv.gz',S/'official_revision/counter_supplement.csv',S/'assist_rules/inputs/cases.json',S/'assist_rules/inputs/official_facts.json']+list((P/'inputs').glob('*'))+[P/'raw_goal_decisions.csv.gz',P/'validation_summary.json',P/'prediction_freeze.json']
 (P/'manifest.json').write_text(json.dumps({str(p.relative_to(S)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(inputs)},indent=2)+'\n')
 print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
