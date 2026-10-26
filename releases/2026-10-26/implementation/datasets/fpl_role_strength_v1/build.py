"""Causal descriptive role and strength context. No forecasts are fitted."""
import collections,itertools
from common import *
C=json.loads((P/'contract.json').read_text())
NATIVE=R/'reports/season_split_base_2026_10_25/complete_2026-27_gw.csv.gz'
NATIVE_AUDIT=NATIVE.with_name('complete_live_data_audit.json')
FIELDS=['season','round','fixture','code','club_code','opponent_club_code','historical_team','was_home','fixture_kickoff_time','observation_available_after_proxy','av_forecast_at','history_eligible','native_minutes','native_starts','starts_quality','team_h_score','team_a_score']
def key(r):return r['season'],num(r['fixture']),num(r['code'])
def role(r):
 m=number(r['native_minutes']);s=number(r['native_starts'])
 valid=r['start_qualified'] and m is not None and 0<=m<=120 and s in [0,1]
 return ('start' if s==1 else 'sub' if m>0 else 'none') if valid else 'unknown'
def slim_rows():
 audit=json.loads(NATIVE_AUDIT.read_text());assert audit['passed'] and sha(NATIVE)==audit['complete_native_sha256']
 native={key(r):r for r in read(NATIVE)};rows=[]
 for r in read(OLD/'player_matches.csv.xz'):
  x={k:r[k] for k in FIELDS};x['start_qualified']=r['starts_quality'] in START_QUALITY;x['start_basis']=r['starts_quality'] or 'unknown'
  if r['season']=='2026-27':
   n=native[key(r)]
   assert all(number(n[k])==number(r[k]) for k in ['native_starts','native_minutes'])
   x['start_qualified']=True;x['start_basis']='verified_archived_complete_official_2026_27'
  x['role']=role(x);rows.append(x)
 assert len(rows)==190124 and len({key(r) for r in rows})==190124
 return rows
def role_context(history,prior,at,club):
 # Inputs have already passed the strict availability and history eligibility gates.
 out=dict(pr_forecast_at=at.isoformat(),pr_history_matches=len(history),pr_history_missing=not history,pr_history_latest_available=history[-1]['observation_available_after_proxy'] if history else None,pr_last_role=history[-1]['role'] if history else None,pr_last_club_code=num(history[-1]['club_code']) if history else None,pr_last_club_differs=bool(history and num(history[-1]['club_code'])!=club),pr_availability_clock='kickoff_plus_24h_proxy',pr_strict_historical_qualified=False)
 for w in C['role_windows']:
  a=history[-w:];known=[r for r in a if r['role']!='unknown'];m=[number(r['native_minutes']) for r in a if number(r['native_minutes']) is not None];start=[number(r['native_minutes']) for r in a if r['role']=='start'];sub=[number(r['native_minutes']) for r in a if r['role']=='sub'];b='pr_last'+str(w)+'_'
  out.update({b+'matches':len(a),b+'window_complete':len(a)==w,b+'role_known':len(known),b+'role_unknown':len(a)-len(known),b+'starts':len(start),b+'sub_appearances':len(sub),b+'no_minutes':sum(r['role']=='none' for r in a),b+'start_rate':len(start)/len(known) if known else None,b+'sub_rate':len(sub)/len(known) if known else None,b+'no_minutes_rate':sum(r['role']=='none' for r in a)/len(known) if known else None,b+'minutes_mean':avg(m),b+'minutes_given_start':avg(start),b+'minutes_given_sub':avg(sub),b+'sixty_given_start':avg([int(v>=60) for v in start]),b+'sixty_given_sub':avg([int(v>=60) for v in sub])})
 for label in ['start','sub','none']:
  streak=0
  for r in reversed(history):
   if r['role']!=label:break
   streak+=1
  matches=[r for r in history if r['role']==label]
  out['pr_consecutive_'+label]=streak if history and history[-1]['role']!='unknown' else None
  out['pr_days_since_'+label]=(at-dt(matches[-1]['fixture_kickoff_time'])).total_seconds()/86400 if matches else None
 out['pr_start_rate_delta_3_10']=(out['pr_last3_start_rate']-out['pr_last10_start_rate']) if out['pr_last3_start_rate'] is not None and out['pr_last10_start_rate'] is not None else None
 out['pr_minutes_delta_3_10']=(out['pr_last3_minutes_mean']-out['pr_last10_minutes_mean']) if out['pr_last3_minutes_mean'] is not None and out['pr_last10_minutes_mean'] is not None else None
 out['pr_last_transition']=(history[-2]['role']+'->'+history[-1]['role']) if len(history)>=2 else None
 out['pr_latest_appearance_preceded_by_no_minutes']=history[-2]['role']=='none' if len(history)>=2 and history[-1]['role'] in ['start','sub'] and history[-2]['role']!='unknown' else None
 known=[r for r in prior if r['role']!='unknown'];starts=[number(r['native_minutes']) for r in known if r['role']=='start'];subs=[number(r['native_minutes']) for r in known if r['role']=='sub']
 out.update(pr_previous_season_matches=len(prior),pr_previous_season_role_known=len(known),pr_previous_season_start_rate=len(starts)/len(known) if known else None,pr_previous_season_minutes_given_start=avg(starts),pr_previous_season_minutes_given_sub=avg(subs))
 return out
