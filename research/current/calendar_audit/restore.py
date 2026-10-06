"""Restore inspected public-calendar and simulation artifacts from readable files."""
from pathlib import Path
import gzip,hashlib,json
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent

def main():
    manifest=json.loads((HERE/'portable_manifest.json').read_text())
    for item in manifest:
        src=ROOT/item['stored'];dst=ROOT/item['restored']
        assert src.resolve().is_relative_to(ROOT.resolve()) and dst.resolve().is_relative_to(ROOT.resolve())
        raw=src.read_bytes();assert hashlib.sha256(raw).hexdigest()==item['plain_sha256']
        packed=gzip.compress(raw,mtime=0)
        assert hashlib.sha256(packed).hexdigest()==item['compressed_sha256'],'Compression differs; use recorded Python/zlib environment to restore exact archived bytes'
        dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists() or dst.read_bytes()!=packed:dst.write_bytes(packed)
    print('Verified/restored',len(manifest),'readable calendar and simulation artifacts')
if __name__=='__main__':main()
