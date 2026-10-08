"""Restore committed raw responses offline; never overwrite differing local files."""
from pathlib import Path
import tarfile,hashlib,json,io
P=Path(__file__).resolve().parent;m=json.loads((P/'raw_manifest.json').read_text());b=(P/'raw_inputs.tar.gz').read_bytes();assert hashlib.sha256(b).hexdigest()==m['archive_sha256'];expected={r['file']:r for r in m['entries']}
with tarfile.open(fileobj=io.BytesIO(b),mode='r:gz') as t:
 members=t.getmembers();assert len(members)==len(expected) and {x.name for x in members}==set(expected)
 for member in members:
  r=expected[member.name];assert member.isfile() and member.name.startswith('inputs/') and '..' not in Path(member.name).parts and not Path(member.name).is_absolute();raw=t.extractfile(member).read();assert len(raw)==r['bytes'] and hashlib.sha256(raw).hexdigest()==r['sha256'];dest=P/member.name
  if dest.exists():assert dest.read_bytes()==raw,f'Preserve differing local file: {dest}'
  else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
print('Verified/restored',len(expected),'raw input files')
