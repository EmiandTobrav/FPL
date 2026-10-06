from pathlib import Path
import sys
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/current'))
from retrained_ensemble.models import combine

def test_ensemble_weights_and_frozen_control_are_separate():
    r=np.array([3.,6.]);e=np.array([6.,3.]);h=np.array([9.,9.]);f=np.array([1.,1.])
    out=combine(r,e,h,f,2*f,3*f)
    np.testing.assert_allclose(out['re_refresh'],[4.5,4.5])
    np.testing.assert_allclose(out['three_refresh'],[6.,6.])
    np.testing.assert_allclose(out['three_frozen'],[2.,2.])
    changed=combine(r,e,h,100*f,200*f,300*f)
    np.testing.assert_array_equal(out['three_refresh'],changed['three_refresh'])
