"""Qualify direct primary locations by complete seasons and every closed control."""
from pathlib import Path
import gzip
import hashlib
import json
import math
import pandas as pd

P = Path(__file__).resolve().parent
B = P.parent.parent
R = B.parent.parent
K = ['season', 'fixture', 'code']
FIELDS = {'saves_inside_box':'saved_ibox', 'saves_outside_box':'saved_obox'}

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def count(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0 or int(value) != value:
        raise ValueError('Nonnegative explicit integer required')
    return int(value)

def exhaust(values, total, appearances, expected):
    total = count(total)
    if count(appearances) != expected or len(values) != expected:
        raise ValueError('Incomplete appearance inventory')
    explicit = [count(v) for v in values if v is not None]
    if sum(explicit) != total:
        raise ValueError('Explicit match counts do not exhaust explicit season total')
    return [0 if v is None else count(v) for v in values]

def main():
    protocol = json.loads((P/'protocol.json').read_text())
    assert digest(P/'plan.csv') == protocol['plan_sha256']
    for name, sha in protocol['input_sha256'].items():
        assert digest(R/name) == sha
    parent = json.loads((P/'inputs/parent_CURRENT.json').read_text())
    reqpath = B/parent['requirements']
    assert digest(reqpath) == parent['requirements_sha256'] == protocol['parent_requirements_sha256']
    before = pd.read_csv(reqpath, low_memory=False)
    plan = pd.read_csv(P/'plan.csv').fillna({'kickoff_time':''})
    sources = pd.read_csv(P/'inputs/source_manifest.csv').fillna({'reused_from':'', 'observed_at':''})
    assert not plan.duplicated(K).any() and not sources.duplicated(K).any()
    assert set(map(tuple, sources[K].to_numpy())) == set(map(tuple, plan[K].to_numpy()))
    assert json.loads((P/'inputs/errors.json').read_text()) == []
    inv = pd.read_csv(R/'training_dataset/scoring/results/historical_inventory.csv.xz', low_memory=False)
    native = inv[inv.season.eq('2025-26') & inv.minutes.gt(0)].set_index(K)
    fixtures = pd.read_csv(R/'project/data/2025-26_fixtures.csv.gz').set_index('id')
    stats = {}
    scope_problems = {}
    rawpaths = []
    for row in plan.merge(sources, on=K, validate='one_to_one', suffixes=('_plan','')).itertuples():
        path = P/row.path
        assert digest(path) == row.file_sha256
        raw = gzip.decompress(path.read_bytes())
        assert hashlib.sha256(raw).hexdigest() == row.raw_sha256
        obj = json.loads(raw)
        assert int(obj['entity']['id']) == row.pl_player_id and obj['entity']['altIds']['opta'] == f'p{row.code}'
        entries = obj['stats']
        assert len({x['name'] for x in entries}) == len(entries)
        values = {x['name']:x['value'] for x in entries}
        if count(values.get('appearances')) != row.appearances:
            scope_problems.setdefault(row.code,[]).append(f'appearance_count_mismatch:{row.fixture}')
        if count(values.get('mins_played')) != row.minutes:
            scope_problems.setdefault(row.code,[]).append(f'native_minutes_mismatch:{row.fixture}')
        if row.fixture:
            anchor = fixtures.loc[row.fixture]
            assert row.pulse_id == anchor.pulse_id and row.fixture_code == anchor.code and row.kickoff_time == anchor.kickoff_time
            base = f'https://footballapi.pulselive.com/football/stats/player/{row.pl_player_id}?fixtures={row.pulse_id}'
            assert row.url in [base, base+'&altIds=true']
            official = native.loc[(row.season,row.fixture,row.code)]
            assert official.position == 'GK' and official.minutes == row.minutes
        else:
            assert row.url == f'https://footballapi.pulselive.com/football/stats/player/{row.pl_player_id}?comps=1&compSeasons=777&altIds=true'
        stats[(row.code,row.fixture)] = values
        rawpaths.append(path)
    controls, predictions, qualification, total_audit = [], [], [], []
    for code, group in plan.groupby('code', sort=True):
        played = group[group.fixture.gt(0)].sort_values('fixture')
        expected = native[native.index.get_level_values('code') == code]
        assert set(played.fixture) == set(expected.index.get_level_values('fixture'))
        assert len(group[group.fixture.eq(0)]) == 1
        season = stats[(code,0)]
        reasons, field_proofs = list(scope_problems.get(code,[])), {}
        for field, source in FIELDS.items():
            vals = [stats[(code,f)].get(source) for f in played.fixture]
            try:
                proven = exhaust(vals, season.get(source), season.get('appearances'), len(expected))
                field_proofs[field] = dict(zip(played.fixture, proven))
            except ValueError as exc:
                reasons.append(f'{field}:{exc}')
        per_keeper = []
        for field, proved in field_proofs.items():
            reference = before[before.season.eq('2025-26') & before.code.eq(code) & before.field.eq(field)]
            for row in reference.itertuples():
                if row.is_open:
                    continue
                actual = proved[row.fixture]
                per_keeper.append(dict(season=row.season, fixture=row.fixture, code=code,
                    field=field, approved_value=row.value, primary_value=actual,
                    agrees=actual == row.value, primary_explicit=stats[(code,row.fixture)].get(FIELDS[field]),
                    proof='explicit' if FIELDS[field] in stats[(code,row.fixture)] else 'complete_season_exhaustion'))
        controls.extend(per_keeper)
        for field in FIELDS:
            cells = [x for x in per_keeper if x['field'] == field]
            if len(cells) < protocol['minimum_closed_controls_per_field_per_keeper']:
                reasons.append(f'{field}:insufficient_controls')
            if any(not x['agrees'] for x in cells):
                reasons.append(f'{field}:closed_control_conflict')
        outside = [x for x in per_keeper if x['field'] == 'saves_outside_box' and x['approved_value'] > 0]
        if len(outside) < protocol['minimum_positive_outside_controls_per_keeper']:
            reasons.append('insufficient_positive_outside_controls')
        if all(field in field_proofs for field in FIELDS):
            for fixture in played.fixture:
                location_sum = sum(field_proofs[field][fixture] for field in FIELDS)
                if location_sum > int(native.loc[('2025-26',fixture,code),'saves']):
                    reasons.append(f'location_counts_exceed_native_saves:{fixture}')
        for row in played.itertuples():
            primary = stats[(code,row.fixture)].get('saves')
            authoritative = int(native.loc[(row.season,row.fixture,code),'saves'])
            total_audit.append(dict(season=row.season, fixture=row.fixture, code=code,
                native_saves=authoritative, primary_explicit_saves=primary,
                agrees=(primary == authoritative) if primary is not None else None,
                used_for_location_derivation=False))
        for field, proved in field_proofs.items():
            for fixture, value in proved.items():
                explicit = stats[(code,fixture)].get(FIELDS[field])
                predictions.append(dict(season='2025-26', fixture=fixture, code=code,
                    field=field, primary_explicit=explicit, primary_value=value,
                    eligible=not reasons, proof='explicit' if explicit is not None else 'complete_season_exhaustion',
                    season_total=season[FIELDS[field]], reason='|'.join(reasons)))
        qualification.append(dict(code=code, appearances=len(expected),
            inside_controls=sum(x['field']=='saves_inside_box' for x in per_keeper),
            outside_controls=sum(x['field']=='saves_outside_box' for x in per_keeper),
            positive_outside_controls=len(outside), control_disagreements=sum(not x['agrees'] for x in per_keeper),
            qualified=not reasons, reason='|'.join(reasons)))
    predictions = pd.DataFrame(predictions)
    controls = pd.DataFrame(controls)
    qualification = pd.DataFrame(qualification)
    lookup = predictions.set_index(K+['field'])
    after, changes = before.copy(), []
    for i, row in before[before.is_open & before.status.eq('missing_data') & before.field.eq('saves_outside_box')].iterrows():
        key = tuple(row[x] for x in K)+('saves_outside_box',)
        if key not in lookup.index or not bool(lookup.loc[key,'eligible']):
            continue
        prediction = lookup.loc[key]
        value = int(prediction.primary_value)
        for col, v in [('value',value),('status','external_derived' if prediction.proof != 'explicit' else 'external_primary_checked'),
            ('quality_status','qualified_direct_primary_location_complete_season'),
            ('provenance','primary_keeper_location/results/keeper_predictions.csv + inputs/source_manifest.csv'),
            ('is_open',False),('is_zero',value==0),('needs_external_quality_review',True),
            ('bulk_method','direct_primary_saved_obox_complete_season_exhaustion'),
            ('bulk_parent_value',prediction.season_total),('bulk_group_id',f'2025-26:{row.code}:saved_obox')]:
            after.at[i,col] = v
        changes.append(dict(zip(K,key[:3]),field=key[3],value=value,proof=prediction.proof))
    changed = before.is_open & ~after.is_open
    assert int(changed.sum()) == len(changes)
    pd.testing.assert_frame_equal(before.loc[~changed],after.loc[~changed],check_dtype=False)
    assert not after.duplicated(K+['field']).any()
    out = P/'results'
    out.mkdir(exist_ok=True)
    def save(data, name):
        data.to_csv(out/name, index=False, compression='xz' if name.endswith('.xz') else None)
    save(predictions,'keeper_predictions.csv'); save(controls,'control_comparisons.csv')
    save(qualification,'keeper_qualification.csv'); save(pd.DataFrame(total_audit),'native_save_audit.csv')
    save(pd.DataFrame(changes,columns=K+['field','value','proof']),'derived_values.csv')
    save(after,'requirements.csv.xz'); save(after[after.is_open],'remaining_fields.csv.xz')
    readiness = after.groupby(K).agg(open_fields=('is_open','sum'),quality_fields=('needs_external_quality_review','sum')).reset_index()
    readiness['inputs_available'] = readiness.open_fields.eq(0); readiness['scoring_qualified'] = False
    save(readiness,'player_match_readiness.csv.xz')
    matches = readiness.groupby(['season','fixture']).agg(player_matches=('code','size'),open_fields=('open_fields','sum'),quality_fields=('quality_fields','sum')).reset_index()
    matches['inputs_available'] = matches.open_fields.eq(0); matches['bonus_ready'] = False
    save(matches,'match_readiness.csv')
    save(after.groupby('field').agg(required=('field','size'),open_cells=('is_open','sum'),quality_cells=('needs_external_quality_review','sum')).reset_index(),'field_summary.csv')
    old_complete = int(before.groupby(['season','fixture']).is_open.sum().eq(0).sum())
    summary = dict(old_open_fields=int(before.is_open.sum()),new_fields=len(changes),open_fields=int(after.is_open.sum()),
        complete_matches=int(matches.inputs_available.sum()),new_complete_matches=int(matches.inputs_available.sum())-old_complete,
        complete_player_matches=int(readiness.inputs_available.sum()),unique_affected_player_matches=int(readiness.open_fields.gt(0).sum()),
        control_cells=len(controls),control_disagreements=int(controls.agrees.eq(False).sum()),
        qualified_keepers=int(qualification.qualified.sum()),keepers=len(qualification),
        raw_fpl_preserved=True,scoring_qualified=False, source_total_saves_never_used_for_location=True)
    (out/'findings.json').write_text(json.dumps(summary, indent=2)+'\n')
    inputs = [P/'build.py',P/'plan.csv',P/'protocol.json',P/'inputs/parent_CURRENT.json',
        P/'inputs/source_manifest.csv',P/'inputs/errors.json',reqpath,*[R/x for x in protocol['input_sha256']],*rawpaths]
    manifest = dict(path_root='research/current',input_sha256={str(x.relative_to(R)):digest(x) for x in inputs},
        outputs_sha256={x.name:digest(x) for x in sorted(out.iterdir()) if x.is_file() and x.name!='manifest.json'})
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)

if __name__ == '__main__':
    main()
