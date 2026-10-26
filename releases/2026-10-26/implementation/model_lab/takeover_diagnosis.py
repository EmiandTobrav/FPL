"""Exploratory H1 diagnostic; never a selection gate or a new model run."""
import pandas as pd
from model_lab.takeover_campaign import R,P,C,S,ARMS,BENCHMARK
from model_lab.common import atomic_json

def main():
    lab=pd.read_csv(R/'datasets/fpl_model_pipeline_v1/operational_proxy_v1.csv.xz',usecols=['season','round','code','target_total_points'])
    frames=[]
    for s in S:
        for gw in range(7,39):
            pred=pd.read_csv(P/f'{s}_gw{gw:02d}.csv.gz').query('offset==0')
            b=pd.read_csv(C/s/f'gw{gw:02d}'/(BENCHMARK+'.csv.gz'))[['code','xp_0']].rename(columns={'xp_0':'benchmark'})
            pool=pd.read_csv(C/s/f'gw{gw:02d}'/'pool.csv.gz')[['code','can_buy']]
            z=pred.merge(b,on='code',validate='one_to_one').merge(pool,on='code',validate='one_to_one')
            z=z[z.can_buy].sort_values(['benchmark','code'],ascending=[False,True]).head(20)
            z=z.merge(lab[lab.season.eq(s)&lab['round'].eq(gw)][['code','target_total_points']],on='code',how='left',validate='one_to_one')
            frames.append(z)
    q=pd.concat(frames,ignore_index=True);records=[]
    for s,g in q.groupby('season'):
        known=g.target_total_points.notna();g=g[known]
        for arm in ARMS:
            e=g[arm]-g.target_total_points
            records.append(dict(season=s,arm=arm,n=len(g),mse=float((e**2).mean()),bias=float(e.mean()),mean_prediction=float(g[arm].mean()),mean_actual=float(g.target_total_points.mean())))
    pd.DataFrame(records).to_csv(P/'exploratory_top20_H1.csv',index=False)
    atomic_json(P/'exploratory_diagnosis.json',dict(status='posthoc_descriptive_only',cohort='top20 buyable players by benchmark H1 at each original origin; code ascending breaks ties',selection_uses_outcomes=False,reason='Inspect decision-relevant H1 calibration after early takeover losses; not preregistered, no gate or model changes',metrics=records))
    print(pd.DataFrame(records).to_string(index=False))

if __name__=='__main__':main()
