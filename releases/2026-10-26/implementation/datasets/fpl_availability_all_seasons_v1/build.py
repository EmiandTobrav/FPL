"""All-season availability joins with the pilot semantics and explicit gaps."""
import collections,csv,itertools,json,lzma
from common import *
def empty(v):return v is None or str(v) in ['', 'None','nan','null']
def optional_date(v):return None if empty(v) else dt(str(v))
def players(row):
 path=R/row['source_file']
 if row['format']=='none' or not path.exists():return [],{},None,'unknown',False,'source_missing'
 if row['format']=='bootstrap':
  data=json.loads(lzma.decompress(path.read_bytes()));event=next((e for e in data['events'] if int(e['id'])==row['round']),None);teams={num(t['id']):t['name'] for t in data['teams']}
  actual=dt(event['deadline_time']) if event else None;binding='next' if event and event['is_next'] else 'this' if event and event['is_current'] else 'unknown'
  bound=bool(event and binding!='unknown' and (not row['actual_deadline'] or actual==dt(row['actual_deadline'])))
  return data['elements'],teams,actual,binding,bound,'bootstrap_event_metadata'
 teams={num(r['id']):r['name'] for r in read(R/'FPL_training_dataset/research/current/project/data'/f'{row["season"]}_teams.csv.gz')}
 return list(read(path)),teams,None,'unbound_csv',False,'status_only_no_round_binding'
def frame(row,previous):
 at=dt(row['selection_cutoff']);source_at=dt(row['source_time']) if row['source_time'] else None;path=R/row['source_file'] if row['source_file'] else None;data,teams,actual,binding,bound,source_note=players(row)
 age=(at-source_at).total_seconds()/3600 if source_at else None
 source_ok=bool(data and source_at and source_at<at and age<=24 and (row['format']=='players_csv' or bound) and (actual is None or source_at<actual))
 why='eligible_git_proxy' if source_ok else 'source_missing' if not data else 'source_not_before_cutoff' if source_at>=at else 'source_older_than_24h' if age>24 else 'event_binding_unresolved'
 output={};nonplayers=0;invalid=0;digest=sha(path) if path and path.exists() else '';seen_ids=set()
 for e in data:
  if empty(e.get('element_type')) or int(float(e['element_type'])) not in [1,2,3,4]:nonplayers+=1;continue
  code=num(e['code']);element=num(e['id']);assert code not in output and element not in seen_ids;seen_ids.add(element)
  team=teams[num(e['team'])];status='' if empty(e.get('status')) else str(e['status']);news='' if empty(e.get('news')) else str(e['news']);added=optional_date(e.get('news_added'));valid=source_ok and status in ['a','d','i','s','n','u'] and (added is None or added<=source_at)
  if not valid:invalid+=1
  reason=pilot.reason(news);departure=status=='u' or (status=='n' and reason=='transfer_or_loan');prior=previous.get(code);consecutive=bool(prior and prior['round']==row['round']-1 and prior['known']);core=valid and status in ['a','d','i','s','n'] and not departure
  target_chance=e.get('chance_of_playing_next_round' if binding=='next' else 'chance_of_playing_this_round') if binding in ['next','this'] else None
  match=__import__('re').search(r'(?:Expected back|Suspended until)\s+(.+)',news,__import__('re').I)
  r=dict(season=row['season'],round=row['round'],code=code,element=element,name=e['web_name'],team_name=team,position=int(float(e['element_type'])),forecast_at=at.isoformat(),snapshot_at_proxy=source_at.isoformat(),source_url=row['source_url'],source_commit=row['commit'],source_blob_sha=row['blob_sha'],source_file=row['source_file'],status=status,known=valid,reason=reason,departure=departure,core=core,news=news if valid else '',news_added=added.isoformat() if added and valid else '',chance=pilot.chance(None if empty(target_chance) else target_chance) if valid else None,chance_binding=binding,news_age_days=(at-added).total_seconds()/86400 if added and valid else None,previous_status=prior['status'] if consecutive else '',previous_snapshot_consecutive=consecutive,reported_return_to_available=bool(consecutive and prior['status'] in ['i','s','n'] and status=='a') if valid else None,expected_return_text=match.group(1) if match and valid else '',raw_file_sha256=digest)
  output[code]=r;previous[code]=r
 audit=dict(season=row['season'],round=row['round'],master_origin=row['master_origin'],forecast_at=at.isoformat(),actual_FPL_deadline=actual.isoformat() if actual else '',snapshot_at_proxy=source_at.isoformat() if source_at else '',snapshot_age_hours=age,format=row['format'],source_available=bool(data),source_eligible=source_ok,eligibility_reason=why,source_players=len(output),known_source_players=sum(p['known'] for p in output.values()),non_player_assets_excluded=nonplayers,chance_binding=binding,source_deadline_bound=bound,source_note=source_note,origin_differs_from_workload=at!=dt(row['master_origin']),source_tier='git_timestamp_proxy',strict_historical_qualified=False,source_url=row['source_url'],source_commit=row['commit'],source_blob_sha=row['blob_sha'],source_file=row['source_file'],source_sha256=digest)
 return output if source_ok else {},list(output.values()),audit
