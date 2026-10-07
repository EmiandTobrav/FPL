import tempfile
import unittest
from pathlib import Path
from collect_resumable import normalize, run, atomic_json


class CollectionTests(unittest.TestCase):
    def setUp(self):
        self.row = dict(season='2024-25', fixture='1', code='123', pl_player_id='4', pulse_id='5')
        self.payload = dict(entity=dict(id=4, altIds=dict(opta='p123')),
                            stats=[dict(name='appearances', value=1), dict(name='mins_played', value=90)])

    def test_missing_stays_unknown_and_explicit_zero_survives(self):
        self.payload['stats'].append(dict(name='saves', value=0))
        row = normalize(self.payload, self.row)
        self.assertEqual(row['pl_saves'], 0)
        self.assertNotIn('pl_big_chance_saves', row)

    def test_wrong_identity_rejected(self):
        self.payload['entity']['altIds']['opta'] = 'p999'
        with self.assertRaises(ValueError):
            normalize(self.payload, self.row)

    def test_aggregate_rejected(self):
        self.payload['stats'][0]['value'] = 38
        with self.assertRaises(ValueError):
            normalize(self.payload, self.row)

    def test_duplicate_metrics_rejected(self):
        self.payload['stats'].append(dict(name='mins_played', value=91))
        with self.assertRaises(ValueError):
            normalize(self.payload, self.row)

    def test_changed_manifest_rejected_before_network(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p/'manifest.csv').write_text('season,fixture,code,pl_player_id,pulse_id\n2024-25,1,123,4,5\n')
            atomic_json(p/'output/checkpoint.json', dict(completed={}, errors={}, manifest_sha256='wrong'))
            with self.assertRaisesRegex(ValueError, 'manifest changed'):
                run(p/'manifest.csv', p/'output')


if __name__ == '__main__':
    unittest.main()
