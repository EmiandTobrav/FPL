"""Extend frozen starts only with exact official squad identities; no outcome reads."""
import json
import sys
import tarfile
import hashlib

import pandas as pd

from predict import P, R, K, digest, save
from validate import check_freeze
sys.path.insert(0, str(P / 'primary_reference'))
from build import extract_lineup
from collect import check_plan


def main():
    check_plan()
    previous = check_freeze()
    ref = P / 'primary_reference'
    protocol = dict(version='explicit_lineups_primary_identity_extension_v4',
        design='Post-diagnostic source coverage extension. V2/V3 failures retained. Previously seen native controls and shared Opta ancestry: regression, not blind holdout.',
        predictor='Preserve frozen v2 predictions; extend only by direct stable code membership in all 142 locked official full squads. No names, minutes or FPL starts outcomes read. Abort on any known prediction conflict.',
        reference='Same fixed 136 early-2022 primary structural references and all compatible native controls. Do not alter raw FPL. No xG correction.',
        gates=json.loads((P / 'protocol.json').read_text())['gates'],
        extra_gates=json.loads((ref / 'protocol.json').read_text())['extra_gates'],
        later_controls='All 240 available native-FPL observations from the six fixed primary control fixtures must agree with official membership and the extended predictor. No missing predictions allowed.',
        application='Only starts. Fill historical missing values from explicit membership, replace documented incompatible early-2022 defaults using primary membership, preserve other native FPL values. Unknown absent identities remain missing.')
    path = P / 'protocol_v4.json'
    encoded = json.dumps(protocol, indent=2) + '\n'
    if path.exists() and path.read_text() != encoded:
        raise ValueError('V4 plan changed')
    path.write_text(encoded)
    manifest = json.loads((ref / 'raw_manifest.json').read_text())
    if digest(ref / 'raw_inputs.tar.gz') != manifest['archive_sha256']:
        raise ValueError('Primary raw reference changed')
    sources = {x['file']: x['sha256'] for x in manifest['entries']}
    rows = []
    with tarfile.open(ref / 'raw_inputs.tar.gz') as archive:
        for row in pd.read_csv(ref / 'fixture_plan.csv').itertuples():
            raw = archive.extractfile(f'raw/fixture_{row.pulse_id}.json').read()
            sha = hashlib.sha256(raw).hexdigest()
            if sha != sources[f'raw/fixture_{row.pulse_id}.json']:
                raise ValueError('Primary source member changed')
            rows.extend(extract_lineup(json.loads(raw), row, sha))
    explicit = pd.DataFrame(rows)
    # FPL original is used solely for identity/club side; never read starts.
    population = pd.read_csv(P.parent / 'scoring/results/historical_inventory.csv.xz', usecols=K + ['was_home'])
    explicit = explicit.merge(population, on=K, validate='one_to_one')
    if not explicit.primary_side.eq(explicit.was_home.map({True: 'home', False: 'away'})).all():
        raise ValueError('Primary extended identity side mismatch')
    old = pd.read_csv(P / 'predictions.csv.xz', low_memory=False)
    extended = old.merge(explicit[K + ['reference_starts', 'source_file', 'source_sha256']], on=K, how='left', validate='one_to_one')
    both = extended.predicted_starts.notna() & extended.reference_starts.notna()
    if not extended.loc[both, 'predicted_starts'].eq(extended.loc[both, 'reference_starts']).all():
        raise ValueError('Known frozen prediction conflicts with new primary source')
    update = extended.reference_starts.notna()
    newly = update & extended.predicted_starts.isna()
    extended.loc[update, 'predicted_starts'] = extended.loc[update, 'reference_starts']
    extended.loc[update, 'status'] = 'documented_primary_lineup_v4'
    extended.loc[update, 'primary_source_file'] = extended.loc[update, 'source_file']
    extended.loc[update, 'primary_source_sha256'] = extended.loc[update, 'source_sha256']
    save(extended.drop(columns=['reference_starts', 'source_file', 'source_sha256']), P / 'predictions_v4.csv.xz')
    names = [P / 'predictions.csv.xz', P / 'freeze_v2.json', path, ref / 'raw_inputs.tar.gz',
        ref / 'raw_manifest.json', ref / 'fixture_plan.csv', ref / 'plan_lock.json', ref / 'build.py',
        P.parent / 'scoring/results/historical_inventory.csv.xz']
    lock = dict(protocol_version=protocol['version'], outcomes_read=False,
        evidence_type=protocol['design'], input_sha256={str(x.relative_to(R)): digest(x) for x in names},
        prediction_code_sha256=digest(P / 'predict_v4.py'), prediction_sha256=digest(P / 'predictions_v4.csv.xz'),
        base_prediction_sha256=previous['prediction_sha256'], new_explicit_memberships=int(newly.sum()))
    lock_path = P / 'freeze_v4.json'
    encoded = json.dumps(lock, indent=2) + '\n'
    if lock_path.exists() and lock_path.read_text() != encoded:
        raise ValueError('V4 frozen prediction/input changed')
    lock_path.write_text(encoded)
    print(dict(new_explicit_memberships=int(newly.sum()), populated=int(extended.predicted_starts.notna().sum())))


if __name__ == '__main__':
    main()
