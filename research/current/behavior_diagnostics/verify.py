from common import *
import hashlib

def main():
    audit=pd.read_csv(OUT/'feature_audit.csv')
    assert len(audit)==204 and (pd.to_datetime(audit.latest_feature_outcome,utc=True)<pd.to_datetime(audit.cutoff,utc=True)).all()
    protocol=json.loads((HERE/'chip_ablation_protocol.json').read_text());n=0
    for regime,rounds in protocol['new_regimes'].items():
        for s in SEASONS:
            base=trace(s,REF,'fixed_chips')
            for m in protocol['models']:
                fn=OUT/f'ablation_{regime}/trace_{s}_{m}_fixed_chips.json.gz';o=json.loads(gzip.decompress(fn.read_bytes()));rows=o['trace']
                assert o['handoff']==base['handoff'] and o['opening']==base['opening']
                assert [r['gw'] for r in rows]==list(range(5,39))
                assert {r['gw']:r['chip'] for r in rows if r['chip']}=={gw:experiment.CAL[gw] for gw in rounds}
                assert o['summary']['points38']==o['summary']['opening_points']+sum(r['net'] for r in rows)
                for r in rows:
                    assert r['net']==r['gross']-r['hits']
                    assert r['gross']==sum(r['contributions'].values())+r['captain_bonus']
                    assert r['bank']>=0 and 1<=r['ft']<=5 and len(set(r['squad']))==15 and len(r['starters'])==11
                n+=1
    inter=pd.read_csv(OUT/'path_interaction_summary.csv').pivot(index='comparison',columns='metric',values='interaction')
    np.testing.assert_allclose(inter.net,inter[['xi','captain','tc','bb','hits']].sum(axis=1),atol=1e-10)
    p=pd.read_csv(OUT/'ablation_factorial_seasons.csv')
    np.testing.assert_allclose(p.fixed_chips-p.no_chips,p.reset_effect+p.bonus_effect+p.interaction,atol=1e-10)
    assert n==144
    # Hash the exact source files and local input representations used in this diagnostic.
    paths=list(HERE.glob('*.py'))+list(HERE.glob('*protocol.json'))
    paths+=[CURRENT/'experiment.py',CURRENT/'project/season_simulator.py',CURRENT/'project/research.py',CURRENT/'project/tuning_v3/decision.py',CURRENT/'project/tuning_v3/build_inputs.py',CURRENT/'project/results/features.pkl']
    paths+=list((CURRENT/'upside').glob('*.py'))+list((CURRENT/'retrained_ensemble').glob('*.py'))
    paths+=list((CURRENT/'project/data').glob('*.csv'))+list((CURRENT/'project/tuning_v3').glob('inputs_*.pkl'))+list((CURRENT/'results').glob('games_*.pkl'))
    for directory in ['results','retrained_ensemble/results','adaptive_events/results']:
        paths+=list((CURRENT/directory).glob('predictions_*.csv.gz'))+list((CURRENT/directory).glob('trace_*.json.gz'))
    manifest={str(p.relative_to(CURRENT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
    (OUT/'source_input_manifest.json').write_text(json.dumps(manifest,indent=2))
    output_paths=[p for p in OUT.rglob('*') if p.is_file() and p.name not in ['output_manifest.json','verification.json']]
    (OUT/'output_manifest.json').write_text(json.dumps({str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(output_paths)},indent=2))
    checks=dict(verified_ablation_seasons=n,identical_handoff=True,exact_chip_schedules=True,point_accounting=True,temporal_features=True,additive_decompositions=True,source_input_files=len(manifest),output_files=len(output_paths))
    (OUT/'verification.json').write_text(json.dumps(checks,indent=2));print(checks)
if __name__=='__main__':main()
