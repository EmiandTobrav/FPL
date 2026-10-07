"""Collect only the frozen 28-row audit sample; stop on access/rate-limit errors."""
from pathlib import Path
import json,hashlib,time,urllib.request
import pandas as pd
P=Path(__file__).resolve().parent;S=P.parent
SEASONS={'2019-20':274,'2020-21':363,'2021-22':418,'2022-23':489,'2023-24':578,'2024-25':719,'2025-26':777}

def main():
 raw=P/'inputs/primary';raw.mkdir(exist_ok=True)
 sources=[];rows=[]
 def get(url,name):
  path=raw/name
  if not path.exists():
   time.sleep(.6)
   data=urllib.request.urlopen(url,timeout=35).read()
   json.loads(data);path.write_bytes(data)
  content=path.read_bytes();sources.append(dict(url=url,file=str(path.relative_to(P)),sha256=hashlib.sha256(content).hexdigest()))
  (P/'primary_sources.json').write_text(json.dumps(sources,indent=2)+'\n')
  return json.loads(content)
 sample=pd.read_csv(P/'control_plan.csv')
 for season,g in sample.groupby('season',sort=True):
  cid=SEASONS[season]
  players=get(f'https://footballapi.pulselive.com/football/stats/ranked/players/appearances?comps=1&compSeasons={cid}&page=0&pageSize=1000&altIds=true',f'players_{season}.json')
  assert players['stats']['pageInfo']['numPages']==1
  ids={}
  for x in players['stats']['content']:
   owner=x['owner'];code=owner.get('altIds',{}).get('opta')
   if code:
    code=int(code.lstrip('p'));pid=int(owner['id'])
    assert code not in ids or ids[code]==pid
    ids[code]=pid
  fixtures=pd.read_csv(S.parent/f'project/data/{season}_fixtures.csv.gz').set_index('id')
  if 'pulse_id' not in fixtures or fixtures.loc[g.fixture,'pulse_id'].isna().any():
   cat=get(f'https://footballapi.pulselive.com/football/fixtures?compSeasons={cid}&page=0&pageSize=500&altIds=true',f'fixtures_{season}.json')
   assert cat['pageInfo']['numPages']==1
   mapping={int(x['altIds']['opta'].lstrip('g')):int(x['id']) for x in cat['content']}
   fixtures['pulse_id']=fixtures.code.map(mapping)
  for row in g.to_dict('records'):
   pid=ids[int(row['code'])];mid=int(fixtures.loc[row['fixture'],'pulse_id'])
   url=f'https://footballapi.pulselive.com/football/stats/player/{pid}?fixtures={mid}&altIds=true'
   data=get(url,f'player_{pid}_{mid}.json')
   assert int(data['entity']['id'])==pid
   assert int(data['entity']['altIds']['opta'].lstrip('p'))==row['code']
   stats={x['name']:x['value'] for x in data['stats']}
   assert stats.get('appearances')==1
   rows.append(dict(**row,pl_player_id=pid,pulse_id=mid,**{'pl_'+k:v for k,v in stats.items()}))
   pd.DataFrame(rows).to_csv(P/'inputs/fresh_primary_controls.csv',index=False)
  print(season,'collected',len(rows),flush=True)
 if len(rows)!=28:raise ValueError('Incomplete frozen sample')
if __name__=='__main__':main()
