from pathlib import Path
import sys
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/current'))
from calendar_counts.features import count_forecast
from calendar_audit.selector import select_before

def test_snapshot_selection_rejects_future_author_or_committer_and_equal_cutoff():
    rows=[dict(sha='old',author_time='2024-01-01T00:00Z',committer_time='2024-01-01T00:00Z'),dict(sha='future_author',author_time='2024-01-04T00:00Z',committer_time='2024-01-02T00:00Z'),dict(sha='equal',author_time='2024-01-02T00:00Z',committer_time='2024-01-03T00:00Z')]
    assert select_before(rows,'2024-01-03T00:00Z')['sha']=='old'
    assert select_before(rows,'2023-01-01T00:00Z') is None

def test_calendar_counts_handle_double_blank_unassigned_and_stale():
    snap=pd.DataFrame(dict(event=[6,6,7,np.nan],team_h=[1,1,2,3],team_a=[2,3,3,1]));base=np.full((3,3),4.);codes={1:101,2:102,3:103}
    out=count_forecast(base,[101,102,103],snap,codes,5,2)
    np.testing.assert_array_equal(out,[[4,8,0],[4,4,4],[4,4,4]])
    np.testing.assert_array_equal(count_forecast(base,[101,102,103],snap,codes,5,14.01),base)
    # End-season columns outside planner horizon must remain untouched.
    np.testing.assert_array_equal(count_forecast(base,[101,102,103],snap,codes,38,2),base)
