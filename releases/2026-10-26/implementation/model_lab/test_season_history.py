import unittest
import pandas as pd
from model_lab.season_history import make_features, STATS

class SeasonBoundaryTests(unittest.TestCase):
    def row(self, season, fixture, minute, available):
        return dict(season=season, fixture=fixture, code=1, available=available,
                    **{s: minute if s=='minutes' else 0 for s in STATS})
    def origins(self, season='2026-27', at='2026-10-20T12:00:00Z'):
        return pd.DataFrame([dict(season=season, round=8, code=1, forecast_at=at)])
    def test_current_window_never_padded_with_prior_season(self):
        history = pd.DataFrame([self.row('2025-26',i,0,'2026-05-01T00:00:00Z') for i in range(5)]+
                               [self.row('2026-27',i+5,80,'2026-10-01T00:00:00Z') for i in range(7)])
        f=make_features(self.origins(),history).iloc[0]
        self.assertEqual(f.current_count_12,7)
        self.assertEqual(f.current_minutes_m12,80)
        self.assertEqual(f.prior_minutes_m12,0)
        self.assertEqual(f.prior_count_12,5)
    def test_true_zero_counts_but_unavailable_match_does_not(self):
        history=pd.DataFrame([self.row('2026-27',1,90,'2026-10-01T00:00:00Z'),
                              self.row('2026-27',2,0,'2026-10-02T00:00:00Z'),
                              self.row('2026-27',3,90,'2026-10-20T12:00:00Z')])
        f=make_features(self.origins(),history).iloc[0]
        self.assertEqual(f.current_count,2)
        self.assertEqual(f.current_minutes_m12,45)
    def test_season_start_missing_is_not_zero_and_gap_is_explicit(self):
        history=pd.DataFrame([self.row('2024-25',1,90,'2025-05-01T00:00:00Z')])
        f=make_features(self.origins(),history).iloc[0]
        self.assertTrue(f.current_missing)
        self.assertTrue(pd.isna(f.current_minutes_m12))
        self.assertEqual(f.prior_season,'2024-25')
        self.assertEqual(f.prior_season_gap,2)
        self.assertEqual(f.prior_minutes_m12,90)
    def test_future_result_cannot_change_features(self):
        h=pd.DataFrame([self.row('2026-27',1,70,'2026-10-01T00:00:00Z')])
        future=pd.DataFrame([self.row('2026-27',2,999,'2026-10-21T00:00:00Z')])
        pd.testing.assert_frame_equal(make_features(self.origins(),h),make_features(self.origins(),pd.concat([h,future])))

if __name__=='__main__': unittest.main()
