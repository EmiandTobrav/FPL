from pathlib import Path
import sys,json,gzip
import pandas as pd,numpy as np
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from adaptive_events.run import OUT,SEASONS,REF,MODELS,games_for,fingerprint
from upside.summarize import ranked_metrics
import experiment

def main():
    assert json.loads((OUT/'run_manifest.json').read_text())==fingerprint()
    audit=pd.read_csv(OUT/'training_audit.csv')
    assert (pd.to_datetime(audit.max_available,utc=True)<pd.to_datetime(audit.cutoff,utc=True)).all()
    assert len(audit)==60
    for s,g in audit.groupby('season'):
        assert g.gw.tolist()==[1,5,9,13,17,21,25,29,33,37]
    results=[];diags=[]
    for s in SEASONS:
        games=games_for(s)
        for mode in ['no_chips','fixed_chips']:
            baseline=json.loads(gzip.decompress((CURRENT/f'results/trace_{s}_{REF}_{mode}.json.gz').read_bytes()))
            for m in [REF,'hgb']+MODELS:
                root=OUT if m in MODELS else CURRENT/'results'
                obj=json.loads(gzip.decompress((root/f'trace_{s}_{m}_{mode}.json.gz').read_bytes()))
                assert obj['handoff']==baseline['handoff'] and obj['opening']==baseline['opening']
                summary=obj['summary'];assert len(obj['trace'])==34
                assert summary['points38']==summary['opening_points']+sum(r['net'] for r in obj['trace'])
                for r in obj['trace']:
                    assert r['net']==r['gross']-r['hits'] and r['gross']==sum(r['contributions'].values())+r['captain_bonus']
                    assert r['bank']>=0 and 1<=r['ft']<=5 and len(set(r['squad']))==15 and len(r['starters'])==11
                    p=games[r['gw']]['frame'].set_index('pid');assert p.loc[r['squad']].pos.value_counts().to_dict()=={1:2,2:5,3:5,4:3}
                results.append(summary)
        for gw in range(5,39):
            g=games[gw];p=g['frame'];ids=p.pid.to_numpy();y=np.array([g['actual'].get(int(i),0) for i in ids]);scheduled=np.asarray(g['count'])>0
            masks={'all':scheduled,'cheap':scheduled&(p.market.to_numpy()<=p.pos.map({1:45,2:50,3:60,4:60}).to_numpy()),'short_history':scheduled&(g['n_history']<12)}
            for m in [REF,'hgb']+MODELS:
                score=experiment.xp_for(g,m)
                for group,mask in masks.items():diags.append(dict(season=s,gw=gw,model=m,stratum=group,**ranked_metrics(y[mask],score[mask],ids[mask],20 if group=='all' else 10)))
    r=pd.DataFrame(results);reference=r[r.model==REF][['season','mode','points38']].rename(columns={'points38':'reference_points'})
    r=r.merge(reference,on=['season','mode']);r['gain']=r.points38-r.reference_points;r.to_csv(OUT/'season_results.csv',index=False)
    summary=r.groupby(['mode','model']).agg(mean_points=('points38','mean'),gain=('gain','mean'),wins=('gain',lambda x:int((x>0).sum())),mean_hits=('hits','mean'),mean_transfers=('transfers','mean'),nonoptimal=('nonoptimal','sum'),max_gap=('max_solver_gap','max')).reset_index();summary.to_csv(OUT/'model_summary.csv',index=False)
    comparisons=[(m,REF) for m in MODELS]+[('hgb_refresh','hgb'),('hgb_recent','hgb_refresh'),('rich_frozen','hgb'),('rich_refresh','rich_frozen'),('rich_refresh','hgb_refresh'),('events_frozen','rich_frozen'),('events_refresh','events_frozen'),('events_refresh','rich_refresh'),('blend_events_direct','rich_refresh'),('blend_three','blend_events_direct')]
    pairs=[]
    for cand,ctrl in comparisons:
        a=r[r.model==cand].merge(r[r.model==ctrl],on=['season','mode'],suffixes=('_a','_b'))
        for x in a.itertuples():pairs.append(dict(season=x.season,mode=x.mode,comparison=cand+' - '+ctrl,gain=x.points38_a-x.points38_b))
    pairs=pd.DataFrame(pairs);pairs.to_csv(OUT/'paired_seasons.csv',index=False)
    stats=[];rng=np.random.default_rng(173)
    for (mode,comparison),g in pairs.groupby(['mode','comparison']):
        vals=g.sort_values('season').gain.to_numpy();boot=rng.choice(vals,size=(50000,len(vals)),replace=True).mean(axis=1)
        stats.append(dict(mode=mode,comparison=comparison,mean_gain=vals.mean(),wins=int((vals>0).sum()),min_gain=vals.min(),max_gain=vals.max(),low95=np.quantile(boot,.025),high95=np.quantile(boot,.975)))
    pd.DataFrame(stats).to_csv(OUT/'paired_summary.csv',index=False)
    diag=pd.DataFrame(diags);diag.to_csv(OUT/'ranking_weekly.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    per=diag.groupby(['season','model','stratum'])[['precision','recall','ndcg','mean_points']].mean().reset_index();per.to_csv(OUT/'ranking_by_season.csv',index=False)
    per.groupby(['model','stratum'])[['precision','recall','ndcg','mean_points']].mean().reset_index().to_csv(OUT/'ranking_summary.csv',index=False)
    selection=[]
    for mode in ['fixed_chips','no_chips']:
        data=r[(r['mode']==mode)&r.model.isin([REF]+MODELS)]
        for season in SEASONS[2:]:
            past=data[data.season<season].groupby('model').gain.agg(['mean','std']);merit=past['mean']-.25*past['std'].fillna(0);best=merit.idxmax();chosen=REF if merit[REF]>=merit[best]-2 else best
            row=data[(data.season==season)&(data.model==chosen)].iloc[0]
            selection.append(dict(season=season,mode=mode,selected=chosen,gain=float(row.gain),points=float(row.points38)))
    pd.DataFrame(selection).to_csv(OUT/'chronological_selection.csv',index=False)
    checks=dict(new_simulations=108,compared_simulations=len(r),new_decisions=108*34,training_windows=len(audit),temporal_training=True,identical_opening=True,accounting=True,nonoptimal=int(r[r.model.isin(MODELS)].nonoptimal.sum()),max_solver_gap=float(r[r.model.isin(MODELS)].max_solver_gap.max()))
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2));print(summary.to_string(index=False));print(pd.DataFrame(selection).to_string(index=False));print(checks)
if __name__=='__main__':main()