def fixtures(rows):
 groups=collections.defaultdict(list)
 for r in rows:groups[(r['season'],num(r['fixture']))].append(r)
 result=[]
 for (s,f),a in sorted(groups.items()):
  assert len({r['fixture_kickoff_time'] for r in a})==1 and len({r['observation_available_after_proxy'] for r in a})==1
  assert len({(number(r['team_h_score']),number(r['team_a_score'])) for r in a})==1
  sides={}
  for home in [True,False]:
   side=[r for r in a if truth(r['was_home'])==home];clubs={num(r['club_code']) for r in side};assert len(clubs)==1
   club=next(iter(clubs));sides[home]=club
   assert len({r['historical_team'] for r in side})==1
  assert sides[True]!=sides[False]
  for r in a:assert num(r['opponent_club_code'])==sides[not truth(r['was_home'])]
  hg=number(a[0]['team_h_score']);ag=number(a[0]['team_a_score']);assert hg is not None and ag is not None and hg>=0 and ag>=0 and hg.is_integer() and ag.is_integer()
  result.append(dict(season=s,fixture=f,home=sides[True],away=sides[False],home_goals=hg,away_goals=ag,kickoff=a[0]['fixture_kickoff_time'],available=a[0]['observation_available_after_proxy']))
 assert len(result)==2730
 return result
class Strength:
 def __init__(self):self.teams=collections.defaultdict(list);self.games=[]
 def baseline(self,home):
  vals=[g['home_goals' if home else 'away_goals'] for g in self.games];prior=C['league_prior_home_goals' if home else 'league_prior_away_goals'];return (C['league_prior_matches']*prior+sum(vals))/(C['league_prior_matches']+len(vals))
 def state(self,club):
  allrows=self.teams[club];a=allrows[-C['strength_window']:];weights=[C['strength_recency_decay']**i for i in reversed(range(len(a)))];den=C['strength_prior_weight']+sum(weights)
  attack=(C['strength_prior_weight']+sum(w*r['adjusted_for'] for w,r in zip(weights,a)))/den
  concede=(C['strength_prior_weight']+sum(w*r['adjusted_against'] for w,r in zip(weights,a)))/den
  return dict(matches=len(allrows),window_matches=len(a),prior_only=not a,attack_index=attack,concession_index=concede,goals_for_mean=avg([r['gf'] for r in a]),goals_against_mean=avg([r['ga'] for r in a]),latest_available=allrows[-1]['available'] if a else None)
 def pre(self,g):
  h=self.state(g['home']);a=self.state(g['away']);bh=self.baseline(True);ba=self.baseline(False)
  return dict(home_for_den=bh*a['concession_index'],home_against_den=ba*a['attack_index'],away_for_den=ba*h['concession_index'],away_against_den=bh*h['attack_index'],prematch_league_home=bh,prematch_league_away=ba,home_opponent_attack=a['attack_index'],home_opponent_concession=a['concession_index'],away_opponent_attack=h['attack_index'],away_opponent_concession=h['concession_index'])
 def add(self,g,pre):
  for home in [True,False]:
   b='home' if home else 'away';gf=g[b+'_goals'];ga=g['away_goals' if home else 'home_goals']
   self.teams[g[b]].append(dict(fixture=g['fixture'],gf=gf,ga=ga,adjusted_for=gf/pre[b+'_for_den'],adjusted_against=ga/pre[b+'_against_den'],available=g['available']))
  self.games.append(g)
 def context(self,own,opp,home,at):
  out=dict(ds_forecast_at=at.isoformat(),ds_season_matches=len(self.games),ds_league_home_goal_rate=self.baseline(True),ds_league_away_goal_rate=self.baseline(False),ds_method='opponent_adjusted_goals_fixed_priors_v1',ds_xg_used=False,ds_is_calibrated_forecast=False,ds_strict_historical_qualified=False)
  for prefix,club in [('ds_team_',own),('ds_opponent_',opp)]:out.update({prefix+k:v for k,v in self.state(club).items()})
  out['ds_match_attack_index']=out['ds_team_attack_index']*out['ds_opponent_concession_index'];out['ds_match_concession_index']=out['ds_team_concession_index']*out['ds_opponent_attack_index']
  for prefix,club,venue in [('ds_team_venue_',own,home),('ds_opponent_venue_',opp,not home)]:
   a=[g for g in self.games if (g['home'] if venue else g['away'])==club][-10:]
   out.update({prefix+'matches':len(a),prefix+'goals_for_mean':avg([g['home_goals' if venue else 'away_goals'] for g in a]),prefix+'goals_against_mean':avg([g['away_goals' if venue else 'home_goals'] for g in a])})
  return out
