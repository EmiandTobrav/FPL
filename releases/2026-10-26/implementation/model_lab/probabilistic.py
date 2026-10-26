"""Coherent categorical forecast heads, without outcome access at inference."""
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier, HistGradientBoostingRegressor
PARAMS=dict(max_iter=100,max_leaf_nodes=15,min_samples_leaf=60,l2_regularization=20,early_stopping=False,random_state=173)
POINT_EDGES=np.array([0,2,5,9])
def point_class(y): return np.searchsorted(POINT_EDGES,np.asarray(y),side='left')
def minute_class(minutes,any60): return np.where(np.asarray(minutes)==0,0,np.where(any60,2,1))
def check(p):
 p=np.asarray(p)
 if not np.isfinite(p).all() or (p<0).any() or not np.allclose(p.sum(axis=1),1):raise ValueError('Invalid probability distribution')
 return p
class Head:
 def __init__(self,k):self.k=k
 def fit(self,x,y):
  self.cols=x.columns[x.notna().any()].tolist(); y=np.asarray(y,dtype=int)
  if len(y)==0:raise ValueError('Empty stratum')
  self.classes=np.unique(y);self.model=None
  if len(self.classes)>1:self.model=HistGradientBoostingClassifier(**PARAMS).fit(x[self.cols],y)
  return self
 def predict(self,x):
  p=np.zeros((len(x),self.k));v=np.ones((len(x),1)) if self.model is None else self.model.predict_proba(x[self.cols]);p[:,self.classes]=v
  return check(p)
class ProbabilityModels:
 def fit(self,x,points,minutes,any60):
  c=minute_class(minutes,any60);pc=point_class(points)
  self.play=Head(2).fit(x,c>0);self.long=Head(2).fit(x[c>0],c[c>0]==2)
  self.direct_minutes=Head(3).fit(x,c)
  self.direct_points=Head(5).fit(x,pc)
  self.conditional=[Head(5).fit(x[c==i],pc[c==i]) for i in range(3)]
  self.minute_means=np.array([np.mean(np.asarray(minutes)[c==i]) for i in range(3)])
  self.minute_heads=[]
  for i in [1,2]:
   cols=x.columns[x[c==i].notna().any()].tolist()
   model=HistGradientBoostingRegressor(**PARAMS).fit(x.loc[c==i,cols],np.asarray(minutes)[c==i]);self.minute_heads.append((cols,model))
  return self
 def predict(self,x):
  p=self.play.predict(x)[:,1];q=self.long.predict(x)[:,1]
  gated=check(np.column_stack([1-p,p*(1-q),p*q]));direct=self.direct_minutes.predict(x)
  distributions=[h.predict(x) for h in self.conditional]
  mixed=check(sum(gated[:,i,None]*distributions[i] for i in range(3)))
  minute_values=[np.clip(model.predict(x[cols]),0,None) for cols,model in self.minute_heads]
  return dict(gated_minutes=gated,direct_minutes=direct,direct_points=self.direct_points.predict(x),conditional_points=mixed,
   constant_minutes=gated@self.minute_means,conditional_expected_minutes=gated[:,1]*minute_values[0]+gated[:,2]*minute_values[1])
def rps(p,y):
 return ((np.cumsum(p,axis=1)[:,:-1]-(np.asarray(y)[:,None]<=np.arange(p.shape[1]-1)))**2).mean(axis=1)
