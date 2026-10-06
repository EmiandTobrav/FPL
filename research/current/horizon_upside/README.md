# Fire-runders planlegging og dekomponert poengforventning

Forsøk 6. oktober 2026. Vi tester om en lengre beslutningshorisont forbedrer sesongpoeng, og om oppside gir ytterligere gevinst når hele poengforventningen beholdes. [Protokollen](protocol.json) ble låst før modelltrening og sesongresultater; ingen parameterleting på resultatene.

## Modeller og matchet design

Tre prognosemodeller testes i begge horisonter:

- **Referanse:** eksisterende 50/50 Ridge + Extra Trees.
- **HGB:** eksisterende direkte regresjon på alle poeng.
- **Dekomponert modell:** HGB-klassifikator for `P(Y>=8)` og separate HGB-regresjoner for `E[Y|Y>=8]` og `E[Y|Y<8]`. Poengforventningen beregnes som `p*high + (1-p)*low`, klippet til minst null per kamp. Ordinære prestasjoner teller fullt; modellen gir ingen vilkårlig ekstra oppsidebonus.

Alle bruker samme BASE+FX og trener bare på eldre sesonger med utfall tilgjengelige før første frist. Ingen ny minuttmodell eller eksterne data innføres. De nye klassifikatorprognosene er ikke separat kalibrert på en holdout. Det er den beregnede totalforventningen som brukes i lagvalget; klassifikatorens sannsynligheter er ikke dokumentert som kalibrerte.

Seks sesonger 2020/21–2025/26 × tre modeller × horisont 1/4 × to chipregimer = **72 nye sesongforløp**. Hver får samme faktiske overlevering etter GW4. Vi rapporterer horisonteffekt innen hver prognosemodell, dekomponert modell mot HGB ved hver horisont og samspillet mellom modell og horisont. Sterk én-rundes referanse og tidligere arkiverte resultater rapporteres separat.

## Hva fremtidsprognosene vet

Dataene inneholder endelig historisk kamptildeling, ikke før-frist-snapshots for alle senere runder. Vi bruker derfor **ikke** fremtidige `games_*.pkl`-rader, fremtidige utfall, fremtidige priser, oppdaterte formvariabler eller senere kampflyttinger i planleggingen.

Aktuell runde bruker samme eksisterende kalenderproxy som tidligere. For hver senere runde antar vi én kamp og gradvis tilbakevending fra aktuell poengprognose per kamp mot et nøytralt motstandernivå: `neutral + (current_per_fixture-neutral)*0.5**k`. Aktuell blankrunde bruker nøytral prognose som startnivå. En aktuell dobbelrunde dobles ikke inn i fremtiden. Nøytral prognose bruker hjemmestatus 0,5 og gjennomsnittlig lagstyrke/forsvar fra tilgjengelig laghistorikk blant klubbene i dagens spillerpool. Alle andre spillerfeatures og priser fryses ved dagens frist.

Dette er en **test av planlegging under et nøytralt fremtidsscenario**, ikke en full kampkalenderbasert test. Den kan ikke avgjøre om oppside fungerer med gode prognoser for konkrete kommende motstandere, blankrunder og dobbeltrunder.

## Planlegger og avgrensninger

En heltallsmodell velger egen tropp, startellever, kaptein, kjøp, salg, bank og gratisbytter i hver planlagte runde. Målet er summen av forventede start-/kapteinspoeng og 0,1 benkvekt, minus fire poeng per betalt bytte og 0,5 friksjon per ordinært bytte. Bare første rundes handling utføres; ved neste frist beregnes planen på nytt med da tilgjengelige data.

Bank og salg av opprinnelige beholdninger bruker faktisk arvet kjøpspris og dagens laggede markedspris. Senere planlagte kjøp/salg bruker samme fryste pris. En spiller kan ikke kjøpes eller selges mer enn én gang i samme plan, og spillere eid ved fristen kan ikke selges og gjenkjøpes innen planen. Dette forenkler prisregnskapet og begrenser raske rundturer. Det påvirker ikke muligheten til å gjenkjøpe etter neste replanlegging.

Gratisbytter følger den eksisterende fem-bytte-regelen med eksakte overgangsvalg, inkludert treff og opptjening. Moderne bytte-/chipregler anvendes på historiske poeng som i tidligere forsøk. Den faste chipkalenderen beholdes. Horisonten forkortes før en fremtidig wildcard/free hit og ved sesongslutt; en aktuell free hit bruker én runde. Planlagte BB/TC innen horisonten regnes med. Ingen terminalverdi for ubrukte gratisbytter eller bank legges til.

