import json,unittest
import pandas as pd
from prepare import P,B,K,digest
from build import aggregate_functions
class LastInventoryTests(unittest.TestCase):
    def test_same_qualified_source_parser_and_complete_native_goal_vector(self):
        q=P/'source_projection';f=json.loads((q/'selection_freeze.json').read_text());self.assertEqual(digest(q/'predict.py'),f['qualified_parser_sha256'])
        gate=pd.read_csv(q/'fixture_gates.csv');self.assertTrue(gate.complete.all());self.assertEqual(gate.scoring_events.iloc[0],1);self.assertEqual(gate.mapped_players.iloc[0],30)
    def test_complete_inventory_does_not_infer_other_assists(self):
        g=pd.read_csv(P/'goal_inventory.csv.gz');self.assertEqual(len(g),1);self.assertTrue(g.status.eq('unresolved').all());self.assertTrue(g.recipient_player_id.isna().all())
        goal=g.iloc[0].to_dict();aggregate=aggregate_functions();self.assertEqual(aggregate([goal],goal['scorer_player_id'],1,True)['value'],0);self.assertIsNone(aggregate([goal],'another_player',1,True)['value'])
    def test_previous_inventories_ids_and_known_totals_preserved(self):
        c=json.loads((P/'inputs/parent_CURRENT.json').read_text());old=pd.read_csv(B/c['assist_goal_decisions']);new=pd.read_csv(P/'results/goal_decisions.csv.gz');pd.testing.assert_frame_equal(old,new.iloc[:len(old)].reset_index(drop=True))
        op=pd.read_csv(B/c['assist_participants']);np=pd.read_csv(P/'participants.csv.gz')
        for field in ['match_id','team_id','player_id']:pd.testing.assert_series_equal(op.loc[op[field].notna(),field],np.loc[op[field].notna(),field])
        prior=pd.read_csv(B/c['assist_totals'],low_memory=False);now=pd.read_csv(P/'results/player_match_totals.csv.gz',low_memory=False);known=prior[prior.value.notna()][K+['value']].merge(now[K+['value']],on=K,suffixes=('_old','_new'),validate='one_to_one');self.assertEqual(len(known),68009);self.assertTrue(known.value_old.eq(known.value_new).all())
    def test_only_one_closure_fourteen_still_open_and_raw_preserved(self):
        c=json.loads((P/'inputs/parent_CURRENT.json').read_text());old=pd.read_csv(B/c['requirements'],low_memory=False);new=pd.read_csv(P/'results/requirements.csv.xz',low_memory=False);filled=old.is_open&~new.is_open;reclass=old.status.eq('missing_data')&new.status.eq('rule_recalculation')
        self.assertEqual(int(filled.sum()),1);self.assertEqual(int(reclass.sum()),14);self.assertEqual(new.loc[filled,'value'].iloc[0],0);self.assertTrue(new.loc[reclass,'is_open'].all());self.assertTrue(new.loc[reclass,'value'].isna().all())
        pd.testing.assert_frame_equal(old.loc[~(filled|reclass)],new.loc[~(filled|reclass)])
        cols=[x for x in old if x not in ['value','status','is_open','is_zero','needs_external_quality_review','quality_status','provenance']];pd.testing.assert_frame_equal(old[cols],new[cols])
    def test_cumulative_coverage_is_retained(self):
        cover=pd.read_csv(P/'results/team_coverage_supplement.csv.gz');goals=pd.read_csv(P/'results/source_goal_inventories.csv.gz');self.assertEqual(len(cover),48);self.assertEqual(len(goals),76);self.assertFalse(cover.duplicated(['match_id','team_id']).any());self.assertTrue(goals.event_id.is_unique)
if __name__=='__main__':unittest.main()
