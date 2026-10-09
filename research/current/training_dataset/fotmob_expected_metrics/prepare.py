from pathlib import Path
import gzip,hashlib,json
import pandas as pd
P=Path(__file__).resolve().parent;R=P.parents[1];K=['season','fixture','code']
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(x,p):p.write_bytes(gzip.compress(x.to_csv(index=False).encode(),mtime=0))
