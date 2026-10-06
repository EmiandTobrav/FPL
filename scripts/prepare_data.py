"""Restore and verify frozen research inputs; standard library only, no ZIP/LFS."""
from pathlib import Path
import gzip, hashlib, json
ROOT = Path(__file__).resolve().parents[1]

def main():
    manifest = json.loads((ROOT/'research/current/data_manifest.json').read_text())
    for item in manifest:
        src = ROOT/item['stored']; dst = ROOT/item['path']
        packed=src.read_bytes()
        if hashlib.sha256(packed).hexdigest()!=item['stored_sha256']:
            raise ValueError(f'Corrupt stored input: {src}')
        data=gzip.decompress(packed)
        if hashlib.sha256(data).hexdigest()!=item['sha256']:
            raise ValueError(f'Corrupt restored input: {dst}')
        dst.parent.mkdir(parents=True,exist_ok=True)
        if not dst.exists() or hashlib.sha256(dst.read_bytes()).hexdigest()!=item['sha256']:
            dst.write_bytes(data)
    (ROOT/'research/current/project/results').mkdir(exist_ok=True)
    for d in ['data/raw','data/interim','data/processed','data/predictions','notebooks']:
        (ROOT/d).mkdir(parents=True,exist_ok=True)
    print(f'Verified {len(manifest)} frozen input files. No network or ZIP extraction required.')
if __name__=='__main__': main()
