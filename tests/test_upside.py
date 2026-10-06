from pathlib import Path
import sys
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/current'))
from upside.models import relevance_weights,tail_target

def test_tail_target_retains_full_haul_contribution_and_handles_negative_points():
    np.testing.assert_array_equal(tail_target([-3,0,7,8,20]),[0,0,0,8,20])

def test_relevance_weights_do_not_use_outcomes_or_player_identity():
    x=pd.DataFrame(dict(historic_m6=[0,4,2],minutes_m6=[0,90,45],n_history=[30,30,3],historic=[0,20,2],pid=[1,2,3]))
    before=relevance_weights(x);x.historic=[30,-3,0];x.pid=[2,3,1]
    np.testing.assert_array_equal(before,relevance_weights(x))
    assert np.all(before>=1) and before[1]>before[0] and before[2]>before[0]

def test_short_history_and_missing_features_keep_training_support():
    x=pd.DataFrame(dict(historic_m6=[np.nan,0],minutes_m6=[np.nan,0],n_history=[0,30]))
    w=relevance_weights(x)
    assert w[0]>w[1]>=1
