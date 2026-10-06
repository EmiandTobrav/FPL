from pathlib import Path
import sys,json,pickle,warnings,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
from scipy.special import expit
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from adaptive_events.features import RICH,load_history,training_design,prediction_rows
from upside.models import estimator
from retrained_ensemble.run import games_for,SEASONS
from decision_specialist.models import future_proxy
from position_specialist.models import fit_position_weights,blend
OUT=HERE/'results'

def prepare_weights():
    _,fixtures,_=load_history();available=fixtures.groupby(['season','event']).available.max()
    frames=[];cutoffs={}
    for s in SEASONS:
        games=games_for(s);cutoffs[s]=pd.Timestamp(games[1]['cutoff']);rows=[]
        for gw in range(5,39):
            g=games[gw];p=g['frame'];q=pd.DataFrame(dict(season=s,gw=gw,pid=p.pid.to_numpy(),pos=p.pos.to_numpy(),a=g['pred']['re_refresh'],b=g['pred']['rich_refresh'],count=g['count'],actual=[g['actual'].get(i,0) for i in p.pid],available=available.get((s,gw),pd.NaT)))
            rows.append(q)
        frames.append(pd.concat(rows,ignore_index=True))
    data=pd.concat(frames,ignore_index=True);data.available=pd.to_datetime(data.available,utc=True)
    global_coefs=json.loads((CURRENT/'decision_specialist/results/gate_coefficients.json').read_text());audits=[];coefficients={}
    for s in SEASONS[2:]:
        tr=data[(data.season<s)&(data.available<cutoffs[s])&(data['count']>0)]
        beta0=global_coefs[s]['constant']['beta'][0]
        beta,loss=fit_position_weights(tr.pos,tr.a,tr.b,tr.actual,tr['count'],beta0)
        assert tr.season.max()<s and tr.available.max()<cutoffs[s]
        coefficients[s]=dict(beta=beta.tolist(),weights=expit(beta).tolist(),global_beta=beta0,global_weight=float(expit(beta0)),loss=loss)
        for pos in range(1,5):
            t=tr[tr.pos==pos];audits.append(dict(season=s,pos=pos,rows=len(t),max_available=str(t.available.max()),cutoff=str(cutoffs[s])))
    (OUT/'coefficients.json').write_text(json.dumps(coefficients,indent=2));pd.DataFrame(audits).to_csv(OUT/'weight_training_audit.csv',index=False)
    print('WEIGHTS',coefficients,flush=True)

def train_year(s):
    warnings.filterwarnings('ignore',message='Skipping features without any observed values')
    d,fixtures,th=load_history();train=training_design(d);games=games_for(s)
    coefficients=json.loads((OUT/'coefficients.json').read_text())[s];w=coefficients['global_weight'];pw=np.asarray(coefficients['weights'])
    old=pd.read_csv(CURRENT/f'decision_specialist/results/horizon_{s}.csv.gz');benchmark=pd.read_csv(CURRENT/f'global_horizon/results/horizon_{s}.csv.gz')
    audits=[];rows=[];diagnostics=[];t=time.time()
    for gw in range(5,39):
        g=games[gw];cut=pd.Timestamp(g['cutoff'])
        if (gw-5)%4==0:
            tr=train[(train.season<=s)&(train.available<cut)]
            assert tr.available.max()<cut
            global_model=estimator().fit(tr[RICH],tr.historic);models={}
            for pos in range(1,5):
                z=tr[tr.pos==pos];assert len(z)>=60
                models[pos]=estimator().fit(z[RICH],z.historic)
                audits.append(dict(season=s,gw=gw,pos=pos,rows=len(z),max_available=str(z.available.max()),cutoff=str(cut),same_season_rows=int((z.season==s).sum())))
            print('FIT',s,gw,'seconds',round(time.time()-t),flush=True)
        batch,p=prediction_rows(d,fixtures,th,g,s,gw);pos_pred=np.zeros(len(p));control=np.zeros(len(p))
        if not batch.empty:
            np.add.at(control,batch._row,np.maximum(0,global_model.predict(batch[RICH])))
            for pos in range(1,5):
                z=batch[batch.pos==pos]
                if len(z):np.add.at(pos_pred,z._row,np.maximum(0,models[pos].predict(z[RICH])))
        error=float(np.max(np.abs(control-g['pred']['rich_refresh'])));assert error<1e-7,(s,gw,error)
        a=g['pred']['re_refresh'];b=g['pred']['rich_refresh'];positions=g['frame'].pos.to_numpy().astype(int)
        preds={'pos_weight':blend(a,b,pw[positions-1]),'pos_hgb':blend(a,pos_pred,w),'hybrid_hgb':blend(a,.5*b+.5*pos_pred,w)}
        h=old[old.gw==gw];base=benchmark[benchmark.gw==gw];assert np.array_equal(p.index,h.pid) and np.array_equal(p.index,base.pid)
        row=base.copy();reference=.5*g['pred']['ridge']+.5*g['pred']['extra']
        for name,pred in preds.items():
            horizon=future_proxy(pred,reference,g['count'],h.reference_1.to_numpy())
            for j in range(3):row[f'{name}_{j}']=horizon[:,j]
        rows.append(row)
        q=row[['season','gw','pid','cutoff','constant_0','pos_weight_0','pos_hgb_0','hybrid_hgb_0']].copy();q['pos']=positions;q['count']=g['count'];q['actual']=[g['actual'].get(i,0) for i in p.index];q['rich_control_error']=error;diagnostics.append(q)
    pd.DataFrame(audits).to_csv(OUT/f'training_audit_{s}.csv',index=False)
    pd.concat(diagnostics,ignore_index=True).to_csv(OUT/f'predictions_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.concat(rows,ignore_index=True).to_csv(OUT/f'horizon_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    print('BUILT',s,'seconds',round(time.time()-t),flush=True)

if __name__=='__main__':
    prepare_weights()
    with ProcessPoolExecutor(max_workers=2) as ex:
        for f in as_completed([ex.submit(train_year,s) for s in SEASONS[2:]]):f.result()
