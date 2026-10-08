"""Freeze a post-diagnostic reference repair; never refit the v2 predictor."""
from pathlib import Path
import sys
import json

import pandas as pd

P = Path(__file__).resolve().parent
sys.path.insert(0, str(P.parent))
from predict import R, digest, save
from validate import check_freeze


def main():
    previous = check_freeze()
    paths = [R / 'project/data/2022-23_fixtures.csv.gz',
        R / 'scoring_2026_27/bulk_reconciliation/collection_plan.csv',
        P.parent.parent / 'scoring/results/historical_inventory.csv.xz',
        P.parent / 'validation_summary.json']
    fixtures = pd.read_csv(paths[0])
    catalog = pd.read_csv(paths[1])
    early = fixtures.loc[fixtures.event.lt(16), 'id']
    todo = catalog[(catalog.season.eq('2022-23') & catalog.fixture.isin(early)) |
                   (catalog.season.isin(['2023-24', '2024-25']) & catalog.fixture.isin([1, 2, 3]))].copy()
    todo['scope'] = todo.season.map({'2022-23': 'structural_start_reference',
        '2023-24': 'later_native_control', '2024-25': 'later_native_control'})
    cols = ['season', 'fixture', 'fixture_code', 'pulse_id', 'home_primary_id',
            'away_primary_id', 'home_score', 'away_score', 'date', 'scope']
    todo = todo[cols].sort_values(['season', 'fixture'])
    assert len(todo) == 142 and len(todo[todo.season.eq('2022-23')]) == 136
    save(todo, P / 'fixture_plan.csv')
    fields = ['starts', 'expected_goals', 'expected_assists',
              'expected_goal_involvements', 'expected_goals_conceded']
    original = pd.read_csv(paths[2], usecols=['season', 'fixture', 'fixture_event'] + fields)
    original = original[original.season.eq('2022-23')]
    audit = []
    for event, group in original.groupby('fixture_event', sort=True):
        for field in fields:
            values = group[field]
            audit.append(dict(event=event, field=field, rows=len(group),
                fixtures=group.fixture.nunique(), nonmissing=int(values.notna().sum()),
                positive=int(values.gt(0).sum()), total=float(values.sum()),
                all_explicit_zero=bool(values.notna().all() and values.eq(0).all())))
    save(pd.DataFrame(audit), P / 'raw_schema_audit.csv')
    protocol = dict(version='explicit_primary_starts_reference_v3',
        design='Post-outcome reference investigation triggered by v2 failure. Not new blind holdout; original failures retained. Predictor v2 and all thresholds remain unchanged.',
        selection='All 136 FPL 2022/23 fixtures with official event <16; plus fixed fixtures 1,2,3 from each of 2023/24 and 2024/25. No outcome ranking or filtering.',
        primary_reference='Only exact fixture/date/team/score identity, eleven unique starters per side and direct stable Opta code membership. Never default zeros or absence from squad.',
        replacement='Only starts references for the fixed 136 fixtures may be replaced, after proving every original match has zero starts despite two explicit primary elevens. Preserve raw starts and all failed v2 comparisons. No xG/xA/xGI/xGC correction authorized.',
        controls='All original mappable four-season controls, unchanged selection. Early 2022 reference must cover every control identity directly. Later primary controls must agree with native FPL starts and frozen v2 predictions. Shared Opta ancestry; not independent provider validation.',
        gates=json.loads((P.parent / 'protocol.json').read_text())['gates'],
        extra_gates=dict(primary_early_fixtures=136, later_control_fixtures=6,
            maximum_primary_native_disagreements=0, maximum_missing_reference=0),
        historical_application='Only direct explicit source membership, compatible native FPL starts retained. Fill missing historical starts and repair documented early-2022 structural defaults separately; no scoring labels approved.',
        unused_substitutes='Not sufficient on its own to approve changed scoring-component zero counters.')
    encoded = json.dumps(protocol, indent=2) + '\n'
    protocol_path = P / 'protocol.json'
    if protocol_path.exists() and protocol_path.read_text() != encoded:
        raise ValueError('Reference protocol changed')
    protocol_path.write_text(encoded)
    lock = dict(input_sha256={str(p.relative_to(R)): digest(p) for p in paths},
        predictor_freeze_sha256=digest(P.parent / 'freeze_v2.json'),
        frozen_prediction_sha256=previous['prediction_sha256'],
        plan_sha256=digest(P / 'fixture_plan.csv'), protocol_sha256=digest(protocol_path),
        audit_sha256=digest(P / 'raw_schema_audit.csv'), plan_code_sha256=digest(Path(__file__)))
    encoded = json.dumps(lock, indent=2) + '\n'
    lock_path = P / 'plan_lock.json'
    if lock_path.exists() and lock_path.read_text() != encoded:
        raise ValueError('Reference selection/input changed')
    lock_path.write_text(encoded)
    print(dict(selected=len(todo), early=136, later_controls=6))


if __name__ == '__main__':
    main()
