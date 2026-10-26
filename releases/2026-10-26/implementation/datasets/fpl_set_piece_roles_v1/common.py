"""Source-locked set-piece metadata using the availability cutoffs."""
import csv,gzip,lzma,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
P=Path(__file__).resolve().parent;R=P.parents[1];AV=R/'datasets/fpl_availability_all_seasons_v1';MASTER=R/'datasets/fpl_master_enriched_v3';OUT=R/'datasets/fpl_master_enriched_v4'
ROLES={'penalties':'penalties','corners_indirect_freekicks':'corners_and_indirect_freekicks','direct_freekicks':'direct_freekicks'}
def dt(v):return datetime.fromisoformat(v.replace('Z','+00:00'))
def num(v):return str(int(float(v)))
def truth(v):return str(v).lower() in ['true','1']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):
 op=lzma.open if str(p).endswith('.xz') else gzip.open if str(p).endswith('.gz') else open
 with op(p,'rt') as f:yield from csv.DictReader(f)
def write(name,rows,fields=None):
 it=iter(rows);first=next(it,None)
 if first is None and fields is None:raise ValueError(name)
 op=lzma.open if name.endswith('.xz') else gzip.open if name.endswith('.gz') else open;kw={'preset':3} if name.endswith('.xz') else {}
 with op(P/name,'wt',newline='',**kw) as f:
  w=csv.DictWriter(f,fieldnames=fields or list(first));w.writeheader()
  if first is not None:w.writerow(first)
  w.writerows(it)
def null(v):return v is None or str(v) in ['', 'None','nan','null']
def order(v):
 if null(v):return None,True
 try:
  x=float(v)
  return (int(x),True) if x>0 and x==int(x) else (None,False)
 except (ValueError,TypeError,OverflowError):return None,False
def raw_players(audit):
 path=R/audit['source_file']
 if audit['format']=='bootstrap':
  d=json.loads(lzma.decompress(path.read_bytes()));return d['elements'],{num(t['id']):t['name'] for t in d['teams']}
 teams={num(t['id']):t['name'] for t in read(R/'FPL_training_dataset/research/current/project/data'/f'{audit["season"]}_teams.csv.gz')}
 return list(read(path)),teams
