"""Counter/identity failure guards and whole-ledger preservation checks."""
import json
import unittest
from types import SimpleNamespace
import pandas as pd
from predict import P, B, K, complete_player, complete_team, decode, identity_gate

class InventoryTests(unittest.TestCase):
    def test_missing_total_and_positive_residual_are_not_zero(self):
        for total in [None, float('nan'), -1, 1.5, True]:
            self.assertFalse(complete_team(total, 0, 0, 0, 0, 0))
        self.assertFalse(complete_team(3, 2, 0, 0, 0, 0))
        self.assertFalse(complete_player(None, 0, 0, 0))

    def test_inventory_requires_all_actor_and_qualifier_guards(self):
        self.assertTrue(complete_team(3, 3, 0, 0, 0, 0))
        for guard in range(4):
            flags = [0, 0, 0, 0]
            flags[guard] = 1
            self.assertFalse(complete_team(3, 3, *flags))
        self.assertFalse(complete_player(1, 1, 1, 0))
        self.assertFalse(complete_player(1, 1, 0, 1))

    def test_qualifier_omission_is_unknown(self):
        for value in [None, '', 'broken', '[]']:
            self.assertIsNone(decode(value))
        self.assertEqual(decode('{"94":null,"14":null}'), {'94': None, '14': None})

    def test_duration_exception_requires_fixture_and_player_identity(self):
        row=SimpleNamespace(season='2023-24', date='2024-01-01', kickoff_time='2024-01-01T12:00:00Z',
            home='Liverpool', away='Man City', team_h_score=1, team_a_score=1,
            was_home=True, historical_team='Liverpool', team_id='liverpool-uuid', minutes=60)
        official=SimpleNamespace(season='2023-2024', match_date='2024-01-01T12:00:00Z',
            team_position='home', team_name='Liverpool', minsPlayed=61)
        fixture=SimpleNamespace(season='2023-2024', match_date='2024-01-01T12:00:00Z',
            home_team='Liverpool', away_team='Manchester City', home_team_id='liverpool-uuid',
            away_team_id='city-uuid', home_score=1, away_score=1)
        self.assertTrue(identity_gate(row, official, fixture, 1, 2)[0])
        self.assertEqual(row.minutes,60)
        self.assertFalse(identity_gate(row, official, None, 1, 2)[0])
        for uuid_count, anchors in [(2,2),(1,1),(0,10)]:
            self.assertFalse(identity_gate(row, official, fixture, uuid_count, anchors)[0])
        for obj,field,value in [(row,'was_home',False),(row,'historical_team','Everton'),
            (row,'team_id','wrong'),(fixture,'away_team','Arsenal'),(fixture,'home_score',2),
            (fixture,'match_date','2024-01-02'),(official,'team_position','away'),
            (official,'minsPlayed',62),(official,'minsPlayed',0)]:
            old=getattr(obj,field);setattr(obj,field,value)
            self.assertFalse(identity_gate(row, official, fixture, 1, 2)[0],field)
            setattr(obj,field,old)
        official.minsPlayed=60
        self.assertFalse(identity_gate(row, official, fixture, 1, 2)[0]) # own exact match is not an independent anchor
        self.assertTrue(identity_gate(row, official, fixture, 1, 3)[0])

    def test_published_overlays_are_only_qualified_one_minute_rows(self):
        overlay=pd.read_csv(P/'results/overlay.csv.gz')
        self.assertTrue(overlay.minute_difference.abs().eq(1).all())
        self.assertTrue(overlay.native_minutes.gt(0).all())
        self.assertTrue(overlay.other_exact_minute_identity_anchors.ge(2).all())
        self.assertTrue(overlay.inventory_proof.isin(['explicit_player_block_total',
            'explicit_primary_team_block_total']).all())
        report=json.loads((P/'results/validation.json').read_text())
        self.assertGreaterEqual(report['one_minute_closed_controls'],1000)
        self.assertGreaterEqual(report['one_minute_explicit_positive_controls'],20)
        self.assertEqual(report['one_minute_closed_control_errors'],0)
        self.assertEqual(report['one_minute_explicit_control_errors'],0)
        self.assertTrue(overlay.season.isin(report['qualified_application_seasons']).all())

    def test_entire_ledger_only_missing_goal_line_rows_changed(self):
        parent = json.loads((P / 'inputs/parent_CURRENT.json').read_text())
        before = pd.read_csv(B / parent['requirements'], low_memory=False)
        after = pd.read_csv(P / 'results/requirements.csv.xz', low_memory=False)
        overlay = pd.read_csv(P / 'results/overlay.csv.gz')
        self.assertEqual(len(before), len(after))
        keys = pd.MultiIndex.from_frame(before[K])
        selected = (before.field.eq('goal_line_clearances') & keys.isin(pd.MultiIndex.from_frame(overlay[K])))
        self.assertTrue(before.loc[selected, 'is_open'].all())
        self.assertTrue(before.loc[selected, 'status'].eq('missing_data').all())
        pd.testing.assert_frame_equal(before.loc[~selected], after.loc[~selected])
        source_columns = ['fpl', 'fotmob', 'archive', 'primary', 'primary_followup',
                          'reconstruction', 'primary_acquisition', 'previous_value', 'previous_status']
        pd.testing.assert_frame_equal(before[source_columns], after[source_columns])
        self.assertTrue(after.loc[selected, 'needs_external_quality_review'].all())
        self.assertFalse(after.loc[selected, 'is_open'].any())
        self.assertEqual(int(before.is_open.sum() - after.is_open.sum()), len(overlay))

    def test_controls_and_readiness_cover_full_published_scope(self):
        report = json.loads((P / 'results/findings.json').read_text())
        self.assertTrue(report['validation']['qualified'])
        self.assertEqual(report['validation']['closed_control_errors'], 0)
        self.assertEqual(report['validation']['explicit_source_errors'], 0)
        req = pd.read_csv(P / 'results/requirements.csv.xz', usecols=K + ['is_open'])
        players = pd.read_csv(P / 'results/player_match_readiness.csv.xz')
        matches = pd.read_csv(P / 'results/match_readiness.csv')
        self.assertEqual(len(players), 77280)
        self.assertEqual(len(matches), 2660)
        self.assertEqual(int(req.is_open.sum()), report['open_fields'])
        self.assertEqual(int(players.inputs_available.sum()), report['complete_player_matches'])
        self.assertEqual(int(matches.inputs_available.sum()), report['complete_matches'])
        self.assertFalse(players.scoring_qualified.any())
        self.assertFalse(matches.bonus_ready.any())

if __name__ == '__main__':
    unittest.main()
