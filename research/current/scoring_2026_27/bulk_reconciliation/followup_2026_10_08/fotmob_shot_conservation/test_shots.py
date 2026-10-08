import copy
import gzip
import json
from pathlib import Path
import unittest
import pandas as pd
from build import count, decode, residual_zero

P = Path(__file__).resolve().parent

class ConservationSafety(unittest.TestCase):
    def test_missing_total_never_certifies(self):
        self.assertFalse(residual_zero(None,[None,None]))

    def test_positive_residual_never_certifies(self):
        self.assertFalse(residual_zero(3,[1,None]))

    def test_excess_sum_never_certifies(self):
        self.assertFalse(residual_zero(1,[2,None]))

    def test_exhausted_explicit_total_certifies(self):
        self.assertTrue(residual_zero(3,[1,2,None]))
        self.assertTrue(residual_zero(0,[None,None]))

    def test_invalid_domain_rejected(self):
        for value in [-1,1.2,True,'0']:
            with self.subTest(value=value), self.assertRaises(ValueError):
                count(value)
        with self.assertRaises(ValueError):
            residual_zero(0,[-1,1])

class RawIdentitySafety(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        plan = pd.read_csv(P/'plan.csv')
        cls.row = plan[plan.fotmob_match_id.eq(4193786)].iloc[0].to_dict()
        cls.raw = json.loads(gzip.decompress((P/'inputs/raw/4193786.json.gz').read_bytes()))

    def test_missing_player_counter_stays_missing(self):
        players,totals = decode(self.row,json.dumps(self.raw).encode())
        self.assertEqual(totals['away'],0)
        self.assertTrue(any(p['explicit_sot'] is None for p in players if p['side']=='away'))

    def test_wrong_match_date_and_score_rejected(self):
        for field,value in [('date','2024-02-25'),('fotmob_match_id',1),('team_a_score',1)]:
            row = dict(self.row,**{field:value})
            with self.subTest(field=field), self.assertRaises(AssertionError):
                decode(row,json.dumps(self.raw).encode())

    def test_swapped_header_teams_rejected(self):
        raw = copy.deepcopy(self.raw)
        raw['header']['teams'].reverse()
        with self.assertRaises(AssertionError):
            decode(self.row,json.dumps(raw).encode())

    def test_contradictory_duplicate_totals_rejected(self):
        raw = copy.deepcopy(self.raw)
        for block in raw['content']['stats']['Periods']['All']['stats']:
            for metric in block['stats']:
                if metric.get('key')=='ShotsOnTarget':
                    metric['rawStats'][0]['value'] += 1
                    with self.assertRaises(AssertionError):
                        decode(self.row,json.dumps(raw).encode())
                    return
        self.fail('Fixture lacks explicit shot totals')

if __name__=='__main__':
    unittest.main()
