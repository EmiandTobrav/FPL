# FPL modellutvikling

Dette repositoryet er felles utgangspunkt for kode, resultater og videre arbeid på tvers av enheter. Det samler mai-prosjektet og den nye start-/hovedmodelltesten. Ingen ZIP-utpakking er nødvendig.

**Gjeldende arbeidsbenchmark:** full kampjustering med H3 og adaptiv Triple Captain (`fixture_full_h3_adaptive_tc`), valgt av brukeren 6. oktober 2026. Gjennomsnitt **2351,50 poeng** på 2022/23–2025/26. Øvrige chips følger faste datoer. Dette er historiske spillerpoeng, ikke full 2025/26-omregning. Se [benchmarkmanifestet](research/current/benchmark.json).

## Start her

**Treningsdatasett, pågående ferdigstillelse — 8. oktober 2026:**
Offisielle 2026/27 GW1–GW5 er samlet i en ny, separat kildeversjon: 1 538
spillerkamper, 50 hele kamper og 3 216 spiller–runde-rader. Poengforklaring,
helkampbonus og kampstatistikk er avstemt. Historisk rest og scoring er fortsatt
uavklart; full treningsleveranse er ikke ferdig.
Historisk beregning er etablert: 185 573 originalrader har avstemt grunnpoeng
og en bevart tidligere versjon har 489 separate omregningskandidater.
**2025/26 har nå kvalifiserte omregnede poengetiketter for 374 hele kamper og
11 315 spillerkamper**, med ny BPS og helkampbonus; 442 poengsummer endres.
Null avvik i komponentregnskapet. Seks kamper er sperret. Tidsriktige features
og kvalifiserte treningsrader gjenstår. Se [kvalifisert poengversjon](research/current/training_dataset/scoring/season_2025_extension/README.md).
Kampstarter er nå kvalifisert for alle 185 573 historiske observasjoner i
2 660 kamper. Komplette startellevere avklarer også 32 672 tidligere manglende
null-minutt-roller. Offisielle lagoppstillinger dokumenterer
2 992 starter som feilaktig stod som null før GW16 i 2022/23. Se
[startdekning og kildekontroll](research/current/training_dataset/lineups/README.md).
En separat xG/xA/xGI/xGC-versjon er nå kvalifisert for alle 26 505 rader i
2022/23. Den dokumenterer tidlig FPL-backfill, en senere GW16-kildeversjon og
296 eksakte GW29-xGI-rettelser; rådata og den mislykkede første kontrollen
bevares. Tilgjengelighet før frist er fortsatt uavklart. Se
[statistikkversjon og kildebevis](research/current/training_dataset/fpl_history_2022/reconciliation/README.md).
Ny legacy-taklingskontroll med 291 primærsvar er gjennomført. Den kvalifiserer
ikke regelen: 15 native BPS-verdier overskrider den foreslåtte klippede grensen,
og fire eksplisitte kildeavvik står åpne. Alle gater og råtellere er bevart.
Se [kontrollbevis og neste avklaringer](research/current/training_dataset/scoring/legacy_tackles/README.md).
Se [dataleveranse og videre arbeid](research/current/training_dataset/README.md)
og [maskinlesbar leveransestatus](research/current/training_dataset/CURRENT.json).

Felles tabeller dekker nå alle åtte sesonger: **187 111 spillerkamper og
181 604 spiller–runde-rader**, med H1-/H3-/H6-targets og en testet innlesings-
kontrakt. 14 365 rundepoeng er kvalifisert; tidsriktige features mangler fortsatt.
Se [datatabeller og innlesing](research/current/training_dataset/canonical_extension/README.md).

**Gjeldende datagapstatus:** **11 219 åpne krav**, **66 478 inputkomplette
spillerkamper og 824 hele kamper**. [15 storsjanseredninger](research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/big_chance_zero_bounds_guarded/README.md)
er avklart med eksakte sesong-/kampgrenser og sperring av en hel lag-sesong
med et tidligere dokumentert hendelsesunntak. Én kandidat forblir åpen.
Alle 983 gamle kontrolltilfeller beholdes; tre tester og 17 byteidentiske
replayfiler består. Originalpiloten er fortsatt feilet. Totalt 3 674 krav
lukket. Ingen ny scoring eller trening.

**Tidligere datagapstatus:** **11 234 åpne krav**, **66 477 inputkomplette
spillerkamper og 824 hele kamper**. [To taklingsfelt](research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/tackle_subset_bounds/README.md)
er utfylt fra en godkjent nulltotal; én ny spillerkamp blir komplett. Tre
tester og 15 byteidentiske replayfiler består. Totalt 3 659 krav er lukket.
Ingen ny scoring; alle tidligere data og assist-/rettelsespekere bevares.

**Tidligere datagapleveranse – 9. oktober 2026:** **11 236 åpne feltkrav i 10 804 spillerkamper**. **66 476 spillerkamper og 824 hele kamper** har komplette input. [Siste assistinventar](research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/espn_last_inventory/README.md) er avklart med én ny kamprespons og den uendrede kvalifiserte parseren. Ett assistkrav lukkes; 14 får komplette mål, men forblir åpne med ukjente bidrag. Det gjenstår **ingen assistinventargap**, men **9 270 assistkrav** er uløste. Fem tester og 24 byteidentiske replayfiler består. Totalt **3 657 feltkrav er lukket** siden omprioriteringen. Datagap først; samlet kvalitet og ny poengversjon følger senere.

**Gjeldende prioritet etter brukerens omdefinering:** lukk datagapene så
effektivt og raskt som mulig → kvalitetssikre samlet datagrunnlag → omregn
og bygg poengetiketter → ferdigstill fristsikre treningsvisninger.
Fremdrift måles først i faktisk lukkede feltkrav. Se arbeidsrekkefølgen under.
Den [operative målbeskrivelsen](docs/DATA_GAP_GOAL.md) angir leveransen
for datagapfasen og når neste fase kan tas opp.
Kilderuter får korte innledende tidsrammer, og små utfyllinger samles i
batcher. Arbeid uten konkrete utfyllingskandidater skal bytte rute;
faktiske feltlukkinger og tidsbruk rapporteres sammen.
En egen [innhentingskø](research/current/scoring_2026_27/bulk_reconciliation/priority/ACQUISITION_CURRENT.json)
skiller **1 949 data-/kildekrav** fra **9 270 assistkrav merket
regelomregning**. Alle 11 219 åpne krav beholdes. Innhent også manglende
hendelsesbevis for assists nå; nye regelberegninger følger senere.

- [Gjeldende restliste og reproduksjon](research/current/scoring_2026_27/bulk_reconciliation/README.md)
- [Prioritert arbeidsrekkefølge](research/current/scoring_2026_27/bulk_reconciliation/WORK_ORDER.md)
- [Maskinlesbar status og filpekere](research/current/scoring_2026_27/bulk_reconciliation/CURRENT.json)

- [Tidligere datakontroll for 2025/26 (historisk)](research/current/rescoring_2025/README.md)

- [Status og neste steg](docs/STATUS.md)
- [Kampjustering, H3/H5/H8 og adaptive chips: 84 nye forløp](research/current/fixture_strategy/README.md)
- [Første kalenderforsøk: +35,5 poeng med chips mot benchmark](research/current/calendar_counts/README.md) og [datakvalitet](research/current/calendar_audit/README.md)
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
