"""Direct converted penalty linked to a uniquely paired ordinary foul.
Handball, missing taker links, ambiguous pairs and intervening play abstain.
"""
import json
ADMIN={17,18,19,20,21,24,25,27,28,34,36,40,65,70,71,75,76}
def q(s):return json.loads(s) if isinstance(s,str) and s.strip() else {}
def classify(goal,events,identities):
 gq=q(goal['qualifier_json']);team=goal['team_id'];scorer=goal['player_id']
 if '9' not in gq or '28' in gq:return None
 e=events[events.period_id.eq(goal['period_id'])&events.clock.between(goal['clock']-600,goal['clock'])]
 f=e[e.type_id.eq(4)&e.clock.lt(goal['clock'])];f=f[f.qualifier_json.map(lambda s:{'9','13'}<=set(q(s)) and '10' not in q(s))]
 wins=f[f.team_id.eq(team)&f.outcome.eq(1)];wins=wins[wins.qualifier_json.map(lambda s:q(s).get('348')==scorer)]
 if len(wins)!=1:return None
 w=wins.iloc[0];losses=f[f.team_id.ne(team)&f.outcome.eq(0)&f.clock.sub(w.clock).abs().le(2)];losses=losses[(losses.x.add(w.x).sub(100).abs().lt(.11))&(losses.y.add(w.y).sub(100).abs().lt(.11))]
 if len(losses)!=1:return None
 l=losses.iloc[0]
 if any(not str(q(r.qualifier_json).get('233','')).isdigit() for r in [w,l]):return None
 if identities.get((goal['match_id'],team,w.player_id),0)!=1 or identities.get((goal['match_id'],team,scorer),0)!=1:return None
 mid=e[e.clock.between(min(w.clock,l.clock),goal['clock'])&~e.event_id.isin([w.event_id,l.event_id,goal['event_id']])]
 # No restart, another foul/shot or coverage gap is accepted as an administrative row.
 safe=mid.type_id.isin(ADMIN)|(mid.type_id.eq(58)&mid.qualifier_json.map(lambda s:'9' in q(s))&mid.team_id.ne(team)&mid.clock.eq(goal['clock']))
 if not safe.all():return None
 # Do not contradict any explicit source fantasy recipient or route.
 if gq.get('280') not in [None,'PENALTY_WON']:return None
 if gq.get('281') not in [None,w.player_id]:return None
 self_won=w.player_id==scorer
 return dict(status='no_assist' if self_won else 'awarded',recipient_player_id='' if self_won else w.player_id,foul_winner=w.player_id,kind='self_won_penalty' if self_won else 'ordinary_foul_penalty',foul_event_id=int(w.event_id),committed_event_id=int(l.event_id),scoring_team_id=team)
