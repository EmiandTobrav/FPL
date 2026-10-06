"""A bounded, chronological prediction experiment; not a squad backtest."""
from pathlib import Path
import sys, json
import numpy as np
import pandas as pd
from sklearn.base import clone
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'project/tuning_v3'))
from build_inputs import design, BASE, FX
from legacy_candidates import ResidualHGB, minutes_baseline

def main():
    source = ROOT/'project/results/features.pkl'
    if not source.exists():
        import research
        d, fixtures = research.load_data()
        research.features(d, fixtures)
    d = design(pd.read_pickle(source))
    cols = BASE + FX
    records = []
    audits = []
    for y in range(2020, 2026):
        season = f'{y}-{str(y+1)[-2:]}'
        import pickle
        with open(ROOT/f'project/tuning_v3/inputs_{season}.pkl','rb') as f:
            cutoff = pd.Timestamp(pickle.load(f)[1]['cutoff'])
        train = d[(d.season < season) & (d.available < cutoff)]
        valid = d[(d.season == season) & (d.event >= 5)].copy()
        residual = ResidualHGB().fit(train[cols], train.historic)
        direct = clone(residual.model).fit(train[cols], train.historic)
        predictions = {'minutes_shrinkage_6':minutes_baseline(valid),
                       'direct_hgb':direct.predict(valid[cols]),
                       'residual_hgb':residual.predict(valid[cols])}
        for name, pred in predictions.items():
            pred = np.maximum(0, pred)
            errors = pred - valid.historic.to_numpy()
            records.append(dict(season=season, model=name, n=len(valid),
                mae=float(np.abs(errors).mean()), rmse=float(np.sqrt((errors**2).mean()))))
        audits.append(dict(season=season, train_rows=len(train),
            train_max=str(train.available.max()), cutoff=str(cutoff)))
        print(season, records[-3:], flush=True)
    out=ROOT/'results/legacy_review';out.mkdir(exist_ok=True)
    pd.DataFrame(records).to_csv(out/'prediction_probe.csv',index=False)
    (out/'protocol.json').write_text(json.dumps(dict(
        purpose='Residual idea feasibility; no transfer/lineup simulation',
        train='Previous seasons only, available strictly before opening cutoff',
        target='Same fixture historic points; features before same GW cutoff',
        rows='Observed player-fixture rows GW5-38; not full eligible player pool',
        limitations=['All seasons previously examined','No new final FPL score claim',
          'Six-observation shrinkage adapts old five-GW idea; not exact reproduction',
          'Direct and residual HGB identical features and hyperparameters'],audits=audits),indent=2))
if __name__=='__main__':main()
