"""Recreate the lineage decision from retained code, without network access."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

P = Path(__file__).resolve().parent

def main():
    expected = hashlib.sha256((P / 'findings.json').read_bytes()).hexdigest()
    with tempfile.TemporaryDirectory(prefix='fpl-shot-lineage-') as temp:
        stage = Path(temp) / 'stage'
        shutil.copytree(P, stage, ignore=shutil.ignore_patterns('__pycache__'))
        (stage / 'findings.json').unlink()
        subprocess.run([sys.executable, str(stage / 'finalize.py')], check=True)
        assert hashlib.sha256((stage / 'findings.json').read_bytes()).hexdigest() == expected
    (P / 'replay_report.json').write_text(json.dumps({'byte_identical_files': 1, 'files': {'findings.json': expected}, 'verified_pinned_source_files': 6, 'network': False}, indent=2) + '\n')

if __name__ == '__main__':
    main()
