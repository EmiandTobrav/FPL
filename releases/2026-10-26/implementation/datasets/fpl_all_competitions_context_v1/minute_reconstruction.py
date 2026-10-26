"""Audited interval reconstruction; a VAR review is not an actual red card."""
from common import cup
minute=cup.minute

def reconstruct(roster,events,length):
 players={p['athlete']['id']:p for p in roster};issues=[]
 start={pid:0 for pid,p in players.items() if p.get('starter')}
 end={};red={};subin=set();subout=set()
 if sum(p.get('starter',False) for p in roster)!=11:issues.append('not_11_starters')
 for e in events:
  kind=e['type']['type'];ps=[p['athlete']['id'] for p in e.get('participants',[])]
  if kind=='substitution':
   if len(ps)<2:issues.append('missing_substitution_participants');continue
   incoming,outgoing=ps[:2];m=minute(e['clock'])
   if incoming not in players or outgoing not in players or m is None:
    issues.append('incomplete_substitution_identity_or_clock');continue
   if outgoing not in start or outgoing in end or incoming in start:issues.append('invalid_active_player_substitution')
   start[incoming]=m;end[outgoing]=m;subin.add(incoming);subout.add(outgoing)
  elif kind=='red-card':
   if ps and ps[0] in players and ps[0] in start and ps[0] not in end:
    m=minute(e['clock'])
    if m is None:issues.append('missing_red_card_clock')
    else:end[ps[0]]=m;red[ps[0]]=m
 for pid,p in players.items():
  if bool(p.get('subbedIn'))!=(pid in subin):issues.append('roster_subbed_in_conflict')
  if bool(p.get('subbedOut'))!=(pid in subout):issues.append('roster_subbed_out_conflict')
 values={pid:(max(0,min(length,end.get(pid,length))-min(length,start[pid])) if pid in start else 0)
         for pid in players}
 expected=11*length-sum(length-min(length,m) for m in red.values())
 if sum(values.values())!=expected:issues.append('team_minute_conservation')
 for pid in players:
  if pid in end and end[pid]<start.get(pid,0):issues.append('negative_interval')
 return values,sorted(set(issues)),expected

