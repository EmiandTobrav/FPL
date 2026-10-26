import csv,gzip,lzma,json,hashlib,math
from pathlib import Path
from datetime import datetime
P=Path(__file__).resolve().parent;R=P.parents[1]
OLD=R/'datasets/fpl_master_enriched_v4';OUT=R/'datasets/fpl_master_enriched_v5'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def dt(s):return datetime.fromisoformat(s.replace('Z','+00:00'))
def num(v):return str(int(float(v)))
def truth(v):return str(v).lower() in ['true','1','1.0']
def number(v):
 try:
  x=float(v);return x if math.isfinite(x) else None
 except (ValueError,TypeError):return None
def read(p):
 op=lzma.open if str(p).endswith('.xz') else gzip.open if str(p).endswith('.gz') else open
 with op(p,'rt',newline='') as f:yield from csv.DictReader(f)
def write(name,rows):
 it=iter(rows);first=next(it);op=lzma.open if name.endswith('.xz') else gzip.open if name.endswith('.gz') else open
 kw={'preset':3} if name.endswith('.xz') else {}
 with op(P/name,'wt',newline='',**kw) as f:
  w=csv.DictWriter(f,fieldnames=list(first));w.writeheader();w.writerow(first);w.writerows(it)
def dump(path,obj):path.write_text(json.dumps(obj,indent=2,ensure_ascii=False)+'\n')
def avg(v):return sum(v)/len(v) if v else None
START_QUALITY={'qualified_explicit_lineup','qualified_complete_start_inventory_zero','native_compatible_fpl','native_fpl','explicit_primary_structural_repair'}
