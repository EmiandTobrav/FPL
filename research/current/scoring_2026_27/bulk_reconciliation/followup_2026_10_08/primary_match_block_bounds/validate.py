"""Check all existing outcomes without adjusting the frozen predictions."""
import json
import pandas as pd
from predict import P, B, R, K, digest, save, write

ARCHIVE = 'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz'
ARCHIVE_SHA = '9995a36d550f313fbde42d62fa778b63c1a9815d70841c202dca1447b295ac88'

def main():
    for n, h in json.loads((P / 'prediction_freeze.json').read_text()).items():
        assert digest(P / n) == h
    for n, h in json.loads((P / 'dependencies.json').read_text()).items():
        assert digest(R / n) == h
    assert digest(R / ARCHIVE) == ARCHIVE_SHA
    parent = json.loads((P / 'inputs/parent_CURRENT.json').read_text())
    before = pd.read_csv(B / parent['requirements'], low_memory=False)
    pred = pd.read_csv(P / 'predictions.csv.gz')
    regression = pd.read_csv(P / 'regression_predictions.csv.gz')
    controls = before[before.field.eq('goal_line_clearances') & ~before.is_open][K + ['value']].merge(regression, on=K, validate='one_to_one', suffixes=('_approved', '_predicted'))
    controls['agrees'] = controls.value_approved.eq(controls.value_predicted)
    archive = pd.read_csv(R / ARCHIVE, low_memory=False)
    positive = archive[archive.clearanceOffLine.gt(0)][K + ['clearanceOffLine']]
    contradictions = positive.merge(pred, on=K, validate='one_to_one')
    out = P / 'results'
    out.mkdir(exist_ok=True)
    save(controls, 'results/controls.csv.gz')
    save(contradictions, 'results/positive_contradictions.csv.gz')
    pending = before[before.field.eq('goal_line_clearances') & before.is_open & before.status.eq('missing_data')]
    overlay = pending[K + ['field']].merge(pred[K + ['value']], on=K, validate='one_to_one')
    plan = json.loads((P / 'plan.json').read_text())
    g = plan['gates']
    primary_controls = controls[controls.scope.eq('primary_match_block')]
    qualified = len(primary_controls) >= g['min_primary_controls'] and len(primary_controls[['season', 'fixture']].drop_duplicates()) >= g['min_primary_control_fixtures'] and len(controls) >= g['min_controls'] and int((~controls.agrees).sum()) <= g['max_errors'] and len(contradictions) <= g['max_positive_contradictions']
    validation = dict(
        qualified=bool(qualified), qualified_fields=['goal_line_clearances'] if qualified else [],
        controls=len(controls), control_fixtures=len(controls[['season', 'fixture']].drop_duplicates()),
        errors=int((~controls.agrees).sum()), positive_contradictions=len(contradictions),
        primary_controls=len(primary_controls), primary_control_fixtures=len(primary_controls[['season', 'fixture']].drop_duplicates()),
        candidate_fields=len(overlay), new_fields=len(overlay) if qualified else 0,
        source='Previously qualified primary match counters only; previous failed 2020 season ranking remains unchanged and is not used.',
        archive_sha256=ARCHIVE_SHA,
        limits='Previously qualified primary component counters, exact roster exhaustion where needed, and deduplicated shared-source GL regression; not independent holdout or final collective QA. GK, missing/nonzero blocks and rejected minute/event cases outside this source are withheld.',
    )
    write(out / 'validation.json', validation)
    if qualified:
        save(overlay, 'results/overlay.csv.gz')
    print(json.dumps(validation, indent=2))

if __name__ == '__main__':
    main()
