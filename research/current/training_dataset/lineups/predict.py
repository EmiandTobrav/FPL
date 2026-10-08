"""Freeze lineup predictions without reading FPL starts as an outcome."""
from pathlib import Path
import hashlib
import json
import lzma
import re
import tarfile
import unicodedata

import pandas as pd

P = Path(__file__).resolve().parent
R = P.parents[1]
K = ['season', 'fixture', 'code']
ALIASES = {'man city': 'manchester city', 'man utd': 'manchester united',
    'spurs': 'tottenham hotspur', 'wolves': 'wolverhampton wanderers',
    'brighton': 'brighton and hove albion', 'newcastle': 'newcastle united',
    'norwich': 'norwich city', 'leicester': 'leicester city',
    'sheffield utd': 'sheffield united', 'leeds': 'leeds united',
    'west brom': 'west bromwich albion', 'nott m forest': 'nottingham forest',
    'west ham': 'west ham united', 'luton': 'luton town', 'ipswich': 'ipswich town'}


def team(value):
    value = unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().lower().replace('&', ' and ')
    value = re.sub(r'\b(afc|fc)\b', '', re.sub('[^a-z0-9]+', ' ', value))
    value = re.sub(r'\s+', ' ', value).strip()
    return ALIASES.get(value, value)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(frame, path):
    data = frame.to_csv(index=False, lineterminator='\n').encode()
    path.write_bytes(lzma.compress(data) if path.suffix == '.xz' else data)


def classify_lineup(frame):
    """Only explicit slots and substitute position, never default timing."""
    frame = frame.copy()
    slot = pd.to_numeric(frame.formation_place, errors='coerce')
    valid_slot = slot.between(1, 11) & slot.eq(slot.round())
    is_sub = frame.position.eq('Substitute') & (slot.isna() | slot.eq(0))
    contradictory = frame.position.eq('Substitute') & valid_slot
    if contradictory.any():
        raise ValueError('Substitute position contradicts starting slot')
    frame['predicted_starts'] = float('nan')
    frame.loc[valid_slot, 'predicted_starts'] = 1
    frame.loc[is_sub, 'predicted_starts'] = 0
    starting = frame[valid_slot].copy()
    starting['numeric_slot'] = slot[valid_slot].astype(int)
    slot_counts = starting.groupby(['match_id', 'team_position']).numeric_slot.agg(lambda values: len(values) == 11 and set(values) == set(range(1, 12)))
    group_names = frame.groupby(['match_id', 'team_position']).team_name.nunique()
    okay = slot_counts & group_names.eq(1)
    teams = frame.groupby('match_id').team_position.agg(lambda values: set(values) == {'home', 'away'})
    invalid = set(teams[~teams].index)
    for (match, side), valid in okay.items():
        if not valid:
            invalid.add(match)
    if frame.duplicated(['match_id', 'player_id']).any():
        raise ValueError('Duplicate lineup participant identity')
    frame['lineup_inventory_valid'] = ~frame.match_id.isin(invalid)
    frame.loc[~frame.lineup_inventory_valid, 'predicted_starts'] = float('nan')
    return frame


