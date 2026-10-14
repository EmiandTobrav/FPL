"""Simple entry point: init a bounded trial, run it, read the report."""
import os
for name in ['OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS']:
    os.environ[name] = '1'
import argparse
from pathlib import Path
import json
from .common import ROOT, read, sha, atomic_json


def main():
    parser = argparse.ArgumentParser(description='Shared FPL model and simulation lab. No execution on import.')
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('init', help='Create a small validation trial with current file hashes')
    p.add_argument('path', type=Path); p.add_argument('--model', choices=['ridge', 'catboost', 'lightgbm'], default='ridge')
    p.add_argument('--features', choices=['baseline', 'extended'], default='extended')
    p = sub.add_parser('run', help='Run a forecast or simulation spec, with completion reuse')
    p.add_argument('spec', type=Path); p.add_argument('--output', type=Path, default=ROOT / 'lab_results')
    p = sub.add_parser('export-bundle', help='Package bounded existing cache inputs without new forecasts')
    p.add_argument('--cache', type=Path, required=True); p.add_argument('--season', required=True)
    p.add_argument('--rounds', type=int, nargs='+', required=True); p.add_argument('--models', nargs='+', required=True)
    p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('predict-bundle', help='Predict a frozen common pool with a new model')
    p.add_argument('spec', type=Path); p.add_argument('--bundle', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    p = sub.add_parser('simulation-spec', help='Create a bounded validation spec for a prepared bundle')
    p.add_argument('--bundle', type=Path, required=True); p.add_argument('--models', nargs='+', required=True)
    p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == 'init':
            files = ['datasets/fpl_2026_27_best_effort_v1/manifest.json', 'datasets/fpl_model_pipeline_v1/manifest.json',
                     'datasets/fpl_model_pipeline_v1/schema.json', 'datasets/fpl_model_pipeline_v1/operational_proxy_v1.csv.xz']
            spec = {'version': 1, 'kind': 'forecast', 'id': args.path.stem, 'purpose': 'framework_validation',
                'clock': 'operational_proxy_v1', 'seasons': ['2023-24'], 'rounds': [1, 2], 'horizon': 1,
                'max_fits': 4, 'reference': 'mean_control',
                'models': [{'id': 'mean_control', 'backend': 'mean', 'feature_set': 'baseline', 'seed': 20261014, 'parameters': {}},
                           {'id': args.model + '_trial', 'backend': args.model, 'feature_set': args.features, 'seed': 20261014, 'parameters': {}}],
                'input_hashes': {n: sha(ROOT / n) for n in files},
                'note': 'Small wiring check of existing model families, not a new scientific result or manager benchmark comparison.'}
            atomic_json(args.path, spec); print(f'Created {args.path}; run: python -m model_lab run {args.path}')
        elif args.command == 'run':
            spec = read(args.spec)
            if spec.get('kind', 'forecast') == 'forecast':
                from .forecast import run
            elif spec['kind'] == 'simulation':
                from .simulation import run
            else: raise ValueError('Unknown trial kind')
            result = run(spec, args.output)
            from .report import write_report
            report = write_report(Path(result['directory']))
            print(json.dumps({'directory': result['directory'], 'report': str(report), 'reused': result.get('reused_completed_run', False)}, indent=2))
        elif args.command == 'export-bundle':
            from .simulation import export_cache
            print(export_cache(args.cache, args.season, args.rounds, args.models, args.output))
        elif args.command == 'predict-bundle':
            from .simulation import add_forecasts
            print(add_forecasts(read(args.spec), args.bundle, args.output))
        elif args.command == 'simulation-spec':
            from .simulation import BENCHMARK
            path = (args.bundle / 'bundle.json').resolve()
            name = str(path.relative_to(ROOT))
            manifest = read(path)
            atomic_json(args.output, {'version': 1, 'kind': 'simulation', 'purpose': 'framework_validation',
                'bundle': name, 'bundle_sha256': sha(path), 'models': args.models, 'reference': BENCHMARK,
                'max_decisions': len(manifest['origins']) * len(args.models), 'policy': 'adaptive',
                'node_limit': 16, 'max_calls_per_decision': 40})
            print(args.output)
    except (ValueError, FileExistsError, KeyError, ImportError) as exc:
        parser.exit(2, f'{exc}\nA completed run can be reused. Started or failed work is never silently retried.\n')


if __name__ == '__main__':
    main()
