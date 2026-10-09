"""Offline isolated reproduction; no collection or full scoring rebuild."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from predict import P, B, R, digest, write
from validate import ARCHIVE, ARCHIVE_SHA

def stage_copy(destination):
    stage = destination / P.relative_to(R)
    shutil.copytree(P, stage, ignore=shutil.ignore_patterns('results', '__pycache__'))
    dependencies = json.loads((P / 'dependencies.json').read_text())
    dependencies[ARCHIVE] = ARCHIVE_SHA
    parent = json.loads((P / 'inputs/parent_CURRENT.json').read_text())
    for field in ['player_match_readiness', 'match_readiness']:
        source = B / parent[field]
        dependencies[str(source.relative_to(R))] = digest(source)
    for n, h in dependencies.items():
        assert digest(R / n) == h
        target = destination / n
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(R / n, target)
    for n in ['predictions.csv.gz', 'season_conservation.csv', 'dependencies.json', 'prediction_freeze.json', 'application_freeze.json']:
        (stage / n).unlink(missing_ok=True)
    return stage

def run(stage, script):
    return subprocess.run([sys.executable, str(stage / script)], capture_output=True, text=True)

def main():
    generated = ['predictions.csv.gz', 'season_conservation.csv', 'dependencies.json', 'prediction_freeze.json', 'application_freeze.json']
    generated += [str(p.relative_to(P)) for p in sorted((P / 'results').iterdir())]
    expected = {n: digest(P / n) for n in generated}
    with tempfile.TemporaryDirectory(prefix='fpl-player-block-replay-') as temp:
        stage = stage_copy(Path(temp) / 'current')
        for script in ['predict.py', 'validate.py', 'build.py']:
            result = run(stage, script)
            assert result.returncode == 0, result.stderr
        assert {n: digest(stage / n) for n in generated} == expected
    write(P / 'replay_report.json', dict(byte_identical_files=len(expected), files=expected, network=False))
    print(len(expected), 'files reproduced byte-identically offline')

if __name__ == '__main__':
    main()
