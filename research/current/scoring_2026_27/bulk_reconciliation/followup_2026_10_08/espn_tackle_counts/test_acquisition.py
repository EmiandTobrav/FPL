import json,unittest
import pandas as pd
from prepare import P
from predict import number
class TackleTests(unittest.TestCase):
    def test_missing_invalid_or_boolean_not_zero(self):
        for x in [None,'0',True,float('nan'),float('inf'),-1,0.5]:self.assertIsNone(number(x))
        self.assertEqual(number(0),0);self.assertEqual(number(3.0),3)
    def test_signed_net_keeps_negative_values(self):
        p=pd.read_csv(P/'predictions.csv.gz');v=p.pivot(index=['season','fixture','code'],columns='field',values='value')
        pd.testing.assert_series_equal(v.legacy_net_tackles,2*v.won_tackles-v.total_tackles,check_names=False)
        self.assertTrue(v.legacy_net_tackles.lt(0).any())
    def test_minute_mismatches_have_no_predictions(self):
        g=pd.read_csv(P/'player_gates.csv');p=pd.read_csv(P/'predictions.csv.gz');keys=['season','fixture','code']
        bad=g[~g.eligible];self.assertEqual(len(bad),55);self.assertTrue(p.merge(bad[keys],on=keys).empty)
    def test_failed_mappings_never_fill_a_requirement(self):
        report=json.loads((P/'results/validation.json').read_text());self.assertEqual(report['qualified_fields'],[]);self.assertEqual(report['new_fields'],0)
        self.assertTrue(pd.read_csv(P/'results/overlay.csv.gz').empty)
        for field in report['fields'].values():self.assertGreater(field['errors'],0)
if __name__=='__main__':unittest.main()
