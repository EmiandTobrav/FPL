from pathlib import Path
import json,urllib.request,hashlib,pandas as pd,time
P=Path(__file__).resolve().parent
p=P/'inputs';p.mkdir(exist_ok=True)
def get(url,name):
 f=p/name
 if not f.exists():
  req=urllib.request.Request(url,headers={'Origin':'https://www.premierleague.com','User-Agent':'FPL-research/1.0'});b=urllib.request.urlopen(req,timeout=40).read();f.write_bytes(b)
 else:b=f.read_bytes()
 return json.loads(b),dict(url=url,file='inputs/'+name,sha256=hashlib.sha256(b).hexdigest())
fixture,src=get('https://footballapi.pulselive.com/football/fixtures/46737?altIds=true','fixture_46737.json');sources=[src]
for side in fixture['teamLists']:
 for player in side['lineup'][1:3]:
  pid=int(player['id']);x,s=get(f'https://footballapi.pulselive.com/football/stats/player/{pid}?fixtures=46737&altIds=true',f'player_{pid}_46737.json');sources.append(s);d={v['name']:v['value'] for v in x['stats']};assert x['entity']['altIds']['opta']==player['altIds']['opta'];print(player['name']['display'],{k:d.get(k) for k in ['appearances','mins_played','total_tackle','won_tackle','fk_foul_won','was_fouled','ontarget_scoring_att','clearance_off_line','total_clearance','outfielder_block','interception','times_tackled']},flush=True)
(P/'pilot_sources.json').write_text(json.dumps(sources,indent=2)+'\n')
