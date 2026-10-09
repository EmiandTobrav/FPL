"""Outcome-blind control selection for an officially unchanged assist subset."""
from pathlib import Path
import gzip,hashlib,json
import pandas as pd
P=Path(__file__).resolve().parent;S=P.parent;B=S.parent;R=B.parent.parent
K=['season','fixture','code']
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def freeze_write(path,payload):
    if path.exists():assert path.read_bytes()==payload, 'Frozen selection changed: '+path.name
    path.write_bytes(payload)
def main():
    original=S/'penalty_foul_recovery'
    old=json.loads((original/'freeze.json').read_text())
    assert digest(original/'predictions.csv.gz')==old['predictions_sha256']
    for name,sha in old['inputs'].items():assert digest(S/name)==sha
    pred=pd.read_csv(original/'predictions.csv.gz').fillna({'recipient_player_id':''})
    people=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz')
    cover=pd.read_csv(S/'assist_intentional_pass/results/team_coverage.csv').set_index(['match_id','team_id']).coverage_ok.to_dict()
    assert not pred.duplicated(['match_id','event_id']).any()
    teams={key:g for key,g in people.groupby(['match_id','team_id'])}
    plan=[]
    for row in pred.itertuples():
        key=(row.match_id,row.scoring_team_id)
        if not cover.get(key,False) or key not in teams:continue
        group=teams[key]
        if not group.own_team_goals.eq(1).all() or group.player_id.isna().any() or group.player_id.duplicated().any():continue
        if row.foul_winner not in set(group.player_id):continue
        for person in group.itertuples():
            plan.append(dict(season=row.season,fixture=int(row.fixture),match_id=row.match_id,event_id=row.event_id,
                kind=row.kind,team_id=row.scoring_team_id,code=int(person.code),player_id=person.player_id,
                predicted_assists=int(row.status=='awarded' and row.recipient_player_id==person.player_id)))
    plan=pd.DataFrame(plan).sort_values(['season','fixture','event_id','code'])
    freeze_write(P/'plan.csv.gz',gzip.compress(plan.to_csv(index=False).encode(),mtime=0))
    freeze_write(P/'predictions.csv.gz',(original/'predictions.csv.gz').read_bytes())
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text())
    files=[P/'protocol.json',Path(__file__),P/'inputs/parent_CURRENT.json',original/'freeze.json',original/'rule.py',
        original/'predictions.csv.gz',S/'assist_intentional_pass/inputs/participants.csv.gz',
        S/'assist_intentional_pass/results/team_coverage.csv',
        S/'assist_intentional_pass/baseline/fpl_baseline.csv.gz',S/'assist_intentional_pass/baseline/build.py',
        S/'assist_intentional_pass/inputs/official_cases.json',
        S/'assist_touch_bounds/results/goal_decisions.csv.gz',S/'assist_touch_bounds/results/candidate_exclusions.csv.gz',
        S/'assist_touch_bounds/results/player_match_totals.csv.gz']
    files.extend(S/name for name in old['inputs'])
    files.extend(B/parent[key] for key in ['requirements','player_match_readiness','match_readiness'])
    manifest={'files':{str(f.relative_to(R)):digest(f) for f in dict.fromkeys(files)},'native_assist_outcomes_read_by_selection':False}
    freeze_write(P/'inputs/manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())
    frozen={'files':{str(f.relative_to(R)):digest(f) for f in [P/'inputs/manifest.json',P/'predictions.csv.gz',P/'plan.csv.gz']},'outcomes_read_by_selection':False}
    freeze_write(P/'prediction_freeze.json',(json.dumps(frozen,indent=2)+'\n').encode())
    goals=plan.drop_duplicates(['match_id','event_id'])
    print({'selected_goals':len(goals),'by_kind':goals.kind.value_counts().to_dict(),'by_season':goals.season.value_counts().to_dict()})
if __name__=='__main__':main()
