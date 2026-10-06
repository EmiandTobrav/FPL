from pathlib import Path
import sys,json,gzip,pickle,hashlib
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from calendar_counts.run import fingerprint,SEASONS
OUT=HERE/'results'

def read(p):return json.loads(gzip.decompress(p.read_bytes()))

def main():
    assert json.loads((OUT/'run_manifest.json').read_text())==fingerprint()
    benchmark=json.loads((CURRENT/'benchmark.json').read_text());rows=[];parity=[]
    for s in SEASONS:
        with open(CURRENT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
        for mode in ['fixed_chips','no_chips']:
            archive=CURRENT/f'global_horizon/results/trace_{s}_constant_h3_{mode}.json.gz'
            assert hashlib.sha256(archive.read_bytes()).hexdigest()==benchmark['trace_sha256'][str(archive.relative_to(CURRENT))]
            base=read(archive)
            for m in ['constant','calendar_count']:
                o=read(OUT/f'trace_{s}_{m}_h3_{mode}.json.gz');r=o['summary']
                assert o['opening']==base['opening'] and o['handoff']==base['handoff']
                assert len(o['trace'])==34 and r['points38']==r['opening_points']+sum(x['net'] for x in o['trace'])
                for x in o['trace']:
                    p=games[x['gw']]['frame'].set_index('pid');squad=p.loc[x['squad']]
                    assert squad.pos.value_counts().to_dict()=={1:2,2:5,3:5,4:3} and squad.club.value_counts().max()<=3
                    assert x['bank']>=0 and 1<=x['ft']<=5
                    assert x['net']==x['gross']-x['hits'] and x['gross']==sum(x['contributions'].values())+x['captain_bonus']
                r['benchmark_points']=base['summary']['points38'];r['gain']=r['points38']-r['benchmark_points'];rows.append(r)
                if m=='constant':
                    differences=sum(any(x[k]!=y[k] for k in ['squad','starters','bench','captain','vice','net']) for x,y in zip(o['trace'],base['trace']))
                    parity.append(dict(season=s,mode=mode,score_difference=r['gain'],different_decisions=differences));assert differences==0 and r['gain']==0
    data=pd.DataFrame(rows).sort_values(['mode','model','season']);data.to_csv(OUT/'all_seasons.csv',index=False)
    rng=np.random.default_rng(173);summary=[]
    for (mode,model),g in data.groupby(['mode','model']):
        v=g.gain.to_numpy();boot=rng.choice(v,(50000,len(v)),replace=True).mean(axis=1)
        summary.append(dict(mode=mode,model=model,mean_points=g.points38.mean(),gain=v.mean(),wins=int((v>0).sum()),low95=np.quantile(boot,.025),high95=np.quantile(boot,.975),mean_hits=g.hits.mean(),mean_transfers=g.transfers.mean(),nonoptimal=g.nonoptimal.sum(),max_gap=g.max_solver_gap.max()))
    summary=pd.DataFrame(summary);summary.to_csv(OUT/'model_summary.csv',index=False);pd.DataFrame(parity).to_csv(OUT/'engine_parity.csv',index=False)
    audit=pd.read_csv(OUT/'forecast_audit.csv');assert len(audit)==136 and audit.current_max_difference.max()==0
    assert (pd.to_datetime(audit.snapshot_time,utc=True)<pd.to_datetime(audit.cutoff,utc=True)).all()
    assert (audit.loc[~audit.use_calendar,'changed_future_player_cells']==0).all()
    checks=dict(simulations=len(data),decisions=len(data)*34,identical_benchmark_decisions=True,identical_current_forecasts=True,identical_opening=True,archived_hashes_verified=True,squad_and_accounting_checks=True,snapshots_strictly_before_cutoff=True,stale_snapshot_fallback_verified=True,nonoptimal=int(data.nonoptimal.sum()),max_solver_gap=float(data.max_solver_gap.max()))
    (OUT/'checks.json').write_text(json.dumps(checks,indent=2))
    (OUT/'output_manifest.json').write_text(json.dumps({p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.glob('*')) if p.is_file() and p.name!='output_manifest.json'},indent=2));print(summary.to_string(index=False));print(checks)
if __name__=='__main__':main()
