"""Qualify whole-season positive total compatibility without removing errors."""
import json,pandas as pd
from predict import P,R,digest,write,save

def main():
 for n,h in json.loads((P/'prediction_freeze.json').read_text()).items():assert digest(P/n)==h,n
 for n,h in json.loads((P/'dependencies.json').read_text()).items():assert digest(R/n)==h,n
 groups=pd.read_csv(P/'season_groups.csv');complete=groups[groups.all_values_complete].copy();complete['agrees']=complete.known_sum.eq(complete.source_total);partial=groups[groups.inventory_complete & ~groups.all_values_complete].copy();partial['negative_residual']=partial.known_sum.gt(partial.source_total)
 save(complete,'complete_controls.csv');save(partial,'partial_groups.csv');plan=json.loads((P/'plan.json').read_text());g=plan['gates'];season_counts=complete.groupby('season').size().to_dict();seasons=[str(y)+'-'+str(y+1)[2:] for y in range(2019,2025)]
 errors=int((~complete.agrees).sum());negative=int(partial.negative_residual.sum());matches=int(complete.inventory_matches.sum());qualified=len(complete)>=g['minimum_complete_positive_player_seasons'] and matches>=g['minimum_complete_player_matches'] and all(season_counts.get(s,0)>=g['minimum_complete_positive_player_seasons_per_season'] for s in seasons) and errors<=g['maximum_complete_sum_errors'] and negative<=g['maximum_partial_negative_residuals']
 candidates=pd.read_csv(P/'predictions.csv.gz')
 write(P/'validation.json',dict(qualified=bool(qualified),complete_positive_player_seasons=len(complete),complete_player_matches=matches,complete_groups_by_season=season_counts,complete_sum_errors=errors,partial_negative_residuals=negative,candidate_fields=len(candidates),qualified_candidate_fields=len(candidates) if qualified else 0,scope_excluded_independent_incomplete_appearance_groups=int((~groups.inventory_complete).sum()),fields_closed=0,ledger_modified=False,limits='Every independently complete positive player-season is compared, including all mismatches. Known values are proof inputs; this is same-source compatibility regression, not holdout. No positive residual is allocated and no incomplete appearance scope is complete. No fields applied by this trial.'))
 print((P/'validation.json').read_text())
if __name__=='__main__':main()
