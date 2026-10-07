from pathlib import Path
import argparse,json
import pandas as pd
from rules import residual
P=Path(__file__).resolve().parent
MAP={'wonTackle':'won_tackle','totalTackle':'total_tackle','wasFouled':'fk_foul_won','ontargetScoringAtt':'ontarget_scoring_att','clearanceOffLine':'clearance_off_line'}
def audit(teams,players):
 groups={k:g for k,g in players.groupby(['match_id','team_position'])};rows=[]
 for team in teams.to_dict('records'):
  g=groups.get((team['match_id'],team['side']))
  if g is None:continue
  for field,totalfield in MAP.items():
   total=team[totalfield];zero,reason=residual(total,g[field].tolist())
   rows.append(dict(season=team['season'],fixture=team['fixture'],match_id=team['match_id'],team_id=g.team_id.iloc[0],side=team['side'],field=field,team_field=totalfield,total=total,known_sum=g[field].sum(),known_players=int(g[field].notna().sum()),missing_players=int(g[field].isna().sum()),reason=reason,zero_certified=zero is not None))
 return pd.DataFrame(rows)
def main():
 ap=argparse.ArgumentParser();ap.add_argument('stage');args=ap.parse_args()
 d=audit(pd.read_csv(P/f'{args.stage}_team_totals.csv'),pd.read_csv(P/'inputs/source_players.csv.gz'))
 d.to_csv(P/f'{args.stage}_conservation.csv',index=False)
 print(d.groupby(['field','reason']).agg(teams=('field','size'),missing_players=('missing_players','sum')).to_string())
if __name__=='__main__':main()
