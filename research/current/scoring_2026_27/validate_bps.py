"""Diagnostic reconstruction. Sparse omitted PL counters treated as zero only
inside this labelled diagnostic, not promoted as observed historical values.
"""
from pathlib import Path
import json,math,sys
import pandas as pd
P=Path(__file__).resolve().parent;O=P/'results'
def calculate(r,assist_source='fpl',fractional=False):
 def n(k):
  x=r.get('pl_'+k,0);return 0 if pd.isna(x) else float(x)
 def f(k):return float(r.get(k,0))
 pos=r['position'];gk=pos=='GK';defensive=pos in ['GK','DEF'];minutes=f('minutes')
 if minutes<=0:return 0
 floor=(lambda x:x) if fractional else math.floor
 goals=n('goals');pens=n('att_pen_goal');assists=n('goal_assist') if assist_source=='opta' else f('assists')
 base=6 if minutes>60 else 3
 base+=(goals-pens)*({'GK':12,'DEF':12,'MID':18,'FWD':24}[pos])+12*pens+9*assists
 if defensive:base+=12*f('clean_sheets')-4*f('goals_conceded')
 if gk:base+=2*n('saves')+n('saved_ibox')+n('big_chance_saves')+7*n('penalty_save')
 base+=floor((n('total_clearance')+n('outfielder_block')+n('interception'))/3)+floor(n('ball_recovery')/3)
 base+=n('accurate_cross_nocorner')+3*n('big_chance_created')+n('total_att_assist')+2*n('won_tackle')+n('won_contest')+3*n('winning_goal')+9*n('clearance_off_line')+n('was_fouled')+2*n('ontarget_scoring_att')
 if n('total_pass')>=30:
  ratio=n('accurate_pass')/n('total_pass');base+=6 if ratio>=.9 else 4 if ratio>=.8 else 2 if ratio>=.7 else 0
 base-=3*n('penalty_conceded')+6*f('penalties_missed')+3*f('yellow_cards')+9*f('red_cards')+6*f('own_goals')+3*n('big_chance_missed')+3*n('error_lead_to_goal')+n('error_lead_to_shot')+n('fouls')+n('total_offside')+n('shot_off_target')
 return base

def bonus(scores):
 return scores.apply(lambda x:max(0,3-int((scores>x).sum())))
def run():
 suffix=f'_gw{sys.argv[1]}' if len(sys.argv)>1 else '';f=pd.read_csv(O/f'primary_player_counts{suffix}.csv');f=f[f.season=='2026-27'].copy();f['bps_reconstructed']=f.apply(calculate,axis=1);f['bps_with_fpl_assists']=f.apply(lambda r:calculate(r,'fpl'),axis=1);f['bps_fractional']=f.apply(lambda r:calculate(r,fractional=True),axis=1)
 f['bps_error']=f.bps_reconstructed-f.bps;f['bonus_reconstructed']=f.groupby('fixture').bps_reconstructed.transform(bonus)
 f['minutes_difference']=f.pl_mins_played-f.minutes
 f.to_csv(O/f'bps_2026_diagnostic{suffix}.csv',index=False)
 result=dict(rows=len(f),matches=int(f.fixture.nunique()),equal_bps=int(f.bps_error.eq(0).sum()),equal_bonus=int(f.bonus_reconstructed.eq(f.bonus).sum()),mean_absolute_bps_error=float(f.bps_error.abs().mean()),fpl_assist_equal_bps=int(f.bps_with_fpl_assists.eq(f.bps).sum()),fractional_equal_bps=int(f.bps_fractional.eq(f.bps).sum()),scope='Source qualification only; sparse-zero and component mappings not yet validated; not harmonized labels')
 (O/f'bps_2026_diagnostic_summary{suffix}.json').write_text(json.dumps(result,indent=2)+'\n');print(result)
if __name__=='__main__':run()
