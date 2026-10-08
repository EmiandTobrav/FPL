"""Protect frozen scores, unresolved whole fixtures and active ingestion."""
from pathlib import Path
import sys
import unittest
import pandas as pd

P = Path(__file__).resolve().parent
T = P.parent
sys.path.insert(0,str(T))
from pipeline import load_dataset, DatasetNotReady
K = ['season','fixture','code']

class Integration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = load_dataset(require_training_ready=False)
        cls.pm = cls.data['player_matches'].set_index(K)
        cls.old = pd.read_csv(T/'canonical/results/player_matches.csv.xz',low_memory=False).set_index(K)

    def test_all_original_observations_and_old_labels_preserved(self):
        self.assertEqual(set(self.pm.index),set(self.old.index))
        pd.testing.assert_series_equal(self.old.original_total_points,self.pm.original_total_points)
        excluded = (self.old.index.get_level_values('season')=='2025-26') & (self.old.index.get_level_values('fixture')==365)
        keys = self.old.index[self.old.scoring_qualified & ~excluded]
        removed = self.old.index[self.old.scoring_qualified & ~self.pm.scoring_qualified]
        self.assertEqual(set(removed),set(self.old.index[self.old.scoring_qualified & excluded]))
        pd.testing.assert_frame_equal(self.old.loc[keys,['total_points_2026_27','bonus_2026_27','bps_2026_27']],
            self.pm.loc[keys,['total_points_2026_27','bonus_2026_27','bps_2026_27']])

    def test_protected_whole_fixtures_have_no_harmonized_targets(self):
        blocked = self.pm.reset_index()
        blocked = blocked[blocked.season.eq('2025-26') & blocked.fixture.isin([33,215,323,337,356,365])]
        self.assertFalse(blocked.scoring_qualified.any())
        self.assertTrue(blocked.total_points_2026_27.isna().all())
        barnes = blocked[blocked.fixture.eq(215)&blocked.code.eq(44699)]
        self.assertEqual(len(barnes),1)
        self.assertEqual(barnes.original_total_points.iloc[0],-1)
        counters = self.data['input_counters']
        approved = counters[counters.season.eq('2025-26') & counters.fixture.eq(365)
            & counters.code.eq(215059) & counters.field.eq('big_chance_saves')]
        self.assertEqual(approved.value.iloc[0],1)
        self.assertFalse(approved.value_qualified_for_scoring.iloc[0])

    def test_active_ingestion_includes_all_eight_seasons(self):
        self.assertEqual(self.data['manifest']['version'],'fpl_2026_27_canonical_v3_partial')
        self.assertEqual(len(self.pm.index.get_level_values('season').unique()),8)
        self.assertEqual(self.pm.scoring_qualified.sum(),self.data['manifest']['counts']['qualified_player_match_labels'])

    def test_partial_double_rounds_do_not_publish_partial_targets(self):
        rounds = self.data['player_rounds']
        historical = rounds[rounds.season.ne('2026-27')]
        self.assertTrue(historical.loc[~historical.scoring_qualified,'total_points_2026_27'].isna().all())

    def test_training_stays_blocked_until_deadline_features_are_qualified(self):
        with self.assertRaises(DatasetNotReady):
            load_dataset()
        self.assertFalse(self.data['player_rounds'].training_ready.any())

if __name__ == '__main__':
    unittest.main()
