import json,unittest
import pandas as pd
from prepare import P,S,B,K
from build import aggregate_functions
class InventoryTests(unittest.TestCase):
    def test_new_inventories_do_not_copy_assists(self):
        goals=pd.read_csv(P/'goal_inventory.csv.gz');self.assertEqual(len(goals),75);self.assertTrue(goals.event_id.lt(0).all());self.assertTrue(goals.status.eq('unresolved').all());self.assertTrue(goals.recipient_player_id.isna().all())
        parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());old=pd.read_csv(B/parent['assist_goal_decisions']);after=pd.read_csv(P/'results/goal_decisions.csv.gz');pd.testing.assert_frame_equal(old,after.iloc[:len(old)].reset_index(drop=True))
    def test_own_goals_credit_opposing_team(self):
        goals=pd.read_csv(P/'goal_inventory.csv.gz');people=pd.read_csv(P/'participants.csv.gz')
        for g in goals[goals.own_goal].itertuples():
            player=people[people.match_id.eq(g.match_id)&people.player_id.eq(g.scorer_player_id)];self.assertEqual(len(player),1);self.assertNotEqual(player.team_id.iloc[0],g.scoring_team_id)
    def test_unknown_goal_context_is_not_no_assist(self):
        aggregate=aggregate_functions();g={'status':'unresolved','own_goal':False,'scorer_player_id':'fpl_player:1','event_id':-10}
        self.assertEqual(aggregate([g],'fpl_player:1',1,True)['value'],0);self.assertIsNone(aggregate([g],'fpl_player:2',1,True)['value']);self.assertIsNone(aggregate([g],'fpl_player:1',1,False)['value'])
    def test_filled_totals_all_zero_and_preserve_known(self):
        overlay=pd.read_csv(P/'results/overlay.csv.gz');self.assertEqual(len(overlay),20);self.assertTrue(overlay.value.eq(0).all())
        parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());old=pd.read_csv(B/parent['assist_totals'],low_memory=False);new=pd.read_csv(P/'results/player_match_totals.csv.gz',low_memory=False);x=old[old.value.notna()][K+['value']].merge(new[K+['value']],on=K,suffixes=('_old','_new'),validate='one_to_one');self.assertTrue(x.value_old.eq(x.value_new).all());self.assertEqual(len(x),67989)
    def test_inventory_reclassification_does_not_close_unknown_values(self):
        parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());old=pd.read_csv(B/parent['requirements'],low_memory=False);new=pd.read_csv(P/'results/requirements.csv.xz',low_memory=False)
        filled=old.is_open & ~new.is_open;reclassified=old.status.eq('missing_data') & new.status.eq('rule_recalculation');self.assertEqual(int(filled.sum()),20);self.assertEqual(int(reclassified.sum()),548);self.assertTrue(new.loc[reclassified,'value'].isna().all());self.assertTrue(new.loc[reclassified,'is_open'].all())
        pd.testing.assert_frame_equal(old.loc[~(filled|reclassified)],new.loc[~(filled|reclassified)])
        mutable={'value','status','is_open','is_zero','needs_external_quality_review','quality_status','provenance'};pd.testing.assert_frame_equal(old[[c for c in old if c not in mutable]],new[[c for c in new if c not in mutable]])
if __name__=='__main__':unittest.main()
