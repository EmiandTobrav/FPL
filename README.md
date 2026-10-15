# FPL modellutvikling

Start i den samlede arbeidsoversikten. Den peker til det rekonstruerte datasettet, modellpipelinen, forsøksresultatene og neste handling. Ingen ny produksjonsmodell er valgt.

## Start her

| Oppgave | Inngang |
|---|---|
| Se utført arbeid og registrert status | [Arbeidsstatus](overview/STATUS.md) |
| Fortsette fra riktig sted | [Neste steg](overview/NEXT.md) |
| Se metoder og positive eller negative resultater | [Metodeoversikt](overview/METHODS.md) |
| Se hendelser, feil og endringer underveis | [Arbeidshistorikk](overview/TIMELINE.md) |
| Finne gjeldende data og benchmark | [Prosjektregister](overview/PROJECT.json) |
| Kjøre modelltester og simulering | [Felles Model Lab](model_lab/README.md) |
| Planlegging uten reservekostnader | [Kontrollert H2-forsøk](reports/explicit_planning_2026_10_15/RESULTATER.md) |
| Sesonglang managerlæring med alle chips | [Forsøk og resultater](reports/season_manager_2026_10_15/RESULTATER.md) |
| Kontrollert forsøk med lært managerpolicy | [Resultater med uendrede prognoser](reports/learned_manager_2026_10_15/RESULTATER.md) |
| Utforske trening som en faktisk manager | [Forskningsidé og vinnermål](overview/MANAGER_LEARNING.md) |
| Planlegge og registrere et nytt forsøk | [Arbeidsflyt](overview/WORKFLOW.md) |
| Forstå Git-strukturen og hva som er publisert | [Git og publiseringsomfang](docs/GIT_LAYOUT.md) |

## Gjeldende datagrunnlag

[datasets/fpl_2026_27_best_effort_v1](datasets/fpl_2026_27_best_effort_v1/README.txt) inneholder den praktiske utgivelsen med poengmål etter 2026/27-reglene og 159291 modellrader. Originaler, aksepterte estimater og kvalitetsflagg beholdes. Dette er en separat best-effort-utgivelse; streng kildekvalifisering er ikke fullført.

[datasets/fpl_model_preparation_v1](datasets/fpl_model_preparation_v1/README.txt) er featuregrunnlaget. [datasets/fpl_model_pipeline_v1](datasets/fpl_model_pipeline_v1/README.txt) er gjeldende inngang for foldvis behandling, trening og prediksjon. Standardklokken er operational_proxy_v1, med conservative_v1 som kontroll. Pakken inneholder fungerende innlesere, tabeller, schema og eksplisitte avhengigheter. Ingen ZIP-utpakking er nødvendig.

Benchmarkfamilien for disse omregnede forsøkene er fixture_full_h3_adaptive_tc_harmonized_causal_v1. Sammenlign netto sesongpoeng på samme data, sesonger, informasjon, starttilstand, policy og ressurser. Prognosefeil er diagnostikk. Den gamle benchmarkens 2351,5 poeng gjelder eldre poengmål og skal ikke overføres til det nye datasettet.

## Videre arbeid

Les arbeidsstatus, neste steg og arbeidsflyt før nye modellforsøk. Søk etter kandidat og mekanisme før registrering. Registreringsverktøyet oppdager identiske nye forsøkskontrakter og endrede inputfiler; relatert eldre arbeid må også vurderes manuelt. Registrering starter ingen kjøring.

```sh
python3 scripts/research.py status
python3 scripts/research.py search "spilletid"
python3 scripts/research.py refresh
python3 -m unittest discover -s scripts -p test_research.py
```

De gamle forskningsmappene og benchmarkdefinisjonene er bevart. [Tidligere startside](docs/LEGACY_README_20261014.md) gir inngang til eldre kode og metodeforsøk. Bruk de nye datasettenes innlesere for omregnede targets; den eldre prepare_data.py tilhører den historiske pipelinen.

## Publisert og lokalt arbeidsmateriale

Git inneholder den portable data- og modellpipelinen, samlet navigasjon og utvalgte resultatkvitteringer. Den nyere kampanjestatusen er et datert kildeuttrekk og beviser ikke at en prosess fortsatt kjører. Full rekonstruksjonsreplay og videreføring av den avanserte simulator-/H8-kampanjen krever det lokale arbeidsarkivet, som har ekstra kode, forecast-cache, beslutningslogger og kildebevis. De delene inngår ikke i denne avgrensede publikasjonen.

[Publiseringsmanifestet](overview/publication_manifest.json) oppgir de konkrete filene og kontrollsummene. Sammendrag og kontrollrapporter skal ikke forveksles med en full eksport av alle bevisfilene de refererer til.

Model Lab kan kjøres direkte fra denne publikasjonen med sine små låste eksempler. De gamle, komplette simulator-/H8-kampanjene har fortsatt separat arkivavhengighet. Første lærte chipreserve er nå testet med uendrede prognoser. Se [kontrollert managerpilot](reports/learned_manager_2026_10_15/RESULTATER.md). Full managerlæring og vinnermål er videre forskning.
