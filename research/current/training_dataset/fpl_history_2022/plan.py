"""Freeze late FPL history acquisition and compatibility gates after three pilots."""
from pathlib import Path
import json
import hashlib

P = Path(__file__).resolve().parent
R = P.parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    protocol = dict(version='late_official_history_structural_2022_v1',
        design='Three inspected diagnostic players (318,407,346) are pilots, not unseen controls. All remaining archived players are a fixed acquisition/compatibility population. Shared official FPL origin, not independent provider holdout.',
        source='Pinned vaastav player gw.csv; getters.py calls FPL element-summary and parsers.py exports history without estimating values. All 778 directory IDs match the frozen native season register.',
        target_fields=['starts', 'expected_goals', 'expected_assists', 'expected_goal_involvements', 'expected_goals_conceded'],
        application_scope='Only semantically invalid uniform-zero blocks before FPL event 16 in 2022/23. Preserve raw FPL and all native compatible values after event 15. Source omissions stay missing. No points/BPS/bonus/events/prices/status rewritten.',
        identity_fields=['element','fixture','was_home','opponent_team','team_h_score','team_a_score','kickoff_time'],
        performance_anchors=['minutes','goals_scored','own_goals','penalties_missed','penalties_saved','saves','yellow_cards','red_cards'],
        gates=dict(minimum_control_fixtures=240, minimum_control_players=300,
            maximum_identity_disagreements=0, maximum_performance_anchor_disagreements=0,
            maximum_source_duplicates=0, maximum_late_start_disagreements=0,
            maximum_direct_primary_start_disagreements=0,
            maximum_late_xg_absolute_rounding_difference=0.01000001,
            maximum_xgi_additivity_difference=0.01000001,
            maximum_season_total_difference_per_summed_row=0.00500001,
            season_total_fixed_rounding_allowance=0.01000001,
            minimum_early_primary_fixtures=136),
        temporal='Late archive values are post-match outcomes/backfills. No historical before-deadline feature availability is established by this acquisition; carry publication/capture uncertainty separately. Season totals cannot be used to allocate missing match values.',
        starts='Cross-check all 136 earlier primary lineups and retain known start qualification. No general zero-filling from minutes.',
        scoring='No historical points/BPS/bonus/defcon labels approved.')
    encoded = json.dumps(protocol, indent=2) + '\n'
    path = P / 'protocol.json'
    if path.exists() and path.read_text() != encoded:
        raise ValueError('Frozen source protocol changed')
    path.write_text(encoded)
    paths = [P / 'source_plan.json', path,
        R / 'project/data/2022-23_players.csv.gz', R / 'project/data/2022-23_fixtures.csv.gz',
        P.parent / 'scoring/results/historical_inventory.csv.xz',
        P.parent / 'lineups/primary_reference/explicit_lineups.csv.xz'] + list((P / 'provenance').glob('*.py'))
    lock = dict(input_sha256={str(x.relative_to(R)): digest(x) for x in paths},
        plan_code_sha256=digest(Path(__file__)), diagnostic_pilots=[318,407,346])
    encoded = json.dumps(lock, indent=2) + '\n'
    path = P / 'plan_lock.json'
    if path.exists() and path.read_text() != encoded:
        raise ValueError('Frozen source input changed')
    path.write_text(encoded)
    print(dict(players=len(json.loads((P / 'source_plan.json').read_text())['players']), controls_exclude_pilots=True))


if __name__ == '__main__':
    main()
