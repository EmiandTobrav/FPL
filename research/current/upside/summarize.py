"""Season utility plus pre-deadline strata diagnostics; never choose on current targets."""
from pathlib import Path
import sys,json,gzip,copy
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent
sys.path.insert(0,str(CURRENT));sys.path.insert(0,str(HERE))
import experiment
from upside.models import CANDIDATES
from upside.run import games_for,fingerprint
OUT=HERE/'results';REFERENCE='mix_ridge_extra_50'
MODELS=[REFERENCE,'ridge','hgb']+CANDIDATES

def ranked_metrics(y,score,pid,k):
    if len(y)==0:return dict(n=0,precision=np.nan,recall=np.nan,ndcg=np.nan,mean_points=np.nan,hauls=0)
    k=min(k,len(y));idx=np.lexsort((pid,-score))[:k]
    gain=np.maximum(y,0);discount=1/np.log2(np.arange(2,k+2))
    ideal=np.sort(gain)[::-1][:k]@discount
    positive=y>=8;hits=positive[idx].sum()
    return dict(n=len(y),precision=hits/k,recall=hits/positive.sum() if positive.sum() else np.nan,
        ndcg=(gain[idx]@discount)/ideal if ideal else np.nan,mean_points=float(y[idx].mean()),hauls=int(positive.sum()))

