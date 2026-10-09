"""Replay the six native CBI vetoes, without permitting any application."""
import gzip
import hashlib
import json
from pathlib import Path
import pandas as pd

P = Path(__file__).resolve().parent
R = P.parents[3]
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
INVENTORY_SHA = 'cb39bc8aadd9cc7f3f255be267fa2cc015c1ecd9efcf4d8dd4b951d62605bdc5'

def main():
    plan = json.loads((P / 'plan.json').read_text())
    assert digest(P / 'plan.json') == json.loads((P / 'plan_freeze.json').read_text())['plan_sha256']
    assert plan['application_allowed'] is False and plan['scoring_allowed'] is False
    for name in ['controls', 'roster']:
        assert digest(R / plan[name + '_file']) == plan[name + '_sha256']
    freeze = json.loads((P / 'inputs/source_freeze.json').read_text())
    assert digest(P / 'inputs/sources.json') == freeze['sources_sha256']
    sources = json.loads((P / 'inputs/sources.json').read_text())
    for item in sources:
        assert digest(P / item['file']) == item['sha256']
    assert len(sources) == 8
    commit = json.loads((P / 'inputs/commit.json').read_text())[0]['sha']
    assert commit == freeze['commit']
    for item in sources[1:]:
        assert commit in item['url']
    inventory_path = R / 'training_dataset/scoring/results/historical_inventory.csv.xz'
    assert digest(inventory_path) == INVENTORY_SHA
    inventory = pd.read_csv(inventory_path, low_memory=False)
    inventory = inventory[inventory.season.eq(plan['season'])]
    roster = pd.read_csv(P / 'inputs/players_raw.csv')
    selected = {p['code']: p for p in plan['players']}
    results = []
    for veto in plan['vetoes']:
        code, fixture = veto['code'], veto['fixture']
        player = selected[code]
        people = roster[roster.code.eq(code)]
        assert len(people) == 1
        for field in ['id', 'first_name', 'second_name']:
            assert people.iloc[0][field] == player[field]
        history = pd.read_csv(P / 'inputs' / (str(code) + '_history.csv'))
        assert not history.fixture.duplicated().any() and history.element.eq(player['id']).all()
        h = history[history.fixture.eq(fixture)]
        n = inventory[inventory.fixture.eq(fixture) & inventory.code.eq(code)]
        assert len(h) == len(n) == 1
        h, n = h.iloc[0], n.iloc[0]
        for field in ['element', 'kickoff_time', 'opponent_team', 'was_home', 'team_a_score', 'team_h_score', 'round', 'minutes']:
            assert h[field] == n[field], (code, fixture, field)
        assert int(n.clearances_blocks_interceptions) == veto['expected']
        results.append(dict(
            season=plan['season'], fixture=fixture, code=code,
            native_cbi=int(n.clearances_blocks_interceptions),
            history_cbi=int(h.clearances_blocks_interceptions),
            rejected_external_cbi=veto['actual'],
            native_bps=int(n.bps), history_bps=int(h.bps),
            cbi_revision=int(n.clearances_blocks_interceptions) != int(h.clearances_blocks_interceptions),
        ))
    frame = pd.DataFrame(results)
    assert len(frame) == 6 and not frame.cbi_revision.any()
    assert (frame.history_cbi != frame.rejected_external_cbi).all()
    out = P / 'results'
    out.mkdir(exist_ok=True)
    (out / 'comparisons.csv.gz').write_bytes(gzip.compress(frame.to_csv(index=False).encode(), mtime=0))
    report = dict(
        source_commit=commit, players=5, checked_vetoes=6, native_cbi_revisions=0,
        external_vetoes_retained=6, missing_keeper_cbi_withheld=341,
        fields_closed=0, corrections_created=0, ledger_modified=False,
        scoring_modified=False, native_inventory_sha256=INVENTORY_SHA,
        route_status='stopped_no_native_revision_at_any_frozen_veto',
        scope='Only the six frozen CBI vetoes; no claim of whole-season reconciliation or source qualification.',
    )
    (out / 'findings.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()
