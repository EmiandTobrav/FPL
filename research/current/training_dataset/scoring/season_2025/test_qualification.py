"""Qualification boundaries and the published complete-fixture view."""
from pathlib import Path
import json
import sys
import unittest

import pandas as pd

P = Path(__file__).resolve().parent
sys.path.insert(0,str(P))
from build import K, season_exhaustion, whole_fixture_eligible
sys.path.insert(0,str(P.parent))
from core import bps_changes

class QualificationTests(unittest.TestCase):
    def test_omitted_primary_count_requires_exact_exhaustion(self):
        self.assertEqual(season_exhaustion([1,None,2],3,3,3),[1,0,2])
        with self.assertRaises(ValueError):
            season_exhaustion([1,None,2],4,3,3)

    def test_incomplete_season_cannot_certify_omitted_zero(self):
        with self.assertRaises(ValueError):
            season_exhaustion([1,None],1,3,3)
        with self.assertRaises(ValueError):
            season_exhaustion([1,None,0],1,2,3)

    def test_negative_or_fractional_primary_count_cannot_certify(self):
        for invalid in [-1,0.5,True,float('nan')]:
            with self.assertRaises(ValueError):
                season_exhaustion([invalid,None],0,2,2)

    def fixture(self):
        return pd.DataFrame([dict(season='2025-26',fixture=1,code=i,minutes=90,
            historical_team_id=i//11,original_point_residual=0,kickoff_sources_agree=True)
            for i in range(22)])

    def test_new_source_revision_blocks_whole_fixture(self):
        group=self.fixture()
        keys=set(map(tuple,group[K].to_numpy()))
        self.assertTrue(whole_fixture_eligible(group,keys,set(),set()))
        self.assertFalse(whole_fixture_eligible(group,keys,set(),{1}))
        self.assertFalse(whole_fixture_eligible(group,keys,{1},set()))

    def test_zero_minute_card_participant_outside_ledger_blocks_fixture(self):
        group=self.fixture()
        keys=set(map(tuple,group[K].to_numpy()))
        extra=pd.DataFrame([dict(season='2025-26',fixture=1,code=99,minutes=0,
            historical_team_id=0,original_point_residual=0,kickoff_sources_agree=True)])
        group=pd.concat([group,extra],ignore_index=True)
        self.assertFalse(whole_fixture_eligible(group,keys,set(),set()))

    def test_new_any_save_term_does_not_require_location_sum(self):
        original=dict(season='2025-26',position='GK',saves=4,penalties_saved=1,assists=0)
        target=dict(clearances_blocks_interceptions=10,times_tackled=0,
            assists_2026_27=0,saves_inside_box=2,saves_outside_box=1,big_chance_saves=1)
        terms=bps_changes(original,target,None)
        self.assertEqual(terms['keeper_saves'],2)
        self.assertEqual(terms['cbi'],-2)
        self.assertNotIn('tackles',terms)

    def test_published_labels_are_complete_fixture_only(self):
        inv=pd.read_csv(P/'results/player_matches.csv.xz',low_memory=False)
        status=pd.read_csv(P/'results/fixture_status.csv')
        allowed=set(status[status.scoring_qualified].fixture)
        qualified=inv[inv.scoring_qualified]
        self.assertEqual(set(qualified.fixture),allowed)
        counts=inv[inv.scoring_relevant_inventory].groupby('fixture').size()
        self.assertEqual(qualified.groupby('fixture').size().to_dict(),counts.loc[sorted(allowed)].to_dict())
        self.assertTrue(inv.loc[~inv.scoring_qualified,'total_points_2026_27'].isna().all())
        self.assertFalse(inv.training_ready.any())
        self.assertFalse(inv.loc[~inv.scoring_relevant_inventory,'scoring_qualified'].any())
        self.assertTrue(qualified.times_tackled.notna().all())
        keepers=qualified[qualified.position.eq('GK')]
        self.assertTrue(keepers[['saves_inside_box','saves_outside_box','big_chance_saves']].notna().all().all())
        self.assertTrue(qualified.loc[qualified.position.ne('GK'),'big_chance_saves'].isna().all())

    def test_published_bps_rank_and_basic_account_agree(self):
        q=pd.read_csv(P/'results/qualified_player_matches.csv.xz',low_memory=False)
        account=pd.read_csv(P/'results/basic_components.csv.xz')
        self.assertTrue(account.residual.eq(0).all())
        fields=set(account.columns)-set(K)-{'bonus','total_points_2026_27','residual'}
        self.assertTrue((account[list(fields)].sum(axis=1)+account.bonus).eq(account.total_points_2026_27).all())
        # Ranking check uses pandas rank, independently of the scorer's count loop.
        ranks=q.groupby('fixture').bps_2026_27.rank(method='min',ascending=False)
        expected=(4-ranks).clip(lower=0)
        self.assertTrue(expected.eq(q.bonus_2026_27).all())
        self.assertTrue((q.total_points-q.bonus+q.bonus_2026_27).eq(q.total_points_2026_27).all())

    def test_protected_keeper_revision_and_doku_conflict_remain_missing(self):
        q=pd.read_csv(P/'results/player_matches.csv.xz',low_memory=False)
        self.assertTrue(q[q.fixture.isin([337,356])].total_points_2026_27.isna().all())
        comparisons=pd.read_csv(P/'results/keeper_primary_comparisons.csv')
        revision=comparisons[~comparisons.agrees]
        self.assertEqual(revision.fixture.tolist(),[337])
        self.assertEqual(revision.approved_value.tolist(),[0])
        self.assertEqual(revision.primary_proved.tolist(),[1])
        summary=json.loads((P/'results/summary.json').read_text())
        self.assertEqual(summary['approved_keeper_values_modified'],0)

if __name__=='__main__':
    unittest.main()
