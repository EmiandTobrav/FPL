from pathlib import Path
import sys,pickle,time
import numpy as np,pandas as pd
from sklearn.pipeline import make_pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge
from sklearn.ensemble import ExtraTreesRegressor,HistGradientBoostingClassifier
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from upside.features import COLS,load_history,prediction_rows,design
from upside.models import estimator
from horizon_upside.features import neutral_rows,horizon_forecast,combine
OUT=HERE/'results'

def main():
    d,fixtures,th=load_history();train=design(d);audits=[];t=time.time()
    for year in range(2020,2026):
        s=f'{year}-{str(year+1)[-2:]}'
        with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
        cut=pd.Timestamp(games[1]['cutoff']);tr=train[(train.season<s)&(train.available<cut)];high=tr.historic>=8
        models={'hgb':estimator(),'high':estimator(),'low':estimator()}
        models['hgb'].fit(tr[COLS],tr.historic)
        models['high'].fit(tr.loc[high,COLS],tr.loc[high,'historic']);models['low'].fit(tr.loc[~high,COLS],tr.loc[~high,'historic'])
        models['prob']=make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),HistGradientBoostingClassifier(max_iter=100,max_leaf_nodes=15,min_samples_leaf=60,l2_regularization=20,early_stopping=False,random_state=173)).fit(tr[COLS],high)
        for name,m in [('ridge',Ridge(alpha=100)),('extra',ExtraTreesRegressor(n_estimators=48,max_depth=12,min_samples_leaf=40,max_features=.8,n_jobs=1,random_state=173))]:
            models[name]=make_pipeline(SimpleImputer(add_indicator=True),StandardScaler(),m).fit(tr[COLS],tr.historic)
        def predict(x):
            z={name:np.maximum(0,models[name].predict(x[COLS])) for name in ['hgb','ridge','extra']}
            z['reference']=.5*z['ridge']+.5*z['extra']
            z['mixture']=combine(models['prob'].predict_proba(x[COLS])[:,1],models['high'].predict(x[COLS]),models['low'].predict(x[COLS]))
            return z
        rows=[];errors=[]
        for gw in range(5,39):
            g=games[gw];batch,p=prediction_rows(d,fixtures,th,g,s,gw)
            current={k:np.zeros(len(p)) for k in ['hgb','ridge','extra','reference','mixture']}
            if not batch.empty:
                for k,v in predict(batch).items():np.add.at(current[k],batch._row,v)
            neutral=predict(neutral_rows(p,th,pd.Timestamp(g['cutoff'])))
            for k in ['hgb','ridge','extra']:
                err=float(np.max(np.abs(current[k]-g['pred'][k])));assert err<1e-5,(s,gw,k,err);errors.append(err)
            # Reuse frozen current forecasts exactly after precision-tolerance validation.
            for k in ['hgb','ridge','extra']:current[k]=g['pred'][k]
            current['reference']=.5*g['pred']['ridge']+.5*g['pred']['extra']
            row=pd.DataFrame(dict(season=s,gw=gw,pid=p.index,cutoff=g['cutoff']))
            for k in ['hgb','reference','mixture']:
                pred=horizon_forecast(current[k],neutral[k],g['count'])
                for j in range(4):row[f'{k}_{j}']=pred[:,j]
            rows.append(row)
        pd.concat(rows,ignore_index=True).to_csv(OUT/f'forecasts_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        audits.append(dict(season=s,training_rows=len(tr),high_rows=int(high.sum()),training_max=str(tr.available.max()),cutoff=str(cut),control_max_difference=max(errors)))
        pd.DataFrame(audits).to_csv(OUT/'training_audit.csv',index=False);print('BUILT',s,round(time.time()-t),flush=True)
if __name__=='__main__':main()
