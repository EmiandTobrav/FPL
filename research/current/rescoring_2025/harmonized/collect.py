"""Resumable, bounded public match-data collection; no access-control workarounds."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import hashlib,json,threading,time,urllib.request,urllib.error,sys
import pandas as pd
P=Path(__file__).resolve().parent;R=P.parents[1];RAW=P/'raw';OUT=P/'results';CACHE=RAW/'normalized'
SEASONS=[f'{y}-{str(y+1)[2:]}' for y in range(2019,2026)]
ALIASES={'Manchester City':'Man City','Manchester United':'Man Utd','Newcastle United':'Newcastle','West Ham United':'West Ham','Wolverhampton Wanderers':'Wolves','Tottenham Hotspur':'Spurs','Tottenham':'Spurs','Brighton & Hove Albion':'Brighton','Brighton and Hove Albion':'Brighton','Nottingham Forest':"Nott'm Forest",'Leicester City':'Leicester','Leeds United':'Leeds','Norwich City':'Norwich','Sheffield United':'Sheffield Utd','AFC Bournemouth':'Bournemouth','Luton Town':'Luton','West Bromwich Albion':'West Brom','Ipswich Town':'Ipswich'}
FIELDS={'minutes_played':'source_minutes','goals':'source_goals','matchstats.headers.tackles':'tackles','shot_blocks':'blocks','clearances':'clearances','interceptions':'interceptions','recoveries':'recoveries'}
STOP=threading.Event();LOCK=threading.Lock();NEXT=0.

def get(url):
 global NEXT
 with LOCK:
  now=time.monotonic();delay=max(0,NEXT-now);NEXT=max(now,NEXT)+.25
 if delay:time.sleep(delay)
 if STOP.is_set():raise RuntimeError('collection stopped')
 try:
  with urllib.request.urlopen(url,timeout=35) as r:return r.read()
 except urllib.error.HTTPError as e:
  if e.code in (401,403,429):STOP.set()
  raise

def manifest():
 rows=[]
 for season in SEASONS:
  y=int(season[:4]);path=RAW/f'league_{season}.json';url=f'https://www.fotmob.com/api/data/leagues?id=47&season={y}%2F{y+1}'
  if not path.exists():path.write_bytes(get(url))
  d=json.loads(path.read_text());a=[]
  for m in d['fixtures']['allMatches']:
   a.append({'match_id':int(m['id']),'home':ALIASES.get(m['home']['name'],m['home']['name']),'away':ALIASES.get(m['away']['name'],m['away']['name']),'date':pd.to_datetime(m['status']['utcTime'],utc=True).strftime('%Y-%m-%d')})
  a=pd.DataFrame(a);f=pd.read_csv(R/f'project/data/{season}_fixtures.csv');t=pd.read_csv(R/f'project/data/{season}_teams.csv').set_index('id')
  f['home']=f.team_h.map(t.name);f['away']=f.team_a.map(t.name);f['date']=pd.to_datetime(f.kickoff_time,utc=True).dt.strftime('%Y-%m-%d')
  z=f.merge(a,on=['date','home','away'],how='left',validate='one_to_one');assert len(z)==380 and z.match_id.notna().all(),season
  z['match_id']=z.match_id.astype(int);z['season']=season
  rows.append(z[['season','id','match_id','date','home','away','team_h_score','team_a_score']])
 z=pd.concat(rows,ignore_index=True);z.to_csv(OUT/'fixture_manifest.csv',index=False);return z

def parse(d,f):
 g=d['general'];assert int(g['matchId'])==f['match_id'] and g['leagueId']==47 and g['finished']
 assert pd.to_datetime(g['matchTimeUTCDate'],utc=True).strftime('%Y-%m-%d')==f['date']
 assert [ALIASES.get(g[k]['name'],g[k]['name']) for k in ['homeTeam','awayTeam']]==[f['home'],f['away']]
 assert [x['score'] for x in d['header']['teams']]==[f['team_h_score'],f['team_a_score']]
 sides={int(g['homeTeam']['id']):f['home'],int(g['awayTeam']['id']):f['away']};rows=[]
 for player in d['content'].get('playerStats',{}).values():
  code=player.get('optaId')
  if not code:continue
  team_id=player.get('teamId');assert int(team_id) in sides
  row={'season':f['season'],'fixture':f['id'],'match_id':f['match_id'],'code':int(str(code).lstrip('p')),'name':player['name'],'source_team':sides[int(team_id)]}
  for block in player.get('stats',[]):
   for metric in block.get('stats',{}).values():
    key=metric.get('key')
    if key in FIELDS:
     dest=FIELDS[key];value=metric.get('stat',{}).get('value');assert dest not in row or row[dest]==value;row[dest]=value
  rows.append(row)
 assert rows and len({x['code'] for x in rows})==len(rows)
 return rows

def collect(f):
 mid=f['match_id'];cached=CACHE/f'{mid}.json'
 if cached.exists():return json.loads(cached.read_text())
 url=f'https://www.fotmob.com/api/data/matchDetails?matchId={mid}';path=RAW/f'fotmob_{mid}.json'
 if not path.exists():
  old=next((p for folder in ['missing_2021','final_gaps'] if (p:=P.parent/folder/'raw'/path.name).exists()),None)
  if old:path=old
  else:path.write_bytes(get(url))
 b=path.read_bytes();rows=parse(json.loads(b),f)
 result={'season':f['season'],'fixture':f['id'],'match_id':mid,'url':url,'sha256':hashlib.sha256(b).hexdigest(),'rows':rows}
 cached.write_text(json.dumps(result,ensure_ascii=False)+'\n');return result

def export():
 files=list(CACHE.glob('*.json'));rows=[];sources=[]
 for f in files:
  try:d=json.loads(f.read_text())
  except json.JSONDecodeError:continue  # another collector may be finishing this cache file
  rows.extend(d.pop('rows'));sources.append(d)
 if rows:
  frame=pd.DataFrame(rows).reindex(columns=['season','fixture','match_id','code','name','source_team']+list(FIELDS.values())).sort_values(['season','fixture','code'])
  for season,g in frame.groupby('season'):g.to_csv(OUT/f'{season}_counts.csv',index=False)
 (OUT/'sources.json').write_text(json.dumps(sorted(sources,key=lambda x:(x['season'],x['fixture'])),indent=2)+'\n')
 return len(sources)

def run():
 from package_data import prepare_inputs
 prepare_inputs()
 RAW.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True);CACHE.mkdir(exist_ok=True)
 z=pd.read_csv(OUT/'fixture_manifest.csv') if (OUT/'fixture_manifest.csv').exists() else manifest()
 # Validate contemporary official-FPL season first, then fill history.
 subset=sys.argv[1].split(',') if len(sys.argv)>1 else None
 if subset:z=z[z.season.isin(subset)].sort_values(['season','id'],ascending=[False,True])
 else:z=z.assign(priority=z.season.ne('2025-26')).sort_values(['priority','season','id'])
 suffix='_subset' if subset else '';errors=[];start=time.monotonic();done=0
 with ThreadPoolExecutor(max_workers=6) as pool:
  jobs={pool.submit(collect,f):f for f in z.to_dict('records')}
  for job in as_completed(jobs):
   f=jobs[job]
   try:job.result();done+=1
   except Exception as e:
    errors.append({'season':f['season'],'fixture':f['id'],'match_id':f['match_id'],'error':repr(e)})
    if STOP.is_set():
     for other in jobs:other.cancel()
     break
   if (done+len(errors))%50==0:
    status={'completed':done,'errors':len(errors),'seconds':round(time.monotonic()-start),'cached_total':len(list(CACHE.glob('*.json')))}
    (OUT/f'progress{suffix}.json').write_text(json.dumps(status)+'\n');print(json.dumps(status),flush=True)
 export();(OUT/f'errors{suffix}.json').write_text(json.dumps(errors,indent=2)+'\n')
 print('FINISHED',done,'completed',len(errors),'errors','stopped',STOP.is_set(),flush=True)
if __name__=='__main__':run()
