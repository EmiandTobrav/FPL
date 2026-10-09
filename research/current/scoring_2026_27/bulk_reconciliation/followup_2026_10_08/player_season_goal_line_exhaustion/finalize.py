"""Complete the qualified but zero-candidate season-total track."""
import json,pandas as pd
from predict import P,B,digest,write,save

def main():
 report=json.loads((P/'validation.json').read_text());assert report['qualified'] and report['candidate_fields']==report['fields_closed']==0
 parent=json.loads((P/'inputs/parent_CURRENT.json').read_text());before=pd.read_csv(B/parent['requirements'],low_memory=False);pending=before[before.is_open&before.field.eq('goal_line_clearances')].copy();old=P.parent/'player_season_goal_line_zeros';sources=json.loads((old/'sources.json').read_text());lookup={}
 for s in sources:
  path=old/s['file'];assert digest(path)==s['sha256']
  for item in json.loads(path.read_text())['stats']['content']:lookup[(s['season'],int(item['owner']['altIds']['opta'][1:]))]=item['value']
 pending['explicit_player_season_gl_total']=[lookup.get((r.season,r.code),float('nan')) for r in pending.itertuples()]
 assert len(pending)==16 and pending.explicit_player_season_gl_total.isna().all()
 pending['source_track_status']='missing_explicit_player_season_counter_not_zero';save(pending[['season','fixture','code','name','position','explicit_player_season_gl_total','source_track_status']],'remaining_target_sources.csv')
 write(P/'findings.json',dict(investigation_status='completed_qualified_zero_candidates',fields_closed=0,ledger_modified=False,scoring_modified=False,remaining_goal_line_requirements=16,complete_player_seasons=371,complete_player_matches=10109,sum_errors=0,all_remaining_targets_lack_explicit_source_counter=True,same_input_retry_allowed=False,reopening_condition='A new explicit compatible player or match GL counter, or a qualified complete event inventory for one of the16 remaining targets. Existing season-counter omission and positive residuals remain missing.'))
 print('Track completed:371 compatible positive totals; all16 open targets unlisted,0 values changed')
if __name__=='__main__':main()
