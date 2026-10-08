"""Offline byte-for-byte replay of this qualified season view."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

P = Path(__file__).resolve().parent
R = P.parents[2]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    manifest = json.loads((P / 'results/manifest.json').read_text())
    inputs = {**manifest['input_sha256'], **manifest['code_sha256']}
    expected = {**manifest['output_sha256'], 'manifest.json':sha(P/'results/manifest.json')}
    for name,value in inputs.items():
        if sha(R/name) != value:
            raise ValueError(f'Replay input changed: {name}')
    with tempfile.TemporaryDirectory(prefix='fpl_2025_scoring_replay_') as tmp:
        root = Path(tmp)/'research/current'
        for name in inputs:
            target = root/name
            target.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(R/name,target)
        result = subprocess.run([sys.executable,'training_dataset/scoring/season_2025/build.py'],
            cwd=root,capture_output=True,text=True)
        if result.returncode:
            raise RuntimeError(result.stdout+result.stderr)
        mismatches = [name for name,value in expected.items()
            if sha(root/'training_dataset/scoring/season_2025/results'/name) != value]
        if mismatches:
            raise ValueError(f'Replay differs: {mismatches}')
    report = dict(offline=True,isolated_copy=True,identical=True,
        checked_outputs=len(expected),input_sha256=inputs,output_sha256=expected,
        python=sys.version.split()[0])
    (P/'reproduction_verification.json').write_text(json.dumps(report,indent=2)+'\n')
    print(dict(offline=True,isolated_copy=True,identical=True,checked_outputs=len(expected)))

if __name__ == '__main__':
    main()
