"""Prospective chip policies. Functions deciding actions never receive outcomes."""
from pathlib import Path
import sys,copy,json,pickle,gzip,time,hashlib
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
import experiment
from decision_specialist.planner import choose
from fixture_strategy.run import SEASONS
OUT=HERE/'results';TYPES=['triple_captain','bench_boost','free_hit','wildcard']
RESERVE={'triple_captain':8.,'bench_boost':12.,'free_hit':12.,'wildcard':12.}

def advance(state,c,chip):
    result=copy.deepcopy(state)
    if chip!='free_hit':
        result['owned']={i:state['owned'].get(i,c['prices'][i]) for i in c['squad']};result['bank']=c['bank_after']
    result['ft']=experiment.next_free(state['ft'],c['transfers'],chip)
    return result

def schedule(gw,width,fixed):
    if fixed.get(gw)=='free_hit':return ['free_hit']
    end=min(39,gw+width)
    for w in range(gw+1,end):
        if fixed.get(w) in ['wildcard','free_hit']:end=w;break
    return [fixed.get(w) for w in range(gw,end)]

def select_plan(p,xp,state,gw,fixed,chip=None):
    chips=schedule(gw,min(3,xp.shape[1]),fixed)
    if chip is not None:chips[0]=chip
    if chips[0]=='free_hit':
        first=choose(p,xp[:,:1],state['owned'],state['bank'],state['ft'],['free_hit'])
        # Temporary squad disappears; continuation starts from the original squad/bank.
        score=first['objective'];calls=[first]
        if len(chips)>1:
            restored=advance(state,first,'free_hit')
            continuation=choose(p,xp[:,1:len(chips)],restored['owned'],restored['bank'],restored['ft'],chips[1:])
            score+=continuation['objective'];calls.append(continuation)
        return first,score,calls
    first=choose(p,xp[:,:len(chips)],state['owned'],state['bank'],state['ft'],chips)
    return first,first['objective'],[first]

def reserve_value(chip,gw):
    end=19 if gw<=19 else 38;start=5 if gw<=19 else 20
    return RESERVE[chip]*(.5+.5*(end-gw)/max(1,end-start))

def decide(p,xp,state,gw,fixed,remaining,last):
    normal,base,calls=select_plan(p,xp,state,gw,fixed)
    if gw in fixed:return fixed[gw],normal,[],calls
    end=19 if gw<=19 else 38
    slots=sum(w not in fixed for w in range(gw,end+1));force=slots<=len(remaining)
    candidates=[]
    for chip in TYPES:
        if chip not in remaining or (chip=='free_hit' and last=='free_hit'):continue
        choice,score,extra=select_plan(p,xp,state,gw,fixed,chip);calls+=extra
        gain=score-base;reserve=reserve_value(chip,gw);future=0.
        if not force:
            # Reuse the ordinary prospective path; no realised future state is read.
            path=[normal]+normal['plan'];projected=copy.deepcopy(state)
            for j in range(1,min(3,len(path)+1,xp.shape[1])):
                prev=path[j-1];previous_chip=fixed.get(gw+j-1)
                projected=advance(projected,prev,previous_chip)
                if gw+j>end or gw+j in fixed or (chip=='free_hit' and previous_chip=='free_hit'):continue
                _,b,extra=select_plan(p,xp[:,j:],projected,gw+j,fixed);calls+=extra
                _,v,extra=select_plan(p,xp[:,j:],projected,gw+j,fixed,chip);calls+=extra
                future=max(future,(.9**j)*(v-b))
            # Cheap outer-window option value for point-multiplying chips only.
            index={int(pid):i for i,pid in enumerate(p.pid)}
            for j in range(3,min(xp.shape[1],end-gw+1)):
                if gw+j in fixed:continue
                if chip=='triple_captain':v=float(np.max(xp[p.can_buy.to_numpy()|p.pid.isin(state['owned']).to_numpy(),j]))
                elif chip=='bench_boost':v=.9*sum(xp[index[i],j] for i in normal['bench'])
                else:continue
                future=max(future,(.9**j)*v)
        threshold=0. if force else max(reserve,future)
        candidates.append(dict(chip=chip,gain=float(gain),reserve=float(reserve),future_value=float(future),threshold=float(threshold),net_value=float(gain-threshold),choice=choice))
    eligible=candidates if force else [x for x in candidates if x['net_value']>0]
    best=max(eligible,key=lambda x:(x['net_value'],-TYPES.index(x['chip']))) if eligible else None
    audit=[{k:v for k,v in x.items() if k!='choice'} for x in candidates]
    return (best['chip'],best['choice'],audit,calls) if best else (None,normal,audit,calls)

