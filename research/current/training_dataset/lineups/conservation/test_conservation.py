"""Check exhaustive-role deduction rejects incomplete and ambiguous inventories."""
import importlib.util
from pathlib import Path
import unittest

import pandas as pd

spec = importlib.util.spec_from_file_location('conservation_candidate_tests', Path(__file__).with_name('predict.py'))
candidate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(candidate)


def fixture():
    rows = []
    for side, offset in [(True, 0), (False, 100)]:
        for code in range(1, 12):
            rows.append(dict(season='test', fixture=1, code=code+offset, was_home=side, predicted_starts=1))
        rows.append(dict(season='test', fixture=1, code=12+offset, was_home=side, predicted_starts=None))
    return pd.DataFrame(rows)


class ConservationTests(unittest.TestCase):
    def test_exhaustive_elevens_prove_non_starts_without_minutes(self):
        frame, proof = candidate.conserve(fixture())
        self.assertEqual(frame.completed_starts.sum(), 22)
        self.assertEqual(frame.conservation_zero.sum(), 2)
        self.assertTrue(proof.complete.all())

    def test_twenty_two_on_one_side_is_not_a_complete_fixture(self):
        data = fixture()
        data.was_home = True
        with self.assertRaisesRegex(ValueError, 'Too many explicit starters'):
            candidate.conserve(data)

    def test_incomplete_single_side_does_not_fill_any_missing_value(self):
        data = fixture()
        data.loc[data.code.eq(1), 'predicted_starts'] = None
        frame, proof = candidate.conserve(data)
        self.assertEqual(frame.conservation_zero.sum(), 0)
        self.assertEqual(frame.completed_starts.isna().sum(), 3)
        self.assertFalse(proof.complete.any())

    def test_unknown_side_is_not_a_proof(self):
        data = fixture()
        data['was_home'] = data.was_home.astype(object)
        data.loc[data.code.eq(1), 'was_home'] = None
        with self.assertRaisesRegex(ValueError, 'identity'):
            candidate.conserve(data)

    def test_duplicate_identity_is_not_a_twelfth_player(self):
        data = pd.concat([fixture(), fixture().iloc[[0]]], ignore_index=True)
        with self.assertRaisesRegex(ValueError, 'identity'):
            candidate.conserve(data)

    def test_known_substitute_value_is_preserved(self):
        data = fixture()
        data.loc[data.code.eq(12), 'predicted_starts'] = 0
        frame, proof = candidate.conserve(data)
        row = frame[frame.code.eq(12)].iloc[0]
        self.assertEqual(row.completed_starts, 0)
        self.assertFalse(row.conservation_zero)


if __name__ == '__main__':
    unittest.main()
