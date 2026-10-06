from pathlib import Path
import sys,json,pickle
import pandas as pd,numpy as np
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from decision_specialist.models import gate_design,fit_gate,predict_gate,future_proxy
from retrained_ensemble.run import games_for,SEASONS
from upside.features import load_history
OUT=HERE/'results'

def main():
    _,fixtures,_=load_history();available=fixtures.groupby(['season','event']).available.max()
    frames=[];games_by={}
    for s in SEASONS:
        games=games_for(s);games_by[s]=games
        features=pd.read_csv(CURRENT/f'behavior_diagnostics/results/scenario_inputs_{s}.csv.gz')
        old=pd.read_csv(CURRENT/f'horizon_upside/results/forecasts_{s}.csv.gz');rows=[];gate_rows=[]
        for gw in range(5,39):
            g=games[gw];f=features[features.gw==gw];h=old[old.gw==gw]
            assert np.array_equal(f.pid,g['frame'].pid) and np.array_equal(h.pid,f.pid)
            assert (pd.to_datetime(f.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
            assert (pd.to_datetime(h.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
            reference=.5*g['pred']['ridge']+.5*g['pred']['extra']
            row=pd.DataFrame(dict(season=s,gw=gw,pid=f.pid.to_numpy(),cutoff=g['cutoff']))
            for name,current in [('reference',reference),('extra_refresh',g['pred']['extra_refresh']),('re_refresh',g['pred']['re_refresh'])]:
                forecast=future_proxy(current,reference,g['count'],h.reference_1.to_numpy())
                if name=='reference':np.testing.assert_allclose(forecast,h[[f'reference_{i}' for i in range(3)]],atol=1e-12)
                for j in range(3):row[f'{name}_{j}']=forecast[:,j]
            rows.append(row)
            q=f[['season','gw','pid','cutoff','minutes_m6','minutes_m12','count','actual']].copy()
            q['a']=g['pred']['re_refresh'];q['b']=g['pred']['rich_refresh'];q['label_available']=available.get((s,gw),pd.NaT)
            gate_rows.append(q)
        pd.concat(rows,ignore_index=True).to_csv(OUT/f'horizon_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        frames.append(pd.concat(gate_rows,ignore_index=True))
    data=pd.concat(frames,ignore_index=True);data['label_available']=pd.to_datetime(data.label_available,utc=True);audits=[];coefficients={}
    for s in SEASONS[2:]:
        cutoff=pd.Timestamp(games_by[s][1]['cutoff'])
        train=data[(data.season<s)&(data.label_available<cutoff)&(data['count']>0)]
        assert train.season.max()<s and train.label_available.max()<cutoff
        evaluate=data[data.season==s].copy();x=gate_design(train.minutes_m6,train.minutes_m12);xt=gate_design(evaluate.minutes_m6,evaluate.minutes_m12)
        coefficients[s]={}
        for name,conditional in [('gate',True),('constant',False)]:
            beta,loss=fit_gate(x,train.a.to_numpy(),train.b.to_numpy(),train.actual.to_numpy(),train['count'].to_numpy(),conditional)
            prediction,w=predict_gate(xt,evaluate.a.to_numpy(),evaluate.b.to_numpy(),beta)
            evaluate[name]=prediction;evaluate[name+'_weight']=w;coefficients[s][name]=dict(beta=beta.tolist(),loss=loss)
        evaluate.to_csv(OUT/f'gate_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
        audits.append(dict(season=s,training_rows=len(train),training_seasons=','.join(sorted(train.season.unique())),max_label_available=str(train.label_available.max()),cutoff=str(cutoff),evaluation_rows=len(evaluate)))
        print('BUILT',s,coefficients[s],flush=True)
    (OUT/'gate_coefficients.json').write_text(json.dumps(coefficients,indent=2));pd.DataFrame(audits).to_csv(OUT/'gate_training_audit.csv',index=False)
if __name__=='__main__':main()
