from pathlib import Path
import json,hashlib,time,urllib.request
P=Path(__file__).resolve().parent

def main():
 catalog=json.loads((P/'inputs/primary/players_2025-26.json').read_text())
 ids={int(x['owner']['altIds']['opta'].lstrip('p')):int(x['owner']['id']) for x in catalog['stats']['content'] if x['owner'].get('altIds',{}).get('opta')}
 rows=[];sources=[]
 for code in [178186,440993,248875]:
  pid=ids[code];url=f'https://footballapi.pulselive.com/football/stats/player/{pid}?comps=1&compSeasons=777&altIds=true'
  path=P/f'inputs/primary/season_2025_{pid}.json'
  if not path.exists():
   time.sleep(.6);path.write_bytes(urllib.request.urlopen(url,timeout=35).read())
  raw=path.read_bytes();data=json.loads(raw)
  assert int(data['entity']['id'])==pid and int(data['entity']['altIds']['opta'].lstrip('p'))==code
  stats={x['name']:x['value'] for x in data['stats']}
  rows.append(dict(season='2025-26',code=code,primary_season_times_tackled=stats.get('times_tackled'),appearances=stats.get('appearances')))
  sources.append(dict(url=url,file=str(path.relative_to(P)),sha256=hashlib.sha256(raw).hexdigest()))
 (P/'inputs/primary_season_checks.json').write_text(json.dumps(rows,indent=2)+'\n')
 (P/'season_check_sources.json').write_text(json.dumps(sources,indent=2)+'\n')
 print(rows)
if __name__=='__main__':main()
