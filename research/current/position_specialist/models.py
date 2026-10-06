import numpy as np
from scipy.special import expit
from scipy.optimize import minimize

def fit_position_weights(pos,a,b,y,count,global_beta):
    pos=np.asarray(pos,dtype=int)
    assert np.isin(pos,[1,2,3,4]).all()
    a,b,y,count=map(np.asarray,(a,b,y,count))
    relevance=1+4*(np.maximum(a,b)/np.maximum(count,1)>=3)
    def objective(beta):
        w=expit(beta[pos-1]);error=a+w*(b-a)-y
        loss=np.average(error**2,weights=relevance)+.01*np.sum((beta-global_beta)**2)
        per=2*relevance*error*(b-a)*w*(1-w)/relevance.sum()
        grad=np.bincount(pos-1,weights=per,minlength=4)+.02*(beta-global_beta)
        return loss,grad
    result=minimize(objective,np.full(4,global_beta),jac=True,method='L-BFGS-B',bounds=[(-4,4)]*4,options={'maxiter':500,'ftol':1e-12})
    assert result.success,result.message
    return result.x,float(result.fun)

def blend(a,b,weight):
    return np.asarray(a)+(np.asarray(b)-np.asarray(a))*weight
