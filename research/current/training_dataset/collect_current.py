"""Resumable, rate-limited official FPL element-history snapshot collection."""
from pathlib import Path
import argparse
import concurrent.futures
import datetime
import hashlib
import json
import threading
import time
import urllib.error
import urllib.request

def collect(snapshot):
    raw = snapshot / 'raw'
    bootstrap_bytes = (raw / 'bootstrap-static.json').read_bytes()
    bootstrap = json.loads(bootstrap_bytes)
    digest = hashlib.sha256(bootstrap_bytes).hexdigest()
    output = raw / 'element-summary'
    output.mkdir(exist_ok=True)
    checkpoint_path = snapshot / 'collection_checkpoint.json'
    checkpoint = json.loads(checkpoint_path.read_text()) if checkpoint_path.exists() else {
        'bootstrap_sha256': digest, 'started_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'completed': {}, 'errors': {}}
    if checkpoint['bootstrap_sha256'] != digest:
        raise ValueError('Bootstrap changed: use a new snapshot directory')
    for eid, record in checkpoint['completed'].items():
        if hashlib.sha256((output / f'{eid}.json').read_bytes()).hexdigest() != record['sha256']:
            raise ValueError('Cached history changed')
    lock, stop = threading.Lock(), threading.Event()
    clock = [0.0]
    def fetch(player):
        eid = player['id']
        url = f'https://fantasy.premierleague.com/api/element-summary/{eid}/'
        with lock:
            delay = max(0, clock[0] - time.monotonic())
            clock[0] = max(clock[0], time.monotonic()) + .25
        if stop.wait(delay):
            raise RuntimeError('Stopped after access or rate-limit response')
        try:
            content = urllib.request.urlopen(url, timeout=30).read()
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403, 429):
                stop.set()
            raise
        except urllib.error.URLError:
            stop.set()
            raise
        data = json.loads(content)
        if not isinstance(data.get('history'), list):
            raise ValueError('No match history')
        if any(r['element'] != eid for r in data['history']):
            raise ValueError('History identity mismatch')
        path = output / f'{eid}.json'
        if path.exists() and path.read_bytes() != content:
            raise ValueError('Refusing to overwrite existing differing response')
        path.write_bytes(content)
        return dict(url=url, sha256=hashlib.sha256(content).hexdigest(),
                    retrieved_at=datetime.datetime.now(datetime.timezone.utc).isoformat())
    pending = [p for p in bootstrap['elements'] if str(p['id']) not in checkpoint['completed']]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        active, iterator = {}, iter(pending)
        def submit():
            p = next(iterator, None)
            if p and not stop.is_set():
                active[pool.submit(fetch, p)] = p
        for _ in range(4):
            submit()
        while active:
            done, _ = concurrent.futures.wait(active, return_when=concurrent.futures.FIRST_COMPLETED)
            for future in done:
                player = active.pop(future)
                eid = str(player['id'])
                try:
                    checkpoint['completed'][eid] = future.result()
                    checkpoint['errors'].pop(eid, None)
                except Exception as exc:
                    checkpoint['errors'][eid] = repr(exc)
                temporary = checkpoint_path.with_suffix('.tmp')
                temporary.write_text(json.dumps(checkpoint, indent=2) + '\n')
                temporary.replace(checkpoint_path)
                if len(checkpoint['completed']) % 50 == 0 or checkpoint['errors']:
                    print(f"Fetched {len(checkpoint['completed'])}/{len(bootstrap['elements'])}; errors {len(checkpoint['errors'])}", flush=True)
                submit()
    print(f"Finished {len(checkpoint['completed'])}/{len(bootstrap['elements'])}; errors {len(checkpoint['errors'])}")
    if len(checkpoint['completed']) != len(bootstrap['elements']):
        raise RuntimeError('Collection incomplete; resume the same snapshot')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('snapshot', type=Path)
    collect(parser.parse_args().snapshot)
