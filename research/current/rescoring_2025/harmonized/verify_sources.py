"""Optional freeze-time raw-response audit; requires local collector cache."""
import json,hashlib
import pandas as pd
from collect import P,RAW,CACHE,OUT,parse,FIELDS
manifest=pd.read_csv(OUT/'fixture_manifest.csv');checked=0
for f in manifest.to_dict('records'):
 mid=f['match_id'];cached=json.loads((CACHE/f'{mid}.json').read_text())
 raw=next(p for p in [RAW/f'fotmob_{mid}.json',P.parent/'missing_2021/raw'/f'fotmob_{mid}.json',P.parent/'final_gaps/raw'/f'fotmob_{mid}.json'] if p.exists())
 b=raw.read_bytes();assert hashlib.sha256(b).hexdigest()==cached['sha256']
 assert cached['season']==f['season'] and cached['fixture']==f['id'] and cached['match_id']==mid
 rows=parse(json.loads(b),f);assert rows==cached['rows']
 for row in rows:
  for field in FIELDS.values():
   value=row.get(field)
   if value is not None:assert value>=0 and int(value)==value,(mid,row['code'],field,value)
 checked+=1
assert checked==2660
(OUT/'source_integrity.json').write_text(json.dumps(dict(raw_hashes_verified=checked,metadata_reparsed=checked,cache_rows_reproduced=checked,nonnegative_integer_counts=True),indent=2)+'\n')
print('Verified',checked,'raw responses and normalized match caches')
