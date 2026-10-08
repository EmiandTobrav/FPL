"""Freeze a keeper-only mapping study before its native comparisons."""
from pathlib import Path
import hashlib
import json
import shutil
import pandas as pd

P=Path(__file__).resolve().parent
B=P.parent.parent
S=B.parent
K=['season','fixture']
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    if (P/'input_lock.json').exists():
        raise ValueError('Frozen keeper plan cannot be replaced')
    (P/'inputs').mkdir(exist_ok=True)
    shutil.copy2(B/'CURRENT.json',P/'inputs/parent_CURRENT.json')
    rows=[]
    for stage in ['fotmob_cbi_conservation','fotmob_keeper_location']:
        root=P.parent/stage
        manifest=pd.read_csv(root/'inputs/source_manifest.csv')
        plan=pd.read_csv(root/'plan.csv')
        merged=manifest.merge(plan,on=K,validate='one_to_one',suffixes=('','_plan'))
        for r in merged.to_dict('records'):
            path=root/r['path']
            if sha(path)!=r['file_sha256']:
                raise ValueError('Archived source fingerprint changed')
            rows.append(dict(season=r['season'],fixture=r['fixture'],date=r['date'],
                home=r['home'],away=r['away'],team_h_score=r['team_h_score'],
                team_a_score=r['team_a_score'],fotmob_match_id=r['fotmob_match_id'],
                path=str(path.relative_to(S)),file_sha256=r['file_sha256'],
                raw_sha256=r['raw_sha256'],url=r['url']))
    plan=pd.DataFrame(rows)
    for _,g in plan.groupby(K):
        if len(g)>1 and g.raw_sha256.nunique()!=1:
            raise ValueError('Conflicting archived source versions')
    plan=plan.drop_duplicates(K).sort_values(K).reset_index(drop=True)
    plan['scope']='historical_keeper_regression_and_missing_targets'
    plan.loc[plan.season.eq('2025-26'),'scope']='native_fpl_keeper_control'
    plan.to_csv(P/'plan.csv',index=False)
    protocol=dict(version='keeper_cbi_conservation_v1',scope='Goalkeepers only; never qualify outfield CBI',
        selection='All archived CBI-study and keeper-location responses, with explicit keeper role and native FPL participation. No outcome-selected controls.',
        exploratory_prior_evidence='Old generic failed study had ten agreeing 2025 keeper comparisons; those are reused regression evidence, not new holdout.',
        control_lineage='Shared Opta/FotMob lineage; all closed historical keeper anchors plus native FPL keeper anchors, not independent provider holdout.',
        minimum_closed_keeper_controls_per_historical_season=30,
        minimum_nonzero_closed_controls_per_historical_season=5,
        minimum_native_keeper_controls=100,minimum_native_control_fixtures=50,
        minimum_native_nonzero_controls=20,maximum_disagreements=0,
        rules=['Keep omitted counters missing unless exact full-team component exhaustion proves zero.',
               'Preserve all previous generic-study team/primary/closed-CBI vetoes for historical targets.',
               'Require explicit isGoalkeeper=true, historical position GK, minutes>0 and matching club side.',
               'Apply only missing_data CBI rows; preserve all conflicts and closed values.',
               'The generic failed V1 mapping and its acceptance gates remain unchanged.'],
        plan_sha256=sha(P/'plan.csv'))
    (P/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n')
    pointer=json.loads((P/'inputs/parent_CURRENT.json').read_text())
    generic=P.parent/'fotmob_cbi_conservation'
    files=[P/'inputs/parent_CURRENT.json',P/'plan.csv',P/'protocol.json',
        B/pointer['requirements'], S.parent/'training_dataset/scoring/results/historical_inventory.csv.xz',
        generic/'results/source_player_components.csv.xz',generic/'results/team_conservation.csv',
        generic/'results/manifest.json',generic/'freeze.json',generic/'build.py',
        P.parent/'fotmob_shot_conservation/build.py']
    files += [S/r.path for r in plan.itertuples()]
    (P/'input_lock.json').write_text(json.dumps(dict(path_root='research/current/scoring_2026_27',
        input_sha256={str(p.relative_to(S)) if p.is_relative_to(S) else str(p.relative_to(S.parent)):sha(p) for p in files},
        outside_root_inputs=['training_dataset/scoring/results/historical_inventory.csv.xz']),indent=2)+'\n')
    print(dict(frozen_sources=len(plan),native_control_fixtures=int(plan.season.eq('2025-26').sum())))

if __name__=='__main__':
    main()
