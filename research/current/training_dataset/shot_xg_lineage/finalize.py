"""Verify retained source code and emit a deterministic lineage decision."""
import hashlib
import json
from pathlib import Path

P = Path(__file__).resolve().parent

def main():
    manifest = json.loads((P / 'sources.json').read_text())
    texts = {}
    for item in manifest['sources']:
        data = (P / item['file']).read_bytes()
        assert hashlib.sha256(data).hexdigest() == item['sha256'], item['file']
        texts[item['path']] = data.decode()
    checks = {
        'legacy_xg_own_model': ('scripts/enrich_shots_xg.R', ['xg_model.rds', 'predict(xg_model$model, X)', 'model is the only xG source']),
        'legacy_xgot_own_model': ('scripts/enrich_shots_xgot.R', ['xgot_model.rds', 'predict(']),
        'context_workflow': ('.github/workflows/daily-opta-scrape.yml', ['SHOT_MODELS: context', 'xg_model_v5.rds', 'xgot_model_v3.rds', 'score_shots_context.R']),
        'context_model_scoring': ('scripts/score_shots_context.R', ['readRDS(', 'add_xg_to_spadl']),
    }
    anchors = []
    for check, (path, needles) in checks.items():
        for needle in needles:
            assert needle in texts[path], (check, needle)
            anchors.append({'check': check, 'source': path, 'text': needle, 'line': next(i for i, line in enumerate(texts[path].splitlines(), 1) if needle in line)})
    result = {'investigation_status': 'completed_alternate_model_lineage', 'pinned_commit': manifest['commit'], 'verified_source_files': len(texts), 'anchors': anchors, 'qualification': 'not_qualified_as_native_FPL_expected_statistics', 'reason': 'Both published enrichment paths use Panna-trained model predictions. The legacy source says the model is the only current xG source; non-null preservation does not certify upstream or per-row historical native FPL lineage.', 'legacy_model_files': ['xg_model.rds', 'xgot_model.rds'], 'context_model_files': ['xg_model_v5.rds', 'xgot_model_v3.rds'], 'per_row_historical_model_version_certified': False, 'physical_events_disqualified': False, 'fields_closed': 0, 'native_expected_values_imported': 0, 'ledger_modified': False, 'scoring_modified': False, 'same_input_retry_allowed': False, 'reopening_condition': 'A specific native-compatible model/data provenance version, or another source with native FPL qualification evidence.'}
    (P / 'findings.json').write_text(json.dumps(result, indent=2) + '\n')
    print('Verified six pinned sources; zero expected-statistic imports')

if __name__ == '__main__':
    main()
