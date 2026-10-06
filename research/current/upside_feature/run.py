from pathlib import Path
import sys,pickle,json,gzip,hashlib
from concurrent.futures import ProcessPoolExecutor
import pandas as pd
import numpy as np
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent
sys.path.insert(0,str(CURRENT))
import experiment
from upside_feature.policy import captain_choice
OUT=HERE/'results';SEASONS=experiment.SEASONS[1:]
MODELS=['matched_base','with_tail','blend_base_50','blend_tail_50'];REF='mix_ridge_extra_50'

def games_for(season):
    with open(CURRENT/f'results/games_{season}.pkl','rb') as f:games=pickle.load(f)
    pred=pd.read_csv(OUT/f'predictions_{season}.csv.gz')
    for gw in range(5,39):
        g=games[gw];p=pred[pred.gw==gw]
        assert np.array_equal(p.pid,g['frame'].pid)
        assert (pd.to_datetime(p.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
        ref=experiment.xp_for(g,REF)
        for m in ['matched_base','with_tail','tail']:g['pred'][m]=p[m].to_numpy()
        g['pred']['blend_base_50']=.5*ref+.5*g['pred']['matched_base']
        g['pred']['blend_tail_50']=.5*ref+.5*g['pred']['with_tail']
        g['n_history']=p.n_history.to_numpy()
    return games

def fingerprint():
    paths=list(HERE.glob('*.py'))+[HERE/'protocol.json',CURRENT/'experiment.py',CURRENT/'project/season_simulator.py']
    paths+=list((CURRENT/'upside').glob('*.py'))
    paths+=list((CURRENT/'project/tuning_v3').glob('*.py'))
    paths+=list((CURRENT/'project/tuning_v3').glob('inputs_*.pkl'))+list((CURRENT/'results').glob('games_*.pkl'))
    paths+=list(OUT.glob('predictions_*.csv.gz'))
    paths+=list((CURRENT/'results').glob('trace_*_mix_ridge_extra_50_*.json.gz'))
    return {str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths)) if p.name!='summarize.py'}

def worker(task):return experiment.run(task,games=games_for(task[0]),trace_dir=OUT)

def captain_replay():
    summaries=[];rows=[]
    for season in SEASONS:
        games=games_for(season)
        for mode in ['no_chips','fixed_chips']:
            obj=json.loads(gzip.decompress((CURRENT/f'results/trace_{season}_{REF}_{mode}.json.gz').read_bytes()))
            delta=0;changed=0
            for r in obj['trace']:
                g=games[r['gw']];p=g['frame'];ids=p.pid.to_numpy();mean=dict(zip(ids,experiment.xp_for(g,REF)));tail=dict(zip(ids,g['pred']['tail']))
                cap,vice=captain_choice(r['starters'],mean,tail,r['captain'],r['vice'])
                pos=dict(zip(p.pid,p.pos));chip=r['chip'] or None
                original=experiment.settle(r['starters'],r['bench'],r['captain'],r['vice'],pos,g['actual'],g['active'],chip)
                result=experiment.settle(r['starters'],r['bench'],cap,vice,pos,g['actual'],g['active'],chip)
                assert original['gross']==r['gross'] and original['captain_bonus']==r['captain_bonus']
                assert result['counted']==original['counted']
                gain=result['gross']-original['gross'];delta+=gain;changed+=cap!=r['captain']
                rows.append(dict(season=season,mode=mode,gw=r['gw'],original_captain=r['captain'],captain=cap,vice=vice,changed=cap!=r['captain'],mean_sacrifice=mean[r['captain']]-mean[cap],gain=gain,original_gross=original['gross'],gross=result['gross'],chip=r['chip']))
            summaries.append(dict(season=season,mode=mode,model='captain_gate',points38=obj['summary']['points38']+delta,reference_points=obj['summary']['points38'],gain=delta,changed=changed))
    pd.DataFrame(rows).to_csv(OUT/'captain_decisions.csv',index=False)
    pd.DataFrame(summaries).to_csv(OUT/'captain_seasons.csv',index=False)

def main():
    path=OUT/'run_manifest.json';current=fingerprint()
    if path.exists():assert json.loads(path.read_text())==current,'Stale experiment cache'
    else:
        assert not list(OUT.glob('trace_*.json.gz'))
        path.write_text(json.dumps(current,indent=2))
    tasks=[(s,m,r) for s in SEASONS for m in MODELS for r in ['no_chips','fixed_chips']]
    with ProcessPoolExecutor(max_workers=4) as ex:
        results=[]
        for i,r in enumerate(ex.map(worker,tasks),1):
            results.append(r);print('DONE',i,len(tasks),flush=True)
    pd.DataFrame(results).to_csv(OUT/'new_season_results.csv',index=False)
    captain_replay()
if __name__=='__main__':main()
