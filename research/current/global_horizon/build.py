from pathlib import Path
import sys,json,pickle
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from decision_specialist.models import future_proxy
from decision_specialist.run_horizon import fingerprint
OUT=HERE/'results';SEASONS=[f'{y}-{str(y+1)[-2:]}' for y in range(2022,2026)]

def main():
    assert json.loads((CURRENT/'decision_specialist/results/horizon_manifest.json').read_text())==fingerprint()
    audits=[]
    for s in SEASONS:
        with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
        gate=pd.read_csv(CURRENT/f'decision_specialist/results/gate_{s}.csv.gz');old=pd.read_csv(CURRENT/f'decision_specialist/results/horizon_{s}.csv.gz');rows=[]
        for gw in range(5,39):
            g=games[gw];p=gate[gate.gw==gw];h=old[old.gw==gw]
            assert np.array_equal(p.pid,g['frame'].pid) and np.array_equal(p.pid,h.pid)
            for f in [p,h]:assert (pd.to_datetime(f.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
            reference=.5*g['pred']['ridge']+.5*g['pred']['extra']
            # Verify identical horizon transformation against the archived matched control.
            control=future_proxy(p.a.to_numpy(),reference,g['count'],h.reference_1.to_numpy())
            error=float(np.max(np.abs(control-h[[f're_refresh_{j}' for j in range(3)]].to_numpy())))
            assert error<1e-12
            prediction=future_proxy(p.constant.to_numpy(),reference,g['count'],h.reference_1.to_numpy())
            np.testing.assert_array_equal(prediction[:,0],p.constant.to_numpy())
            row=p[['season','gw','pid','cutoff']].copy()
            for j in range(3):row[f'constant_{j}']=prediction[:,j]
            rows.append(row);audits.append(dict(season=s,gw=gw,cutoff=g['cutoff'],rows=len(p),control_max_difference=error))
        pd.concat(rows,ignore_index=True).to_csv(OUT/f'horizon_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.DataFrame(audits).to_csv(OUT/'forecast_audit.csv',index=False);print('BUILT',len(audits),'rounds')
if __name__=='__main__':main()
