# Tre eksempler på utvikling, evaluering og beslutningsstøtte

[Startside](../README.md) · [Arbeidsmetodikk](AI_WORKFLOW.md) · [Alle utvalgte resultater](RESULTS_INDEX.md)

Eksemplene viser hvordan et problem avgrenses og hvordan resultatet påvirker beslutningen. Agentene implementerte kode og analyser; prosjekteierens rolle er mål, krav, koordinering og vurdering. Originalrapportene er autoritative for tall og forsøksbetingelser. Ingen av eksemplene dokumenterer generell overlegenhet på nye sesonger.

## 1. Modellutvikling: gir kampkontekst bedre poengprognoser?

**Problem:** En spiller kan ha null, én eller flere kamper i en FPL-runde. Kan en rekonstruert kalender og historisk lag-/motstanderstyrke forbedre poengprognosen uten å endre spilletidsmodellen?

**Avgrensning:** Behold minuttprognoser og kategorisannsynligheter nøyaktig uendret. Sammenlign seks spor på de samme 29 144 evaluerbare radene i 2025/26, inkludert 2 070 faste kandidatrader. Kandidatlisten er valgt før utfall; den endres ikke for å passe nye prognoser. Forsøket gjennomførte 228 poengtilpasninger, ingen minuttmodelltilpasninger og ingen etterfølgende kandidatbytte.

**Resultat:** MSE (gjennomsnittlig kvadratfeil; lavere er bedre) gikk fra **3,662726 til 3,603974**, en reduksjon på **1,604 %**. Blant lagkandidatene gikk MSE fra **13,375402 til 12,935643**, en reduksjon på **3,288 %**.

**Kvalitetssikring:** Rapporten dokumenterer kontroll av 1 036 inputhasher, 38 tidsfrister og identiske treningsnøkler. Kontrollsporet gjenskapte de beholdte prognosene uten avvik. Separate sammenligninger skilte kalenderreparasjon, videreføring av kalenderinformasjon og styrkefelter.

**Beslutning og læring:** Behold som forskningskandidat. Bedre prognosefeil er ikke automatisk bedre lagvalg. Perioden var allerede undersøkt, historisk informasjon bruker tidsproxyer, og blokkintervallene er beskrivende uten korreksjon for mange sammenligninger. Full gjentakelse krever lokalt input- og kodearkiv; GitHub inneholder [original rapportkopi](evidence/2026-10-16/point_context.md) med [kildehash](evidence/2026-10-16/MANIFEST.json).

## 2. Beslutningsstøtte: lære når spesialfordeler bør spares

**Problem:** Gode spillerprognoser avgjør ikke alene når det lønner seg å bruke en chip. Triple Captain øker kapteinens poeng, mens Bench Boost lar benken bidra. Kan en liten lært komponent støtte disse valgene?

**Avgrensning:** To Ridge-modeller lærer verdien av å spare disse fordelene fra tidligere sesonger. Prognoser, regelmotor, startregler og planlegger beholdes. Modell og skalering fryses før evalueringssesongen. Dette er en avgrenset komponent, ikke en full manager lært med reinforcement learning.

| Sesong | Benchmark | Lært policy | Forskjell i netto poeng |
|---|---:|---:|---:|
| 2022/23, kontroll uten læring | 2 429 | 2 429 | 0 |
| 2023/24, lært evaluering | 2 413 | 2 466 | +53 |
| 2024/25, lært evaluering | 2 344 | 2 385 | +41 |

**Resultat:** **+47 netto poeng i sesongsnitt** over de to lærte evalueringssesongene. Kontrollåret uten læring er ikke medregnet som bevis for læring.

**Kvalitetssikring:** Den opprinnelige etterkontrollen beregnet 228 oppgjør og tilstandsoverganger på nytt og gjenskapte alle 114 referanserunder. Uendrede prognoser og tidsriktig trening ble kontrollert. En mekanisk oppsummeringsfeil og den eksplisitte rettingen er bevart.

**Beslutning og læring:** Pilotkravet bestått; benchmark beholdt inntil separat vurdering. Bare to allerede undersøkte sesonger tester læring. Flere treningsrader deler samme chiputfall. Gevinsten inkluderer senere endringer i tropp og bytter og kan ikke tilskrives chipbonus alene.

Les [resultat og begrensninger](../reports/learned_manager_2026_10_15/RESULTATER.md), [protokoll](../reports/learned_manager_2026_10_15/protocol.json) og [lagret etterkontroll](../reports/learned_manager_2026_10_15/audit.json). Publiserte bevis kan hashkontrolleres; full simulatorreplay krever lokale input.

## 3. Forkastet forsøk: mer omfattende læring ga dårligere valg

**Problem:** Kan sesonglang læring forbedre hele handlingsrangeringen — bytter, kaptein, benk og alle chips — utover den lille chip-policyen?

**Avgrensning:** Lær en rangering av lovlige handlingsforslag med uendrede prognoser. Inkluder både benchmark, chip-policyen og en kontroll med **samme forslagsregler uten læring**. Den siste kontrollen undersøker om læringen tilfører noe utover endret handlingsutvalg.

| Sesong | Benchmark | Samme forslag uten læring | Episodisk lært manager |
|---|---:|---:|---:|
| 2023/24 | 2 413 | 2 391 | 1 838 |
| 2024/25 | 2 344 | 2 475 | 2 433 |

**Resultat:** **−243 poeng i sesongsnitt mot benchmark**, og **−297,5 mot samme forslagsregler uten læring**. Selv i året kandidaten slo benchmark, tapte den mot kontrollen uten læring.

**Kvalitetssikring:** Den opprinnelige etterkontrollen omfattet 304 nye trenings-/evalueringsrunder, lagrede forslag, oppgjør, tidsgrenser, modelltilpasninger og ressursbruk. Forslag og valg ble lagret før utfall ble lest. Kontrollen gjenbrukte regelmotoren og var ikke en ekstern regelvalidering.

**Beslutning og læring:** Forkast kandidatversjonen som oppgradering. En mer omfattende modell er ikke nødvendigvis en bedre løsning. Den ekstra kontrollen hindret at et positivt enkeltår ble tolket som bevis for nytten av læring. Gjentatte forløp gjennom samme historiske sesong er heller ikke nye uavhengige sesonger.

Les [originalrapport](../reports/season_manager_2026_10_15/RESULTATER.md), [protokoll](../reports/season_manager_2026_10_15/protocol.json) og [begrensninger](../reports/season_manager_2026_10_15/BEGRENSNINGER.md). Kode, modeller og komprimerte beslutningsbevis er publisert; full gjentakelse krever lokalt inputarkiv.
