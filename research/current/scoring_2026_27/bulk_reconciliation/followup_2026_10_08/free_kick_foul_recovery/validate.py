"""Compare only frozen rule-compatible one-goal vectors to native FPL truth."""
from pathlib import Path
import json,gzip,hashlib
import pandas as pd
from prepare import P,S,B,R,K,digest
OUT=P/'results'
def save(frame,name):
    raw=frame.to_csv(index=False).encode()
    (OUT/name).write_bytes(gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw)
def main():
    OUT.mkdir(exist_ok=True)
    for path,sha in json.loads((P/'inputs/manifest.json').read_text())['files'].items():assert digest(R/path)==sha,path
    for path,sha in json.loads((P/'prediction_freeze.json').read_text())['files'].items():assert digest(R/path)==sha,path
    plan=pd.read_csv(P/'plan.csv.gz')
    baseline=pd.read_csv(S/'assist_intentional_pass/baseline/fpl_baseline.csv.gz',usecols=K+['assists'])
    controls=plan.merge(baseline,on=K,validate='one_to_one')
    assert len(controls)==len(plan) and controls.assists.notna().all()
    controls['agrees']=controls.predicted_assists.eq(controls.assists)
    vectors=controls.groupby(['season','fixture','match_id','event_id','kind']).agg(players=('code','size'),
        predicted_assists=('predicted_assists','sum'),native_assists=('assists','sum'),
        agrees=('agrees','all')).reset_index()
    save(controls,'player_controls.csv.gz');save(vectors,'goal_vector_controls.csv')
    pred=pd.read_csv(P/'predictions.csv.gz').fillna({'recipient_player_id':''})
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text())
    old=pd.read_csv(B/parent['assist_goal_decisions']).fillna({'recipient_player_id':''})
    joined=pred.merge(old[['match_id','event_id','status','recipient_player_id']],on=['match_id','event_id'],suffixes=('','_approved'),validate='one_to_one')
    conflicts=joined[joined.status_approved.ne('unresolved') & (~joined.status.eq(joined.status_approved)|~joined.recipient_player_id.eq(joined.recipient_player_id_approved))]
    save(conflicts,'protected_conflicts.csv')
    denied=pd.read_csv(S/'assist_touch_bounds/results/candidate_exclusions.csv.gz')
    denials={(r.match_id,int(r.event_id),r.player_id) for r in denied.itertuples()}
    denials.update((r['match_id'],int(r['goal_event_id']),r['candidate_player_id']) for r in json.loads((S/'assist_intentional_pass/inputs/official_cases.json').read_text()) if not r['expected_award'])
    denial_conflicts=pred[pred.status.eq('awarded')].apply(lambda r:(r.match_id,int(r.event_id),r.recipient_player_id) in denials,axis=1).sum()
    gate=json.loads((P/'protocol.json').read_text())['gate']
    counts=vectors.kind.value_counts().to_dict()
    qualified=(len(vectors)>=gate['minimum_control_goals'] and vectors.agrees.all() and len(conflicts)==0 and denial_conflicts==0)
    report=dict(control_goals=len(vectors),control_player_matches=len(controls),control_kinds=counts,
        control_seasons=vectors.season.value_counts().sort_index().to_dict(),
        goal_vector_errors=int((~vectors.agrees).sum()),player_errors=int((~controls.agrees).sum()),
        protected_conflicts=len(conflicts),candidate_denial_conflicts=int(denial_conflicts),
        qualified_kinds=sorted(k for k,n in counts.items() if qualified and n>=gate['minimum_control_goals_per_kind']),
        limits='Rule-compatible historical/native FPL whole-team regression, shared Opta lineage and previously seen outcomes. Not untouched holdout, not general historical assist-rule transfer.')
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
if __name__=='__main__':main()
