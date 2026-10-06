"""Rolling multi-stage MILP with cash, FT carry and explicit future transfers."""
import numpy as np
from scipy.optimize import milp,Bounds,LinearConstraint
from scipy.sparse import coo_matrix
from decision import selling_price,next_free,legal_positions

def shortlist(pool,forecast,owned):
    p=pool.copy();p['xp']=forecast[:,0];p['mean']=forecast.mean(axis=1)
    ids=set(owned)
    for pos in [1,2,3,4]:
        g=p[(p.pos==pos)&p.can_buy]
        for score in ['xp','mean']:ids.update(g.nlargest(12 if pos==1 else 22,score).pid)
        ids.update(g.sort_values(['market','xp','pid'],ascending=[True,False,True]).head(8).pid)
        ids.update(g.assign(value=g.xp/g.market).nlargest(8,'value').pid)
    idx=np.flatnonzero(p.pid.isin(ids));order=np.argsort(p.iloc[idx].pid.to_numpy())
    idx=idx[order]
    return pool.iloc[idx].reset_index(drop=True),forecast[idx]

def solve(pool,forecast,owned,bank,ft,chips,keep_only=False):
    p=pool.reset_index(drop=True);n=len(p);H=len(chips);forecast=forecast[:,:H]
    ids=p.pid.to_numpy(dtype=int);positions=p.pos.to_numpy();market=p.market.to_numpy(dtype=int)
    own=np.array([i in owned for i in ids]);initial=own.astype(int)
    sell=np.array([selling_price(owned[i],v) if i in owned else v for i,v in zip(ids,market)])
    # x ownership, l starters, c captain, u purchases, v sales; 80 FT transition arcs and cash.
    stride=5*n+81;size=H*stride;obj=np.zeros(size);upper=np.ones(size);integrality=np.ones(size)
    def ix(t,block):return np.arange(t*stride+block*n,t*stride+(block+1)*n)
    def arc(t):return np.arange(t*stride+5*n,t*stride+5*n+80)
    def cash(t):return (t+1)*stride-1
    rr=[];cc=[];vv=[];lower=[];higher=[]
    def add(indices,values,lo=-np.inf,hi=np.inf):
        indices=np.asarray(indices,dtype=int);values=np.broadcast_to(values,indices.shape)
        rr.extend([len(lower)]*len(indices));cc.extend(indices);vv.extend(values);lower.append(lo);higher.append(hi)
    states=np.repeat(np.arange(1,6),16);counts=np.tile(np.arange(16),5)
    successors=[]
    for t in range(H):
        x,l,c,u,v=[ix(t,b) for b in range(5)];a=arc(t);chip=chips[t];ordinary=chip not in ['wildcard','free_hit']
        xp=forecast[:,t]
        obj[x]=-(1 if chip=='bench_boost' else .1)*xp+1e-7*market+np.arange(n)*1e-10
        obj[l]=-(1e-6 if chip=='bench_boost' else .9)*xp
        obj[c]=-(2 if chip=='triple_captain' else 1)*xp
        obj[u]=.5 if ordinary else 0
        obj[a]=4*np.maximum(0,counts-states) if ordinary else 0
        successor=np.minimum(5,np.maximum(0,states-counts)+1) if ordinary else states
        successors.append(successor)
        upper[cash(t)]=100000;integrality[cash(t)]=0
        upper[u]=(~own)&p.can_buy.to_numpy() # never rebuy an initial holding in this plan
        upper[x]=p.can_buy.to_numpy()|own
        add(x,1,15,15);add(l,1,11,11);add(c,1,1,1)
        for pos,total,minimum,maximum in [(1,2,1,1),(2,5,3,5),(3,5,2,5),(4,3,1,3)]:
            mask=np.flatnonzero(positions==pos);add(x[mask],1,total,total);add(l[mask],1,minimum,maximum)
        for club in p.club.unique():
            mask=np.flatnonzero(p.club.to_numpy()==club);cap=max(3,len(mask)) if keep_only else 3
            add(x[mask],1,hi=cap)
        for i in range(n):
            add([l[i],x[i]],[1,-1],hi=0);add([c[i],l[i]],[1,-1],hi=0)
            prev=[ix(t-1,0)[i]] if t else []
            val=[1,-1,1]+([-1] if t else [])
            add([x[i],u[i],v[i]]+prev,val,0 if t else initial[i],0 if t else initial[i])
            add([u[i],v[i]],[1,1],hi=1)
        add(a,1,1,1);add(np.r_[u,a],np.r_[np.ones(n),-counts],0,0)
        if t==0:add(a,states,ft,ft)
        else:add(np.r_[a,arc(t-1)],np.r_[states,-successors[t-1]],0,0)
        inds=np.r_[cash(t),u,v,([cash(t-1)] if t else [])]
        vals=np.r_[1,market,-sell,([-1] if t else [])]
        add(inds,vals,bank if t==0 else 0,bank if t==0 else 0)
    for i in range(n):
        add([ix(t,3)[i] for t in range(H)],1,hi=1)
        add([ix(t,4)[i] for t in range(H)],1,hi=1)
    matrix=coo_matrix((vv,(rr,cc)),shape=(len(lower),size)).tocsc()
    r=milp(obj,integrality=integrality,bounds=Bounds(np.zeros(size),upper),constraints=LinearConstraint(matrix,lower,higher),options={'time_limit':5,'mip_rel_gap':.001})
    if r.x is None:raise RuntimeError(f'No feasible plan: {r.message}')
    plan=[];current_owned=dict(owned);current_bank=bank;free=ft
    for t in range(H):
        chosen=set(ids[r.x[ix(t,0)]>.5]);start=ids[r.x[ix(t,1)]>.5].tolist();incoming=chosen-set(current_owned);outgoing=set(current_owned)-chosen
        xp=dict(zip(ids,forecast[:,t]));order=sorted(start,key=lambda i:(-xp[i],i));cap,vice=order[:2]
        bench=sorted(chosen-set(start),key=lambda i:(0 if positions[np.flatnonzero(ids==i)[0]]==1 else 1,-xp[i],i))
        prices={int(i):int(v) for i,v in zip(ids,market)};after=current_bank+sum(selling_price(current_owned[i],prices[i]) for i in outgoing)-sum(prices[i] for i in incoming)
        transfers=len(incoming);paid=max(0,transfers-free) if chips[t] not in ['wildcard','free_hit'] else 0
        assert after==round(r.x[cash(t)]) and after>=0
        assert np.isclose(r.x[arc(t)]@states,free) and np.isclose(r.x[arc(t)]@counts,transfers)
        assert legal_positions(start,dict(zip(ids,positions))) and len(chosen)==15
        row=dict(squad=chosen,starters=start,bench=bench,captain=cap,vice=vice,incoming=incoming,outgoing=outgoing,transfers=transfers,paid=paid,bank_after=int(after),prices=prices,free_before=free)
        plan.append(row)
        if chips[t]!='free_hit':current_owned={i:current_owned.get(i,prices[i]) for i in chosen};current_bank=after
        free=next_free(free,transfers,chips[t])
    choice=plan[0];choice.update(solver_gap=float(r.mip_gap),solver_status=int(r.status),pool_size=n,planned_horizon=H,plan=plan[1:],objective=float(-r.fun))
    return choice

def choose(pool,forecast,owned,bank,ft,chips):
    p,f=shortlist(pool,forecast,owned)
    over=pool[pool.pid.isin(owned)].groupby('club').size().max()>3
    result=solve(p,f,owned,bank,ft,chips)
    if over and chips[0] is None:
        mask=p.pid.isin(owned).to_numpy();keep=solve(p[mask],f[mask],owned,bank,ft,chips,True)
        if keep['objective']>result['objective']+1e-8:result=keep
    return result
