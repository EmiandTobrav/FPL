"""New dataset ingestion contract; frozen benchmark/model loaders are untouched."""
from pathlib import Path
import argparse,hashlib,json
import pandas as pd

P=Path(__file__).resolve().parent
class DatasetNotReady(ValueError):pass

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def load_dataset(root=P,require_training_ready=True):
    root=Path(root)
    config=json.loads((root/'ACTIVE.json').read_text())
    manifest=json.loads((root/config['manifest']).read_text())
    if config['dataset_version']!=manifest['version'] or config['points_standard']!=manifest['points_standard'] or manifest['points_standard']!='2026-27':
        raise ValueError('Dataset or scoring version mismatch')
    if require_training_ready and not manifest['training_ready']:
        raise DatasetNotReady('Training is blocked: deadline-safe features, complete qualified labels and eligible-universe evidence are unfinished. Original historical points are not a fallback.')
    frames={}
    for name in ['player_matches','player_rounds','next_round_targets','input_counters']:
        path=root/config[name]
        if sha(path)!=manifest['output_sha256'][path.name]:raise ValueError(f'Dataset file changed: {name}')
        frames[name]=pd.read_csv(path,low_memory=False)
    pm=frames['player_matches'];pr=frames['player_rounds']
    if not pm.points_standard.eq('2026-27').all() or not pr.points_standard.eq('2026-27').all() or not pm.dataset_version.eq(manifest['version']).all():
        raise ValueError('Row-level scoring/dataset standard mismatch')
    if pm.duplicated(['season','fixture','code']).any() or pr.duplicated(['season','round','code']).any():
        raise ValueError('Duplicate dataset identity')
    if pm.loc[~pm.scoring_qualified,'total_points_2026_27'].notna().any():
        raise ValueError('Unqualified historical target exposed')
    if require_training_ready:
        if not pr.training_ready.any():raise DatasetNotReady('No qualified training rows')
        frames['training_rows']=pr[pr.training_ready].copy()
    frames['manifest']=manifest
    return frames

def main():
    parser=argparse.ArgumentParser(description='Inspect or validate ingestion of the new 2026/27-standard dataset; never train models.')
    parser.add_argument('--inspect',action='store_true',help='Load the incomplete canonical tables for coverage inspection only')
    args=parser.parse_args()
    try:data=load_dataset(require_training_ready=not args.inspect)
    except DatasetNotReady as exc:
        parser.exit(2,str(exc)+'\n')
    print(json.dumps(dict(dataset_version=data['manifest']['version'],points_standard='2026-27',
        player_matches=len(data['player_matches']),player_rounds=len(data['player_rounds']),
        seasons=data['manifest']['counts']['seasons'],training_ready=data['manifest']['training_ready']),indent=2))

if __name__=='__main__':main()
