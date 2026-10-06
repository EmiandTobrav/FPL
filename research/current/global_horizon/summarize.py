from pathlib import Path
import sys,json,gzip,pickle,hashlib,ast
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from global_horizon.run import fingerprint,SEASONS
OUT=HERE/'results';REF='mix_ridge_extra_50'
MODELS=['constant_h1','constant_h3','re_refresh_h1','re_refresh_h3',REF,'constant_original_engine','extra_refresh']

def read(s,m,mode):
    source=m
    if m.startswith('constant_h'):root=OUT
    elif m==REF:root=CURRENT/'results'
    elif m=='extra_refresh':root=CURRENT/'retrained_ensemble/results'
    else:
        root=CURRENT/'decision_specialist/results'
        if m=='constant_original_engine':source='constant'
    path=root/f'trace_{s}_{source}_{mode}.json.gz'
    if root==CURRENT/'decision_specialist/results':
        manifest=json.loads((root/'output_manifest.json').read_text());assert hashlib.sha256(path.read_bytes()).hexdigest()==manifest[path.name]
    obj=json.loads(gzip.decompress(path.read_bytes()));obj['summary']['model']=m
    return obj

def main():
    assert json.loads((OUT/'horizon_manifest.json').read_text())==fingerprint()
    def function(path,name):
        return ast.dump(next(n for n in ast.parse(path.read_text()).body if isinstance(n,ast.FunctionDef) and n.name==name),include_attributes=False)
    for name in ['run','horizon_chips']:assert function(HERE/'run.py',name)==function(CURRENT/'decision_specialist/run_horizon.py',name)
    audit=pd.read_csv(OUT/'forecast_audit.csv');assert len(audit)==136 and audit.control_max_difference.max()<1e-12
    rows=[];parity=[]
    for s in SEASONS:
        with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
        for mode in ['fixed_chips','no_chips']:
            base=read(s,REF,mode)
            for m in MODELS:
                o=read(s,m,mode);assert o['handoff']==base['handoff'] and o['opening']==base['opening'];summary=o['summary']
                assert len(o['trace'])==34 and summary['points38']==summary['opening_points']+sum(r['net'] for r in o['trace'])
                for r in o['trace']:
                    assert r['net']==r['gross']-r['hits'] and r['gross']==sum(r['contributions'].values())+r['captain_bonus']
                    p=games[r['gw']]['frame'].set_index('pid');assert p.loc[r['squad']].pos.value_counts().to_dict()=={1:2,2:5,3:5,4:3}
                    assert r['bank']>=0 and 1<=r['ft']<=5
                rows.append(summary)
            a=read(s,'constant_h1',mode);b=read(s,'constant_original_engine',mode)
            parity.append(dict(season=s,mode=mode,points_difference=a['summary']['points38']-b['summary']['points38'],different_squads=sum(set(x['squad'])!=set(y['squad']) for x,y in zip(a['trace'],b['trace']))))
    data=pd.DataFrame(rows);ref=data[data.model==REF][['season','mode','points38']].rename(columns={'points38':'reference_points'});data=data.merge(ref,on=['season','mode']);data['gain']=data.points38-data.reference_points;data.to_csv(OUT/'all_seasons.csv',index=False)
    summary=data.groupby(['mode','model']).agg(mean_points=('points38','mean'),gain=('gain','mean'),wins=('gain',lambda x:int((x>0).sum())),mean_hits=('hits','mean'),mean_transfers=('transfers','mean'),nonoptimal=('nonoptimal','sum'),max_gap=('max_solver_gap','max')).reset_index();summary.to_csv(OUT/'model_summary.csv',index=False)
    pairs=[]
    for a,b in [('constant_h3','constant_h1'),('constant_h3','re_refresh_h3'),('constant_h3',REF),('constant_h3','extra_refresh'),('constant_h3','constant_original_engine'),('constant_h1','re_refresh_h1'),('re_refresh_h3','re_refresh_h1')]:
        z=data[data.model==a].merge(data[data.model==b],on=['season','mode'],suffixes=('_a','_b'))
        for r in z.itertuples():pairs.append(dict(season=r.season,mode=r.mode,comparison=a+' - '+b,gain=r.points38_a-r.points38_b))
    for (season,mode),group in data.groupby(['season','mode']):
        z=group.set_index('model').points38
        pairs.append(dict(season=season,mode=mode,comparison='interaction',gain=(z.constant_h3-z.constant_h1)-(z.re_refresh_h3-z.re_refresh_h1)))
    paired=pd.DataFrame(pairs);paired.to_csv(OUT/'paired_seasons.csv',index=False);rng=np.random.default_rng(173);stats=[]
    for (mode,comparison),g in paired.groupby(['mode','comparison']):
        v=g.gain.to_numpy();boot=rng.choice(v,size=(50000,len(v)),replace=True).mean(axis=1)
        stats.append(dict(mode=mode,comparison=comparison,mean_gain=v.mean(),wins=int((v>0).sum()),min_gain=v.min(),max_gain=v.max(),low95=np.quantile(boot,.025),high95=np.quantile(boot,.975)))
    pd.DataFrame(stats).to_csv(OUT/'paired_summary.csv',index=False);pd.DataFrame(parity).to_csv(OUT/'engine_parity.csv',index=False)
    new=data[data.model.isin(['constant_h1','constant_h3'])]
    checks=dict(new_simulations=len(new),new_decisions=len(new)*34,compared_simulations=len(data),matched_matrix_simulations=32,identical_run_function=True,identical_horizon_chip_function=True,control_traces_sha256_verified=True,identical_opening=True,point_accounting=True,forecast_control_max_difference=float(audit.control_max_difference.max()),nonoptimal=int(new.nonoptimal.sum()),max_solver_gap=float(new.max_solver_gap.max()))
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2))
    paths=[p for p in OUT.rglob('*') if p.is_file() and p.name!='output_manifest.json'];(OUT/'output_manifest.json').write_text(json.dumps({str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(paths)},indent=2))
    print(summary.to_string(index=False));print(pd.DataFrame(stats).to_string(index=False));print(checks)
if __name__=='__main__':main()
