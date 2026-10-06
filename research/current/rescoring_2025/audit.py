"""Audit archived inputs; same-season reconciliation is NOT historical rescoring.
Run from any directory: python research/current/rescoring_2025/audit.py
"""
from pathlib import Path
import hashlib
import json
import sys
import pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'project'))
from scoring import portable_core, defensive_points, allocate_bonus, self_test
OUT = Path(__file__).resolve().parent / 'results'
FIELDS = ['minutes', 'goals_scored', 'assists', 'bonus', 'bps',
          'clearances_blocks_interceptions', 'tackles', 'recoveries', 'defensive_contribution']

def run():
    OUT.mkdir(exist_ok=True)
    rows, hashes = [], {}
    for start in range(2019, 2026):
        season = f'{start}-{str(start+1)[2:]}'
        path = ROOT / 'project' / 'data' / f'{season}_gw.csv'
        d = pd.read_csv(path)
        hashes[str(path.relative_to(ROOT))] = hashlib.sha256(path.read_bytes()).hexdigest()
        row = {'season': season, 'raw_rows': len(d), 'fixtures': d.fixture.nunique(),
               'duplicate_player_fixture_rows': int(d.duplicated(['element', 'fixture']).sum())}
        row.update({f'{c}_nonnull': int(d[c].notna().sum()) if c in d else 0 for c in FIELDS})
        rows.append(row)
    pd.DataFrame(rows).to_csv(OUT / 'coverage.csv', index=False)
    d = pd.read_csv(ROOT / 'project/data/2025-26_gw.csv')
    scorecols = FIELDS + ['total_points','clean_sheets','goals_conceded','saves',
                         'penalties_saved','penalties_missed','yellow_cards','red_cards','own_goals','position']
    dup = d[d.duplicated(['element','fixture'], keep=False)]
    conflicts = int((dup.groupby(['element','fixture'])[scorecols].nunique(dropna=False).max(axis=1)>1).sum())
    assert conflicts == 0, 'Conflicting duplicate scoring inputs; inspect before deduplication'
    d = d.drop_duplicates(['element','fixture']).copy()
    d['pos'] = d.position.map({'GK':1,'DEF':2,'MID':3,'FWD':4})
    assert d.pos.notna().all() and d[scorecols].notna().all().all()
    predicted = portable_core(d) + 3*d.assists + d.bonus + defensive_points(d)
    active = d[d.minutes > 0].copy()
    bonus = active.groupby('fixture').bps.transform(lambda s: allocate_bonus(s))
    score_mismatch = int((predicted != d.total_points).sum())
    bonus_mismatch = int((bonus != active.bonus).sum())
    assert score_mismatch == bonus_mismatch == 0
    self_test()  # Threshold boundaries and tied bonus allocations.
    result = {'target_season':'2025-26', 'unique_player_fixture_rows':len(d),
              'fixtures':int(d.fixture.nunique()), 'active_player_fixture_rows':len(active),
              'conflicting_duplicate_scoring_keys':conflicts,
              'total_points_mismatches':score_mismatch, 'bonus_allocation_mismatches':bonus_mismatch,
              'validated':'Same-season arithmetic using official stored assists and BPS; defensive points from recorded counts.',
              'not_validated':'Historical new-rule assists or BPS reconstruction; provider equivalence; every rare rule branch.',
              'historical_exact_rescoring_ready':False,
              'blocker':'Pre-2025/26 archives lack defensive counts and verified target-rule assists/BPS.'}
    (OUT/'reconciliation.json').write_text(json.dumps(result, indent=2)+'\n')
    (OUT/'input_sha256.json').write_text(json.dumps(hashes, indent=2)+'\n')
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    run()
