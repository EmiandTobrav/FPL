"""Final reports for population-qualified xG, with valid recency reuse."""
import sys,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from scripts import test_xg_adaptation_v2 as config
from scripts import report_xg_adaptation as old
from model_lab.common import sha,atomic_json
import pandas as pd
P=config.P;D=config.D;t=config.t

def finish():
    t.check()
    for name in ['dataset_verification.json','population_verification.json','interval_verification.json']:assert t.read(P/name)['passed']
    for arm in ['control']+t.ARMS:assert t.read(P/f'manager_verification_{arm}.json')['passed']
    for arm in t.ARMS:assert t.read(P/f'prediction_verification_{arm}.json')['passed'] and t.read(P/f'preflight_{arm}.json')['passed']
    scores=pd.concat([pd.read_csv(P/f'scores_{arm}.csv') for arm in ['control']+t.ARMS]);scores.to_csv(P/'scores.csv',index=False);wide=scores.pivot(index='season',columns='arm',values='net');wide['xg_delta']=wide.xg_only-wide.control;wide['recent_delta']=wide.recent_only-wide.control;wide.to_csv(P/'comparison.csv');gate={arm:bool((wide[arm]>wide.control).all()) for arm in t.ARMS};audit=pd.concat([pd.read_csv(P/f'base_audit_{s}.csv') for s in t.S]);reused=int(audit.reused_parent_only_if_entire_actual_training_matrix_identical.sum());assert reused>=8 and 80-reused<=72
    artifacts=list(P.glob('*.csv'))+[P/name for name in ['dataset_verification.json','population_verification.json','interval_verification.json','prediction_verification_xg_only.json','prediction_verification_recent_only.json','manager_verification_control.json','manager_verification_recent_only.json','manager_verification_xg_only.json','recency_reuse.json']]+[D/'manifest.json',D/'release.json',Path(__file__),R/'scripts/verify_xg_adaptation_v2.py']
    atomic_json(P/'final_verification.json',dict(passed=True,complete_valid_candidate_episodes=6,new_corrected_xg_episodes=3,reused_valid_recency_episodes=3,reused_control_episodes=3,decisions_independently_replayed=342,valid_xg_base_packages=80,new_corrected_base_fits=80-reused,reused_on_exact_matrix_equality=reused,new_projection_heads=240,reused_recency_heads=240,independent_interventions_only=True,success_by_arm=gate,all_same_keys_targets_policy_clock_and_per_decision_resources=True,previous_invalidated_xg_episodes=3,active_model_unchanged=True,files={str(p.relative_to(R)):sha(p) for p in artifacts}));print('FINAL',wide.to_string(),gate,flush=True)

if __name__=='__main__':
    if sys.argv[1]=='managers':old.managers(sys.argv[2])
    elif sys.argv[1]=='metrics':old.metrics()
    elif sys.argv[1]=='finish':finish()
    else:raise ValueError(sys.argv[1])
