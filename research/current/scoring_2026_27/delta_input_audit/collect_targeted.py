"""Follow up Doku aggregate discrepancy; these are targeted, not holdout controls."""
from pathlib import Path
import json,hashlib,time,urllib.request
import pandas as pd
P=Path(__file__).resolve().parent;S=P.parent

def main():
 code=248875
 cat=json.loads((P/'inputs/primary/players_2025-26.json').read_text())
 owners=[x['owner'] for x in cat['stats']['content'] if x['owner'].get('altIds',{}).get('opta')==f'p{code}'];assert len(owners)==1
 pid=int(owners[0]['id'])
 archive=pd.read_csv(P/'inputs/archive_projection.csv.gz',low_memory=False)
 selected=archive[archive.season.eq('2025-26')&archive.code.eq(code)].sort_values('fixture')
 fixtures=pd.read_csv(S.parent/'project/data/2025-26_fixtures.csv.gz').set_index('id')
 rows=[];sources=[]
 for row in selected.itertuples():
  mid=int(fixtures.loc[row.fixture,'pulse_id']);url=f'https://footballapi.pulselive.com/football/stats/player/{pid}?fixtures={mid}&altIds=true';path=P/f'inputs/primary/targeted_{pid}_{mid}.json'
  if not path.exists():
   time.sleep(.6);path.write_bytes(urllib.request.urlopen(url,timeout=35).read())
  raw=path.read_bytes();data=json.loads(raw)
  assert int(data['entity']['id'])==pid and int(data['entity']['altIds']['opta'].lstrip('p'))==code
  stats={x['name']:x['value'] for x in data['stats']};assert stats.get('appearances')==1
  rows.append(dict(season=row.season,fixture=row.fixture,code=code,name=row.name,pl_player_id=pid,pulse_id=mid,**{'pl_'+k:v for k,v in stats.items()}))
  sources.append(dict(url=url,file=str(path.relative_to(P)),sha256=hashlib.sha256(raw).hexdigest()))
  pd.DataFrame(rows).to_csv(P/'inputs/targeted_primary_controls.csv',index=False)
  (P/'targeted_sources.json').write_text(json.dumps(sources,indent=2)+'\n')
  if len(rows)%10==0:print('targeted',len(rows),flush=True)
 print('Completed targeted',len(rows))
if __name__=='__main__':main()
