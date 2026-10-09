"""Replay the failed expected-statistic pilot without changing its gates."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from prepare import P, R, digest
from predict import SOURCE

def main():
    generated = ['predictions.csv.gz', 'identity_inventory.csv.gz', 'source_files.json', 'prediction_freeze.json']
    generated += [str(f.relative_to(P)) for f in sorted((P / 'results').iterdir())]
    expected = {n: digest(P / n) for n in generated}
    dependencies = json.loads((P / 'dependencies.json').read_text())
    dependencies.update(json.loads((P / 'source_files.json').read_text()))
    decoder = str((SOURCE / 'build.py').relative_to(R))
    dependencies[decoder] = json.loads((P / 'results/validation.json').read_text())['source_identity_decoder_sha256']
    with tempfile.TemporaryDirectory(prefix='fpl-failed-xg-replay-') as temp:
        destination = Path(temp) / 'current'
        stage = destination / P.relative_to(R)
        shutil.copytree(P, stage, ignore=shutil.ignore_patterns('results', '__pycache__', 'replay_report.json'))
        for n in generated:
            (stage / n).unlink(missing_ok=True)
        for n, h in dependencies.items():
            assert digest(R / n) == h, n
            target = destination / n
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(R / n, target)
        for script in ['predict.py', 'validate.py']:
            result = subprocess.run([sys.executable, str(stage / script)], capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
        assert {n: digest(stage / n) for n in generated} == expected
    (P / 'replay_report.json').write_text(json.dumps(dict(byte_identical_files=len(expected), files=expected, network=False, fields_added=0), indent=2) + '\n')
    print(len(expected), 'failed-pilot files reproduced byte-identically offline')

if __name__ == '__main__':
    main()
