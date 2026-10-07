"""Offline source qualification and updated FPL-authoritative requirements.

Raw signed net tackles are distinct from a clipped BPS component. Shared Opta
ancestry and diagnostic event counts are never labelled independent validation.
"""
from pathlib import Path
import hashlib,json
import pandas as pd
P=Path(__file__).resolve().parent;S=P.parent;KEY=['season','fixture','code']
FIELDS={'timesTackled':'times_tackled','savedObox':'saved_obox','savedIbox':'saved_ibox',
 'totalTackle':'total_tackle','wonTackle':'won_tackle','challengeLost':'challenge_lost',
 'clearanceOffLine':'clearance_off_line','totalClearance':'total_clearance','outfielderBlock':'outfielder_block',
 'interception':'interception','ballRecovery':'ball_recovery','wasFouled':'was_fouled',
 'ontargetScoringAtt':'ontarget_scoring_att','attPenGoal':'att_pen_goal','saves':'saves'}
REQ_MAP={'times_tackled':'timesTackled','saves_outside_box':'savedObox','saves_inside_box':'savedIbox',
 'total_tackles':'totalTackle','won_tackles':'wonTackle','goal_line_clearances':'clearanceOffLine',
 'recoveries':'ballRecovery','fouls_won':'wasFouled','shots_on_target':'ontargetScoringAtt','penalty_goals':'attPenGoal','saves':'saves'}
OPEN={'missing_data','external_conflict','rule_recalculation','fpl_extract_exception'}
HASHES={}

def read(path):
 HASHES[str(path.relative_to(S))]=hashlib.sha256(path.read_bytes()).hexdigest()
 return pd.read_csv(path,low_memory=False)

def save(df,name):
 df.to_csv(P/name,index=False,compression={'method':'gzip','mtime':0} if name.endswith('.gz') else None)

def raw_net(total,won):
 """Two explicit compatible counts; no null coercion and no BPS clipping."""
 valid=total.notna()&won.notna()&total.ge(0)&won.ge(0)&won.le(total)&total.mod(1).eq(0)&won.mod(1).eq(0)
 return (2*won-total).where(valid)

def compare(a,b):
 status=pd.Series('both_omitted',index=a.index)
 status.loc[a.notna()^b.notna()]='omission_difference'
 status.loc[a.notna()&b.notna()&a.eq(b)]='equal_explicit'
 status.loc[a.notna()&b.notna()&a.ne(b)]='explicit_conflict'
 return status

