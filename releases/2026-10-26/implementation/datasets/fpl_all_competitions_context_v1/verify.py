"""All-season source/identity/minute, preservation and as-of verification."""
import collections,itertools,json,re,unittest,sys
from common import *
from build_context import OUT,national
from build_calendar import calculate as calendar
from workload_store import Store
from build_minutes import level
from minute_reconstruction import reconstruct
def clock(v):
 m=re.match(r'(\d+)',v.get('displayValue',''));return int(m.group(1)) if m else None
def main():
 meta,_=metadata();seasons,origins,_=config();matches={(r['season'],r['external_match_key']):r for r in read(P/'matches.csv.gz')};players=list(read(P/'player_minutes.csv.gz'));identities={};byraw=collections.defaultdict(list)
 keys=set();FPL_keys=set()
 for r in players:
  k=r['season'],r['external_match_key'],r['espn_player_id'];assert k not in keys;keys.add(k)
  fk=r['season'],r['external_match_key'],r['code'];assert fk not in FPL_keys;FPL_keys.add(fk)
  assert r['code'] in meta[r['season']] and r['element']==meta[r['season']][r['code']]['id']
  assert not truth(r['is_fpl_fixture']) and r['data_role']=='workload_context'
  assert r['age_level']==('club' if r['competition_type']=='club_cup' else level(r['external_match_key'].split(':')[0]))
  assert not {'bonus','bps','total_points','target_total_points','fixture'}&r.keys()
  identity=r['season'],r['espn_player_id'];assert identities.setdefault(identity,r['code'])==r['code']
  byraw[r['raw_file']].append(r)
 roster_checked=0;event_checked=0;duration_checks=0;differences=[]
 for filename,rows in byraw.items():
  d=json.loads((R/filename).read_text());comp=d['header']['competitions'][0];assert comp['status']['type']['completed']
  match=matches[(rows[0]['season'],rows[0]['external_match_key'])];length=int(match['match_length_excluding_added_time']);duration_checks+=1
  if any(e.get('period',{}).get('number') in [3,4] for e in d.get('keyEvents',[])):assert length==120
  rosters={p['athlete']['id']:p for side in d.get('rosters',[]) for p in side.get('roster',[])}
  for r in rows:
   assert dt(r['kickoff_utc'])==dt(comp['date'])
   if r['minutes_played']=='':continue
   p=rosters[r['espn_player_id']];subs=sorted(clock(e['clock']) for e in p.get('plays',[]) if e.get('substitution') and clock(e['clock']) is not None);red=[clock(e['clock']) for e in p.get('plays',[]) if e.get('redCard') and clock(e['clock']) is not None]
   # Independently collect this player's entry and exit from event participants.
   pid=r['espn_player_id'];start=0 if p.get('starter') else None;end=length;event_red=False
   for e in d.get('keyEvents',[]):
    ids=[a['athlete']['id'] for a in e.get('participants',[])];kind=e['type']['type'];m=clock(e['clock'])
    if kind=='substitution' and len(ids)>=2:
     if ids[0]==pid:start=m
     if ids[1]==pid:end=m
    elif kind=='red-card' and ids and ids[0]==pid and start is not None and end==length:
     end=m;event_red=True
   value=0 if start is None else max(0,min(length,end)-min(length,start));assert value==int(r['minutes_played']),(r,value);event_checked+=1
   if (p.get('subbedIn') or p.get('subbedOut')) and not subs:continue
   if event_red and not red:continue
   if not p.get('starter') and not p.get('subbedIn'):v=0
   else:
    st=0 if p.get('starter') else subs[0];en=subs[-1] if p.get('subbedOut') else length
    if red:en=min(en,min(red))
    v=max(0,min(length,en)-min(length,st))
   if v!=int(r['minutes_played']):differences.append(dict(season=r['season'],external_match_key=r['external_match_key'],team=r['team'],espn_player_id=r['espn_player_id'],player_name=r['player_name'],event_minutes=r['minutes_played'],roster_minutes=v,raw_file=r['raw_file']))
   roster_checked+=1
 if differences:
  write('minute_representation_disagreements.csv',differences)
  raise AssertionError(f'{len(differences)} minute contradictions; see minute_representation_disagreements.csv')
 teamchecks=0
 for r in read(P/'team_timeline_audit.csv.gz'):
  if truth(r['qualified']):assert int(r['total_minutes'])==int(r['expected_minutes']);teamchecks+=1
 if len(sys.argv)>1 and sys.argv[1]=='minutes':
  result=dict(passed=True,independent_event_interval_minute_checks=event_checked,roster_representation_minute_checks=roster_checked,qualified_team_conservation_checks=teamchecks,match_duration_checks=duration_checks)
  (P/'minute_verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True);return
 before_counts=collections.Counter();after_counts=collections.Counter();original_fields=None;seen=set();preserved=0
 for original,new in itertools.zip_longest(read(MASTER/'player_matches.csv.xz'),read(OUT/'player_matches.csv.xz')):
  assert original is not None and new is not None
  assert all(new[k]==v for k,v in original.items()),(original['season'],original['fixture'],original['code'])
  key=new['season'],new['fixture'],new['code'];assert key not in seen;seen.add(key)
  assert truth(new['is_fpl_fixture']) and new['competition']=='Premier League'
  assert new['wl_forecast_at'] and new['cal_forecast_at'];before_counts[original['season']]+=1;after_counts[new['season']]+=1;preserved+=1
 assert before_counts==after_counts and preserved==190124
 pl=collections.defaultdict(list);cup_rows=collections.defaultdict(list);intl=collections.defaultdict(list)
 for r in read(MASTER/'player_matches.csv.xz'):
  if truth(r['history_eligible']):pl[num(r['code'])].append((dt(r['fixture_kickoff_time']),float(r['native_minutes'])))
 for r in players:
  if r['minutes_played']=='':continue
  t=dt(r['kickoff_utc']);v=int(r['minutes_played'])
  if r['competition_type']=='club_cup':cup_rows[r['code']].append((t,v))
  else:intl[(r['season'],r['code'])].append((t,v))
 sums=0;contexts=set();calendar_cache={};announcements=list(read(P/'historical_announced_club_fixtures.csv'));cal_checks=0
 for r in read(P/'player_round_context.csv.xz'):
  key=r['season'],r['round'],r['code'];assert key not in contexts;contexts.add(key);at=dt(r['wl_forecast_at'])
  assert at==origins[(r['season'],int(r['round']))]-timedelta(minutes=90)
  for days in [3,7,14,28]:
   values=[]
   for label,rows in [('pl',pl[r['code']]),('external',cup_rows[r['code']]),('international',intl[(r['season'],r['code'])])]:
    value=sum(v for t,v in rows if at-timedelta(days=days)<=t and t+timedelta(hours=24)<at);values.append(value)
    assert float(r[f'wl_{label}_minutes_lower_bound_{days}d'])==value,(key,label,days,value);sums+=1
   assert float(r[f'wl_all_observed_minutes_lower_bound_{days}d'])==sum(values);sums+=1
  assert not truth(r['wl_all_competitions_coverage_complete'])
  if r['wl_international_latest_input_available_at']:assert dt(r['wl_international_latest_input_available_at'])<at
  ck=r['season'],r['round'],r['cal_last_observed_club'];team=ck[-1]
  if ck not in calendar_cache:
   eligible=[a for a in announcements if a['season']==r['season'] and team and team in [a['home_team'],a['away_team']] and dt(a['available_after_proxy'])<at<=dt(a['kickoff_utc'])]
   calendar_cache[ck]={d:sum(dt(a['kickoff_utc'])<at+timedelta(days=d) for a in eligible) for d in [7,14,28]}
  for days in [7,14,28]:
   value=r[f'cal_announced_cup_fixtures_lower_bound_next_{days}d'];assert (int(value) if value else None)==(calendar_cache[ck][days] if team else None);cal_checks+=1
   if not truth(r['cal_pl_calendar_fresh']):assert r[f'cal_PL_registered_fixtures_next_{days}d']==''
 hashes=0
 for file,digest in json.loads((P/'minute_input_hashes.json').read_text()).items():assert sha(R/file)==digest;hashes+=1
 for selection in json.loads((P/'calendar_origin_selection.json').read_text()):
  if selection['status']=='ok':assert dt(selection['source_time'])<dt(selection['forecast_at'])
 # Preserve all confirmed pilot FPL identities/minutes, except explicitly expanded source scope.
 pilot={(r['external_match_key'],r['espn_player_id']):r for r in read(PILOT/'international_player_minutes.csv.gz')}
 newpilot={(r['external_match_key'],r['espn_player_id']):r for r in players if r['season']=='2025-26' and r['competition_type']=='international'}
 recovered_pilot_unknown=0
 for key,oldrow in pilot.items():
  assert key in newpilot and newpilot[key]['code']==oldrow['code'],key
  if oldrow['minutes_played']!='':assert newpilot[key]['minutes_played']==oldrow['minutes_played'],key
  elif newpilot[key]['minutes_played']!='':recovered_pilot_unknown+=1
 newcup={(r['external_match_key'],r['espn_player_id']):r for r in players if r['season']=='2025-26' and r['competition_type']=='club_cup'};cup_preserved=0
 for row in read(CUP/'player_minutes.csv.gz'):
  if dt(row['kickoff_utc'])>=seasons['2025-26']['end']:continue
  key=row['external_match_key'],row['espn_player_id'];assert key in newcup and row['code']==newcup[key]['code'] and row['minutes_played']==newcup[key]['minutes_played'],key;cup_preserved+=1
 result=dict(passed=True,master_rows_preserved=preserved,season_rows=dict(after_counts),player_round_rows=len(contexts),independent_event_interval_minute_checks=event_checked,roster_representation_minute_checks=roster_checked,qualified_team_conservation_checks=teamchecks,independent_aggregate_checks=sums,historical_calendar_aggregate_checks=cal_checks,source_hashes_checked=hashes,match_duration_checks=duration_checks,pilot_international_rows_preserved=len(pilot),historical_PL_origins=len(origins),all_competitions_complete=False,FPL_observations_added=0,model_changed=False)
 result['previously_unknown_pilot_minute_rows_recovered']=recovered_pilot_unknown
 result['previous_cup_pilot_in_scope_rows_preserved']=cup_preserved
 (P/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
class TimeTests(unittest.TestCase):
 def setUp(self):
  self.at=dt('2020-09-12T10:00:00Z');self.base={'wl_hours_since_last_observed_scoped_appearance_end_proxy':100,**{f'wl_scoped_{f}_lower_bound_{d}d':10 for d in [3,7,14,28] for f in ['minutes','appearances','starts']}}
 def e(self,m=90,available=None):return dict(kickoff=self.at-timedelta(days=2),available=available or self.at-timedelta(days=1),end=self.at-timedelta(hours=46),minutes=m,starts=1,team='Norway',age_level='senior')
 def test_equal_availability_excluded(self):self.assertEqual(national('1',self.at,self.base,{'1':[self.e(available=self.at)]})['wl_international_minutes_lower_bound_7d'],0)
 def test_unknown_minutes(self):self.assertEqual(national('1',self.at,self.base,{'1':[self.e(None)]})['wl_international_unknown_minute_rows_7d'],1)
 def test_under19_is_youth(self):self.assertEqual(level('uefa.euro.u19'),'U19')
 def test_VAR_review_does_not_send_player_off(self):
  roster=[dict(athlete={'id':str(i)},starter=True,subbedIn=False,subbedOut=False) for i in range(11)]
  events=[dict(type={'type':kind},clock={'displayValue':str(m)+"'"},participants=[{'athlete':{'id':'0'}}]) for kind,m in [('var---red-card-upgrade',22),('red-card',70)]]
  values,issues,expected=reconstruct(roster,events,90);self.assertEqual(values['0'],70);self.assertEqual(expected,970);self.assertEqual(issues,[])
 def test_future_rows_invariant(self):self.assertEqual(national('1',self.at,self.base,{'1':[self.e()]}),national('1',self.at,self.base,{'1':[self.e(),self.e(available=self.at+timedelta(days=2))]}))
 def test_rest_shortens(self):self.assertEqual(national('1',self.at,self.base,{'1':[self.e()]})['wl_hours_since_last_observed_any_appearance_end_proxy'],46)
 def test_future_announcement_excluded(self):
  a=dict(season='2020-21',home_team='Liverpool',away_team='Real Madrid',available_after_proxy=self.at.isoformat(),kickoff_utc=(self.at+timedelta(days=2)).isoformat());r=calendar('Liverpool','2020-21',1,self.at,[],[a]);self.assertEqual(r['cal_announced_cup_fixtures_lower_bound_next_7d'],0)
 def test_season_end_not_blank_rounds(self):
  r=dict(home_team='Liverpool',away_team='Other',event='47',kickoff_time='2020-07-26T15:00:00Z',source_time='2020-07-20T00:00:00Z',snapshot_age_days='1',calendar_usable='True');c=calendar('Liverpool','2019-20',47,dt('2020-07-26T13:30:00Z'),[r],[]);self.assertEqual(c['cal_horizon_rounds_available_next_6'],1);self.assertEqual(c['cal_PL_blank_rounds_next_6'],0)
if __name__=='__main__':
 result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(TimeTests));assert result.wasSuccessful();main()
