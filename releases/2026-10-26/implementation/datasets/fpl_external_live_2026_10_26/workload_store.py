"""Generalized copy of the audited v1 club-workload Store; season_start is explicit."""
import bisect,collections
from datetime import datetime,timedelta,timezone
WINDOWS=[3,7,14,28]
def stamp(t):return t.isoformat() if t is not None else ''
def rounded(x):return round(x,4) if x is not None else None

class Store:
 def __init__(self,pl,cup,pl_fixtures,cup_fixtures,raw_rosters,identity):
  self.pl=collections.defaultdict(list);self.cup=collections.defaultdict(list)
  for e in pl:self.pl[e['code']].append(e)
  for e in cup:self.cup[e['code']].append(e)
  for groups in [self.pl,self.cup]:
   for code,events in groups.items():events.sort(key=lambda e:e['available'])
  self.pl_times={k:[e['available'] for e in v] for k,v in self.pl.items()}
  self.cup_times={k:[e['available'] for e in v] for k,v in self.cup.items()}
  self.pl_fixtures=pl_fixtures;self.cup_fixtures=cup_fixtures
  self.raw_rosters=raw_rosters;self.identity=identity
 def prior(self,groups,times,code,at):
  z=groups.get(code,[]);return z[:bisect.bisect_left(times.get(code,[]),at)]
 def calculate(self,code,at):
  pl=self.prior(self.pl,self.pl_times,code,at);cup=self.prior(self.cup,self.cup_times,code,at)
  observed=pl+cup
  last=max(observed,key=lambda e:e['kickoff']) if observed else None
  team=last['team'] if last and last['kickoff']>=self.season_start else None
  out={'wl_forecast_at':stamp(at),'wl_data_role':'workload_context',
   'wl_clock':'round_first_actual_kickoff_minus_90m;stats_kickoff_plus_24h',
   'wl_historical_deadline_qualified':False,'wl_internationals_covered':False,'wl_friendlies_covered':False,
   'wl_last_observed_club':team,'wl_club_known':team is not None,
   'wl_latest_input_available_at':stamp(max((e['available'] for e in observed),default=None)),
   'wl_latest_input_kickoff':stamp(max((e['kickoff'] for e in observed),default=None))}
  for label,events in [('pl',pl),('external',cup),('observed_scoped',observed)]:
   played=[e for e in events if e['minutes']>0]
   appearance=max(played,key=lambda e:e['kickoff']) if played else None
   out[f'wl_hours_since_last_{label}_appearance_end_proxy']=rounded((at-appearance['end']).total_seconds()/3600) if appearance else None
   out[f'wl_last_{label}_appearance_minutes']=appearance['minutes'] if appearance else None
   out[f'wl_last_{label}_appearance_competition']=appearance['competition'] if appearance else None
  out['wl_rest_may_overstate_due_to_missing_matches']=True
  out['wl_match_end_is_proxy']=True
  last_pl=max(pl,key=lambda e:e['kickoff']) if pl else None
  out['wl_last_pl_role']=('starter' if last_pl['starts']==1 else ('substitute' if last_pl['minutes']>0 else 'did_not_play')) if last_pl else 'unknown'
  out['wl_last_pl_observation_minutes']=last_pl['minutes'] if last_pl else None
  external_past=[f for f in self.cup_fixtures if team in f['teams'] and f['kickoff']<at] if team else []
  last_club_cup=max(external_past,key=lambda f:f['kickoff']) if external_past else None
  if last_club_cup is None:out['wl_last_external_role']='no_prior_club_fixture_or_unknown_club'
  elif last_club_cup['available']>=at:out['wl_last_external_role']='statistics_not_yet_available'
  else:
   p=next((e for e in cup if e['key']==last_club_cup['key']),None)
   if p:out['wl_last_external_role']='starter' if p['starts']==1 else ('substitute' if p['minutes']>0 else 'unused_bench')
   else:out['wl_last_external_role']='not_in_squad_verified' if self.absence_verified(code,team,last_club_cup,at) else 'unknown_identity_or_squad'
  last_external_player=next((e for e in cup if last_club_cup and e['key']==last_club_cup['key']),None)
  out['wl_last_external_fixture_kickoff']=stamp(last_club_cup['kickoff']) if last_club_cup else ''
  out['wl_last_external_fixture_minutes']=last_external_player['minutes'] if last_external_player else (0 if out['wl_last_external_role']=='not_in_squad_verified' else None)
  for days in WINDOWS:
   start=at-timedelta(days=days)
   ps=[e for e in pl if start<=e['kickoff']<at];cs=[e for e in cup if start<=e['kickoff']<at]
   relevant=[e for e in observed if start<=e['kickoff']<at]
   anchor=max((e for e in observed if e['kickoff']<start),key=lambda e:e['kickoff'],default=None)
   clubs={e['team'] for e in relevant}
   if anchor:clubs.add(anchor['team'])
   stable=len(clubs)<=1
   out[f'wl_club_context_stable_{days}d']=stable
   past_pl=[f for f in self.pl_fixtures if start<=f['kickoff']<at]
   past_cup=[f for f in self.cup_fixtures if start<=f['kickoff']<at]
   pexpected=[f for f in past_pl if team in f['teams']] if team else []
   cexpected=[f for f in past_cup if team in f['teams']] if team else []
   pmap={e['key']:e for e in ps};cmap={e['key']:e for e in cs}
   pc=not past_pl or bool(team and stable and all(f['available']<at and f['key'] in pmap for f in pexpected))
   cc=not past_cup or bool(team and stable and all(f['available']<at and
       (f['key'] in cmap or self.absence_verified(code,team,f,at)) for f in cexpected))
   # No appearances on an unknown team cannot establish complete coverage.
   out[f'wl_pl_coverage_complete_{days}d']=pc
   out[f'wl_external_coverage_complete_{days}d']=cc
   out[f'wl_pl_missing_or_pending_matches_{days}d']=sum(f['available']>=at or f['key'] not in pmap for f in pexpected) if team else None
   out[f'wl_external_missing_or_pending_matches_{days}d']=sum(f['available']>=at or (f['key'] not in cmap and not self.absence_verified(code,team,f,at)) for f in cexpected) if team else None
   out[f'wl_external_verified_not_in_squad_{days}d']=sum(f['available']<at and f['key'] not in cmap and self.absence_verified(code,team,f,at) for f in cexpected) if team else None
   for label,events,complete in [('pl',ps,pc),('external',cs,cc)]:
    minutes=sum(e['minutes'] for e in events);appearances=sum(e['minutes']>0 for e in events);starts=sum(e['starts'] or 0 for e in events)
    out[f'wl_{label}_observed_rows_{days}d']=len(events)
    for field,value in [('minutes',minutes),('appearances',appearances),('starts',starts)]:
     out[f'wl_{label}_{field}_lower_bound_{days}d']=value
     out[f'wl_{label}_{field}_{days}d']=value if complete and (field!='starts' or all(e['starts'] is not None for e in events)) else None
   for field in ['minutes','appearances','starts']:
    out[f'wl_scoped_{field}_lower_bound_{days}d']=out[f'wl_pl_{field}_lower_bound_{days}d']+out[f'wl_external_{field}_lower_bound_{days}d']
    a,b=out[f'wl_pl_{field}_{days}d'],out[f'wl_external_{field}_{days}d']
    out[f'wl_scoped_{field}_{days}d']=a+b if a is not None and b is not None else None
   out[f'wl_external_extra_time_match_appearances_{days}d']=sum(e['minutes']>0 and e['extra_time'] for e in cs) if cc else None
   out[f'wl_external_90plus_appearances_{days}d']=sum(e['minutes']>=90 for e in cs) if cc else None
  out['wl_external_played_within_72h']=True if any(e['minutes']>0 and e['end']>=at-timedelta(hours=72) for e in cup) else (False if out['wl_external_coverage_complete_7d'] else None)
  out['wl_scoped_rest_hours']=out['wl_hours_since_last_observed_scoped_appearance_end_proxy'] if out['wl_pl_coverage_complete_28d'] and out['wl_external_coverage_complete_28d'] and any(e['minutes']>0 and e['kickoff']>=at-timedelta(days=28) for e in observed) else None
  return out
 def absence_verified(self,code,team,fixture,at):
  prior=self.prior(self.cup,self.cup_times,code,at)
  identities={e['espn_player_id'] for e in prior}
  ids=self.raw_rosters.get((fixture['key'],team))
  return bool(len(identities)==1 and ids is not None and not identities&ids)

