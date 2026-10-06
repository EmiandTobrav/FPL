# Fortsett her

Oppdatert 6. oktober 2026. Brukeren ønsker GitHub som sentral for kode og fremgang på tvers av enheter. Denne mappen og repositoryet skal være tilstrekkelig kontekst uten den gamle samtalen eller ZIP-filene.

## Mål og avklaringer

Maksimer robust FPL-sluttscore etter at hovedmodellen tar over fra startmodellen. Test enkeltmodeller, faste og lærte prognosekombinasjoner, og separate variabler for motstanderens angrep og forsvar. Startmodellens overlevering skal inneholde den faktiske troppen, bank, kjøpspriser og gratisbytter. Ikke tilpass startlaget til et kunstig idealmottakerlag. Startstrategiens delmål ved GW8,12,15,19 beholdes separat.

Kvantifisering av elite-managere var et tidligere spor. Brukeren gikk videre til hovedmodellen; dette er nå hovedprioriteten. Rå elite-eierskapsarkiv er ikke nødvendig for gjeldende eksperiment og er ikke flyttet inn som aktivt datasett.

## Gjeldende referanse

Startmodell: `handoff=4`, `look=3`, `carry=1`, `friction=0.5`, `prior_mix=0`, `chip_reserve=1000`, `scenario=neutral`. Modeller trenes på eldre sesonger; hovedmottakerens optimizer har én-rundes horisont. Alle ti kandidater får samme starttilstand. Friksjon 0,5, benkvekt 0,10. Fast chipkalender: WC6, TC15, FH18, BB19, WC24, FH33, BB36, TC37. Det kjøres også uten chips.

120 ferdige forløp: seks sesonger × ti modeller × to chipregimer, totalt 4080 hovedmodellbeslutninger. Modeller: Ridge, Bayesian Ridge, Extra Trees, HGB med grunnvariabler, HGB med utvidelser, Ridge/Extra Trees 50/50, Ridge/utvidet HGB med HGB-vekt 25/50/75 %, og treveis lik blanding.

50/50 Ridge + Extra Trees ga +37,17 uten chips / +55,67 med fast kalender mot Ridge, med positiv gevinst i 5/6 og 4/6 sesonger. Fritt modellvalg kun ut fra eldre sesonger ga +3,75/+2,25 i fire evalueringssesonger. Beskrivende vinner og tidsordnet modellvalg er ulike sammenligninger. Ingen urørt holdout gjenstår i disse dataene. Ingen produksjonsmodell er automatisk byttet.

Utvidet HGB mot enkel HGB ga +15,17 poeng uten chips og −6,50 med chips. Det er en samlet featurepakke, ikke en isolert xG-effekt. Eget lags/motstanderens mål for/mot, Elo og lagget xG finnes; `starts_m6` er en 60+-minuttersproxy. Enkle målrateprodukter og `exp(-lambda_against)` er ikke en kalibrert Dixon–Coles-modell.

## Hva som ble gjort ved GitHub-integrasjonen

- Mai-repositoryet gjennomgått og bevart; nytt arbeid integrert under `research/current`.
- Hele aktive forsøket med rådata, startinnganger, prognoser, 120 beslutningsspor og resultattabeller flyttet inn.
- Individuelle gzip-innganger med SHA-256 og automatisk klargjøring erstatter manuell ZIP-utpakking.
- Residualideen implementert som opt-in HGB-kandidat og kjørt som separat prediksjonstest. RMSE bedret seg bare i 1/6 sesonger mot direkte HGB; ingen ny sluttscore påstås.
- Eldre API-/feature-/ensemblekode beholdt. Metodeproblemene er dokumentert i REPOSITORY_REVIEW, ikke skjult ved å overskrive gamle resultater.

## Prioritert neste arbeid

1. Hold prognosene fast og test hovedmodellens flerukers byttehorisont mot samme én-rundes referanse. Bruk bare kalender/prognoser som var tilgjengelige ved beslutningen; ikke les fremtidige `games_*.pkl`-rader som om de var kjent.
2. Isoler angrep, forsvar og xG som egne ablasjoner, med uendret spillerpool og optimizer.
3. Test residual-CatBoost/XGBoost og faste/innlærte blandinger på dagens felles spillerpool dersom begrenset modellbudsjett tillater det. Nåværende residual-HGB-pilot gir ingen klar gevinst.
4. Bygg og kalibrer en reell minuttmodell; skill fra shrinkage av allerede minuttavhengige poeng.
5. Bruk bevart FPL API-kode til prospektive før-frist-snapshots for pris, tilgjengelighet, tropp og kalender. Da kan en ny holdout opprettes.

Ikke velg vekter på evalueringssesongens fasit. Endre én gruppe parametere om gangen og foretrekk stabile områder. Rapporter nettosesongpoeng, treffkostnad, usikkerhet og sesongvise forskjeller, i tillegg til MAE/RMSE.

## Reproduksjon og begrensninger

Se rot-README. `prepare_data.py` må kjøres før forsøkene på ny maskin. Prognosebygging bruker lokale rådata. Modellkandidater og dataendringer skal ha separate protokoller/resultater; gammel trace-cache må ikke brukes ved endringer.

Historiske poeng, moderne chips/FT-regler; priser er laggede proxyer; skader og spilleravganger er ufullstendige; endelig historisk kamptildeling i aktuell GW antas kjent ved frist. Dette er forskningssimulering, ikke dokumentert faktisk rank eller topp-prosent-sannsynlighet. De gamle Parquet-LFS-filene er ikke nødvendige for det aktive forsøket.

## Siste verifikasjon

156 tester bestått etter klargjøring (152 eksisterende funksjonstester, reparert mappestrukturtest og tre nye forskningstester). 367 deprecation/future-advarsler fra eldre pandas-kode; ingen testfeil. De 47 pakkede inngangene er kontrollert mot både lagret og gjenopprettet SHA-256. Residualpiloten er gjennomført for alle seks sesonger. GitHub Actions er konfigurert for samme testkommando; lokal teststatus er ikke det samme som bekreftet CI-status.
