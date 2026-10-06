# FPL modellutvikling

Dette repositoryet er felles utgangspunkt for kode, resultater og videre arbeid på tvers av enheter. Det samler mai-prosjektet og den nye start-/hovedmodelltesten. Ingen ZIP-utpakking er nødvendig.

## Start her

- [Status og neste steg](docs/STATUS.md)
- [Oppsidemodeller: 48 nye forløp og resultater](research/current/upside/README.md)
- [Oppside som variabel og kapteinssignal: oppfølgingstest](research/current/upside_feature/README.md)
- [Faglitteratur og prioriterte forsøk](docs/LITERATURE_REVIEW.md)
- [Gjennomgang av det eldre repositoryet](docs/REPOSITORY_REVIEW.md)
- [Aktuell forsøksprotokoll](research/current/protocol.json)
- [Sesongresultater: 120 forløp](research/current/results/season_results.csv)
- [Modellsammendrag](research/current/results/model_summary.csv)
- [Tidsordnet modellvalg](research/current/results/chronological_selection.csv)
- [Detaljert rapport](research/current/FPL_hovedmodell_test.html) (last ned og åpne i nettleser)

## Kjør på en ny maskin

```bash
git clone https://github.com/EmiandTobrav/FPL.git
cd FPL
python -m venv .venv
source .venv/bin/activate
pip install -r research/current/requirements_versions.txt pytest requests pyarrow
python scripts/prepare_data.py
PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m pytest -q
cd research/current
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python experiment.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python summarize.py
```

Bruk Python 3.12. På Windows aktiveres miljøet med `.venv\Scripts\activate`, og miljøvariablene settes med PowerShell-syntaks. Repositoryet er privat; Git må ha tilgang til kontoen.

`prepare_data.py` gjenoppretter hver datafil fra en separat gzip-fil og kontrollerer SHA-256. Det krever verken ZIP-verktøy, Git LFS eller tilgang til denne samtalen. Pickle-inngangene er våre egne fryste data; bruk kun en betrodd checkout.

Eksisterende beslutningsspor brukes som cache. For en full ny avspilling slettes `research/current/results/trace_*.json.gz` lokalt før `experiment.py`. Ikke gjenbruk spor etter endringer i modeller eller input. For nye prognoser slettes `results/games_*.pkl` og `project/results/features.pkl` før `build.py`. Bevar resultater fra hvert nytt eksperiment separat; referanseforsøket skal ikke overskrives med en annen protokoll.

## Struktur og status

| Område | Rolle |
|---|---|
| `research/current/` | Aktiv forskning: startmodell til GW4, hovedmodell til GW38, fryste innganger og beslutningsspor |
| `src/`, `tests/`, `reports/` | Bevart eldre pipeline, tester og historiske rapporter; se metodeforbehold i gjennomgangen |
| `docs/` | Beslutninger, funn og konkret fortsettelseskontekst |
| `scripts/prepare_data.py` | Automatisk klargjøring og kontroll av innganger |

Den beskrivende kandidaten er 50/50 Ridge + Extra Trees: +37,17 poeng uten chips og +55,67 med fast chipkalender mot Ridge i gjennomsnitt over seks sesonger. Dette er retrospektive resultater, ikke en urørt sluttprøve. Fritt tidsordnet modellvalg ga bare +3,75/+2,25 poeng over fire evalueringssesonger. Ingen produksjonsmodell er byttet automatisk.

Historiske poeng spilles av med moderne bytte-/chipregler. Pris, spillerstatus og kampkalender har dokumenterte proxybegrensninger. Resultatene er ikke faktiske historiske rangeringer eller en full omregning til årets poengregler.
