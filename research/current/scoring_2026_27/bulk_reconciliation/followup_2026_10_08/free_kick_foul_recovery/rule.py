"""Certify an actual direct ordinary free-kick foul pair, never context alone."""
import json
ADMIN={17,18,19,20,21,24,25,27,28,34,36,40,65,70,71,75,76}
def q(value):
    try:obj=json.loads(value) if isinstance(value,str) and value.strip() else None
    except (ValueError,TypeError):return None
    return obj if isinstance(obj,dict) else None
def classify(goal,events,identities):
    gq=q(goal['qualifier_json']);team=goal['team_id'];scorer=goal['player_id']
    if gq is None or '26' not in gq or set(gq)&{'9','28','29','154','55'}:return None
    if gq.get('280') not in [None,'FREE_KICK_WON'] or gq.get('282') not in [None,team]:return None
    if identities.get((goal['match_id'],team,scorer),0)!=1:return None
    e=events[events.period_id.eq(goal['period_id'])&events.clock.between(goal['clock']-600,goal['clock'])].copy()
    e['q']=e.qualifier_json.map(q)
    fouls=e[e.type_id.eq(4)&e.clock.lt(goal['clock'])]
    fouls=fouls[fouls.q.map(lambda x:x is not None and {'13','152'}<=set(x) and not set(x)&{'9','10','241'})]
    wins=fouls[fouls.team_id.eq(team)&fouls.outcome.eq(1)]
    candidates=[]
    for w in wins.itertuples():
        losses=fouls[fouls.team_id.ne(team)&fouls.outcome.eq(0)&fouls.clock.sub(w.clock).abs().le(2)]
        losses=losses[(losses.x.add(w.x).sub(100).abs().lt(.11))&(losses.y.add(w.y).sub(100).abs().lt(.11))]
        if len(losses)!=1:continue
        loss=losses.iloc[0]
        if not all(str(x.get('233','')).isdigit() for x in [w.q,loss.q]):continue
        if identities.get((goal['match_id'],team,w.player_id),0)!=1:continue
        if gq.get('281') not in [None,w.player_id]:continue
        mid=e[e.clock.between(min(w.clock,loss.clock),goal['clock'])&~e.event_id.isin([w.event_id,loss.event_id,goal['event_id']])]
        if not mid.type_id.isin(ADMIN).all():continue
        self_won=w.player_id==scorer
        candidates.append(dict(status='no_assist' if self_won else 'awarded',recipient_player_id='' if self_won else w.player_id,
            foul_winner=w.player_id,kind='self_won_free_kick' if self_won else 'ordinary_foul_free_kick',
            foul_event_id=int(w.event_id),committed_event_id=int(loss.event_id),scoring_team_id=team))
    return candidates[0] if len(candidates)==1 else None
