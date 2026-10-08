"""Freeze an additive scoring version while preserving every v1 artifact."""
from pathlib import Path
import hashlib
import json
import shutil

P = Path(__file__).resolve().parent
R = P.parents[2]
BASE = P.parent/'season_2025'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    if (P/'input_lock.json').exists():
        raise ValueError('Frozen extension must not be replaced')
    (P/'inputs').mkdir(exist_ok=True)
    shutil.copytree(BASE/'inputs/primary',P/'inputs/primary')
    for name in ['keeper_revision_plan.csv','keeper_revision_sources.csv','keeper_revision_protocol.json']:
        shutil.copy2(BASE/name,P/name)
    shutil.copy2(R/'scoring_2026_27/bulk_reconciliation/CURRENT.json',P/'inputs/ledger_CURRENT.json')
    protocol = json.loads((BASE/'protocol.json').read_text())
    protocol['version'] = 'season_2025_changed_components_v3_direct_locations_bcs_revision_quarantine'
    protocol['source_validation'] += '; plus all 746 direct primary location controls and 14 independently conserved outside-box zeros'
    protocol['required_controls']['all_746_direct_primary_location_controls_equal'] = True
    protocol['required_controls']['all_previous_still_qualified_point_labels_preserved'] = True
    protocol['required_controls']['latest_primary_big_chance_controls'] = 381
    protocol['required_controls']['latest_primary_revisions_quarantined'] = [[337,200720],[365,215059]]
    (P/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    old = json.loads((BASE/'results/manifest.json').read_text())
    paths = [R/name for name in {**old['input_sha256'],**old['code_sha256']}]
    paths += [BASE/'results/manifest.json',BASE/'results/player_matches.csv.xz']
    stage = R/'scoring_2026_27/bulk_reconciliation/followup_2026_10_08/primary_keeper_location'
    location = json.loads((stage/'results/manifest.json').read_text())
    paths += [R/name for name in location['input_sha256']]
    paths += [stage/'results'/name for name in location['outputs_sha256']]
    paths.append(stage/'results/manifest.json')
    pointer = json.loads((P/'inputs/ledger_CURRENT.json').read_text())
    paths.append(R/'scoring_2026_27/bulk_reconciliation'/pointer['requirements'])
    paths += [x for x in P.rglob('*') if x.is_file() and '__pycache__' not in x.parts and x.name != 'input_lock.json']
    lock = dict(path_root='research/current',input_sha256={str(p.relative_to(R)):sha(p) for p in paths})
    (P/'input_lock.json').write_text(json.dumps(lock,indent=2)+'\n')
    print(dict(frozen_inputs=len(lock['input_sha256'])))

if __name__ == '__main__':
    main()
