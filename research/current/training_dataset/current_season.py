"""Build current-season observations from official, finished-event snapshots.

Event live data are round aggregates. Match histories supply exact fixture
identity, club side and the full appearance inventory including zero BPS.
No current price, club or availability is backdated into features.
"""
from pathlib import Path
import argparse
import csv
import datetime
import gzip
import hashlib
import io
import json

API = 'https://fantasy.premierleague.com/api/'
POSITIONS = {1: 'GK', 2: 'DEF', 3: 'MID', 4: 'FWD'}
MATCH_FIELDS = ('goals_scored', 'assists', 'own_goals', 'penalties_saved',
                'penalties_missed', 'yellow_cards', 'red_cards', 'saves',
                'bonus', 'bps', 'defensive_contribution')

def require(condition, message):
    if not condition:
        raise ValueError(message)

def json_read(path):
    return json.loads(path.read_bytes())

def save_rows(path, rows):
    require(bool(rows), f'No rows for {path.name}')
    columns = list(dict.fromkeys(k for row in rows for k in row))
    text = io.StringIO(newline='')
    writer = csv.DictWriter(text, fieldnames=columns, lineterminator='\n')
    writer.writeheader()
    writer.writerows(rows)
    raw = gzip.compress(text.getvalue().encode(), mtime=0)
    # Portable gzip bytes across Python/zlib platforms.
    path.write_bytes(raw[:9] + bytes([255]) + raw[10:])

def explain_points(element):
    return sum(s['points'] for f in element['explain'] for s in f['stats'])

def award_bonus(values):
    return {key: max(0, 3 - sum(other > score for other in values.values()))
            for key, score in values.items()}

