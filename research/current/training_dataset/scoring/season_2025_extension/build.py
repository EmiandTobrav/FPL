"""Extend frozen v1 scoring after independently qualified direct-location inputs."""
from pathlib import Path
import hashlib
import gzip
import importlib.util
import json
import sys
import pandas as pd

P = Path(__file__).resolve().parent
R = P.parents[2]
BASE = P.parent/'season_2025'
K = ['season','fixture','code']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    lock = json.loads((P/'input_lock.json').read_text())
    for name, expected in lock['input_sha256'].items():
        if sha(R/name) != expected:
            raise ValueError(f'Frozen extension input changed: {name}')
    stage = R/'scoring_2026_27/bulk_reconciliation/followup_2026_10_08/primary_keeper_location'
    manifest = json.loads((stage/'results/manifest.json').read_text())
    for name, expected in manifest['input_sha256'].items():
        if sha(R/name) != expected:
            raise ValueError(f'Location producer input changed: {name}')
    for name, expected in manifest['outputs_sha256'].items():
        if sha(stage/'results'/name) != expected:
            raise ValueError(f'Location producer output changed: {name}')
    controls = pd.read_csv(stage/'results/control_comparisons.csv')
    if len(controls) != 746 or not controls.agrees.all():
        raise ValueError('Full direct-location population controls differ')
    qualification = pd.read_csv(stage/'results/keeper_qualification.csv').set_index('code')
    changes = pd.read_csv(stage/'results/derived_values.csv')
    if len(changes) != 14 or not qualification.loc[changes.code,'qualified'].all():
        raise ValueError('Unqualified changed location input')
    pointer = json.loads((P/'inputs/ledger_CURRENT.json').read_text())
    req = pd.read_csv(R/'scoring_2026_27/bulk_reconciliation'/pointer['requirements'], low_memory=False)
    reference = req.set_index(K+['field'])
    for row in changes.itertuples():
        value = reference.loc[(row.season,row.fixture,row.code,row.field)]
        if value.is_open or value.value != row.value:
            raise ValueError('Changed ledger location lacks exact producer proof')
    sys.path.insert(0,str(P.parent))
    spec = importlib.util.spec_from_file_location('frozen_season_2025',BASE/'build.py')
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    base.P = P
    base.build()
    out = P/'results'
    # Newly collected location responses also expose BCS revisions. Retain the
    # approved counters but quarantine every contradictory whole fixture.
    plan = pd.read_csv(stage/'plan.csv')
    sources = pd.read_csv(stage/'inputs/source_manifest.csv')
    primary_stats = {}
    for row in sources.itertuples():
        body = json.loads(gzip.decompress((stage/row.path).read_bytes()))
        primary_stats[(row.code,row.fixture)] = {x['name']:x['value'] for x in body['stats']}
    bc_reference = req[req.season.eq('2025-26') & req.field.eq('big_chance_saves')].set_index(['code','fixture'])
    bc_audit = []
    for code, group in plan.groupby('code',sort=True):
        fixtures = sorted(group.loc[group.fixture.gt(0),'fixture'])
        season = primary_stats[(code,0)]
        values = base.season_exhaustion([primary_stats[(code,f)].get('big_chance_saves') for f in fixtures],
            season.get('big_chance_saves'),season.get('appearances'),len(fixtures))
        for fixture, value in zip(fixtures,values):
            old = bc_reference.loc[(code,fixture),'value']
            bc_audit.append(dict(season='2025-26',fixture=fixture,code=code,
                approved_value=old,latest_primary_value=value,agrees=old==value,
                primary_explicit=primary_stats[(code,fixture)].get('big_chance_saves'),
                approved_value_replaced=False))
    bc_audit = pd.DataFrame(bc_audit)
    revisions = bc_audit[~bc_audit.agrees]
    if len(bc_audit) != 381 or set(zip(revisions.fixture,revisions.code)) != {(337,200720),(365,215059)}:
        raise ValueError('Unreviewed latest primary big-chance-save revision')
    blocked = set(revisions.fixture)
    point_fields = ['bps_2026_27','bonus_2026_27','total_points_2026_27','assists_2026_27','defcon_points_2026_27']
    for name in ['player_matches.csv.xz','qualified_player_matches.csv.xz']:
        frame = pd.read_csv(out/name,low_memory=False)
        affected = frame.fixture.isin(blocked)
        if name == 'qualified_player_matches.csv.xz':
            frame = frame[~affected].copy()
        else:
            frame.loc[affected,point_fields] = float('nan')
            frame.loc[affected,'scoring_qualified'] = False
            frame.loc[affected,'label_status'] = 'blocked_latest_primary_big_chance_revision'
            for field in ['times_tackled','saves_inside_box','saves_outside_box','big_chance_saves']:
                frame.loc[affected,field] = float('nan')
                frame.loc[affected,field+'_source'] = None
        base.save(frame,out/name)
    fixture_status = pd.read_csv(out/'fixture_status.csv')
    fixture_status.loc[fixture_status.fixture.isin(blocked),'scoring_qualified'] = False
    fixture_status.loc[fixture_status.fixture.isin(blocked),'source_revision_quarantined'] = True
    base.save(fixture_status,out/'fixture_status.csv')
    for name in ['changed_bps_components.csv.xz','basic_components.csv.xz']:
        frame = pd.read_csv(out/name,low_memory=False)
        base.save(frame[~frame.fixture.isin(blocked)],out/name)
    base.save(bc_audit,out/'latest_primary_big_chance_controls.csv')
    previous = pd.read_csv(BASE/'results/player_matches.csv.xz',low_memory=False).set_index(K)
    current = pd.read_csv(out/'player_matches.csv.xz',low_memory=False).set_index(K)
    fields = ['bps_2026_27','bonus_2026_27','total_points_2026_27','assists_2026_27','defcon_points_2026_27']
    old_keys = previous.index[previous.scoring_qualified & ~previous.index.get_level_values('fixture').isin(blocked)]
    pd.testing.assert_frame_equal(previous.loc[old_keys,fields],current.loc[old_keys,fields],check_dtype=False)
    for name in ['player_matches.csv.xz','qualified_player_matches.csv.xz']:
        frame = pd.read_csv(out/name,low_memory=False)
        frame['qualification_manifest'] = 'training_dataset/scoring/season_2025_extension/results/manifest.json'
        base.save(frame,out/name)
    summary = json.loads((out/'summary.json').read_text())
    qview = current[current.scoring_qualified]
    summary.update(qualified_player_matches=len(qview),
        qualified_whole_fixtures=int(fixture_status.scoring_qualified.sum()),
        blocked_whole_fixtures=int((~fixture_status.scoring_qualified).sum()),
        changed_bonus_rows=int(qview.original_bonus.ne(qview.bonus_2026_27).sum()),
        changed_total_point_rows=int(qview.original_total_points.ne(qview.total_points_2026_27).sum()),
        latest_primary_big_chance_control_cells=381,
        source_revision_fixtures=sorted(blocked),
        prior_qualified_fixture_quarantined=365)
    summary.update(previous_qualified_whole_fixtures=363,
        new_qualified_whole_fixtures=12,
        net_qualified_whole_fixture_increase=summary['qualified_whole_fixtures']-363,
        previous_still_qualified_point_labels_preserved=True,
        direct_primary_location_control_cells=746)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    qualified = json.loads((out/'qualification.json').read_text())
    qualified['checks']['direct_primary_location_control_cells_equal'] = 746
    qualified['checks']['previous_qualified_labels_preserved'] = len(old_keys)
    qualified['checks']['latest_primary_big_chance_controls'] = 381
    qualified['checks']['latest_primary_big_chance_revisions_quarantined'] = sorted(blocked)
    (out/'qualification.json').write_text(json.dumps(qualified,indent=2)+'\n')
    result_manifest = json.loads((out/'manifest.json').read_text())
    result_manifest['code_sha256'][str(Path(__file__).relative_to(R))] = sha(Path(__file__))
    result_manifest['output_sha256'] = {name:sha(out/name) for name in base.OUTPUTS if name != 'manifest.json'}
    result_manifest['output_sha256']['latest_primary_big_chance_controls.csv'] = sha(out/'latest_primary_big_chance_controls.csv')
    result_manifest['counts'] = summary
    (out/'manifest.json').write_text(json.dumps(result_manifest,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)

if __name__ == '__main__':
    main()
