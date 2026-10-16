"""Small, comparable result cards; no automatic model promotion."""
from pathlib import Path
from .common import read


def write_report(directory):
    directory = Path(directory); summary = read(directory / 'summary.json')
    lines = ['# Modellforsøk', '', f'Formål: `{summary["purpose"]}`.', '', summary['interpretation'], '']
    if 'metrics' in summary:
        lines += ['| Modell | Sesong | Rader | RMSE | MAE | RMSE mot kontroll |', '|---|---|---:|---:|---:|---:|']
        for r in summary['metrics']:
            lines.append(f'| {r["model"]} | {r["season"]} | {r["rows"]} | {r["rmse"]:.4f} | {r["mae"]:.4f} | {r["rmse_delta_vs_reference"]:+.4f} |')
        lines += ['', f'Ferdige prognosefolder gjenbrukt: {summary["cached_folds_reused"]}.', '']
    else:
        lines += ['| Modell | Sesong | Runder | Netto poeng | Mot benchmark | Hel sesong | Løserkall |', '|---|---|---:|---:|---:|---|---:|']
        for r in summary['results']:
            lines.append(f'| {r["model"]} | {r["season"]} | {r["rounds"]} | {r["net_points"]:.1f} | {r["gain_vs_reference"]:+.1f} | {r["complete_season"]} | {r["solver_calls"]} |')
    lines += ['', 'Modell og benchmark er ikke automatisk endret. '
              'Les forsøkskontrakten og kontrollene før en metode tas videre.', '',
              '[Fullt resultat](summary.json) · [Fullføringskvittering](complete.json)', '']
    p = directory / 'REPORT.md'; p.write_text('\n'.join(lines)); return p
