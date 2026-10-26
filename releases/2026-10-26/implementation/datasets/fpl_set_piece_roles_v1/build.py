"""Reported hierarchies and conservative absence scenarios; never actual takers."""
import collections,itertools
from common import *
OUT_STATUSES={'i','s','n','u'}
def all_out(group):
 if not group:return None
 # A doubtful player remains a possible participant and blocks confirmed absence.
 if any(p['status_known'] and p['status'] in ['a','d'] for p in group):return False
 if any(not p['status_known'] for p in group):return None
 return all(p['status'] in OUT_STATUSES for p in group)
def role_features(own,team,role):
 base='sp_'+role+'_';out={};known=bool(own and own['roles'][role]['known']);entry=own['roles'][role] if own else None;rank=entry['order'] if known else None
 names=['listed_order','listed_for_role','listed_first_choice','reported_text','team_listed_players','team_first_choice_players','team_schema_complete','team_has_tied_orders','team_has_order_gaps','same_rank_other_players','ranks_ahead_complete','listed_players_ahead','ahead_reported_available','ahead_reported_doubtful','ahead_reported_unavailable','ahead_departure_reports','ahead_status_unknown','all_listed_ahead_reported_out','first_choice_absence_reported','first_choice_status_uncertain','potential_promotion','top_remaining_listed_candidate','top_remaining_tied','unique_top_remaining_candidate']
 out[base+'source_known']=known
 if not known:return dict(out,**{base+n:None for n in names})
 listed=[p for p in team if p['roles'][role]['known'] and p['roles'][role]['order'] is not None];orders=[p['roles'][role]['order'] for p in listed];primary=[p for p in listed if p['roles'][role]['order']==1]
 schema_complete=all(p['roles'][role]['known'] for p in team);tied=len(orders)!=len(set(orders));gaps=bool(orders and set(orders)!=set(range(1,max(orders)+1)))
 out.update({base+'listed_order':rank,base+'listed_for_role':rank is not None,base+'listed_first_choice':rank==1,base+'reported_text':entry['text'],base+'team_listed_players':len(listed),base+'team_first_choice_players':len(primary),base+'team_schema_complete':schema_complete,base+'team_has_tied_orders':tied,base+'team_has_order_gaps':gaps,base+'first_choice_absence_reported':all_out(primary) if schema_complete else None,base+'first_choice_status_uncertain':any(not p['status_known'] or p['status']=='d' for p in primary) if primary else None})
 own_names=['same_rank_other_players','ranks_ahead_complete','listed_players_ahead','ahead_reported_available','ahead_reported_doubtful','ahead_reported_unavailable','ahead_departure_reports','ahead_status_unknown','all_listed_ahead_reported_out','potential_promotion','top_remaining_listed_candidate','top_remaining_tied','unique_top_remaining_candidate']
 if rank is None:return dict(out,**{base+n:None for n in own_names})
 ahead=[p for p in listed if p['roles'][role]['order']<rank];same=[p for p in listed if p['code']!=own['code'] and p['roles'][role]['order']==rank];complete=set(range(1,rank))<={p['roles'][role]['order'] for p in ahead};ahead_out=all_out(ahead)
 out.update({base+'same_rank_other_players':len(same),base+'ranks_ahead_complete':complete,base+'listed_players_ahead':len(ahead),base+'ahead_reported_available':sum(p['status_known'] and p['status']=='a' for p in ahead),base+'ahead_reported_doubtful':sum(p['status_known'] and p['status']=='d' for p in ahead),base+'ahead_reported_unavailable':sum(p['status_known'] and p['status'] in ['i','s','n'] and not p['departure'] for p in ahead),base+'ahead_departure_reports':sum(p['status_known'] and p['departure'] for p in ahead),base+'ahead_status_unknown':sum(not p['status_known'] for p in ahead),base+'all_listed_ahead_reported_out':ahead_out})
 if not own['status_known'] or own['status']=='d':top=None
 elif own['status'] in OUT_STATUSES:top=False
 elif not schema_complete or not complete:top=None
 elif rank==1:top=True
 else:top=ahead_out
 if rank==1:promotion=False
 elif own['status_known'] and own['status'] in OUT_STATUSES:promotion=False
 else:promotion=top
 tie=None
 if top is True:
  if any(p['status_known'] and p['status'] in ['a','d'] for p in same):tie=True
  elif any(not p['status_known'] for p in same):tie=None
  else:tie=False
 unique=(not tie) if top is True and tie is not None else False if top is False else None
 out.update({base+'potential_promotion':promotion,base+'top_remaining_listed_candidate':top,base+'top_remaining_tied':tie,base+'unique_top_remaining_candidate':unique})
 return out
