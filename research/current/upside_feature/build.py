from pathlib import Path
import sys,json,pickle,time
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent
sys.path.insert(0,str(CURRENT))
from upside.features import COLS,load_history,prediction_rows,design
from upside.models import estimator,tail_target
OUT=HERE/'results'

def main():
    d,fixtures,th=load_history();train=design(d).reset_index(drop=True)
    train['tail_feature']=np.nan;audits=[];t=time.time()
    # Honest historical meta-features: a whole held-out season per expanding window.
    for year in range(2020,2025):
        season=f'{year}-{str(year+1)[-2:]}'
        with open(CURRENT/f'results/games_{season}.pkl','rb') as f:g=pickle.load(f)
        cut=pd.Timestamp(g[1]['cutoff'])
        fit=train[(train.season<season)&(train.available<cut)]
        mask=train.season==season
        model=estimator().fit(fit[COLS],tail_target(fit.historic))
        train.loc[mask,'tail_feature']=np.maximum(0,model.predict(train.loc[mask,COLS]))
        assert (fit.season<season).all() and fit.available.max()<cut
        audits.append(dict(kind='inner',season=season,rows=len(fit),max_season=fit.season.max(),max_available=str(fit.available.max()),cutoff=str(cut)))
        print('INNER',season,round(time.time()-t),flush=True)
    train.loc[train.tail_feature.notna(),['season','pid','available','tail_feature']].to_csv(OUT/'honest_training_features.csv.gz',index=True,compression={'method':'gzip','mtime':0})
    for year in range(2021,2026):
        season=f'{year}-{str(year+1)[-2:]}'
        with open(CURRENT/f'results/games_{season}.pkl','rb') as f:games=pickle.load(f)
        cut=pd.Timestamp(games[1]['cutoff'])
        tr=train[(train.season<season)&(train.available<cut)&train.tail_feature.notna()]
        base=estimator().fit(tr[COLS],tr.historic)
        augmented=estimator().fit(tr[COLS+['tail_feature']],tr.historic)
        earlier=train[(train.season<season)&(train.available<cut)]
        tail=estimator().fit(earlier[COLS],tail_target(earlier.historic))
        old=pd.read_csv(CURRENT/f'upside/results/predictions_{season}.csv.gz');rows=[];errors=[]
        for gw in range(5,39):
            game=games[gw];batch,p=prediction_rows(d,fixtures,th,game,season,gw)
            pred={k:np.zeros(len(p)) for k in ['matched_base','with_tail','tail']}
            if not batch.empty:
                batch['tail_feature']=np.maximum(0,tail.predict(batch[COLS]))
                np.add.at(pred['tail'],batch._row,batch.tail_feature)
                for name,model,cols in [('matched_base',base,COLS),('with_tail',augmented,COLS+['tail_feature'])]:
                    np.add.at(pred[name],batch._row,np.maximum(0,model.predict(batch[cols])))
            previous=old[old.gw==gw];assert np.array_equal(previous.pid,p.index)
            err=float(np.max(np.abs(previous['tail'].to_numpy()-pred['tail'])));assert err<1e-7;errors.append(err)
            rows.append(pd.DataFrame(dict(season=season,gw=gw,pid=p.index,cutoff=game['cutoff'],n_history=p.n_history.to_numpy(),**pred)))
        pd.concat(rows,ignore_index=True).to_csv(OUT/f'predictions_{season}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        audits.append(dict(kind='outer',season=season,rows=len(tr),max_season=tr.season.max(),max_available=str(tr.available.max()),cutoff=str(cut),tail_control_max=max(errors)))
        pd.DataFrame(audits).to_csv(OUT/'training_audit.csv',index=False)
        print('OUTER',season,len(tr),round(time.time()-t),flush=True)
if __name__=='__main__':main()
