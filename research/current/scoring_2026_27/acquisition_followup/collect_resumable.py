"""Checkpointed PL player/match collector. Missing counters remain missing.

Input CSV: season,fixture,code,pl_player_id,pulse_id (plus optional metadata).
Does not assign fantasy points or declare historical coverage complete.
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import argparse
import csv
import hashlib
import json
import os
import threading
import time
import urllib.error
import urllib.request

STOP = threading.Event()
LOCK = threading.Lock()
NEXT = 0.0


def normalize(payload, row):
    entity = payload['entity']
    if int(entity['id']) != int(row['pl_player_id']):
        raise ValueError('player identity mismatch')
    opta = entity.get('altIds', {}).get('opta')
    if opta is not None and int(str(opta).lstrip('p')) != int(row['code']):
        raise ValueError('Opta identity mismatch')
    pairs = payload['stats']
    stats = {item['name']: item['value'] for item in pairs}
    if len(stats) != len(pairs):
        raise ValueError('duplicate statistic names')
    if stats.get('appearances') != 1 or stats.get('mins_played', 0) <= 0:
        raise ValueError('not one active player appearance')
    return dict(row, **{'pl_' + key: value for key, value in stats.items()})


def atomic_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    os.replace(temporary, path)


def fetch(row, cache, interval):
    global NEXT
    pid, mid = int(row['pl_player_id']), int(row['pulse_id'])
    url = f'https://footballapi.pulselive.com/football/stats/player/{pid}?fixtures={mid}&altIds=true'
    path = cache / f'player_{pid}_{mid}.json'
    cached = path.exists()
    if cached:
        raw = path.read_bytes()
    else:
        with LOCK:
            delay = max(0, NEXT - time.monotonic())
            NEXT = max(NEXT, time.monotonic()) + interval
        if STOP.wait(delay):
            raise RuntimeError('stopped after access or rate-limit response')
        try:
            raw = urllib.request.urlopen(url, timeout=30).read()
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403, 429):
                STOP.set()
            raise
    normalized = normalize(json.loads(raw), row)
    if not cached:
        temporary = path.with_suffix('.json.tmp')
        temporary.write_bytes(raw)
        os.replace(temporary, path)
    return dict(row=normalized, source=dict(url=url, sha256=hashlib.sha256(raw).hexdigest(),
                file=path.name, reused_cache=cached))


def run(manifest, output, limit=None, workers=6, interval=0.75):
    STOP.clear()
    with manifest.open() as handle:
        rows = list(csv.DictReader(handle))
    keys = [(r['season'], r['fixture'], r['code']) for r in rows]
    if len(set(keys)) != len(keys):
        raise ValueError('duplicate input keys')
    primary_keys = [(r['pl_player_id'], r['pulse_id']) for r in rows]
    if len(set(primary_keys)) != len(primary_keys):
        raise ValueError('duplicate provider keys')
    output.mkdir(parents=True, exist_ok=True)
    cache = output / 'raw'
    cache.mkdir(exist_ok=True)
    state_path = output / 'checkpoint.json'
    state = json.loads(state_path.read_text()) if state_path.exists() else {'completed': {}, 'errors': {}}
    digest = hashlib.sha256(manifest.read_bytes()).hexdigest()
    if state.get('manifest_sha256', digest) != digest:
        raise ValueError('manifest changed: use a new output directory')
    state['manifest_sha256'] = digest
    # Only checkpoints with their verified raw response can be reused.
    for key, record in list(state['completed'].items()):
        path = cache / record['source']['file']
        if not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != record['source']['sha256']:
            raise ValueError(f'missing or corrupt cached response: {key}')
    def key(row):
        return f"{row['season']}:{row['fixture']}:{row['code']}"
    pending = [r for r in rows if key(r) not in state['completed']]
    if limit is not None:
        pending = pending[:limit]
    iterator = iter(pending)
    with ThreadPoolExecutor(max_workers=workers) as pool:
        active = {}
        def submit():
            row = next(iterator, None)
            if row is not None and not STOP.is_set():
                active[pool.submit(fetch, row, cache, interval)] = row
        for _ in range(workers):
            submit()
        while active:
            done, _ = wait(active, return_when=FIRST_COMPLETED)
            for future in done:
                row = active.pop(future)
                identity = key(row)
                try:
                    state['completed'][identity] = future.result()
                    state['errors'].pop(identity, None)
                except Exception as exc:
                    state['errors'][identity] = dict(error=repr(exc), row=row)
                # A completed request is durable before the next is submitted.
                atomic_json(state_path, state)
                submit()
            print(f"checkpoint {len(state['completed'])}/{len(rows)}; errors {len(state['errors'])}", flush=True)
    records = [state['completed'][k]['row'] for k in sorted(state['completed'])]
    if records:
        columns = list(dict.fromkeys(k for record in records for k in record))
        with (output / 'observations.csv').open('w') as handle:
            writer = csv.DictWriter(handle, fieldnames=columns)
            writer.writeheader()
            writer.writerows(records)
    summary = dict(requested_rows=len(rows), completed_rows=len(records), errors=len(state['errors']),
                   remaining_rows=len(rows)-len(records), stopped_for_access_or_rate_limit=STOP.is_set(),
                   full_historical_rescoring_ready=False, missing_policy='omitted counters stay blank',
                   manifest_sha256=digest)
    atomic_json(output / 'summary.json', summary)
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('manifest', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    print(run(args.manifest, args.output, args.limit))
