"""Replay the historical calculation offline in a fresh, isolated tree."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

P = Path(__file__).resolve().parent
R = P.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads((P / 'results/manifest.json').read_text())
    inputs = {**manifest['input_sha256'], **manifest['code_sha256']}
    for name, sha in inputs.items():
        if digest(R / name) != sha:
            raise ValueError(f'Frozen historical input/code changed: {name}')
    expected = {name: digest(P / 'results' / name)
                for name in [*manifest['output_sha256'], 'manifest.json']}
    for name, sha in manifest['output_sha256'].items():
        if expected[name] != sha:
            raise ValueError(f'Frozen historical result changed: {name}')
    with tempfile.TemporaryDirectory(prefix='fpl_historical_scoring_replay_') as tmp:
        root = Path(tmp) / 'research/current'
        for name in inputs:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(R / name, target)
        result = subprocess.run([sys.executable, 'training_dataset/scoring/historical.py'],
                                cwd=root, capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError(result.stdout + result.stderr)
        mismatch = [name for name, sha in expected.items()
                    if digest(root / 'training_dataset/scoring/results' / name) != sha]
        if mismatch:
            raise ValueError(f'Historical replay differs: {mismatch}')
    report = dict(offline=True, isolated_copy=True, identical=True,
                  checked_outputs=len(expected), python=sys.version.split()[0],
                  output_sha256=expected, input_sha256=inputs)
    (P / 'reproduction_verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(dict(offline=True, isolated_copy=True, identical=True, checked_outputs=len(expected)))


if __name__ == '__main__':
    main()
