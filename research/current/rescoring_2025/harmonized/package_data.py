"""Store expensive observations and derived labels as reviewable plaintext partitions."""
import argparse,json,hashlib,gzip
from pathlib import Path
import pandas as pd
P=Path(__file__).resolve().parent;O=P/'results';D=P/'dataset'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def prepare_inputs():
 root=P.parents[1];manifest=O/'manifest.json'
 expected=json.loads(manifest.read_text()).get('inputs_sha256',{}) if manifest.exists() else {}
 for year in range(2019,2026):
  season=f'{year}-{str(year+1)[2:]}'
  for kind in ['gw','players','fixtures','teams']:
   path=root/f'project/data/{season}_{kind}.csv'
   if not path.exists():
    compressed=path.with_suffix('.csv.gz')
    if not compressed.exists():raise FileNotFoundError(f'Missing repository input: {compressed}')
    path.write_bytes(gzip.decompress(compressed.read_bytes()))
   wanted=expected.get(str(path.relative_to(root)))
   if wanted:assert sha(path)==wanted,f'Frozen FPL input changed: {path}'

def pack(seasons):
 for season in seasons:
  for kind in ['counts','labels']:
   source=O/f'{season}_{kind}.csv';dest=D/kind/season;dest.mkdir(parents=True,exist_ok=True)
   for old in dest.glob('part-*.csv'):old.unlink()
   frame=pd.read_csv(source)
   for i,start in enumerate(range(0,len(frame),2500)):
    frame.iloc[start:start+2500].to_csv(dest/f'part-{i:03d}.csv',index=False)
  sources=[s for s in json.loads((O/'sources.json').read_text()) if s['season']==season]
  assert len(sources)==380
  path=D/'sources';path.mkdir(parents=True,exist_ok=True);(path/f'{season}.json').write_text(json.dumps(sources,indent=2)+'\n')
 validation=O/'validation_2025.csv'
 if validation.exists():
  dest=D/'validation';dest.mkdir(exist_ok=True)
  frame=pd.read_csv(validation)
  for i,start in enumerate(range(0,len(frame),2500)):frame.iloc[start:start+2500].to_csv(dest/f'part-{i:03d}.csv',index=False)
 files={str(p.relative_to(D)):sha(p) for p in sorted(D.rglob('*')) if p.is_file() and p.name!='sha256.json'}
 (D/'sha256.json').write_text(json.dumps(files,indent=2)+'\n')
def restore():
 for name,expected in json.loads((D/'sha256.json').read_text()).items():assert sha(D/name)==expected,name
 O.mkdir(exist_ok=True);sources=[]
 for kind in ['counts','labels']:
  for season in sorted((D/kind).iterdir()):
   pd.concat([pd.read_csv(p) for p in sorted(season.glob('part-*.csv'))],ignore_index=True).to_csv(O/f'{season.name}_{kind}.csv',index=False)
 if (D/'validation').exists():pd.concat([pd.read_csv(p) for p in sorted((D/'validation').glob('part-*.csv'))],ignore_index=True).to_csv(O/'validation_2025.csv',index=False)
 for p in sorted((D/'sources').glob('*.json')):sources.extend(json.loads(p.read_text()))
 (O/'sources.json').write_text(json.dumps(sorted(sources,key=lambda x:(x['season'],x['fixture'])),indent=2)+'\n')
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('action',choices=['pack','restore']);ap.add_argument('seasons',nargs='*');a=ap.parse_args()
 if a.action=='pack':pack(a.seasons)
 else:restore()
