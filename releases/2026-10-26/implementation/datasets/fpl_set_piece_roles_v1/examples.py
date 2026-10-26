"""Reviewable reported-role scenarios; selection never reads match outcomes."""
import collections
from common import *
def main():
 source={(r['season'],r['round'],r['code']):r for r in read(P/'source_roles.csv.gz')};teams=collections.defaultdict(list)
 for r in source.values():teams[(r['season'],r['round'],r['team'])].append(r)
 output=[]
 for r in read(P/'player_round_context.csv.xz'):
  key=r['season'],r['round'],r['code'];own=source.get(key)
  for role in ROLES:
   prefix='sp_'+role+'_'
   if r[prefix+'potential_promotion']!='True':continue
   assert own is not None;rank=int(r[prefix+'listed_order']);ahead=[p for p in teams[(r['season'],r['round'],own['team'])] if truth(p[role+'_known']) and p[role+'_order'] and int(p[role+'_order'])<rank]
   output.append(dict(season=r['season'],round=r['round'],code=r['code'],player=own['name'],team=own['team'],role=role,reported_order=rank,own_reported_status=r['sp_own_reported_status'],listed_players_ahead='; '.join(p['name']+' (FPL '+p['status']+')' for p in ahead),tied_top_remaining=r[prefix+'top_remaining_tied'],unique_top_remaining_candidate=r[prefix+'unique_top_remaining_candidate'],forecast_at=r['sp_forecast_at'],source_url=r['sp_source_url'],interpretation='possible_larger_role_if_selected_not_confirmed_taker'))
 write('potential_promotion_scenarios.csv.gz',output);write('scenario_examples.csv',output[:12]);print('Reported-role scenarios',len(output),flush=True)
if __name__=='__main__':main()
