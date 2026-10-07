"""Verify every retained primary response against the published normalized totals."""
from pathlib import Path
import gzip,hashlib,json
import pandas as pd
from collect import normalize
P=Path(__file__).resolve().parent

def main():
 plan=pd.read_csv(P/'collection_plan.csv').set_index(['season','fixture'])
 sources=json.loads((P/'full_sources.json').read_text());rows=[]
 if len(sources)!=len(plan):raise ValueError('Incomplete primary collection')
 if len({(s['season'],s['fixture']) for s in sources})!=len(plan):raise ValueError('Duplicate primary fixture')
 for s in sources:
  p=P/s['file'];raw=gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_bytes()
  if hashlib.sha256(raw).hexdigest()!=s['sha256']:raise ValueError('Raw primary drift')
  row=plan.loc[(s['season'],s['fixture'])].to_dict();row.update(season=s['season'],fixture=s['fixture'])
  rows.extend(normalize(raw,row))
 rebuilt=pd.DataFrame(rows).sort_values(['season','fixture','side']).reset_index(drop=True)
 saved=pd.read_csv(P/'full_team_totals.csv').sort_values(['season','fixture','side']).reset_index(drop=True)
 pd.testing.assert_frame_equal(rebuilt[saved.columns],saved,check_dtype=False)
 (P/'source_verification.json').write_text(json.dumps(dict(primary_fixtures=len(sources),team_rows=len(saved),raw_hashes_verified=True,normalization_reproduced=True,missing_counters_retained=True),indent=2)+'\n')
 print('Verified',len(sources),'primary responses;',len(saved),'team rows')
if __name__=='__main__':main()
