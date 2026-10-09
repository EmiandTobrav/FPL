"""Close the existing insufficient-control trial without changing any data."""
import json
from pathlib import Path
from prepare import P,digest

def main():
    report=json.loads((P/'results/validation.json').read_text())
    gate=json.loads((P/'protocol.json').read_text())['gate']
    assert not report['qualified_kinds']
    unmet=[]
    if report['control_goals']<gate['minimum_control_goals']:unmet.append('minimum_control_goals')
    for kind,count in sorted(report['control_kinds'].items()):
        if count<gate['minimum_control_goals_per_kind']:unmet.append('minimum_control_goals_per_kind:'+kind)
    assert unmet
    findings=dict(investigation_status='completed_unqualified_insufficient_controls',data_completion_status='not_complete',fields_closed=0,ledger_modified=False,scoring_modified=False,qualified_kinds=[],control_goals=report['control_goals'],required_control_goals=gate['minimum_control_goals'],control_player_matches=report['control_player_matches'],control_kinds=report['control_kinds'],required_control_goals_per_kind=gate['minimum_control_goals_per_kind'],goal_vector_errors=report['goal_vector_errors'],player_errors=report['player_errors'],unmet_gates=unmet,same_input_retry_allowed=False,reopening_condition='New complete, rule-compatible source goal/foul inventories that add eligible frozen one-goal whole-team controls. Keep original zero-error/minimum gates. No goal decisions or labels are applied by this trial.')
    (P/'results/findings.json').write_text(json.dumps(findings,indent=2)+'\n')
    print(json.dumps(findings,indent=2))
if __name__=='__main__':main()
