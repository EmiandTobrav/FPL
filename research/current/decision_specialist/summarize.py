from pathlib import Path
import sys,json,gzip,pickle
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
import experiment
from retrained_ensemble.run import games_for
from decision_specialist.run_horizon import fingerprint as horizon_fingerprint
from decision_specialist.run_gate import fingerprint as gate_fingerprint
OUT=HERE/'results';REF='mix_ridge_extra_50'

def read_trace(s,m,mode):
    root=OUT
    if m==REF or m in ['ridge','extra']:root=CURRENT/'results'
    elif m in ['re_refresh','extra_refresh','three_refresh']:root=CURRENT/'retrained_ensemble/results'
    elif m=='rich_refresh':root=CURRENT/'adaptive_events/results'
    return json.loads(gzip.decompress((root/f'trace_{s}_{m}_{mode}.json.gz').read_bytes()))

def paired_results(rows,comparisons,label):
    pairs=[]
    for a,b in comparisons:
        aa=rows[rows.model==a];bb=rows[rows.model==b]
        merged=aa.merge(bb,on=['season','mode'],suffixes=('_a','_b'),validate='one_to_one')
        for r in merged.itertuples():pairs.append(dict(season=r.season,mode=r.mode,comparison=a+' - '+b,gain=r.points38_a-r.points38_b))
    p=pd.DataFrame(pairs);p.to_csv(OUT/f'{label}_paired_seasons.csv',index=False);rng=np.random.default_rng(173);summary=[]
    for (mode,c),g in p.groupby(['mode','comparison']):
        v=g.gain.to_numpy();boot=rng.choice(v,size=(50000,len(v)),replace=True).mean(axis=1)
        summary.append(dict(mode=mode,comparison=c,mean_gain=v.mean(),wins=int((v>0).sum()),seasons=len(v),minimum=v.min(),maximum=v.max(),low95=np.quantile(boot,.025),high95=np.quantile(boot,.975)))
    pd.DataFrame(summary).to_csv(OUT/f'{label}_paired_summary.csv',index=False)

def selection(data,label):
    seasons=sorted(data.season.unique());rows=[]
    for mode in ['fixed_chips','no_chips']:
        d=data[data['mode']==mode]
        for s in seasons[2:]:
            before=d[d.season<s].groupby('model').gain.agg(['mean','std']);merit=before['mean']-.25*before['std'].fillna(0);best=merit.idxmax();chosen=REF if merit[REF]>=merit[best]-2 else best
            r=d[(d.season==s)&(d.model==chosen)].iloc[0];rows.append(dict(season=s,mode=mode,selected=chosen,gain=r.gain))
    pd.DataFrame(rows).to_csv(OUT/f'{label}_selection.csv',index=False)

