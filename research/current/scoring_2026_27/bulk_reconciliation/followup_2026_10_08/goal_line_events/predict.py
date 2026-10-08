"""Prove complete block inventories before counting their explicit last-line subset."""
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

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def integer(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) and value >= 0 and int(value) == value

def decode(value):
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        obj = json.loads(value)
    except (ValueError, TypeError):
        return None
    return obj if isinstance(obj, dict) else None

def complete_player(explicit, blocks, malformed, impossible):
    return integer(explicit) and explicit == blocks and not malformed and not impossible

def complete_team(explicit, blocks, unknown_actors, malformed, player_conflicts, impossible):
    return (integer(explicit) and explicit == blocks and not unknown_actors and not malformed
            and not player_conflicts and not impossible)

def save(frame, name):
    raw = frame.to_csv(index=False).encode()
    (P / name).write_bytes(gzip.compress(raw, mtime=0) if name.endswith('.gz') else raw)

def main():
    manifest = json.loads((P / 'inputs/manifest.json').read_text())
    for name, expected in manifest['files'].items():
        assert digest(R / name) == expected, name
    events = pd.read_csv(P / 'inputs/events.csv.gz', low_memory=False)
    people = pd.read_csv(P / 'inputs/players.csv.gz')
    source = pd.read_csv(R / 'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz', low_memory=False)
    source = source[source.mapping_status.eq('matched') & source.season.ne('2026-27')].copy()
    native = pd.read_csv(R / 'training_dataset/scoring/results/historical_inventory.csv.xz',
                         usecols=K + ['minutes'], low_memory=False)
    source = source.merge(native, on=K, validate='one_to_one')
    events['q'] = events.qualifier_json.map(decode)
    events['block'] = events.q.map(lambda q: q is not None and '94' in q)
    events['line'] = events.q.map(lambda q: q is not None and '14' in q)
    events['malformed'] = events.q.isna()
    events['impossible'] = events.line & ~events.block
    by_player = events.groupby(['match_id', 'team_id', 'player_id']).agg(
        blocks=('block', 'sum'), lines=('line', 'sum'), malformed=('malformed', 'sum'),
        impossible=('impossible', 'sum'))
    pindex = people.set_index(['match_id', 'team_id', 'player_id'])
    assert pindex.index.is_unique
    events['unknown_actor'] = ~pd.MultiIndex.from_frame(events[['match_id', 'team_id', 'player_id']]).isin(pindex.index)
    grouped = events.groupby(['match_id', 'team_id']).agg(
        blocks=('block', 'sum'), malformed=('malformed', 'sum'), impossible=('impossible', 'sum'),
        unknown_actors=('unknown_actor', 'sum'))
    # Primary totals use home/away roles, not a heuristic team-name join.
    bridge = people[['match_id', 'team_id', 'team_position']].drop_duplicates()
    assert not bridge.duplicated(['match_id', 'team_position']).any()
    totals = pd.read_csv(P.parent / 'season_conservation/inputs/full_team_totals.csv')
    totals = totals.merge(bridge, left_on=['match_id', 'side'], right_on=['match_id', 'team_position'],
                          how='left', validate='many_to_one')
    counts = by_player.blocks.to_dict()
    conflicts = {}
    for row in people[people.outfielderBlock.notna()].itertuples():
        key = (row.match_id, row.team_id, row.player_id)
        if not integer(row.outfielderBlock) or row.outfielderBlock != counts.get(key, 0):
            conflicts[key[:2]] = conflicts.get(key[:2], 0) + 1
    team_gates, complete = [], set()
    for row in totals.itertuples():
        key = (row.match_id, row.team_id)
        state = grouped.loc[key].to_dict() if key in grouped.index else dict(
            blocks=0, malformed=0, impossible=0, unknown_actors=0)
        valid = pd.notna(row.team_id) and complete_team(row.outfielder_block, state['blocks'],
            state['unknown_actors'], state['malformed'], conflicts.get(key, 0), state['impossible'])
        team_gates.append(dict(season=row.season, fixture=row.fixture, match_id=row.match_id,
            team_id=row.team_id, primary_total=row.outfielder_block, **state,
            player_conflicts=conflicts.get(key, 0), complete=bool(valid)))
        if valid:
            complete.add(key)
    save(pd.DataFrame(team_gates), 'team_gates.csv')
    rows = []
    for row in source.itertuples():
        key = (row.match_id, row.team_id, row.player_id)
        if key not in pindex.index:
            continue
        official = pindex.loc[key]
        if (official.match_date[:10] != row.date or official.season != row.season[:4] + '-' + str(int(row.season[:4]) + 1)
                or official.minsPlayed != row.minutes):
            continue
        state = by_player.loc[key].to_dict() if key in by_player.index else dict(
            blocks=0, lines=0, malformed=0, impossible=0)
        direct = complete_player(official.outfielderBlock, state['blocks'], state['malformed'], state['impossible'])
        team = key[:2] in complete
        if not (direct or team) or state['malformed'] or state['impossible']:
            continue
        rows.append(dict(season=row.season, fixture=row.fixture, code=row.code, match_id=row.match_id,
            team_id=row.team_id, player_id=row.player_id, value=int(state['lines']),
            block_events=int(state['blocks']), explicit_player_blocks=official.outfielderBlock,
            inventory_proof='explicit_player_block_total' if direct else 'explicit_primary_team_block_total',
            explicit_archive_goal_line=official.clearanceOffLine))
    pred = pd.DataFrame(rows).sort_values(K)
    assert not pred.duplicated(K).any()
    save(pred, 'predictions.csv.gz')
    files = [P / 'protocol.json', P / 'inputs/manifest.json', Path(__file__), P / 'predictions.csv.gz',
             P / 'team_gates.csv']
    freeze = {'files': {str(x.relative_to(R)): digest(x) for x in files},
              'closed_ledger_values_read_by_prediction': False}
    path = P / 'prediction_freeze.json'
    payload = (json.dumps(freeze, indent=2) + '\n').encode()
    if path.exists():
        assert path.read_bytes() == payload, 'Frozen predictions changed'
    path.write_bytes(payload)
    print({'predictions': len(pred), 'complete_primary_teams': len(complete),
           'proofs': pred.inventory_proof.value_counts().to_dict()})

if __name__ == '__main__':
    main()
