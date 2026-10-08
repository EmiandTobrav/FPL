"""Source identity and semantic checks are separate from dataset approval."""
import unittest

import pandas as pd

from build import differences, K


class HistoryCompatibilityTests(unittest.TestCase):
    def test_key_fields_are_not_compared_as_absent_suffixed_columns(self):
        data = pd.DataFrame([dict(season='2022-23', fixture=1, code=1,
            element=10, element_source=10)])
        self.assertTrue(differences(data, ['fixture','element']).empty)

    def test_minute_change_remains_an_explicit_conflict(self):
        data = pd.DataFrame([dict(season='2022-23', fixture=1, code=1,
            minutes=90, minutes_source=89)])
        result = differences(data, ['minutes'])
        self.assertEqual(len(result), 1)
        self.assertEqual(result.iloc[0].original, 90)
        self.assertEqual(result.iloc[0].source, 89)

    def test_absent_source_value_is_not_zero(self):
        data = pd.DataFrame([dict(season='2022-23', fixture=1, code=1,
            saves=0, saves_source=None)])
        result = differences(data, ['saves'])
        self.assertEqual(len(result), 1)


if __name__ == '__main__':
    unittest.main()
