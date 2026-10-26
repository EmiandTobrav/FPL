"""Navigate research and register bounded experiments without launching training."""
import argparse
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
OVERVIEW = ROOT / 'overview'
RECORDS = ROOT / 'experiments'
IDENTITY = ('dataset_id', 'input_hashes', 'clock', 'features', 'candidate_id',
            'model_parameters', 'decision_policy', 'benchmark_id', 'seasons', 'resources')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def local(path):
    p = (ROOT / path).resolve()
    if not p.is_relative_to(ROOT.resolve()) or not p.is_file():
        raise ValueError(f'File is missing or outside project: {path}')
    return p


def fingerprint(spec):
    identity = {k: spec[k] for k in IDENTITY}
    identity['seasons'] = sorted(identity['seasons'])
    return hashlib.sha256(json.dumps(identity, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def catalog():
    records = read(OVERVIEW / 'research_catalog.json')
    for p in sorted(RECORDS.glob('*.proposal.json')):
        spec = read(p)
        result = p.with_name(p.name.replace('.proposal.json', '.result.json'))
        records.append({'id': spec['id'], 'candidate_id': spec['candidate_id'],
            'title': spec['hypothesis'], 'status': 'completed' if result.exists() else 'registered',
            'finding': read(result)['conclusion'] if result.exists() else 'Not run by this register.',
            'evidence': [str(p.relative_to(ROOT))], 'fingerprint': spec['fingerprint']})
    return records


def validate(spec):
    required = (*IDENTITY, 'id', 'hypothesis', 'change', 'related_work',
                'success_criterion', 'stop_rule', 'maximum_runs')
    for key in required:
        if key not in spec or spec[key] is None or spec[key] == '':
            raise ValueError(f'Fill required field: {key}')
    if not isinstance(spec['input_hashes'], dict) or not spec['input_hashes']:
        raise ValueError('input_hashes must bind actual files, including a dataset manifest.')
    if not isinstance(spec['maximum_runs'], int) or isinstance(spec['maximum_runs'], bool) or spec['maximum_runs'] < 1:
        raise ValueError('maximum_runs must be a positive integer.')
    if not isinstance(spec['related_work'], list) or not spec['related_work']:
        raise ValueError('Review at least one related catalog entry before registration.')
    if not isinstance(spec['seasons'], list) or not spec['seasons'] or len(set(spec['seasons'])) != len(spec['seasons']):
        raise ValueError('seasons must be a nonempty unique list.')
    for name in ('model_parameters', 'decision_policy', 'resources'):
        if not isinstance(spec[name], dict) or not spec[name]:
            raise ValueError(f'{name} must be an explicit nonempty object.')
    active = read(OVERVIEW / 'PROJECT.json')
    if spec['dataset_id'] != active['dataset']['id'] or spec['benchmark_id'] != active['benchmark']['id']:
        raise ValueError('Proposal differs from active dataset or benchmark; establish an explicit new project contract first.')
    if not any(p.endswith('/manifest.json') and p.startswith(active['dataset']['directory'] + '/') for p in spec['input_hashes']):
        raise ValueError('Bind the active dataset manifest in input_hashes.')
    for path, expected in spec['input_hashes'].items():
        if sha(local(path)) != expected:
            raise ValueError(f'Input changed or hash is wrong: {path}')
    records = catalog()
    known = {r['id'] for r in records}
    if any(r not in known for r in spec['related_work']):
        raise ValueError('related_work contains an unknown catalog ID.')
    fp = fingerprint(spec)
    for record in records:
        if record.get('fingerprint') == fp:
            raise ValueError(f'Identical registered experiment: {record["id"]}')
        if record['id'] == spec['id']:
            raise ValueError(f'Experiment ID already exists: {spec["id"]}')
        if record.get('candidate_id') == spec['candidate_id']:
            raise ValueError(f'Candidate already explored: {record["id"]}. Use an explicit new version and state the changed hypothesis.')
    return fp


def exclusive(path, data):
    path.parent.mkdir(exist_ok=True)
    with path.open('x', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write('\n')


def refresh():
    records = catalog()
    for r in records:
        for p in r['evidence']:
            local(p)
    state = read(local(read(OVERVIEW / 'PROJECT.json')['evaluation']['status_source']))
    lines = ['# FPL arbeidsstatus', '',
        'Dette er en lesende oversikt. Kildenes lagrede status beviser ikke at en prosess fortsatt kjører.', '',
        f'**Siste registrerte fase:** `{state.get("phase", "unknown")}`.',
        f'**Status oppdatert i kildefilen:** {state.get("updated_at_utc", "unknown")}.', '',
        'Start med [arbeidsflyten](WORKFLOW.md), [neste steg](NEXT.md) og [prosjektregisteret](PROJECT.json).', '',
        '| ID | Metode eller trinn | Status | Funn |', '|---|---|---|---|']
    for r in records:
        title = r['title'].replace('|', '/')
        finding = r['finding'].replace('|', '/').replace('\n', ' ')
        lines.append(f'| {r["id"]} | [{title}](../{r["evidence"][0]}) | {r["status"]} | {finding} |')
    lines += ['', 'Tall fra ulike kontrakter kan ikke summeres eller rangeres direkte. '
              'Se [metodeoversikten](METHODS.md) for sammenligningsgrunnlag. '
              'Negative resultater er del av utgangspunktet for neste hypotese.', '']
    (OVERVIEW / 'STATUS.md').write_text('\n'.join(lines), encoding='utf-8')
    journal = local('reports/fpl_improvement_2026_10_14/campaign_registry.jsonl')
    timeline = ['# FPL arbeidshistorikk', '',
        'Hendelser fra eksisterende kampanjelogg, i registrert rekkefølge. Tid vises i Europe/Oslo når UTC-tid finnes. '
        'En plan, klargjøring eller godkjenning er ikke et fullført modellforsøk.', '',
        '| Tid | Hendelse | Registrert merknad |', '|---|---|---|']
    for number, line in enumerate(journal.read_text().splitlines(), 1):
        event = json.loads(line)
        when = event.get('at_utc', '')
        try:
            when = datetime.fromisoformat(when.replace('Z', '+00:00')).astimezone(ZoneInfo('Europe/Oslo')).strftime('%d.%m.%Y %H:%M')
        except ValueError:
            pass
        title = str(event.get('event', event.get('kind', 'registered event'))).replace('|', '/')
        detail = str(event.get('details', event.get('status', event.get('decision', '')))).replace('|', '/').replace('\n', ' ')
        timeline.append(f'| {when} | {title} | {detail[:240]} |')
    timeline += ['', '[Full kilde med alle detaljer](../reports/fpl_improvement_2026_10_14/campaign_registry.jsonl). '
                 'Eldre faser er samlet i [arbeidsstatusen](STATUS.md) og [metodeoversikten](METHODS.md).', '']
    (OVERVIEW / 'TIMELINE.md').write_text('\n'.join(timeline), encoding='utf-8')
    print(f'Refreshed status: {len(records)} catalog entries. Source phase: {state.get("phase")}.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('refresh')
    sub.add_parser('status')
    p = sub.add_parser('search'); p.add_argument('query')
    for cmd in ('check', 'register'):
        p = sub.add_parser(cmd); p.add_argument('spec', type=Path)
    p = sub.add_parser('complete'); p.add_argument('experiment_id'); p.add_argument('result', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'refresh':
            refresh()
        elif args.command == 'status':
            state = read(local(read(OVERVIEW / 'PROJECT.json')['evaluation']['status_source']))
            print('Recorded phase:', state.get('phase'), '\nRecorded next actions:')
            for action in state.get('next_actions', []): print('-', action)
            print('\nNo launch, retry or process verification performed.')
        elif args.command == 'search':
            terms = args.query.lower().split()
            hits = [r for r in catalog() if all(t in json.dumps(r, ensure_ascii=False).lower() for t in terms)]
            print(json.dumps(hits, indent=2, ensure_ascii=False))
        elif args.command in ('check', 'register'):
            spec = read(args.spec); fp = validate(spec)
            if args.command == 'register':
                spec.update(fingerprint=fp, registered_at_utc=datetime.now(timezone.utc).isoformat())
                exclusive(RECORDS / (fp + '.proposal.json'), spec)
                refresh()
            print('Contract validated. Does not launch or authorize training. Fingerprint:', fp)
        elif args.command == 'complete':
            matches = [p for p in RECORDS.glob('*.proposal.json') if read(p)['id'] == args.experiment_id]
            if len(matches) != 1: raise ValueError('Expected one locally registered proposal.')
            result = read(args.result)
            for key in ('conclusion', 'decision', 'results', 'evidence_hashes'):
                if not result.get(key): raise ValueError(f'Missing result field: {key}')
            if result['decision'] not in ('reject', 'retain_for_research', 'promote_to_review'):
                raise ValueError('Unknown decision; benchmark promotion requires a separate review.')
            for p, expected in result['evidence_hashes'].items():
                if sha(local(p)) != expected: raise ValueError(f'Result evidence changed: {p}')
            result['experiment_id'] = args.experiment_id
            exclusive(matches[0].with_name(matches[0].name.replace('.proposal.json', '.result.json')), result)
            refresh()
    except (ValueError, OSError, KeyError, TypeError) as e:
        parser.exit(2, f'{e}\n')


if __name__ == '__main__':
    main()
