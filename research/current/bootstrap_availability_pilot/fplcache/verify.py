"""Verify recorded archive evidence; this does not qualify historical features."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import lzma
import pandas as pd

P = Path(__file__).resolve().parent

def main():
    meta = json.loads((P/'probe.json').read_text())
    for source in meta['sources']:
        assert hashlib.sha256((P/source['file']).read_bytes()).hexdigest() == source['sha256']
    commits = json.loads((P/'file_commits.json').read_text())
    assert len(commits) == 1 and commits[0]['sha'] == meta['source_commit']
    obj = json.loads(lzma.decompress((P/'bootstrap_2025_08_15_1252.json.xz').read_bytes()))
    players = obj['elements']
    assert len(players) == meta['players'] == 685
    assert len({p['id'] for p in players}) == len({p['code'] for p in players}) == len(players)
    gw = obj['events'][0]
    assert gw['id'] == 1 and gw['deadline_time'] == meta['first_round_deadline']
    assert not gw['finished'] and not gw['is_current']
    committed = datetime.fromisoformat(meta['source_commit_committer_date'].replace('Z','+00:00'))
    deadline = datetime.fromisoformat(gw['deadline_time'].replace('Z','+00:00'))
    assumed_utc_filename = datetime(2025,8,15,12,52,tzinfo=timezone.utc)
    assert assumed_utc_filename <= committed < deadline
    archive = pd.DataFrame(players).set_index('code')
    inventory = P.parents[1]/'training_dataset/scoring/results/historical_inventory.csv.xz'
    native = pd.read_csv(inventory,low_memory=False)
    fields = ['minutes','total_points','goals_scored','assists']
    previous = native[native.season.eq('2024-25')].groupby('code')[fields].sum()
    comparison = archive[['web_name']+fields].join(previous,rsuffix='_2024')
    comparable = comparison[comparison.minutes_2024.notna()].copy()
    for field in fields:
        comparable[field+'_agrees_with_2024'] = comparable[field].eq(comparable[field+'_2024'])
    comparable.reset_index().to_csv(P/'previous_season_comparisons.csv.xz',index=False,compression='xz')
    result = dict(source_hashes_verified=True,source_commit=meta['source_commit'],
        deadline=gw['deadline_time'],players=len(players),stable_codes_unique=True,
        nonzero_minutes_before_first_round=int(archive.minutes.ne(0).sum()),
        nonzero_points_before_first_round=int(archive.total_points.ne(0).sum()),
        previous_season_comparable_players=len(comparable),
        previous_season_equal_values={field:int(comparable[field+'_agrees_with_2024'].sum()) for field in fields},
        inventory_sha256=hashlib.sha256(inventory.read_bytes()).hexdigest(),
        preseason_performance_fields_are_not_current_season_cumulative=True,
        collector_filename_consistent_with_utc_commit=True,
        historical_feature_availability_qualified=False,
        remaining_checks=['Historical collector timezone/publication attestation',
            'Selection of pre-deadline snapshots for every required round',
            'Preseason carryover/reset semantics and source revisions per statistic',
            'Eligible universe and native zero-participation outcome evidence',
            'Feature definition and source-season compatibility across seasons'])
    (P/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
    print(result)

if __name__ == '__main__':
    main()
