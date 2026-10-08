"""Conservative actor sets after an explicit goal-linked source certificate.
Never awards an assist. Additional attacking actors expand, never replace, the set.
"""
import json
ADMIN={20,51,58,83}
ACTION_TYPES={'ATTEMPT_SAVED':{15},'BLOCKED_SHOT':{15},'POST':{14},'PASS_LOST':{1},'OWN_GOAL':{1,13,14,15,61}}
def q(v):return json.loads(v) if isinstance(v,str) and v.strip() else {}
def tail_candidates(mid,team,anchor):
 non=mid[~mid.type_id.isin(ADMIN)]
 if non[['type_id','team_id','player_id']].isna().any().any():return None
 return {anchor}|set(non.loc[non.team_id.eq(team),'player_id'])
def classify(goal,events,teams,mapping,identities):
 qs=q(goal['qualifier_json']);own='28' in qs
 if len(teams)!=2 or goal['team_id'] not in teams or set(qs)&{'9','26'}:return []
 team=next(t for t in teams if t!=goal['team_id']) if own else goal['team_id'];ep=events[events.period_id.eq(goal['period_id'])];certs=[]
 if not own and {'29','55'}<=set(qs):
  ps=ep[ep.team_id.eq(team)&ep.type_id.eq(1)&ep.outcome.eq(1)&ep.player_id.ne(goal['player_id'])&ep.clock.between(goal['clock']-20,goal['clock'],inclusive='left')]
  ps=ps[ps.qualifier_json.map(lambda x:'210' in q(x) and q(x)['210'] in [None,16,'16'])]
  if len(ps)==1:certs.append(('pass210_actor_set',ps.iloc[0]))
 kind=qs.get('280');linked=qs.get('281');raw=qs.get('282');mapped=mapping.get((goal['season'],int(raw))) if isinstance(raw,str) and raw.isdigit() else raw
 if kind in ACTION_TYPES and linked and mapped==team and (own or linked!=goal['player_id']):
  cs=ep[ep.team_id.eq(team)&ep.player_id.eq(linked)&ep.type_id.isin(ACTION_TYPES[kind])&ep.clock.between(goal['clock']-20,goal['clock'],inclusive='left')]
  if len(cs):
   cs=cs[cs.clock.eq(cs.clock.max())]
   if len(cs)==1:certs.append(('linked_'+kind+'_actor_set',cs.iloc[0]))
 out=[]
 for kind,c in certs:
  mid=ep[ep.clock.between(c.clock,goal['clock'])&~ep.event_id.isin([c.event_id,goal['event_id']])];actors=tail_candidates(mid,team,c.player_id)
  if actors is None:continue
  # A normal goal scorer cannot assist their own goal. Do not remove an own-goal actor from the scoring side.
  if not own:actors.discard(goal['player_id'])
  if not actors or any(identities.get((goal['match_id'],team,a),0)!=1 for a in actors):continue
  out.append(dict(kind=kind,candidates=sorted(actors),anchor_event_id=int(c.event_id),scoring_team_id=team))
 # Preserve all plausible certificate/actor candidates, rather than choosing a preferred source.
 if not out:return []
 union=set().union(*(set(r['candidates']) for r in out))
 if len(union)<2:return []
 return [dict(kind='+'.join(sorted(r['kind'] for r in out)),candidates=sorted(union),anchor_event_ids=[r['anchor_event_id'] for r in out],scoring_team_id=team)]
