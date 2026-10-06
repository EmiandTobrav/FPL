# Kalenderforsøk1: antall kommende kamper

Fullført6. oktober 2026. **+35,5 poeng per sesong med chips og +45,5 uten chips mot `constant_h3`.** Kandidaten er lovende, men primærgevinsten er ujevn og dagens benchmark beholdes.

## Hva er endret?

For de to fremtidige rundene i H3-planen multipliseres benchmarkens eksisterende prognose med antall lagkamper registrert for runden i siste før-cutoff-kalender. En kjent blank gir 0; en kjent dobbel gir 2. En ufordelt kamp legges ikke i en senere runde etter fasit. Kalender eldre enn14 dager gir uendret benchmarkprognose. Terskelen ble låst etter dekningsrevisjonen, før kandidatens sesongresultater.

Aktuell rundeprognose, lærte modellvekter, retrening, shortlist, optimizer, priser, overlevering og chipkalender er identiske. Motstander og hjemme/borte i fremtidige runder er ikke forbedret i dette forsøket. Poeng per kamp er fortsatt en proxy, og to kamper betyr ikke at spilleren faktisk får dobbelt så mange minutter.

Protokoll og kode ble låst lokalt før kjøring. GitHub-lagring ble forsinket av godkjenningskontrollen, så første kodecommit kom mens simuleringene kjørte; det hevdes ikke ekstern forhåndsregistrering før kjøring.

## Resultater

| Regime | Benchmark | Kalenderkandidat | Gevinst | Seire/uavgjort/tap | Beskrivende95 % intervall |
|---|---:|---:|---:|---:|---|
| Med fast chipkalender | 2308,25 | **2343,75** | **+35,50** | 2/1/1 | [−14,75; +107,25] |
| Uten chips | 2172,75 | **2218,25** | **+45,50** | 3/1/0 | [+7,00; +94,25] |

| Sesong | Kalenderpoeng med chips | Gevinst med chips | Gevinst uten chips |
|---|---:|---:|---:|
| 2022/23 | 2305 | −29 | +14 |
| 2023/24 | 2314 | +143 | +121 |
| 2024/25 | 2518 | +28 | +47 |
| 2025/26 | 2238 | 0 | 0 |

Med chips faller treffkostnaden fra 25 til 18 og bruttopoengene øker 28,5: samlet +35,5. Antall bytter faller fra 77,5 til 75,5. Uten chips faller treffkostnaden fra 26 til 22, bruttopoengene øker 41,5 og antall bytter faller fra 40,5 til 39,5. Dette er regnskapsdekomponering, ikke isolerte årsakseffekter.

2023/24 står for mye av gevinsten. 2025/26 hadde arkiv≤14 dager i bare 8 av 34 runder, og bare GW30 fikk endrede fremtidsprognoser. Disse endringene ga ingen endrede beslutninger. Nullresultatet er derfor ikke en sterk test av full kalenderinformasjon i den sesongen.

## Datakvalitet og tolkning

[Kalenderrevisjonen](../calendar_audit/README.md) dokumenterer82 arkiver, tidsstempler, dekningshull og forskjeller mot sluttkalenderen. Kalenderen kan mangle annonseringer mellom arkivtid og frist selv om den er yngre enn14 dager.

Aktuelle rundeprognoser og frister beholder benchmarkens historiske begrensninger. Resultatet er en kontrollert forbedring innen eksisterende simulator, ikke dokumentasjon på en fullstendig tidsriktig live-FPL-backtest. De fire sesongene er brukt i tidligere modellvalg. Bootstrap bruker 50000 parete sesongresamplinger med seed 173, er beskrivende og korrigerer ikke for alle tidligere forsøk.

**Beslutning:** behold `constant_h3` som avtalt arbeidsbenchmark og registrer `calendar_count_h3` som ny kalenderutfordrer. Ingen terskel eller chipdato tilpasses disse resultatene. Neste steg bør forbedre arkivdekningen, særlig 2025/26, og deretter teste motstander/hjemme-borte per faktisk planlagt kamp i en separat ablasjon. Full rekonstruksjon av faktiske frister og aktuell kalender krever en ny felles baseline.

## Kontroller og reproduksjon

16 nye sesongforløp / 544 beslutninger. Alle 8 benchmarkforløp gjenskaper lag, startellever, benk, kaptein, visekaptein og poeng nøyaktig. Alle aktuelle prognoser er identiske, og gamle snapshots gir nøyaktig fallback. Oppgjør, posisjoner, klubbgrenser, bank og FT består kontrollene. Alle solvere har optimal status innen toleransen, største gap 9,56×10⁻⁶.

To nye tester for kalenderutvalg/dobbel/blank/fallback og tre eksisterende planlegger-/prognosetester består ved direkte kjøring. Ingen full pytest-suite eller GitHub CI-verifikasjon hevdes. Se `results/environment.json`.

Fra repositoryroten:

```bash
python scripts/prepare_data.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/calendar_counts/build.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/calendar_counts/run.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/calendar_counts/summarize.py
```

Kalendere og simuleringsspor ligger lesbart i `portable`; klargjøringen gjenoppretter filformatene som koden forventer. Prognosefilene regenereres av `build.py` fra de arkiverte benchmarkprognosene og kalenderne, og kontrolleres mot kjøringens hashmanifest. Dermed unngås opplasting av ugjennomsiktige komprimerte nye filer.
