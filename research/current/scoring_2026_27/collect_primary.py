"""Collect identity-checked primary player-match counts for source qualification.
No unvalidated bulk fallback and no access-control workarounds.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import pandas as pd
import sys,json,time,threading,urllib.request,urllib.error,hashlib
P=Path(__file__).resolve().parent;R=P.parent;RAW=P/'raw/primary';OUT=P/'results';RAW.mkdir(exist_ok=True)
LOCK=threading.Lock();NEXT=0;STOP=threading.Event();SOURCES=[]
def get(url,path):
 global NEXT
 if path.exists():return json.loads(path.read_text())
 with LOCK:
  now=time.monotonic();delay=max(0,NEXT-now);NEXT=max(now,NEXT)+.5
 if delay:time.sleep(delay)
 if STOP.is_set():raise RuntimeError('collection stopped')
 try:
  b=urllib.request.urlopen(url,timeout=35).read();d=json.loads(b);path.write_bytes(b);return d
 except urllib.error.HTTPError as e:
  if e.code in [401,403,429]:STOP.set()
  raise

def prepare(current_gw=1,historical=True):
 jobs=[]
 for year in (range(2019,2027) if historical else [2026]):
  season=f'{year}-{str(year+1)[2:]}'
  if year==2026:
   b=json.loads((P/'raw/bootstrap.json').read_text());players=pd.DataFrame(b['elements']);fixtures=pd.DataFrame(get('https://fantasy.premierleague.com/api/fixtures/',RAW/'fixtures_2026.json'));f=pd.DataFrame(get(f'https://fantasy.premierleague.com/api/event/{current_gw}/live/',RAW/f'live_2026_gw{current_gw}.json')['elements']);stats=pd.DataFrame([dict(element=x.id,**x.stats) for x in f.itertuples()]);sel=fixtures[(fixtures.event==current_gw)&fixtures.finished]
   # Official GW1 has one match per club; verify this before assigning player fixtures.
   team_fixture={}
   for x in sel.itertuples():
    for tid in [x.team_h,x.team_a]:assert tid not in team_fixture;team_fixture[tid]=x.id
   fixture_by_element={int(x.id):x.explain[0]['fixture'] for x in f.itertuples() if len(x.explain)==1};stats['fixture']=stats.element.map(fixture_by_element);stats=stats[stats.minutes>0];stats['position']=stats.element.map(players.set_index('id').element_type).map({1:'GK',2:'DEF',3:'MID',4:'FWD'})
   stats['code']=stats.element.map(players.set_index('id').code);stats['name']=stats.element.map(players.set_index('id').web_name)
  else:
   fixtures=pd.read_csv(R/f'project/data/{season}_fixtures.csv');players=pd.read_csv(R/f'project/data/{season}_players.csv');f=pd.read_csv(R/f'project/data/{season}_gw.csv');sel=fixtures.sort_values('kickoff_time').head(1);stats=f[(f.fixture.isin(sel.id))&(f.minutes>0)].drop_duplicates().copy();stats['code']=stats.element.map(players.set_index('id').code)
   if 'position' not in stats:stats['position']=stats.element.map(players.set_index('id').element_type).map({1:'GK',2:'DEF',3:'MID',4:'FWD'})
   stats['position']=stats.position.replace({'GKP':'GK'})
  assert not stats.duplicated(['element','fixture']).any()
  if 'pulse_id' not in fixtures or fixtures.pulse_id.fillna(0).eq(0).any():
   catalog=get(f'https://footballapi.pulselive.com/football/fixtures?compSeasons={274 if year==2019 else 841}&page=0&pageSize=500&altIds=true',RAW/f'fixtures_{year}_primary.json');assert catalog['pageInfo']['numPages']==1
   mapping={int(x['altIds']['opta'].lstrip('g')):int(x['id']) for x in catalog['content']}
   fixtures['pulse_id']=fixtures.code.map(mapping);assert fixtures.loc[fixtures.id.isin(sel.id),'pulse_id'].notna().all();sel=fixtures[fixtures.id.isin(sel.id)]
  first=sel.iloc[0];mid=int(first.pulse_id);url=f'https://footballapi.pulselive.com/football/stats/match/{mid}';match=get(url,RAW/f'match_{mid}.json');assert int(match['entity']['id'])==mid
  cid=match['entity']['gameweek']['compSeason']['id'];url=f'https://footballapi.pulselive.com/football/stats/ranked/players/appearances?comps=1&compSeasons={cid}&page=0&pageSize=1000&altIds=true';ranked=get(url,RAW/f'players_{season}.json');assert ranked['stats']['pageInfo']['numPages']==1
  ids={int(x['owner']['altIds']['opta'].lstrip('p')):int(x['owner']['id']) for x in ranked['stats']['content'] if x['owner'].get('altIds',{}).get('opta')}
  for row in stats.to_dict('records'):
   row={k:row.get(k) for k in ['element','fixture','code','name','position','minutes','goals_scored','assists','bps','bonus','saves','penalties_saved','penalties_missed','yellow_cards','red_cards','own_goals','goals_conceded','clean_sheets']};row.update(season=season,pulse_id=int(fixtures.set_index('id').loc[row['fixture'],'pulse_id']),pl_player_id=ids.get(row['code']));assert row['pl_player_id'] is not None; jobs.append(row)
  print('prepared',season,len(stats),flush=True)
 return jobs

def run():
 gw=int(sys.argv[1]) if len(sys.argv)>1 else 1;suffix=f'_gw{gw}' if gw!=1 else '';manifest=OUT/f'primary_collection_manifest{suffix}.csv';jobs=pd.read_csv(manifest).to_dict('records') if manifest.exists() else prepare(gw,historical=gw==1);pd.DataFrame(jobs).to_csv(manifest,index=False);rows=[];sources=[];errors=[]
 def fetch(row):
  pid=int(row['pl_player_id']);mid=int(row['pulse_id']);url=f'https://footballapi.pulselive.com/football/stats/player/{pid}?fixtures={mid}';path=RAW/f'player_{pid}_{mid}.json';d=get(url,path);assert int(d['entity']['id'])==pid;code=d['entity'].get('altIds',{}).get('opta');assert code is None or int(code.lstrip('p'))==int(row['code'])
  stats={s['name']:s['value'] for s in d['stats']};assert stats.get('appearances')==1
  out=dict(row);out.update({'pl_'+k:v for k,v in stats.items()});return out,dict(season=row['season'],fixture=row['fixture'],code=row['code'],url=url,file=str(path.relative_to(P)),sha256=hashlib.sha256(path.read_bytes()).hexdigest())
 with ThreadPoolExecutor(max_workers=12) as pool:
  futures={pool.submit(fetch,r):r for r in jobs}
  for future in as_completed(futures):
   try:r,s=future.result();rows.append(r);sources.append(s)
   except Exception as e:
    errors.append(dict(row=futures[future],error=repr(e)))
    if STOP.is_set():
     for f in futures:f.cancel()
     break
   if (len(rows)+len(errors))%50==0:print('collected',len(rows),'errors',len(errors),flush=True)
 pd.DataFrame(rows).sort_values(['season','fixture','code']).to_csv(OUT/f'primary_player_counts{suffix}.csv',index=False)
 (OUT/f'primary_sources{suffix}.json').write_text(json.dumps(sources,indent=2)+'\n');(OUT/f'primary_errors{suffix}.json').write_text(json.dumps(errors,indent=2)+'\n');print('FINISHED',len(rows),len(errors),flush=True)
if __name__=='__main__':run()
