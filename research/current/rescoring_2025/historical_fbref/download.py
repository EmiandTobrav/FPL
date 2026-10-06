"""Restore archived FBref sources; verify exact published asset hashes."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import urllib.request,hashlib,json
P=Path(__file__).resolve().parent
BASE='https://github.com/JaseZiv/worldfootballR_data/releases/download/fb_advanced_match_stats/'
def get(kind):
 p=P/'raw'/f'{kind}.csv';p.parent.mkdir(exist_ok=True)
 expected=json.loads((P/'source_sha256.json').read_text())[p.name]
 if not p.exists() or hashlib.sha256(p.read_bytes()).hexdigest()!=expected:
  tmp=p.with_suffix('.download');urllib.request.urlretrieve(BASE+f'ENG_M_1st_{kind}_player_advanced_match_stats.csv',tmp)
  assert hashlib.sha256(tmp.read_bytes()).hexdigest()==expected,'Source asset changed; do not silently rebuild'
  tmp.replace(p)
 return kind
if __name__=='__main__':
 with ThreadPoolExecutor(2) as ex:print(list(ex.map(get,['defense','misc'])))
