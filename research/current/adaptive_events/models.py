import numpy as np
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import HistGradientBoostingClassifier
from upside.models import estimator
from adaptive_events.features import RICH,minute_category,residual_target
MODELS=['hgb_refresh','hgb_recent','rich_frozen','rich_refresh','events_frozen','events_refresh','blend_events_direct','blend_three','blend_reference_mixture']

class Events:
    def fit(self,tr):
        cat=minute_category(tr.minutes)
        self.minutes=make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,min_samples_leaf=60,l2_regularization=20,early_stopping=False,random_state=173)).fit(tr[RICH],cat)
        x=tr.loc[cat>0,RICH].copy();x['long_category']=(cat[cat>0]==2).astype(int)
        targets={'goals':tr.goals_scored,'assists':tr.assists,'clean':tr.clean_sheets*tr.pos.map({1:4,2:4,3:1,4:0}),'other':residual_target(tr)}
        self.models={k:estimator().fit(x,y.loc[cat>0]) for k,y in targets.items()}
        return self
    def predict(self,x,diagnostics=False):
        p=self.minutes.predict_proba(x[RICH]);classes=self.minutes[-1].classes_
        probs={int(c):p[:,j] for j,c in enumerate(classes)}
        total=np.zeros(len(x));weights=x.pos.map({1:6,2:6,3:5,4:4}).to_numpy()
        for category in [1,2]:
            z=x[RICH].copy();z['long_category']=int(category==2)
            pred={k:m.predict(z) for k,m in self.models.items()}
            conditional=category+weights*np.maximum(0,pred['goals'])+3*np.maximum(0,pred['assists'])+np.clip(pred['clean'],0,x.pos.map({1:4,2:4,3:1,4:0}).to_numpy())+pred['other']
            total+=probs.get(category,np.zeros(len(x)))*conditional
        score=np.maximum(0,total)
        return (score,probs) if diagnostics else score
