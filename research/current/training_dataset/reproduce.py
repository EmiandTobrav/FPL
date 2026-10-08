"""Offline reproduction of current, historical, penalty and lineup artifacts."""
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
    historical_manifest = json.loads((P / 'scoring/results/manifest.json').read_text())
    inputs.update(historical_manifest['input_sha256'])
    lineup_freeze = json.loads((P / 'lineups/freeze_v2.json').read_text())
    inputs.update(lineup_freeze['input_sha256'])
    inputs.update(json.loads((P / 'lineups/freeze_v4.json').read_text())['input_sha256'])
    reference_lock = json.loads((P / 'lineups/primary_reference/plan_lock.json').read_text())
    inputs.update(reference_lock['input_sha256'])
    inputs.update(json.loads((P / 'lineups/conservation/freeze.json').read_text())['input_sha256'])
    inputs.update(json.loads((P / 'fpl_history_2022/plan_lock.json').read_text())['input_sha256'])
    inputs.update(json.loads((P / 'fpl_history_2022/reconciliation/plan_lock.json').read_text())['input_sha256'])
    inputs.update(str(path.relative_to(R)) for path in P.rglob('*')
                  if path.is_file() and '__pycache__' not in path.parts
                  and path.name != 'reproduction_verification.json'
                  and not path.is_relative_to(P / 'lineups/raw')
                  and not path.is_relative_to(P / 'lineups/primary_reference/raw')
                  and not path.is_relative_to(P / 'fpl_history_2022/raw'))
    output_paths = list((P / 'snapshots/2026_10_08/derived').glob('*'))
    output_paths += [P / 'penalty_controls' / n for n in
                    ['plan.csv', 'freeze.json', 'isolation_evidence.csv', 'comparisons.csv',
                     'validation_summary.json', 'protected_conflicts.csv', 'denial_conflicts.csv']]
    output_paths += list((P / 'penalty_controls/results').glob('*'))
    output_paths += list((P / 'scoring/results').glob('*'))
    output_paths += [P / 'lineups' / name for name in ['predictions.csv.xz',
        'fixture_identity.csv', 'freeze_v2.json', 'control_comparisons.csv.xz',
        'control_disagreements.csv', 'control_summary.csv', 'validation_summary.json']]
    output_paths += [P / 'lineups' / name for name in ['protocol_v4.json', 'predictions_v4.csv.xz',
        'freeze_v4.json', 'control_comparisons_v4.csv.xz', 'control_summary_v4.csv',
        'validation_summary_v4.json', 'starts_qualified.csv.xz', 'starts_coverage.csv',
        'starts_active_gaps.csv', 'application_manifest.json']]
    output_paths += [P / 'lineups/primary_reference' / name for name in ['fixture_plan.csv',
        'raw_schema_audit.csv', 'plan_lock.json', 'explicit_lineups.csv.xz',
        'later_primary_controls.csv.xz', 'compatible_control_comparisons.csv.xz',
        'compatible_control_summary.csv', 'validation_summary.json']]
    output_paths += [P / 'lineups/conservation' / name for name in ['protocol.json',
        'predictions.csv.xz', 'complete_start_inventories.csv', 'freeze.json',
        'control_comparisons.csv.xz', 'control_summary.csv', 'validation_summary.json',
        'starts_qualified.csv.xz', 'coverage.csv', 'manifest.json']]
    output_paths += [P / 'fpl_history_2022' / name for name in ['protocol.json','plan_lock.json',
        'late_player_history.csv.xz','source_inventory_gaps.csv','identity_disagreements.csv',
        'performance_disagreements.csv','late_xg_controls.csv','late_xg_disagreements.csv',
        'season_total_checks.csv.xz','original_xgi_semantic_conflicts.csv',
        'disagreement_groups.csv','validation_summary.json']]
    output_paths += [P / 'fpl_history_2022/reconciliation' / name for name in
        ['protocol.json', 'plan_lock.json', 'evidence_lock.json',
         'verified_final_objects.csv', 'same_old_snapshot_checks.csv',
         'reconciled_reference_checks.csv', 'qualified_season_total_checks.csv.xz',
         'documented_revisions.csv.xz', 'expected_statistics_qualified.csv.xz', 'manifest.json']]
    expected = {str(path.relative_to(R)): digest(path) for path in output_paths}
    with tempfile.TemporaryDirectory(prefix='fpl_dataset_replay_') as tmp:
        root = Path(tmp) / 'research/current'
        for name in inputs:
            target = root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(R / name, target)
        for name in expected:
            # Freeze and plan are copied then compared by the scripts themselves.
            if Path(name).name not in ['plan.csv', 'freeze.json', 'isolation_evidence.csv',
                                      'fixture_plan.csv', 'freeze_v2.json', 'freeze_v4.json', 'plan_lock.json',
                                      'raw_schema_audit.csv', 'evidence_lock.json']:
                if Path(name).name == 'protocol.json':
                    continue  # Included in locked input checks before regeneration.
                (root / name).unlink()
        tasks = [['training_dataset/penalty_controls/plan.py'],
                 ['training_dataset/penalty_controls/validate.py'],
                 ['training_dataset/penalty_controls/build.py'],
                 ['training_dataset/current_season.py', 'training_dataset/snapshots/2026_10_08'],
                 ['training_dataset/scoring/historical.py'],
                 ['training_dataset/lineups/predict.py'],
                 ['training_dataset/lineups/validate.py'],
                 ['training_dataset/lineups/primary_reference/plan.py'],
                 ['training_dataset/lineups/primary_reference/build.py'],
                 ['training_dataset/lineups/predict_v4.py'],
                 ['training_dataset/lineups/validate_v4.py'],
                 ['training_dataset/lineups/apply.py'],
                 ['training_dataset/lineups/conservation/predict.py'],
                 ['training_dataset/lineups/conservation/build.py'],
                 ['training_dataset/fpl_history_2022/plan.py'],
                 ['training_dataset/fpl_history_2022/build.py'],
                 ['training_dataset/fpl_history_2022/reconciliation/plan.py'],
                 ['training_dataset/fpl_history_2022/reconciliation/freeze_evidence.py'],
                 ['training_dataset/fpl_history_2022/reconciliation/build.py']]
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
