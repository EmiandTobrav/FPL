"""As-of PL versions and dated primary cup announcements across seasons."""
import collections,json,re
from zoneinfo import ZoneInfo
from common import *
def announced():
 rows=[]
 for r in read(PILOT/'historical_announced_club_fixtures.csv'):
  rows.append(dict(season=r['season'],calendar_key=r['calendar_key'],competition=r['competition'],home_team=r['home_team'],away_team=r['away_team'],kickoff_utc=r['kickoff_utc'],publication_date=r['publication_date'],available_after_proxy=r['available_after_proxy'],source_url=r['source_url'],source_file=str((PILOT/r['source_file']).relative_to(R)),source_access='cached_primary_document',historical_deadline_qualified=False))
 sources=json.loads((P/'primary_calendar_sources.json').read_text())
 def add(source,season,home,away,date,time,comp,zone='Europe/London',access='web_index_of_primary_article'):
  publication,url=sources[source];t=datetime.strptime(date+' '+time,'%Y-%m-%d %H:%M').replace(tzinfo=ZoneInfo(zone)).astimezone(timezone.utc)
  rows.append(dict(season=season,calendar_key=source+':'+str(len(rows)),competition=comp,home_team=home,away_team=away,kickoff_utc=t.isoformat(),publication_date=publication,available_after_proxy=(dt(publication+'T00:00:00Z')+timedelta(days=1)).isoformat(),source_url=url,source_file='datasets/fpl_all_competitions_context_v1/primary_article_extractions.json' if access.startswith('web_') else 'datasets/fpl_all_competitions_context_v1/raw/primary_ucl2024.pdf',source_access=access,historical_deadline_qualified=False))
 # Structured factual extraction of dated primary articles read through web access.
 # HTML retrieval now returns 404 for several old club pages. Access method remains explicit.
 cases={
  'lfc2019':('2019-20','UEFA Champions League',[
   ('Napoli','Liverpool','2019-09-17','20:00'),('Liverpool','Salzburg','2019-10-02','20:00'),('Genk','Liverpool','2019-10-23','20:00'),('Liverpool','Genk','2019-11-05','20:00'),('Liverpool','Napoli','2019-11-27','20:00'),('Salzburg','Liverpool','2019-12-10','17:55')]),
  'lfc2020qf':('2020-21','UEFA Champions League',[
   ('Real Madrid','Liverpool','2021-04-06','20:00'),('Liverpool','Real Madrid','2021-04-14','20:00')]),
  'lfc2021':('2021-22','UEFA Champions League',[
   ('Liverpool','AC Milan','2021-09-15','20:00'),('Porto','Liverpool','2021-09-28','20:00'),('Atletico Madrid','Liverpool','2021-10-19','20:00'),('Liverpool','Atletico Madrid','2021-11-03','20:00'),('Liverpool','Porto','2021-11-24','20:00'),('AC Milan','Liverpool','2021-12-07','20:00')]),
  'lfc2023':('2023-24','UEFA Europa League',[
   ('LASK','Liverpool','2023-09-21','17:45'),('Liverpool','Union SG','2023-10-05','20:00'),('Liverpool','Toulouse','2023-10-26','20:00'),('Toulouse','Liverpool','2023-11-09','17:45'),('Liverpool','LASK','2023-11-30','20:00'),('Union SG','Liverpool','2023-12-14','17:45')])}
 (P/'primary_article_extractions.json').write_text(json.dumps(dict(access_method='primary_article_text_read_via_web_search_open',retrieved_at=datetime.now(timezone.utc).isoformat(),sources={k:sources[k] for k in cases},structured_fixtures=cases,unused_city2022_reason='No verified publication date available; not backdated'),indent=2))
 for source,(season,comp,fs) in cases.items():
  for home,away,date,time in fs:add(source,season,home,away,date,time,comp)
 aliases={'Manchester City':'Man City','Liverpool FC':'Liverpool','Arsenal FC':'Arsenal','Aston Villa FC':'Aston Villa'}
 for page in (P/'raw/primary_ucl2024.txt').read_text().split('\f'):
  for side in [0,1]:
   team=None
   for line in page.splitlines():
    part=(line[:90] if side==0 else line[90:]).strip()
    if part in aliases:team=aliases[part];continue
    m=re.fullmatch(r'(\d+ \w+ 202[45])\s+(\d\d:\d\d)\s+(.*?) \(([HA])\)',part)
    if m and team:
     day,time,opponent,ha=m.groups();date=datetime.strptime(day,'%d %B %Y').strftime('%Y-%m-%d');add('ucl2024','2024-25',team if ha=='H' else opponent,opponent if ha=='H' else team,date,time,'UEFA Champions League','Europe/Paris','cached_primary_PDF_modification_date_proxy')
    elif part and not m and not re.match(r'\d',part):team=None
 assert sum(r['calendar_key'].startswith('ucl2024:') for r in rows)==32
 write('historical_announced_club_fixtures.csv',rows);return rows
