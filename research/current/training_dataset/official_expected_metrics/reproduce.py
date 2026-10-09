"""Recreate route decisions from retained public responses without network."""
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

P = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    names = ['discovery.json', 'six_case_coverage.csv', 'findings.json']
    expected = {name: digest(P / name) for name in names}
    with tempfile.TemporaryDirectory(prefix='fpl-official-routes-') as temp:
        stage = Path(temp) / 'stage'
        shutil.copytree(P, stage, ignore=shutil.ignore_patterns('__pycache__'))
        for name in names:
            (stage / name).unlink()
        subprocess.run([sys.executable, str(stage / 'finalize.py')], check=True)
        assert {name: digest(stage / name) for name in names} == expected
    (P / 'replay_report.json').write_text(json.dumps({'byte_identical_files': len(names), 'files': expected, 'network': False}, indent=2) + '\n')

if __name__ == '__main__':
    main()
