"""Offline reproduction of the current snapshot and penalty validation pilot."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

P = Path(__file__).resolve().parent
R = P.parent
S = R / 'scoring_2026_27/bulk_reconciliation/followup_2026_10_08'

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    frozen = json.loads((P / 'penalty_controls/freeze.json').read_text())
    inputs = set(frozen['inputs'])
    extras = ['assist_intentional_pass/baseline/build.py', 'assist_intentional_pass/rules.py',
              'assist_intentional_pass/baseline/fpl_baseline.csv.gz',
              'assist_intentional_pass/inputs/official_cases.json',
              'assist_touch_bounds/results/goal_decisions.csv.gz',
              'assist_touch_bounds/results/candidate_exclusions.csv.gz',
              'penalty_foul_recovery/validation_comparisons.csv',
              'penalty_foul_recovery/validation_summary.json']
    inputs.update(str((S / n).relative_to(R)) for n in extras)
    inputs.add(str((S.parent / 'CURRENT.json').relative_to(R)))
    inputs.update(str(path.relative_to(R)) for path in P.rglob('*')
                  if path.is_file() and '__pycache__' not in path.parts
                  and path.name != 'reproduction_verification.json')
    output_paths = list((P / 'snapshots/2026_10_08/derived').glob('*'))
    output_paths += [P / 'penalty_controls' / n for n in
                    ['plan.csv', 'freeze.json', 'isolation_evidence.csv', 'comparisons.csv',
                     'validation_summary.json', 'protected_conflicts.csv', 'denial_conflicts.csv']]
    output_paths += list((P / 'penalty_controls/results').glob('*'))
    expected = {str(path.relative_to(R)): digest(path) for path in output_paths}
    with tempfile.TemporaryDirectory(prefix='fpl_dataset_replay_') as tmp:
        root = Path(tmp) / 'research/current'
        for name in inputs:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(R / name, target)
        for name in expected:
            # Freeze and plan are copied then compared by the scripts themselves.
            if Path(name).name not in ['plan.csv', 'freeze.json', 'isolation_evidence.csv']:
                (root / name).unlink()
        tasks = [['training_dataset/penalty_controls/plan.py'],
                 ['training_dataset/penalty_controls/validate.py'],
                 ['training_dataset/penalty_controls/build.py'],
                 ['training_dataset/current_season.py', 'training_dataset/snapshots/2026_10_08']]
        for task in tasks:
            result = subprocess.run([sys.executable, *task], cwd=root, capture_output=True, text=True)
            if result.returncode:
                raise RuntimeError(result.stdout + result.stderr)
        mismatch = [name for name, sha in expected.items() if digest(root / name) != sha]
        if mismatch:
            raise ValueError(f'Reproduced bytes differ: {mismatch}')
    report = dict(offline=True, isolated_copy=True, checked_outputs=len(expected), identical=True,
                  python=sys.version.split()[0], output_sha256=expected,
                  input_sha256={name: digest(R / name) for name in sorted(inputs)})
    (P / 'reproduction_verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(dict(offline=True, isolated_copy=True, checked_outputs=len(expected), identical=True))

if __name__ == '__main__':
    main()
