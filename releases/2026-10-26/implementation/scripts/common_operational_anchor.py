"""Score the immutable operational forecasts on the new common outcome rows.

This is an external frozen reference, not a claim of matched fresh training.
Every newly trained model is restricted to the exact same anchor rows.
"""
import sys,json
from pathlib import Path
import pandas as pd
import numpy as np
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R))
from model_lab.common import sha,atomic_json,verify_files
from scripts import common_model_retest as run
P=run.P;D=run.D
SOURCE=R/'reports/season_role_gate_2026_10_24/predictions.csv.gz'

def main():
    spec=run.read(P/'proposal.json');verify_files(R,spec['input_hashes'])
    old=pd.read_csv(SOURCE);old.forecast_at=pd.to_datetime(old.forecast_at,utc=True,format='mixed')
    d=pd.read_pickle(D/'training.pkl');q=d.merge(old[run.KEY+['forecast_at','can_buy']+[f'fixed_{i}' for i in range(3)]+[f'y_{i}' for i in range(3)]],on=run.KEY,validate='one_to_one',suffixes=('','_anchor'))
    q=q[q.eval_eligible&q.can_buy].copy();assert q.forecast_at.eq(q.forecast_at_anchor).all()
    rows=[];predictions=run.collect();keys=[]
    for h in [1,3]:
        v=q[q[f'target_points_{h}'].notna()&q[[f'fixed_{i}' for i in range(h)]].notna().all(axis=1)].copy();v['anchor_prediction']=v[[f'fixed_{i}' for i in range(h)]].sum(1)
        # Independent target check against the original stored labels, where known.
        known=v[[f'y_{i}' for i in range(h)]].notna().all(axis=1)
        np.testing.assert_allclose(v.loc[known,f'target_points_{h}'],v.loc[known,[f'y_{i}' for i in range(h)]].sum(1))
        for s,g in v.groupby('season'):
            ordered=g.sort_values('row_id');ids=ordered.row_id.tolist();target=ordered[f'target_points_{h}'].to_numpy();reference=ordered.anchor_prediction.to_numpy();keyhash=sha_string('\n'.join(ids))
            keys.append(dict(season=s,horizon=h,n=len(ids),keys_sha256=keyhash))
            rows.append(dict(season=s,horizon=h,arm='frozen_operational',n=len(ids),point_mse=float(np.mean((reference-target)**2)),keys_sha256=keyhash))
            for arm in run.ARMS:
                pred=predictions[predictions.horizon.eq(h)&predictions.arm.eq(arm)].set_index('row_id').loc[ids,'predicted_points'].to_numpy()
                rows.append(dict(season=s,horizon=h,arm=arm,n=len(ids),point_mse=float(np.mean((pred-target)**2)),keys_sha256=keyhash))
    result=pd.DataFrame(rows);result.to_csv(P/'operational_anchor_metrics.csv',index=False)
    atomic_json(P/'operational_anchor_verification.json',dict(passed=True,common_keys=keys,immutable_anchor_sha256=sha(SOURCE),all_arms_same_known_evaluation_keys=True,aligned_origins=True,source_labels_checked_against_master=True,training_matched=False,reason='Frozen operational forecasts retain their original training inputs and recipe; all new family fits use the common table. This is a system-reference comparison, not an isolated feature effect or operational refit.',production_changed=False))
    print(result.to_string(index=False))

def sha_string(s):
    import hashlib
    return hashlib.sha256(s.encode()).hexdigest()

if __name__=='__main__':main()
