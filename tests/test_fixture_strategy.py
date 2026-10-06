import sys
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/current'))
from fixture_strategy.features import assemble,effect

def test_fixture_aggregation_and_fallback():
    base=np.array([[4.,3.,2.5],[3.,2.,1.5]])
    cur=np.array([1.,-.5]);fx={1:[np.array([.5,np.nan]),np.array([-.5,np.nan])],2:[]}
    result=assemble(base,cur,fx,1)
    np.testing.assert_array_equal(result[:,0],base[:,0])
    np.testing.assert_allclose(result[:,1],[5,0]);np.testing.assert_array_equal(result[:,2],0)
    np.testing.assert_array_equal(assemble(base,cur,fx,15),base)

def test_separate_effects_minutes_and_clipping():
    coefficients={2:[0,0,0,0,0,1,2,-1]}
    pos=np.array([2,2]);minutes=np.array([90,0])
    np.testing.assert_allclose(effect(pos,minutes,1,1.85,1.85,coefficients,'venue'),[.5,0])
    np.testing.assert_allclose(effect(pos,minutes,1,1.85,1.85,coefficients,'opponent'),[.5,0])
    np.testing.assert_allclose(effect(pos,minutes,1,1.85,1.85,coefficients,'full'),[1,0])
    np.testing.assert_array_equal(effect(pos,minutes,1,1.85,1.85,coefficients,'count'),[0,0])
    np.testing.assert_allclose(effect(pos,minutes,1,100,1,coefficients,'full'),[2,0])

if __name__=='__main__':
    test_fixture_aggregation_and_fallback();test_separate_effects_minutes_and_clipping();print('2 feature tests passed')

def test_chip_opportunity_expiry_and_free_hit_restoration():
    import pandas as pd
    from fixture_strategy.chips import decide,advance
    p=pd.DataFrame({'pid':range(1,16),'pos':[1]*2+[2]*5+[3]*5+[4]*3,'club':[i%5 for i in range(15)],'market':[50]*15,'can_buy':[True]*15})
    state={'owned':{i:50 for i in range(1,16)},'bank':0,'ft':1}
    xp=np.full((15,8),3.);xp[:,1]=10
    chip,choice,audit,_=decide(p,xp,state,5,{}, {'triple_captain'},None)
    assert chip is None and audit[0]['future_value']>audit[0]['gain']
    chip,choice,audit,_=decide(p,xp,state,19,{}, {'triple_captain'},None)
    assert chip=='triple_captain'
    temporary=dict(choice,squad=set(range(101,116)),prices={i:40 for i in range(101,116)},bank_after=150,transfers=15)
    assert advance(state,temporary,'free_hit')==state
    chip,_,_,_=decide(p,xp,state,18,{18:'bench_boost'}, {'triple_captain'},None)
    assert chip=='bench_boost'

if __name__=='__main__':
    test_chip_opportunity_expiry_and_free_hit_restoration();print('Chip opportunity, expiry, reservation and restoration tests passed')
