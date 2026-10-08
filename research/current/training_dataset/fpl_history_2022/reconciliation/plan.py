"""Freeze same-FPL snapshot reconciliation; retain the failed V1 equality test."""
from pathlib import Path
import json
import hashlib

P = Path(__file__).resolve().parent
R = P.parents[2]
FIELDS = ['expected_goals','expected_assists','expected_goal_involvements','expected_goals_conceded']


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    prior = json.loads((P.parent / 'validation_summary.json').read_text())
    if prior['qualified']:
        raise ValueError('Expected retained failed cross-snapshot control')
    old_gates = json.loads((P.parent / 'protocol.json').read_text())['gates']
    protocol = dict(version='same_fpl_final_2022_snapshot_reconciliation_v2',
        design='Post-diagnostic deterministic official-source version reconciliation. V1 equality control and failures remain immutable and failed. This is not a refitted predictor or new holdout.',
        authority='Both weekly and final histories come from archived official FPL. Preserve all raw and compatible existing values. A separately named derived expected-stat version may use explicit final FPL backfill/revision; no external source voting or estimates.',
        source_gates=dict(required_unchanged_player_directory_trees=778,
            maximum_old_snapshot_identity_or_anchor_disagreements=0,
            maximum_old_snapshot_expected_value_disagreements=0,
            maximum_changes_outside_explicit_scope=0,
            maximum_nonfinite_or_negative_final_expected_values=0),
        unchanged_numeric_gates=old_gates,
        scopes=dict(early='Events <16: use direct final official FPL history for the documented structural zero block.',
            gw16='Event 16: use explicit final FPL history as a separately recorded later snapshot revision, only after proving the weekly baseline reproduces the 2022-11-23 archive and final byte objects are unchanged since 2023-05-29.',
            gw29='Only xGI values inconsistent with native compatible xG+xA: derive the exact sum under the official field definition. No xG/xA/xGC replacement in this group.',
            other='All other native compatible values remain numerically unchanged.'),
        gates_not_relaxed='V1 same-value gate remains failed. V2 proves two real versions and records their revisions. Identical-version equality, identity, algebra and season-aggregate controls keep their original tolerances.',
        temporal='Archive publication date bounds the existence of the final version, not when a historical manager knew each value. All before-deadline feature availability remains unqualified.',
        scoring='Expected-statistics-only view. No points/BPS/bonus/defcon/assist-event labels are approved.')
    encoded = json.dumps(protocol, indent=2) + '\n'
    path = P / 'protocol.json'
    if path.exists() and path.read_text() != encoded:
        raise ValueError('Reconciliation protocol changed')
    path.write_text(encoded)
    inputs = [P / 'source_metadata.json', P / 'end_season_directory_trees.csv', path,
        P.parent / 'source_plan.json', P.parent / 'raw_manifest.json',
        P.parent / 'late_player_history.csv.xz', P.parent / 'validation_summary.json',
        R / 'project/data/2022-23_players.csv.gz',
        P.parents[1] / 'scoring/results/historical_inventory.csv.xz'] + sorted((P / 'provenance').glob('*.txt'))
    lock = dict(input_sha256={str(x.relative_to(R)):digest(x) for x in inputs},
        code_sha256=digest(Path(__file__)))
    encoded = json.dumps(lock, indent=2) + '\n'
    path = P / 'plan_lock.json'
    if path.exists() and path.read_text() != encoded:
        raise ValueError('Frozen reconciliation input changed')
    path.write_text(encoded)
    print(dict(retained_v1_failures=482, selected_weekly_snapshot='GW16 2022-11-23'))


if __name__ == '__main__':
    main()
