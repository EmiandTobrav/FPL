from pathlib import Path
import json,shutil,sys,tempfile,unittest
import pandas as pd
P=Path(__file__).resolve().parent
sys.path.insert(0,str(P));sys.path.insert(0,str(P.parent))
from build import RK,horizon_targets,strict_sum
from pipeline import DatasetNotReady,load_dataset

class CanonicalTests(unittest.TestCase):
    def test_missing_round_is_not_blank_zero(self):
        q=pd.DataFrame([dict(season='2025-26',round=1,code=1,total_points_2026_27=2,scoring_qualified=True),
            dict(season='2025-26',round=3,code=1,total_points_2026_27=7,scoring_qualified=True)])
        result=horizon_targets(q)
        self.assertTrue(pd.isna(result.iloc[0].target_points_next_1_rounds))
        self.assertFalse(result.iloc[0].target_next_3_qualified)
    def test_horizon_does_not_cross_season_or_player(self):
        q=pd.DataFrame([dict(season='2025-26',round=38,code=1,total_points_2026_27=2,scoring_qualified=True),
            dict(season='2026-27',round=1,code=1,total_points_2026_27=7,scoring_qualified=True),
            dict(season='2026-27',round=2,code=2,total_points_2026_27=9,scoring_qualified=True)])
        result=horizon_targets(q)
        self.assertTrue(result.target_points_next_1_rounds.isna().all())
    def test_one_unqualified_round_blocks_entire_horizon(self):
        q=pd.DataFrame([dict(season='2025-26',round=i,code=1,total_points_2026_27=i,scoring_qualified=i!=3) for i in range(1,5)])
        result=horizon_targets(q)
        self.assertEqual(result.iloc[0].target_points_next_1_rounds,2)
        self.assertTrue(pd.isna(result.iloc[0].target_points_next_3_rounds))
    def test_partial_double_round_never_gets_partial_total(self):
        q=pd.DataFrame(dict(season=['2025-26']*2,round=[25]*2,code=[1]*2,points=[2,float('nan')]))
        group=q.groupby(RK)
        self.assertTrue(strict_sum(group,'points',group.size()).isna().all())
        q.loc[1,'points']=3;group=q.groupby(RK)
        self.assertEqual(strict_sum(group,'points',group.size()).iloc[0],5)
    def test_default_loader_refuses_training_before_features_qualified(self):
        with self.assertRaises(DatasetNotReady):load_dataset()
    def test_loader_rejects_wrong_points_standard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp)
            config=json.loads((P.parent/'ACTIVE.json').read_text());config['points_standard']='2025-26'
            (root/'ACTIVE.json').write_text(json.dumps(config))
            (root/'canonical/results').mkdir(parents=True)
            shutil.copy2(P/'results/manifest.json',root/'canonical/results/manifest.json')
            with self.assertRaises(ValueError):load_dataset(root,False)
    def test_published_all_seasons_original_and_qualified_targets_preserved(self):
        q=pd.read_csv(P/'results/player_matches.csv.xz',low_memory=False)
        self.assertEqual(q.season.nunique(),8)
        self.assertEqual(len(q),187111)
        self.assertTrue(q.loc[~q.scoring_qualified,'total_points_2026_27'].isna().all())
        self.assertEqual(int(q.scoring_qualified.sum()),12509)
        self.assertTrue(q.starts.notna().all())
        self.assertFalse(q.training_ready.any())
    def test_counters_preserve_open_missingness_and_native_zero(self):
        q=pd.read_csv(P/'results/input_counters.csv.xz',low_memory=False)
        self.assertEqual(int(q.is_open.sum()),14907)
        self.assertTrue(q.loc[q.is_open,'value'].isna().all())
        self.assertTrue(q.loc[~q.is_open,'value'].notna().all())
        self.assertTrue(q.loc[~q.is_open,'value'].eq(0).any())
        self.assertFalse(q.before_deadline_feature_qualified.any())
    def test_explicit_native_nonparticipation_labels_retained_without_eligibility_claim(self):
        q=pd.read_csv(P/'results/player_rounds.csv.xz',low_memory=False)
        dnp=q[q.season.eq('2026-27')&q.fixture_count.eq(0)]
        self.assertEqual(len(dnp),1678)
        self.assertTrue(dnp.scoring_qualified.all())
        self.assertTrue(dnp.total_points_2026_27.eq(0).all())
        self.assertFalse(dnp.deadline_eligible_universe_qualified.any())

if __name__=='__main__':unittest.main()
