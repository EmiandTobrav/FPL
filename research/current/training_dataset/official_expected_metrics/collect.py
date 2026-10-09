"""Retain anonymous responses from paths observed in the official public frontend."""
import hashlib
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent

def collect(url, name):
    output = ROOT / 'inputs' / (name + '.json')
    if output.exists():
        raise SystemExit('Already retained; do not repeat an unchanged request')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0', 'Accept': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            status, data = response.status, response.read()
    except urllib.error.HTTPError as exc:
        status, data = exc.code, exc.read()
    output.write_bytes(data)
    item = {'url': url, 'status': status, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'path': str(output.relative_to(ROOT)), 'retrieved_at': datetime.now(timezone.utc).isoformat()}
    log = ROOT / 'api_sources.json'
    sources = json.loads(log.read_text()) if log.exists() else []
    sources.append(item)
    log.write_text(json.dumps(sources, indent=2) + '\n')
    print(json.dumps(item))

if __name__ == '__main__':
    collect(sys.argv[1], sys.argv[2])
