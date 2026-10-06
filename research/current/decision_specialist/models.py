import numpy as np
from scipy.special import expit
from scipy.optimize import minimize
PRIOR=np.log(.5)

def gate_design(minutes6,minutes12):
    m=np.nan_to_num(np.asarray(minutes6,dtype=float),nan=0.)
    old=np.asarray(minutes12,dtype=float);old=np.where(np.isfinite(old),old,m)
    return np.column_stack([np.ones(len(m)),np.clip(m/90,0,1),np.clip((old-m)/90,0,1),((m>=30)&(m<70)).astype(float)])

def fit_gate(x,a,b,y,count,conditional=True):
    x=x if conditional else x[:,:1]
    prior=np.zeros(x.shape[1]);prior[0]=PRIOR
    weights=1+4*(np.maximum(a,b)/np.maximum(count,1)>=3)
    def objective(beta):
        w=expit(x@beta);error=a+w*(b-a)-y
        loss=np.average(error**2,weights=weights)+.01*np.sum((beta-prior)**2)
        gradient=2*x.T@(weights*error*(b-a)*w*(1-w))/weights.sum()+.02*(beta-prior)
        return loss,gradient
    result=minimize(objective,prior,jac=True,method='L-BFGS-B',bounds=[(-4,4)]*len(prior),options={'maxiter':500,'ftol':1e-12})
    assert result.success,result.message
    return result.x,float(result.fun)

def predict_gate(x,a,b,beta):
    w=expit(x[:,:len(beta)]@beta)
    return a+w*(b-a),w

def future_proxy(current,reference,count,reference_future1,horizon=3):
    """Uses current-deadline reference scenario, not outcomes/future game records."""
    current=np.asarray(current);reference=np.asarray(reference);count=np.asarray(count)
    per_reference=reference/np.maximum(count,1)
    neutral_reference=np.where(count>0,2*np.asarray(reference_future1)-per_reference,reference_future1)
    delta=np.where(count>0,(current-reference)/np.maximum(count,1),0)
    neutral=np.maximum(0,neutral_reference+delta)
    per=np.where(count>0,current/np.maximum(count,1),neutral)
    return np.column_stack([current]+[np.maximum(0,neutral+(per-neutral)*.5**j) for j in range(1,horizon)])
