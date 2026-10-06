from pathlib import Path
import json,pickle,hashlib,sys
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from calendar_counts.features import count_forecast
from calendar_audit.selector import select_before
OUT=HERE/'results';AUDIT=CURRENT/'calendar_audit'

def main():
    selection=pd.read_csv(AUDIT/'selection.csv');sources=json.loads((AUDIT/'source_commits.json').read_text());manifest={x['path']:x for x in json.loads((AUDIT/'snapshot_manifest.json').read_text())};audits=[]
    for s,q in selection.groupby('season'):
        with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
        predictions=pd.read_csv(CURRENT/f'global_horizon/results/horizon_{s}.csv.gz');codes=pd.read_csv(CURRENT/f'project/data/{s}_teams.csv').set_index('id').code;rows=[]
        for r in q.itertuples():
            g=games[r.gw];assert pd.Timestamp(r.cutoff)==pd.Timestamp(g['cutoff'])
            c=select_before(sources[s],g['cutoff']);assert c['sha']==r.sha
            path=AUDIT/f'snapshots/{s}_{r.sha}.csv.gz';assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest[str(path.relative_to(AUDIT))]['stored_sha256']
            snap=pd.read_csv(path,usecols=['id','event','team_h','team_a'])
            row=predictions[predictions.gw==r.gw].copy();assert np.array_equal(row.pid,g['frame'].pid)
            assert (pd.to_datetime(row.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
            base=row[[f'constant_{j}' for j in range(3)]].to_numpy()
            forecast=count_forecast(base,g['frame'].club,snap,codes,r.gw,r.age_days)
            for j in range(3):row[f'calendar_count_{j}']=forecast[:,j]
            rows.append(row);audits.append(dict(season=s,gw=r.gw,cutoff=r.cutoff,snapshot_time=r.snapshot_time,sha=r.sha,age_days=r.age_days,use_calendar=r.age_days<=14,changed_future_player_cells=int(np.count_nonzero(forecast[:,1:]!=base[:,1:])),current_max_difference=float(np.max(np.abs(forecast[:,0]-base[:,0])))))
        pd.concat(rows,ignore_index=True).to_csv(OUT/f'horizon_{s}.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    pd.DataFrame(audits).to_csv(OUT/'forecast_audit.csv',index=False);print(pd.DataFrame(audits).groupby('season')[['use_calendar','changed_future_player_cells']].sum().to_string())
if __name__=='__main__':main()
