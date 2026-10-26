# FPL — fra historiske data til begrunnede lagvalg

**Oppdatert 26. oktober 2026:** [Utvidede datasett, korrigert kalender og valgt komponentmodell med fem runders planlegging](releases/2026-10-26/README.md). Historisk gevinst +104 / −13 / +37 mot samme-kalender-kontroll. Selve observasjons- og modelltabellene følger med; full live-/modellreplay krever fortsatt arbeidsarkivet. Eldre daterte statusavsnitt nedenfor gjelder sitt opprinnelige tidspunkt.

Et forskningsprosjekt for **Fantasy Premier League**, der man velger fotballspillere innenfor et budsjett og får poeng fra prestasjonene deres. Prosjektet undersøker hvordan historiske data, maskinlæring og simulering kan støtte valg av spillere, kaptein og bytter. Målet er flere **netto sesongpoeng etter overgangskostnader** — og å kunne etterprøve om en foreslått forbedring faktisk virker.

Dette er også en arbeidsprøve i problemformulering, styring av KI-agenter og evaluering. Jeg definerer mål og krav, koordinerer agentarbeidet, vurderer forslag og korrigerer retningen. KI-agenter implementerer Python-kode, tester og analyser. Jeg har ikke tradisjonell programmeringsbakgrunn; mitt bidrag er å styre utviklingen og vurdere løsningene mot dokumenterte krav. Se [arbeidsmetodikken og rollefordelingen](docs/AI_WORKFLOW.md).

**Les på tre minutter:** [tre konkrete eksempler](docs/CASE_STUDIES.md) → [hvordan arbeidet kvalitetssikres](docs/AI_WORKFLOW.md) → [prøv en begrenset demo](docs/QUICKSTART.md).

## Hva prosjektet inneholder

- Et rekonstruert treningsgrunnlag med **159 291 spiller–runde-rader**, dokumenterte estimater og kvalitetsflagg.
- En modellpipeline som trener på tidligere tilgjengelig historikk og sammenligner prognoser på samme tidsperioder.
- En simulator for lagvalg, kaptein, benk, bytter og spesialfordeler («chips»), med eksplisitte regel- og ressursgrenser.
- Forsøkskontrakter, fryste input, resultatlogger og bevarte negative funn som gjør beslutningene sporbare.

## Fra data til beslutning

```text
Historiske data → rekonstruerte poeng → tidsstyrte features
                                             ↓
                                      poengprognoser
                                             ↓
                              lagvalg og sesongsimulering
                                             ↓
                             kontroll, resultat og beslutning
```

| Del | Ansvar | Teknisk inngang |
|---|---|---|
| Data og features | Skille observasjoner, estimater og informasjon tilgjengelig før fristen | [Datasett](datasets/fpl_2026_27_best_effort_v1/README.txt), [modellpipeline](datasets/fpl_model_pipeline_v1/README.txt) |
| Prognoser og beslutninger | Teste modeller og lovlige lagvalg med felles kontroller | [Model Lab](model_lab/README.md) |
| Evaluering og styring | Låse hypotese og sammenligning, bevare bevis og avgjøre neste steg | [Arbeidsflyt](overview/WORKFLOW.md), [resultatoversikt](docs/RESULTS_INDEX.md) |

Python, pandas, NumPy og scikit-learn brukes i grunnløpet. CatBoost og LightGBM inngår i egne modellspor. KI-agentene er verktøy i utviklingsarbeidet; den simulerte FPL-manageren er en separat beslutningspolicy.

## Tre resultater — og hva de betyr

| Forsøk | Dokumentert resultat | Beslutning |
|---|---|---|
| Bedre kampkontekst i poengmodellen | 1,604 % lavere gjennomsnittlig kvadratfeil (MSE) totalt; 3,288 % blant faste lagkandidater i 2025/26 | Beholdt som forskningskandidat; ikke dokumentert gevinst i sesongpoeng |
| Lære når to chips bør spares | +53 og +41 netto poeng i 2023/24 og 2024/25, snitt **+47**, med uendrede prognoser | Avgrenset pilot bestått; ingen automatisk oppgradering |
| Lære hele managerens handlingsrangering | **−243** poeng i sesongsnitt mot benchmark; **−297,5** mot samme forslagsregler uten læring | Forkastet som oppgradering; kontrollen avdekket svakere beslutninger |

[Eksemplene med problem, metode, kontroll og originalrapporter](docs/CASE_STUDIES.md). Radene gjelder ulike forsøkskontrakter og er ikke én rangering. Historiske perioder er tidligere undersøkt; tallene dokumenterer ikke generell overlegenhet på nye sesonger.

## Prøv prosjektet

[Demooppskriften](docs/QUICKSTART.md) bruker Python 3.12 og eksisterende eksempler: to prognoserunder med høyst fire modelltilpasninger, og én simulert runde med låste prognoser. Ingen API-nøkkel eller privat arbeidsarkiv er nødvendig. Demoen kontrollerer at delene fungerer sammen; den gjentar ikke de store forskningsforsøkene.

## Status og avgrensning

Presentasjonen er gjennomgått 22. oktober 2026, med publiserte resultater fra 16. oktober som grunnlag. **Ingen ny produksjonsmanager er godkjent.** Den fryste prognosepakken `forecast-package-20261016-v1` er et eget spor: GW1–6 er retrospektivt evaluert, og lagrede GW7-prognoser er ikke i seg selv et prospektivt resultat.

Historisk kilde- og fristinformasjon er delvis rekonstruert. Best-effort-poengmål inneholder estimater. Den eldre benchmarken `fixture_full_h3_adaptive_tc` og den omregnede familien `fixture_full_h3_adaptive_tc_harmonized_causal_v1` har ulike poenggrunnlag; gamle poengsummer kan ikke overføres mellom dem.

GitHub inneholder et avgrenset utvalg av det større lokale prosjektet. Utvalgte rapporter kan leses og enkelte lagrede bevis kontrolleres, mens full gjentakelse av avanserte forsøk krever lokale input som ikke følger med. [Publisert versus lokalt materiale](docs/PUBLICATION_SCOPE.md) forklarer dette konkret.

## Videre lesning

| Jeg vil … | Gå til |
|---|---|
| Forstå krav, agentstyring og kvalitetssikring | [Arbeidsmetodikk](docs/AI_WORKFLOW.md) |
| Se alle utvalgte funn, også negative | [Resultatoversikt](docs/RESULTS_INDEX.md) |
| Bidra eller kjøre den eldre kodebasens tester | [Bidragsguide](CONTRIBUTING.md) |
| Finne grener, PR-er og publisert materiale | [GitHub-kart](docs/REPOSITORY_MAP.md), [publiseringsdetaljer](docs/GIT_LAYOUT.md) |
| Finne gjeldende dataversjon og forsøkskontrakter | [Prosjektregister](overview/PROJECT.json), [arbeidshistorikk](overview/TIMELINE.md) |
| Se videre forskningsoppgaver | [Prioriteringer](docs/ROADMAP.md) |
| Forstå den eldre forskningsbasen | [Historisk prosjektinngang](docs/PROJECT_ENTRY_2026_10_07.md) |

Eldre dokumenter beskriver tidspunktet de ble skrevet. Mappenavnet `research/current` betyr ikke at alle forsøk der fortsatt er aktive.
