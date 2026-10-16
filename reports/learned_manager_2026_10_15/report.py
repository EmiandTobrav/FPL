"""Summarize only a completed, audited frozen comparison; never launch a run."""
import csv
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from model_lab.common import read, sha, atomic_json


def table(path, rows):
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader(); w.writerows(rows)


def main():
    audit = read(HERE / 'audit.json')
    if audit['status'] != 'pass' or audit['rounds_recomputed'] != 228:
        raise ValueError('Require all six audited full seasons')
    protocol = read(HERE / 'protocol.json')
    reference, candidate = protocol['reference'], protocol['candidate']
    records = {(r['season'], r['policy']): r for r in audit['records']}
    rows, rounds, chips, training = [], [], [], []
    changes = {r['season']: r['different_round_decisions'] for r in audit['decision_changes']}
    for season in protocol['seasons']:
        a, b = records[season, reference], records[season, candidate]
        rows.append({'season': season, 'trained_evaluation': season != '2022-23',
            'reference_net_points': a['net_points'], 'candidate_net_points': b['net_points'],
            'difference': b['net_points'] - a['net_points'],
            'reference_hit_cost': a['hit_cost'], 'candidate_hit_cost': b['hit_cost'],
            'different_round_decisions': changes[season],
            'reference_solver_calls': a['solver_calls'], 'candidate_solver_calls': b['solver_calls'],
            'reference_solver_seconds': a['original_solver_seconds_sum'],
            'candidate_solver_seconds': b['original_solver_seconds_sum'],
            'reference_decision_cpu_seconds': a['decision_process_cpu_seconds'],
            'candidate_decision_cpu_seconds': b['decision_process_cpu_seconds'],
            'candidate_fit_cpu_seconds': b['policy_fit_cpu_seconds']})
        samples = read(HERE / 'training' / f'{season}_samples.json')
        for chip in ['triple_captain', 'bench_boost']:
            subset = [r for r in samples if r['chip'] == chip]
            events = {(r['season'], r['future_exercise_round']) for r in subset}
            training.append({'evaluation_season': season, 'chip': chip, 'training_rows': len(subset),
                'distinct_teacher_exercises': len(events),
                'training_seasons': ', '.join(sorted({r['season'] for r in subset}))})
        for gw in range(1, 39):
            logs = {p: read(HERE / 'runs' / f'{season}__{p}' / f'gw{gw:02d}.json') for p in [reference, candidate]}
            rounds.append({'season': season, 'round': gw,
                'reference_net_points': logs[reference]['net_points'],
                'candidate_net_points': logs[candidate]['net_points'],
                'difference': logs[candidate]['net_points'] - logs[reference]['net_points'],
                'reference_chip': logs[reference]['chip'], 'candidate_chip': logs[candidate]['chip']})
            for p, log in logs.items():
                if log['chip']:
                    chips.append({'season': season, 'policy': p, 'round': gw, 'chip': log['chip'],
                        'net_points': log['net_points'], 'captain': log['decision']['captain']})
    table(HERE / 'results.csv', rows); table(HERE / 'rounds.csv', rounds)
    table(HERE / 'chips.csv', chips); table(HERE / 'training_summary.csv', training)
    trained = [r for r in rows if r['trained_evaluation']]
    mean = sum(r['difference'] for r in trained) / len(trained)
    success = all(r['difference'] > 0 for r in trained) and mean > 0
    conclusion = (f'Lært TC/BB-reserve ga {mean:+.1f} netto poeng i snitt i de to lærte evalueringssesongene; '
        + ('begge sesonger positive. Pilotkravet bestått; behold benchmark inntil separat vurdering.' if success
           else 'pilotkravet om gevinst i begge sesonger ble ikke oppfylt. Behold dagens benchmark.'))
    lines = ['# Lært managerpolicy: kontrollert sammenligning', '', conclusion, '',
        'Prognosene er identiske. Bare verdien av å spare Triple Captain og Bench Boost er lært. '
        'Kandidaten styrer lovlige, hele sesongforløp gjennom den eksisterende planleggeren. '
        'Dette er en liten lært beslutningskomponent, ikke en full manager lært med reinforcement learning.', '',
        '| Sesong | Rolle | Benchmark | Lært policy | Forskjell | Endrede rundebeslutninger |',
        '|---|---|---:|---:|---:|---:|']
    for r in rows:
        role = 'Lært evaluering' if r['trained_evaluation'] else 'Kontroll uten læring'
        lines.append(f"| {r['season']} | {role} | {r['reference_net_points']:.0f} | {r['candidate_net_points']:.0f} | {r['difference']:+.0f} | {r['different_round_decisions']} |")
    lines += ['', f'Primært snitt for 2023/24 og 2024/25: **{mean:+.1f} poeng per sesong**. '
        f"Snitt over alle tre, inkludert kontrollen: {sum(r['difference'] for r in rows) / 3:+.1f}. "
        'Poeng er etter overgangskostnader. Den kalde kontrollen inngår ikke som bevis for læring.', '',
        '## Hva ble lært?', '',
        'To små Ridge-modeller lærer diskontert chipbonus fra benchmarkens faktiske senere chipbruk i tidligere sesonger. '
        'Det velges ikke en optimal fremtidig runde med fasit. Modellen for 2023/24 bruker bare 2022/23; '
        'modellen for 2024/25 bruker 2022/23 og 2023/24. Modeller og skalering fryses før første frist.', '',
        '| Evalueringssesong | Chip | Treningsrader | Ulike observerte chipbruk |', '|---|---|---:|---:|']
    for r in training:
        lines.append(f"| {r['evaluation_season']} | {r['chip']} | {r['training_rows']} | {r['distinct_teacher_exercises']} |")
    lines += ['', 'Flere treningsrader deler samme senere chiputfall. De er derfor ikke uavhengige treningseksempler. '
        'Datagrunnlaget er lite og følger én eksisterende managers atferd. Modellen lærer ikke en identifisert '
        'kontrafaktisk verdi av å vente og deretter velge andre lag.', '',
        '## Hvilke valg ble endret?', '',
        '| Sesong | Policy | Triple Captain, runder | Bench Boost, runder | Overgangskostnad |',
        '|---|---|---|---|---:|']
    for season in protocol['seasons']:
        for p in [reference, candidate]:
            def used(chip):
                return ', '.join(str(r['round']) for r in chips if r['season'] == season and r['policy'] == p and r['chip'] == chip) or 'Ingen'
            label = 'Benchmark' if p == reference else 'Lært policy'
            lines.append(f"| {season} | {label} | {used('triple_captain')} | {used('bench_boost')} | {records[season, p]['hit_cost']} |")
    lines += ['', 'Sesongforskjellen inkluderer alle senere følger av endrede handlinger. '
        'Den kan ikke tilskrives chipbonus alene; tropp, kaptein og bytter kan også avvike etter første forskjell. '
        '[Rundetabellen](rounds.csv) og [chiploggen](chips.csv) viser forløpet.', '',
        '## Ressurser og kontroller', '',
        'Begge bruker samme datasett, 114 fryste prognosetidspunkter, lovlighetsmotor, startregler, '
        'planlegger og grenser: én tråd/arbeider, samme frø, 16 noder per løserkall og høyst 40 kall per beslutning. '
        'Ingen prognosemodell trenes på nytt. Begge har en tildelt grense på fem CPU-sekunder til policytilpasning per sesong. '
        'Lik ressursramme innebærer ikke lik faktisk bruk. Tilpasningstiden måler selve Ridge/skalering; '
        'uttrekk av treningsrader og verifisering av arkivfiler er forarbeid uten separat tidsmåling.', '',
        '| Sesong | Løserkall benchmark / lært | Løsersekunder benchmark / lært | Tilpasning lært, CPU-s |',
        '|---|---:|---:|---:|']
    for r in rows:
        lines.append(f"| {r['season']} | {r['reference_solver_calls']} / {r['candidate_solver_calls']} | {r['reference_solver_seconds']:.1f} / {r['candidate_solver_seconds']:.1f} | {r['candidate_fit_cpu_seconds']:.4f} |")
    lines += ['', 'Faktisk CPU og veggklokketid per sesong finnes i sesongkvitteringene. For benchmark 2022/23 '
        'gikk totalmålingen tapt ved en mekanisk oppsummeringsfeil. De 38 fullførte rundene ble bevart og validert '
        'uten nye løserkall. Per-kall-tid er bevart. Se [metodikk og retting](README.md).', '',
        'Etterkontrollen består: 228 oppgjør og tilstandsoverganger er beregnet på nytt; '
        'alle 114 referanserunder gjenskaper arkivert benchmarkhandling og poeng; '
        'kontrollen uten læring er identisk; inputhash, uendrede prognoser, treningsdatoer, koeffisienter '
        'og løsergrenser er kontrollert. Ukjente valgte utfall ble ikke gjort om til nuller. '
        'Dette er en maskinell etterkontroll som gjenbruker den samme regelmotoren, ikke en ekstern validering av reglene.', '',
        '## Tolkning og videre arbeid', '',
        ('Pilotkravet er bestått, men benchmark oppgraderes ikke automatisk. Neste vurdering bør undersøke '
         'om gevinsten tåler et bredere, tidsriktig treningsgrunnlag og en på forhånd fastlagt ny evaluering.' if success else
         'Denne versjonen erstatter ikke benchmarken. Behold resultatet som en avvist kandidat under den registrerte '
         'hypotesen; ikke juster vekter og test på de samme resultatene som om det var en ny bekreftelse. '
         'Et eventuelt neste forsøk bør først forbedre antall uavhengige, tidsriktige chipforløp og verdien av '
         'å vente under alternative lovlige viderehandlinger.'), '',
        'Bare to sesonger tester faktisk læring. Alle evalueringsårene er allerede studerte utviklingsdata. '
        'Ingen påstand om statistisk signifikans, generell overlegenhet eller vinnsannsynlighet følger av dette. '
        '2025/26 er ikke brukt i dette forsøket. Det eksisterende best-effort-poengmålet og dets kvalitetsbegrensninger gjelder fortsatt.', '',
        '## Sporbarhet', '',
        '- [Fryst protokoll](protocol.json), [registrering](registration.json) og [etterkontroll](audit.json).',
        '- [Sesongresultater og ressurser](results.csv), [rundepoeng](rounds.csv), [chipvalg](chips.csv), [treningsomfang](training_summary.csv).',
        '- `training/`: treningsrader og koeffisienter. `runs/`: låste avgjørelser, oppgjør og kvitteringer.',
        '- `failure.json` og `mechanical_resume_v002.*`: bevart feil og eksplisitt mekanisk retting. `complete.json`: faktisk fullføring.', '']
    (HERE / 'RESULTATER.md').write_text('\n'.join(lines), encoding='utf-8')
    evidence = [HERE / name for name in ['protocol.json', 'audit.json', 'complete.json', 'RESULTATER.md',
        'results.csv', 'rounds.csv', 'chips.csv', 'training_summary.csv', 'mechanical_resume_v002.json']]
    evidence += sorted((HERE / 'training').glob('*.json'))
    evidence += sorted((HERE / 'runs').rglob('*.json'))
    result = {'conclusion': conclusion, 'decision': 'promote_to_review' if success else 'reject',
        'results': {'seasons': rows, 'trained_mean_difference': mean, 'pilot_success': success,
            'benchmark_unchanged': True, 'forecast_training_calls': 0},
        'evidence_hashes': {str(p.relative_to(ROOT)): sha(p) for p in evidence}}
    atomic_json(HERE / 'result.json', result)
    print(json.dumps({'conclusion': conclusion, 'decision': result['decision']}, ensure_ascii=False))


if __name__ == '__main__':
    main()
