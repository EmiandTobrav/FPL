import unittest,json,hashlib
from pathlib import Path
import pandas as pd
from rules import residual,zero_subset,signed_net
P=Path(__file__).resolve().parent;KEY=['season','fixture','code']
class ConservationTests(unittest.TestCase):
 def test_explicit_total_exhausted(self):self.assertEqual(residual(3,[1,None,2])[0],0)
 def test_missing_total(self):self.assertIsNone(residual(None,[1,None,2])[0])
 def test_zero_team_total(self):self.assertEqual(residual(0,[None,None])[0],0)
 def test_positive_residual_not_allocated(self):self.assertIsNone(residual(4,[1,None,2])[0])
 def test_conflict(self):self.assertEqual(residual(2,[1,None,2])[1],'aggregate_conflict')
 def test_invalid_counter(self):
  for values in [[-1,None],[.5,None],[float('inf'),None]]:self.assertIsNone(residual(2,values)[0])
 def test_subset(self):
  self.assertEqual(zero_subset(0),0);self.assertIsNone(zero_subset(None));self.assertIsNone(zero_subset(2))
 def test_signed_not_clipped(self):self.assertEqual(signed_net(3,1),-1)
 def test_net_requires_both(self):self.assertIsNone(signed_net(None,0));self.assertIsNone(signed_net(2,None))
 def test_impossible_won(self):self.assertIsNone(signed_net(1,2))
 def test_masked_positive_is_not_zero(self):self.assertIsNone(residual(4,[2,None])[0])
 def test_nan_not_observed_zero(self):self.assertIsNone(residual(float('nan'),[float('nan')])[0])

class OutputTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.before=pd.read_csv(P.parent/'assist_reconciliation/requirements.csv.gz',low_memory=False)
  cls.after=pd.read_csv(P/'requirements.csv.gz',low_memory=False)
  cls.derived=pd.read_csv(P/'derived_values.csv.gz',low_memory=False)
 def test_only_missing_target_fields_change(self):
  mask=~self.before.status.eq('missing_data')|~self.before.field.isin(['won_tackles','legacy_net_tackles','shots_on_target','fouls_won','goal_line_clearances'])
  pd.testing.assert_frame_equal(self.before[mask],self.after.loc[mask,self.before.columns],check_dtype=False)
 def test_assists_and_keepers_unchanged(self):
  mask=self.before.field.isin(['assists_2026_27','big_chance_saves','saves','saves_inside_box','saves_outside_box'])
  pd.testing.assert_frame_equal(self.before[mask],self.after.loc[mask,self.before.columns],check_dtype=False)
 def test_deduplicated_changes(self):
  self.assertFalse(self.derived.duplicated(KEY+['field']).any())
  self.assertEqual(len(self.derived),int((self.before.is_open&~self.after.is_open).sum()))
 def test_all_derived_values_keep_quality_caveat(self):
  a=self.after[self.after.status.eq('external_derived')]
  self.assertTrue(a.needs_external_quality_review.all());self.assertFalse(a.is_open.any())
 def test_no_generic_sparse_fill(self):
  self.assertTrue(self.derived.method.isin(['explicit_total_tackles_zero_subset','explicit_team_total_exhausted','signed_net_from_qualified_won_and_total']).all())
  zeros=self.derived[self.derived.method.eq('explicit_total_tackles_zero_subset')]
  self.assertTrue(zeros.parent_value.eq(0).all());self.assertGreater(len(zeros),28000)
 def test_conservation_certificates(self):
  d=pd.read_csv(P/'conservation.csv.gz');c=d[d.zero_certified]
  self.assertTrue(c.total.notna().all());self.assertTrue(c.total.eq(c.known_sum).all())
  self.assertFalse(d.loc[d.total.isna(),'zero_certified'].any())
 def test_readiness_is_not_bonus_approval(self):
  d=pd.read_csv(P/'match_readiness.csv')
  self.assertFalse(d.bonus_ready.any());self.assertTrue(d.inputs_available.eq(d.open_fields.eq(0)).all())
 def test_count_union(self):
  f=json.loads((P/'findings.json').read_text());d=self.after
  self.assertEqual(f['unique_affected_player_matches'],len(d.loc[d.is_open,KEY].drop_duplicates()))
  self.assertEqual(f['unique_open_or_quality_player_matches'],len(d.loc[d.is_open|d.needs_external_quality_review,KEY].drop_duplicates()))
 def test_conflicting_total_never_parent(self):
  bad=self.before[self.before.field.eq('total_tackles')&self.before.is_open]
  forbidden=set(map(tuple,bad[KEY].to_numpy()))
  deriv=self.derived[self.derived.method.isin(['explicit_total_tackles_zero_subset','signed_net_from_qualified_won_and_total'])]
  self.assertFalse(forbidden & set(map(tuple,deriv[KEY].to_numpy())))
 def test_line_subset_rejected(self):
  d=pd.read_csv(P/'line_subset_counterexamples.csv')
  self.assertGreater(len(d),0)
  self.assertFalse(self.derived.method.str.contains('clearance.*block',regex=True).any())
 def test_temporal_controls_separate(self):
  p=pd.read_csv(P/'pilot_plan.csv');h=pd.read_csv(P/'holdout_plan.csv')
  self.assertFalse(set(p.pulse_id)&set(h.pulse_id))
  for season,g in h.groupby('season'):self.assertGreater(g.date.min(),p.loc[p.season.eq(season),'date'].max())
 def test_frozen_method_and_manifest(self):
  f=json.loads((P/'protocol.json').read_text())
  for name,digest in f['frozen'].items():self.assertEqual(hashlib.sha256((P/name).read_bytes()).hexdigest(),digest)
  for name,digest in json.loads((P/'manifest.json').read_text()).items():self.assertEqual(hashlib.sha256((P.parent/name).read_bytes()).hexdigest(),digest)
if __name__=='__main__':unittest.main()
