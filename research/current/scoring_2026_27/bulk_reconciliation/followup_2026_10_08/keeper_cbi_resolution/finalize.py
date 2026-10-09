"""One consolidated keeper-CBI decision and exact remaining target inventory."""
import json
import shutil
import pandas as pd
from event_audit import P, R, S, K, digest, write, save

B = S.parent
REFERENCES = [
    S / 'fotmob_keeper_cbi/results/control_comparisons.csv',
    S / 'fotmob_keeper_cbi/results/keeper_predictions.csv',
    S / 'fotmob_keeper_cbi/protocol.json',
    S / 'keeper_cbi_source_check/archive_comparison.csv',
    S / 'keeper_cbi_source_check/primary_comparison.csv',
    S / 'keeper_native_history/results/comparisons.csv.gz',
    S / 'keeper_native_history/results/findings.json',
]

def prepare_scope():
    assert not (P / 'casefile_scope_freeze.json').exists()
    parent = json.loads((B / 'CURRENT.json').read_text())
    assert digest(B / parent['remaining_fields']) == parent['remaining_fields_sha256']
    shutil.copy2(B / 'CURRENT.json', P / 'inputs/ledger_CURRENT.json')
    shutil.copy2(B / parent['remaining_fields'], P / 'inputs/remaining_fields.csv.xz')
    write(P / 'casefile_scope_freeze.json', dict(
        local={n: digest(P / n) for n in ['inputs/ledger_CURRENT.json', 'inputs/remaining_fields.csv.xz']},
        references={str(f.relative_to(R)): digest(f) for f in REFERENCES},
        direction='Complete the started keeper-CBI track; never reopen the same failed routes without specific new source evidence.',
        user_source_access='User confirmed no known additional source access on 2026-10-09.',
    ))

def main():
    frozen = json.loads((P / 'casefile_scope_freeze.json').read_text())
    for n, h in frozen['local'].items():
        assert digest(P / n) == h
    for n, h in frozen['references'].items():
        assert digest(R / n) == h
    remaining = pd.read_csv(P / 'inputs/remaining_fields.csv.xz', low_memory=False)
    missing = remaining[remaining.field.eq('clearances_blocks_interceptions') & remaining.position.eq('GK')].copy()
    assert len(missing) == 341 and missing.status.eq('missing_data').all() and missing.value.isna().all()
    source = pd.read_csv(S / 'fotmob_keeper_cbi/results/keeper_predictions.csv')
    targets = missing[K + ['field', 'name', 'status', 'value']].merge(source[K + ['candidate_cbi', 'historical_target_group_compatible']], on=K, how='left', validate='one_to_one')
    targets['applied'] = False
    targets['blocker'] = 'native_keeper_mapping_gate_failed_six_vetoes'
    save(targets, 'results/remaining_keeper_targets.csv.gz')
    archive = pd.read_csv(S / 'keeper_cbi_source_check/archive_comparison.csv')
    native = pd.read_csv(S / 'keeper_native_history/results/comparisons.csv.gz')
    diagnostic = pd.read_csv(P / 'results/six_veto_event_counts.csv.gz')
    cases = archive.merge(native[K + ['history_cbi', 'native_bps', 'history_bps']], on=K, validate='one_to_one')
    cases = cases.merge(diagnostic[K + ['type11', 'type41', 'type8', 'type12', 'type59', 'diagnostic_claim_punch_interception']], on=K, validate='one_to_one')
    assert len(cases) == 6 and cases.history_cbi.eq(cases.expected).all()
    cases['resolution'] = 'unresolved_FPL_specific_event_inclusion_or_source_revision'
    cases['required_new_evidence'] = 'Documented FPL-compatible keeper CBI mapping or corrected provider data version that explains native values and passes the full fixed control population.'
    save(cases, 'results/six_case_decisions.csv.gz')
    controls = pd.read_csv(S / 'fotmob_keeper_cbi/results/control_comparisons.csv')
    controls = controls[controls.kind.eq('native_fpl_keeper_cbi')]
    native_failures = int((~controls.agrees).sum())
    diagnostic = json.loads((P / 'results/findings.json').read_text())
    assert native_failures == 6 and diagnostic['hypothesis_errors'] == 369
    historical = pd.read_csv(S / 'fotmob_keeper_cbi/results/control_comparisons.csv')
    historical = historical[~historical.kind.eq('native_fpl_keeper_cbi')]
    report = dict(
        track='keeper_cbi', investigation_status='consolidated_source_block_demonstrated',
        data_completion_status='not_complete', missing_keeper_requirements=341,
        covered_source_candidate_rows=int(targets.candidate_cbi.notna().sum()),
        compatible_historical_target_groups=int(targets.historical_target_group_compatible.fillna(False).sum()),
        protected_outfield_cbi_conflicts=int((remaining.field.eq('clearances_blocks_interceptions') & remaining.status.eq('external_conflict')).sum()),
        native_controls=len(controls), native_fixtures=len(controls[['season','fixture']].drop_duplicates()),
        native_positive_controls=int(controls.expected.gt(0).sum()), native_source_vetoes=native_failures,
        historical_controls=len(historical), historical_errors=int((~historical.agrees).sum()),
        native_history_vetoes_revised=0, diagnostic_hypothesis_errors=369,
        fields_closed=0, applied=False, ledger_modified=False,
        next_required_evidence='FPL-specific CBI event inclusion or a corrected compatible source version; six-case outcome fitting and repeated unchanged source downloads are insufficient.',
        resume_condition='A specific new source record/version or provider definition explaining the six vetoes; then rerun all original native/historical/identity/minute/team gates, with no control removal or threshold reduction.',
        same_source_retry_allowed=False,
        scope='Keepers only. All 341 missing values remain missing; the 204 outfield conflicts are preserved separately.',
    )
    write(P / 'TRACK_CURRENT.json', report)
    write(P / 'manifest.json', {str(f.relative_to(P)): digest(f) for f in sorted(P.rglob('*')) if f.is_file() and '__pycache__' not in str(f) and f.name not in ['manifest.json', 'replay_report.json']})
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    import sys
    prepare_scope() if len(sys.argv) > 1 and sys.argv[1] == 'prepare' else main()
