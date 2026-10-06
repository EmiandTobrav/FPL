from pathlib import Path
import sys,json,gzip
import pandas as pd,numpy as np
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from horizon_upside.run import OUT,SEASONS,MODELS,fingerprint

def main():
    assert json.loads((OUT/'run_manifest.json').read_text())==fingerprint()
    audit=pd.read_csv(OUT/'training_audit.csv');assert (pd.to_datetime(audit.training_max,utc=True)<pd.to_datetime(audit.cutoff,utc=True)).all();assert audit.control_max_difference.max()<1e-5
    results=[];diagnostics=[];legacy=[]
    for s in SEASONS:
        for mode in ['no_chips','fixed_chips']:
            ref=json.loads(gzip.decompress((CURRENT/f'results/trace_{s}_mix_ridge_extra_50_{mode}.json.gz').read_bytes()))
            legacy.append(dict(season=s,mode=mode,points38=ref['summary']['points38']))
            for m in MODELS:
                for h in [1,4]:
                    obj=json.loads(gzip.decompress((OUT/f'trace_{s}_{m}_h{h}_{mode}.json.gz').read_bytes()))
                    summary=obj['summary'];results.append(summary)
                    assert obj['handoff']==ref['handoff'] and obj['opening']==ref['opening']
                    assert summary['points38']==summary['opening_points']+sum(r['net'] for r in obj['trace'])
                    for r in obj['trace']:
                        assert r['net']==r['gross']-r['hits'] and r['gross']==sum(r['contributions'].values())+r['captain_bonus']
                        assert r['bank']>=0 and 1<=r['ft']<=5 and len(set(r['squad']))==15 and len(r['starters'])==11
                        assert r['captain'] in r['starters'] and r['vice'] in r['starters'] and r['captain']!=r['vice']
                        for p in r['plan']:assert p['bank_after']>=0 and 1<=p['free_before']<=5 and len(set(p['squad']))==15
                        diagnostics.append(dict(season=s,mode=mode,model=f'{m}_h{h}',gw=r['gw'],horizon=r['planned_horizon'],status=r['solver_status'],gap=r['solver_gap'],future_transfers=sum(r['planned_transfers'])))
    r=pd.DataFrame(results).sort_values(['season','mode','model']);r.to_csv(OUT/'season_results.csv',index=False)
    legacy=pd.DataFrame(legacy);r=r.merge(legacy.rename(columns={'points38':'legacy_points'}),on=['season','mode']);r['legacy_gain']=r.points38-r.legacy_points
    summary=r.groupby(['mode','model']).agg(mean_points=('points38','mean'),legacy_gain=('legacy_gain','mean'),mean_hits=('hits','mean'),mean_transfers=('transfers','mean'),nonoptimal=('nonoptimal','sum'),max_gap=('max_solver_gap','max')).reset_index();summary.to_csv(OUT/'model_summary.csv',index=False)
    pairs=[]
    comparisons=[('mixture_h4','reference_h4'),('hgb_h4','reference_h4')]+[(f'{m}_h4',f'{m}_h1') for m in MODELS]+[(f'mixture_h{h}',f'hgb_h{h}') for h in [1,4]]+[(f'{m}_h{h}','reference_h1') for m in ['hgb','mixture'] for h in [1,4]]
    for cand,control in comparisons:
        a=r[r.model==cand].merge(r[r.model==control],on=['season','mode'],suffixes=('_a','_b'))
        for x in a.itertuples():pairs.append(dict(season=x.season,mode=x.mode,comparison=cand+' - '+control,gain=x.points38_a-x.points38_b))
    for (s,mode),g in r.groupby(['season','mode']):
        v=g.set_index('model').points38
        pairs.append(dict(season=s,mode=mode,comparison='interaction: mixture horizon gain - HGB horizon gain',gain=(v.mixture_h4-v.mixture_h1)-(v.hgb_h4-v.hgb_h1)))
    pairs=pd.DataFrame(pairs);pairs.to_csv(OUT/'paired_seasons.csv',index=False)
    stats=[];rng=np.random.default_rng(173)
    for (mode,comparison),g in pairs.groupby(['mode','comparison']):
        vals=g.sort_values('season').gain.to_numpy();boot=rng.choice(vals,size=(50000,len(vals)),replace=True).mean(axis=1)
        stats.append(dict(mode=mode,comparison=comparison,mean_gain=vals.mean(),wins=int((vals>0).sum()),min_gain=vals.min(),max_gain=vals.max(),low95=np.quantile(boot,.025),high95=np.quantile(boot,.975)))
    pd.DataFrame(stats).to_csv(OUT/'paired_summary.csv',index=False)
    diag=pd.DataFrame(diagnostics);diag.to_csv(OUT/'solver_decisions.csv.gz',index=False,compression={'method':'gzip','mtime':0})
    checks=dict(simulations=len(r),decisions=len(diag),temporal_training=True,identical_opening=True,accounting=True,max_training_control_error=float(audit.control_max_difference.max()),nonoptimal=int((diag.status!=0).sum()),max_solver_gap=float(diag.gap.max()),mean_h4_length=float(diag[diag.model.str.endswith('h4')].horizon.mean()),h4_decisions_with_future_transfers=int((diag[diag.model.str.endswith('h4')].future_transfers>0).sum()))
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2));print(summary.to_string(index=False));print(pd.DataFrame(stats).to_string(index=False));print(checks)
if __name__=='__main__':main()
