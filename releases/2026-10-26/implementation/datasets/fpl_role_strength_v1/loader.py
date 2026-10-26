"""Read explicit descriptive context; no automatic use by forecasting models."""
import csv,hashlib,json,lzma
from pathlib import Path
P=Path(__file__).resolve().parent
def iter_context(by_round=False,strict=False):
 name='player_round_role_context.csv.xz' if by_round else 'player_match_context.csv.xz';path=P/name
 manifest=json.loads((P/'manifest.json').read_text())
 if hashlib.sha256(path.read_bytes()).hexdigest()!=manifest['files'][name]:raise ValueError('Context file hash mismatch')
 with lzma.open(path,'rt') as f:
  for row in csv.DictReader(f):
   if strict and row['pr_strict_historical_qualified']!='True':continue
   yield row
