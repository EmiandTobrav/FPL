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
    controls = before[before.field.eq('goal_line_clearances') & ~before.is_open][K + ['value']].merge(pred, on=K, validate='one_to_one', suffixes=('_approved', '_predicted'))
    controls['scope']='closed_historical_ledger'
    references=pd.read_csv(P.parent/'goal_line_events/predictions.csv.gz')
    references=references[references.season.eq('2025-26')][K+['value']]
    extra=references.merge(pred,on=K,validate='one_to_one',suffixes=('_approved','_predicted'))
    extra['scope']='previously_qualified_2025_event_inventory'
    controls=pd.concat([controls,extra],ignore_index=True)
    assert not controls.duplicated(K).any()
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
    qualified = len(controls) >= g['minimum_controls'] and int((~controls.agrees).sum()) <= g['maximum_errors'] and len(contradictions) <= g['maximum_positive_archive_contradictions']
    validation = dict(
        qualified=bool(qualified), qualified_fields=['goal_line_clearances'] if qualified else [],
        controls=len(controls), control_fixtures=len(controls[['season', 'fixture']].drop_duplicates()),
        errors=int((~controls.agrees).sum()), positive_contradictions=len(contradictions),
        candidate_fields=len(overlay), new_fields=len(overlay) if qualified else 0,
        controls_by_scope=controls.groupby('scope').size().to_dict(), controls_by_season=controls.groupby('season').size().to_dict(),
        omitted_players_inferred_zero=False, failed_league_exhaustion_applied=False,
        archive_sha256=ARCHIVE_SHA,
        limits='Only explicit individual season GL zeros; active appearance/code identities checked. Shared-source approved GL regression, including52 prior qualified2025 event inventories; not native FPL GL, independent holdout or final collective QA. The separate failed league-total probe remains rejected; unlisted players are not zero.',
    )
    write(out / 'validation.json', validation)
    if qualified:
        save(overlay, 'results/overlay.csv.gz')
    print(json.dumps(validation, indent=2))

if __name__ == '__main__':
    main()
