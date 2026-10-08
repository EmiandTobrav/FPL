"""Replay only this data-gap batch in a clean offline temporary tree."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
from predict import P, B, R, digest

def main():
    manifest = json.loads((P / 'inputs/manifest.json').read_text())
    parent = json.loads((P / 'inputs/parent_CURRENT.json').read_text())
    expected = json.loads((P / 'results/manifest.json').read_text())
    with tempfile.TemporaryDirectory(prefix='fpl-goal-line-replay-') as temporary:
        root = (Path(temporary) / 'research/current').resolve()
        files = {R / name for name in manifest['files']}
        files.update(x for x in P.rglob('*') if x.is_file() and '__pycache__' not in x.parts
                     and 'results' not in x.parts)
        files.update(B / parent[key] for key in ['requirements', 'player_match_readiness', 'match_readiness'])
        for source in files:
            target = root / source.relative_to(R)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        stage = root / P.relative_to(R)
        for script in ['predict.py', 'build.py']:
            subprocess.run([sys.executable, str(stage / script)], check=True,
                           stdout=subprocess.DEVNULL)
        actual = json.loads((stage / 'results/manifest.json').read_text())
        assert actual == expected, 'Replay output set or hashes changed'
        for name, sha in expected.items():
            assert digest(P / 'results' / name) == sha
            assert digest(stage / 'results' / name) == sha, name
        assert digest(stage / 'prediction_freeze.json') == digest(P / 'prediction_freeze.json')
    report = dict(offline=True, isolated=True, byte_identical_results=len(expected),
                  frozen_predictions_identical=True, output_sha256=expected)
    (P / 'reproduction_verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print({k: v for k, v in report.items() if k != 'output_sha256'})

if __name__ == '__main__':
    main()
