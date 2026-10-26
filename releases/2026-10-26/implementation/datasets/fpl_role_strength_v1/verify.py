"""Independent source-preservation, as-of aggregation and strength replay checks."""
import collections,itertools,math
from common import *
from build import Strength,strength_context,role_context,role,C
def eq(a,b):
 if b is None:assert a=='',(a,b)
 elif isinstance(b,bool):assert a==str(b),(a,b)
 elif isinstance(b,(int,float)):assert math.isclose(float(a),b,rel_tol=1e-10,abs_tol=1e-10),(a,b)
 else:assert a==str(b),(a,b)
def state(club,prior):
 a=[g for g in prior if club in [g['home'],g['away']]][-10:];w=[.9**(len(a)-1-i) for i in range(len(a))];den=5+sum(w)
 gf=[];ga=[];af=[];aa=[]
 for g in a:
  b='home' if club==g['home'] else 'away';gf.append(float(g[b+'_goals']));ga.append(float(g['away_goals' if b=='home' else 'home_goals']));af.append(gf[-1]/float(g[b+'_for_den']));aa.append(ga[-1]/float(g[b+'_against_den']))
 return dict(matches=sum(club in [g['home'],g['away']] for g in prior),window_matches=len(a),prior_only=not a,attack_index=(5+sum(x*y for x,y in zip(w,af)))/den,concession_index=(5+sum(x*y for x,y in zip(w,aa)))/den,goals_for_mean=avg(gf),goals_against_mean=avg(ga),latest_available=a[-1]['available'] if a else None)
def baseline(prior,home):return (20*(1.5 if home else 1.2)+sum(float(g['home_goals' if home else 'away_goals']) for g in prior))/(20+len(prior))
def semantic_tests():
 tests=[]
 def checked(name,assertion):assert assertion,name;tests.append(name)
 def g(f,k,hg,ag,s='2020-21'):
  from datetime import timedelta
  return dict(season=s,fixture=str(f),home='1',away='2',home_goals=hg,away_goals=ag,kickoff=k,available=(dt(k)+timedelta(hours=24)).isoformat())
 first=g(1,'2020-09-01T12:00:00+00:00',3,0);second=g(2,'2020-09-02T12:00:00+00:00',0,5)
 origins=[('2020-21','target',at,'1','2',True) for at in ['2020-09-02T12:00:00+00:00','2020-09-02T12:00:01+00:00','2020-09-03T12:00:00+00:00']]
 result,audit=strength_context([first,second],origins);v=list(result.values())
 checked('exact availability excluded',v[0]['ds_team_matches']==0)
 checked('one second after availability included',v[1]['ds_team_matches']==1)
 checked('manual adjusted attack 7/6',abs(v[1]['ds_team_attack_index']-7/6)<1e-12)
 checked('manual concession 5/6',abs(v[1]['ds_team_concession_index']-5/6)<1e-12)
 checked('simultaneous kickoff cannot use released first result',audit[1]['home_for_den']==1.5)
 changed=dict(second,home_goals=30,away_goals=40);mutated,_=strength_context([first,changed],origins)
 checked('future and unreleased outcomes cannot alter any origin',result==mutated)
 third=g(3,'2021-09-01T12:00:00+00:00',2,2,'2021-22');origin=('2021-22','target','2021-09-01T11:00:00+00:00','1','2',True);r,_=strength_context([first,third],[origin]);checked('new season neutral reset',r[(origin[0],origin[1],origin[2],origin[3])]['ds_team_prior_only'])
 def player(m,s,q=True):return dict(native_minutes=str(m),native_starts=str(s),start_qualified=q)
 checked('short start remains start',role(player(12,1))=='start')
 checked('long substitute remains substitute',role(player(70,0))=='sub')
 checked('zero is not a bench label',role(player(0,0))=='none')
 checked('unqualified zero remains unknown',role(player(0,0,False))=='unknown')
 checked('invalid binary start excluded',role(player(90,2))=='unknown')
 sample=[]
 for i,(m,s) in enumerate([(90,1),(0,0),(15,0)]):sample.append(dict(player(m,s),role=role(player(m,s)),fixture_kickoff_time=f'2020-09-0{i+1}T12:00:00+00:00',observation_available_after_proxy=f'2020-09-0{i+2}T12:00:00+00:00',club_code='1'))
 c=role_context(sample,[],dt('2020-09-05T12:00:00+00:00'),'2')
 checked('conditional duration and correct known denominator',c['pr_last3_minutes_given_start']==90 and c['pr_last3_minutes_given_sub']==15 and c['pr_last3_start_rate']==1/3)
 checked('no padding limited history',c['pr_last10_matches']==3 and not c['pr_last10_window_complete'])
 checked('transfer history identified',c['pr_last_club_differs'])
 checked('return only describes observed zero',c['pr_latest_appearance_preceded_by_no_minutes'])
 return tests