def main():
 HASHES.clear()
 archive=read(P/'inputs/archive_projection.csv.gz').set_index(KEY)
 if not archive.index.is_unique:raise ValueError('Duplicate target keys')
 linked=archive.mapping_status.eq('matched')
 if archive.loc[linked,['match_id','player_id']].duplicated().any():raise ValueError('Duplicate source identity')
 invalid=[];coverage=[]
 for season,g in archive.groupby(level='season'):
  for field in FIELDS:
   v=g[field];bad=v.notna()&(v.lt(0)|v.mod(1).ne(0))
   for k in v[bad].index:invalid.append(dict(zip(KEY,k),field=field,value=v.loc[k]))
   coverage.append(dict(season=season,field=field,rows=len(g),explicit=int(v.notna().sum()),explicit_zero=int(v.eq(0).sum()),positive=int(v.gt(0).sum()),omitted=int(v.isna().sum()),invalid=int(bad.sum())))
 save(pd.DataFrame(coverage),'field_coverage.csv')
 if invalid:raise ValueError('Invalid archive counters: '+repr(invalid[:3]))
 archive['legacy_net_tackles']=raw_net(archive.totalTackle,archive.wonTackle)
 # Existing development controls + new preselected source checks.
 old=read(S/'bps_recovery/inputs/primary_controls.csv.gz');old['control_scope']='existing_development'
 follow=read(S/'keeper_recovery/followup/primary_verified/observations.csv');follow['control_scope']='existing_followup'
 fresh=read(P/'inputs/fresh_primary_controls.csv');fresh['control_scope']='fresh_prespecified'
 if len(fresh)!=28 or fresh.duplicated(KEY).any():raise ValueError('Incomplete fresh sample')
 targeted=read(P/'inputs/targeted_primary_controls.csv');targeted['control_scope']='targeted_after_aggregate_difference'
 frames=pd.concat([old,follow,fresh,targeted],ignore_index=True)
 numeric=[x for x in frames if x.startswith('pl_') and x not in ['pl_player_id']]
 for _,g in frames.groupby(KEY):
  if len(g)>1 and g[numeric].nunique().gt(1).any():raise ValueError('Primary control disagreement')
 controls=frames.drop_duplicates(KEY,keep='last').set_index(KEY)
 if pd.MultiIndex.from_frame(fresh[KEY]).isin(pd.MultiIndex.from_frame(pd.concat([old[KEY],follow[KEY]]))).any():raise ValueError('Fresh sample reused')
 joined=archive.join(controls[[x for x in controls if x.startswith('pl_')]+['control_scope']],how='inner')
 comparisons=[]
 for field,alias in FIELDS.items():
  b=joined.get('pl_'+alias,pd.Series(float('nan'),index=joined.index))
  c=joined[['name','control_scope',field]].rename(columns={field:'archive'}).copy();c['field']=field;c['primary']=b;c['comparison']=compare(c.archive,b);comparisons.append(c.reset_index())
 comp=pd.concat(comparisons,ignore_index=True)
 save(comp,'primary_comparisons.csv.gz')
 save(comp.groupby(['control_scope','field','comparison'],sort=True).size().rename('cells').reset_index(),'primary_comparison_summary.csv')
 save(comp[comp.comparison.isin(['explicit_conflict','omission_difference'])],'primary_disagreements.csv')
 # Event counts are diagnostics, not proof that omitted stats/qualifiers are zero.
 events=read(P/'inputs/event_counts.csv.gz')
 event=archive.reset_index().merge(events,on=['match_id','player_id'],how='left',validate='many_to_one').set_index(KEY)
 ed=[]
 for field,col in [('totalTackle','event_total_tackle'),('wonTackle','event_won_tackle'),('challengeLost','event_challenge_lost'),('clearanceOffLine','event_line_markers')]:
  d=event[['name',field,col]].rename(columns={field:'archive',col:'event_candidate'}).copy();d['field']=field
  d['comparison']=compare(d.archive,d.event_candidate);ed.append(d.reset_index())
 ed=pd.concat(ed,ignore_index=True)
 save(ed,'event_comparisons.csv.gz')
 save(ed.groupby(['field','comparison']).size().rename('cells').reset_index(),'event_comparison_summary.csv')
 save(ed[ed.comparison.eq('explicit_conflict')],'event_conflicts.csv')
 # Every existing external requirement is screened; direct source corroboration is labelled separately.
 req=read(S/'fpl_authority/requirements.csv.gz')
 if req.duplicated(KEY+['field']).any():raise ValueError('Duplicate requirements')
 req['previous_status']=req.status;req['previous_value']=req.value
 req['quality_status']='not_external_work'
 req.loc[req.needs_external_quality_review,'quality_status']='mapping_reviewed_not_individually_confirmed'
 # Values supplied by the new archive projection. Earlier FPL/approved fields never enter this branch.
 new_fields={'times_tackled':'timesTackled','saves_outside_box':'savedObox','legacy_net_tackles':'legacy_net_tackles'}
 protected=req.status.isin(['fpl_authoritative','approved_reconstruction','official_revision','documented_zero'])
 for field,column in new_fields.items():
  mask=req.field.eq(field)&~protected;idx=req.index[mask];keys=pd.MultiIndex.from_frame(req.loc[idx,KEY])
  values=archive[column].reindex(keys).to_numpy();req.loc[idx,'archive_projected']=values
  have=pd.Series(values,index=idx).notna();oldval=req.loc[idx,'value']
  conflict=have&oldval.notna()&oldval.ne(values)
  fill=have&~conflict&req.loc[idx,'status'].isin(['missing_data','external_available'])
  ii=idx[fill];req.loc[ii,'value']=pd.Series(values,index=idx).loc[ii]
  req.loc[ii,'status']='external_available'
  req.loc[ii,'provenance']='hash_pinned_archive_explicit' if field!='legacy_net_tackles' else 'signed_2_wonTackle_minus_totalTackle_both_explicit'
  req.loc[ii,'quality_status']='mapping_reviewed_not_individually_confirmed'
  ii=idx[conflict];req.loc[ii,['value','status','quality_status']]=[float('nan'),'external_conflict','projection_conflict']
 # Keep primary values and matched event disagreements visible, without majority voting.
 pindex=controls.reindex(archive.index)
 prim={field:pindex.get('pl_'+FIELDS[column],pd.Series(float('nan'),index=archive.index)) for field,column in REQ_MAP.items()}
 prim['legacy_net_tackles']=raw_net(pindex.pl_total_tackle,pindex.pl_won_tackle)
 prim['clearances_blocks_interceptions']=pindex[['pl_total_clearance','pl_outfielder_block','pl_interception']].sum(axis=1,min_count=3)
 event_bad={}
 for field,columns in [('total_tackles',['totalTackle']),('won_tackles',['wonTackle']),('legacy_net_tackles',['totalTackle','wonTackle']),('goal_line_clearances',['clearanceOffLine'])]:
  bad=ed[ed.field.isin(columns)&ed.comparison.eq('explicit_conflict')]
  event_bad[field]=pd.MultiIndex.from_frame(bad[KEY].drop_duplicates())
 for field in set(REQ_MAP)|{'legacy_net_tackles','clearances_blocks_interceptions'}:
  mask=req.field.eq(field)&~protected;idx=req.index[mask];keys=pd.MultiIndex.from_frame(req.loc[idx,KEY])
  primary=prim[field].reindex(keys).to_numpy();req.loc[idx,'primary_audit_value']=primary
  conflict=req.loc[idx,'value'].notna()&pd.Series(primary,index=idx).notna()&req.loc[idx,'value'].ne(primary)
  ii=idx[conflict];req.loc[ii,['value','status','quality_status']]=[float('nan'),'external_conflict','explicit_primary_conflict']
  if field in event_bad:
   ii=idx[keys.isin(event_bad[field])]
   req.loc[ii,['value','status','quality_status']]=[float('nan'),'external_conflict','explicit_event_conflict']
  equal=req.loc[idx,'value'].notna()&pd.Series(primary,index=idx).notna()&req.loc[idx,'value'].eq(primary)&req.loc[idx,'status'].eq('external_available')
  ii=idx[equal];req.loc[ii,'status']='external_checked';req.loc[ii,'quality_status']='checked_against_primary_same_opta_ancestry'
 req['is_open']=req.status.isin(OPEN)
 req['needs_external_quality_review']=req.status.eq('external_available')
 req['is_zero']=req.value.eq(0)&~req.is_open
 # Preserve exact FPL and keeper cells; assert before writing anything final.
 before=read(S/'fpl_authority/requirements.csv.gz')
 assert req.loc[protected,'value'].equals(before.loc[protected,'value'])
 assert req.loc[protected,'status'].equals(before.loc[protected,'status'])
 save(req,'requirements.csv.gz')
 save(req[req.is_open],'remaining_fields.csv.gz')
 save(req[req.needs_external_quality_review],'external_quality_queue.csv.gz')
 save(req[req.status.eq('external_checked')],'primary_checked_values.csv.gz')
 fields=req.groupby('field',sort=True).agg(required=('field','size'),open_cells=('is_open','sum'),external_quality_cells=('needs_external_quality_review','sum'))
 for status in sorted(req.status.unique()):fields[status]=req.status.eq(status).groupby(req.field).sum()
 fields['explicit_or_derived_zero']=req.is_zero.groupby(req.field).sum()
 save(fields.reset_index(),'field_summary.csv')
 save(req.groupby(['season','field','status'],sort=True).size().rename('cells').reset_index(),'field_summary_by_season.csv')
 pending=req[req.is_open]
 players=pending.groupby(KEY).agg(name=('name','first'),open_fields=('field','size'),fields=('field',lambda x:'|'.join(sorted(x)))).reset_index()
 save(players,'remaining_player_matches.csv.gz')
 save(pending.groupby(['season','fixture']).agg(date=('date','first'),home=('home','first'),away=('away','first'),open_fields=('field','size'),unique_affected_player_matches=('code','nunique')).reset_index(),'match_summary.csv')
 save(players.groupby(['season','code']).agg(name=('name','first'),open_fields=('open_fields','sum'),unique_affected_player_matches=('fixture','size')).reset_index(),'player_summary.csv')
 save(req.groupby(['field','previous_status','status']).size().rename('cells').reset_index(),'transitions.csv')
 work=req[req.is_open|req.needs_external_quality_review]
 save(work.groupby(KEY).agg(name=('name','first'),open_fields=('is_open','sum'),external_quality_fields=('needs_external_quality_review','sum')).reset_index(),'all_work_player_matches.csv.gz')
 # Quality audit of available source aggregates against authoritative 2025/26 FPL.
 fpl=read(S/'fpl_authority/fpl_baseline.csv.gz').set_index(KEY)
 c=archive.loc[archive.index.get_level_values('season')=='2025-26'].copy()
 c['archive_cbi_explicit']=c[['totalClearance','outfielderBlock','interception']].sum(axis=1,min_count=3)
 fq=[]
 for source,target in [('archive_cbi_explicit','clearances_blocks_interceptions'),('totalTackle','tackles'),('ballRecovery','recoveries'),('saves','saves')]:
  d=c[['name',source]].rename(columns={source:'archive'});d['field']=target;d['fpl']=fpl[target].reindex(d.index);d['comparison']=compare(d.archive,d.fpl);fq.append(d.reset_index())
 fq=pd.concat(fq,ignore_index=True);save(fq,'fpl_2025_comparisons.csv.gz')
 save(fq.groupby(['field','comparison']).size().rename('cells').reset_index(),'fpl_2025_comparison_summary.csv')
 # Published official season totals are extra controls, not a licence to assign a difference to a match.
 published=json.loads((P/'inputs/published_season_controls.json').read_text())
 season_totals=pd.DataFrame(published['rows'])
 totals=c.groupby(level='code').timesTackled.sum(min_count=1)
 season_totals['archive_match_sum']=season_totals.code.map(totals)
 season_totals['published_minus_archive']=season_totals.value-season_totals.archive_match_sum
 api=pd.DataFrame(json.loads((P/'inputs/primary_season_checks.json').read_text())).set_index('code')
 season_totals['primary_season_total']=season_totals.code.map(api.primary_season_times_tackled)
 season_totals['primary_match_sum']=season_totals.code.map(targeted.groupby('code').pl_times_tackled.sum(min_count=1))
 season_totals['resolution']='published_agrees'
 season_totals.loc[season_totals.published_minus_archive.ne(0),'resolution']='aggregate_difference_unlocated'
 mask=season_totals.primary_season_total.eq(season_totals.archive_match_sum)&season_totals.published_minus_archive.ne(0)
 season_totals.loc[mask,'resolution']='current_primary_agrees_archive_published_snapshot_differs'
 located=comp[comp.field.eq('timesTackled')&comp.control_scope.eq('targeted_after_aggregate_difference')&comp.comparison.eq('explicit_conflict')]
 for code,g in located.groupby('code'):
  season_totals.loc[season_totals.code.eq(code),'resolution']='located_primary_match_conflict'
  season_totals.loc[season_totals.code.eq(code),'conflict_fixtures']='|'.join(str(int(x)) for x in g.fixture)
 save(season_totals,'official_season_comparisons.csv')
 # Report line-clearance omission diagnostics, explicitly unapproved as zero evidence.
 line=ed[(ed.field=='clearanceOffLine')&ed.season.ne('2026-27')]
 line_result=dict(explicit_pairs=int((line.archive.notna()&line.event_candidate.notna()).sum()),explicit_equal=int(line.comparison.eq('equal_explicit').sum()),explicit_conflicts=int(line.comparison.eq('explicit_conflict').sum()),omitted_stat_event_positive=int((line.archive.isna()&line.event_candidate.gt(0)).sum()),omitted_stat_event_zero_candidate=int((line.archive.isna()&line.event_candidate.eq(0)).sum()),zeros_approved=0,reason='Matching positives do not establish complete negative reporting; zero event counts are diagnostic only.')
 (P/'line_clearance_audit.json').write_text(json.dumps(line_result,indent=2)+'\n')
 result=dict(steps_1_and_2_audit_completed=True,historical_population=77280,projected_rows=len(archive),historical_linked=int((linked&(archive.index.get_level_values('season')!='2026-27')).sum()),fresh_controls=28,targeted_controls=len(targeted),
  old_open_cells=int(before.is_open.sum()),open_cells=int(req.is_open.sum()),unique_affected_player_matches=len(players),
  newly_available_cells=int((before.is_open&~req.is_open).sum()),newly_flagged_conflict_cells=int((~before.is_open&req.is_open).sum()),
  external_quality_cells=int(req.needs_external_quality_review.sum()),external_quality_unique_player_matches=len(req.loc[req.needs_external_quality_review,KEY].drop_duplicates()),
  unique_open_or_external_quality_player_matches=len(work[KEY].drop_duplicates()),checked_against_primary_cells=int(req.status.eq('external_checked').sum()),status_counts=req.status.value_counts().to_dict(),
  fresh_explicit_comparisons=int((comp.control_scope.eq('fresh_prespecified')&comp.comparison.isin(['equal_explicit','explicit_conflict'])).sum()),fresh_explicit_conflicts=int((comp.control_scope.eq('fresh_prespecified')&comp.comparison.eq('explicit_conflict')).sum()),
  published_season_total_differences=int(season_totals.published_minus_archive.ne(0).sum()),inferred_sparse_zeros=0,legacy_net_clipping_qualified=False,independent_provider_validation=False,new_scoring_holdout=False,
  all_available_external_cells_individually_verified=False,fpl_values_modified=False,keeper_values_modified=False,locked_labels_modified=False,full_historical_harmonization_complete=False,cost_nok=0)
 (P/'findings.json').write_text(json.dumps(result,indent=2)+'\n')
 for path in list(P.glob('*.py'))+list((P/'inputs').glob('*.json'))+[P/'inputs/kante_net_example.csv']+[P/'definitions.json',P/'control_plan.csv',P/'control_protocol.json',P/'primary_sources.json',P/'season_check_sources.json',P/'targeted_sources.json']:
  if path.exists():HASHES[str(path.relative_to(S))]=hashlib.sha256(path.read_bytes()).hexdigest()
 sources=sum([json.loads((P/name).read_text()) for name in ['primary_sources.json','season_check_sources.json','targeted_sources.json']],[])
 for source in sources:
  path=P/source['file'];digest=hashlib.sha256(path.read_bytes()).hexdigest()
  if digest!=source['sha256']:raise ValueError('Primary raw drift')
  HASHES[str(path.relative_to(S))]=digest
 (P/'manifest.json').write_text(json.dumps(dict(inputs=HASHES),indent=2,sort_keys=True)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
