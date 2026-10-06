from pathlib import Path
import sys,json,gzip
import numpy as np
import pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent
sys.path.insert(0,str(CURRENT))
from upside_feature.run import OUT,SEASONS,MODELS,REF,games_for,fingerprint
from upside.summarize import ranked_metrics
import experiment

def main():
    assert json.loads((OUT/'run_manifest.json').read_text())==fingerprint()
    audit=pd.read_csv(OUT/'training_audit.csv')
    assert (pd.to_datetime(audit.max_available,utc=True)<pd.to_datetime(audit.cutoff,utc=True)).all()
    assert (audit.max_season<audit.season).all()
    assert audit[audit.kind=='outer'].tail_control_max.max()<1e-7
    results=[];diag=[]
    for s in SEASONS:
        games=games_for(s)
        for mode in ['no_chips','fixed_chips']:
            baseline=json.loads(gzip.decompress((CURRENT/f'results/trace_{s}_{REF}_{mode}.json.gz').read_bytes()))
            results.append(baseline['summary'])
            for m in MODELS:
                obj=json.loads(gzip.decompress((OUT/f'trace_{s}_{m}_{mode}.json.gz').read_bytes()))
                assert obj['handoff']==baseline['handoff'] and obj['opening']==baseline['opening']
                assert len(obj['trace'])==34
                assert obj['summary']['points38']==obj['summary']['opening_points']+sum(r['net'] for r in obj['trace'])
                for r in obj['trace']:
                    assert r['net']==r['gross']-r['hits']
                    assert r['gross']==sum(r['contributions'].values())+r['captain_bonus']
                    assert r['bank']>=0 and 1<=r['ft']<=5 and len(set(r['squad']))==15
                    p=games[r['gw']]['frame'].set_index('pid')
                    assert p.loc[r['squad']].pos.value_counts().to_dict()=={1:2,2:5,3:5,4:3}
                results.append(obj['summary'])
        for gw in range(5,39):
            g=games[gw];p=g['frame'];ids=p.pid.to_numpy();y=np.array([g['actual'].get(int(i),0) for i in ids]);sched=np.asarray(g['count'])>0
            masks={'all':sched,'cheap':sched&(p.market.to_numpy()<=p.pos.map({1:45,2:50,3:60,4:60}).to_numpy()),'short_history':sched&(g['n_history']<12)}
            for m in [REF]+MODELS:
                score=experiment.xp_for(g,m)
                for name,mask in masks.items():diag.append(dict(season=s,gw=gw,model=m,stratum=name,**ranked_metrics(y[mask],score[mask],ids[mask],20 if name=='all' else 10)))
    r=pd.DataFrame(results);ref=r[r.model==REF][['season','mode','points38']].rename(columns={'points38':'reference_points'})
    r=r.merge(ref,on=['season','mode']);r['gain']=r.points38-r.reference_points;r.to_csv(OUT/'season_results.csv',index=False)
    summary=r.groupby(['mode','model']).agg(mean_points=('points38','mean'),mean_gain=('gain','mean'),wins=('gain',lambda x:int((x>0).sum())),mean_hits=('hits','mean')).reset_index();summary.to_csv(OUT/'model_summary.csv',index=False)
    pairs=[]
    for candidate,control in [('with_tail','matched_base'),('blend_tail_50','blend_base_50')]+[(m,REF) for m in MODELS]:
        a=r[r.model==candidate].merge(r[r.model==control],on=['season','mode'],suffixes=('_candidate','_control'))
        for row in a.itertuples():pairs.append(dict(season=row.season,mode=row.mode,candidate=candidate,control=control,gain=row.points38_candidate-row.points38_control))
    cap=pd.read_csv(OUT/'captain_seasons.csv')
    pairs+= [dict(season=x.season,mode=x.mode,candidate='captain_gate',control=REF,gain=x.gain) for x in cap.itertuples()]
    pairs=pd.DataFrame(pairs);pairs.to_csv(OUT/'paired_seasons.csv',index=False)
    stats=[];rng=np.random.default_rng(173)
    for (mode,candidate,control),g in pairs.groupby(['mode','candidate','control']):
        vals=g.sort_values('season').gain.to_numpy();boot=rng.choice(vals,size=(50000,len(vals)),replace=True).mean(axis=1)
        stats.append(dict(mode=mode,candidate=candidate,control=control,mean_gain=vals.mean(),wins=int((vals>0).sum()),min_gain=vals.min(),max_gain=vals.max(),low95=np.quantile(boot,.025),high95=np.quantile(boot,.975)))
    stats=pd.DataFrame(stats);stats.to_csv(OUT/'paired_summary.csv',index=False)
    d=pd.DataFrame(diag);d.to_csv(OUT/'ranking_weekly.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    per=d.groupby(['season','model','stratum'])[['precision','recall','ndcg','mean_points']].mean().reset_index();per.to_csv(OUT/'ranking_by_season.csv',index=False)
    per.groupby(['model','stratum'])[['precision','recall','ndcg','mean_points']].mean().reset_index().to_csv(OUT/'ranking_summary.csv',index=False)
    checks=dict(outer_seasons=5,main_simulations=40,captain_replays=10,main_decisions=1360,captain_decisions=340,temporal_checks=True,identical_handoff=True,accounting=True,tail_control_max=float(audit.tail_control_max.max()),nonoptimal=int(r[r.model.isin(MODELS)].nonoptimal.sum()),max_solver_gap=float(r[r.model.isin(MODELS)].max_solver_gap.max()))
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2))
    print(summary.to_string(index=False));print(stats.to_string(index=False));print(checks)
if __name__=='__main__':main()
