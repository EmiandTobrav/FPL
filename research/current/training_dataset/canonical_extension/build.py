"""Add qualified whole fixtures to canonical v1; preserve full original inventory."""
from pathlib import Path
import hashlib
import importlib.util
import json
import pandas as pd

P = Path(__file__).resolve().parent
T = P.parent
R = T.parent
BASE = T/'canonical'
SOURCE = T/'scoring/season_2025_extension'
VERSION = 'fpl_2026_27_canonical_v3_partial'
K = ['season','fixture','code']
RK = ['season','round','code']

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    hashes = {}
    def js(path):
        hashes[str(path.relative_to(R))] = sha(path)
        return json.loads(path.read_text())
    def csv(path):
        hashes[str(path.relative_to(R))] = sha(path)
        return pd.read_csv(path,low_memory=False)
    parent = js(BASE/'results/manifest.json')
    for name, expected in parent['output_sha256'].items():
        if sha(BASE/'results'/name) != expected:
            raise ValueError('Frozen canonical parent changed')
        hashes[str((BASE/'results'/name).relative_to(R))] = expected
    source_manifest = js(SOURCE/'results/manifest.json')
    for name, expected in source_manifest['output_sha256'].items():
        if sha(SOURCE/'results'/name) != expected:
            raise ValueError('Qualified scoring producer changed')
        hashes[str((SOURCE/'results'/name).relative_to(R))] = expected
    spec = importlib.util.spec_from_file_location('frozen_canonical',BASE/'build.py')
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    if sha(BASE/'build.py') != parent['code_sha256']['training_dataset/canonical/build.py']:
        raise ValueError('Frozen aggregation semantics changed')
    pm = csv(BASE/'results/player_matches.csv.xz').set_index(K)
    previous = pm[pm.scoring_qualified][core.TARGETS].copy()
    source = csv(SOURCE/'results/player_matches.csv.xz').set_index(K)
    fields = core.TARGETS+['scoring_qualified','label_status','points_version',
        'times_tackled','saves_inside_box','saves_outside_box','big_chance_saves',
        'times_tackled_source','saves_inside_box_source','saves_outside_box_source','big_chance_saves_source']
    for field in fields:
        pm.loc[source.index,field] = source[field]
    excluded = (previous.index.get_level_values('season') == '2025-26') & (previous.index.get_level_values('fixture') == 365)
    removed = previous.index[excluded]
    if not pm.loc[removed,core.TARGETS].isna().all().all():
        raise ValueError('Known latest-primary revision was not quarantined')
    remaining = previous.index[~excluded]
    pd.testing.assert_frame_equal(previous.loc[remaining],pm.loc[remaining,core.TARGETS],check_dtype=False)
    pm = pm.reset_index()
    pm['dataset_version'] = VERSION
    if len(pm) != parent['counts']['player_matches'] or pm.duplicated(K).any():
        raise ValueError('Canonical inventory changed')
    if pm.loc[~pm.scoring_qualified,core.TARGETS].notna().any().any():
        raise ValueError('Unknown harmonized labels exposed')
    pr = csv(BASE/'results/player_rounds.csv.xz').set_index(RK)
    hist = pm[pm.season.ne('2026-27')]
    grouped = hist.groupby(RK,sort=True)
    size = grouped.size()
    for field in core.TARGETS:
        pr.loc[size.index,field] = core.strict_sum(grouped,field,size)
    pr.loc[size.index,'scoring_qualified'] = grouped.scoring_qualified.all()
    pr.loc[size.index,'label_status'] = 'blocked_missing_or_unqualified_fixture'
    pr.loc[pr.scoring_qualified & pr.index.isin(size.index),'label_status'] = 'qualified_complete_observed_round'
    pr = pr.reset_index()
    pr['dataset_version'] = VERSION
    if pr.duplicated(RK).any() or len(pr) != parent['counts']['player_rounds']:
        raise ValueError('Canonical round universe changed')
    future = core.horizon_targets(pr)
    ledger = js(P/'inputs/ledger_CURRENT.json')
    reqpath = R/'scoring_2026_27/bulk_reconciliation'/ledger['requirements']
    if sha(reqpath) != ledger['requirements_sha256']:
        raise ValueError('Frozen extended ledger changed')
    req = csv(reqpath)
    counters = req[K+['field','value','status','provenance','is_open','needs_external_quality_review']].copy()
    counters.loc[counters.is_open,'value'] = float('nan')
    qualified_keys = pd.MultiIndex.from_frame(pm.loc[pm.scoring_qualified,K])
    counters['value_qualified_for_scoring'] = pd.MultiIndex.from_frame(counters[K]).isin(qualified_keys)
    counters['before_deadline_feature_qualified'] = False
    coverage = []
    for season, group in pm.groupby('season',sort=True):
        for field in core.STATS+core.TARGETS+['times_tackled','big_chance_saves','saves_inside_box','saves_outside_box']:
            coverage.append(dict(season=season,field=field,canonical_rows=len(group),
                populated_rows=int(group[field].notna().sum()),
                populated_scoring_qualified_rows=int((group[field].notna()&group.scoring_qualified).sum()),
                before_deadline_feature_qualified_rows=0))
    summary = dict(parent['counts'])
    summary.update(version=VERSION,qualified_player_match_labels=int(pm.scoring_qualified.sum()),
        qualified_player_round_labels=int(pr.scoring_qualified.sum()),
        qualified_whole_historical_fixtures=source_manifest['counts']['qualified_whole_fixtures'],
        qualified_next_round_targets=int(future.target_next_1_qualified.sum()),
        qualified_next_three_round_targets=int(future.target_next_3_qualified.sum()),
        qualified_next_six_round_targets=int(future.target_next_6_qualified.sum()),
        historical_open_fields=ledger['open_fields'],previous_still_qualified_point_labels_preserved=True,
        source_revision_fixtures=[337,365],prior_qualified_fixture_quarantined=365)
    out = P/'results'
    out.mkdir(exist_ok=True)
    for frame,name in [(pm,'player_matches.csv.xz'),(pr,'player_rounds.csv.xz'),
        (future,'next_round_targets.csv.xz'),(counters,'input_counters.csv.xz'),
        (pd.DataFrame(coverage),'statistic_coverage.csv')]:
        core.save(frame,out/name)
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    manifest = dict(version=VERSION,points_standard='2026-27',training_ready=False,path_root='research/current',
        input_sha256=hashes,code_sha256={str(p.relative_to(R)):sha(p) for p in [Path(__file__).resolve(),BASE/'build.py']},
        output_sha256={p.name:sha(p) for p in sorted(out.iterdir()) if p.is_file() and p.name!='manifest.json'},counts=summary)
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(json.dumps(summary,indent=2),flush=True)

if __name__ == '__main__':
    main()