def features(own,team,a):
 out=dict(sp_forecast_at=a['forecast_at'],sp_source_known=bool(own and any(x['known'] for x in own['roles'].values())),sp_source_tier='git_timestamp_proxy',sp_strict_historical_qualified=False,sp_source_format=a['format'],sp_source_age_hours=float(a['snapshot_age_hours']) if a['snapshot_age_hours'] else None,sp_source_commit=a['source_commit'],sp_source_sha256=a['source_sha256'],sp_source_url=a['source_url'],sp_snapshot_team=own['team'] if own else None,sp_own_reported_status=own['status'] if own and own['status_known'] else None,sp_own_status_known=bool(own and own['status_known']),sp_actual_taker_confirmed=False,sp_promotion_is_scenario_not_confirmed_role=True,sp_role_list_is_exhaustive=False,sp_role_update_time_known=False,sp_scope='FPL_registered_snapshot_football_players_only',sp_source_reason=a['eligibility_reason'] if not truth(a['source_eligible']) else 'player_missing_or_invalid_in_source' if own is None else 'role_schema_absent_or_invalid' if not any(x['known'] for x in own['roles'].values()) else 'eligible_reported_metadata')
 for role in ROLES:out.update(role_features(own,team,role))
 return out
def season_sources(season,audits,status_index,input_hashes):
 frames={};exports=[];origin_audit=[]
 for a in sorted([x for x in audits if x['season']==season],key=lambda x:int(x['round'])):
  gw=int(a['round']);key=season,gw;frame={};raw,teams=raw_players(a);path=R/a['source_file'];assert sha(path)==a['source_sha256'];input_hashes[a['source_file']]=sha(path);eligible=truth(a['source_eligible']);source_at=dt(a['snapshot_at_proxy']);nonplayers=0
  for e in raw:
   if int(float(e['element_type'])) not in [1,2,3,4]:nonplayers+=1;continue
   code=num(e['code']);av=status_index[(season,gw,code)];assert num(e['id'])==av['element'] and teams[num(e['team'])]==av['team_name'];news_at=None if null(e.get('news_added')) else dt(e['news_added']);record_ok=eligible and (news_at is None or news_at<=source_at)
   roles={}
   for role,prefix in ROLES.items():
    present=prefix+'_order' in e;rank,valid=order(e.get(prefix+'_order'));text=e.get(prefix+'_text');roles[role]=dict(known=record_ok and present and valid,order=rank if record_ok and present and valid else None,text='' if null(text) else str(text),field_present=present,rank_valid=valid,raw_order_json=json.dumps(e[prefix+'_order']) if present else '')
   person=dict(code=code,element=av['element'],name=e['web_name'],team=av['team_name'],status=av['status'],status_known=truth(av['known']),departure=truth(av['departure']),roles=roles)
   if eligible:frame[code]=person
   exported=dict(season=season,round=gw,code=code,element=av['element'],name=e['web_name'],team=av['team_name'],source_eligible=eligible,record_time_valid=record_ok,status=av['status'],status_known=person['status_known'],departure=person['departure'],forecast_at=a['forecast_at'],snapshot_at_proxy=a['snapshot_at_proxy'],source_file=a['source_file'],source_sha256=a['source_sha256'])
   for role,x in roles.items():
    for name,value in x.items():exported[role+'_'+name]=value
   exports.append(exported)
  frames[gw]=frame;origin_audit.append(dict(season=season,round=gw,forecast_at=a['forecast_at'],source_eligible=eligible,eligibility_reason=a['eligibility_reason'],source_format=a['format'],source_file=a['source_file'],source_sha256=a['source_sha256'],source_players=len(frame),non_player_assets_excluded=nonplayers,**{role+'_schema_players':sum(p['roles'][role]['known'] for p in frame.values()) for role in ROLES}))
 return frames,exports,origin_audit
