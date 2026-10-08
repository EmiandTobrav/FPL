"""Freeze whole-season keeper inventories before direct-counter comparisons."""
from pathlib import Path
import hashlib
import json
import pandas as pd

P = Path(__file__).resolve().parent
B = P.parent.parent
R = B.parent.parent

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    P.joinpath('inputs/raw').mkdir(parents=True, exist_ok=True)
    parent = B/'CURRENT.json'
    pointer = json.loads(parent.read_text())
    reqpath = B/pointer['requirements']
    assert digest(reqpath) == pointer['requirements_sha256']
    req = pd.read_csv(reqpath, low_memory=False)
    targets = req[req.is_open & req.field.eq('saves_outside_box')]
    assert targets.season.eq('2025-26').all() and len(targets) == 16
    codes = set(targets.code)
    invpath = R/'training_dataset/scoring/results/historical_inventory.csv.xz'
    inv = pd.read_csv(invpath, low_memory=False)
    keepers = inv[inv.season.eq('2025-26') & inv.code.isin(codes) & inv.minutes.gt(0)].copy()
    assert keepers.position.eq('GK').all()
    fixturespath = R/'project/data/2025-26_fixtures.csv.gz'
    fixtures = pd.read_csv(fixturespath).set_index('id')
    rankedpath = B.parent/'delta_input_audit/inputs/primary/players_2025-26.json'
    ranked = json.loads(rankedpath.read_text())
    assert ranked['stats']['pageInfo']['numPages'] == 1
    ids = {int(x['owner']['altIds']['opta'].lstrip('p')):int(x['owner']['id'])
           for x in ranked['stats']['content'] if x['owner'].get('altIds', {}).get('opta')}
    rows = []
    for code, group in keepers.groupby('code', sort=True):
        pid = ids[int(code)]
        rows.append(dict(season='2025-26', fixture=0, code=int(code), pl_player_id=pid,
            pulse_id=0, minutes=int(group.minutes.sum()), appearances=len(group),
            kickoff_time='', fixture_code=0,
            url=f'https://footballapi.pulselive.com/football/stats/player/{pid}?comps=1&compSeasons=777&altIds=true'))
        for row in group.sort_values('fixture').itertuples():
            f = fixtures.loc[row.fixture]
            rows.append(dict(season=row.season, fixture=int(row.fixture), code=int(code),
                pl_player_id=pid, pulse_id=int(f.pulse_id), minutes=int(row.minutes), appearances=1,
                kickoff_time=f.kickoff_time, fixture_code=int(f.code),
                url=f'https://footballapi.pulselive.com/football/stats/player/{pid}?fixtures={int(f.pulse_id)}&altIds=true'))
    plan = pd.DataFrame(rows)
    assert not plan.duplicated(['season','fixture','code']).any()
    plan.to_csv(P/'plan.csv', index=False)
    (P/'inputs/parent_CURRENT.json').write_bytes(parent.read_bytes())
    protocol = dict(scope='Direct primary saved_ibox and saved_obox counts; field-specific qualification; native FPL saves retained independently',
        selection='All 12 keepers with the 16 remaining 2025/26 outside-box gaps; complete native appearance inventories, including every known inside/outside control',
        exploratory_pilot='Kelleher 37 appearances: 37 inside and 36 outside controls agree; one native-total-save difference is recorded and never used to derive location',
        controls_selected_before_other_keeper_comparisons=True,
        minimum_closed_controls_per_field_per_keeper=10,
        minimum_positive_outside_controls_per_keeper=5,
        maximum_location_control_disagreements=0,
        requirements=[
            'Unique primary player ID and explicit Opta ID match the native keeper code',
            'Every match has explicit appearances=1 and exact native minutes; full fixture plan matches the native season appearance set',
            'Primary season appearances and minutes equal the complete native inventory',
            'For each location field, the sum of all explicit nonnegative match counts exactly exhausts the explicit primary season count; only then omitted match counts are proved zero',
            'All closed inside and outside controls in the keeper season agree; any discrepancy vetoes that keeper',
            'Direct inside-plus-outside counts never exceed native FPL saves; any such discrepancy vetoes the keeper season',
            'Never infer outside from saves minus inside; never replace native saves or any closed location value',
            'Existing conflicts remain protected; only missing outside-box requirements may be filled',
            'This qualifies direct location inputs only, not BPS, bonus, targets or feature availability'],
        parent_requirements_sha256=digest(reqpath), plan_sha256=digest(P/'plan.csv'),
        input_sha256={str(x.relative_to(R)):digest(x) for x in [invpath, fixturespath, rankedpath]})
    (P/'protocol.json').write_text(json.dumps(protocol, indent=2)+'\n')
    print(json.dumps(dict(keepers=len(codes), appearances=len(keepers), jobs=len(plan), targets=len(targets))))

if __name__ == '__main__':
    main()
