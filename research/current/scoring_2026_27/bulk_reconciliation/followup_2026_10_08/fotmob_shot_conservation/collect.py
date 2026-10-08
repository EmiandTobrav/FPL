"""Collect public, fixed-plan FotMob evidence without interpreting missing counters."""
from pathlib import Path
import concurrent.futures
import gzip
import hashlib
import json
import urllib.request
import pandas as pd

P = Path(__file__).resolve().parent

def fetch(row):
    mid = int(row['fotmob_match_id'])
    url = f'https://www.fotmob.com/api/data/matchDetails?matchId={mid}'
    path = P / 'inputs' / 'raw' / f'{mid}.json.gz'
    if path.exists():
        raw = gzip.decompress(path.read_bytes())
    else:
        pilot = Path('/private/tmp/fpl-shot-source-pilot') / f'{mid}.json'
        if pilot.exists():
            raw = pilot.read_bytes()
        else:
            request = urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'})
            with urllib.request.urlopen(request, timeout=30) as response:
                raw = response.read()
        json.loads(raw)
        path.write_bytes(gzip.compress(raw, mtime=0))
    return dict(season=row['season'], fixture=int(row['fixture']),
                fotmob_match_id=mid, url=url, raw_sha256=hashlib.sha256(raw).hexdigest(),
                file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                path=str(path.relative_to(P)))

def main():
    protocol = json.loads((P / 'protocol.json').read_text())
    assert hashlib.sha256((P / 'plan.csv').read_bytes()).hexdigest() == protocol['plan_sha256']
    (P / 'inputs/raw').mkdir(exist_ok=True)
    rows = pd.read_csv(P / 'plan.csv').to_dict('records')
    collected = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        for result in pool.map(fetch, rows):
            collected.append(result)
            if len(collected) % 20 == 0:
                print(f'Collected {len(collected)}/{len(rows)} public match responses', flush=True)
    pd.DataFrame(collected).sort_values(['season','fixture']).to_csv(P / 'inputs/source_manifest.csv',index=False)
    print(f'Collected {len(collected)} responses', flush=True)

if __name__ == '__main__':
    main()
