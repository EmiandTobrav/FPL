from pathlib import Path
import sys,json,hashlib,pickle,gzip
import numpy as np,pandas as pd
HERE=Path(__file__).resolve().parent;CURRENT=HERE.parent;sys.path.insert(0,str(CURRENT))
from decision_specialist.models import gate_design,predict_gate
from decision_specialist.run_gate import fingerprint as gate_fingerprint
from decision_specialist.run_horizon import fingerprint as horizon_fingerprint
OUT=HERE/'results'

def main():
    assert json.loads((OUT/'gate_manifest.json').read_text())==gate_fingerprint()
    assert json.loads((OUT/'horizon_manifest.json').read_text())==horizon_fingerprint()
    beta=json.loads((OUT/'gate_coefficients.json').read_text());aud=pd.read_csv(OUT/'gate_training_audit.csv');checks=[]
    for row in aud.itertuples():
        assert all(s<row.season for s in row.training_seasons.split(','))
        assert pd.Timestamp(row.max_label_available)<pd.Timestamp(row.cutoff)
        p=pd.read_csv(OUT/f'gate_{row.season}.csv.gz');x=gate_design(p.minutes_m6,p.minutes_m12)
        for m in ['gate','constant']:
            y,w=predict_gate(x,p.a.to_numpy(),p.b.to_numpy(),np.array(beta[row.season][m]['beta']))
            np.testing.assert_allclose(p[m],y,atol=1e-12);np.testing.assert_allclose(p[m+'_weight'],w,atol=1e-12)
            assert ((w>0)&(w<1)).all()
        checks.append(dict(season=row.season,rows=len(p),gate_min=p.gate_weight.min(),gate_max=p.gate_weight.max(),constant_weight=p.constant_weight.iloc[0]))
    pd.DataFrame(checks).to_csv(OUT/'gate_coefficient_verification.csv',index=False)
    # Copy differs from the old planner only in its prespecified solver settings.
    old=(CURRENT/'horizon_upside/planner.py').read_text().replace("'time_limit':5,'mip_rel_gap':.001","'time_limit':10,'mip_rel_gap':1e-5")
    assert old==(HERE/'planner.py').read_text()
    checks=json.loads((OUT/'checks.json').read_text())
    assert checks['horizon_new_simulations']==72 and checks['gate_new_simulations']==16
    source_paths=list(HERE.glob('*.py'))+[HERE/'protocol.json']
    source_paths+=list((CURRENT/'behavior_diagnostics/results').glob('scenario_inputs_*.csv.gz'))+list((CURRENT/'horizon_upside/results').glob('forecasts_*.csv.gz'))+list((CURRENT/'retrained_ensemble/results').glob('predictions_*.csv.gz'))+list((CURRENT/'adaptive_events/results').glob('predictions_*.csv.gz'))
    source_paths+=list((CURRENT/'project/data').glob('*.csv'))+[CURRENT/'upside/features.py',CURRENT/'project/research.py',CURRENT/'project/results/features.pkl']
    sources={str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(source_paths))}
    (OUT/'build_source_inputs.json').write_text(json.dumps(sources,indent=2))
    output=[p for p in OUT.rglob('*') if p.is_file() and p.name!='output_manifest.json']
    (OUT/'output_manifest.json').write_text(json.dumps({str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output)},indent=2))
    print('VERIFIED',checks,'output files',len(output))
if __name__=='__main__':main()
