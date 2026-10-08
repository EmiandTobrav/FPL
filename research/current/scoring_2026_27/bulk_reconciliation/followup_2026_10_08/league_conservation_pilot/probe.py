from pathlib import Path
import urllib.request,urllib.error,json,hashlib
P=Path(__file__).resolve().parent
# One bounded schema probe: does a season-scoped competition aggregate exist?
u='https://footballapi.pulselive.com/football/stats/comp/1?compSeasons=274&altIds=true'
try:
 b=urllib.request.urlopen(urllib.request.Request(u,headers={'Origin':'https://www.premierleague.com','User-Agent':'FPL-research/1.0'}),timeout=30).read();(P/'response.json').write_bytes(b);d=json.loads(b);print(str(d)[:2500]);result=dict(url=u,sha256=hashlib.sha256(b).hexdigest(),status=200)
except urllib.error.HTTPError as e:result=dict(url=u,status=e.code);print(result)
(P/'source_attempt.json').write_text(json.dumps(result,indent=2)+'\n')
