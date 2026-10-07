import ast
import unittest
import pandas as pd
from build_assist_patch import build, P


class AssistPatchTests(unittest.TestCase):
    def setUp(self):
        root = P.parent.parent/'project/data'
        self.fixtures = pd.read_csv(root/'2024-25_fixtures.csv.gz')
        self.players = pd.read_csv(root/'2024-25_players.csv.gz')

    def test_official_positive_and_negative_examples(self):
        result = build(self.fixtures, self.players)
        self.assertEqual(set(result[result.assist_delta.eq(1)].element), {755,495,77,235})
        self.assertEqual(set(result[result.assist_delta.eq(0)].element), {366,541})
        self.assertEqual(result.direct_points_delta.sum(), 12)
        self.assertFalse(result.duplicated(['season','fixture','element']).any())

    def test_wrong_fixture_rejected(self):
        idx = self.fixtures.index[self.fixtures.id.eq(336)][0]
        stats = ast.literal_eval(self.fixtures.loc[idx,'stats'])
        next(s for s in stats if s['identifier']=='goals_scored')['h'] = []
        self.fixtures.loc[idx,'stats'] = repr(stats)
        with self.assertRaisesRegex(ValueError, 'goalscorer'):
            build(self.fixtures, self.players)

    def test_preexisting_correction_rejected(self):
        idx = self.fixtures.index[self.fixtures.id.eq(336)][0]
        stats = ast.literal_eval(self.fixtures.loc[idx,'stats'])
        next(s for s in stats if s['identifier']=='assists')['h'].append(dict(element=755,value=1))
        self.fixtures.loc[idx,'stats'] = repr(stats)
        with self.assertRaisesRegex(ValueError, 'double-add'):
            build(self.fixtures, self.players)


if __name__ == '__main__':
    unittest.main()