def main():
 tests=semantic_tests();inputs=json.loads((P/'input_hashes.json').read_text())
 for name,h in inputs.items():assert sha(R/name)==h,name
 source=list(read(P/'player_history_audit.csv.gz'));index={(r['season'],num(r['fixture']),num(r['code'])):r for r in source};histories=collections.defaultdict(list)
 assert len(index)==len(source)==190124
 native={ (r['season'],num(r['fixture']),num(r['code'])):r for r in read(R/'reports/season_split_base_2026_10_25/complete_2026-27_gw.csv.gz')};team_starts=collections.Counter()
 for r in source:
  qualified=r['starts_quality'] in START_QUALITY
  if r['season']=='2026-27':
   n=native[(r['season'],num(r['fixture']),num(r['code']))];assert number(r['native_starts'])==number(n['native_starts']) and number(r['native_minutes'])==number(n['native_minutes']);qualified=True
  assert truth(r['start_qualified'])==qualified;team_starts[(r['season'],num(r['fixture']),num(r['club_code']))]+=number(r['native_starts'])
  m=number(r['native_minutes']);s=number(r['native_starts']);expected=('start' if s==1 else 'sub' if m>0 else 'none') if qualified and m is not None and 0<=m<=120 and s in [0,1] else 'unknown';assert r['role']==expected
  if truth(r['history_eligible']):histories[(r['season'],num(r['code']))].append(r)
 assert len(team_starts)==5460 and all(v==11 for v in team_starts.values())
 for a in histories.values():a.sort(key=lambda r:(dt(r['fixture_kickoff_time']),int(float(r['fixture']))))
 games=list(read(P/'fixture_strength_audit.csv'));assert len(games)==2730 and len({(g['season'],g['fixture']) for g in games})==2730
 byseason=collections.defaultdict(list)
 for g in games:byseason[g['season']].append(g)
 for a in byseason.values():a.sort(key=lambda g:(dt(g['available']),int(g['fixture'])))
 # Pre-match denominator independently reconstructed from only available past games.
 prechecks=0
 for g in games:
  prior=[p for p in byseason[g['season']] if dt(p['available'])<dt(g['kickoff'])];h=state(g['home'],prior);a=state(g['away'],prior);bh=baseline(prior,True);ba=baseline(prior,False)
  for name,value in dict(home_for_den=bh*a['concession_index'],home_against_den=ba*a['attack_index'],away_for_den=ba*h['concession_index'],away_against_den=bh*h['attack_index']).items():eq(g[name],value);prechecks+=1
 cached_roles={};cached_strength={};round_roles={};counts=collections.Counter();preserved=0;feature_checks=0;seen=set()
 context=iter(read(P/'player_match_context.csv.xz'))
 for original,new in itertools.zip_longest(read(OLD/'player_matches.csv.xz'),read(OUT/'player_matches.csv.xz')):
  assert original is not None and new is not None
  assert all(new[k]==v for k,v in original.items());k=(new['season'],num(new['fixture']),num(new['code']));assert k not in seen;seen.add(k)
  audit=index[k]
  for name in ['native_minutes','native_starts','history_eligible','club_code','opponent_club_code','av_forecast_at']:assert audit[name]==original[name]
  ctx=next(context);assert (ctx['season'],ctx['fixture'],ctx['code'])==k
  for name,v in ctx.items():assert new[name]==v
  s=new['season'];code=num(new['code']);at=dt(new['av_forecast_at']);club=num(new['club_code']);opp=num(new['opponent_club_code']);home=truth(new['was_home']);rk=s,new['round'],code
  if rk not in cached_roles:
   a=[h for h in histories[(s,code)] if dt(h['observation_available_after_proxy'])<at];values=dict(pr_history_matches=len(a),pr_history_missing=not a,pr_history_latest_available=a[-1]['observation_available_after_proxy'] if a else None,pr_last_role=a[-1]['role'] if a else None,pr_last_club_code=num(a[-1]['club_code']) if a else None,pr_last_club_differs=bool(a and num(a[-1]['club_code'])!=club))
   for w in [3,5,10]:
    b=a[-w:];valid=[h for h in b if h['role']!='unknown'];starts=[float(h['native_minutes']) for h in valid if h['role']=='start'];subs=[float(h['native_minutes']) for h in valid if h['role']=='sub'];none=sum(h['role']=='none' for h in valid);pre='pr_last'+str(w)+'_'
    values.update({pre+'matches':len(b),pre+'window_complete':len(b)==w,pre+'role_known':len(valid),pre+'role_unknown':len(b)-len(valid),pre+'starts':len(starts),pre+'sub_appearances':len(subs),pre+'no_minutes':none,pre+'start_rate':len(starts)/len(valid) if valid else None,pre+'sub_rate':len(subs)/len(valid) if valid else None,pre+'no_minutes_rate':none/len(valid) if valid else None,pre+'minutes_mean':avg([float(h['native_minutes']) for h in b]),pre+'minutes_given_start':avg(starts),pre+'minutes_given_sub':avg(subs),pre+'sixty_given_start':avg([v>=60 for v in starts]),pre+'sixty_given_sub':avg([v>=60 for v in subs])})
   for label in ['start','sub','none']:
    reverse=list(reversed(a));streak=next((i for i,h in enumerate(reverse) if h['role']!=label),len(reverse));matches=[h for h in a if h['role']==label]
    values['pr_consecutive_'+label]=streak if a and a[-1]['role']!='unknown' else None;values['pr_days_since_'+label]=(at-dt(matches[-1]['fixture_kickoff_time'])).total_seconds()/86400 if matches else None
   year=int(s[:4])-1;prior=[h for h in histories[(f'{year}-{str(year+1)[-2:]}',code)] if dt(h['observation_available_after_proxy'])<at];valid=[h for h in prior if h['role']!='unknown'];start=[float(h['native_minutes']) for h in valid if h['role']=='start'];sub=[float(h['native_minutes']) for h in valid if h['role']=='sub']
   values.update(pr_previous_season_matches=len(prior),pr_previous_season_role_known=len(valid),pr_previous_season_start_rate=len(start)/len(valid) if valid else None,pr_previous_season_minutes_given_start=avg(start),pr_previous_season_minutes_given_sub=avg(sub))
   values['pr_start_rate_delta_3_10']=values['pr_last3_start_rate']-values['pr_last10_start_rate'] if values['pr_last3_start_rate'] is not None else None;values['pr_minutes_delta_3_10']=values['pr_last3_minutes_mean']-values['pr_last10_minutes_mean'] if a else None
   values['pr_last_transition']=a[-2]['role']+'->'+a[-1]['role'] if len(a)>=2 else None;values['pr_latest_appearance_preceded_by_no_minutes']=a[-2]['role']=='none' if len(a)>=2 and a[-1]['role'] in ['start','sub'] and a[-2]['role']!='unknown' else None
   cached_roles[rk]=values
  for name,value in cached_roles[rk].items():eq(new[name],value);feature_checks+=1
  assert dt(new['pr_forecast_at'])==dt(new['ds_forecast_at'])==at
  sk=s,new['av_forecast_at'],club,opp,home
  if sk not in cached_strength:
   prior=[g for g in byseason[s] if dt(g['available'])<at];v=dict(ds_season_matches=len(prior),ds_league_home_goal_rate=baseline(prior,True),ds_league_away_goal_rate=baseline(prior,False))
   for prefix,c in [('ds_team_',club),('ds_opponent_',opp)]:v.update({prefix+n:x for n,x in state(c,prior).items()})
   v['ds_match_attack_index']=v['ds_team_attack_index']*v['ds_opponent_concession_index'];v['ds_match_concession_index']=v['ds_team_concession_index']*v['ds_opponent_attack_index']
   for prefix,c,venue in [('ds_team_venue_',club,home),('ds_opponent_venue_',opp,not home)]:
    a=[g for g in prior if (g['home'] if venue else g['away'])==c][-10:];v.update({prefix+'matches':len(a),prefix+'goals_for_mean':avg([float(g['home_goals' if venue else 'away_goals']) for g in a]),prefix+'goals_against_mean':avg([float(g['away_goals' if venue else 'home_goals']) for g in a])})
   cached_strength[sk]=v
  for name,value in cached_strength[sk].items():eq(new[name],value);feature_checks+=1
  assert new['pr_strict_historical_qualified']==new['ds_strict_historical_qualified']==new['ds_xg_used']==new['ds_is_calibrated_forecast']=='False'
  rr={k:v for k,v in new.items() if k.startswith('pr_')}
  if rk in round_roles:assert round_roles[rk]==rr
  else:round_roles[rk]=rr
  # Audit each physical result against original repeated score/team fields.
  g=next(g for g in byseason[s] if g['fixture']==num(new['fixture']))
  assert club==g['home' if home else 'away'] and opp==g['away' if home else 'home'];assert number(new['team_h_score'])==float(g['home_goals']) and number(new['team_a_score'])==float(g['away_goals'])
  assert dt(g['available'])==dt(new['observation_available_after_proxy']) and dt(g['kickoff'])==dt(new['fixture_kickoff_time'])
  counts[s]+=1;preserved+=1
 assert next(context,None) is None and preserved==190124
 roundcount=0
 for rr in read(P/'player_round_role_context.csv.xz'):
  rk=rr.pop('season'),rr.pop('round'),rr.pop('code');assert rr==round_roles[rk];roundcount+=1
 assert roundcount==len(round_roles)==182939
 for name,h in inputs.items():assert sha(R/name)==h,name
 dump(P/'verification.json',dict(passed=True,master_rows_preserved=preserved,season_rows=dict(counts),player_round_contexts=roundcount,physical_fixtures=2730,team_start_conservation_checks=len(team_starts),independent_prematch_denominator_checks=prechecks,independent_feature_checks=feature_checks,semantic_tests=tests,semantic_tests_passed=len(tests),future_mutation_invariance=True,all_original_fields_preserved=True,strict_historical_qualified=False,xg_used=False,models_fitted=0))
 print((P/'verification.json').read_text(),flush=True)
if __name__=='__main__':main()
