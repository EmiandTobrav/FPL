"""Losslessly package this task's own raw responses; retain original-content hashes."""
from pathlib import Path
import gzip,json,hashlib
P=Path(__file__).resolve().parent

def main():
 count=0
 for p in sorted((P/'inputs/matches').glob('*.json')):
  raw=p.read_bytes();packed=gzip.compress(raw,mtime=0)
  target=p.with_suffix('.json.gz')
  if target.exists() and gzip.decompress(target.read_bytes())!=raw:raise ValueError('Existing packed response differs')
  target.write_bytes(packed)
  if gzip.decompress(target.read_bytes())!=raw:raise ValueError('Compression failed')
  p.unlink();count+=1
 for stage in ['pilot','holdout','full']:
  p=P/f'{stage}_sources.json'
  if not p.exists():continue
  rows=json.loads(p.read_text())
  for row in rows:
   if row['file'].endswith('.json'):row['file']+='.gz'
   if hashlib.sha256(gzip.decompress((P/row['file']).read_bytes())).hexdigest()!=row['sha256']:raise ValueError('Primary response hash changed')
  p.write_text(json.dumps(rows,indent=2)+'\n')
 print('Losslessly packed',count,'raw responses')
if __name__=='__main__':main()
