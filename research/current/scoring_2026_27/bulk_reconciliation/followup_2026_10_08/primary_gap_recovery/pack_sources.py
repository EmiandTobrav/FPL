from pathlib import Path
import tarfile,io,gzip,json,hashlib
P=Path(__file__).resolve().parent;entries=[];buf=io.BytesIO()
with tarfile.open(fileobj=buf,mode='w') as tar:
 for f in sorted((P/'inputs').glob('*.json')):
  b=f.read_bytes();name=f.relative_to(P).as_posix();i=tarfile.TarInfo(name);i.size=len(b);i.mtime=0;i.mode=0o644;tar.addfile(i,io.BytesIO(b));entries.append(dict(file=name,bytes=len(b),sha256=hashlib.sha256(b).hexdigest()))
b=gzip.compress(buf.getvalue(),mtime=0);(P/'raw_inputs.tar.gz').write_bytes(b);(P/'raw_manifest.json').write_text(json.dumps(dict(archive_sha256=hashlib.sha256(b).hexdigest(),entries=entries),indent=2)+'\n');print('Packed',len(entries),'files;',len(b),'bytes')
