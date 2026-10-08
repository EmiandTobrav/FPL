"""Freeze this season's ledger independently of the old historical replay."""
from pathlib import Path
import hashlib
import json
import shutil

P = Path(__file__).resolve().parent
R = P.parents[2]
S = R / 'scoring_2026_27'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    lock = P / 'input_lock.json'
    if lock.exists():
        raise ValueError('Existing input lock must not be replaced')
    pointer = P / 'inputs/ledger_CURRENT.json'
    shutil.copy2(S / 'bulk_reconciliation/CURRENT.json', pointer)
    current = json.loads(pointer.read_text())
    keeper = S / 'bulk_reconciliation/followup_2026_10_08/fotmob_keeper_location'
    names = [
        P / 'protocol.json', P / 'keeper_revision_protocol.json',
        P / 'keeper_revision_plan.csv', P / 'keeper_revision_sources.csv', pointer,
        S / 'bulk_reconciliation' / current['requirements'],
        R / 'training_dataset/scoring/results/historical_inventory.csv.xz',
        R / 'training_dataset/scoring/results/fixture_source_disagreements.csv',
        R / 'project/data/2025-26_fixtures.csv.gz',
        S / 'delta_input_audit/primary_comparisons.csv.gz',
        S / 'keeper_recovery/current_season_validation.csv',
        S / 'keeper_recovery/current_validation.json',
        S / 'keeper_recovery/findings.json',
        S / 'keeper_recovery/source_manifest.json',
        S / 'fpl_authority/rule_dependencies.json',
        keeper / 'freeze.json', keeper / 'results/manifest.json',
        keeper / 'results/keeper_predictions.csv',
        keeper / 'results/save_evidence.csv',
        keeper / 'results/control_comparisons.csv',
        keeper / 'results/findings.json'
    ] + sorted((P / 'inputs/primary').glob('*.json.gz'))
    lock.write_text(json.dumps(dict(path_root='research/current',
        input_sha256={str(p.relative_to(R)): sha(p) for p in names}), indent=2) + '\n')

if __name__ == '__main__':
    main()