Begge horisonter bruker samme metode for kandidatutvalg: union av toppspillere etter aktuell prognose og fire-runders gjennomsnitt, billige spillere, verdi og alle nåværende beholdninger. Dette er bredere enn den gamle én-rundes listen. Gamle referanser gjengis separat slik at utvalg-/solverforskjeller ikke fremstilles som en ren horisonteffekt. Troppsgrenser og posisjoner er uendret. Optimalitet gjelder kandidatlisten, ikke alle mulige FPL-spillere.

Solverbudsjett er fem sekunder per beslutning og relativt gap 0,001. Status 0 betyr at solverens toleranse er nådd, ikke nødvendigvis et eksakt null-gap. Vi lagrer status og gap for hver beslutning. Resterende gap må vurderes før små poengforskjeller tillegges betydning.

## Resultater

**Positiv delgevinst, men ingen ny totalvinner:** Den dekomponerte modellen forbedrer vanlig HGB ved én-rundesplanlegging. Den slår ikke den sterke Ridge/Extra Trees-referansen, og fire-rundersplanlegging svekker den dekomponerte modellen i dette nøytrale fremtidsscenarioet. Ingen produksjonsendring.

### Gjennomsnittlig nettosesongpoeng

| Modell | Uten chips, H1 | Uten chips, H4 | Fast chipkalender, H1 | Fast chipkalender, H4 |
|---|---:|---:|---:|---:|
| Ridge/Extra Trees | 2159,7 | 2137,7 | 2216,5 | 2241,8 |
| Vanlig HGB | 2083,8 | 2121,2 | 2125,5 | 2160,8 |
| Dekomponert modell | 2113,8 | 2081,2 | 2198,0 | 2145,7 |

| Paret effekt | Uten chips | Fast chipkalender |
|---|---:|---:|
| Fire mot én runde, Ridge/Extra Trees | −22,0 | +25,3 |
| Fire mot én runde, vanlig HGB | +37,3 | +35,3 |
| Fire mot én runde, dekomponert modell | −32,7 | −52,3 |
| Dekomponert mot HGB ved én runde | **+30,0** | **+72,5** |
| Dekomponert mot HGB ved fire runder | −40,0 | −15,2 |

Den dekomponerte modellen vinner mot vanlig HGB i 3/6 sesonger uten chips og 5/6 med chips ved én-rundesplanlegging. Sesongevinsten varierer fra −125 til +156 uten chips, og −35 til +225 med chips. Beskrivende 95 %-bootstrapintervaller er [−68,2; 120,2] og [9,2; 148,0]. Det siste intervallet ligger over null, men forsøket er retrospektivt, flere sammenligninger er gjort, og intervallet korrigerer ikke for modellleting. Dette er en lovende sammenligning mot HGB, ikke et bevis på generell overlegenhet.

Mot sterk én-rundesreferanse taper dekomponert H1 fortsatt −45,8/−18,5 poeng. Ved H4 taper den −56,5/−96,2 mot sterk H4-referanse. Vi har derfor funnet en måte å bruke oppside som forbedrer en svakere modell i denne testen, men ikke en måte som gir høyere sesonggevinst enn prosjektets beste etablerte referanse.

Fire-runders Ridge/Extra Trees er høyest med fast chipkalender, +25,3 mot matchet H1, men vinner bare i 4/6 sesonger og har intervall [−9,3; 58,8]. Uten chips taper den −22,0. Vanlig HGB forbedres av H4 i 5/6 og 4/6 sesonger, men taper fortsatt mot sterk H1. Dette er ikke tilstrekkelig grunnlag for en generell overgang til H4.

### Hva som faktisk endret seg

Den dekomponerte modellen lærer sannsynlighet og betingede poengnivåer med tre estimatorer. Sammenligningen mot én direkte HGB tester hele modellkonstruksjonen, inkludert ulik kapasitet; den isolerer ikke ny ekstern informasjon eller én enkel oppsidevariabel.

