from pathlib import Path
import sys,pickle,time,warnings
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from adaptive_events.features import COLS,RICH,load_history,training_design,prediction_rows,recent_weights
from adaptive_events.models import Events
from upside.models import estimator
OUT=HERE/'results'

def train_year(year):
    warnings.filterwarnings('ignore',message='Skipping features without any observed values')
    d,fixtures,th=load_history();train=training_design(d);audits=[];t=time.time()
    for year in [year]:
        s=f'{year}-{str(year+1)[-2:]}'
        with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
        cut=pd.Timestamp(games[1]['cutoff']);tr=train[(train.season<s)&(train.available<cut)]
        control=estimator().fit(tr[COLS],tr.historic)
        frozen_rich=estimator().fit(tr[RICH],tr.historic);frozen_events=Events().fit(tr)
        audits.append(dict(season=s,gw=1,kind='frozen',rows=len(tr),max_available=str(tr.available.max()),cutoff=str(cut),same_season_rows=0))
        rows=[];errors=[]
        for gw in range(5,39):
            g=games[gw];cut=pd.Timestamp(g['cutoff'])
            if (gw-5)%4==0:
                tr=train[(train.season<=s)&(train.available<cut)]
                refresh=estimator().fit(tr[COLS],tr.historic)
                recent=estimator().fit(tr[COLS],tr.historic,histgradientboostingregressor__sample_weight=recent_weights(tr.available,cut))
                rich=estimator().fit(tr[RICH],tr.historic);events=Events().fit(tr)
                audits.append(dict(season=s,gw=gw,kind='refresh',rows=len(tr),max_available=str(tr.available.max()),cutoff=str(cut),same_season_rows=int((tr.season==s).sum())))
                pd.DataFrame(audits).to_csv(OUT/f'training_audit_{s}.csv',index=False)
                print('FIT',s,gw,len(tr),'seconds',round(time.time()-t),flush=True)
            batch,p=prediction_rows(d,fixtures,th,g,s,gw)
            estimators=[('control',control,COLS),('hgb_refresh',refresh,COLS),('hgb_recent',recent,COLS),('rich_frozen',frozen_rich,RICH),('rich_refresh',rich,RICH)]
            pred={k:np.zeros(len(p)) for k in [x[0] for x in estimators]+['events_frozen','events_refresh','p_play_sum','p_60_sum']}
            if not batch.empty:
                for name,m,cols in estimators:np.add.at(pred[name],batch._row,np.maximum(0,m.predict(batch[cols])))
                np.add.at(pred['events_frozen'],batch._row,frozen_events.predict(batch))
                scores,probs=events.predict(batch,True);np.add.at(pred['events_refresh'],batch._row,scores)
                np.add.at(pred['p_play_sum'],batch._row,1-probs[0]);np.add.at(pred['p_60_sum'],batch._row,probs[2])
            err=float(np.max(np.abs(pred['control']-g['pred']['hgb'])));assert err<1e-7,(s,gw,err);errors.append(err)
            rows.append(pd.DataFrame(dict(season=s,gw=gw,pid=p.index,cutoff=g['cutoff'],n_history=p.n_history.to_numpy(),**pred)))
        pd.concat(rows,ignore_index=True).to_csv(OUT/f'predictions_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        print('BUILT',s,'control_error',max(errors),'seconds',round(time.time()-t),flush=True)
def main():
    from concurrent.futures import ProcessPoolExecutor,as_completed
    tasks=[]
    for year in range(2020,2026):
        season=f'{year}-{str(year+1)[-2:]}'
        if (OUT/f'predictions_{season}.csv.gz').exists() and (OUT/f'training_audit_{season}.csv').exists():
            print('CACHED',season,flush=True)
        else:tasks.append(year)
    with ProcessPoolExecutor(max_workers=2) as ex:
        futures=[ex.submit(train_year,year) for year in tasks]
        for f in as_completed(futures):f.result()
    pd.concat([pd.read_csv(OUT/f'training_audit_{year}-{str(year+1)[-2:]}.csv') for year in range(2020,2026)],ignore_index=True).to_csv(OUT/'training_audit.csv',index=False)
if __name__=='__main__':main()
