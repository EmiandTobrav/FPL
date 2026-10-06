from pathlib import Path
import sys
import numpy as np
from scipy.special import expit
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'research/current'))
from position_specialist.models import fit_position_weights,blend

def test_position_weights_learn_opposite_expert_strengths_and_pool_empty_groups():
    pos=np.repeat([1,2],200);a=np.zeros(400);b=np.full(400,4.);y=np.where(pos==1,0.,4.)
    beta,_=fit_position_weights(pos,a,b,y,np.ones(400),0.)
    assert expit(beta[0])<.1 and expit(beta[1])>.9
    np.testing.assert_allclose(beta[2:],0,atol=1e-12)

def test_no_expert_difference_returns_global_prior_and_convex_scores():
    a=np.array([1.,4.,2.,3.]);prior=.3
    beta,_=fit_position_weights([1,2,3,4],a,a,[10,0,5,-2],np.ones(4),prior)
    np.testing.assert_allclose(beta,prior,atol=1e-12)
    np.testing.assert_allclose(blend(a,a,expit(beta)),a)
    pred=blend(a,a+2,expit(beta));assert ((pred>=a)&(pred<=a+2)).all()
