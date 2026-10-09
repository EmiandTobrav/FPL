"""Acquire source goals and canonical identities; do not predict new assist rules."""
import json
import pandas as pd
from prepare import P,S,B,R,K,digest,save,freeze_write

def main():
    for name,h in json.loads((P/'selection_freeze.json').read_text()).items():assert digest(P/name)==h,name
    for name,h in json.loads((P/'dependencies.json').read_text()).items():assert digest(R/name)==h,name
    source=S/'espn_primary_identity';plan=pd.read_csv(P/'inputs/plan.csv.gz');native=pd.read_csv(P/'inputs/native_identity_scope.csv.gz')
    source_people=pd.read_csv(source/'players.csv.gz');source_goals=pd.read_csv(source/'goal_events.csv.gz');source_gates=pd.read_csv(source/'fixture_gates.csv');srcs=json.loads((source/'inputs/sources.json').read_text());source_map={s['file']:s for s in srcs}
    old_people=pd.read_csv(S/'assist_intentional_pass/inputs/participants.csv.gz');people=old_people.copy()
    parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());old_goals=pd.read_csv(B/parent['assist_goal_decisions']);assert old_goals.event_id.is_unique
    rows=[];identities=[];cover=[];raw_proofs=[]
    for f in plan.itertuples():
        key=(f.season,f.fixture);old=old_goals[old_goals.season.eq(f.season)&old_goals.fixture.eq(f.fixture)];assert old.empty
        gate=source_gates[source_gates.season.eq(f.season)&source_gates.fixture.eq(f.fixture)];assert len(gate)==1 and gate.complete.all()
        selected=people.season.eq(f.season)&people.fixture.eq(f.fixture);original=people[selected];ni=native[native.season.eq(f.season)&native.fixture.eq(f.fixture)]
        sp=source_people[source_people.season.eq(f.season)&source_people.fixture.eq(f.fixture)]
        assert set(sp.code)<=set(original.code) and not sp.code.duplicated().any() and sp.espn_player_id.notna().all() and not sp.espn_player_id.duplicated().any()
        extra=ni[ni.code.isin(set(original.code)-set(sp.code))]
        assert len(extra)==len(set(original.code)-set(sp.code)) and extra[['goals_scored','own_goals']].eq(0).all().all(),(key,extra.to_dict('records'))
        joined=sp.merge(ni,on=K,validate='one_to_one');assert joined.native_goals.eq(joined.goals_scored).all() and joined.native_own_goals.eq(joined.own_goals).all()
        mids=original.match_id.dropna().unique();assert len(mids)<=1;mid=mids[0] if len(mids) else f'fpl_fixture:{f.season}:{f.fixture}'
        people.loc[selected,'match_id']=people.loc[selected,'match_id'].fillna(mid)
        teamcodes=ni.set_index('code').historical_team_id.to_dict()
        for i in people.index[selected]:
            if pd.isna(people.at[i,'player_id']):people.at[i,'player_id']=f'fpl_player:{int(people.at[i,"code"])}'
            if pd.isna(people.at[i,'team_id']):people.at[i,'team_id']=f'fpl_team:{f.season}:{int(teamcodes[people.at[i,"code"]])}'
        updated=people[selected];assert updated.player_id.notna().all() and updated.team_id.notna().all() and updated.player_id.is_unique
        cp=updated.merge(sp[['code','espn_player_id','espn_team_id']],on='code',how='left',validate='one_to_one');provider=cp.dropna(subset=['espn_player_id']).set_index('espn_player_id').to_dict('index');teams=cp[['team_id','espn_team_id']].dropna().drop_duplicates();assert len(teams)==2 and not teams.espn_team_id.duplicated().any();team_map=teams.set_index('espn_team_id').team_id.to_dict()
        rawname=f'inputs/raw/summary_{f.espn_event_id}.json';assert digest(source/rawname)==source_map[rawname]['sha256'];raw=json.loads((source/rawname).read_bytes());raw_proofs.append(source_map[rawname])
        clocks={}
        for entry in raw.get('commentary',[]):
            play=entry.get('play',{});pid=play.get('id')
            if pid:
                data=(play.get('period',{}).get('number'),play.get('clock',{}).get('value'))
                if pid in clocks:assert clocks[pid]==data
                clocks[pid]=data
        sg=source_goals[source_goals.season.eq(f.season)&source_goals.fixture.eq(f.fixture)]
        for event in sg.itertuples():
            assert event.recognized and event.espn_player_id in provider
            person=provider[event.espn_player_id];tid=person['espn_team_id']
            if not event.own_goal:assert tid==event.espn_team_id
            scoring_team=[v for k,v in team_map.items() if k!=tid][0] if event.own_goal else team_map[tid]
            assert str(int(event.event_id)) in clocks
            period,clock=clocks[str(int(event.event_id))];assert period in [1,2] and clock is not None
            rows.append(dict(season=f.season,fixture=f.fixture,match_id=mid,event_id=-int(event.event_id),period_id=period,clock=clock,status='unresolved',recipient_player_id=None,scoring_team_id=scoring_team,scorer_player_id=person['player_id'],own_goal=event.own_goal,reason='complete_goal_inventory_causal_assist_facts_pending',route='source_goal_inventory_pending',evidence_event_ids=str(int(event.event_id)),missing='causal_target_assist_facts',raw_status='unresolved',source_url=source_map[rawname]['url'],evidence_scope='qualified_ESPN_native_goal_vector_complete_inventory',required_for_historical_assist_recalculation=True))
        local=[r for r in rows if r['season']==f.season and r['fixture']==f.fixture]
        for team,g in updated.groupby('team_id'):
            expected=g.own_team_goals.unique();assert len(expected)==1
            actual=sum(r['scoring_team_id']==team for r in local);assert expected[0]==actual,(f.season,f.fixture,team,expected[0],actual,local)
            cover.append(dict(season=f.season,fixture=f.fixture,match_id=mid,team_id=team,expected_goals=expected[0],observed_goals=actual,coverage_ok=True))
        identities.extend(cp[K+['match_id','team_id','player_id','espn_player_id','espn_team_id']].to_dict('records'))
    additions=pd.DataFrame(rows);assert additions.event_id.is_unique and not additions.event_id.isin(old_goals.event_id).any();assert additions.status.eq('unresolved').all()
    save(additions,P/'goal_inventory.csv.gz');save(people,P/'participants.csv.gz');save(pd.DataFrame(identities),P/'identity_bridge.csv.gz');save(pd.DataFrame(cover),P/'team_goal_coverage.csv.gz')
    for col in old_people:
        if col not in ['match_id','team_id','player_id']:pd.testing.assert_series_equal(people[col],old_people[col])
        else:assert people.loc[old_people[col].notna(),col].equals(old_people.loc[old_people[col].notna(),col])
    freeze=dict(files={name:digest(P/name) for name in ['prepare.py','predict.py','selection_freeze.json','protocol.json','dependencies.json','goal_inventory.csv.gz','participants.csv.gz','identity_bridge.csv.gz','team_goal_coverage.csv.gz']},raw_source_proofs=raw_proofs,assist_rule_predictions=False)
    freeze_write(P/'prediction_freeze.json',(json.dumps(freeze,indent=2)+'\n').encode());print(dict(fixtures=len(plan),goals=len(additions),participants=len(identities),teams=len(cover)))
if __name__=='__main__':main()