Lengre planlegging påvirker faktiske bytter. Vanlig HGBs gjennomsnittlige treffkostnad stiger fra 32,0 til 53,3 uten chips og fra 30,7 til 46,7 med chips. Den dekomponerte modellen stiger fra 24,7 til 45,3 og fra 30,0 til 33,3. En lengre horisont gir dermed ikke automatisk færre eller bedre bytter. Planene inneholder fremtidige bytter i 1004 av 1224 H4-beslutninger; dette er reell flertrinns planlegging, ikke bare et ekstra beholdningspåslag.

Det er ingen støtte her for et positivt samspill mellom dekomponering og H4: endringen i horisonteffekt relativt til HGB er −70,0 uten chips og −87,7 med chips. Dette gjelder den faste nøytrale prognosemetoden, og kan ikke overføres direkte til en god, konkret kampkalenderbasert planlegger.

### Referanser, solver og usikkerhet

Den opprinnelige arkiverte referansen har 2155,7/2216,3 poeng, mens ny matchet H1 har 2159,7/2216,5. H4-referansen er dermed −18,0/+25,5 mot arkivet. Forskjellen mellom gammel og ny H1 skyldes det nye kandidat-/solveroppsettet; den inkluderes ikke i den rene horisonteffekten.

Alle 2448 beslutninger har gjennomførbare løsninger og bestått poeng-/bankkontroll. **287 av 1224 H4-beslutninger** når tidsgrensen før ønsket gap er oppnådd; alle H1-beslutninger når toleransen. Største relative gap er **1,552 %**. Det er gap i den planlagte forventningsverdien, ikke en feilmargin for faktisk sesongpoeng. H4-resultatene dokumenterer derfor denne tidsbegrensede planleggeren, ikke et bevist optimalt fire-rundersresultat. CPU-/tidsgrense kan gi andre gyldige planer ved omkjøring. Små gevinster bør ikke brukes til produksjonsvalg uten en strammere solverkontroll.

Gjennomsnittlig H4-plan er 3,43 runder fordi horisonten forkortes ved chips og sesongslutt. Ingen parameter ble justert etter sesongresultatene. En JSON-lagringsfeil ble rettet, testet og hele gyldige forsøket kjørt på nytt med uendrede modellinnstillinger.

**Videre prioritet:** Behold dekomponert H1 som en forskningskandidat, men behold sterk referanse som benchmark. Før ytterligere flerukers tuning bør vi skaffe historiske før-frist-kalendere og bedre minutter-/tilgjengelighetsprognoser. En eventuell blanding av dekomponert modell og sterk referanse må testes tidsordnet; den er ikke testet i dette forsøket. Ingen positive resultater her tilsier at en slik blanding nødvendigvis vil vinne.

[Sesongresultater](results/season_results.csv), [modellgjennomsnitt](results/model_summary.csv), [parete effekter og intervaller](results/paired_summary.csv), [sesongvise differanser](results/paired_seasons.csv) og [kontroller](results/checks.json).

## Reproduksjon

Fra repositoryroten etter rot-README-miljøoppsett og `python scripts/prepare_data.py`:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/horizon_upside/run.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/horizon_upside/summarize.py
```

Lagrede prognoser og spor gjenbrukes. En ny identisk simulering kan kjøres ved å slette bare `horizon_upside/results/trace_*.json.gz` i en separat arbeidskopi. Full retrening bruker `build.py` først. Endret kildekode eller input krever ny forsøkskopi uten gamle spor/`run_manifest.json`; ikke bland nye modeller med gammel cache.

`features.py` inneholder nøytral fremtidskonstruksjon og totalforventningsformelen. `build.py` trener; `planner.py` løser flerrundeproblemet; `run.py` utfører første handling og gjør faktisk poengoppgjør; `summarize.py` kontrollerer og sammenligner. Prognoser, tidsgrenser, 72 spor med fremtidige planer, solverdiagnostikk og parete resultater ligger i `results/`.

Alle evalueringssesonger er tidligere studert. Ingen urørt holdout eller faktisk historisk rank påstås. Parete bootstrapintervaller bruker 50 000 resamplinger av seks sesongpar, uten korreksjon for tidligere modellleting. Begrensninger i priser, registreringer, skadehistorikk og aktuell kampkalender arves fra hovedforsøket. En eventuell gevinst skal ikke automatisk erstatte referansen uten videre vurdering.

168 tester bestått lokalt på den ferdige koden, inkludert kontroller av nøytral fremtid ved blank-/dobbelrunde, forventningsformelen, horisontgrenser, FT-tak, utsatt kjøp, treff, salgspris og lagring av planer. GitHub CI-status er ikke verifisert.