def strength_context(games,origins):
 contexts={};audit=[]
 for s in sorted({g['season'] for g in games}):
  state=Strength();events=collections.defaultdict(lambda:dict(kick=[],release=[],query=[]))
  for g in games:
   if g['season']==s:events[dt(g['kickoff'])]['kick'].append(g);events[dt(g['available'])]['release'].append(g)
  for o in origins:
   if o[0]==s:events[dt(o[2])]['query'].append(o)
  pre={}
  for at,e in sorted(events.items()):
   # All simultaneous queries/kickoffs read the same state before any release.
   for o in e['query']:
    _,f,_,club,opp,home=o;contexts[(s,f,o[2],club)]=state.context(club,opp,home,at)
   for g in e['kick']:pre[g['fixture']]=state.pre(g)
   for g in e['release']:
    p=pre[g['fixture']];audit.append(dict(g,**p));state.add(g,p)
 return contexts,audit
def main():
 deps=[OLD/'player_matches.csv.xz',OLD/'manifest.json',NATIVE,NATIVE_AUDIT,P/'contract.json',P/'common.py',P/'build.py',R/'datasets/ACTIVE.json']
 hashes={str(p.relative_to(R)):sha(p) for p in deps};rows=slim_rows();games=fixtures(rows)
 origins={(r['season'],num(r['fixture']),r['av_forecast_at'],num(r['club_code']),num(r['opponent_club_code']),truth(r['was_home'])) for r in rows};sc,gameaudit=strength_context(games,origins)
 histories=collections.defaultdict(list)
 for r in rows:
  if truth(r['history_eligible']):histories[(r['season'],num(r['code']))].append(r)
 for a in histories.values():a.sort(key=lambda r:(dt(r['fixture_kickoff_time']),int(float(r['fixture']))))
 contexts={};cache={};coverage=collections.defaultdict(collections.Counter)
 for r in rows:
  s=r['season'];code=num(r['code']);at=dt(r['av_forecast_at']);club=num(r['club_code']);k=(s,r['round'],code)
  if k not in cache:
   a=[h for h in histories[(s,code)] if dt(h['observation_available_after_proxy'])<at];year=int(s[:4])-1;previous=f'{year}-{str(year+1)[-2:]}'
   prior=[h for h in histories[(previous,code)] if dt(h['observation_available_after_proxy'])<at];cache[k]=role_context(a,prior,at,club)
  c=cache[k];assert c['pr_forecast_at']==at.isoformat()
  context=dict(c,**sc[(s,num(r['fixture']),r['av_forecast_at'],club)]);contexts[key(r)]=context
  coverage[s]['master_rows']+=1;coverage[s]['rows_with_role_history']+=bool(c['pr_history_matches']);coverage[s]['rows_with_5_match_role_history']+=c['pr_last5_window_complete'];coverage[s]['rows_with_team_strength_history']+=not context['ds_team_prior_only'];coverage[s]['rows_with_opponent_strength_history']+=not context['ds_opponent_prior_only']
 write('player_history_audit.csv.gz',rows);write('fixture_strength_audit.csv',gameaudit)
 write('player_match_context.csv.xz',(dict(season=r['season'],fixture=num(r['fixture']),code=num(r['code']),**contexts[key(r)]) for r in rows))
 write('player_round_role_context.csv.xz',(dict(season=k[0],round=k[1],code=k[2],**c) for k,c in cache.items()))
 OUT.mkdir(exist_ok=True)
 with lzma.open(OUT/'player_matches.csv.xz','wt',newline='',preset=3) as f:
  writer=None
  for r in read(OLD/'player_matches.csv.xz'):
   merged=dict(r,**contexts[key(r)])
   if writer is None:writer=csv.DictWriter(f,fieldnames=list(merged));writer.writeheader()
   writer.writerow(merged)
 write('coverage.csv',(dict(season=s,**c) for s,c in sorted(coverage.items())))
 dump(P/'input_hashes.json',hashes);dump(P/'summary.json',dict(master_rows=len(rows),fixtures=len(games),player_round_role_rows=len(cache),role_columns=list(next(iter(cache.values()))),strength_columns=[k for k in next(iter(contexts.values())) if k.startswith('ds_')],coverage={s:dict(c) for s,c in coverage.items()},qualified_role_rows=sum(r['role']!='unknown' for r in rows),unknown_role_rows=sum(r['role']=='unknown' for r in rows),models_fitted=0))
 for name,h in hashes.items():assert sha(R/name)==h,name
 print(json.dumps(dict(built=True,rows=len(rows),role_columns=len(next(iter(cache.values()))),strength_columns=sum(k.startswith('ds_') for k in next(iter(contexts.values())))),indent=2),flush=True)
if __name__=='__main__':main()