def main():
    assert json.loads((OUT/'run_manifest.json').read_text())==fingerprint()
    summaries=[];checks=[];diagnostics=[]
    for season in experiment.SEASONS:
        games=games_for(season);handoff=None
        for model in MODELS:
            for mode in ['no_chips','fixed_chips']:
                root=OUT if model in CANDIDATES else CURRENT/'results'
                obj=json.loads(gzip.decompress((root/f'trace_{season}_{model}_{mode}.json.gz').read_bytes()))
                sig=json.dumps(obj['handoff'],sort_keys=True)
                if handoff is None:handoff=sig
                assert sig==handoff
                s=obj['summary'].copy();rows=obj['trace']
                assert [r['gw'] for r in rows]==list(range(5,39))
                assert s['points38']==s['opening_points']+sum(r['gross']-r['hits'] for r in rows)
                cap=[]
                for r in rows:
                    assert r['bank']>=0 and 1<=r['ft']<=5
                    assert len(set(r['squad']))==15 and len(r['starters'])==11
                    assert r['gross']==sum(r['contributions'].values())+r['captain_bonus']
                    frame=games[r['gw']]['frame'].set_index('pid')
                    counts=frame.loc[r['squad']].pos.value_counts().to_dict()
                    assert counts=={1:2,2:5,3:5,4:3}
                    cap.append(games[r['gw']]['actual'].get(r['captain'],0))
                s['captain_mean_points']=np.mean(cap);s['captain_haul_rate']=np.mean(np.array(cap)>=8)
                summaries.append(s);checks.append(dict(season=season,model=model,mode=mode,verified_rounds=len(rows)))
        for gw in range(5,39):
            game=games[gw];p=game['frame'];ids=p.pid.to_numpy()
            y=np.array([game['actual'].get(int(i),0) for i in ids])
            sched=np.asarray(game['count'])>0
            cheap=p.market.to_numpy()<=p.pos.map({1:45,2:50,3:60,4:60}).to_numpy()
            masks={'all':sched,'cheap':sched&cheap,'short_history':sched&(game['n_history']<12)}
            for m in MODELS:
                score=experiment.xp_for(game,m)
                for stratum,mask in masks.items():
                    diagnostics.append(dict(season=season,gw=gw,model=m,stratum=stratum,
                        **ranked_metrics(y[mask],score[mask],ids[mask],20 if stratum=='all' else 10)))
    results=pd.DataFrame(summaries)
    base=results[results.model==REFERENCE][['season','mode','points38']].rename(columns={'points38':'reference_points'})
    results=results.merge(base,on=['season','mode']);results['gain']=results.points38-results.reference_points
    results.to_csv(OUT/'season_results.csv',index=False)
    summary=results.groupby(['mode','model']).agg(mean_points=('points38','mean'),mean_gain=('gain','mean'),
        wins=('gain',lambda x:int((x>0).sum())),min_gain=('gain','min'),max_gain=('gain','max'),
        mean_hits=('hits','mean'),mean_transfers=('transfers','mean'),captain_mean=('captain_mean_points','mean'),
        captain_haul_rate=('captain_haul_rate','mean')).reset_index()
    summary.to_csv(OUT/'model_summary.csv',index=False)
    intervals=[];rng=np.random.default_rng(173)
    for (mode,model),group in results[results.model.isin(CANDIDATES)].groupby(['mode','model']):
        values=group.gain.to_numpy();boot=rng.choice(values,size=(50000,len(values)),replace=True).mean(axis=1)
        intervals.append(dict(mode=mode,model=model,mean_gain=float(values.mean()),
            low95=float(np.quantile(boot,.025)),high95=float(np.quantile(boot,.975)),seasons=len(values)))
    pd.DataFrame(intervals).to_csv(OUT/'season_bootstrap.csv',index=False)
    diag=pd.DataFrame(diagnostics);diag.to_csv(OUT/'weekly_ranking_metrics.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    per=diag.groupby(['season','model','stratum'])[['precision','recall','ndcg','mean_points']].mean().reset_index()
    per.to_csv(OUT/'ranking_by_season.csv',index=False)
    per.groupby(['model','stratum'])[['precision','recall','ndcg','mean_points']].mean().reset_index().to_csv(OUT/'ranking_summary.csv',index=False)
    selections=[]
    for mode in ['no_chips','fixed_chips']:
        allowed=results[(results['mode']==mode)&results.model.isin([REFERENCE]+CANDIDATES)]
        for season in experiment.SEASONS[2:]:
            past=allowed[allowed.season<season].groupby('model').gain.agg(['mean','std'])
            merit=past['mean']-.25*past['std'].fillna(0);best=merit.idxmax()
            selected=REFERENCE if merit[REFERENCE]>=merit[best]-2 else best
            r=allowed[(allowed.season==season)&(allowed.model==selected)].iloc[0]
            selections.append(dict(season=season,mode=mode,selected=selected,gain=float(r.gain),points=float(r.points38)))
    pd.DataFrame(selections).to_csv(OUT/'chronological_selection.csv',index=False)
    # Ensure current outcome mutations cannot influence either new decision score's choices.
    state,_=experiment.opening(experiment.SEASONS[0]);g=games_for(experiment.SEASONS[0])[5]
    fake=copy.deepcopy(g);fake['actual']={int(i):9999 for i in g['frame'].pid};fake['active']={int(i):True for i in g['frame'].pid}
    for m in ['upside_only','weighted_mean']:
        _,a=experiment.make_choice(g,m,state,None);_,b=experiment.make_choice(fake,m,state,None)
        for key in ['squad','starters','bench','captain','vice','incoming','outgoing']:assert a[key]==b[key]
    audit=pd.read_csv(OUT/'training_audit.csv')
    assert (pd.to_datetime(audit.training_max,utc=True)<pd.to_datetime(audit.first_cutoff,utc=True)).all()
    verification=dict(new_simulations=48,new_decisions=48*34,compared_simulations=len(results),
        identical_handoff=True,accounting=True,temporal_training=True,outcome_blind_decisions=True,
        control_max_difference=float(audit.control_max_difference.max()),
        new_nonoptimal_decisions=int(results[results.model.isin(CANDIDATES)].nonoptimal.sum()),
        new_max_solver_gap=float(results[results.model.isin(CANDIDATES)].max_solver_gap.max()))
    (OUT/'checks.json').write_text(json.dumps(verification,indent=2))
    print(summary.to_string(index=False));print(pd.DataFrame(selections).to_string(index=False));print(verification)
if __name__=='__main__':main()
