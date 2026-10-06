from pathlib import Path
import sys,json,pickle,time
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parent))
from features import CURRENT,COLS,load_history,prediction_rows,design
from models import estimator,tail_target,relevance_weights
OUT=Path(__file__).resolve().parent/'results'

def main():
    OUT.mkdir(exist_ok=True);d,fixtures,th=load_history();train=design(d);audits=[];t=time.time()
    for year in range(2020,2026):
        season=f'{year}-{str(year+1)[-2:]}'
        with open(CURRENT/f'results/games_{season}.pkl','rb') as f:games=pickle.load(f)
        cut=pd.Timestamp(games[1]['cutoff'])
        tr=train[(train.season<season)&(train.available<cut)]
        weights=relevance_weights(tr)
        mean=estimator().fit(tr[COLS],tr.historic)
        tail=estimator().fit(tr[COLS],tail_target(tr.historic))
        weighted=estimator().fit(tr[COLS],tr.historic,
            histgradientboostingregressor__sample_weight=weights)
        rows=[];errors=[]
        for gw in range(5,39):
            game=games[gw];batch,p=prediction_rows(d,fixtures,th,game,season,gw)
            predictions={n:np.zeros(len(p)) for n in ['tail','weighted','control']}
            if not batch.empty:
                for n,m in [('tail',tail),('weighted',weighted),('control',mean)]:
                    np.add.at(predictions[n],batch._row,np.maximum(0,m.predict(batch[COLS])))
            difference=float(np.max(np.abs(predictions['control']-game['pred']['hgb'])))
            assert difference<1e-7,(season,gw,difference)
            errors.append(difference)
            row=pd.DataFrame(dict(season=season,gw=gw,pid=p.index,n_history=p.n_history.to_numpy(),
                cutoff=game['cutoff'],**predictions));rows.append(row)
        pd.concat(rows,ignore_index=True).to_csv(OUT/f'predictions_{season}.csv.gz',index=False,
            compression={'method':'gzip','mtime':0})
        audits.append(dict(season=season,training_rows=len(tr),training_max=str(tr.available.max()),
            first_cutoff=str(cut),control_max_difference=max(errors),min_weight=float(weights.min()),
            max_weight=float(weights.max()),training_hauls=int((tr.historic>=8).sum())))
        pd.DataFrame(audits).to_csv(OUT/'training_audit.csv',index=False)
        print('BUILT',season,audits[-1],'seconds',round(time.time()-t),flush=True)
if __name__=='__main__':main()
