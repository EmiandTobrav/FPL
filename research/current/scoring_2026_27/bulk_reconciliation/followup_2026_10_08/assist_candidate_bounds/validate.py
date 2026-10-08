from pathlib import Path
import json,hashlib
import pandas as pd
P=Path(__file__).resolve().parent;S=P.parent/'assist_intentional_pass'
def feasible(units,allowed):
    matched={}
    def put(unit,seen):
        for i,a in enumerate(allowed):
            if units[unit] not in a or i in seen:continue
            seen.add(i)
            if i not in matched or put(matched[i],seen):matched[i]=unit;return True
        return False
    return all(put(i,set()) for i in range(len(units)))
def main():
    freeze=json.loads((P/'prediction_freeze.json').read_text())
    for n,d in freeze['inputs'].items():assert hashlib.sha256((P.parent/n).read_bytes()).hexdigest()==d
    assert hashlib.sha256((P/'bounds.csv.gz').read_bytes()).hexdigest()==freeze['prediction_sha256']
    bounds=pd.read_csv(P/'bounds.csv.gz').set_index(['match_id','event_id']).candidate_player_id.to_dict()
    goals=pd.read_csv(S/'results/goal_decisions.csv.gz');old=goals.set_index(['match_id','event_id'])
    people=pd.read_csv(S/'inputs/participants.csv.gz').merge(pd.read_csv(S/'baseline/fpl_baseline.csv.gz')[['season','fixture','code','assists']],on=['season','fixture','code'],validate='one_to_one')
    plan=pd.read_csv(P/'validation_plan.csv');rows=[]
    for c in plan.to_dict('records'):
        g=goals[goals.match_id.eq(c['match_id'])&goals.scoring_team_id.eq(c['team_id'])]
        p=people[people.match_id.eq(c['match_id'])&people.team_id.eq(c['team_id'])]
        assert p.assists.notna().all() and len(g)==p.own_team_goals.iloc[0]
        players=set(p.player_id.dropna());allowed=[];new=0;bounded=0
        for r in g.itertuples():
            key=(r.match_id,r.event_id)
            if key in bounds:
                allowed.append({bounds[key]});bounded+=1;new+=r.status=='unresolved'
            else:allowed.append(players if r.own_goal else players-{r.scorer_player_id})
        units=[r.player_id for r in p.itertuples() for _ in range(int(r.assists))]
        rows.append({**c,'goals':len(g),'bounded_goals':bounded,'new_bounded_goals':new,'actual_assists':len(units),'feasible':feasible(units,allowed)})
    out=pd.DataFrame(rows);out.to_csv(P/'validation_results.csv',index=False)
    conflicts=[]
    for key,candidate in bounds.items():
        r=old.loc[key]
        if r.status=='awarded' and r.recipient_player_id!=candidate:conflicts.append({'match_id':key[0],'event_id':key[1],'candidate':candidate,'protected_recipient':r.recipient_player_id})
    pd.DataFrame(conflicts).to_csv(P/'protected_conflicts.csv',index=False)
    summary=dict(teams=len(out),fixtures=int(out.match_id.nunique()),bounded_goals=int(out.bounded_goals.sum()),new_bounded_goals=int(out.new_bounded_goals.sum()),infeasible_teams=int((~out.feasible).sum()),protected_conflicts=len(conflicts),qualified=bool(out.new_bounded_goals.sum()>=20 and out.feasible.all() and not conflicts),limits='Aggregate feasibility validates exclusions collectively, not individual assist awards. Shared supplier; historical season transfer still requires quality qualification.')
    (P/'validation_summary.json').write_text(json.dumps(summary,indent=2)+'\n');print(json.dumps(summary,indent=2))
if __name__=='__main__':main()