def primary_lineups(hashes):
    """Use original PL lineup arrays, never external reconstructed minutes."""
    root = R / 'scoring_2026_27/bulk_reconciliation/followup_2026_10_08/primary_gap_recovery'
    for name in ['raw_manifest.json', 'raw_inputs.tar.gz', 'fixture_plan.csv']:
        hashes[str((root / name).relative_to(R))] = digest(root / name)
    manifest = json.loads((root / 'raw_manifest.json').read_text())
    if digest(root / 'raw_inputs.tar.gz') != manifest['archive_sha256']:
        raise ValueError('Primary raw archive changed')
    expected = {row['file']: row['sha256'] for row in manifest['entries']}
    rows = []
    with tarfile.open(root / 'raw_inputs.tar.gz') as archive:
        for plan in pd.read_csv(root / 'fixture_plan.csv').itertuples():
            name = f'inputs/fixture_{plan.pulse_id}.json'
            raw = archive.extractfile(name).read()
            if hashlib.sha256(raw).hexdigest() != expected[name]:
                raise ValueError('Primary lineup response changed')
            data = json.loads(raw)
            if data['id'] != plan.pulse_id or data['status'] != 'C' or int(data['altIds']['opta'].lstrip('g')) != plan.fixture_code:
                raise ValueError('Primary lineup fixture identity mismatch')
            if [row['team']['id'] for row in data['teams']] != [plan.home_primary_id, plan.away_primary_id] or [row['score'] for row in data['teams']] != [plan.home_score, plan.away_score]:
                raise ValueError('Primary lineup team/score identity mismatch')
            if pd.to_datetime(data['kickoff']['millis'], unit='ms', utc=True).strftime('%Y-%m-%d') != plan.date:
                raise ValueError('Primary lineup date mismatch')
            on = {event['personId'] for event in data['events'] if event['type'] == 'S' and event['description'] == 'ON'}
            if len(data['teamLists']) != 2:
                raise ValueError('Incomplete primary team lineup')
            for side in data['teamLists']:
                if len(side['lineup']) != 11 or side['teamId'] not in [plan.home_primary_id, plan.away_primary_id]:
                    raise ValueError('Invalid primary starting lineup')
                for started, people in [(1, side['lineup']), (0, side['substitutes'])]:
                    for person in people:
                        code = person['altIds']['opta']
                        if not re.fullmatch(r'p\d+', code):
                            raise ValueError('Invalid primary player code')
                        rows.append(dict(season=plan.season, fixture=plan.fixture, code=int(code[1:]),
                            predicted_starts=started, primary_side='home' if side['teamId'] == plan.home_primary_id else 'away',
                            primary_unused_substitute=started == 0 and person['id'] not in on,
                            primary_person_id=person['id'], primary_source_file=name,
                            primary_source_sha256=expected[name], status='documented_primary_lineup'))
    out = pd.DataFrame(rows)
    if out.duplicated(K).any():
        raise ValueError('Duplicate primary lineup identity')
    return out


