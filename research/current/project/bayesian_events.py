"""Empirical hierarchical conjugate event models; fixed configurations.
Beta-binomial playing-time categories; Gamma-Poisson event rates per 90.
Hypermeans come only from earlier training observations, grouped by position.
No MCMC, posterior correlation model or calibrated interval claim.
"""
from pathlib import Path
import numpy as np
import pandas as pd
from research import ROOT,OUT,SEASONS,metrics

CONFIGS=[('bayes_events3',3,False),('bayes_events10',10,False),
         ('bayes_events30',30,False),('bayes_events10_elo',10,True)]

def predict(tr,te,strength,elo,target):
    n=te.n_history.fillna(0).clip(upper=38).to_numpy()
    minutes=te.minutes_m38.fillna(0).to_numpy()*n
    exposure=minutes/90
    gp=tr.groupby('pos')
    prior_play=te.pos.map(gp.played.mean()).to_numpy()
    prior_long=te.pos.map(gp.long_play.mean()).to_numpy()
    play=(te.played_m38.fillna(0).to_numpy()*n+strength*prior_play)/(n+strength)
    long=(te.long_play_m38.fillna(0).to_numpy()*n+strength*prior_long)/(n+strength)
    # Recent minutes partially pooled towards position, then constrained by play.
    prior_minutes=te.pos.map(gp.minutes.mean()).to_numpy()
    pred_minutes=(te.minutes_m6.fillna(0).to_numpy()*np.minimum(n,6)+3*prior_minutes)/(np.minimum(n,6)+3)
    pred_minutes=np.minimum(pred_minutes,90*play)
    out=play+long
    for c,weight in [('goals_scored',te.pos.map({1:10,2:6,3:5,4:4}).to_numpy()),
                     ('assists',3 if target=='historic' else 0),('yellow_cards',-1),
                     ('saves',1/3)]:
        prior_rate=gp[c].sum()/gp.minutes.sum()*90
        mean=te.pos.map(prior_rate).fillna(0).to_numpy()
        # Gamma shape = strength * mean, rate = strength, conjugate posterior.
        event=(te[f'{c}_m38'].fillna(0).to_numpy()*n+strength*mean)/(exposure+strength)*pred_minutes/90
        if elo and c in ['goals_scored','assists']:
            event*=np.exp(np.clip(te.elo_diff.to_numpy()/1600,-.4,.4))
        out+=event*weight
    prior_cs=te.pos.map(gp.clean_sheets.mean()).to_numpy()
    cs=(te.clean_sheets_m38.fillna(0).to_numpy()*n+strength*prior_cs)/(n+strength)
    if elo:cs*=np.exp(np.clip(te.elo_diff.to_numpy()/1200,-.5,.5))
    out+=np.minimum(cs,long)*te.pos.map({1:4,2:4,3:1,4:0}).to_numpy()
    # Small penalties pooled by position; save floor modeled approximately above.
    for c,w in [('penalties_saved',5),('penalties_missed',-2),('red_cards',-3),('own_goals',-2)]:
        out+=te.pos.map(gp[c].mean()).to_numpy()*w
    out-=te.pos.map(gp.conceded_penalty.mean()).to_numpy()
    if target=='historic':
        prior_bonus=te.pos.map(gp.bonus.mean()).to_numpy()
        out+=(te.bonus_m38.fillna(0).to_numpy()*n+strength*prior_bonus)/(n+strength)
    return out

def run():
    d=pd.read_pickle(OUT/'features.pkl')
    d['conceded_penalty']=np.floor(d.goals_conceded/2)*d.pos.isin([1,2])
    rows=[]
    for target in ['historic','core']:
        for s in SEASONS:
            tr=d[(d.season<s)|((d.season==SEASONS[0])&(d.event<=10))]
            te=d[(d.season==s)&((d.event>10) if s==SEASONS[0] else True)]
            tr=tr[tr.available<te.cutoff.min()]
            pv=te[['season','event','fixture','pid','pos',target,'minutes_m6']].rename(columns={target:'actual'}).copy()
            for name,k,elo in CONFIGS:
                p=predict(tr,te,k,elo,target)
                rows.append({'target':target,'season':s,'model':name,'n_train':len(tr),**metrics(te,p,target)})
                pv[name]=p
            pv.to_csv(OUT/f'bayes_predictions_{target}_{s}.csv.gz',index=False)
    pd.DataFrame(rows).to_csv(OUT/'bayes_metrics.csv',index=False)
    print('Completed 56 conjugate Bayesian comparisons')

if __name__=='__main__':run()
