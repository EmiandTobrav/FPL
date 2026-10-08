"""Exact conservation and full-ledger preservation, without point recalculation."""
import json
import unittest
import pandas as pd
from predict import P, B, K, exhaust

class SeasonBlockTests(unittest.TestCase):
    def test_missing_season_and_positive_residual_never_prove_zero(self):
        ids = list(range(38))
        for total in [None, float('nan'), -1, 1.5, True]:
            self.assertIsNone(exhaust(total, [None] * 38, ids)[0])
        self.assertIsNone(exhaust(2, [1] + [None] * 37, ids)[0])
        self.assertIsNone(exhaust(1, [2] + [None] * 37, ids)[0])
        self.assertIsNone(exhaust(1, [-1] + [None] * 37, ids)[0])

    def test_complete_unique_fixture_scope_required(self):
        ids = list(range(38))
        self.assertIsNone(exhaust(1, [1] + [None] * 36, ids[:-1])[0])
        self.assertIsNone(exhaust(1, [1] + [None] * 37, ids[:-1] + [0])[0])
        values, reason = exhaust(1, [1] + [None] * 37, ids)
        self.assertEqual(values, [1] + [0] * 37)
        self.assertEqual(reason, 'exact_season_exhaustion')

    def test_only_missing_goal_line_cells_changed_and_sources_preserved(self):
        parent = json.loads((P / 'inputs/parent_CURRENT.json').read_text())
        before = pd.read_csv(B / parent['requirements'], low_memory=False)
        after = pd.read_csv(P / 'results/requirements.csv.xz', low_memory=False)
        overlay = pd.read_csv(P / 'results/overlay.csv.gz')
        keys = pd.MultiIndex.from_frame(before[K])
        selected = before.field.eq('goal_line_clearances') & keys.isin(pd.MultiIndex.from_frame(overlay[K]))
        self.assertEqual(len(before), len(after))
        self.assertTrue(before.loc[selected, 'is_open'].all())
        self.assertTrue(before.loc[selected, 'status'].eq('missing_data').all())
        pd.testing.assert_frame_equal(before.loc[~selected], after.loc[~selected])
        preserved = ['fpl', 'fotmob', 'archive', 'primary', 'primary_followup', 'reconstruction',
                     'primary_acquisition', 'previous_value', 'previous_status']
        pd.testing.assert_frame_equal(before[preserved], after[preserved])
        self.assertTrue(after.loc[selected, 'value'].eq(0).all())
        self.assertTrue(after.loc[selected, 'needs_external_quality_review'].all())
        self.assertEqual(int(before.is_open.sum() - after.is_open.sum()), len(overlay))

    def test_all_eligible_season_groups_match_and_no_control_conflicts(self):
        summary = json.loads((P / 'results/findings.json').read_text())
        self.assertTrue(summary['validation']['qualified'])
        self.assertGreaterEqual(summary['validation']['closed_controls'], 1000)
        self.assertEqual(summary['validation']['closed_control_errors'], 0)
        self.assertEqual(summary['validation']['explicit_positive_conflicts'], 0)
        groups = pd.read_csv(P / 'season_conservation.csv')
        self.assertEqual(len(groups), 120)
        self.assertTrue(groups.fixtures.eq(38).all())
        eligible = groups[groups.qualified]
        self.assertTrue(eligible.known_match_sum.eq(eligible.explicit_season_total).all())

    def test_full_readiness_remains_input_only(self):
        summary = json.loads((P / 'results/findings.json').read_text())
        players = pd.read_csv(P / 'results/player_match_readiness.csv.xz')
        matches = pd.read_csv(P / 'results/match_readiness.csv')
        self.assertEqual(len(players), 77280)
        self.assertEqual(len(matches), 2660)
        self.assertEqual(int(players.open_fields.sum()), summary['open_fields'])
        self.assertEqual(int(players.inputs_available.sum()), summary['complete_player_matches'])
        self.assertEqual(int(matches.inputs_available.sum()), summary['complete_matches'])
        self.assertFalse(players.scoring_qualified.any())
        self.assertFalse(matches.bonus_ready.any())

if __name__ == '__main__':
    unittest.main()