def main():
 OUT.mkdir(exist_ok=True);code_hash=sha(P/'build.py');audits=list(read(AV/'snapshot_audit.csv'));audit_index={(r['season'],int(r['round'])):r for r in audits};status_index={(r['season'],int(r['round']),r['code']):r for r in read(AV/'source_player_status.csv.gz')};targets=collections.defaultdict(list)
 for row in read(MASTER/'player_matches.csv.xz'):targets[row['season']].append(dict(season=row['season'],round=int(row['round']),fixture=num(row['fixture']),code=num(row['code'])))
 input_hashes={str(p.relative_to(R)):sha(p) for p in [MASTER/'player_matches.csv.xz',MASTER/'manifest.json',AV/'snapshot_audit.csv',AV/'source_player_status.csv.gz',AV/'metadata_verification.json',AV/'manifest.json',P/'common.py']};coverage=[];all_audit=[];fields=None
 with lzma.open(P/'player_match_context.csv.xz','wt',newline='',preset=3) as mf,lzma.open(P/'player_round_context.csv.xz','wt',newline='',preset=3) as rf,lzma.open(OUT/'player_matches.csv.xz','wt',newline='',preset=3) as of,gzip.open(P/'source_roles.csv.gz','wt',newline='') as sf:
  mw=rw=ow=sw=None
  for season,originals in itertools.groupby(read(MASTER/'player_matches.csv.xz'),lambda r:r['season']):
   frames,source_rows,source_audit=season_sources(season,audits,status_index,input_hashes);all_audit+=source_audit
   for row in source_rows:
    if sw is None:sw=csv.DictWriter(sf,fieldnames=list(row));sw.writeheader()
    sw.writerow(row)
   teams=collections.defaultdict(list)
   for gw,frame in frames.items():
    for p in frame.values():teams[(gw,p['team'])].append(p)
   cache={};index={};known=0;promotions=collections.Counter();listed_counts=collections.Counter()
   for target in targets[season]:
    gw=target['round'];code=target['code'];key=gw,code
    if key not in cache:
     own=frames[gw].get(code);team=teams[(gw,own['team'])] if own else [];c=features(own,team,audit_index[(season,gw)]);cache[key]=c;rr=dict(season=season,round=gw,code=code,**c)
     if rw is None:rw=csv.DictWriter(rf,fieldnames=list(rr));rw.writeheader();fields=list(c)
     rw.writerow(rr)
     for role in ROLES:
      promotions[role]+=c['sp_'+role+'_potential_promotion'] is True;listed_counts[role]+=c['sp_'+role+'_listed_for_role'] is True
    c=cache[key];mr=dict(target,**c)
    if mw is None:mw=csv.DictWriter(mf,fieldnames=list(mr));mw.writeheader()
    mw.writerow(mr);index[(target['fixture'],code)]=c;known+=c['sp_source_known']
   count=0
   for row in originals:
    c=index[(num(row['fixture']),num(row['code']))];assert dt(c['sp_forecast_at'])==dt(row['av_forecast_at']);merged=dict(row,**c)
    if ow is None:ow=csv.DictWriter(of,fieldnames=list(merged));ow.writeheader()
    ow.writerow(merged);count+=1
   coverage.append(dict(season=season,master_rows=count,player_round_rows=len(cache),source_known_match_rows=known,source_unknown_match_rows=count-known,**{role+'_listed_player_rounds':listed_counts[role] for role in ROLES},**{role+'_potential_promotion_player_rounds':promotions[role] for role in ROLES}))
   print('Set-piece roles',season,count,'PL rows',known,'with role source',flush=True)
 assert sha(P/'build.py')==code_hash;input_hashes[str((P/'build.py').relative_to(R))]=code_hash;write('coverage.csv',coverage);write('source_audit.csv',all_audit);(P/'input_hashes.json').write_text(json.dumps(input_hashes,indent=2));(P/'summary.json').write_text(json.dumps(dict(master_rows=sum(r['master_rows'] for r in coverage),source_known_match_rows=sum(r['source_known_match_rows'] for r in coverage),source_unknown_match_rows=sum(r['source_unknown_match_rows'] for r in coverage),set_piece_columns=fields,coverage=coverage,model_fits=0),indent=2))
if __name__=='__main__':main()
