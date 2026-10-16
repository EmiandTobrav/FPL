"""Portable best-effort training reader. Uses an explicit feature allowlist."""
from pathlib import Path
import hashlib,json
import numpy as np
import pandas as pd

def load_training_data(root=None,split='train',target='target_total_points',exclude_flagged=False):
    root=Path(root) if root is not None else Path(__file__).resolve().parent
    manifest=json.loads((root/'manifest.json').read_text())
    schema=json.loads((root/'schema.json').read_text())
    if not manifest['training_ready_best_effort']:raise ValueError('Not a best-effort training release')
    for name in ['schema.json','training_rows.csv.xz']:
        digest=hashlib.sha256((root/name).read_bytes()).hexdigest()
        if digest!=manifest['output_sha256'][name]:raise ValueError('Changed release file: '+name)
    if split not in ['train','validation','test','current_native']:raise ValueError('Unknown chronological split')
    if target not in ['target_total_points','target_points_h3','target_points_h6']:raise ValueError('Unsupported prediction target')
    data=pd.read_csv(root/'training_rows.csv.xz',low_memory=False)
    rows=data[data.split.eq(split)&data[target].notna()].copy()
    if exclude_flagged:rows=rows[~rows.quality_flagged_for_sensitivity].copy()
    features=schema['model_feature_columns']
    if any(not name.startswith('f_') for name in features):raise ValueError('Unsafe feature allowlist')
    X=rows[features].to_numpy(dtype=float);y=rows[target].to_numpy(dtype=float)
    if not np.isfinite(X).all() or not np.isfinite(y).all():raise ValueError('Missing model inputs')
    return dict(X=X,y=y,feature_names=features,rows=rows,manifest=manifest)

if __name__=='__main__':
    report={}
    for split in ['train','validation','test','current_native']:
        d=load_training_data(split=split)
        report[split]=dict(rows=len(d['y']),features=d['X'].shape[1],quality_flagged=int(d['rows'].quality_flagged_for_sensitivity.sum()))
    print(json.dumps(report,indent=2))
