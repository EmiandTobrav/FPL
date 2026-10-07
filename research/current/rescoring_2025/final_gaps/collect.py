"""Fetch remaining gap fixtures and fixed controls, preserving metadata and source hashes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor,as_completed
import sys,json,hashlib,urllib.request,urllib.error
import pandas as pd
P=Path(__file__).resolve().parent;R=P.parents[1];OLD=P.parent/'missing_2021';O=P/'results';RAW=P/'raw'
sys.path.insert(0,str(OLD))
from fetch import parse,ALIASES,ARCHIVE,FIELDS
ALIASES.update({"AFC Bournemouth":"Bournemouth","Tottenham":"Spurs"})

def manifest():
 path=OLD/'raw/fotmob_47.csv'
 if not path.exists():path.parent.mkdir(exist_ok=True);urllib.request.urlretrieve(ARCHIVE,path)
 a=pd.read_csv(path,low_memory=False)[['match_id','match_time_utc','home_team','away_team']].drop_duplicates()
 a['date']=pd.to_datetime(a.match_time_utc,format='%a, %b %d, %Y, %H:%M UTC',utc=True).dt.strftime('%Y-%m-%d')
 a['home']=a.home_team.replace(ALIASES);a['away']=a.away_team.replace(ALIASES)
 gaps=pd.read_csv(P.parent/'gap_repair/results/remaining_gaps.csv');allrows=[]
 for season in ['2022-23','2023-24']:
  f=pd.read_csv(R/f'project/data/{season}_fixtures.csv');teams=pd.read_csv(R/f'project/data/{season}_teams.csv').set_index('id')
  f['home']=f.team_h.map(teams.name);f['away']=f.team_a.map(teams.name);f['date']=pd.to_datetime(f.kickoff_time,utc=True).dt.strftime('%Y-%m-%d')
  f=f.merge(a[['match_id','date','home','away']],on=['date','home','away'],how='left',validate='one_to_one')
  targets=set(gaps.loc[gaps.season==season,'fixture']);f['purpose']=f.id.map(lambda x:'gap' if x in targets else 'control')
  controls=f[(f.purpose=='control')&f.match_id.notna()].sort_values(['date','id'])
  ids=controls.iloc[[i*(len(controls)-1)//7 for i in range(8)]].id
  f=f[f.id.isin(targets)|f.id.isin(ids)].copy();assert f.match_id.notna().all();f['match_id']=f.match_id.astype(int);f['season']=season
  allrows.append(f[['season','id','pulse_id','date','home','away','team_h_score','team_a_score','match_id','purpose']])
 z=pd.concat(allrows);assert len(z[z.purpose=='gap'])==21
 z.to_csv(O/'fixture_manifest.csv',index=False);return z

def run():
 O.mkdir(exist_ok=True);RAW.mkdir(exist_ok=True);z=manifest()
 expected={x['match_id']:x['sha256'] for x in json.loads((O/'sources.json').read_text())} if (O/'sources.json').exists() else {}
 def fetch(row):
  mid=row['match_id'];url=f'https://www.fotmob.com/api/data/matchDetails?matchId={mid}';path=RAW/f'fotmob_{mid}.json'
  if not path.exists():
   with urllib.request.urlopen(url,timeout=30) as response:path.write_bytes(response.read())
  b=path.read_bytes();sha=hashlib.sha256(b).hexdigest()
  if mid in expected:assert sha==expected[mid],'Source revision changed; review required'
  rows=parse(json.loads(b),row)
  for r in rows:r['season']=row['season']
  return rows,{'season':row['season'],'fixture':row['id'],'match_id':mid,'url':url,'sha256':sha}
 rows=[];sources=[]
 with ThreadPoolExecutor(max_workers=2) as pool:
  jobs=[pool.submit(fetch,r) for r in z.to_dict('records')]
  for i,job in enumerate(as_completed(jobs),1):
   try:a,b=job.result()
   except Exception:
    for other in jobs:other.cancel()
    raise
   rows.extend(a);sources.append(b)
   if i%10==0:print(i,'/',len(jobs),flush=True)
 pd.DataFrame(rows).reindex(columns=['season','fixture','match_id','purpose','code','fotmob_id','name','source_team']+list(FIELDS.values())).sort_values(['season','fixture','code']).to_csv(O/'fotmob_players.csv',index=False)
 (O/'sources.json').write_text(json.dumps(sorted(sources,key=lambda x:(x['season'],x['fixture'])),indent=2)+'\n')
 print('complete',len(sources),'matches',len(rows),'player rows',flush=True)
if __name__=='__main__':run()
