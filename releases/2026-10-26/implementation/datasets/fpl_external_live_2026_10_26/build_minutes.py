"""Season-specific FPL identities and audited external playing minutes."""
import collections,json,sys
from common import *
from minute_reconstruction import reconstruct
def level(league):
 for pattern,name in [('u21','U21'),('u20','U20'),('u17','U17'),('u19','U19'),('olympics','U23_Olympic')]:
  if pattern in league:return name
 return 'senior'
def prepare():
 seasons,rounds,members=config();meta,teams=metadata();events=json.loads((P/'events.json').read_text());anchors=collections.defaultdict(set);local={};lookup={};token_names={};names={};dob=collections.defaultdict(set)
 for season,people in meta.items():
  lookup[season]=collections.defaultdict(set);names[season]=collections.defaultdict(set);token_names[season]={}
  for code,m in people.items():
   full=m['first_name']+' '+m['second_name'];token_names[season][code]=cup.tokens(full)
   if m.get('birth_date') and m['birth_date'] not in ['None','nan','']:dob[code].add(m['birth_date'])
   clubs=members.get((season,code),set())|{teams[season][m['team']]}
   for name in [full,m.get('known_name',''),m['web_name']]:
    if not name or name in ['None','nan']:continue
    names[season][cup.norm(name)].add(code)
    for club in clubs:lookup[season][(club,cup.norm(name))].add(code)
 for r in read(CUP/'player_links.csv'):anchors[r['espn_player_id']].add(r['code'])
 for r in read(PILOT/'international_player_minutes.csv.gz'):anchors[r['espn_player_id']].add(r['code'])
 for pid,codes in json.loads((R/'datasets/fpl_all_competitions_context_v1/identity_global_anchors.json').read_text()).items():anchors[pid].update(codes)
 # Build club+name anchors first, so national matches can reuse verified ESPN IDs.
 for key,z in events.items():
  if z['competition_type']!='club_cup':continue
  path=locate(f'{z["league"]}_{z["event"]["id"]}_summary.json')
  if not path.exists():continue
  d=json.loads(path.read_text())
  for season in z['seasons']:
   for side in d.get('rosters',[]):
    club=cup.club(side['team']['displayName'])
    if club not in seasons[season]['clubs']:continue
    for p in side.get('roster',[]):
     a=p['athlete'];pid=a['id'];name=a.get('fullName',a['displayName']);codes=set(lookup[season].get((club,cup.norm(name)),set()))|set(lookup[season].get((club,cup.norm(a['displayName'])),set()))
     if not codes and len(cup.tokens(name))>=2:
      codes={code for code,tokens in token_names[season].items() if cup.tokens(name)<=tokens and club in (members.get((season,code),set())|{teams[season][meta[season][code]['team']]})}
     if len(codes)==1:
      code=next(iter(codes));local[(season,pid)]=dict(code=code,method='unique_normalized_name_or_exact_tokens_and_club');anchors[pid].add(code)
 candidates=collections.defaultdict(set);people={};missing=0
 for key,z in events.items():
  path=locate(f'{z["league"]}_{z["event"]["id"]}_summary.json')
  if not path.exists():missing+=1;continue
  for side in json.loads(path.read_text()).get('rosters',[]):
   for p in side.get('roster',[]):
    a=p['athlete'];pid=a['id'];people[pid]=a;name=a.get('fullName',a['displayName']);ts=cup.tokens(name)
    for season in z['seasons']:
     already=anchors.get(pid,set())&meta[season].keys()
     if len(already)==1:continue
     cs=set(names[season].get(cup.norm(name),set()))|set(names[season].get(cup.norm(a['displayName']),set()))
     if len(ts)>=2:cs|={code for code,tokens in token_names[season].items() if ts<=tokens}
     candidates[pid]|=cs
 # Profiles are requested only for plausible FPL names, never for every foreign player.
 profiles=sorted(pid for pid,codes in candidates.items() if codes)
 (P/'profile_candidates.json').write_text(json.dumps(profiles));(P/'identity_candidates.json').write_text(json.dumps({k:sorted(v) for k,v in candidates.items() if v}));(P/'identity_club_anchors.json').write_text(json.dumps([dict(season=s,espn_player_id=pid,**v) for (s,pid),v in sorted(local.items())]));(P/'identity_global_anchors.json').write_text(json.dumps({pid:sorted(cs) for pid,cs in anchors.items()}))
 print('Club identity anchors',len(local),'candidate profiles',len(profiles),'missing source summaries',missing,flush=True)
 return seasons,meta,members,anchors,local,dob
