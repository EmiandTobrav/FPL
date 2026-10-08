"""Restore exact original gzip ledgers from committed byte parts, offline.

No recompression, external archives, machine paths or authentication required.
Existing local files are checked, never overwritten.
"""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent
for row in json.loads((P/'ledger_parts.json').read_text()):
 dest=P/row['original']
 if dest.exists():
  assert hashlib.sha256(dest.read_bytes()).hexdigest()==row['sha256'],f'Local file differs; preserve and inspect: {dest}'
 else:
  chunks=[]
  for part in row['parts']:
   b=(P/part['path']).read_bytes();assert len(b)==part['bytes'] and hashlib.sha256(b).hexdigest()==part['sha256'],part['path'];chunks.append(b)
  raw=b''.join(chunks);assert len(raw)==row['bytes'] and hashlib.sha256(raw).hexdigest()==row['sha256'];dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
 print('Verified original ledger:',row['original'])
