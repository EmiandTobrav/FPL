"""Retain the rejected aggregate route and verify the complete collection chain."""
import json
from predict import P,digest,write

def main():
 for folder,freeze in [('control_extension_selection','control_extension_freeze.json'),('league_selection','league_selection_freeze.json'),('initial_prediction','prediction_freeze.json')]:
  root=P/'inputs'/folder
  for n,h in json.loads((root/freeze).read_text()).items():assert digest(root/n)==h,n
 for n,h in json.loads((P/'league_selection_freeze.json').read_text()).items():assert digest(P/n)==h,n
 players=json.loads((P/'inputs/2019-20.json').read_text());teams=json.loads((P/'inputs/2019-20_teams.json').read_text())
 source=json.loads((P/'team_sources.json').read_text())[0];assert digest(P/source['file'])==source['sha256']
 assert players['entity']==teams['entity']=='clearance_off_line'
 p=sum(v['value'] for v in players['stats']['content']);t=sum(v['value'] for v in teams['stats']['content']);n=len(teams['stats']['content'])
 assert n!=20 and p!=t
 write(P/'league_findings.json',dict(status='completed_rejected',explicit_team_records=n,required_active_teams=20,player_sum=p,team_sum=t,team_minus_player_residual=t-p,fields_closed=0,omitted_player_zero_inference_allowed=False,remaining_season_team_requests=0,same_source_retry_allowed=False))
 print('Collection snapshots verified; failed19-team/10-count aggregate route preserved')
if __name__=='__main__':main()
