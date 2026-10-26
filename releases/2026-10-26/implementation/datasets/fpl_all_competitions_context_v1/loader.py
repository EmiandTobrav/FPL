"""Read external workload or context explicitly; never mix external FPL labels."""
import csv,gzip,lzma,hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
def records(table='player_match_context.csv.xz'):
 if table not in ['player_match_context.csv.xz','player_round_context.csv.xz','player_minutes.csv.gz','matches.csv.gz']:raise ValueError('Explicit released table required')
 p=P/table;m=json.loads((P/'manifest.json').read_text());assert hashlib.sha256(p.read_bytes()).hexdigest()==m['files'][table]
 op=lzma.open if table.endswith('.xz') else gzip.open
 with op(p,'rt') as f:
  for r in csv.DictReader(f):
   if table in ['player_minutes.csv.gz','matches.csv.gz']:
    assert r['is_fpl_fixture']=='False' and r['data_role']=='workload_context'
    if table=='player_minutes.csv.gz':assert r['code'] and r['element']
   yield r
