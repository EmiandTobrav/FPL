from pathlib import Path
import sys,pickle,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from upside.features import COLS,load_history,prediction_rows,design
from retrained_ensemble.models import estimators
OUT=HERE/'results'

def train_year(year):
    s=f'{year}-{str(year+1)[-2:]}'
    d,fixtures,th=load_history();train=design(d);t=time.time();audits=[]
    with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
    cut=pd.Timestamp(games[1]['cutoff']);tr=train[(train.season<s)&(train.available<cut)]
    frozen=estimators()
    for m in frozen.values():m.fit(tr[COLS],tr.historic)
    audits.append(dict(season=s,gw=1,kind='frozen_control',rows=len(tr),max_available=str(tr.available.max()),cutoff=str(cut),same_season_rows=0))
    rows=[];errors=[]
    for gw in range(5,39):
        g=games[gw];cut=pd.Timestamp(g['cutoff'])
        if (gw-5)%4==0:
            tr=train[(train.season<=s)&(train.available<cut)];models=estimators()
            for m in models.values():m.fit(tr[COLS],tr.historic)
            audits.append(dict(season=s,gw=gw,kind='refresh',rows=len(tr),max_available=str(tr.available.max()),cutoff=str(cut),same_season_rows=int((tr.season==s).sum())))
            pd.DataFrame(audits).to_csv(OUT/f'training_audit_{s}.csv',index=False)
            print('FIT',s,gw,'seconds',round(time.time()-t),flush=True)
        batch,p=prediction_rows(d,fixtures,th,g,s,gw)
        pred={k:np.zeros(len(p)) for k in ['ridge_refresh','extra_refresh','ridge_control','extra_control']}
        if not batch.empty:
            for name in ['ridge','extra']:
                np.add.at(pred[name+'_refresh'],batch._row,np.maximum(0,models[name].predict(batch[COLS])))
                np.add.at(pred[name+'_control'],batch._row,np.maximum(0,frozen[name].predict(batch[COLS])))
        for name in ['ridge','extra']:
            err=float(np.max(np.abs(pred[name+'_control']-g['pred'][name])));assert err<1e-5,(s,gw,name,err);errors.append(err)
        rows.append(pd.DataFrame(dict(season=s,gw=gw,pid=p.index,cutoff=g['cutoff'],**pred)))
    pd.concat(rows,ignore_index=True).to_csv(OUT/f'predictions_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.DataFrame([dict(season=s,control_max_difference=max(errors))]).to_csv(OUT/f'control_audit_{s}.csv',index=False)
    print('BUILT',s,'control_error',max(errors),'seconds',round(time.time()-t),flush=True)

def main():
    tasks=[y for y in range(2020,2026) if not (OUT/f'predictions_{y}-{str(y+1)[-2:]}.csv.gz').exists()]
    with ProcessPoolExecutor(max_workers=2) as ex:
        futures=[ex.submit(train_year,y) for y in tasks]
        for f in as_completed(futures):f.result()
    for name in ['training_audit','control_audit']:
        pd.concat([pd.read_csv(OUT/f'{name}_{y}-{str(y+1)[-2:]}.csv') for y in range(2020,2026)],ignore_index=True).to_csv(OUT/f'{name}.csv',index=False)
if __name__=='__main__':main()
