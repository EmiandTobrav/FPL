"""Apply qualified conservation and subset bounds; keep all raw sources intact."""
from pathlib import Path
import argparse,hashlib,json
import pandas as pd
from rules import residual,zero_subset,signed_net
from probe import audit,MAP
P=Path(__file__).resolve().parent;S=P.parent;KEY=['season','fixture','code']
OPEN={'missing_data','external_conflict','rule_recalculation','fpl_extract_exception'}
FIELD={'wonTackle':'won_tackles','wasFouled':'fouls_won','ontargetScoringAtt':'shots_on_target','clearanceOffLine':'goal_line_clearances'}
def read(p):return pd.read_csv(p,low_memory=False)
def save(d,name):d.to_csv(P/name,index=False,compression={'method':'gzip','mtime':0} if name.endswith('.gz') else None)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--stage',default='full',choices=['pilot','full']);args=ap.parse_args()
 frozen=json.loads((P/'protocol.json').read_text())['frozen']
 for name,digest in frozen.items():
  if hashlib.sha256((P/name).read_bytes()).hexdigest()!=digest:raise ValueError('Frozen method changed')
 for cohort in ['pilot','holdout']:
  control=read(P/f'{cohort}_conservation.csv')
  if control.reason.isin(['aggregate_conflict','unallocated_positive_residual']).any():raise ValueError('Control mapping failed')
 source=read(P/'inputs/source_players.csv.gz')
 if source.groupby(['match_id','team_position']).team_id.nunique().gt(1).any():raise ValueError('Ambiguous team side')
 teams=read(P/f'{args.stage}_team_totals.csv')
 conservation=audit(teams,source);save(conservation,'conservation.csv.gz')
 meta=read(S/'delta_input_audit/inputs/archive_projection.csv.gz')
 meta=meta[meta.season.ne('2026-27')].set_index(KEY)
 fm=read(P/'inputs/fotmob_total_tackles.csv.gz').set_index(KEY)['matchstats.headers.tackles']
 ev=read(S/'delta_input_audit/inputs/event_counts.csv.gz').set_index(['match_id','player_id'])
 positive=read(P/'inputs/positive_event_evidence.csv.gz').set_index(['match_id','player_id'])
 before=read(S/'assist_reconciliation/requirements.csv.gz');req=before.copy()
 bad_total_keys=set(map(tuple,before.loc[before.field.eq('total_tackles')&before.is_open,KEY].to_numpy()))
 req['bulk_previous_status']=req.status;req['bulk_previous_value']=req.value
 req['bulk_method']='';req['bulk_parent_value']=float('nan');req['bulk_group_id']=''
 if req.duplicated(KEY+['field']).any():raise ValueError('Duplicate requirement key')
 identities=meta.reset_index().dropna(subset=['match_id','player_id'])
 if identities.duplicated(['match_id','player_id']).any():raise ValueError('Ambiguous source-to-FPL link')
 # Preserve every explicit source counter, including bench/non-FPL participants in sums.
 enriched=source.merge(identities[KEY+['match_id','player_id']],on=['season','fixture','match_id','player_id'],how='left',validate='one_to_one')
 groupmap=conservation.set_index(['match_id','team_id','field'])
 look={};evidence=[];rejected=[]
 for r in enriched.to_dict('records'):
  if pd.isna(r['code']):continue
  key=(r['season'],int(r['fixture']),int(r['code']))
  for src,target in FIELD.items():
   gkey=(r['match_id'],r['team_id'],src)
   if pd.notna(r[src]) or gkey not in groupmap.index:continue
   g=groupmap.loc[gkey]
   if not g.zero_certified:continue
   # A known positive event is contrary evidence, even if the player counter is omitted.
   ekey=(r['match_id'],r['player_id']);eventfield={'wonTackle':'event_won_tackle','clearanceOffLine':'event_line_markers'}.get(src)
   contrary=eventfield and ekey in ev.index and ev.loc[ekey,eventfield]>0
   posfield={'wasFouled':'positive_foul_won','ontargetScoringAtt':'positive_on_target'}.get(src)
   contrary=contrary or (posfield and ekey in positive.index and positive.loc[ekey,posfield]>0)
   if contrary:
    rejected.append(dict(zip(KEY,key),field=target,reason='positive_event_veto'));continue
   gid=f"{r['season']}:{int(r['fixture'])}:{r['team_id']}:{src}"
   proof=dict(value=0,method='explicit_team_total_exhausted',parent_value=g.total,group_id=gid,source_field=src)
   look[(*key,target)]=proof;evidence.append(dict(zip(KEY,key),field=target,**proof))
 # Explicit total-tackle zero is a logical subset proof, independent of an omitted won field.
 tackle_mapping=[]
 for key,r in meta.iterrows():
  total=float(fm.get(key,float('nan')));rawtotal=r.totalTackle
  if pd.notna(total) and pd.notna(rawtotal):tackle_mapping.append(dict(zip(KEY,key),fotmob_total=total,archive_total=rawtotal,agrees=total==rawtotal))
  if key[0]=='2025-26' or key in bad_total_keys or zero_subset(total) is None:continue
  if pd.notna(rawtotal) and rawtotal!=0:continue
  if pd.notna(r.wonTackle) and r.wonTackle!=0:continue
  ekey=(r.match_id,r.player_id)
  if ekey in ev.index and ev.loc[ekey,'event_total_tackle']>0:continue
  proof=dict(value=0,method='explicit_total_tackles_zero_subset',parent_value=0,group_id=':'.join(map(str,key))+':total_tackles',source_field='FotMob explicit matchstats.headers.tackles')
  look[(*key,'won_tackles')]=proof
 save(pd.DataFrame(tackle_mapping),'tackle_mapping_checks.csv.gz')
 save(pd.DataFrame(rejected,columns=KEY+['field','reason']),'rejected_derived_candidates.csv.gz')
 # Only close missing cells. Existing conflicts and all closed cells remain exactly as before.
 lookup_index=req.set_index(KEY+['field']).index
 changes=[]
 for field in ['won_tackles','fouls_won','shots_on_target','goal_line_clearances']:
  for i,r in req[req.field.eq(field)&req.status.eq('missing_data')].iterrows():
   key=tuple(r[k] for k in KEY);proof=look.get((*key,field))
   if proof is None:continue
   for col,val in [('value',proof['value']),('status','external_derived'),('quality_status','qualified_conservation_or_subset_shared_opta'),('bulk_method',proof['method']),('bulk_parent_value',proof['parent_value']),('bulk_group_id',proof['group_id']),('provenance','bulk_reconciliation/derived_values.csv.gz + conservation.csv.gz')]:req.at[i,col]=val
   changes.append(dict(zip(KEY,key),field=field,**proof))
 # Net tackles uses explicit/qualified won plus a compatible explicit total; signed result retained.
 won=req[req.field.eq('won_tackles')].set_index(KEY)
 for i,r in req[req.field.eq('legacy_net_tackles')&req.status.eq('missing_data')].iterrows():
  key=tuple(r[k] for k in KEY)
  if key in bad_total_keys or key not in won.index or won.loc[key,'status'] in OPEN:continue
  w=won.loc[key,'value'];m=meta.loc[key];ft=fm.get(key);at=m.totalTackle
  # Cross-source positive disagreements are quarantined, not arbitrated by priority.
  if pd.notna(at) and pd.notna(ft) and at!=ft:continue
  total=at if pd.notna(at) else ft
  v=signed_net(float(total),float(w))
  if v is None:continue
  proof=dict(value=v,method='signed_net_from_qualified_won_and_total',parent_value=total,group_id=':'.join(map(str,key))+':tackle_pair',source_field='totalTackle/FotMob total + resolved won_tackles')
  for col,val in [('value',v),('status','external_derived'),('quality_status','qualified_counter_not_legacy_bps_clipping'),('bulk_method',proof['method']),('bulk_parent_value',total),('bulk_group_id',proof['group_id']),('provenance','bulk_reconciliation/derived_values.csv.gz')]:req.at[i,col]=val
  changes.append(dict(zip(KEY,key),field='legacy_net_tackles',**proof))
 req['is_open']=req.status.isin(OPEN);req['is_zero']=req.value.eq(0)&~req.is_open
 # Derived external inputs still carry source quality caveats; no blanket primary-player approval.
 req.loc[req.status.eq('external_derived'),'needs_external_quality_review']=True
 untouched=~before.status.eq('missing_data')|~before.field.isin(list(FIELD.values())+['legacy_net_tackles'])
 pd.testing.assert_frame_equal(before.loc[untouched],req.loc[untouched,before.columns],check_dtype=False)
 changed=before.is_open&~req.is_open
 if int(changed.sum())!=len(changes):raise ValueError('Change accounting drift')
 save(pd.DataFrame(changes),'derived_values.csv.gz');save(req,'requirements.csv.gz');pending=req[req.is_open];save(pending,'remaining_fields.csv.gz')
 fields=req.groupby('field').agg(required=('field','size'),open_cells=('is_open','sum'),quality_cells=('needs_external_quality_review','sum'))
 for status in sorted(req.status.unique()):fields[status]=req.status.eq(status).groupby(req.field).sum()
 fields['newly_available']=changed.groupby(req.field).sum();save(fields.reset_index(),'field_summary.csv')
 save(req.groupby(['season','field','status']).size().rename('cells').reset_index(),'field_summary_by_season.csv')
 players=pending.groupby(KEY).agg(name=('name','first'),open_fields=('field','size'),fields=('field',lambda s:'|'.join(sorted(s)))).reset_index();save(players,'remaining_player_matches.csv.gz')
 save(players.groupby(['season','code']).agg(name=('name','first'),open_fields=('open_fields','sum'),unique_affected_player_matches=('fixture','size')).reset_index(),'player_summary.csv')
 # Inventory completeness is a necessary gate, not proof that the unqualified scorer is ready.
 prior=before.groupby(KEY).is_open.sum().rename('previous_open_fields');now=req.groupby(KEY).is_open.sum().rename('open_fields')
 quality=req.groupby(KEY).needs_external_quality_review.sum().rename('quality_fields')
 readiness=pd.concat([prior,now,quality],axis=1).reset_index();readiness['inputs_available']=readiness.open_fields.eq(0);readiness['newly_inputs_available']=readiness.inputs_available&readiness.previous_open_fields.gt(0);readiness['scoring_qualified']=False
 save(readiness,'player_match_readiness.csv.gz')
 matches=readiness.groupby(['season','fixture']).agg(player_matches=('code','size'),open_fields=('open_fields','sum'),previous_open_fields=('previous_open_fields','sum'),unique_affected_player_matches=('open_fields',lambda v:int(v.gt(0).sum())),quality_fields=('quality_fields','sum')).reset_index()
 matches['inputs_available']=matches.open_fields.eq(0);matches['newly_inputs_available']=matches.inputs_available&matches.previous_open_fields.gt(0);matches['bonus_ready']=False
 save(matches,'match_readiness.csv');save(matches,'match_summary.csv')
 save(req.groupby(['field','bulk_previous_status','status']).size().rename('cells').reset_index(),'transitions.csv')
 # Whole-population structural checks replace repetitive individual review.
 available=~req.is_open
 invalid=available&(req.value.isna()|req.value.mod(1).ne(0))
 invalid|=available&req.value.lt(0)&~req.field.isin(['legacy_net_tackles','historical_bps'])
 if invalid.any():raise ValueError('Invalid available counter')
 qa=req.groupby(['season','field']).agg(cells=('field','size'),open_cells=('is_open','sum'),source_quality_cells=('needs_external_quality_review','sum')).reset_index()
 qa['automated_population_checks']='unique_identity|explicit_or_derived_value|integer_domain|protected_source_preservation'
 qa['next_review_unit']='field_definition_and_season; individual exceptions only'
 save(qa,'quality_review_groups.csv')
 (P/'automated_quality.json').write_text(json.dumps(dict(required_cells=len(req),duplicate_keys=int(req.duplicated(KEY+['field']).sum()),invalid_available_counters=int(invalid.sum()),protected_cells_checked=int(untouched.sum()),review_groups=len(qa),all_available_cells_individually_primary_verified=False),indent=2)+'\n')
 q=req.needs_external_quality_review;work=req.is_open|q
 save(req[q],'external_quality_queue.csv.gz')
 save(req[work].groupby(KEY).agg(name=('name','first'),open_fields=('is_open','sum'),quality_fields=('needs_external_quality_review','sum')).reset_index(),'all_work_player_matches.csv.gz')
 summary=dict(stage=args.stage,old_open_cells=int(before.is_open.sum()),newly_available_cells=int(changed.sum()),open_cells=int(req.is_open.sum()),old_unique_affected_player_matches=len(before.loc[before.is_open,KEY].drop_duplicates()),unique_affected_player_matches=len(players),newly_available_by_field=req.loc[changed,'field'].value_counts().to_dict(),source_team_field_groups=len(conservation),conservation_group_status=conservation.reason.value_counts().to_dict(),available_player_matches=int(readiness.inputs_available.sum()),newly_available_player_matches=int(readiness.newly_inputs_available.sum()),available_complete_fixtures=int(matches.inputs_available.sum()),newly_available_complete_fixtures=int(matches.newly_inputs_available.sum()),bonus_ready_fixtures=0,quality_cells=int(q.sum()),quality_player_matches=len(req.loc[q,KEY].drop_duplicates()),unique_open_or_quality_player_matches=len(req.loc[work,KEY].drop_duplicates()),status_counts=req.status.value_counts().to_dict(),newly_available_not_individually_primary_checked=True,legacy_net_clipping_qualified=False,independent_provider_validation=False,raw_fpl_modified=False,approved_keeper_modified=False,locked_scoring_modified=False,full_harmonization_complete=False,cost_nok=0)
 (P/'findings.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2),flush=True)
 inputs=[S/'assist_reconciliation/requirements.csv.gz',S/'delta_input_audit/inputs/archive_projection.csv.gz',S/'delta_input_audit/inputs/event_counts.csv.gz',P/'inputs/source_players.csv.gz',P/'inputs/fotmob_total_tackles.csv.gz',P/'inputs/positive_event_evidence.csv.gz',P/'inputs/positive_event_source.json',P/'definitions.json',P/'pilot_conservation.csv',P/'holdout_conservation.csv',P/f'{args.stage}_sources.json',P/f'{args.stage}_team_totals.csv',P/'protocol.json']+list(P.glob('*.py'))
 (P/'manifest.json').write_text(json.dumps({str(p.relative_to(S)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},indent=2)+'\n')
if __name__=='__main__':main()
