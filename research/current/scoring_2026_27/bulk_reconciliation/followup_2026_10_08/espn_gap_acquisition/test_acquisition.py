import json,unittest
import pandas as pd
from prepare import P,B,K,digest
from predict import count

class AcquisitionTests(unittest.TestCase):
    def test_unknown_or_invalid_counter_is_not_zero(self):
        for x in [None,'0',True,float('nan'),float('inf'),-1,0.5]:self.assertIsNone(count(x))
        self.assertEqual(count(0),0);self.assertEqual(count(3.0),3)

    def test_all_filled_counters_have_complete_goal_inventory(self):
        overlay=pd.read_csv(P/'results/overlay.csv.gz');gates=pd.read_csv(P/'fixture_gates.csv')
        joined=overlay.merge(gates,on=K[:2],validate='many_to_one')
        self.assertTrue(joined.complete.all());self.assertEqual(set(overlay.field),{'penalty_goals'})

    def test_failed_foul_source_is_withheld_globally(self):
        report=json.loads((P/'results/validation.json').read_text())
        self.assertGreater(report['fields']['fouls_won']['errors'],0)
        self.assertNotIn('fouls_won',report['qualified_fields'])

    def test_all_existing_values_and_native_columns_preserved(self):
        parent=json.loads((P/'inputs/parent_CURRENT.json').read_text())
        before=pd.read_csv(B/parent['requirements'],low_memory=False);after=pd.read_csv(P/'results/requirements.csv.xz',low_memory=False)
        changed=before.is_open & ~after.is_open
        self.assertEqual(int(changed.sum()),54)
        pd.testing.assert_frame_equal(before.loc[~changed],after.loc[~changed])
        mutable={'value','status','provenance','quality_status','needs_external_quality_review','is_open','is_zero'}
        columns=[c for c in before if c not in mutable]
        pd.testing.assert_frame_equal(before[columns],after[columns])
        self.assertTrue(before.loc[changed,'value'].isna().all());self.assertTrue(after.loc[changed,'needs_external_quality_review'].all())

    def test_selected_control_and_target_scopes_disjoint(self):
        plan=pd.read_csv(P/'plan.csv');self.assertFalse(plan.duplicated(K[:2]).any())
        self.assertEqual(plan.scope.value_counts().to_dict(),{'target':44,'control':30})
        freeze=json.loads((P/'selection_freeze.json').read_text());self.assertEqual(digest(P/'plan.csv'),freeze['plan_sha256'])

if __name__=='__main__':unittest.main()
