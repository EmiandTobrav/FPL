"""Opening strategies with stateful handover to three frozen receivers.
Selection is forward-only; final historical schedule and price proxies remain limitations.
"""
from pathlib import Path
import json,pickle,copy,gzip,time,argparse
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
from decision import choose,settle,next_free,selling_price
OUT=Path(__file__).resolve().parent
SEASONS=[f'{y}-{str(y+1)[-2:]}' for y in range(2020,2026)]
RECEIVERS=['ridge','bayes','extra']
CHIPS=['wildcard','free_hit','bench_boost','triple_captain']
def projected(game,cfg,name):
 f=game['forecast'][name].copy()
 if cfg.get('scenario','neutral')=='final_calendar':return f
 n=game['neutral'][name];counts=np.maximum(game['fixture_count'],1)
 recent=f[:,0]/counts
 recent=np.where(game['fixture_count']>0,recent,n)
 for k in range(1,f.shape[1]):f[:,k]=np.maximum(0,n+(recent-n)*(.5**k))
 return f

def pool_at(game,cfg,gw,receiver=None):
 p=game['frame'].copy()
 if receiver:
  p['xp']=game['forecast'][receiver][:,0];p['bonus']=0.;return p
 f=(1-cfg['prior_mix'])*projected(game,cfg,'ridge')+cfg['prior_mix']*projected(game,cfg,'prior')
 p['xp']=f[:,0];p['bonus']=0.
 if cfg['look']:p['bonus']+=.8*f[:,1:1+cfg['look']].mean(axis=1)
 if cfg['carry']:
  start=max(0,cfg['handoff']+1-gw);end=min(f.shape[1],start+6)
  continuation=np.mean([projected(game,cfg,m)[:,start:end].mean(axis=1) for m in RECEIVERS],axis=0)
  p['bonus']+=cfg['carry']*.8*continuation
 return p

def expected(choice,p,chip,friction):
 x=p.set_index('pid');ids=list(choice['squad'])
 points=(x.loc[ids,'xp'].sum() if chip=='bench_boost' else x.loc[choice['starters'],'xp'].sum()+.1*x.loc[choice['bench'],'xp'].sum())
 points+=(2 if chip=='triple_captain' else 1)*x.loc[choice['captain'],'xp']
 bonus=x.loc[ids,'bonus'].sum() if chip!='free_hit' else 0
 return float(points+bonus-4*choice['paid']-friction*choice['transfers'])

def act(game,cfg,gw,state,mode,receiver=None):
 p=pool_at(game,cfg,gw,receiver);owned=state['owned'];bank=state['bank'];ft=state['ft'];initial=not owned
 friction=.5 if receiver else cfg['friction']
 
 normal=choose(p,owned,bank,ft,transfer_friction=friction)
 # A real club transfer can temporarily create >3 holdings. Keeping them is legal.
 if owned and p[p.pid.isin(owned)].groupby('club').size().max()>3:
  keep=choose(p[p.pid.isin(owned)].copy(),owned,bank,ft,transfer_friction=friction)
  if expected(keep,p,None,friction)>expected(normal,p,None,friction)+1e-8:normal=keep
 candidates=[(0.,None,normal)]
 allow=receiver is not None or cfg['chip_reserve']<1000
 if allow:
  ordinary_score=expected(normal,p,None,friction)
  for chip in CHIPS:
   if chip not in state['chips']:continue
   if initial and chip in ['wildcard','free_hit']:continue
   if chip=='free_hit' and state['last']=='free_hit':continue
   reserve=(1 if receiver else cfg['chip_reserve'])*{'wildcard':12,'free_hit':12,'bench_boost':12,'triple_captain':8}[chip]*(.5+.5*(19-gw)/18)
   if chip in ['bench_boost','triple_captain']:
    choice=normal
   else:
    pp=p.copy()
    if chip=='free_hit':pp['bonus']=0.
    choice=choose(pp,owned,bank,ft,chip,transfer_friction=friction)
   gain=expected(choice,p,chip,0 if chip in ['wildcard','free_hit'] else friction)-ordinary_score
   # FH restores the pre-transfer holdings, not the ordinary candidate squad.
   if chip=='free_hit':gain+=p.set_index('pid').loc[list(owned),'bonus'].sum()
   force=(20-gw)<=len(state['chips'])
   candidates.append((gain-(0 if force else reserve),chip,choice))
  if (20-gw)<=len(state['chips']):candidates=[x for x in candidates if x[1] is not None] or candidates
 _,chip,choice=max(candidates,key=lambda x:x[0])
 pos=dict(zip(p.pid,p.pos));r=settle(choice['starters'],choice['bench'],choice['captain'],choice['vice'],pos,game['actual'],game['active'],chip)
 prev_owned=dict(owned);prev_bank=bank;prev_ft=ft
 if chip!='free_hit':
  state['owned']={i:owned[i] if i in owned else choice['prices'][i] for i in choice['squad']};state['bank']=choice['bank_after']
 state['ft']=next_free(ft,choice['transfers'],chip,initial);state['last']=chip
 if chip:state['chips'].remove(chip)
 if chip=='free_hit':assert state['owned']==prev_owned and state['bank']==prev_bank
 assert state['bank']>=0 and 1<=state['ft']<=5 and len(state['owned'])==15
 row={'gw':gw,'net':r['gross']-4*choice['paid'],'gross':r['gross'],'hits':4*choice['paid'],'transfers':choice['transfers'],'chip':chip or '',
      'bank':state['bank']/10,'ft':state['ft'],'free_before':prev_ft,'chips_left':len(state['chips']),'solver_status':choice['solver_status'],
      'squad':sorted(choice['squad']),'starters':choice['starters'],'bench':choice['bench'],'captain':choice['captain'],'vice':choice['vice'],
      'incoming':sorted(choice['incoming']),'outgoing':sorted(choice['outgoing']),'persistent_squad':sorted(state['owned'])}
 return row
