import json
ADMIN={20,17,18,19,34,40}
BLOCK={43,84,75,76,4,16}
def q(v):return json.loads(v) if isinstance(v,str) and v.strip() else {}
def classify(goal,events,teams,mapping,identities):
 if set(q(goal['qualifier_json'])) & {'9','26','28'} or len(teams)!=2:return []
 team=goal['team_id']
 if team not in teams:return []
 ep=events[events.period_id.eq(goal['period_id']) & events.clock.between(goal['clock']-60,goal['clock'])]
 passes=ep[ep.type_id.eq(61)&ep.team_id.eq(team)&ep.player_id.ne(goal['player_id'])&ep.clock.lt(goal['clock'])]
 if passes.empty:return []
 last=passes[passes.clock.eq(passes.clock.max())]
 if len(last)!=1:return []
 b=last.iloc[0]
 if identities.get((goal['match_id'],team,b.player_id),0)!=1:return []
 tail=ep[ep.clock.ge(b.clock)&ep.event_id.ne(goal['event_id'])]
 if tail.type_id.isin(BLOCK).any() or tail.type_id.isna().any():return []
 non=tail[~tail.type_id.isin(ADMIN)]
 if non[['team_id','player_id']].isna().any().any():return []
 actors=set(non.loc[non.team_id.eq(team),'player_id'])|{b.player_id};actors.discard(goal['player_id'])
 if any(identities.get((goal['match_id'],team,x),0)!=1 for x in actors):return []
 return [dict(kind='explicit_attacking_ball_touch_bound',candidates=sorted(actors),anchor_event_ids=[int(b.event_id)],scoring_team_id=team)]