def main():
    hashes = {}
    def read(path, **kwargs):
        hashes[str(path.relative_to(R))] = digest(path)
        return pd.read_csv(path, low_memory=False, **kwargs)
    protocol = P / 'protocol.json'
    hashes[str(protocol.relative_to(R))] = digest(protocol)
    projections = json.loads((P / 'projection_manifest.json').read_text())
    hashes[str((P / 'projection_manifest.json').relative_to(R))] = digest(P / 'projection_manifest.json')
    for name, meta in projections['projections'].items():
        if digest(P / name) != meta['sha256']:
            raise ValueError('Source projection changed')
    lineup = classify_lineup(read(P / 'opta_lineups.csv.xz', keep_default_na=False))
    fixtures = read(P / 'opta_fixtures.csv.xz', keep_default_na=False)
    fixtures = fixtures[fixtures.match_status.eq('Played')].copy()
    fixtures['fixture_lookup'] = list(zip(fixtures.season.str[:4], fixtures.match_date.str[:10],
        fixtures.home_team.map(team), fixtures.away_team.map(team)))
    if fixtures.fixture_lookup.duplicated().any():
        raise ValueError('Ambiguous source fixture')
    fixture_lookup = fixtures.set_index('fixture_lookup').to_dict('index')
    anchors = []
    for year in range(2019, 2026):
        path = R / f'scoring_2026_27/bps_recovery/inputs/counts-{year}-{str(year+1)[2:]}.csv.gz'
        d = read(path, usecols=['code', 'player_id', 'mapping_status'], dtype={'player_id': str})
        anchors.append(d[d.mapping_status.eq('matched') & d.player_id.notna()][['code', 'player_id']])
    anchors = pd.concat(anchors).drop_duplicates()
    counts = anchors.groupby('code').player_id.nunique()
    anchors = anchors[anchors.code.isin(counts[counts.eq(1)].index)].set_index('code').player_id.to_dict()
    if pd.Series(anchors).duplicated().any():
        raise ValueError('Source player ID maps to multiple FPL codes')
    # This usecols list explicitly excludes the control outcome 'starts'.
    population = read(P.parent / 'scoring/results/historical_inventory.csv.xz',
        usecols=K + ['element', 'historical_team', 'was_home'])
    by_match = {match: group.set_index('player_id') for match, group in lineup.groupby('match_id')}
    fixture_mappings = {}
    fixture_rows = []
    for season in sorted(population.season.unique()):
        fp = read(R / f'project/data/{season}_fixtures.csv.gz')
        tp = read(R / f'project/data/{season}_teams.csv.gz').set_index('id')
        for row in fp.itertuples():
            key = (season[:4], str(row.kickoff_time)[:10], team(tp.loc[row.team_h, 'name']), team(tp.loc[row.team_a, 'name']))
            match = fixture_lookup.get(key)
            if match is None:
                fixture_rows.append(dict(season=season, fixture=row.id, match_id='', status='missing_source_fixture'))
                continue
            if int(match['home_score']) != row.team_h_score or int(match['away_score']) != row.team_a_score:
                raise ValueError('Source/FPL fixture score mismatch')
            group = by_match.get(match['match_id'])
            okay = group is not None and group.lineup_inventory_valid.all()
            fixture_mappings[(season, row.id)] = match['match_id'] if okay else None
            fixture_rows.append(dict(season=season, fixture=row.id, match_id=match['match_id'],
                                     status='verified_full_lineup' if okay else 'invalid_lineup_inventory'))
    predicted = []
    for row in population.itertuples():
        mid = fixture_mappings.get((row.season, row.fixture))
        pid = anchors.get(row.code)
        group = by_match.get(mid)
        matched = group is not None and pid in group.index
        item = dict(season=row.season, fixture=row.fixture, code=row.code, element=row.element,
                    match_id=mid, player_id=pid, predicted_starts=None, status='unmapped_player_or_fixture')
        if matched:
            source = group.loc[pid]
            if source.team_position != ('home' if row.was_home else 'away') or team(source.team_name) != team(row.historical_team):
                raise ValueError('Lineup/FPL player club-side mismatch')
            item.update(predicted_starts=source.predicted_starts, position=source.position,
                formation_place=source.formation_place, source_minutes=source.minutes_played,
                source_sub_on_minute=source.sub_on_minute, source_is_starter=source.is_starter,
                status='explicit_full_lineup' if pd.notna(source.predicted_starts) else 'unknown_starting_role')
        predicted.append(item)
    predictions = pd.DataFrame(predicted).sort_values(K).reset_index(drop=True)
    primary = primary_lineups(hashes)
    explicit = primary.merge(population[K + ['was_home']], on=K, validate='one_to_one')
    if not explicit.primary_side.eq(explicit.was_home.map({True: 'home', False: 'away'})).all():
        raise ValueError('Primary lineup/FPL side mismatch')
    combined = predictions.merge(explicit.drop(columns='was_home'), on=K, how='left', validate='one_to_one', suffixes=('', '_primary'))
    both = combined.predicted_starts.notna() & combined.predicted_starts_primary.notna()
    if not combined.loc[both, 'predicted_starts'].eq(combined.loc[both, 'predicted_starts_primary']).all():
        raise ValueError('Archive/primary starting lineup conflict')
    use = combined.predicted_starts_primary.notna()
    combined.loc[use, 'predicted_starts'] = combined.loc[use, 'predicted_starts_primary']
    combined.loc[use, 'status'] = combined.loc[use, 'status_primary']
    predictions = combined.drop(columns=['predicted_starts_primary', 'status_primary'])
    save(predictions, P / 'predictions.csv.xz')
    save(pd.DataFrame(fixture_rows), P / 'fixture_identity.csv')
    lock = dict(protocol_version=json.loads(protocol.read_text())['version'], outcomes_read=False,
        input_sha256=hashes, prediction_code_sha256=digest(Path(__file__)),
        prediction_sha256=digest(P / 'predictions.csv.xz'), fixture_identity_sha256=digest(P / 'fixture_identity.csv'))
    lock_path = P / 'freeze_v2.json'
    if lock_path.exists() and json.loads(lock_path.read_text()) != lock:
        raise ValueError('Frozen lineup plan/input/prediction changed')
    lock_path.write_text(json.dumps(lock, indent=2) + '\n')
    print(dict(predictions=len(predictions), populated=int(predictions.predicted_starts.notna().sum()), outcomes_read=False))


if __name__ == '__main__':
    main()
