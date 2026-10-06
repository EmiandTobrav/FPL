from pathlib import Path
import sys,json,pickle,gzip,copy,time
from concurrent.futures import ProcessPoolExecutor,as_completed
import numpy as np,pandas as pd
ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'project'));sys.path.insert(0,str(ROOT/'project/tuning_v3'))
from engine import act,CHIPS
from decision import choose,settle,selling_price,next_free
SEASONS=[f'{y}-{str(y+1)[-2:]}' for y in range(2020,2026)]
MODELS=['ridge','bayes','extra','hgb','hgb_extended','mix_ridge_extra_50','mix_ridge_hgb_25','mix_ridge_hgb_50','mix_ridge_hgb_75','mix_three']
CFG=json.loads((ROOT/'project/tuning_v3/protocol.json').read_text())['seed'];CFG['scenario']='neutral'
CAL={6:'wildcard',15:'triple_captain',18:'free_hit',19:'bench_boost',24:'wildcard',33:'free_hit',36:'bench_boost',37:'triple_captain'}

def xp_for(game,m):
 d=game['pred']
 if m in d:return d[m]
 if m=='mix_ridge_extra_50':return .5*d['ridge']+.5*d['extra']
 if m=='mix_three':return (d['ridge']+d['extra']+d['hgb_extended'])/3
 w=int(m.rsplit('_',1)[1])/100
 return (1-w)*d['ridge']+w*d['hgb_extended']

def opening(s):
 with open(ROOT/f'project/tuning_v3/inputs_{s}.pkl','rb') as f:games=pickle.load(f)
 state={'owned':{},'bank':1000,'ft':1,'chips':set(CHIPS),'last':None};hist=[]
 for gw in range(1,5):hist.append(act(games[gw],CFG,gw,state,'adaptive'))
 return state,hist

def make_choice(game,m,state,chip):
 p=game['frame'].copy();p['xp']=xp_for(game,m);p['bonus']=0.
 c=choose(p,state['owned'],state['bank'],state['ft'],chip)
 # Respect the same inherited real-club-transfer exception as the previous engine.
 if chip is None and p[p.pid.isin(state['owned'])].groupby('club').size().max()>3:
  keep=choose(p[p.pid.isin(state['owned'])],state['owned'],state['bank'],state['ft'])
  def val(z):
   x=p.set_index('pid').xp
   return x.loc[z['starters']].sum()+x.loc[z['captain']]+.1*x.loc[z['bench']].sum()-4*z['paid']-.5*z['transfers']
  if val(keep)>val(c)+1e-8:c=keep
 return p,c

