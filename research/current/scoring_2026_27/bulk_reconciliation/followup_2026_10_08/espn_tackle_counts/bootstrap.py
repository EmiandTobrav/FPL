"""Restore pinned public response bytes offline, without overwriting changes."""
import hashlib,io,json,tarfile
from pathlib import Path

P=Path(__file__).resolve().parent

def main():
    manifest=json.loads((P/'raw_manifest.json').read_text());raw=(P/'raw_inputs.tar.gz').read_bytes()
    assert hashlib.sha256(raw).hexdigest()==manifest['archive_sha256']
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        members=archive.getmembers();assert {m.name for m in members}==set(manifest['files'])
        for member in members:
            assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            data=archive.extractfile(member).read();assert hashlib.sha256(data).hexdigest()==manifest['files'][member.name]
            dest=P/member.name
            if dest.exists():assert dest.read_bytes()==data,f'Local response changed: {dest}'
            else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    print(f'Verified {len(members)} exact response files')

if __name__=='__main__':main()
