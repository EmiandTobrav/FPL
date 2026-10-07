import unittest
import pandas as pd
from audit import apply_aliases

class IdentityTests(unittest.TestCase):
    def setUp(self):
        self.target=pd.DataFrame([dict(code=12,match_id='m1',player_id=None,mapping_status='name_candidates_0',frozen_minutes=90,position='MID')])
        self.stats=pd.DataFrame([dict(match_id='m1',player_id='p1',minsPlayed=90,goalAssist=float('nan'),position='Striker',season='2020-2021')])
        self.alias=pd.DataFrame([dict(code=12,player_id='p1')])
    def test_verified_fixture_only(self):
        self.stats.loc[0,'match_id']='other'
        self.assertEqual(apply_aliases(self.target,self.stats,self.alias).iloc[0].mapping_status,'name_candidates_0')
    def test_missing_match_preserved(self):
        self.target.loc[0,'mapping_status']='missing_match'
        self.assertEqual(apply_aliases(self.target,self.stats,self.alias).iloc[0].mapping_status,'missing_match')
    def test_missing_counter_preserved(self):
        r=apply_aliases(self.target,self.stats,self.alias).iloc[0]
        self.assertTrue(pd.isna(r.goalAssist));self.assertEqual(r.player_id,'p1');self.assertEqual(r.mapping_status,'matched')
    def test_fpl_position_retained(self):
        self.assertEqual(apply_aliases(self.target,self.stats,self.alias).iloc[0].position,'MID')
    def test_existing_identity_conflict_rejected(self):
        self.target.loc[0,['mapping_status','player_id']]=['matched','other']
        with self.assertRaises(AssertionError):apply_aliases(self.target,self.stats,self.alias)
    def test_duplicate_alias_rejected(self):
        with self.assertRaises(AssertionError):apply_aliases(self.target,self.stats,pd.concat([self.alias,self.alias]))
    def test_duplicate_source_identity_rejected(self):
        with self.assertRaises(AssertionError):apply_aliases(self.target,pd.concat([self.stats,self.stats]),self.alias)
    def test_two_targets_cannot_share_provider_identity(self):
        target=pd.concat([self.target,self.target.assign(code=13)],ignore_index=True)
        alias=pd.concat([self.alias,self.alias.assign(code=13)],ignore_index=True)
        with self.assertRaises(AssertionError):apply_aliases(target,self.stats,alias)

if __name__=='__main__':unittest.main()
