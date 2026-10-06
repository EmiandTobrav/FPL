from pathlib import Path
import sys
import numpy as np,pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/current'))
from adaptive_events.features import minute_category,residual_target,recent_weights

def test_minute_categories_respect_scoring_boundary():
    np.testing.assert_array_equal(minute_category([0,1,59,60,90]),[0,1,1,2,2])

def test_point_components_reconcile_even_for_rule_differences():
    d=pd.DataFrame(dict(minutes=[0,59,60,90],pos=[1,2,3,1],goals_scored=[0,1,1,1],assists=[0,0,1,0],clean_sheets=[0,0,1,1],historic=[0,7,13,18]))
    other=residual_target(d)
    appearance=(d.minutes>0).astype(int)+(d.minutes>=60).astype(int)
    reconstructed=appearance+d.goals_scored*d.pos.map({1:6,2:6,3:5,4:4})+3*d.assists+d.clean_sheets*d.pos.map({1:4,2:4,3:1,4:0})+other
    np.testing.assert_array_equal(reconstructed,d.historic)
    assert other.iloc[-1]==6 # residual includes any rule/bonus difference

def test_recent_weights_have_one_year_half_life_and_reject_future():
    cut=pd.Timestamp('2025-01-01',tz='UTC');dates=pd.Series([cut-pd.Timedelta(days=1),cut-pd.Timedelta(days=366)])
    w=recent_weights(dates,cut);assert np.isclose(w[1]/w[0],.5)
    import pytest
    with pytest.raises(AssertionError):recent_weights(pd.Series([cut]),cut)

def test_event_inference_marginalizes_minutes_without_reading_current_outcomes():
    from adaptive_events.models import Events
    from adaptive_events.features import RICH
    class Minutes:
        classes_=np.array([0,1,2])
        def __getitem__(self,key):return self
        def predict_proba(self,x):return np.tile([.2,.3,.5],(len(x),1))
    class Constant:
        def __init__(self,value):self.value=value
        def predict(self,x):return np.full(len(x),self.value)
    model=Events();model.minutes=Minutes();model.models={k:Constant(v) for k,v in {'goals':0,'assists':0,'clean':0,'other':0}.items()}
    x=pd.DataFrame(0.,index=[0,1],columns=RICH);x['pos']=[2,3];x['minutes']=[0,90];x['historic']=[0,20]
    before=model.predict(x);np.testing.assert_allclose(before,[1.3,1.3])
    x.minutes=[90,0];x.historic=[99,-5]
    np.testing.assert_array_equal(before,model.predict(x))
