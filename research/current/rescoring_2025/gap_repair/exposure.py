"""Frozen-decision exposure to unresolved labels; not a new strategy backtest."""
from pathlib import Path
import json
import pandas as pd
P=Path(__file__).resolve().parent;R=P.parents[1]
def run():
 rows=[];details=[]
 for season in ['2022-23','2023-24']:
  trace=json.loads((P/f'raw/trace_{season}.json').read_text())
  players=pd.read_csv(R/f'project/data/{season}_players.csv')
  d=pd.read_csv(P/f'results/{season}_labels.csv')
  d['code']=d.element.map(players.set_index('id').code)
  table=d.groupby(['round','code'])[['minutes','total_points','defcon_lower','defcon_upper']].sum()
  low=high=0;old=0
  for t in trace['trace']:
   gw=t['gw'];assert gw>=5
   def stats(code):
    return table.loc[(gw,code)] if (gw,code) in table.index else pd.Series(dict(minutes=0,total_points=0,defcon_lower=0,defcon_upper=0))
   captain=t['captain'] if stats(t['captain']).minutes>0 else t['vice'] if stats(t['vice']).minutes>0 else None
   extra=2 if t['chip']=='triple_captain' else 1
   expected_bonus=stats(captain).total_points*extra if captain is not None else 0
   assert expected_bonus==t['captain_bonus'],(season,gw,'captain')
   assert sum(t['contributions'].values())+expected_bonus==t['gross']
   for code in t['counted']:
    s=stats(code)
    assert s.total_points==t['contributions'][str(code)],(season,gw,code)
    weight=1+(extra if code==captain else 0)
    low+=weight*s.defcon_lower;high+=weight*s.defcon_upper
    if s.defcon_upper>s.defcon_lower:details.append({'season':season,'gw':gw,'code':code,'weight':weight,'unknown_span':weight*(s.defcon_upper-s.defcon_lower)})
   old+=t['net']
  rows.append({'season':season,'scope':'GW5-38 frozen counted players incl captain and chips','historical_net':old,'defcon_lower':low,'defcon_upper':high,'uncertainty_span':high-low,'fixed_decision_total_lower':old+low,'fixed_decision_total_upper':old+high})
 pd.DataFrame(rows).to_csv(P/'results/benchmark_exposure.csv',index=False)
 pd.DataFrame(details,columns=['season','gw','code','weight','unknown_span']).to_csv(P/'results/benchmark_unknown_rows.csv',index=False)
 print(pd.DataFrame(rows).to_string(index=False))
if __name__=='__main__':run()
