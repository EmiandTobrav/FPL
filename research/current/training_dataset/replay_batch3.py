"""Replay frozen Linux-produced gzip files on macOS without changing inputs.

Python 3.12's gzip.compress(mtime=0) delegates to zlib, whose OS header byte
differs by platform. The frozen files use OS=3. Only that metadata byte is
canonicalized in an isolated child process; all input hashes and frozen output
hashes still have to pass. No CSV or prediction transformations are permitted.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

P = Path(__file__).resolve().parent
BATCH = P.parent / 'scoring_2026_27/bulk_reconciliation/followup_2026_10_08/bulk_batch3'
SHIM = '''import gzip
_original_compress = gzip.compress
def _canonical_compress(data, compresslevel=9, *, mtime=None):
    out = _original_compress(data, compresslevel=compresslevel, mtime=mtime)
    if mtime == 0:
        out = out[:9] + bytes([3]) + out[10:]
    return out
gzip.compress = _canonical_compress
'''

def main():
    verification = BATCH / 'replay_verification.json'
    original_verification = verification.read_bytes()
    try:
        with tempfile.TemporaryDirectory(prefix='gzip_platform_') as tmp:
            Path(tmp, 'sitecustomize.py').write_text(SHIM)
            env = dict(os.environ)
            env['PYTHONPATH'] = tmp + os.pathsep + env.get('PYTHONPATH', '')
            subprocess.run([sys.executable, str(BATCH / 'reproduce.py')], env=env, check=True)
        evidence = json.loads(verification.read_text())
    finally:
        verification.write_bytes(original_verification)
    assert evidence['identical'] and evidence['checked_outputs'] == 63
    evidence['platform_adapter'] = 'gzip OS header byte=3; frozen hashes unchanged'
    (P / 'batch3_replay_verification.json').write_text(json.dumps(evidence, indent=2) + '\n')

if __name__ == '__main__':
    main()