def main():
 if len(sys.argv)>1 and sys.argv[1]=='levels':
  for filename in ['matches.csv.gz','player_minutes.csv.gz','unknown_minutes.csv.gz']:
   rows=list(read(P/filename))
   for r in rows:r['age_level']='club' if r['competition_type']=='club_cup' else level(r['external_match_key'].split(':')[0])
   write(filename,rows)
  print('Competition age levels synchronized',flush=True);return
 if len(sys.argv)>1 and sys.argv[1]=='build':
  seasons,rounds,members=config();meta,teams=metadata();anchors={pid:set(cs) for pid,cs in json.loads((P/'identity_global_anchors.json').read_text()).items()};local={(r['season'],r['espn_player_id']):dict(code=r['code'],method=r['method']) for r in json.loads((P/'identity_club_anchors.json').read_text())};dob=collections.defaultdict(set)
  for people in meta.values():
   for code,m in people.items():
    if m.get('birth_date') and m['birth_date'] not in ['None','nan','']:dob[code].add(m['birth_date'])
 else:seasons,meta,members,anchors,local,dob=prepare()
 if len(sys.argv)>1 and sys.argv[1]=='prepare':return
 candidates=json.loads((P/'identity_candidates.json').read_text());profile_matches={};identity_audit=[]
 for pid,codes in candidates.items():
  path=locate(f'athlete_{pid}.json');profile=json.loads(path.read_text()) if path.exists() else {};birth=profile.get('dateOfBirth','')[:10];good={c for c in codes if birth and birth in dob.get(c,set())}
  profile_matches[pid]=good;identity_audit.append(dict(espn_player_id=pid,candidates=len(codes),FPL_birthdate_candidates=len(good),profile_available=bool(profile),FPL_birthdates_available=sum(bool(dob.get(c)) for c in codes)))
 write('identity_profile_audit.csv',identity_audit)
 events=json.loads((P/'events.json').read_text());fixtures=[];players=[];audits=[];source_audit=[];identities={};raw_hashes={}
 for key,z in events.items():
  path=locate(f'{z["league"]}_{z["event"]["id"]}_summary.json')
  if not path.exists():source_audit.append(dict(external_match_key=key,source_available=False,roster_sides=0,FPL_rows=0));continue
  d=json.loads(path.read_text());comp=d['header']['competitions'][0];assert comp['status']['type']['completed'] and str(d['header']['id'])==z['event']['id'];assert dt(comp['date'])==dt(z['event']['date'])
  cs={c['homeAway']:c for c in comp['competitors']}
  for c in z['event']['competitions'][0]['competitors']:assert c['id']==cs[c['homeAway']]['id']
  rawlog=d.get('keyEvents',[]);log=[];seen_substitutions=set()
  for event in rawlog:
   if event['type']['type']=='substitution' and 'friendly' not in z['league']:
    minute=cup.minute(event['clock']);signature=(event.get('team',{}).get('id'),tuple(p['athlete']['id'] for p in event.get('participants',[])),minute)
    # Older competitive feeds can publish the same substitution twice under
    # different event IDs. Exact incoming/outgoing/standard-minute duplicates
    # describe one legal substitution; the raw records remain preserved.
    if minute is not None and signature in seen_substitutions:continue
    seen_substitutions.add(signature)
   log.append(event)
  kinds={e['type']['type'] for e in log};status=comp['status']['type'];length=120 if any('extra-time' in k for k in kinds) or status.get('detail')=='AET' or any(e.get('period',{}).get('number') in [3,4] for e in log) else 90
  complete='end-regular-time' in kinds or (status.get('name')=='STATUS_FULL_TIME' and status.get('detail')=='FT')
  isclub=z['competition_type']=='club_cup';before=len(players);home=cs['home']['team']['displayName'];away=cs['away']['team']['displayName'];home=cup.club(home) if isclub else home;away=cup.club(away) if isclub else away
  for season in z['seasons']:
   f=dict(season=season,external_match_key=key,competition=z['label'],competition_type=z['competition_type'],age_level='club' if isclub else level(z['league']),is_fpl_fixture=False,data_role='workload_context',kickoff_utc=comp['date'],home_team=home,away_team=away,match_length_excluding_added_time=length,extra_time=length==120,penalty_shootout=status.get('detail')=='FT-Pens' or 'start-shootout' in kinds,duplicate_substitution_records_removed=len(rawlog)-len(log),raw_file=str(path.relative_to(R)),source_url=f'https://www.espn.com/soccer/match/_/gameId/{z["event"]["id"]}',historical_deadline_qualified=False)
   start_count=len(players)
   # All selected club fixtures are retained, including missing lineups/FPL matches.
   if isclub:fixtures.append(f)
   sides={}
   for side in d.get('rosters',[]):
    roster=side.get('roster',[]);team=side['team']['displayName'];team=cup.club(team) if isclub else team;tid=side['team']['id'];sides[team]=True
    if isclub and team not in seasons[season]['clubs']:continue
    values,issues,expected=reconstruct(roster,[e for e in log if e.get('team',{}).get('id')==tid],length)
    if not complete:issues.append('unconfirmed_match_duration')
    qualified=not issues
    accepted=[];unmapped=0
    for p in roster:
     a=p['athlete'];pid=a['id'];candidates_for_season=anchors.get(pid,set())&meta[season].keys();method='verified_ESPN_identity_bridge'
     if (season,pid) in local:code=local[(season,pid)]['code'];method=local[(season,pid)]['method']
     elif len(candidates_for_season)==1:code=next(iter(candidates_for_season))
     else:
      cs2=profile_matches.get(pid,set())&meta[season].keys();code=next(iter(cs2)) if len(cs2)==1 else '';method='unique_candidate_name_and_exact_birthdate'
     if not code:unmapped+=1;continue
     ident=(season,pid);previous=identities.setdefault(ident,code);assert previous==code,(ident,previous,code)
     accepted.append(dict(season=season,external_match_key=key,competition=f['competition'],competition_type=z['competition_type'],age_level=f['age_level'],is_fpl_fixture=False,data_role='workload_context',kickoff_utc=f['kickoff_utc'],team=team,opponent=away if side['homeAway']=='home' else home,was_home=side['homeAway']=='home',espn_player_id=pid,player_name=a.get('fullName',a['displayName']),code=code,element=meta[season][code]['id'],identity_status=method,starter=bool(p.get('starter')),subbed_in=bool(p.get('subbedIn')),subbed_out=bool(p.get('subbedOut')),minutes_played=values[pid] if qualified else '',minutes_basis='derived_lineup_substitution_dismissal_clocks' if qualified else 'unknown_timeline_conflict',team_timeline_qualified=qualified,minutes_directly_reported=False,extra_time_included=length==120,uncertainty='added_time_excluded_minute_rounding' if qualified else ';'.join(sorted(set(issues))),historical_deadline_qualified=False,source_url=f['source_url'],raw_file=f['raw_file']))
    players+=accepted
    if isclub or accepted:audits.append(dict(season=season,external_match_key=key,team=team,competition_type=z['competition_type'],qualified=qualified,issues=';'.join(sorted(set(issues))),roster_players=len(roster),total_minutes=sum(values.values()),expected_minutes=expected,FPL_rows=len(accepted),unmapped_squad_rows=unmapped))
   if isclub:
    for team in {home,away}&seasons[season]['clubs']:
     if team not in sides:audits.append(dict(season=season,external_match_key=key,team=team,competition_type=z['competition_type'],qualified=False,issues='missing_roster',roster_players=0,total_minutes='',expected_minutes='',FPL_rows=0,unmapped_squad_rows=''))
   elif len(players)>start_count:fixtures.append(f)
  source_audit.append(dict(external_match_key=key,source_available=True,roster_sides=sum(bool(s.get('roster')) for s in d.get('rosters',[])),FPL_rows=len(players)-before))
  if isclub or len(players)>before:raw_hashes[str(path.relative_to(R))]=sha(path)
 write('matches.csv.gz',fixtures);write('player_minutes.csv.gz',players);write('team_timeline_audit.csv.gz',audits);write('source_match_audit.csv.gz',source_audit)
 assert len({(r['season'],r['external_match_key'],r['espn_player_id']) for r in players})==len(players)
 coverage=[]
 for season in seasons:
  for kind in ['club_cup','international']:
   fs=[r for r in fixtures if r['season']==season and r['competition_type']==kind];ps=[r for r in players if r['season']==season and r['competition_type']==kind]
   coverage.append(dict(season=season,competition_type=kind,fixtures=len(fs),FPL_players=len({r['code'] for r in ps}),squad_rows=len(ps),known_minute_rows=sum(r['minutes_played']!='' for r in ps),unknown_minute_rows=sum(r['minutes_played']=='' for r in ps),all_competitions_complete=False))
 write('coverage.csv',coverage);write('unknown_minutes.csv.gz',[r for r in players if r['minutes_played']==''])
 (P/'minute_input_hashes.json').write_text(json.dumps(raw_hashes,indent=2));(P/'minute_summary.json').write_text(json.dumps(dict(coverage=coverage,physical_fixtures_with_FPL_or_PL_club=len({r['external_match_key'] for r in fixtures}),all_competitions_complete=False),indent=2));print(json.dumps(coverage,indent=2),flush=True)
if __name__=='__main__':main()
