from pathlib import Path
import urllib.request,json,re,hashlib
P=Path(__file__).resolve().parent
u='https://www.premierleague.com/en/stats/top/clubs/total-clearances'
f=P/'official_stats_page.html'
if not f.exists():f.write_bytes(urllib.request.urlopen(u,timeout=30).read())
s=f.read_text();src=re.findall(r'<script[^>]*src="([^"]+)"',s);print(json.dumps(src,indent=2));(P/'page_source.json').write_text(json.dumps(dict(url=u,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),scripts=src),indent=2)+'\n')
