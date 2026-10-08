"""Nonnegative conservation and protection of the real ledger population."""
import unittest
import math
import json
from pathlib import Path
import pandas as pd
from build import count, exhaust

P = Path(__file__).resolve().parent
B = P.parent.parent
K = ['season','fixture','code','field']

class Conservation(unittest.TestCase):
    def test_exhausted_total_proves_omitted_zero(self):
        self.assertEqual(exhaust([2,None,0,3],5,4,4),[2,0,0,3])

    def test_unallocated_positive_residual_is_unknown(self):
        with self.assertRaises(ValueError):
            exhaust([2,None],3,2,2)

    def test_missing_season_total_is_unknown(self):
        with self.assertRaises(ValueError):
            exhaust([0,None],None,2,2)

    def test_complete_appearance_inventory_is_required(self):
        for values, appearances in [([0],2),([0,None],3)]:
            with self.assertRaises(ValueError):
                exhaust(values,0,appearances,2)

    def test_invalid_counters_never_prove_zeros(self):
        for value in [False,-1,.5,math.inf,math.nan,'0']:
            with self.assertRaises(ValueError):
                count(value)

class LedgerIntegrity(unittest.TestCase):
    def test_only_missing_outside_fields_change(self):
        pointer = json.loads((P/'inputs/parent_CURRENT.json').read_text())
        before = pd.read_csv(B/pointer['requirements'],low_memory=False).set_index(K)
        after = pd.read_csv(P/'results/requirements.csv.xz',low_memory=False).set_index(K)
        changed = before.is_open & ~after.is_open
        self.assertTrue(before.loc[changed].status.eq('missing_data').all())
        self.assertEqual(set(before.loc[changed].index.get_level_values('field')),{'saves_outside_box'})
        pd.testing.assert_frame_equal(before.loc[~changed],after.loc[~changed],check_dtype=False)

    def test_no_unqualified_keeper_applied(self):
        q = pd.read_csv(P/'results/keeper_qualification.csv').set_index('code')
        changes = pd.read_csv(P/'results/derived_values.csv')
        self.assertTrue(q.loc[changes.code,'qualified'].all())
        good = q[q.qualified]
        self.assertTrue(good.control_disagreements.eq(0).all())
        self.assertTrue(good.inside_controls.ge(10).all())
        self.assertTrue(good.outside_controls.ge(10).all())

if __name__ == '__main__':
    unittest.main()
