from common import *
from concurrent.futures import ProcessPoolExecutor,as_completed
import time
MODELS_AB=['ridge','ridge_refresh','extra','extra_refresh',REF,'re_refresh']
CAL=dict(experiment.CAL)
REGIMES={'wc_only':[6,24],'fh_only':[18,33],'resets_only':[6,18,24,33],'bonuses_only':[15,19,36,37]}

def worker(task):
    s,m,regime=task;root=OUT/('ablation_'+regime);root.mkdir(exist_ok=True)
    original=experiment.CAL
    try:
        experiment.CAL={gw:CAL[gw] for gw in REGIMES[regime]}
        result=experiment.run((s,m,'fixed_chips'),games=games_for(s),trace_dir=root)
    finally:experiment.CAL=original
    return dict(result,regime=regime)

def main():
    t=time.time();rows=[]
    tasks=[(s,m,r) for s in SEASONS for m in MODELS_AB for r in REGIMES]
    with ProcessPoolExecutor(max_workers=4) as ex:
        for i,f in enumerate(as_completed([ex.submit(worker,t) for t in tasks]),1):
            rows.append(f.result())
            if i%24==0:print('ABLATION',i,len(tasks),round(time.time()-t),flush=True)
    for s in SEASONS:
        for m in MODELS_AB:
            for r in ['no_chips','fixed_chips']:rows.append(dict(trace(s,m,r)['summary'],regime=r))
    data=pd.DataFrame(rows);data.to_csv(OUT/'ablation_seasons.csv',index=False)
    pairs=[]
    for a,b in COMPARISONS[:3]:
        z=data[data.model==a].merge(data[data.model==b],on=['season','regime'],suffixes=('_a','_b'))
        for row in z.itertuples():pairs.append(dict(season=row.season,regime=row.regime,comparison=a+' - '+b,gain=row.points38_a-row.points38_b))
    pairs=pd.DataFrame(pairs);pairs.to_csv(OUT/'ablation_paired_seasons.csv',index=False)
    pairs.groupby(['regime','comparison']).gain.agg(['mean','min','max',lambda x:int((x>0).sum())]).rename(columns={'<lambda_0>':'positive_seasons'}).to_csv(OUT/'ablation_paired_summary.csv')
    pivot=pairs.pivot(index=['season','comparison'],columns='regime',values='gain');pivot['reset_effect']=pivot.resets_only-pivot.no_chips;pivot['bonus_effect']=pivot.bonuses_only-pivot.no_chips;pivot['interaction']=pivot.fixed_chips-pivot.resets_only-pivot.bonuses_only+pivot.no_chips
    pivot.to_csv(OUT/'ablation_factorial_seasons.csv');pivot.groupby('comparison')[['reset_effect','bonus_effect','interaction']].mean().to_csv(OUT/'ablation_factorial_summary.csv')
    new=data[data.regime.isin(REGIMES)]
    checks=dict(new_season_simulations=len(new),new_decisions=len(new)*34,nonoptimal=int(new.nonoptimal.sum()),max_solver_gap=float(new.max_solver_gap.max()))
    (OUT/'ablation_checks.json').write_text(json.dumps(checks,indent=2));print(checks)
if __name__=='__main__':main()
