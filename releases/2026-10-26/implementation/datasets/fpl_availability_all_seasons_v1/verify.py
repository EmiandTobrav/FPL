"""Independent all-season checks, including stale archives and deadline repairs."""
import collections,itertools,json,lzma,unittest,sys
from common import *
from build import empty,optional_date
History=pilot.History;peer_features=pilot.peer_features;feature=pilot.feature;chance=pilot.chance;reason=pilot.reason
def main():
 audits={(a['season'],int(a['round'])):a for a in read(P/'snapshot_audit.csv')};selected={(s['season'],s['round']):s for s in json.loads((P/'selected_sources.json').read_text())};assert len(audits)==len(selected)==272
 raw={};teams_by_origin={};rosters={};valid_origins=0;nonplayers=0
 for key,a in audits.items():
  s=selected[key];path=R/a['source_file'];assert sha(path)==a['source_sha256'];source=dt(a['snapshot_at_proxy']);at=dt(a['forecast_at']);assert source<at
  assert at<=dt(a['master_origin']);age=(at-source).total_seconds()/3600;assert abs(age-float(a['snapshot_age_hours']))<1e-8
  if a['format']=='bootstrap':
   b=path.read_bytes();assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==a['source_blob_sha'];data=json.loads(lzma.decompress(b));event=next(e for e in data['events'] if e['id']==key[1]);actual=dt(event['deadline_time']);binding='next' if event['is_next'] else 'this' if event['is_current'] else 'unknown';eligible=age<=24 and source<actual and binding!='unknown'
   assert dt(a['actual_FPL_deadline'])==actual and at==min(dt(a['master_origin']),actual);assert a['chance_binding']==binding
   teammap={num(t['id']):t['name'] for t in data['teams']};elements=data['elements']
  else:
   elements=list(read(path));teammap={num(t['id']):t['name'] for t in read(R/'FPL_training_dataset/research/current/project/data'/f'{key[0]}_teams.csv.gz')};eligible=age<=24;assert not truth(a['source_deadline_bound']) and a['chance_binding']=='unbound_csv' and a['actual_FPL_deadline']==''
  assert truth(a['source_eligible'])==eligible
  valid_origins+=eligible;teams_by_origin[key]=teammap;raw[key]={};rosters[key]=collections.defaultdict(list)
  for e in elements:
   pos=int(float(e['element_type']))
   if pos not in [1,2,3,4]:nonplayers+=1;continue
   code=num(e['code']);e=dict(e,normalized_code=code,position=pos,team_name=teammap[num(e['team'])]);raw[key][code]=e;rosters[key][e['team_name']].append(e)
  assert len(raw[key])==int(a['source_players'])
 histories=collections.defaultdict(list)
 for r in read(MASTER/'player_matches.csv.xz'):
  if truth(r['history_eligible']):
   t=dt(r['fixture_kickoff_time']);available=dt(r['observation_available_after_proxy']);assert available==t+timedelta(hours=24)
   histories[(num(r['code']),r['historical_team'])].append((t,available,float(r['native_minutes'])))
 weight_cache={};peer_checks=0;minute_checks=0;share_checks=0;unknown=0;known=0;nullchance=0;contexts={};coverage=collections.defaultdict(collections.Counter)
 for r in read(P/'player_round_context.csv.xz'):
  season=r['season'];gw=int(r['round']);key=season,gw;code=r['code'];ck=season,gw,code;assert ck not in contexts;contexts[ck]=r;a=audits[key];at=dt(r['av_forecast_at']);assert at==dt(a['forecast_at']);assert not truth(r['av_strict_historical_qualified'])
  assert truth(r['av_mixed_origin_with_workload'])==(at!=dt(a['master_origin']))
  own=raw[key].get(code);source_ok=truth(a['source_eligible']);valid=bool(source_ok and own and own.get('status') in ['a','d','i','s','n','u'] and (optional_date(own.get('news_added')) is None or optional_date(own['news_added'])<=dt(a['snapshot_at_proxy'])))
  assert truth(r['av_source_known'])==valid
  if not valid:
   assert r['av_reported_status']=='' and r['av_reported_chance']==''
   assert all(r[k]=='' for k in r if k.startswith(('av_team_','av_same_FPL_position_')));unknown+=1;coverage[season]['unknown_rounds']+=1;continue
  known+=1;coverage[season]['known_rounds']+=1;assert r['av_reported_status']==own['status'] and r['av_snapshot_team']==own['team_name'] and int(r['av_FPL_position'])==own['position']
  expected=own.get('chance_of_playing_next_round' if a['chance_binding']=='next' else 'chance_of_playing_this_round') if a['chance_binding'] in ['next','this'] else None
  expected=None if empty(expected) else float(expected);actual=None if not r['av_reported_chance'] else float(r['av_reported_chance']);assert actual==expected
  if expected is None:nullchance+=1
  if a['format']=='players_csv':assert actual is None and truth(r['av_status_only_source']) and not truth(r['av_chance_binding_verified'])
  peers=[e for e in rosters[key][own['team_name']] if e['normalized_code']!=code]
  def ok(e):return e.get('status') in ['a','d','i','s','n','u'] and (optional_date(e.get('news_added')) is None or optional_date(e['news_added'])<=dt(a['snapshot_at_proxy']))
  def departure(e):return e['status']=='u' or (e['status']=='n' and reason('' if empty(e.get('news')) else e['news'])=='transfer_or_loan')
  for label,group in [('team',peers),('same_FPL_position',[p for p in peers if p['position']==own['position']])]:
   valid_peers=[p for p in group if ok(p)];core=[p for p in valid_peers if p['status'] in ['a','d','i','s','n'] and not departure(p)]
   values={'other_registered_players':len(group),'status_unknown_players':len(group)-len(valid_peers),'reported_available_players':sum(p['status']=='a' for p in valid_peers),'reported_doubtful_players':sum(p['status']=='d' for p in valid_peers),'reported_injured_players':sum(p['status']=='i' for p in core),'reported_suspended_players':sum(p['status']=='s' for p in core),'reported_other_unavailable_players':sum(p['status']=='n' for p in core),'departure_or_loan_reports':sum(departure(p) for p in valid_peers)}
   for name,value in values.items():assert int(r[f'av_{label}_{name}'])==value;peer_checks+=1
   for days in [28,90]:
    for p in core:
     wk=key,p['normalized_code'],own['team_name'],days
     if wk not in weight_cache:weight_cache[wk]=sum(v for t,available,v in histories[(p['normalized_code'],own['team_name'])] if at-timedelta(days=days)<=t<at and available<at)
    total=sum(weight_cache[(key,p['normalized_code'],own['team_name'],days)] for p in core);assert float(r[f'av_{label}_past_PL_minutes_{days}d'])==total;minute_checks+=1
    for category,statuses in [('medical_or_suspension',['i','s']),('all_core_unavailable',['i','s','n']),('doubtful',['d'])]:
     value=sum(weight_cache[(key,p['normalized_code'],own['team_name'],days)] for p in core if p['status'] in statuses);assert float(r[f'av_{label}_{category}_past_PL_minutes_{days}d'])==value;minute_checks+=1
     share=r[f'av_{label}_{category}_past_PL_minute_share_{days}d']
     if total:assert abs(float(share)-value/total)<=5.1e-9
     else:assert share==''
     share_checks+=1
 master_rows=0;known_matches=0;seen=set();season_rows=collections.Counter()
 for old,new in itertools.zip_longest(read(MASTER/'player_matches.csv.xz'),read(OUT/'player_matches.csv.xz')):
  assert old is not None and new is not None;assert all(new[k]==v for k,v in old.items());k=new['season'],new['fixture'],new['code'];assert k not in seen;seen.add(k)
  c=contexts[(new['season'],int(new['round']),num(new['code']))];assert all(new[k]==v for k,v in c.items() if k.startswith('av_'))
  assert truth(new['is_fpl_fixture']) and new['competition']=='Premier League';master_rows+=1;known_matches+=truth(new['av_source_known']);season_rows[new['season']]+=1
 assert master_rows==190124 and len(contexts)==182939
 # The completed pilot must remain exactly reproducible under the all-season layer.
 pilot_checked=0
 for p in read(PILOT/'player_round_context.csv.xz'):
  c=contexts[(p['season'],int(p['round']),p['code'])]
  assert all(c[k]==v for k,v in p.items() if k.startswith('av_')),(p['round'],p['code']);pilot_checked+=1
 for (season,gw),deadline in {('2021-22',18):'2021-12-18T13:30:00Z',('2024-25',15):'2024-12-07T11:00:00Z'}.items():assert dt(audits[(season,gw)]['forecast_at'])==dt(deadline) and dt(audits[(season,gw)]['snapshot_at_proxy'])<dt(deadline)
 for name,digest in json.loads((P/'input_hashes.json').read_text()).items():assert sha(R/name)==digest,name
 result=dict(passed=True,master_rows_preserved=master_rows,season_rows=dict(season_rows),player_round_contexts=len(contexts),known_master_rows=known_matches,unknown_master_rows=master_rows-known_matches,known_player_rounds=known,unknown_player_rounds=unknown,origin_sources_checked=len(audits),eligible_source_origins=valid_origins,non_player_assets_excluded=nonplayers,null_or_unbound_chances_preserved=nullchance,independent_peer_count_checks=peer_checks,independent_past_minute_checks=minute_checks,independent_share_checks=share_checks,pilot_round_contexts_preserved=pilot_checked,earlier_deadline_repairs=2,strict_historical_qualified=False,model_fits=0)
 (P/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
class BoundaryTests(unittest.TestCase):
 def setUp(self):self.at=dt('2023-09-01T17:30:00Z')
 def ev(self,team='A',available=None,kickoff=None,minutes=90):return dict(code='1',team=team,available=available or self.at-timedelta(days=1),kickoff=kickoff or self.at-timedelta(days=2),minutes=minutes)
 def person(self,code,status='a',departure=False):return dict(code=code,known=True,position=3,status=status,departure=departure,core=not departure)
 def test_equal_availability_excluded(self):self.assertEqual(History([self.ev(available=self.at)]).minutes('1','A',self.at,28),0)
 def test_window_start_included(self):self.assertEqual(History([self.ev(kickoff=self.at-timedelta(days=28))]).minutes('1','A',self.at,28),90)
 def test_other_club_excluded(self):self.assertEqual(History([self.ev(team='Old')]).minutes('1','New',self.at,90),0)
 def test_future_stats_do_not_change_weights(self):self.assertEqual(History([self.ev()]).minutes('1','A',self.at,28),History([self.ev(),self.ev(available=self.at+timedelta(days=2),minutes=200)]).minutes('1','A',self.at,28))
 def test_loan_not_medical_absence(self):
  out=peer_features(self.person('1'),[self.person('2','u',True)],{});self.assertEqual(out['av_team_reported_injured_players'],0)
 def test_self_is_excluded_from_peer_group(self):
  out=peer_features(self.person('1','i'),[self.person('2')],{('2',28):90,('2',90):90});self.assertEqual(out['av_team_reported_injured_players'],0)
 def test_zero_weight_share_unknown(self):self.assertIsNone(peer_features(self.person('1'),[],{})['av_team_all_core_unavailable_past_PL_minute_share_90d'])
 def test_unknown_player_has_no_future_team(self):self.assertIsNone(feature(None,[],{})['av_snapshot_team'])
 def test_null_chance_is_not_100(self):self.assertIsNone(chance(None))
 def test_will_does_not_mean_illness(self):self.assertEqual(reason('Knee injury. Will be assessed.'),'injury')
 def test_earlier_actual_deadline_wins(self):self.assertEqual(min(dt('2024-12-07T13:30:00Z'),dt('2024-12-07T11:00:00Z')),dt('2024-12-07T11:00:00Z'))
if __name__=='__main__':
 result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(BoundaryTests));assert result.wasSuccessful();main()
