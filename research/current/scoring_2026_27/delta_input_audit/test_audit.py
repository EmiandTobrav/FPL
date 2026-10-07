import hashlib,json,unittest
import pandas as pd
from build import P,S,KEY,OPEN,raw_net,compare

class DefinitionTests(unittest.TestCase):
 def test_signed_net_uses_possession_outcome_not_failed_challenges(self):
  result=raw_net(pd.Series([3,3,4]),pd.Series([3,1,2]))
  self.assertEqual(result.tolist(),[3,-1,0])
 def test_no_sparse_zero_or_invalid_input(self):
  result=raw_net(pd.Series([3,None,1,2.5,-1]),pd.Series([None,1,2,1,0]))
  self.assertTrue(result.isna().all())
 def test_omission_is_not_an_explicit_zero_match(self):
  result=compare(pd.Series([None,0,1,2,None]),pd.Series([0,0,2,None,None]))
  self.assertEqual(result.tolist(),['omission_difference','equal_explicit','explicit_conflict','omission_difference','both_omitted'])

class OutputTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.req=pd.read_csv(P/'requirements.csv.gz',low_memory=False)
  cls.old=pd.read_csv(S/'fpl_authority/requirements.csv.gz',low_memory=False)
  cls.archive=pd.read_csv(P/'inputs/archive_projection.csv.gz',low_memory=False)
  cls.result=json.loads((P/'findings.json').read_text())
 def test_fpl_and_keeper_values_and_statuses_unchanged(self):
  mask=self.old.status.isin(['fpl_authoritative','approved_reconstruction','documented_zero'])
  pd.testing.assert_frame_equal(self.req.loc[mask,KEY+['field','value','status']],self.old.loc[mask,KEY+['field','value','status']])
  keep=self.req[self.req.field.eq('big_chance_saves')]
  self.assertEqual(int(keep.status.eq('approved_reconstruction').sum()),5343)
  self.assertEqual(int(keep.is_open.sum()),38)
  self.assertFalse(self.req.field.eq('minutes').any())
 def test_source_and_target_identity_unique(self):
  a=self.archive
  self.assertFalse(a.duplicated(KEY).any())
  self.assertFalse(a[a.mapping_status.eq('matched')].duplicated(['match_id','player_id']).any())
  self.assertFalse(self.req.duplicated(KEY+['field']).any())
  linked=a.mapping_status.eq('matched')
  self.assertTrue(a.loc[linked,'team_id'].eq(a.loc[linked,'team_id_raw']).all())
  self.assertTrue(a.loc[linked,'date'].eq(a.loc[linked,'match_date'].str[:10]).all())
 def test_explicit_archive_zero_is_preserved_but_absence_is_not_zero(self):
  r=self.req[self.req.field.eq('times_tackled')]
  zeros=r.archive_projected.eq(0)&~r.is_open
  self.assertGreater(int(zeros.sum()),30000)
  self.assertTrue(r.loc[zeros,'value'].eq(0).all())
  absent=r.archive_projected.isna()&r.previous_status.eq('missing_data')
  self.assertTrue(r.loc[absent,'value'].isna().all())
 def test_legacy_net_requires_both_explicit_raw_counts(self):
  r=self.req[self.req.field.eq('legacy_net_tackles')].set_index(KEY)
  a=self.archive.set_index(KEY).reindex(r.index)
  known=r.value.notna()
  self.assertTrue(a.loc[known,['wonTackle','totalTackle']].notna().all().all())
  self.assertTrue(r.loc[known,'value'].eq(2*a.loc[known,'wonTackle']-a.loc[known,'totalTackle']).all())
  self.assertTrue(r.value.lt(0).any())
  self.assertFalse(self.result['legacy_net_clipping_qualified'])
 def test_external_event_conflicts_remain_open(self):
  r=self.req[self.req.quality_status.eq('explicit_event_conflict')]
  self.assertGreater(len(r),0)
  self.assertTrue(r.is_open.all());self.assertTrue(r.value.isna().all())
  self.assertTrue(r.status.eq('external_conflict').all())
 def test_line_clearance_omissions_never_promoted_to_zero(self):
  r=self.req[self.req.field.eq('goal_line_clearances')]
  self.assertFalse(r.value.eq(0).any())
  audit=json.loads((P/'line_clearance_audit.json').read_text())
  self.assertGreater(audit['omitted_stat_event_zero_candidate'],60000)
  self.assertEqual(audit['zeros_approved'],0)
 def test_fresh_controls_preselected_and_not_reused(self):
  plan=pd.read_csv(P/'control_plan.csv').sort_values(KEY).reset_index(drop=True)
  fresh=pd.read_csv(P/'inputs/fresh_primary_controls.csv').sort_values(KEY).reset_index(drop=True)
  pd.testing.assert_frame_equal(plan[KEY+['stratum']],fresh[KEY+['stratum']])
  self.assertEqual(len(plan),28)
  old=pd.read_csv(S/'bps_recovery/inputs/primary_controls.csv.gz',low_memory=False)
  self.assertFalse(pd.MultiIndex.from_frame(fresh[KEY]).isin(pd.MultiIndex.from_frame(old[KEY])).any())
  c=pd.read_csv(P/'primary_comparisons.csv.gz');c=c[c.control_scope.eq('fresh_prespecified')]
  self.assertEqual(int(c.comparison.eq('equal_explicit').sum()),160)
  self.assertFalse(c.comparison.eq('explicit_conflict').any())
 def test_checked_cells_have_explicit_primary_agreement(self):
  r=self.req[self.req.status.eq('external_checked')]
  self.assertGreater(len(r),1000)
  self.assertTrue(r.value.eq(r.primary_audit_value).all())
  self.assertFalse(r.is_open.any());self.assertFalse(r.needs_external_quality_review.any())
 def test_unique_counts_and_transition_balance(self):
  r=self.req
  self.assertEqual(int(r.is_open.sum()),self.result['open_cells'])
  self.assertEqual(len(r.loc[r.is_open,KEY].drop_duplicates()),self.result['unique_affected_player_matches'])
  self.assertEqual(self.result['old_open_cells']-self.result['newly_available_cells']+self.result['newly_flagged_conflict_cells'],self.result['open_cells'])
  self.assertEqual(pd.read_csv(P/'field_summary.csv').open_cells.sum(),self.result['open_cells'])
 def test_fpl_differences_are_diagnostics_not_fpl_overrides(self):
  f=pd.read_csv(P/'fpl_2025_comparisons.csv.gz')
  self.assertGreater(int(f.comparison.eq('explicit_conflict').sum()),0)
  r=self.req[self.req.status.eq('fpl_authoritative')]
  self.assertTrue(r.value.eq(r.previous_value).all())
 def test_published_aggregate_differences_preserved(self):
  f=pd.read_csv(P/'official_season_comparisons.csv')
  self.assertEqual(len(f),16)
  self.assertEqual(int(f.published_minus_archive.ne(0).sum()),3)
  self.assertEqual(int(f.resolution.eq('current_primary_agrees_archive_published_snapshot_differs').sum()),2)
 def test_manifest_hashes_and_claim_limits(self):
  for rel,digest in json.loads((P/'manifest.json').read_text())['inputs'].items():
   self.assertEqual(hashlib.sha256((S/rel).read_bytes()).hexdigest(),digest,rel)
  self.assertFalse(self.result['fpl_values_modified'])
  self.assertFalse(self.result['independent_provider_validation'])
  self.assertFalse(self.result['full_historical_harmonization_complete'])
  self.assertFalse(self.result['new_scoring_holdout'])

if __name__=='__main__':unittest.main()
