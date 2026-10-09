"""Whole-vector controls, physical-rule abstentions and full-data preservation."""
import ast,json,unittest,importlib.util
import pandas as pd
from prepare import P,S,B,K,digest
from build import aggregate_functions
spec=importlib.util.spec_from_file_location('unchanged_penalty_rule',S/'penalty_foul_recovery/rule.py')
rule=importlib.util.module_from_spec(spec);spec.loader.exec_module(rule)
class PenaltyTests(unittest.TestCase):
    def test_physical_rule_rejects_handball_missing_link_and_intervening_play(self):
        goal={'match_id':'match','event_id':30,'team_id':'home','player_id':'taker','period_id':1,'clock':1000,'qualifier_json':'{"9":null}'}
        rows=[dict(event_id=10,type_id=4,team_id='home',player_id='taker',outcome=1,period_id=1,clock=800,x=90,y=50,qualifier_json='{"9":null,"13":null,"348":"taker","233":"20"}'),
            dict(event_id=20,type_id=4,team_id='away',player_id='defender',outcome=0,period_id=1,clock=800,x=10,y=50,qualifier_json='{"9":null,"13":null,"233":"10"}'),
            dict(event_id=30,type_id=16,team_id='home',player_id='taker',outcome=1,period_id=1,clock=1000,x=88,y=50,qualifier_json='{"9":null}')]
        events=pd.DataFrame(rows);identities={('match','home','taker'):1}
        result=rule.classify(goal,events,identities)
        self.assertEqual(result['status'],'no_assist')
        for qualifiers in ['{"9":null,"13":null,"233":"20"}','{"9":null,"13":null,"348":"taker","233":"20","10":null}']:
            changed=events.copy();changed.loc[0,'qualifier_json']=qualifiers
            self.assertIsNone(rule.classify(goal,changed,identities))
        extra=dict(rows[0],event_id=25,type_id=1,clock=900)
        self.assertIsNone(rule.classify(goal,pd.concat([events,pd.DataFrame([extra])]),identities))
        self.assertIsNone(rule.classify(goal,events,{('match','home','taker'):2}))

    def test_unknown_other_goal_is_not_zero(self):
        aggregate=aggregate_functions()
        goals=[dict(status='no_assist',event_id=1),dict(status='unresolved',event_id=2,own_goal=False,scorer_player_id='other')]
        self.assertIsNone(aggregate(goals,'player',2,True)['value'])
        self.assertIsNone(aggregate(goals[:1],'player',2,True)['value'])
        self.assertEqual(aggregate(goals[:1],'player',1,True)['value'],0)

    def test_selection_does_not_read_native_assist_outcomes(self):
        tree=ast.parse((P/'prepare.py').read_text())
        calls=[node for node in ast.walk(tree) if isinstance(node,ast.Call) and isinstance(node.func,ast.Attribute) and node.func.attr=='read_csv']
        self.assertTrue(all('fpl_baseline' not in ast.unparse(node) for node in calls))
        self.assertFalse(json.loads((P/'prediction_freeze.json').read_text())['outcomes_read_by_selection'])
        self.assertEqual(digest(P/'predictions.csv.gz'),digest(S/'penalty_foul_recovery/predictions.csv.gz'))

    def test_all_control_vectors_and_rule_kinds_pass(self):
        report=json.loads((P/'results/validation.json').read_text())
        self.assertGreaterEqual(report['control_goals'],20)
        self.assertGreaterEqual(report['control_kinds']['self_won_penalty'],5)
        self.assertGreaterEqual(report['control_kinds']['ordinary_foul_penalty'],5)
        self.assertEqual(report['player_errors'],0)
        self.assertEqual(report['goal_vector_errors'],0)
        self.assertEqual(report['protected_conflicts'],0)
        self.assertEqual(report['candidate_denial_conflicts'],0)
        controls=pd.read_csv(P/'results/goal_vector_controls.csv')
        self.assertEqual(len(controls),report['control_goals'])
        self.assertTrue(controls.agrees.all())

    def test_approved_goals_and_known_assist_totals_are_preserved(self):
        old=pd.read_csv(S/'assist_touch_bounds/results/goal_decisions.csv.gz')
        new=pd.read_csv(P/'results/goal_decisions.csv.gz')
        applied=pd.read_csv(P/'results/applied_goal_decisions.csv')
        mask=pd.MultiIndex.from_frame(old[['match_id','event_id']]).isin(pd.MultiIndex.from_frame(applied[['match_id','event_id']]))
        self.assertTrue(old.loc[mask,'status'].eq('unresolved').all())
        self.assertTrue(applied.kind.eq('self_won_penalty').all())
        self.assertFalse(applied.season.eq('2025-26').any())
        pd.testing.assert_frame_equal(old.loc[~mask],new.loc[~mask])
        a=pd.read_csv(S/'assist_touch_bounds/results/player_match_totals.csv.gz',low_memory=False)
        b=pd.read_csv(P/'results/player_match_totals.csv.gz',low_memory=False)
        known=a[a.value.notna()][K+['value']].merge(b[K+['value']],on=K,validate='one_to_one',suffixes=('_old','_new'))
        self.assertTrue(known.value_old.eq(known.value_new).all())

    def test_only_empty_open_assist_ledger_values_change(self):
        parent=json.loads((P/'inputs/parent_CURRENT.json').read_text())
        old=pd.read_csv(B/parent['requirements'],low_memory=False);new=pd.read_csv(P/'results/requirements.csv.xz',low_memory=False)
        overlay=pd.read_csv(P/'results/overlay.csv.gz')
        mask=old.field.eq('assists_2026_27')&pd.MultiIndex.from_frame(old[K]).isin(pd.MultiIndex.from_frame(overlay[K]))
        self.assertTrue(old.loc[mask,'is_open'].all());self.assertTrue(old.loc[mask,'value'].isna().all())
        pd.testing.assert_frame_equal(old.loc[~mask],new.loc[~mask])
        fields=[col for col in old if col not in ['value','status','is_open','is_zero','provenance','quality_status','needs_external_quality_review']]
        pd.testing.assert_frame_equal(old[fields],new[fields])
        self.assertTrue(new.loc[mask,'needs_external_quality_review'].all())
        self.assertEqual(int(old.is_open.sum()-new.is_open.sum()),len(overlay))

    def test_full_readiness_and_output_hashes(self):
        report=json.loads((P/'results/findings.json').read_text())
        for name,sha in json.loads((P/'results/manifest.json').read_text()).items():self.assertEqual(digest(P/'results'/name),sha)
        pm=pd.read_csv(P/'results/player_match_readiness.csv.xz');matches=pd.read_csv(P/'results/match_readiness.csv')
        self.assertEqual(len(pm),77280);self.assertEqual(len(matches),2660)
        self.assertEqual(int(pm.inputs_available.sum()),report['complete_player_matches'])
        self.assertEqual(int(matches.inputs_available.sum()),report['complete_matches'])
        self.assertFalse(pm.scoring_qualified.any());self.assertFalse(matches.bonus_ready.any())
if __name__=='__main__':unittest.main()
