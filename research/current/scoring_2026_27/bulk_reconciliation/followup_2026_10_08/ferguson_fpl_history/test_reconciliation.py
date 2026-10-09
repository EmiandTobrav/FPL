import json,unittest
import pandas as pd
from prepare import P,B,K
class FPLHistoryTests(unittest.TestCase):
    def test_only_documented_six_factual_corrections(self):
        corrections=pd.read_csv(P/'results/native_fpl_corrections.csv.gz');self.assertEqual(len(corrections),6)
        self.assertEqual(set(corrections.fixture),{239});self.assertEqual(set(corrections.code),{487117})
        native=pd.read_csv(P/'inputs/native_player_season.csv.gz');after=pd.read_csv(P/'results/native_player_season_corrected.csv.gz')
        pd.testing.assert_frame_equal(native[native.fixture.ne(239)],after[after.fixture.ne(239)])
        self.assertEqual(native[native.fixture.eq(239)].minutes.iloc[0],0);self.assertEqual(after[after.fixture.eq(239)].minutes.iloc[0],17)
        self.assertTrue(native.bps.equals(after.bps))
    def test_season_totals_confirm_complete_history(self):
        totals=pd.read_csv(P/'results/season_total_checks.csv.gz');self.assertEqual(len(totals),19);self.assertTrue(totals.difference.abs().le(1e-8).all())
    def test_raw_BPS_and_other_ledger_values_preserved(self):
        parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());before=pd.read_csv(B/parent['requirements'],low_memory=False);after=pd.read_csv(P/'results/requirements.csv.xz',low_memory=False)
        mask=before.is_open & ~after.is_open;self.assertEqual(int(mask.sum()),1)
        self.assertEqual(before.loc[mask,'status'].iloc[0],'fpl_extract_exception');self.assertEqual(after.loc[mask,'value'].iloc[0],4)
        pd.testing.assert_frame_equal(before.loc[~mask],after.loc[~mask]);pd.testing.assert_series_equal(before.fpl,after.fpl);pd.testing.assert_series_equal(before.value,after.value)
    def test_native_snapshot_and_corrected_snapshot_distinct(self):
        history=pd.read_csv(P/'inputs/player_history.csv');gw=pd.read_csv(P/'inputs/gw24.csv')
        h=history[history.fixture.eq(239)].iloc[0];g=gw[gw.fixture.eq(239)&gw.element.eq(123)].iloc[0]
        self.assertEqual(h.bps,g.bps);self.assertEqual(h.total_points,1);self.assertEqual(g.total_points,0)
if __name__=='__main__':unittest.main()
