from pathlib import Path
import json,sys,unittest
import pandas as pd
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P))
from build import qualified_seasons
class KeeperGateTests(unittest.TestCase):
    def test_one_native_disagreement_vetoes_all_historical_seasons(self):
        protocol=json.loads((P/'protocol.json').read_text())
        controls=pd.read_csv(P/'results/control_comparisons.csv')
        controls['agrees']=True
        good,native=qualified_seasons(controls,protocol)
        self.assertTrue(native);self.assertTrue(good.keeper_mapping_qualified.all())
        controls.loc[controls.season.eq('2025-26').idxmax(),'agrees']=False
        good,native=qualified_seasons(controls,protocol)
        self.assertFalse(native);self.assertFalse(good.keeper_mapping_qualified.any())
    def test_failed_pilot_never_changes_parent_requirement_rows(self):
        pointer=json.loads((P/'inputs/parent_CURRENT.json').read_text())
        before=pd.read_csv(P.parent.parent/pointer['requirements'],low_memory=False)
        after=pd.read_csv(P/'results/requirements.csv.xz',low_memory=False)
        pd.testing.assert_frame_equal(before,after)
    def test_six_native_exceptions_preserved(self):
        controls=pd.read_csv(P/'results/control_comparisons.csv')
        bad=controls[~controls.agrees]
        self.assertEqual(set(bad.fixture),{41,289,307,310,317,346})
        self.assertTrue(bad.kind.eq('native_fpl_keeper_cbi').all())
        self.assertFalse(json.loads((P/'results/findings.json').read_text())['native_fpl_gate_passed'])
if __name__=='__main__':unittest.main()
