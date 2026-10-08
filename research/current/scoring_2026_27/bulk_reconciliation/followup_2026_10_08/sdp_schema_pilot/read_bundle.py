from pathlib import Path
import urllib.request,re,json,hashlib
P=Path(__file__).resolve().parent;u='https://www.premierleague.com/resources/v1.54.15/scripts/bundle-es.min.js';f=P/'bundle.js'
if not f.exists():f.write_bytes(urllib.request.urlopen(u,timeout=30).read())
s=f.read_text();patterns=[r'.{0,120}/stats.{0,180}',r'.{0,80}clearanceOffLine.{0,120}',r'.{0,100}compSeasons.{0,160}'];out={p:re.findall(p,s)[:40] for p in patterns};print(json.dumps(out,indent=2));(P/'bundle_source.json').write_text(json.dumps(dict(url=u,sha256=hashlib.sha256(f.read_bytes()).hexdigest()),indent=2)+'\n')