def main():
    assert json.loads((OUT/'horizon_manifest.json').read_text())==horizon_fingerprint()
    assert json.loads((OUT/'gate_manifest.json').read_text())==gate_fingerprint()
    audit=pd.read_csv(OUT/'gate_training_audit.csv');assert len(audit)==4
    assert (pd.to_datetime(audit.max_label_available,utc=True)<pd.to_datetime(audit.cutoff,utc=True)).all()
    all_rows={};verification=[]
    horizon_models=[f'{m}_h{h}' for m in ['reference','extra_refresh','re_refresh'] for h in [1,3]]
    for label,seasons,models in [('horizon',experiment.SEASONS,horizon_models+[REF]),('gate',experiment.SEASONS[2:],['gate','constant','three_refresh','re_refresh','rich_refresh','extra_refresh',REF])]:
        rows=[]
        for s in seasons:
            with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
            for mode in ['fixed_chips','no_chips']:
                base=read_trace(s,REF,mode)
                for m in models:
                    o=read_trace(s,m,mode);assert o['handoff']==base['handoff'] and o['opening']==base['opening'];summary=o['summary']
                    assert len(o['trace'])==34 and summary['points38']==summary['opening_points']+sum(r['net'] for r in o['trace'])
                    for r in o['trace']:
                        assert r['net']==r['gross']-r['hits'] and r['gross']==sum(r['contributions'].values())+r['captain_bonus']
                        p=games[r['gw']]['frame'].set_index('pid');assert p.loc[r['squad']].pos.value_counts().to_dict()=={1:2,2:5,3:5,4:3}
                        assert r['bank']>=0 and 1<=r['ft']<=5
                        if 'planned_horizon' in r:assert len(r['plan'])==r['planned_horizon']-1
                    rows.append(summary);verification.append(dict(experiment=label,season=s,model=m,mode=mode,verified_rounds=34))
        data=pd.DataFrame(rows);reference=data[data.model==REF][['season','mode','points38']].rename(columns={'points38':'reference_points'});data=data.merge(reference,on=['season','mode']);data['gain']=data.points38-data.reference_points
        data.to_csv(OUT/f'{label}_all_seasons.csv',index=False)
        summary=data.groupby(['mode','model']).agg(mean_points=('points38','mean'),gain=('gain','mean'),wins=('gain',lambda x:int((x>0).sum())),mean_hits=('hits','mean'),mean_transfers=('transfers','mean'),nonoptimal=('nonoptimal','sum'),max_gap=('max_solver_gap','max')).reset_index();summary.to_csv(OUT/f'{label}_summary.csv',index=False);print(label,summary.to_string(index=False));all_rows[label]=data
    comps=[(m,REF) for m in horizon_models]+[(m+'_h3',m+'_h1') for m in ['reference','extra_refresh','re_refresh']]+[(m+'_h3','reference_h3') for m in ['extra_refresh','re_refresh']]
    paired_results(all_rows['horizon'],comps,'horizon')
    paired_results(all_rows['gate'],[('gate',m) for m in ['constant','three_refresh','re_refresh','rich_refresh',REF]]+[('constant','three_refresh'),('constant',REF),('gate','extra_refresh'),('constant','extra_refresh')],'gate')
    selection(all_rows['horizon'],'horizon');selection(all_rows['gate'][all_rows['gate'].model.isin(['gate','constant','three_refresh',REF])],'gate')
    # Record differences attributable to changing the decision engine, independent of H3.
    parity=[]
    for s in experiment.SEASONS:
        gpar=games_for(s)
        for mode in ['fixed_chips','no_chips']:
            for m,old in [('reference',REF),('extra_refresh','extra_refresh'),('re_refresh','re_refresh')]:
                a=read_trace(s,m+'_h1',mode);b=read_trace(s,old,mode)
                first={}
                for x,y in zip(a['trace'],b['trace']):
                    if set(x['squad'])!=set(y['squad']):
                        g=gpar[x['gw']];xp=dict(zip(g['frame'].pid,experiment.xp_for(g,old)))
                        def value(row):
                            holding=sum(xp[i] for i in row['squad']) if row['chip']=='bench_boost' else sum(xp[i] for i in row['starters'])+.1*sum(xp[i] for i in row['bench'])
                            return holding+(2 if row['chip']=='triple_captain' else 1)*xp[row['captain']]-row['hits']-(.5*row['transfers'] if row['chip'] not in ['wildcard','free_hit'] else 0)
                        first=dict(first_squad_difference_gw=x['gw'],first_squad_objective_difference=value(x)-value(y));break
                parity.append(dict(season=s,mode=mode,model=m,points_difference=a['summary']['points38']-b['summary']['points38'],different_squads=sum(set(x['squad'])!=set(y['squad']) for x,y in zip(a['trace'],b['trace'])),**first))
    pd.DataFrame(parity).to_csv(OUT/'h1_engine_parity.csv',index=False)
    from upside.summarize import ranked_metrics
    diagnostics=[];weights=[]
    for s in experiment.SEASONS[2:]:
        games=games_for(s);pred=pd.read_csv(OUT/f'gate_{s}.csv.gz')
        for gw in range(5,39):
            g=games[gw];p=pred[pred.gw==gw];ids=p.pid.to_numpy();y=p.actual.to_numpy();scheduled=p['count'].to_numpy()>0
            ref=experiment.xp_for(g,REF);relevant=np.zeros(len(p),bool);idx=np.flatnonzero(scheduled);relevant[idx[np.lexsort((ids[idx],-ref[idx]))[:60]]]=True
            masks={'all':scheduled,'rotation':scheduled&(p.minutes_m6.to_numpy()>=30)&(p.minutes_m6.to_numpy()<70),'falling':scheduled&((p.minutes_m6-p.minutes_m12).to_numpy()<=-15),'short_history':scheduled&(g['n_history']<12)}
            for m in ['gate','constant','three_refresh','re_refresh','rich_refresh',REF]:
                score=p[m].to_numpy() if m in ['gate','constant'] else experiment.xp_for(g,m)
                for group,mask in masks.items():
                    rm=mask&relevant;e=score[rm]-y[rm];k=20 if group=='all' else 10
                    rank=ranked_metrics(y[mask],score[mask],ids[mask],k) if mask.sum()>=k else dict(mean_points=np.nan,precision=np.nan,ndcg=np.nan)
                    diagnostics.append(dict(season=s,gw=gw,model=m,group=group,n_relevant=int(rm.sum()),se=float((e*e).sum()),top_points=rank['mean_points'],precision=rank['precision'],ndcg=rank['ndcg']))
            for group,mask in masks.items():
                weights.append(dict(season=s,gw=gw,group=group,n=int(mask.sum()),mean_gate_weight=float(p.gate_weight.to_numpy()[mask].mean()) if mask.any() else np.nan,constant_weight=float(p.constant_weight.iloc[0])))
    d=pd.DataFrame(diagnostics);d.to_csv(OUT/'gate_diagnostics_weekly.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    keys=['season','model','group'];per=d.groupby(keys)[['n_relevant','se']].sum().join(d.groupby(keys)[['top_points','precision','ndcg']].mean()).reset_index();per['rmse']=np.sqrt(per.se/per.n_relevant.replace(0,np.nan));per.to_csv(OUT/'gate_diagnostics_seasons.csv',index=False);per.groupby(['model','group'])[['rmse','top_points','precision','ndcg']].mean().to_csv(OUT/'gate_diagnostics_summary.csv')
    pd.DataFrame(weights).to_csv(OUT/'gate_weights_weekly.csv',index=False)
    pd.DataFrame(verification).to_csv(OUT/'trace_verification.csv',index=False)
    new_h=all_rows['horizon'][all_rows['horizon'].model!=REF];new_g=all_rows['gate'][all_rows['gate'].model.isin(['gate','constant'])]
    checks=dict(horizon_new_simulations=len(new_h),gate_new_simulations=len(new_g),new_decisions=(len(new_h)+len(new_g))*34,temporal_meta_training=True,matched_openings=True,point_accounting=True,horizon_nonoptimal=int(new_h.nonoptimal.sum()),horizon_max_gap=float(new_h.max_solver_gap.max()),gate_nonoptimal=int(new_g.nonoptimal.sum()),gate_max_gap=float(new_g.max_solver_gap.max()))
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2));print(checks)
if __name__=='__main__':main()
