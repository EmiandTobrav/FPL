from pathlib import Path
import gzip, hashlib, json
import pandas as pd

P = Path(__file__).resolve().parent
B = P.parents[1]
R = P.parents[3]
K = ['season', 'fixture', 'code', 'field']

def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def save(x, p): p.write_bytes(gzip.compress(x.to_csv(index=False).encode(), mtime=0) if p.suffix == '.gz' else x.to_csv(index=False).encode())

