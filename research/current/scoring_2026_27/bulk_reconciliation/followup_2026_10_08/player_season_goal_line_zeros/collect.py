"""Complete the fixed explicit-zero source trial; never infer omitted values."""
from pathlib import Path
import json,hashlib,urllib.request
P=Path(__file__).resolve().parent
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 for n,h in json.loads((P/'selection_freeze.json').read_text()).items():assert digest(P/n)==h,n
 sources=json.loads((P/'sources.json').read_text())
 seasons=json.loads((P/'plan.json').read_text())['seasons']
 if (P/'control_extension_plan.json').exists():
  for n,h in json.loads((P/'control_extension_freeze.json').read_text()).items():
   if n!='sources.json':assert digest(P/n)==h,n
  seasons.update(json.loads((P/'control_extension_plan.json').read_text())['additional_control_seasons'])
 for season,cid in seasons.items():
  if any(x['season']==season for x in sources):continue
  url=f'https://footballapi.pulselive.com/football/stats/ranked/players/clearance_off_line?comps=1&compSeasons={cid}&page=0&pageSize=1000&altIds=true'
  path=P/'inputs'/f'{season}.json';assert not path.exists()
  req=urllib.request.Request(url,headers={'Origin':'https://www.premierleague.com','User-Agent':'FPL-research/1.0'})
  with urllib.request.urlopen(req,timeout=30) as response:raw=response.read()
  path.write_bytes(raw);sources.append(dict(season=season,url=url,file=str(path.relative_to(P)),sha256=digest(path)))
  (P/'sources.json').write_text(json.dumps(sources,indent=2)+'\n')
  x=json.loads(raw);assert x['entity']=='clearance_off_line' and x['stats']['pageInfo']['numPages']==1
  rows=x['stats']['content'];assert len(rows)==x['stats']['pageInfo']['numEntries']
  zeros=sum(v.get('value')==0 for v in rows);print(season,'records',len(rows),'explicitzero',zeros,flush=True)
  if not zeros:break
if __name__=='__main__':main()
