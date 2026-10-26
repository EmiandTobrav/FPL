"""Independent raw-role and absence-scenario checks, plus master preservation."""
import collections,hashlib,itertools,json,unittest
from common import *
from build import role_features,features,all_out
def digest(row):return hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
def reference_order(e,prefix):
 field=prefix+'_order'
 if field not in e:return None,False
 value=e[field]
 if value is None or str(value) in ['', 'None','nan','null']:return None,True
 try:
  v=float(value)
  if not v.is_integer() or v<=0:return None,False
  return int(v),True
 except (ValueError,TypeError,OverflowError):return None,False
def main():
 audits={(r['season'],int(r['round'])):r for r in read(AV/'snapshot_audit.csv')};statuses={(r['season'],int(r['round']),r['code']):r for r in read(AV/'source_player_status.csv.gz')};raw={};groups=collections.defaultdict(list);source_checks=0
 for key,a in audits.items():
  es,teams=raw_players(a);assert sha(R/a['source_file'])==a['source_sha256'];eligible=truth(a['source_eligible'])
  if eligible:assert dt(a['snapshot_at_proxy'])<dt(a['forecast_at']) and float(a['snapshot_age_hours'])<=24
  for e in es:
   if int(float(e['element_type'])) not in [1,2,3,4]:continue
   code=num(e['code']);av=statuses[(key[0],key[1],code)];assert av['team_name']==teams[num(e['team'])] and av['element']==num(e['id'])
   news=e.get('news_added');record_ok=eligible and (null(news) or dt(news)<=dt(a['snapshot_at_proxy']));r=dict(code=code,team=av['team_name'],status=av['status'],status_known=truth(av['known']),departure=truth(av['departure']),ranks={})
   for role,prefix in ROLES.items():
    rank,valid=reference_order(e,prefix);r['ranks'][role]=(rank if record_ok and valid else None,record_ok and valid)
   raw[(key[0],key[1],code)]=r
   if eligible:groups[(key[0],key[1],r['team'])].append(r)
  source_checks+=1
 context_hashes={};known=0;missing=0;own_checks=0;group_checks=0;scenario_checks=0;promotion_counts=collections.Counter();list_counts=collections.Counter();source_origin_keys=set();ties=0;gaps=0
 for row in read(P/'player_round_context.csv.xz'):
  season=row['season'];gw=int(row['round']);code=row['code'];key=(season,gw,code);assert key not in context_hashes;a=audits[(season,gw)];at=dt(row['sp_forecast_at']);assert at==dt(a['forecast_at']);assert not truth(row['sp_strict_historical_qualified']) and not truth(row['sp_actual_taker_confirmed']) and not truth(row['sp_role_list_is_exhaustive'])
  own=raw.get(key) if truth(a['source_eligible']) else None;team=groups[(season,gw,own['team'])] if own else []
  known_any=bool(own and any(valid for rank,valid in own['ranks'].values()));assert truth(row['sp_source_known'])==known_any
  if known_any:known+=1;source_origin_keys.add((season,gw))
  else:missing+=1
  for role in ROLES:
   p='sp_'+role+'_';rank,valid=own['ranks'][role] if own else (None,False);assert truth(row[p+'source_known'])==valid
   if not valid:
    assert all(row[k]=='' for k in row if k.startswith(p) and k!=p+'source_known');continue
   own_checks+=1;assert (int(row[p+'listed_order']) if row[p+'listed_order'] else None)==rank;assert truth(row[p+'listed_for_role'])==(rank is not None);assert truth(row[p+'listed_first_choice'])==(rank==1)
   listed=[x for x in team if x['ranks'][role][1] and x['ranks'][role][0] is not None];orders=[x['ranks'][role][0] for x in listed];primary=[x for x in listed if x['ranks'][role][0]==1];complete=all(x['ranks'][role][1] for x in team);has_ties=len(set(orders))!=len(orders);has_gaps=bool(orders and set(orders)!=set(range(1,max(orders)+1)))
   assert int(row[p+'team_listed_players'])==len(listed) and int(row[p+'team_first_choice_players'])==len(primary)
   assert truth(row[p+'team_schema_complete'])==complete and truth(row[p+'team_has_tied_orders'])==has_ties and truth(row[p+'team_has_order_gaps'])==has_gaps;group_checks+=5;ties+=has_ties;gaps+=has_gaps
   def out_value(group):
    if not group:return None
    if any(x['status_known'] and x['status'] in ['a','d'] for x in group):return False
    if any(not x['status_known'] for x in group):return None
    return True
   def equal_optional(name,value):
    expected='' if value is None else str(value);assert row[p+name]==expected,(key,p+name,row[p+name],expected)
   equal_optional('first_choice_absence_reported',out_value(primary) if complete else None)
   if rank is None:
    assert row[p+'potential_promotion']=='' and row[p+'listed_players_ahead']=='' and row[p+'unique_top_remaining_candidate']=='';continue
   list_counts[role]+=1;ahead=[x for x in listed if x['ranks'][role][0]<rank];same=[x for x in listed if x['ranks'][role][0]==rank and x['code']!=code];contiguous=all(i in {x['ranks'][role][0] for x in ahead} for i in range(1,rank))
   values={'same_rank_other_players':len(same),'listed_players_ahead':len(ahead),'ahead_reported_available':sum(x['status_known'] and x['status']=='a' for x in ahead),'ahead_reported_doubtful':sum(x['status_known'] and x['status']=='d' for x in ahead),'ahead_reported_unavailable':sum(x['status_known'] and x['status'] in ['i','s','n'] and not x['departure'] for x in ahead),'ahead_departure_reports':sum(x['status_known'] and x['departure'] for x in ahead),'ahead_status_unknown':sum(not x['status_known'] for x in ahead)}
   for name,value in values.items():assert int(row[p+name])==value;group_checks+=1
   assert truth(row[p+'ranks_ahead_complete'])==contiguous;equal_optional('all_listed_ahead_reported_out',out_value(ahead))
   if not own['status_known'] or own['status']=='d':top=None
   elif own['status'] in ['i','s','n','u']:top=False
   elif not complete or not contiguous:top=None
   else:top=True if rank==1 else out_value(ahead)
   promotion=False if rank==1 or (own['status_known'] and own['status'] in ['i','s','n','u']) else top
   equal_optional('top_remaining_listed_candidate',top);equal_optional('potential_promotion',promotion)
   tied=None
   if top is True:
    tied=True if any(x['status_known'] and x['status'] in ['a','d'] for x in same) else None if any(not x['status_known'] for x in same) else False
   unique=(not tied) if top is True and tied is not None else False if top is False else None
   equal_optional('top_remaining_tied',tied);equal_optional('unique_top_remaining_candidate',unique);scenario_checks+=5;promotion_counts[role]+=promotion is True
  context_hashes[key]=digest({k:v for k,v in row.items() if k.startswith('sp_')})
 assert len(context_hashes)==182939
 match_seen=set()
 for row in read(P/'player_match_context.csv.xz'):
  key=row['season'],row['fixture'],row['code'];assert key not in match_seen;match_seen.add(key)
  assert digest({k:v for k,v in row.items() if k.startswith('sp_')})==context_hashes[(row['season'],int(row['round']),row['code'])]
 assert len(match_seen)==190124
 preserved=0;known_matches=0;season_counts=collections.Counter()
 for original,new in itertools.zip_longest(read(MASTER/'player_matches.csv.xz'),read(OUT/'player_matches.csv.xz')):
  assert original is not None and new is not None;assert all(new[k]==v for k,v in original.items());assert new['competition']=='Premier League' and truth(new['is_fpl_fixture'])
  key=new['season'],new['fixture'],num(new['code']);assert key in match_seen;match_seen.remove(key)
  assert digest({k:v for k,v in new.items() if k.startswith('sp_')})==context_hashes[(new['season'],int(new['round']),num(new['code']))]
  assert dt(new['sp_forecast_at'])==dt(new['av_forecast_at']);preserved+=1;known_matches+=truth(new['sp_source_known']);season_counts[new['season']]+=1
 assert preserved==190124 and not match_seen
 for name,value in json.loads((P/'input_hashes.json').read_text()).items():assert sha(R/name)==value,name
 result=dict(passed=True,master_rows_preserved=preserved,season_rows=dict(season_counts),player_round_contexts=len(context_hashes),source_origins_checked=source_checks,origins_with_usable_role_schema=len(source_origin_keys),known_role_source_master_rows=known_matches,unknown_role_source_master_rows=preserved-known_matches,known_role_source_player_rounds=known,unknown_role_source_player_rounds=missing,own_role_checks=own_checks,independent_group_count_checks=group_checks,independent_scenario_checks=scenario_checks,listed_player_rounds=dict(list_counts),potential_promotion_player_rounds=dict(promotion_counts),player_role_rows_with_ties=ties,player_role_rows_with_gaps=gaps,actual_taker_confirmed=False,strict_historical_qualified=False,model_fits=0)
 (P/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
def player(code,rank,status='a',status_known=True,rank_known=True,departure=None):
 return dict(code=code,team='A',status=status,status_known=status_known,departure=status=='u' if departure is None else departure,roles={r:dict(known=rank_known,order=rank,text='') for r in ROLES})
class ScenarioTests(unittest.TestCase):
 def result(self,own,other):return role_features(own,[own]+other,'penalties')
 def test_reported_backup_can_gain_role(self):
  out=self.result(player('2',2),[player('1',1,'i')]);self.assertTrue(out['sp_penalties_potential_promotion']);self.assertTrue(out['sp_penalties_unique_top_remaining_candidate'])
 def test_doubtful_first_choice_is_not_out(self):self.assertFalse(self.result(player('2',2),[player('1',1,'d')])['sp_penalties_potential_promotion'])
 def test_unknown_first_choice_blocks_inference(self):self.assertIsNone(self.result(player('2',2),[player('1',1,status_known=False)])['sp_penalties_potential_promotion'])
 def test_own_doubt_blocks_positive_flag(self):self.assertIsNone(self.result(player('2',2,'d'),[player('1',1,'i')])['sp_penalties_potential_promotion'])
 def test_gap_is_not_automatic_promotion(self):
  out=self.result(player('3',3),[player('1',1,'i')]);self.assertFalse(out['sp_penalties_ranks_ahead_complete']);self.assertIsNone(out['sp_penalties_potential_promotion'])
 def test_one_available_primary_blocks_shared_primary_absence(self):self.assertFalse(self.result(player('2',2),[player('1',1,'i'),player('3',1)])['sp_penalties_potential_promotion'])
 def test_tied_backups_are_not_unique(self):
  out=self.result(player('2',2),[player('1',1,'s'),player('3',2)]);self.assertTrue(out['sp_penalties_potential_promotion']);self.assertTrue(out['sp_penalties_top_remaining_tied']);self.assertFalse(out['sp_penalties_unique_top_remaining_candidate'])
 def test_unknown_tied_backup_is_not_unique(self):self.assertIsNone(self.result(player('2',2),[player('1',1,'i'),player('3',2,status_known=False)])['sp_penalties_unique_top_remaining_candidate'])
 def test_unlisted_is_not_missing_schema(self):
  a=self.result(player('2',None),[player('1',1)]);b=self.result(player('2',None,rank_known=False),[player('1',1)]);self.assertFalse(a['sp_penalties_listed_for_role']);self.assertIsNone(b['sp_penalties_listed_for_role']);self.assertIsNone(a['sp_penalties_potential_promotion'])
 def test_departure_is_separate_from_medical_absence(self):
  out=self.result(player('2',2),[player('1',1,'u')]);self.assertEqual(out['sp_penalties_ahead_departure_reports'],1);self.assertEqual(out['sp_penalties_ahead_reported_unavailable'],0)
 def test_unavailable_own_player_not_promoted(self):self.assertFalse(self.result(player('2',2,'i'),[player('1',1,'s')])['sp_penalties_potential_promotion'])
 def test_no_primary_does_not_mean_primary_absent(self):self.assertIsNone(self.result(player('2',2),[])['sp_penalties_first_choice_absence_reported'])
 def test_existing_primary_needs_no_promotion(self):
  out=self.result(player('1',1),[]);self.assertTrue(out['sp_penalties_listed_first_choice']);self.assertFalse(out['sp_penalties_potential_promotion'])
 def test_zero_order_is_not_unlisted(self):self.assertEqual(order(0),(None,False));self.assertEqual(order(None),(None,True))
if __name__=='__main__':
 result=unittest.TextTestRunner().run(unittest.defaultTestLoader.loadTestsFromTestCase(ScenarioTests));assert result.wasSuccessful();main()
