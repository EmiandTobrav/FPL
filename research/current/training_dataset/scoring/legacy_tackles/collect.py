"""Bounded, resumable primary acquisition for a frozen legacy component study."""
import gzip
import hashlib
import io
import json
import tarfile
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED

import pandas as pd

from prepare import P, R, S, digest

STOP, LOCK, NEXT = threading.Event(), threading.Lock(), 0.


def check_freeze():
    freeze = json.loads((P / 'freeze.json').read_text())
    if freeze['outcomes_read'] or digest(P / 'prepare.py') != freeze['code_sha256']:
        raise ValueError('Frozen outcome-independent plan changed')
    for name, sha in freeze['input_sha256'].items():
        if digest(R / name) != sha:
            raise ValueError('Frozen legacy input changed: ' + name)


def normalize(raw, row):
    data = json.loads(raw)
    entity = data['entity']
    if (int(entity['id']) != int(row['pl_player_id'])
            or int(entity['altIds']['opta'].lstrip('p')) != int(row['code'])):
        raise ValueError('Primary entity identity disagreement')
    stats = {x['name']:x['value'] for x in data['stats']}
    if len(stats) != len(data['stats']) or stats.get('appearances') != 1:
        raise ValueError('Duplicate or non-single-appearance primary response')
    return stats


def fetch(row):
    global NEXT
    pid, mid = int(row['pl_player_id']), int(row['pulse_id'])
    name = f'player_{pid}_{mid}.json'
    path = P / 'raw' / name
    reused = S / 'delta_input_audit/inputs/primary' / name
    url = f'https://footballapi.pulselive.com/football/stats/player/{pid}?fixtures={mid}&altIds=true'
    if path.exists():
        raw, origin = path.read_bytes(), 'resumed_local_response'
    elif reused.exists():
        raw, origin = reused.read_bytes(), 'reused_frozen_primary_response'
    else:
        with LOCK:
            delay = max(0, NEXT - time.monotonic())
            NEXT = max(NEXT, time.monotonic()) + .6
        if STOP.wait(delay):
            raise RuntimeError('Stopped after access or rate response')
        try:
            raw = urllib.request.urlopen(urllib.request.Request(url,
                headers={'User-Agent':'FPL-research/1.0'}), timeout=40).read()
        except urllib.error.HTTPError as exc:
            if exc.code in [401,403,429]:
                STOP.set()
            raise
        except urllib.error.URLError:
            STOP.set()  # Fail early on unavailable DNS/network; preserve resumable cache.
            raise
        origin = 'new_primary_response'
    normalize(raw, row)
    if not path.exists():
        tmp = path.with_suffix('.tmp')
        tmp.write_bytes(raw)
        tmp.replace(path)
    return dict(**{k:row[k] for k in ['season','fixture','code']}, url=url, file=name,
        sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw), origin=origin)


def main():
    check_freeze()
    (P / 'raw').mkdir(exist_ok=True)
    rows = pd.read_csv(P / 'plan.csv').to_dict('records')
    entries, errors = [], []
    with ThreadPoolExecutor(max_workers=4) as pool:
        iterator, active = iter(rows), {}
        def submit():
            row = next(iterator, None)
            if row is not None and not STOP.is_set():
                active[pool.submit(fetch, row)] = row
        for _ in range(4):
            submit()
        while active:
            done, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in done:
                row = active.pop(future)
                try:
                    entries.append(future.result())
                except Exception as exc:
                    errors.append(dict(season=row['season'], fixture=row['fixture'],
                        code=row['code'], error=str(exc)))
                submit()
            if len(entries) % 25 == 0 or not active:
                print(dict(completed=len(entries), planned=len(rows), errors=len(errors)), flush=True)
    (P / 'collection_errors.json').write_text(json.dumps(errors, indent=2) + '\n')
    if errors or len(entries) != len(rows):
        raise ValueError('Primary collection incomplete; durable raw cache retained')
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as archive:
        for entry in sorted(entries, key=lambda x:x['file']):
            raw = (P / 'raw' / entry['file']).read_bytes()
            member = tarfile.TarInfo(entry['file'])
            member.size, member.mtime = len(raw), 0
            archive.addfile(member, io.BytesIO(raw))
    path = P / 'raw_inputs.tar.gz'
    path.write_bytes(gzip.compress(buffer.getvalue(), mtime=0))
    manifest = dict(entries=sorted(entries, key=lambda x:(x['season'],x['fixture'],x['code'])),
        archive_sha256=digest(path), plan_freeze_sha256=digest(P / 'freeze.json'),
        collector_code_sha256=digest(P / 'collect.py'), raw_archive_bytes=path.stat().st_size,
        collection_stopped_for_access_or_rate=STOP.is_set())
    (P / 'source_manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    print(dict(completed=len(entries), archive_bytes=path.stat().st_size), flush=True)


if __name__ == '__main__':
    main()
