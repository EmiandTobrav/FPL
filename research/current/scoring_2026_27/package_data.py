from pathlib import Path
import hashlib,json,sys
import pandas as pd
P=Path(__file__).resolve().parent;O=P/'results';D=P/'primary_data'
def run(action):
 if action=='pack':
  D.mkdir(exist_ok=True)
  for name in ['primary_player_counts','primary_player_counts_gw2','bps_2026_diagnostic','bps_2026_diagnostic_gw2']:
   f=pd.read_csv(O/f'{name}.csv');dest=D/name;dest.mkdir(exist_ok=True)
   for i,start in enumerate(range(0,len(f),100)):f.iloc[start:start+100].to_csv(dest/f'part-{i:03d}.csv',index=False)
  (D/'sha256.json').write_text(json.dumps({str(p.relative_to(D)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(D.rglob('*.csv'))},indent=2)+'\n')
 else:
  for name,sha in json.loads((D/'sha256.json').read_text()).items():assert hashlib.sha256((D/name).read_bytes()).hexdigest()==sha
  for folder in D.iterdir():
   if folder.is_dir():pd.concat([pd.read_csv(p) for p in sorted(folder.glob('*.csv'))],ignore_index=True).to_csv(O/f'{folder.name}.csv',index=False)
if __name__=='__main__':run(sys.argv[1])
