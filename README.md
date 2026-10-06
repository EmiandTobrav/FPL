# FPL modellutvikling

Dette repositoryet er felles utgangspunkt for kode, resultater og videre arbeid på tvers av enheter. Det samler mai-prosjektet og den nye start-/hovedmodelltesten. Ingen ZIP-utpakking er nødvendig.

**Gjeldende arbeidsbenchmark:** global, lært HGB-vekt med tre-rundersplanlegging (`constant_h3`), valgt av brukeren 6. oktober 2026. Gjennomsnitt 2308,25 poeng med chips på 2022/23–2025/26. Nye forsøk måles mot denne; historiske tabeller beholder sine opprinnelige referanser. Se [benchmarkmanifestet](research/current/benchmark.json).

## Start her

- [Status og neste steg](docs/STATUS.md)
- [Posisjonsspesialisering: 32 nye forløp, benchmarken beholdes](research/current/position_specialist/README.md)
- [Global HGB-vekt med H3: kombinasjonstest, 16 nye forløp](research/current/global_horizon/README.md)
- [Aktive utfordrere](research/current/challengers.json) og [utført kombinasjonsforsøk](docs/NEXT_EXPERIMENT.md)
- [Tre-rundersplanlegging og lært HGB-blanding: 88 nye forløp](research/current/decision_specialist/README.md)
- [Chipmekanismer og modellstyrker per situasjon: diagnostikk og 144 ablasjoner](research/current/behavior_diagnostics/README.md)
- [Retrening av Ridge/Extra Trees og faste blandinger: 60 nye forløp](research/current/retrained_ensemble/README.md)
- [Løpende retrening og hendelsesmodell: 108 nye forløp](research/current/adaptive_events/README.md)
- [Fire-runders planlegging og dekomponert oppsidemodell: 72 forløp](research/current/horizon_upside/README.md)
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

Retreningsrunden: retrent Extra Trees gir +37,2 poeng mot referansen med fast chipkalender, men −39,0 uten chips. Oppdatert treveisblanding gir +26,3/+10,3 med/uten chips. Tidsordnet modellvalg gir −4,25 på primærmålet; ingen automatisk produksjonsendring. Se forsøksrapporten for sesongvariasjon og begrensninger.

Ny diagnostikk: WC/FH gir en viktig del av retreningsgevinsten gjennom troppsendringer; direkte TC/BB-bonuser forklarer lite av omslaget. Utvidet HGB rangerer fallende/ustabil spilletid bedre i alle seks sesonger, mens kort historikk fortsatt er uløst. 4536 matchede beslutninger, 144 chipablasjoner og 176 lokale tester er gjennomført. Se diagnoseoversikten over.

Siste forsøk: oppdatert Ridge/Extra med tre-rundersplanlegging gir +51,0/+31,2 med/uten chips over seks sesonger. Lært global HGB-vekt gir +54,3/+40,5 over fire; situasjonsstyrt vekt +62,0/+12,0, men uten stabil tilleggsverdi over global vekt. Ulike evalueringsperioder må ikke blandes. 88 nye forløp og 179 lokale tester er ferdige; se rapporten over.

Historiske poeng spilles av med moderne bytte-/chipregler. Pris, spillerstatus og kampkalender har dokumenterte proxybegrensninger. Resultatene er ikke faktiske historiske rangeringer eller en full omregning til årets poengregler.
