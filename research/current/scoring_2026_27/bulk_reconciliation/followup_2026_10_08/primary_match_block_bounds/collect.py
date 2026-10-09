"""Freeze existing source dependencies; no new network calls."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent
B=P.parents[1]
R=B.parents[1]
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text(json.dumps(v,indent=2)+'\n')
def prepare():
 parent=json.loads((B/'CURRENT.json').read_text());write(P/'inputs/parent_CURRENT.json',parent)
 sources=['primary_gap_recovery/'+n for n in ['qualified_components.csv.gz','players.json','roster.csv','conservation.csv','freeze.json','validation_summary.json','explicit_component_controls.csv']]
 sources+=['player_season_block_bounds/'+n for n in ['predictions.csv.gz','results/validation.json']]
 write(P/'plan.json',dict(target='Only missing goal_line_clearances for native FPL DEF/MID/FWD with qualified primary match outfielder_block=0',proof='Nonnegative whole-match goal-line clearances are a subset of whole-match outfield shot blocks. Primary zero is explicit or certified by original exact complete-roster team conservation. GK and nonzero/missing block rows excluded.',sources={n:digest(P.parent/n) for n in sources},gates=dict(min_controls=1000,min_primary_controls=100,min_primary_control_fixtures=20,max_errors=0,max_positive_contradictions=0),controls='All already closed GL values among primary predictions, plus deduplicated previously qualified zero-season block regressions. Reused source qualification requires original zero-error explicit component checks. Shared-source regression, not independent holdout.',omitted_values_are_not_zero=True,scoring_allowed=False,features_allowed=False))
 write(P/'selection_freeze.json',{n:digest(P/n) for n in ['plan.json','inputs/parent_CURRENT.json']})
if __name__=='__main__':prepare()
