"""Explicit reported-role context; no strict historical qualification implied."""
import csv,hashlib,json,lzma
from pathlib import Path
P=Path(__file__).resolve().parent
def iter_context(by_round=False,strict=False):
 name='player_round_context.csv.xz' if by_round else 'player_match_context.csv.xz';path=P/name;m=json.loads((P/'manifest.json').read_text());assert hashlib.sha256(path.read_bytes()).hexdigest()==m['files'][name]
 with lzma.open(path,'rt') as f:
  for row in csv.DictReader(f):
   if strict and row['sp_strict_historical_qualified']!='True':continue
   yield row
