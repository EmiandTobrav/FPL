"""Project explicit counters and complete scoring inventories before validation."""
import importlib.util,json,math
from collections import Counter
import pandas as pd
from prepare import P,R,K,digest,save

spec=importlib.util.spec_from_file_location('native_identity',R/'scoring_2026_27/keeper_recovery/recover.py')
identity=importlib.util.module_from_spec(spec);spec.loader.exec_module(identity)

def count(v):
    return int(v) if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) and v>=0 and v==int(v) else None

def main():
    selection=json.loads((P/'selection_freeze.json').read_text())
    assert digest(P/'plan.csv')==selection['plan_sha256']
    assert digest(P/'inputs/native_players.csv.gz')==selection['native_players_sha256']
    assert digest(P/'protocol.json')==selection['protocol_sha256']
    sources=json.loads((P/'inputs/sources.json').read_text())
    for s in sources: assert digest(P/s['file'])==s['sha256']
    plan=pd.read_csv(P/'plan.csv').merge(pd.read_csv(P/'inputs/fixture_bridge.csv',dtype={'espn_event_id':str}),on=K[:2],validate='one_to_one')
    native=pd.read_csv(P/'inputs/native_players.csv.gz')
    players=[];goals=[];gates=[];summaries={}
    for r in plan.itertuples():
        d=json.loads((P/f'inputs/raw/summary_{r.espn_event_id}.json').read_bytes());summaries[(r.season,r.fixture)]=d
        assert str(d['header']['id'])==r.espn_event_id
        c=d['header']['competitions'][0];assert c['status']['type']['completed'] and c['date'][:10]==r.date
        sides={x['homeAway']:x for x in c['competitors']}
        for side,name,score in [('home',r.home,r.home_score),('away',r.away,r.away_score)]:
            assert identity.team(sides[side]['team']['displayName'])==identity.team(name)
            assert int(sides[side]['score'])==score
        n=native[native.season.eq(r.season)&native.fixture.eq(r.fixture)]
        for team in d.get('rosters',[]):
            club=identity.team(team['team']['displayName']);pool=n[n.historical_team.map(identity.team).eq(club)]
            for a in team.get('roster',[]):
                stats={x['name']:count(x.get('value')) for x in a.get('stats',[])}
                if len(stats)!=len(a.get('stats',[])) or stats.get('appearances')!=1:continue
                athlete=a['athlete'];pn=athlete.get('fullName',athlete.get('displayName',''))
                provider=dict(player_name=pn,first_name=pn.rsplit(' ',1)[0],last_name=athlete.get('lastName',pn.rsplit(' ',1)[-1]))
                hits=[(int(x.code),identity.name_match(x._asdict(),provider)) for x in pool.itertuples()]
                best=max([score for _,score in hits],default=0);codes=[code for code,score in hits if best>0 and score==best]
                if len(codes)!=1:continue
                code=codes[0];fp=pool[pool.code.eq(code)].iloc[0]
                players.append(dict(season=r.season,fixture=r.fixture,scope=r.scope,code=code,espn_player_id=str(athlete['id']),espn_team_id=str(team['team']['id']),source_name=pn,position=fp.position,native_goals=int(fp.goals_scored),native_own_goals=int(fp.own_goals),source_goals=stats.get('totalGoals'),source_own_goals=stats.get('ownGoals'),fouls_won=stats.get('foulsSuffered')))
        for e in d.get('keyEvents',[]):
            if not e.get('scoringPlay'):continue
            typ=e.get('type',{});sid=str(typ.get('id',''));kind=typ.get('type','');text=typ.get('text','')
            penalty=sid=='98' and kind=='penalty---scored' and text=='Penalty - Scored'
            ordinary=kind=='goal' or kind.startswith('goal---')
            own=kind=='own-goal' and text=='Own Goal'
            parts=e.get('participants',[])
            goals.append(dict(season=r.season,fixture=r.fixture,event_id=str(e['id']),espn_player_id=str(parts[0]['athlete']['id']) if parts else '',espn_team_id=str(e.get('team',{}).get('id','')),kind=kind,penalty=penalty,own_goal=own,recognized=bool((penalty or ordinary or own) and not e.get('shootout') and e.get('period',{}).get('number') in [1,2]),source_text=e.get('text','')))
    players=pd.DataFrame(players);goals=pd.DataFrame(goals)
    # Reject all ambiguous or inconsistent identities before any count output.
    bad=players.duplicated(K[:3],keep=False)|players.duplicated(K[:2]+['espn_player_id'],keep=False)
    bycode=players.groupby(['season','code']).espn_player_id.nunique();byid=players.groupby(['season','espn_player_id']).code.nunique()
    bad|=pd.Series([bycode[(r.season,r.code)]!=1 or byid[(r.season,r.espn_player_id)]!=1 for r in players.itertuples()],index=players.index)
    players=players[~bad].copy();pred=[]
    for x in players[players.fouls_won.notna()].itertuples():pred.append(dict(season=x.season,fixture=x.fixture,code=x.code,field='fouls_won',value=int(x.fouls_won),scope=x.scope,espn_player_id=x.espn_player_id,method='explicit_foulsSuffered'))
    for r in plan.itertuples():
        g=goals[goals.season.eq(r.season)&goals.fixture.eq(r.fixture)];p=players[players.season.eq(r.season)&players.fixture.eq(r.fixture)]
        n=native[native.season.eq(r.season)&native.fixture.eq(r.fixture)]
        why=[];mapping={x.espn_player_id:x for x in p.itertuples()}
        if len(g)!=r.home_score+r.away_score:why.append('goal_count')
        if g.event_id.duplicated().any() or not g.recognized.all():why.append('unknown_or_duplicate_scoring_type')
        if not set(g.espn_player_id)<=set(mapping):why.append('unresolved_scorer')
        goalcounts=Counter(g.loc[~g.own_goal,'espn_player_id']);owncounts=Counter(g.loc[g.own_goal,'espn_player_id'])
        if any(x.source_goals!=x.native_goals or x.source_own_goals!=x.native_own_goals or goalcounts[x.espn_player_id]!=x.native_goals or owncounts[x.espn_player_id]!=x.native_own_goals for x in p.itertuples()):why.append('native_scorer_vector')
        if int(n.goals_scored.sum()+n.own_goals.sum())!=len(g):why.append('native_goal_inventory')
        if int(p.native_goals.sum()+p.native_own_goals.sum())!=len(g):why.append('unmapped_native_scorer')
        # Native and source club identities also constrain goal beneficiaries.
        benef=Counter()
        for e in g.itertuples():
            if e.espn_player_id not in mapping:continue
            team_id=mapping[e.espn_player_id].espn_team_id
            if e.own_goal:
                others=[str(t['team']['id']) for t in summaries[(r.season,r.fixture)]['rosters'] if str(t['team']['id'])!=team_id]
                if len(others)!=1:why.append('own_goal_team');continue
                team_id=others[0]
            benef[team_id]+=1
        c=summaries[(r.season,r.fixture)]['header']['competitions'][0]
        if any(benef[str(t['team']['id'])]!=int(t['score']) for t in c['competitors']):why.append('team_goal_score')
        gates.append(dict(season=r.season,fixture=r.fixture,scope=r.scope,complete=not why,reasons=';'.join(sorted(set(why))),scoring_events=len(g),mapped_players=len(p)))
        if why:continue
        counts=Counter(g.loc[g.penalty,'espn_player_id'])
        for x in p.itertuples():pred.append(dict(season=x.season,fixture=x.fixture,code=x.code,field='penalty_goals',value=counts[x.espn_player_id],scope=x.scope,espn_player_id=x.espn_player_id,method='complete_typed_goal_inventory'))
    save(players,P/'players.csv.gz');save(goals,P/'goal_events.csv.gz');save(pd.DataFrame(gates),P/'fixture_gates.csv');save(pd.DataFrame(pred),P/'predictions.csv.gz')
    files=[P/n for n in ['protocol.json','prepare.py','collect.py','predict.py','plan.csv','selection_freeze.json','inputs/native_players.csv.gz','inputs/fixture_bridge.csv','inputs/sources.json','inputs/parent_CURRENT.json','players.csv.gz','goal_events.csv.gz','fixture_gates.csv','predictions.csv.gz']]
    record={'files':{str(f.relative_to(P)):digest(f) for f in files},'sources':sources}
    freeze=P/'prediction_freeze.json'
    if freeze.exists():assert json.loads(freeze.read_text())==record
    freeze.write_text(json.dumps(record,indent=2)+'\n');print(pd.DataFrame(pred).groupby(['scope','field']).size().to_dict());print(pd.DataFrame(gates).reasons.value_counts().to_dict())

if __name__=='__main__':main()
