import copy
from pathlib import Path
import unittest
from unittest.mock import patch

import current_season as current

P = Path(__file__).resolve().parent
SNAPSHOT = P / 'snapshots/2026_10_08'

class CurrentSeasonTests(unittest.TestCase):
    def test_bonus_shared_positions_and_negative_scores(self):
        self.assertEqual(current.award_bonus({1: 30, 2: 30, 3: 20, 4: 10}), {1: 3, 2: 3, 3: 1, 4: 0})
        self.assertEqual(current.award_bonus({1: 30, 2: 20, 3: 20, 4: 10}), {1: 3, 2: 2, 3: 2, 4: 0})
        self.assertEqual(current.award_bonus({1: 30, 2: 20, 3: 10, 4: 10}), {1: 3, 2: 2, 3: 1, 4: 1})
        self.assertEqual(current.award_bonus({1: -2, 2: -2, 3: -3, 4: -4}), {1: 3, 2: 3, 3: 1, 4: 0})

    def test_zero_bps_participants_are_included_in_snapshot(self):
        report = current.build(SNAPSHOT)
        import pandas as pd
        rows = pd.read_csv(SNAPSHOT / 'derived/player_matches.csv.gz')
        self.assertTrue(((rows.minutes > 0) & (rows.bps == 0)).any())
        self.assertEqual(report['player_matches'], len(rows))
        self.assertEqual(report['fixtures'], 50)
        self.assertEqual(report['finished_events'], [1, 2, 3, 4, 5])

    def test_unfinished_fixture_is_rejected(self):
        original = current.json_read
        def reader(path):
            data = original(path)
            if path.name == 'fixtures.json':
                data = copy.deepcopy(data)
                data[0]['finished'] = False
            return data
        with patch.object(current, 'json_read', side_effect=reader):
            with self.assertRaisesRegex(ValueError, 'unfinished fixtures'):
                current.build(SNAPSHOT)

    def test_changed_match_bps_is_rejected(self):
        original = current.json_read
        def reader(path):
            data = original(path)
            if path.name == 'fixtures.json':
                data = copy.deepcopy(data)
                bps = next(s for s in data[0]['stats'] if s['identifier'] == 'bps')
                bps['h'][0]['value'] += 1
            return data
        with patch.object(current, 'json_read', side_effect=reader):
            with self.assertRaisesRegex(ValueError, 'History/fixture BPS mismatch'):
                current.build(SNAPSHOT)

    def test_round_point_explanation_is_not_assumed_correct(self):
        original = current.json_read
        def reader(path):
            data = original(path)
            if path.name == 'event_1_live.json':
                data = copy.deepcopy(data)
                data['elements'][0]['explain'][0]['stats'][0]['points'] += 1
            return data
        with patch.object(current, 'json_read', side_effect=reader):
            with self.assertRaisesRegex(ValueError, 'Point accounting mismatch'):
                current.build(SNAPSHOT)

if __name__ == '__main__':
    unittest.main()