def build(snapshot):
    raw = snapshot / 'raw'
    bootstrap = json_read(raw / 'bootstrap-static.json')
    fixtures = json_read(raw / 'fixtures.json')
    players = {p['id']: p for p in bootstrap['elements']}
    require(len(players) == len(bootstrap['elements']), 'Duplicate element identity')
    checkpoint = json_read(snapshot / 'collection_checkpoint.json')
    require(checkpoint['bootstrap_sha256'] == hashlib.sha256((raw / 'bootstrap-static.json').read_bytes()).hexdigest(),
            'Collection uses a different bootstrap')
    require(set(checkpoint['completed']) == {str(eid) for eid in players}, 'Element histories incomplete')
    histories = {}
    history_sources = []
    for eid in players:
        path = raw / 'element-summary' / f'{eid}.json'
        record = checkpoint['completed'][str(eid)]
        require(hashlib.sha256(path.read_bytes()).hexdigest() == record['sha256'], 'History hash mismatch')
        history_sources.append(dict(file=f'raw/element-summary/{eid}.json', **record))
        for row in json_read(path)['history']:
            require(row['element'] == eid, 'History identity mismatch')
            key = (row['fixture'], eid)
            require(key not in histories, 'Duplicate history key')
            histories[key] = row
    finished = [e for e in bootstrap['events'] if e['finished']]
    require(bool(finished), 'No finished events')
    season = f"{finished[0]['deadline_time'][:4]}-{int(finished[0]['deadline_time'][:4])+1:04d}" 
    season = season[:5] + season[-2:]
    rounds, matches, points, source_records = [], [], [], []
    bonus_checks = statistic_checks = 0
    files = [('bootstrap-static.json', API + 'bootstrap-static/'),
             ('fixtures.json', API + 'fixtures/')]
    for event in finished:
        gw = event['id']
        filename = f'event_{gw}_live.json'
        live = json_read(raw / filename)['elements']
        files.append((filename, API + f'event/{gw}/live/'))
        lookup = {x['id']: x for x in live}
        require(len(lookup) == len(live), f'Duplicate live identity in GW{gw}')
        event_fixtures = [f for f in fixtures if f['event'] == gw]
        require(bool(event_fixtures) and all(f['finished'] for f in event_fixtures),
                f'Event {gw} contains unfinished fixtures')
        counts = {}
        for f in event_fixtures:
            for team in (f['team_h'], f['team_a']):
                counts[team] = counts.get(team, 0) + 1
        fixture_players = {}
        for fixture in event_fixtures:
            stats = {s['identifier']: s for s in fixture['stats']}
            require('bps' in stats, 'Missing complete fixture BPS inventory')
            source_scores = {x['element']: x['value'] for side in ('h', 'a')
                             for x in stats['bps'][side]}
            appearances = {eid: h for (fid, eid), h in histories.items() if fid == fixture['id']
                           and (h['minutes'] > 0 or any(h.get(k, 0) != 0 for k in
                                ('bps', 'total_points', 'yellow_cards', 'red_cards', 'own_goals')))}
            require(set(source_scores) <= set(appearances), 'Published BPS player absent from history')
            scores = {eid: h['bps'] for eid, h in appearances.items()}
            require(all(scores[eid] == score for eid, score in source_scores.items()), 'History/fixture BPS mismatch')
            require(len(scores) >= 22, 'Incomplete active match roster')
            expected_bonus = award_bonus(scores)
            for side in ('h', 'a'):
                team = fixture['team_' + side]
                # Refuse event aggregate -> match statistics in doubles.
                require(counts[team] == 1, 'Double GW requires element-summary data')
                entries = [dict(element=eid, value=h['bps']) for eid, h in appearances.items()
                           if h['was_home'] == (side == 'h')]
                require(len(entries) >= 11, 'Incomplete team roster')
                for entry in entries:
                    eid = entry['element']
                    require(eid in lookup and eid in players, 'Unknown appearance identity')
                    require(eid not in fixture_players, 'Duplicate appearance in single GW')
                    fixture_players[eid] = fixture['id']
                    element = lookup[eid]
                    p = players[eid]
                    history = histories[(fixture['id'], eid)]
                    row = dict(season=season, round=gw, element=eid, code=p['code'],
                               fixture=fixture['id'], position=POSITIONS[p['element_type']],
                               name=p['first_name'] + ' ' + p['second_name'],
                               team=team, opponent_team=fixture['team_a' if side == 'h' else 'team_h'],
                               was_home=side == 'h', kickoff_time=fixture['kickoff_time'],
                               team_h_score=fixture['team_h_score'], team_a_score=fixture['team_a_score'])
                    row.update({k: v for k, v in element['stats'].items()
                                if k not in ('played', 'in_dreamteam')})
                    require(history['round'] == gw and history['opponent_team'] == row['opponent_team']
                            and history['kickoff_time'] == row['kickoff_time'], 'History match identity mismatch')
                    for field, value in element['stats'].items():
                        if field in ('played', 'in_dreamteam'):
                            continue
                        require(field in history and history[field] == value,
                                f'History/event {field} mismatch')
                    for field in ('value', 'selected', 'transfers_balance', 'transfers_in', 'transfers_out'):
                        row[field] = history[field]
                    require(row['bps'] == entry['value'], 'Event and match BPS mismatch')
                    for field in MATCH_FIELDS:
                        require(field in stats, f'Missing match statistic {field}')
                        inventory = {x['element']: x['value'] for x in stats[field][side]}
                        # Here omitted match values are NOT used as source observations:
                        # the explicit live value must itself be zero if no match entry exists.
                        if eid in inventory:
                            require(row[field] == inventory[eid], f'Event/match {field} mismatch')
                        else:
                            require(row[field] == 0, f'Unlisted nonzero match {field}')
                        statistic_checks += 1
                    require(row['bonus'] == expected_bonus[eid], 'Whole-match bonus mismatch')
                    bonus_checks += 1
                    require(row['total_points'] == explain_points(element), 'Point accounting mismatch')
                    for explanation in element['explain']:
                        require(explanation['fixture'] == fixture['id'], 'Wrong explanation fixture')
                        for item in explanation['stats']:
                            points.append(dict(season=season, round=gw, fixture=fixture['id'],
                                               element=eid, code=p['code'], **item))
                    row['assists_2026_27'] = row['assists']
                    row['defcon_count'] = row['defensive_contribution']
                    row['defcon_points'] = sum(s['points'] for f in element['explain'] for s in f['stats']
                                              if s['identifier'] == 'defensive_contribution')
                    require(row['defcon_points'] in (0, 2), 'Invalid official defensive award')
                    row['original_total_points'] = row['total_points']
                    row['total_points_2026_27'] = row['total_points']
                    row['original_bps'] = row['bps']
                    row['bps_2026_27'] = row['bps']
                    row['original_bonus'] = row['bonus']
                    row['bonus_2026_27'] = row['bonus']
                    row['scoring_status'] = 'official_target_season'
                    row['source_live_file'] = 'raw/' + filename
                    row['source_fixture_file'] = 'raw/fixtures.json'
                    row['source_history_file'] = f'raw/element-summary/{eid}.json'
                    row['observed_at'] = checkpoint['completed'][str(eid)]['retrieved_at']
                    matches.append(row)
        for element in live:
            eid = element['id']
            require(eid in players, 'Unknown round identity')
            require(element['stats']['total_points'] == explain_points(element), 'Round accounting mismatch')
            require(not element['stats']['minutes'] or eid in fixture_players,
                    'Active player missing from match inventory')
            if eid not in fixture_players:
                require(all(not s['value'] and not s['points'] for f in element['explain'] for s in f['stats']),
                        'Nonparticipant has scoring events')
            p = players[eid]
            row = dict(season=season, round=gw, element=eid, code=p['code'],
                       position=POSITIONS[p['element_type']], **element['stats'])
            row['fixture_count'] = int(eid in fixture_players)
            row['total_points_2026_27'] = row['total_points']
            row['scoring_status'] = 'official_target_season'
            row['source_live_file'] = 'raw/' + filename
            rounds.append(row)
    for filename, url in files:
        source_records.append(dict(file='raw/' + filename, url=url,
                                   sha256=hashlib.sha256((raw / filename).read_bytes()).hexdigest(),
                                   file_written_at=datetime.datetime.fromtimestamp(
                                       (raw / filename).stat().st_mtime, datetime.timezone.utc).isoformat()))
    require(len({(r['fixture'], r['code']) for r in matches}) == len(matches), 'Duplicate canonical match')
    require(len({(r['round'], r['code']) for r in rounds}) == len(rounds), 'Duplicate canonical round')
    output = snapshot / 'derived'
    output.mkdir(exist_ok=True)
    save_rows(output / 'player_matches.csv.gz', matches)
    save_rows(output / 'player_rounds.csv.gz', rounds)
    save_rows(output / 'point_components.csv.gz', points)
    report = dict(version='fpl2627_official_snapshot_20261008_v1',
                  builder_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                  season=season, finished_events=[e['id'] for e in finished],
                  player_matches=len(matches), player_rounds=len(rounds),
                  fixtures=len({r['fixture'] for r in matches}),
                  whole_match_bonus_checks=bonus_checks, statistic_checks=statistic_checks,
                  point_explanations_balanced=True, no_current_prices_backdated=True,
                  raw_sources=source_records + history_sources,
                  limitation='Observation-time snapshot, not historical availability. '
                  'Current bootstrap position/name identity metadata; team from match side. '
                  'Historical deadline price/status/features are not provided by live API.')
    report['outputs'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                         for p in sorted(output.glob('*.csv.gz'))}
    (output / 'manifest.json').write_text(json.dumps(report, indent=2) + '\n')
    return report

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('snapshot', type=Path)
    report = build(parser.parse_args().snapshot)
    print(json.dumps({k: v for k, v in report.items() if k != 'raw_sources'}, indent=2))
