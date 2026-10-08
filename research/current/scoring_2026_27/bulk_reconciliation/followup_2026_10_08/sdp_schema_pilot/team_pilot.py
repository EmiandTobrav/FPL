from pathlib import Path
import urllib.request,json,hashlib
P=Path(__file__).resolve().parent;u='https://sdp-prem-prod.premier-league-prod.pulselive.com/api/v2/competitions/8/seasons/2019/teams/1/stats';f=P/'manutd2019.json'
if not f.exists():f.write_bytes(urllib.request.urlopen(urllib.request.Request(u,headers={'Origin':'https://www.premierleague.com'}),timeout=30).read())
d=json.loads(f.read_bytes());print(str(d)[:5500]);(P/'pilot_source.json').write_text(json.dumps(dict(url=u,sha256=hashlib.sha256(f.read_bytes()).hexdigest()),indent=2)+'\n')
