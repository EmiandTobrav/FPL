"""Bounded primary gap collection; stop new work on 401/403/429."""
from pathlib import Path
import pandas as pd,json,hashlib,urllib.request,urllib.error,time,threading,concurrent.futures
P=Path(__file__).resolve().parent;S=P.parent;I=P/'inputs';I.mkdir(exist_ok=True)
lock=threading.Lock();stop=threading.Event();next_start=0.;records=[]
def fetch(url,name):
 global next_start
 f=I/name
 if not f.exists():
  with lock:
   if stop.is_set():raise RuntimeError('Collection stopped')
   now=time.monotonic();delay=max(0,next_start-now);next_start=max(now,next_start)+.51
  if delay:time.sleep(delay)
  if stop.is_set():raise RuntimeError('Collection stopped')
  try:
   b=urllib.request.urlopen(urllib.request.Request(url,headers={'Origin':'https://www.premierleague.com','User-Agent':'FPL-research/1.0'}),timeout=40).read()
  except urllib.error.HTTPError as e:
   if e.code in [401,403,429]:stop.set()
   raise
  json.loads(b);f.write_bytes(b)
 b=f.read_bytes();rec=dict(url=url,file='inputs/'+name,sha256=hashlib.sha256(b).hexdigest())
 with lock:records.append(rec)
 return json.loads(b)
def main():
 teams=pd.read_csv(S/'season_conservation/inputs/full_team_totals.csv');todo=teams[teams.match_id.isna()][['season','fixture','fixture_code','pulse_id','home_primary_id','away_primary_id','home_score','away_score','date']].drop_duplicates();todo['scope']='gap'
 controls=teams[(teams.season=='2024-25')&teams.fixture.isin([1,2,3])][todo.columns[:-1]].drop_duplicates();controls['scope']='later_control';todo=pd.concat([todo,controls],ignore_index=True);todo.to_csv(P/'fixture_plan.csv',index=False)
 roster=[]
 for r in todo.itertuples():
  pid=int(r.pulse_id);d=fetch(f'https://footballapi.pulselive.com/football/fixtures/{pid}?altIds=true',f'fixture_{pid}.json');assert d['id']==pid and int(d['altIds']['opta'].lstrip('g'))==r.fixture_code and d['status']=='C';assert d['teams'][0]['team']['id']==r.home_primary_id and d['teams'][1]['team']['id']==r.away_primary_id;assert d['teams'][0]['score']==r.home_score and d['teams'][1]['score']==r.away_score
  assert pd.to_datetime(d['kickoff']['millis'],unit='ms',utc=True).strftime('%Y-%m-%d')==r.date
  on={e['personId'] for e in d['events'] if e['type']=='S' and e['description']=='ON'}
  for team in d['teamLists']:
   side='home' if team['teamId']==r.home_primary_id else 'away';assert len(team['lineup'])==11
   for x in team['lineup']+team['substitutes']:
    if x not in team['lineup'] and x['id'] not in on:continue
    roster.append(dict(season=r.season,fixture=r.fixture,code=int(x['altIds']['opta'].lstrip('p')),pl_player_id=x['id'],pulse_id=pid,primary_team_id=team['teamId'],side=side,scope=r.scope,name=x['name']['display']))
 roster=pd.DataFrame(roster);assert not roster.duplicated(['season','fixture','code']).any();roster.to_csv(P/'roster.csv',index=False)
 targets=pd.read_csv(S/'bulk_followup/results/remaining_fields.csv.gz',low_memory=False);targets=targets[targets.match_id.isna()][['season','fixture','code']].drop_duplicates();covered=targets.merge(roster,on=['season','fixture','code'],how='left',validate='one_to_one');assert covered.pl_player_id.notna().all()
 def player(r):
  d=fetch(f'https://footballapi.pulselive.com/football/stats/player/{int(r.pl_player_id)}?fixtures={int(r.pulse_id)}&altIds=true',f'player_{int(r.pl_player_id)}_{int(r.pulse_id)}.json');assert int(d['entity']['altIds']['opta'].lstrip('p'))==r.code and int(d['entity']['id'])==r.pl_player_id;s={x['name']:x['value'] for x in d['stats']};assert len(s)==len(d['stats']) and s.get('appearances')==1;return {**r._asdict(),**s}
 results=[]
 with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
  # map is bounded by four workers; stop flag prevents new requests after an access/rate refusal.
  for v in pool.map(player,roster.itertuples(index=False)):
   results.append(v)
   if len(results)%60==0:print('Verified player responses',len(results),'of',len(roster),flush=True)
 (P/'players.json').write_text(json.dumps(results,indent=2)+'\n');(P/'sources.json').write_text(json.dumps(records,indent=2)+'\n');print('Complete',len(results),flush=True)
if __name__=='__main__':main()
