"""Consolidated event evidence; diagnostic hypotheses never apply values."""
import gzip
import hashlib
import json
import sys
from pathlib import Path
import pandas as pd

P = Path(__file__).resolve().parent
R = P.parents[3]
S = P.parent
K = ['season', 'fixture', 'code']
RAW_SHA = 'a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2'

def digest(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def write(p, v):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(v, indent=2) + '\n')

def save(frame, name):
    path = P / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(frame.to_csv(index=False).encode(), mtime=0))

def prepare():
    controls = S / 'fotmob_keeper_cbi/results/control_comparisons.csv'
    projection = R / 'scoring_2026_27/delta_input_audit/inputs/archive_projection.csv.gz'
    c = pd.read_csv(controls)
    c = c[c.kind.eq('native_fpl_keeper_cbi')]
    assert len(c) == 569
    a = pd.read_csv(projection, low_memory=False)
    m = c.merge(a[K + ['match_id', 'player_id']], on=K, validate='one_to_one')
    assert len(m) == 569 and m[['match_id', 'player_id']].notna().all().all()
    save(m, 'inputs/control_identity_mapping.csv.gz')
    write(P / 'plan.json', dict(
        diagnostic_only=True, application_allowed=False,
        scope='All 569 frozen native keeper controls; six old vetoes kept explicitly.',
        prior_exploration='Six veto event streams were inspected first. Claims plus punches happens to equal all six native values. This is outcome-informed discovery, not a qualified rule.',
        fixed_hypothesis='Count type11 + type41 + type8 events for a keeper, compared diagnostically with native CBI. No fitted time windows, outcomes, calibration or case-specific corrections.',
        source_type_labels_provisional={'11': 'claim', '41': 'punch', '8': 'interception', '12': 'clearance', '59': 'keeper_sweeper'},
        definition_source='https://www.statsperform.com/opta-event-definitions/',
        definition_limit='Public definitions distinguish punches, clearances and keeper sweeper, but do not specify FPL CBI inclusion or the numerical event-ID mapping used by this archive.',
        raw_sha256=RAW_SHA,
        dependencies={str(controls.relative_to(R)): digest(controls), str(projection.relative_to(R)): digest(projection)},
    ))
    write(P / 'selection_freeze.json', {n: digest(P / n) for n in ['plan.json', 'inputs/control_identity_mapping.csv.gz']})

def extract(raw):
    import pyarrow.parquet as pq
    assert digest(raw) == RAW_SHA
    for n, h in json.loads((P / 'selection_freeze.json').read_text()).items():
        assert digest(P / n) == h
    mapping = pd.read_csv(P / 'inputs/control_identity_mapping.csv.gz')
    selected = pq.read_table(raw, filters=[('season', '=', '2025-2026'), ('match_id', 'in', mapping.match_id.unique().tolist())]).to_pandas()
    assert not selected.duplicated(['match_id', 'event_id']).any()
    save(selected.sort_values(['match_id', 'period_id', 'minute', 'second', 'event_id']), 'inputs/complete_control_match_events.csv.gz')
    write(P / 'inputs/source_freeze.json', dict(raw_sha256=RAW_SHA, source_rows=len(selected), matches=selected.match_id.nunique(), projection_sha256=digest(P / 'inputs/complete_control_match_events.csv.gz')))

def audit():
    for n, h in json.loads((P / 'selection_freeze.json').read_text()).items():
        assert digest(P / n) == h
    plan = json.loads((P / 'plan.json').read_text())
    for n, h in plan['dependencies'].items():
        assert digest(R / n) == h
    freeze = json.loads((P / 'inputs/source_freeze.json').read_text())
    assert digest(P / 'inputs/complete_control_match_events.csv.gz') == freeze['projection_sha256']
    events = pd.read_csv(P / 'inputs/complete_control_match_events.csv.gz')
    assert len(events) == freeze['source_rows'] and events.match_id.nunique() == freeze['matches']
    mapping = pd.read_csv(P / 'inputs/control_identity_mapping.csv.gz')
    rows = []
    for r in mapping.itertuples():
        e = events[events.match_id.eq(r.match_id) & events.player_id.eq(r.player_id)]
        assert len(e) > 0
        counts = e.type_id.value_counts().to_dict()
        hypothesis = sum(counts.get(x, 0) for x in [11, 41, 8])
        rows.append(dict(season=r.season, fixture=r.fixture, code=r.code, native_cbi=r.expected,
                         rejected_source_cbi=r.actual, old_veto=not r.agrees,
                         type11=int(counts.get(11, 0)), type41=int(counts.get(41, 0)),
                         type8=int(counts.get(8, 0)), type12=int(counts.get(12, 0)),
                         type59=int(counts.get(59, 0)), diagnostic_claim_punch_interception=hypothesis,
                         diagnostic_agrees=hypothesis == r.expected))
    frame = pd.DataFrame(rows)
    save(frame, 'results/all_native_diagnostic.csv.gz')
    save(frame[frame.old_veto], 'results/six_veto_event_counts.csv.gz')
    # Every event in each veto match is preserved, not only candidate actions.
    veto_ids = mapping.loc[~mapping.agrees, 'match_id']
    save(events[events.match_id.isin(veto_ids)], 'results/six_complete_veto_match_events.csv.gz')
    report = dict(native_controls=len(frame), frozen_vetoes=int(frame.old_veto.sum()),
                  hypothesis_errors=int((~frame.diagnostic_agrees).sum()),
                  hypothesis_veto_errors=int((~frame.loc[frame.old_veto, 'diagnostic_agrees']).sum()),
                  hypothesis_qualified=False, application_allowed=False, fields_closed=0,
                  limits='Outcome-informed diagnostic. Neither a new holdout nor documented FPL event inclusion. No failing control is excluded and no source counter is replaced.')
    write(P / 'results/findings.json', report)
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    if sys.argv[1] == 'prepare':
        prepare()
    elif sys.argv[1] == 'extract':
        extract(Path(sys.argv[2]))
    else:
        audit()