def run(task):
    s,mode=task;path=OUT/f'trace_{s}_full_h3_{mode}.json.gz'
    if path.exists():return json.loads(gzip.decompress(path.read_bytes()))['summary']
    adaptive=set(TYPES if mode=='adaptive_all' else [mode.removeprefix('adaptive_')])
    fixed={w:c for w,c in experiment.CAL.items() if c not in adaptive}
    games=pickle.load(open(CURRENT/f'results/games_{s}.pkl','rb'));predictions=pd.read_csv(OUT/f'forecast_{s}.csv.gz')
    state,opening=experiment.opening(s);handoff=copy.deepcopy(state);remaining=adaptive&state['chips'];rows=[];last=None;solver_status=[];gaps=[]
    for gw in range(5,39):
        if gw==20:remaining=adaptive.copy()
        g=games[gw];p=g['frame'];q=predictions[predictions.gw==gw]
        assert np.array_equal(p.pid,q.pid) and (pd.to_datetime(q.cutoff,utc=True)==pd.Timestamp(g['cutoff'])).all()
        xp=q[[f'full_{j}' for j in range(8)]].to_numpy()[:,:min(8,39-gw)]
        chip,c,audit,calls=decide(p,xp,state,gw,fixed,remaining,last)
        for x in calls:solver_status.append(x['solver_status']);gaps.append(x['solver_gap'])
        if chip in adaptive:assert chip in remaining;remaining.remove(chip)
        assert not (last=='free_hit' and chip=='free_hit')
        r=experiment.settle(c['starters'],c['bench'],c['captain'],c['vice'],dict(zip(p.pid,p.pos)),g['actual'],g['active'],chip)
        before=copy.deepcopy(state);state=advance(state,c,chip)
        if chip=='free_hit':assert state['owned']==before['owned'] and state['bank']==before['bank'] and state['ft']==before['ft']
        assert state['bank']>=0 and 1<=state['ft']<=5
        assert r['gross']==sum(g['actual'].get(i,0) for i in r['counted'])+r['captain_bonus']
        rows.append(dict(gw=gw,net=r['gross']-4*c['paid'],gross=r['gross'],hits=4*c['paid'],chip=chip or '',transfers=c['transfers'],bank=state['bank'],ft=state['ft'],squad=sorted(c['squad']),starters=c['starters'],bench=c['bench'],captain=c['captain'],vice=c['vice'],incoming=sorted(c['incoming']),outgoing=sorted(c['outgoing']),captain_bonus=r['captain_bonus'],counted=r['counted'],contributions={str(i):g['actual'].get(i,0) for i in r['counted']},persistent_squad=sorted(state['owned']),remaining=sorted(remaining),chip_candidates=audit,solver_status=c['solver_status'],solver_gap=c['solver_gap']))
        last=chip
        if gw in [19,38]:assert not remaining,remaining
        if gw%5==0:print('PROGRESS',s,mode,gw,flush=True)
    summary=dict(season=s,model='full_h3',forecast_model='full',horizon=3,mode=mode,points38=sum(r['net'] for r in opening)+sum(r['net'] for r in rows),opening_points=sum(r['net'] for r in opening),hits=sum(r['hits'] for r in rows),transfers=sum(r['transfers'] for r in rows),nonoptimal=sum(x!=0 for x in solver_status),max_solver_gap=max(gaps),solver_calls=len(gaps))
    obj=dict(summary=summary,opening=opening,handoff=dict(owned=handoff['owned'],bank=handoff['bank'],ft=handoff['ft']),trace=rows)
    path.write_bytes(gzip.compress(json.dumps(obj,default=lambda x:x.item() if isinstance(x,np.generic) else list(x)).encode(),mtime=0));return summary

def main():
    paths=[HERE/'chips.py',HERE/'protocol.json',CURRENT/'decision_specialist/planner.py',CURRENT/'experiment.py']+list(OUT.glob('forecast_*.csv.gz'))
    sig={str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths};manifest=OUT/'manifest_chips.json'
    if manifest.exists():assert json.loads(manifest.read_text())==sig
    else:manifest.write_text(json.dumps(sig,indent=2))
    tasks=[(s,'adaptive_'+m) for m in TYPES+['all'] for s in SEASONS];rows=[];start=time.time()
    with ProcessPoolExecutor(max_workers=4) as ex:
        for i,f in enumerate(as_completed([ex.submit(run,t) for t in tasks]),1):
            rows.append(f.result());pd.DataFrame(rows).to_csv(OUT/'seasons_chips.csv',index=False);print('DONE',i,len(tasks),rows[-1],'seconds',round(time.time()-start),flush=True)
if __name__=='__main__':main()
