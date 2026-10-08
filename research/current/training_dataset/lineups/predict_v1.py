"""Freeze lineup predictions without reading FPL starts as an outcome."""
from pathlib import Path
import hashlib
import json
import lzma
import re
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
    group = frame.groupby(['match_id', 'team_position'], sort=True)
    slot_counts = frame[valid_slot].groupby(['match_id', 'team_position']).formation_place.nunique()
    group_names = frame.groupby(['match_id', 'team_position']).team_name.nunique()
    okay = slot_counts.eq(11) & group_names.eq(1)
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
    save(predictions, P / 'predictions.csv.xz')
    save(pd.DataFrame(fixture_rows), P / 'fixture_identity.csv')
    lock = dict(protocol_version=json.loads(protocol.read_text())['version'], outcomes_read=False,
        input_sha256=hashes, prediction_code_sha256=digest(Path(__file__)),
        prediction_sha256=digest(P / 'predictions.csv.xz'), fixture_identity_sha256=digest(P / 'fixture_identity.csv'))
    lock_path = P / 'freeze.json'
    if lock_path.exists() and json.loads(lock_path.read_text()) != lock:
        raise ValueError('Frozen lineup plan/input/prediction changed')
    lock_path.write_text(json.dumps(lock, indent=2) + '\n')
    print(dict(predictions=len(predictions), populated=int(predictions.predicted_starts.notna().sum()), outcomes_read=False))


if __name__ == '__main__':
    main()
