"""Extended squad objective: current XI/captain plus forecast holding value.
Future value is a linear squad approximation, not a full multistage optimum.
"""
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from season_simulator import selling_price,legal_positions,settle,next_free
import numpy as np,pandas as pd
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix
def choose(pool,owned,bank,ft,chip=None,bench_weight=.10,transfer_friction=.5,full_pool=False):
    """Same one-week policy for every forecast model. No future forecast rows.
    0.5 expected-point friction per ordinary transfer values continuity/free slots.
    Up to 20 transfers each ordinary GW; WC/FH unrestricted. Candidate shortlist
    uses projections and prices only. Optimality refers to that shortlist.
    """
    p=pool.copy();p['owned']=p.pid.isin(owned)
    if not full_pool:
        ids=set(owned)
        for pos in [1,2,3,4]:
            g=p[(p.pos==pos)&p.can_buy].copy();g['rank_xp']=g.xp+g.bonus
            ids.update(g.nlargest(22 if pos!=1 else 12,'rank_xp').pid)
            ids.update(g.nlargest(22 if pos!=1 else 12,'xp').pid)
            ids.update(g.sort_values(['market','xp','pid'],ascending=[True,False,True]).head(8).pid)
            ids.update(g.assign(value=g.xp/g.market).nlargest(8,'value').pid)
        p=p[p.pid.isin(ids)].copy()
    p=p.sort_values('pid').reset_index(drop=True)
    n=len(p);size=3*n+1;xp=np.maximum(p.xp.to_numpy(),0)
    own=p.owned.to_numpy();market=p.market.to_numpy(dtype=int)
    price=np.array([selling_price(owned[int(pid)],int(v)) if int(pid) in owned else int(v) for pid,v in zip(p.pid,market)])
    total_funds=bank+price[own].sum()
    obj=np.zeros(size)
    if chip=='bench_boost':obj[:n]=-xp;obj[n:2*n]=-1e-6*xp
    else:obj[:n]=-bench_weight*xp;obj[n:2*n]=-(1-bench_weight)*xp
    obj[2*n:3*n]=-(2 if chip=='triple_captain' else 1)*xp
    ordinary=bool(owned) and chip not in ['wildcard','free_hit']
    if ordinary:obj[:n]+=transfer_friction*(~own)
    # Stable tie breaking favouring fewer transfers, cheaper squad then lower ID.
    obj[:n]+=1e-7*market+np.arange(n)*1e-10
    obj[:n]-=p.bonus.to_numpy()
    obj[-1]=4
    rr=[];cc=[];vv=[];lo=[];hi=[]
    def add(idx,val,l=-np.inf,u=np.inf):
        row=len(lo);idx=np.asarray(list(idx),dtype=int);val=np.broadcast_to(val,idx.shape)
        rr.extend([row]*len(idx));cc.extend(idx.tolist());vv.extend(val.tolist());lo.append(l);hi.append(u)
    add(range(n),1,15,15);add(range(n,2*n),1,11,11);add(range(2*n,3*n),1,1,1)
    add(range(n),price,u=total_funds)
    for pos,count,l,u in [(1,2,1,1),(2,5,3,5),(3,5,2,5),(4,3,1,3)]:
        idx=np.flatnonzero(p.pos.to_numpy()==pos);add(idx,1,count,count);add(idx+n,1,l,u)
    for club in p.club.unique():
        idx=np.flatnonzero(p.club.to_numpy()==club)
        cap=max(3,len(idx)) if set(p.pid)==set(owned) else 3
        add(idx,1,u=cap)
    for i in range(n):add([n+i,i],[1,-1],u=0);add([2*n+i,n+i],[1,-1],u=0)
    if ordinary:
        idx=np.flatnonzero(~own)
        add(list(idx)+[size-1],list(np.ones(len(idx)))+[-1],u=ft)
        add(idx,1,u=20)
    upper=np.ones(size);upper[-1]=15
    upper[:n]=np.where(p.can_buy.to_numpy()|own,1,0)
    matrix=coo_matrix((vv,(rr,cc)),shape=(len(lo),size)).tocsc()
    r=milp(obj,integrality=np.ones(size),bounds=Bounds(np.zeros(size),upper),
           constraints=LinearConstraint(matrix,lo,hi),options={'time_limit':5,'mip_rel_gap':1e-7})
    if r.x is None:
        if not full_pool:return choose(pool,owned,bank,ft,chip,bench_weight,transfer_friction,True)
        raise RuntimeError(f'No feasible team: {r.message}')
    chosen=p[r.x[:n]>.5].copy();starters=p.loc[r.x[n:2*n]>.5,'pid'].astype(int).tolist()
    # Captain selection from chosen XI is explicit and deterministic.
    order=p[p.pid.isin(starters)].sort_values(['xp','pid'],ascending=[False,True]).pid.astype(int).tolist()
    cap,vice=order[:2]
    bench=p[~p.pid.isin(starters)&p.pid.isin(chosen.pid)].sort_values(['pos','xp','pid'],ascending=[True,False,True])
    bgk=bench[bench.pos==1].pid.astype(int).tolist()
    bout=bench[bench.pos!=1].sort_values(['xp','pid'],ascending=[False,True]).pid.astype(int).tolist()
    ids=set(chosen.pid.astype(int));incoming=ids-set(owned);outgoing=set(owned)-ids
    transfers=len(incoming) if owned else 0;paid=max(0,transfers-ft) if ordinary else 0
    prices=dict(zip(p.pid.astype(int),market.astype(int)))
    after=bank+sum(selling_price(owned[i],prices[i]) for i in outgoing)-sum(prices[i] for i in incoming)
    if not owned:after=bank-sum(prices[i] for i in incoming)
    assert after>=0
    assert len(ids)==15 and len(starters)==11 and len(bgk+bout)==4
    assert chosen.groupby('pos').size().to_dict()=={1:2,2:5,3:5,4:3}
    assert chosen.groupby('club').size().max()<=3 or ids==set(owned)
    assert legal_positions(starters,dict(zip(p.pid,p.pos)))
    return dict(squad=ids,starters=starters,bench=bgk+bout,captain=cap,vice=vice,
                incoming=incoming,outgoing=outgoing,transfers=transfers,paid=paid,bank_after=int(after),
                prices=prices,solver_gap=float(getattr(r,'mip_gap',0)),solver_status=int(r.status),pool_size=len(p))
