"""Outcome-blind common rolling policy, derived from the active benchmark.
Only dated decision pools, origin-made forecasts, and manager state enter here.
"""
import copy
import numpy as np
from planner import choose
from engine import next_free
from initial_optimizer import choose as initial_choose
TYPES=['triple_captain','bench_boost','free_hit','wildcard']
RESERVE={'triple_captain':8.,'bench_boost':12.,'free_hit':12.,'wildcard':12.}
FIXED={6:'wildcard',18:'free_hit',19:'bench_boost',24:'wildcard',33:'free_hit',36:'bench_boost'}

def advance(state,c,chip):
    result=copy.deepcopy(state)
    if chip!='free_hit':
        result['owned']={i:state['owned'].get(i,c['prices'][i]) for i in c['squad']};result['bank']=c['bank_after']
    result['ft']=next_free(state['ft'],c['transfers'],chip,initial=not state['owned'])
    return result

def schedule(gw,width,fixed):
    if fixed.get(gw)=='free_hit':return ['free_hit']
    end=min(39,gw+width)
    for w in range(gw+1,end):
        if fixed.get(w) in ['wildcard','free_hit']:end=w;break
    return [fixed.get(w) for w in range(gw,end)]

def select_plan(p,xp,state,gw,fixed,chip=None):
    if not state['owned']:
        q=p.copy();q['xp']=xp[:,0];q['bonus']=0.
        c=initial_choose(q,{},state['bank'],state['ft'],chip)
        values=dict(zip(q.pid,q.xp));c['plan']=[]
        c['objective']=sum(values[i] for i in c['starters'])+(2 if chip=='triple_captain' else 1)*values[c['captain']]+(1 if chip=='bench_boost' else .1)*sum(values[i] for i in c['bench'])
        return c,c['objective'],[c]
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
        if chip not in remaining or (chip=='free_hit' and last=='free_hit') or (gw==1 and chip in ['free_hit','wildcard']):continue
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

