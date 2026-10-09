"""Bounded official-source route audit; no statistical imputation or writes."""
import csv
import gzip
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent

def read(name):
    return json.loads((P / name).read_text())

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def write(name, value):
    (P / name).write_text(json.dumps(value, indent=2) + '\n')

def main():
    plan = read('plan.json')
    for name, sha in plan['discovery_files'].items():
        assert digest(P / name) == sha, name
    for record, path in [(read('page_source.json'), 'inputs/page.html'), (read('bundle_source.json'), 'inputs/bundle-es.min.js')]:
        assert digest(P / path) == record['sha256']
    for record in read('chunk_sources.json'):
        path = record.get('path') or ('inputs/' + record['url'].split('/')[-1])
        assert digest(P / path) == record['sha256'], path
    api = read('api_sources.json')
    for record in api:
        assert digest(P / record['path']) == record['sha256'], record['path']
        assert record['url'].startswith(plan['base_url'] + '/')
    bundle = (P / 'inputs/bundle-es.min.js').read_text()
    paths = {'matchStats': '/v3/matches/${e}/stats', 'matchLineups': '/v3/matches/${e}/lineups', 'playerSeasonStats': '/v2/competitions/${t}/seasons/${n}/players/${e}/stats', 'playerMatchList': '/v1/competitions/${e}/seasons/${t}/players/${n}/matches/all', 'teamPlayerStatsLeaderboard': '/v1/competitions/${e}/seasons/${t}/teams/players/stats/leaderboard', 'matchList': '/v2/matches${ju(e,!0)}'}
    for name, path in paths.items():
        assert name + ':e.query' in bundle and path in bundle, name
    assert 'function yp(e){return e?e.replace(/([a-z0-9])([A-Z])/g,"$1_$2").toLowerCase():null}' in bundle
    leaderboard = read('inputs/leaderboard_2025_xg.json')
    assert len(leaderboard['data']) == 10
    assert all('playerMetadata' in x and 'expectedGoals' in x['stats'] for x in leaderboard['data'])
    team_stats = read('inputs/match_2561895_stats.json')
    assert len(team_stats) == 2
    assert all(set(x) == {'side', 'stats', 'teamId'} for x in team_stats)
    assert all('expectedGoals' in x['stats'] for x in team_stats)
    lineup = read('inputs/keeper_veto_41_lineups.json')
    players = [x for key in ['home_team', 'away_team'] for x in lineup[key]['players']]
    assert any(x['id'] == '204936' and x['position'] == 'Goalkeeper' for x in players)
    assert all('stats' not in x for x in players)
    season = read('inputs/donnarumma_2025_season.json')
    assert season['player']['id'] == '204936' and 'totalClearances' in season['stats']
    games = read('inputs/donnarumma_2025_matches.json')['currentAndPreviousMatches']
    assert all('stats' not in x for x in games)
    assert any(x['matchId'] == '2561936' for x in games)
    assert read('inputs/keeper_veto_41_uuid.json') == []
    write('discovery.json', {'base_url': plan['base_url'], 'competition': '8', 'season': '2025', 'observed_paths': paths, 'expected_goals_sort': 'expected_goals:desc,player_metadata.last_name:asc', 'player_ids': 'numeric FPL Opta code; 204936 confirmed by returned player identity and lineup', 'match_ids': 'numeric FPL fixture code; 2561936 confirmed by player match list and native fixture inventory', 'uuid_probe': 'HTTP 200 empty array; not a missing-value-zero rule', 'unused_vX_route': 'HTTP 400 No configuration found; frontend matchList route /v2/matches succeeds'})
    dependencies = read('control_sources.json')
    for name, sha in dependencies.items():
        assert digest(P / name) == sha, name
    with gzip.open(P / 'inputs/six_case_decisions.csv.gz', 'rt') as stream:
        cases = list(csv.DictReader(stream))
    with gzip.open(P / 'inputs/native_fixtures.csv.gz', 'rt') as stream:
        fixtures = {x['id']: x for x in csv.DictReader(stream)}
    assert len(cases) == 6
    assert fixtures['41']['code'] == '2561936'
    with (P / 'six_case_coverage.csv').open('w', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=['season', 'fixture', 'player_code', 'match_code', 'native_cbi', 'official_per_player_match_cbi', 'decision'], lineterminator='\n')
        writer.writeheader()
        for row in cases:
            writer.writerow({'season': row['season'], 'fixture': row['fixture'], 'player_code': row['code'], 'match_code': fixtures[row['fixture']]['code'], 'native_cbi': row['expected'], 'official_per_player_match_cbi': '', 'decision': 'not_available_in_observed_routes; no replacement'})
    write('findings.json', {'investigation_status': 'completed_bounded_public_route_audit', 'prior_source_pilot': '../scoring_2026_27/bulk_reconciliation/followup_2026_10_08/sdp_schema_pilot/README.md', 'new_provider_discovered': False, 'audit_relationship': 'Extension of an existing official SDP schema pilot. The team-match limitation was already known; new observed player-season, leaderboard, lineup and player-match-list routes still expose no player-match statistics. Do not describe this as a new provider or repeat the old match-schema probe.', 'official_api_accessible': True, 'retained_api_responses': len(api), 'successful_api_responses': sum(x['status'] == 200 for x in api), 'team_match_stats_rows': 2, 'player_season_leaderboard_rows': 10, 'keeper_season_stats_available': True, 'player_match_list_available': True, 'player_match_stats_available_in_observed_routes': False, 'six_native_vetoes_resolved': 0, 'keeper_cbi_requirements_remaining': 341, 'fields_closed': 0, 'expected_metric_imports': 0, 'ledger_modified': False, 'scoring_modified': False, 'reason': 'Observed official frontend routes provide team-match statistics, player-season statistics, lineups and player match lists. They provide no matched per-player per-match CBI or expected metrics. Seasonal/team totals cannot be allocated to individuals.', 'scope_limit': 'This is a bounded audit of retained frontend routes and responses, not a claim that no other public or licensed endpoint exists.', 'same_input_retry_allowed': False, 'reopening_condition': 'A documented public player-match statistics route or compatible export/version with concrete keeper-CBI/expected-statistic values; rerun full existing native/historical gates before applying.'})
    print('Official API accessible; observed routes resolve zero keeper-CBI or expected-statistic fields')

if __name__ == '__main__':
    main()
