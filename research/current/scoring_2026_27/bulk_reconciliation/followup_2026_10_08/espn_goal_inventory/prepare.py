from pathlib import Path
import hashlib,json,gzip
import pandas as pd
P=Path(__file__).resolve().parent;S=P.parent;B=S.parent;R=B.parent.parent;K=['season','fixture','code']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(x,p):p.write_bytes(gzip.compress(x.to_csv(index=False).encode(),mtime=0))
def freeze_write(p,b):
    if p.exists():assert p.read_bytes()==b,p
    p.write_bytes(b)
