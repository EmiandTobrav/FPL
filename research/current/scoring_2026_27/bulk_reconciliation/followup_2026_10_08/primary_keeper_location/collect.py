"""Reuse recorded primary responses; fetch remaining public scopes once."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
import gzip
import hashlib
import json
import threading
import time
import urllib.request
import urllib.error
import pandas as pd

P = Path(__file__).resolve().parent
R = P.parents[3]
LOCK = threading.Lock()
STOP = threading.Event()
NEXT = 0.0

def digest(b):
    return hashlib.sha256(b).hexdigest()

def main():
    protocol = json.loads((P/'protocol.json').read_text())
    assert digest((P/'plan.csv').read_bytes()) == protocol['plan_sha256']
    plan = pd.read_csv(P/'plan.csv').to_dict('records')
    candidates = {}
    for path in sorted(R.rglob('player_*.json')):
        candidates.setdefault(path.name, []).append(path)
    old = R/'training_dataset/scoring/season_2025'
    kelleher = pd.read_csv(old/'keeper_revision_sources.csv').set_index('fixture')

    def fetch(row):
        global NEXT
        fixture, code = int(row['fixture']), int(row['code'])
        dest = P/f'inputs/raw/{code}_{fixture}.json.gz'
        origin, url, observed = None, row['url'], None
        if code == 200720:
            item = kelleher.loc[fixture]
            source = old/item.file
            assert digest(source.read_bytes()) == item.file_sha256
            raw = gzip.decompress(source.read_bytes())
            assert digest(raw) == item.raw_sha256
            origin, url = str(source.relative_to(R)), item.url
        elif fixture:
            name = f"player_{int(row['pl_player_id'])}_{int(row['pulse_id'])}.json"
            for source in candidates.get(name, []):
                raw = source.read_bytes()
                obj = json.loads(raw)
                if int(obj['entity']['id']) == row['pl_player_id'] and obj['entity'].get('altIds', {}).get('opta') == f'p{code}':
                    origin = str(source.relative_to(R))
                    url = row['url'].replace('&altIds=true', '')
                    break
        if origin is None:
            if dest.exists():
                raise RuntimeError('Unmanifested cached file: recover its recorded collection, do not invent provenance')
            with LOCK:
                delay = max(0, NEXT-time.monotonic())
                NEXT = max(NEXT, time.monotonic())+.5
            if delay:
                time.sleep(delay)
            if STOP.is_set():
                raise RuntimeError('Public-source collection stopped')
            try:
                raw = urllib.request.urlopen(url, timeout=35).read()
            except urllib.error.HTTPError as exc:
                if exc.code in [401, 403, 429]:
                    STOP.set()
                raise
            observed = datetime.now(timezone.utc).isoformat()
        obj = json.loads(raw)
        assert int(obj['entity']['id']) == row['pl_player_id']
        assert obj['entity']['altIds']['opta'] == f'p{code}'
        dest.write_bytes(gzip.compress(raw, mtime=0))
        return dict(season=row['season'], fixture=fixture, code=code, url=url,
            path=str(dest.relative_to(P)), raw_sha256=digest(raw), file_sha256=digest(dest.read_bytes()),
            reused_from=origin or '', observed_at=observed or '', reused=origin is not None)

    rows, errors = [], []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(fetch, row):row for row in plan}
        for future in as_completed(futures):
            try:
                rows.append(future.result())
            except Exception as exc:
                errors.append(dict(**futures[future], error=repr(exc)))
            if (len(rows)+len(errors)) % 25 == 0:
                print(json.dumps(dict(completed=len(rows), errors=len(errors), reused=sum(x['reused'] for x in rows))), flush=True)
            if STOP.is_set():
                for other in futures:
                    other.cancel()
    pd.DataFrame(rows).sort_values(['code','fixture']).to_csv(P/'inputs/source_manifest.csv', index=False)
    (P/'inputs/errors.json').write_text(json.dumps(errors, indent=2)+'\n')
    print(json.dumps(dict(completed=len(rows), errors=len(errors), reused=sum(x['reused'] for x in rows))), flush=True)
    if errors:
        raise RuntimeError('Collection incomplete; no application permitted')

if __name__ == '__main__':
    main()
