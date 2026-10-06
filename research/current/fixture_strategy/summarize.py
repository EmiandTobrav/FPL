from pathlib import Path
import json,gzip
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;OUT=HERE/'results';CURRENT=HERE.parent

def main():
    d=pd.concat([pd.read_csv(OUT/f'seasons_{x}.csv') for x in ['h3','long','chips']],ignore_index=True)
    benchmark=pd.read_csv(CURRENT/'calendar_counts/results/all_seasons.csv');benchmark=benchmark[benchmark.model=='constant_h3'].set_index(['season','mode']).points38
    d['benchmark']=d.apply(lambda r:benchmark[(r.season,'no_chips' if r['mode']=='no_chips' else 'fixed_chips')],axis=1)
    d['gain']=d.points38-d.benchmark
    counts=d[(d.forecast_model=='count')].set_index(['season','horizon','mode']).points38
    full=d[(d.model=='full_h3')&(d['mode']=='fixed_chips')].set_index('season').points38
    d['matched_control']=d.apply(lambda r:full[r.season] if r['mode'].startswith('adaptive_') else counts[(r.season,r.horizon,r['mode'])],axis=1)
    d['matched_gain']=d.points38-d.matched_control;d.sort_values(['mode','model','season']).to_csv(OUT/'all_seasons.csv',index=False)
    rng=np.random.default_rng(173);ix=rng.integers(0,4,(50000,4));rows=[]
    for (model,mode),g in d.groupby(['model','mode']):
        v=g.sort_values('season').matched_gain.to_numpy();lo,hi=np.quantile(v[ix].mean(axis=1),[.025,.975])
        rows.append(dict(model=model,mode=mode,points=g.points38.mean(),gain=g.gain.mean(),matched_gain=g.matched_gain.mean(),wins=int((v>0).sum()),ties=int((v==0).sum()),losses=int((v<0).sum()),matched_ci_low=lo,matched_ci_high=hi,hits=g.hits.mean(),transfers=g.transfers.mean(),nonoptimal=int(g.nonoptimal.sum()),max_solver_gap=g.max_solver_gap.max()))
    summary=pd.DataFrame(rows);summary.to_csv(OUT/'summary.csv',index=False)
    chiprows=[]
    for path in OUT.glob('trace_*.json.gz'):
        z=json.loads(gzip.decompress(path.read_bytes()));s=z['summary']
        for r in z['trace']:
            if r['chip']:chiprows.append(dict(season=s['season'],model=s['model'],mode=s['mode'],gw=r['gw'],chip=r['chip'],net=r['net'],hits=r['hits'],captain_bonus=r['captain_bonus']))
    pd.DataFrame(chiprows).to_csv(OUT/'chip_dates.csv',index=False)
    print(summary.to_string(index=False))
if __name__=='__main__':main()