def snapshots():
 meta,teams=metadata();seasons,rounds,_=config();output=[];audits=[]
 reconstructed=collections.defaultdict(list)
 for r in read(R/'reports/calendar_reconstruction_2026_10_16/fixture_snapshots.csv.gz'):
  if r['season']=='2025-26':reconstructed[int(r['round'])].append(r)
 team_codes={s:{r['code']:r['name'] for r in read(R/'FPL_training_dataset/research/current/project/data'/f'{s}_teams.csv.gz')} for s in seasons}
 for selection in json.loads((P/'calendar_origin_selection.json').read_text()):
  season=selection['season'];gw=selection['round'];at=dt(selection['forecast_at']);rows=[]
  if season=='2025-26' and gw in reconstructed:
   for r in reconstructed[gw]:
    rows.append(dict(season=season,round=gw,forecast_at=at.isoformat(),source_time=r['source_time'],snapshot_age_days=r['snapshot_age_days'],calendar_usable=truth(r['calendar_usable']),fixture_id=r['fixture_id'],event=r['event'],kickoff_time=r['kickoff_time'],home_team=team_codes[season][r['home_code']],away_team=team_codes[season][r['away_code']],source_file=r['source_file'],source_sha=r['source_sha'],event_basis=r['event_basis']))
  elif selection['status']=='ok':
   age=(at-dt(selection['source_time'])).total_seconds()/86400
   for r in read(R/selection['raw_file']):
    rows.append(dict(season=season,round=gw,forecast_at=at.isoformat(),source_time=selection['source_time'],snapshot_age_days=age,calendar_usable=age<=14,fixture_id=num(r['id']),event=num(r['event']) if r['event'] and r['event'] not in ['nan','None'] else '',kickoff_time=r['kickoff_time'],home_team=teams[season][num(r['team_h'])],away_team=teams[season][num(r['team_a'])],source_file=selection['raw_file'],source_sha=selection['source_sha'],event_basis='pre_origin_git_fixture_snapshot'))
  assert not rows or len(rows)==380,(season,gw,len(rows))
  assert all(dt(r['source_time'])<at for r in rows)
  output+=rows;audits.append(dict(season=season,round=gw,forecast_at=at.isoformat(),fixtures=len(rows),source_time=rows[0]['source_time'] if rows else '',snapshot_age_days=rows[0]['snapshot_age_days'] if rows else '',calendar_usable=rows[0]['calendar_usable'] if rows else False,status='available_git_publication_proxy' if rows else 'unknown'))
 write('fixture_snapshots.csv.gz',output);write('calendar_origin_audit.csv',audits);print('PL calendar origins',len(audits),'fresh',sum(truth(r['calendar_usable']) for r in audits),flush=True)
def calculate(team,season,gw,at,rows,announcements):
 source=rows[0] if rows else None;fresh=bool(source and truth(source['calendar_usable']));own=[r for r in rows if team and team in [r['home_team'],r['away_team']]];unassigned=sum(not r['event'] for r in own)
 out=dict(cal_forecast_at=at.isoformat(),cal_last_observed_club=team,cal_club_assignment_is_observed_proxy=True,cal_historical_deadline_qualified=False,cal_pl_source_time=source['source_time'] if source else '',cal_pl_snapshot_age_days=float(source['snapshot_age_days']) if source else None,cal_pl_calendar_fresh=fresh,cal_all_competitions_complete=False,cal_cup_missing_means_no_match=False,cal_international_callup_forecast_available=False,cal_PL_unassigned_fixtures=unassigned if own else None,cal_PL_round_bindings_complete=bool(own and not unassigned),cal_historical_cup_calendar_complete=False)
 for n in [1,3,6]:
  # Use the official numeric FPL round axis, including blank/COVID rounds.
  last_round=max((int(float(r['event'])) for r in rows if r['event']),default=gw-1)
  slots=range(gw,min(gw+n,last_round+1));fs=[r for r in own if r['event'] and int(float(r['event'])) in slots]
  out[f'cal_horizon_rounds_available_next_{n}']=len(slots) if rows else None
  out[f'cal_PL_fixtures_next_{n}_rounds']=len(fs) if own else None
  out[f'cal_PL_blank_rounds_next_{n}']=sum(not any(int(float(r['event']))==slot for r in fs) for slot in slots) if own and not unassigned else None
  out[f'cal_PL_double_rounds_next_{n}']=sum(sum(int(float(r['event']))==slot for r in fs)>1 for slot in slots) if own and not unassigned else None
 known=[r for r in announcements if r['season']==season and team and team in [r['home_team'],r['away_team']] and dt(r['available_after_proxy'])<at<=dt(r['kickoff_utc'])]
 pl=[r for r in own if r['kickoff_time'] and dt(r['kickoff_time'])>=at] if fresh else []
 times=[dt(r['kickoff_utc']) for r in known]+[dt(r['kickoff_time']) for r in pl];out['cal_hours_until_next_known_club_fixture']=round((min(times)-at).total_seconds()/3600,4) if times else None
 for days in [7,14,28]:
  cc=sum(dt(r['kickoff_utc'])<at+timedelta(days=days) for r in known);pc=sum(dt(r['kickoff_time'])<at+timedelta(days=days) for r in pl)
  out[f'cal_announced_cup_fixtures_lower_bound_next_{days}d']=cc if team else None
  out[f'cal_PL_registered_fixtures_next_{days}d']=pc if fresh and own else None
  out[f'cal_known_club_fixtures_lower_bound_next_{days}d']=cc+pc if team else None
 return out
if __name__=='__main__':announced();snapshots()
