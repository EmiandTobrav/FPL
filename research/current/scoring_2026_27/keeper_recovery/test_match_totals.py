import unittest

from reconcile_match_totals import explicit_team_value, upper_bound


class MatchTotalsTests(unittest.TestCase):
    def test_sole_keeper_explicit_counter(self):
        self.assertEqual(explicit_team_value(1, 90, 2, 2, 1, 1), 1)

    def test_omission_is_not_zero(self):
        self.assertIsNone(explicit_team_value(1, 90, 2, 2, None, 1))
        self.assertEqual(upper_bound(4, None), 4)

    def test_substitution_cannot_allocate_team_counter(self):
        self.assertIsNone(explicit_team_value(2, 90, 2, 2, 1, 1))
        self.assertIsNone(explicit_team_value(1, 45, 2, 2, 1, 1))

    def test_conflicts_remain_unresolved(self):
        for args in [(1,90,2,3,1,1), (1,90,2,2,3,3), (1,90,2,2,1,2)]:
            self.assertIsNone(explicit_team_value(*args))

    def test_bounds_do_not_impute_counts(self):
        self.assertEqual(upper_bound(11, 3), 3)
        self.assertEqual(upper_bound(2, 5), 2)
        self.assertEqual(upper_bound(2, 0), 0)
        with self.assertRaises(ValueError):
            upper_bound(2, -1)


if __name__ == '__main__':
    unittest.main()