def run(task, *, games=None, trace_dir=None):
 s,m,mode=task;fn=(Path(trace_dir) if trace_dir is not None else ROOT/'results')/f'trace_{s}_{m}_{mode}.json.gz'
 if fn.exists():return json.loads(gzip.decompress(fn.read_bytes()))['summary']
 if games is None:
  with open(ROOT/f'results/games_{s}.pkl','rb') as f:games=pickle.load(f)
 state,hist=opening(s);start=copy.deepcopy(state);opening_points=sum(x['net'] for x in hist)
 rows=[]
 for gw in range(5,39):
  game=games[gw];chip=CAL.get(gw) if mode=='fixed_chips' else None
  p,c=make_choice(game,m,state,chip);pos=dict(zip(p.pid,p.pos));xp=dict(zip(p.pid,p.xp))
  r=settle(c['starters'],c['bench'],c['captain'],c['vice'],pos,game['actual'],game['active'],chip)
  before=copy.deepcopy(state);cost=4*c['paid']
  assert set(state['owned']).issubset(set(p.pid))
  expected_bank=state['bank']+sum(selling_price(state['owned'][i],c['prices'][i]) for i in c['outgoing'])-sum(c['prices'][i] for i in c['incoming'])
  assert expected_bank==c['bank_after'] and expected_bank>=0
  if chip!='free_hit':
   state['owned']={i:state['owned'].get(i,c['prices'][i]) for i in c['squad']};state['bank']=c['bank_after']
  else:assert state==before
  state['ft']=next_free(state['ft'],c['transfers'],chip)
  # Reconcile every counted player and captain multiplier.
  assert r['gross']==sum(game['actual'].get(i,0) for i in r['counted'])+r['captain_bonus']
  rows.append(dict(gw=gw,net=r['gross']-cost,gross=r['gross'],hits=cost,transfers=c['transfers'],chip=chip or '',bank=state['bank'],ft=state['ft'],solver_status=c['solver_status'],solver_gap=c['solver_gap'],squad=sorted(c['squad']),starters=c['starters'],bench=c['bench'],captain=c['captain'],vice=c['vice'],incoming=sorted(c['incoming']),outgoing=sorted(c['outgoing']),forecast={str(i):float(xp[i]) for i in sorted(c['squad'])},captain_bonus=r['captain_bonus'],autosub_gain=r['autosub_gain'],counted=r['counted'],contributions={str(i):float(game['actual'].get(i,0)) for i in set(r['counted'])},owned_after=sorted(state['owned']),purchase_prices=state['owned']))
 summary=dict(season=s,model=m,mode=mode,points38=opening_points+sum(x['net'] for x in rows),points5_38=sum(x['net'] for x in rows),opening_points=opening_points,hits=sum(x['hits'] for x in rows),transfers=sum(x['transfers'] for x in rows),nonoptimal=sum(x['solver_status']!=0 for x in rows),max_solver_gap=max(x['solver_gap'] for x in rows),bank=state['bank']/10,ft=state['ft'])
 for endpoint in [8,12,15,19]:summary[f'points{endpoint}']=opening_points+sum(x['net'] for x in rows if x['gw']<=endpoint)
 obj=dict(summary=summary,opening=hist,handoff=dict(owned=start['owned'],bank=start['bank'],ft=start['ft']),trace=rows)
 fn.write_bytes(gzip.compress(json.dumps(obj,default=lambda x:x.item() if isinstance(x,np.generic) else list(x)).encode(),mtime=0));return summary

def main():
 protocol=dict(created='2026-10-05',models=MODELS,seasons=SEASONS,opening=CFG,regimes=['no_chips','fixed_chips'],chip_calendar=CAL,objective='GW38 net points; same original opening policy GW1-4',selection='For 2022-23 onward, select model from earlier seasons only: mean difference versus ridge minus .25 SD; prefer ridge if within 2 points of best, otherwise best. Select independently per chip regime.',forecast_fitting='Only previous seasons; frozen within a season, input features update before each decision.',test_status='Retrospective; all seasons previously examined.',limitations=['Lagged market-price proxy, not deadline prices','No complete timestamped injury/availability archive','Current-round final event assignment assumed known 36h before first kickoff; no future fixture calendar is used','Five-bank-transfer and two-chip-set rules replayed across historical points; not historical rank and not full current scoring rescore','Fixed chip calendar controls resources, does not optimize chip timing','Extended features bundle multiple changes; cannot isolate an xG effect','Same initial start-model state, not an independently rebuilt GW1 squad'])
 (ROOT/'protocol.json').write_text(json.dumps(protocol,indent=2))
 tasks=[(s,m,mode) for s in SEASONS for m in MODELS for mode in ['no_chips','fixed_chips']];rows=[];t=time.time()
 with ProcessPoolExecutor(max_workers=4) as ex:
  futures=[ex.submit(run,t) for t in tasks]
  for i,f in enumerate(as_completed(futures),1):
   rows.append(f.result())
   if i%5==0 or i==len(tasks):print('DONE',i,len(tasks),'seconds',round(time.time()-t),flush=True);pd.DataFrame(rows).to_csv(ROOT/'results/season_results.csv',index=False)
if __name__=='__main__':main()