def main():
 OUT.mkdir(exist_ok=True);builder_digest=sha(P/'build.py');selections=json.loads((P/'selected_sources.json').read_text());selection={(r['season'],r['round']):r for r in selections};events=[];targets=collections.defaultdict(list)
 for r in read(MASTER/'player_matches.csv.xz'):
  targets[r['season']].append(dict(season=r['season'],round=int(float(r['round'])),fixture=num(r['fixture']),code=num(r['code'])))
  if truth(r['history_eligible']):events.append(dict(code=num(r['code']),team=r['historical_team'],kickoff=dt(r['fixture_kickoff_time']),available=dt(r['observation_available_after_proxy']),minutes=float(r['native_minutes'])))
 history=pilot.History(events);input_hashes={str(path.relative_to(R)):sha(path) for path in [MASTER/'player_matches.csv.xz',MASTER/'manifest.json',PILOT/'build.py',PILOT/'player_match_context.csv.xz',P/'selected_sources.json']};audits=[];coverage=[];fields=None
 with lzma.open(P/'player_match_context.csv.xz','wt',newline='',preset=3) as mf,lzma.open(P/'player_round_context.csv.xz','wt',newline='',preset=3) as rf,lzma.open(OUT/'player_matches.csv.xz','wt',newline='',preset=3) as of,__import__('gzip').open(P/'source_player_status.csv.gz','wt',newline='') as sf:
  mw=rw=ow=sw=None
  for season,originals in itertools.groupby(read(MASTER/'player_matches.csv.xz'),lambda r:r['season']):
   previous={};frames={};source_audits={};weights={};rosters=collections.defaultdict(list)
   for row in sorted([s for s in selections if s['season']==season],key=lambda r:r['round']):
    frm,source_rows,audit=frame(row,previous);gw=row['round'];frames[gw]=frm;audits.append(audit);source_audits[gw]=audit
    if row['source_file']:input_hashes[row['source_file']]=sha(R/row['source_file'])
    for source in source_rows:
     if sw is None:sw=csv.DictWriter(sf,fieldnames=list(source));sw.writeheader()
     sw.writerow(source)
    at=dt(audit['forecast_at']);weight={}
    for own in frm.values():
     for days in [28,90]:weight[(own['code'],days)]=history.minutes(own['code'],own['team_name'],at,days)
     rosters[(gw,own['team_name'])].append(own)
    weights[gw]=weight
   cache={};index={};match_known=0
   for t in targets[season]:
    gw=t['round'];code=t['code'];key=gw,code;a=source_audits[gw]
    if key not in cache:
     own=frames[gw].get(code);peers=[p for p in rosters[(gw,own['team_name'])] if p['code']!=code] if own else [];c=pilot.feature(own,peers,weights[gw]);c['av_forecast_at']=a['forecast_at']
     c.update(av_master_operational_origin=a['master_origin'],av_actual_FPL_deadline=a['actual_FPL_deadline'],av_source_age_hours=a['snapshot_age_hours'],av_source_format=a['format'],av_source_eligibility_reason=a['eligibility_reason'] if not a['source_eligible'] else 'player_missing_from_snapshot' if own is None else 'eligible_git_proxy' if own['known'] else 'invalid_status_or_news_timestamp',av_source_deadline_bound=a['source_deadline_bound'],av_mixed_origin_with_workload=a['origin_differs_from_workload'],av_chance_binding_verified=a['source_deadline_bound'],av_status_only_source=a['format']=='players_csv')
     cache[key]=c;rr=dict(season=season,round=gw,code=code,**c)
     if rw is None:rw=csv.DictWriter(rf,fieldnames=list(rr));rw.writeheader();fields=list(c)
     rw.writerow(rr)
    c=cache[key];mr=dict(t,**c)
    if mw is None:mw=csv.DictWriter(mf,fieldnames=list(mr));mw.writeheader()
    mw.writerow(mr);index[(t['fixture'],code)]=c;match_known+=bool(c['av_source_known'])
   count=0
   for r in originals:
    c=index[(num(r['fixture']),num(r['code']))];merged=dict(r,**c)
    if ow is None:ow=csv.DictWriter(of,fieldnames=list(merged));ow.writeheader()
    ow.writerow(merged);count+=1
   coverage.append(dict(season=season,master_rows=count,player_round_rows=len(cache),forecast_origins=len(frames),eligible_source_origins=sum(a['source_eligible'] for a in source_audits.values()),known_master_rows=match_known,unknown_master_rows=count-match_known,bootstrap_origins=sum(a['format']=='bootstrap' for a in source_audits.values()),status_only_csv_origins=sum(a['format']=='players_csv' for a in source_audits.values()),non_player_assets_excluded=sum(a['non_player_assets_excluded'] for a in source_audits.values()),strict_historical_qualified=False))
   print('Availability enriched',season,count,'rows',match_known,'known',count-match_known,'unknown',flush=True)
 assert sha(P/'build.py')==builder_digest;input_hashes[str((P/'build.py').relative_to(R))]=builder_digest
 write('snapshot_audit.csv',audits);write('coverage.csv',coverage);(P/'input_hashes.json').write_text(json.dumps(input_hashes,indent=2));(P/'summary.json').write_text(json.dumps(dict(master_rows=sum(r['master_rows'] for r in coverage),known_master_rows=sum(r['known_master_rows'] for r in coverage),unknown_master_rows=sum(r['unknown_master_rows'] for r in coverage),availability_columns=fields,coverage=coverage,model_fits=0),indent=2))
if __name__=='__main__':main()
