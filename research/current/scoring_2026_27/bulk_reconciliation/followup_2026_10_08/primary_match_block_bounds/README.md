# Mållinjeklareringer fra kvalifiserte nullblokker per spillerkamp

Denne ferdigstilte datagapbatchen lukker **27 krav**, fra **11 215 til 11 188**.
Åtte utfyllinger gjelder 2019/20 kamp 135, ni gjelder 2020/21 kamp 104 og ti
2020/21 kamp 108. Alle verdiene er null. **17 mållinjekrav gjenstår**.
66 478 spillerkamper og 824 hele kamper er inputkomplette; ingen nye rader
eller hele kamper blir komplette fordi andre krav fortsatt er åpne.

## Kilde og avgrensning

Vi gjenbruker de 685 kodemappede spillerresponsene fra den allerede
kvalifiserte [primærinnhentingen](../primary_gap_recovery/README.md).
Ingen nye nettsvar hentes. Utvalget omfatter eksplisitt null i
`outfielder_block`, eller null med opprinnelig full aktiv spillerliste,
eksakt avstemming mot en uttrykkelig lagkamptotal og ikke-negative heltall.
Kildeminutter, kamp-/spilleridentiteter og kildekvalifikasjon gjenbrukes.
Brukte nullblokktellere avstemmes på nytt mot rå spillerverdier og direkte lagtotaler.
De to gamle frysavhengighetene for en annen GL-sesongregel/ledger inngår ikke
i avledningen av `outfielder_block`; de endres ikke. Øvrige relevante originale
kildehashverdier verifiseres og alle brukte filer versjonsfestes.

Hele kampens mållinjeklareringer er en ikke-negativ delmengde av utespillerens
skuddblokker. Null skuddblokker gir derfor null mållinjeklareringer. Utelatelser
blir aldri null uten den opprinnelige eksakte lagavstemmingen. Keepere er
utelatt; keepernes blokkteller kan ikke antas å dekke mållinjeklareringer.
Positive/manglende blokktall, beskyttede konflikter og andre minuttruter gir
ingen utfylling. Den gamle mislykkede 2020/21-spillersesongavstemmingen på én
blokkering beholdes uendret og brukes ikke i denne direkte kampregelen.

## Fryste kontroller og bevaring

498 primærprediksjoner over 24 kamper er fryst før mållinjeutfall sammenlignes.
Tidligere kvalifiserte null-sesongprediksjoner gjenbrukes som regresjon;
overlapp fjernes med den direkte primærgruppen først. Før sammenligning er
minst 1 000 samlede kontroller, 100 direkte primærkontroller i 20 kamper og
null feil/positive arkivmotsetninger krevd. Alle gater består:
**1 975 kontroller i 398 kamper**, inkludert **471 direkte kontroller i 24
kamper**, null avvik og null positive arkivmotsetninger. De tidligere 344
komponentkontrollene i primærkvalifikasjonen har fortsatt null feil.
Kontrollene deler kildeopphav og tidligere sett bevis; dette er regresjon og
kildekompatibilitet, ikke uavhengig holdout eller samlet kvalitetsgodkjenning.

**775 221 øvrige ledger-rader er identiske**, og alle opprinnelige kilde- og
tidligere-verdi-kolonner er bevart for alle 775 248 rader. Native FPL,
assists, native rettelser, keeper-CBI-avklaringen og gamle poengversjoner
bevares. Ny kvalitetsstatus krever fortsatt senere kollektiv kontroll.
Ingen BPS, bonus, poeng, features eller trening bygges i denne batchen.

## Reproduksjon

Fra denne mappen, med prosjektets Python-miljø og pandas:

```bash
python -m unittest -v test_bounds.py
python reproduce.py
```

Tre tester kontrollerer at et positivt lagresidual ikke kan bli null, at et
kjent positivt mållinjeavvik sperrer anvendelsen, og at keepere og beskyttede
konflikter bevares. Isolert offline-replay gjenskaper **16 filer byteidentisk**.
Det krever bare de versjonerte kildefilene; ingen nettinnhenting/parquet.
[Protokoll](plan.json), [prediksjonsfrys](prediction_freeze.json),
[kildeavhengigheter](dependencies.json), [resultat](results/findings.json) og
[replaybevis](replay_report.json) dokumenterer leveransen. Gjeldende ledger
velges gjennom [CURRENT.json](../../CURRENT.json).
