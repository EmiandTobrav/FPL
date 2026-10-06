# Posisjonsspesialisering mot constant_h3

Forsøksrunde 6. oktober 2026. Sesongsimuleringene pågår. Protokoll og kode ble lagt i GitHub før simuleringene: `2bf91eff3581a487f998d64c42d5f0f5277fcf70`.

## Avgrensning

Tre kandidater testes mot aktiv benchmark på 2022/23–2025/26:

- `pos_weight_h3`: fire HGB-blandingsvekter, lært på tidligere sesongers ærlige prognoser. Logitvektene regulariseres mot den opprinnelige globale vekten med koeffisient 0,01. Ingen sesongpoeng brukes til å velge vektene.
- `pos_hgb_h3`: fire posisjonsvise HGB-modeller erstatter global rik HGB som ekspert. Den opprinnelige globale sesongvekten mellom HGB og retrent Ridge/Extra beholdes.
- `hybrid_hgb_h3`: HGB-eksperten er en på forhånd fastsatt 50/50-blanding av global og posisjonsvis HGB. Resten er identisk med foregående kandidat.

Dette er tre kontrollerte endringer av benchmarkens prognoser. Posisjons-HGB testes som egen HGB-ekspert i den eksisterende ensemblekonstruksjonen, ikke som en fjerde kandidat med 100 % HGB og uten Ridge/Extra. Vi gjør ikke noe etterfølgende vektsøk.

## Felles betingelser

Samme RICH-variabler, HGB-hyperparametre og retrening ved GW5,9,13,17,21,25,29,33,37. Trening bruker bare utfall med tilgjengelighet før aktuell frist. Posisjonsvektene læres før hver sesongs GW1 på tidligere sesonger; 2020/21 og 2021/22 er de første metatreningssesongene.

Den eksisterende `global_horizon.run.run` brukes direkte med en ny resultatmappe. Samme tre-rundersplanlegger, fremtidsproxy, spillerutvalg, solverbudsjett, faktiske GW4-overlevering, priser og chipkalender. Ingen nye kalender-, skade- eller rolledata. Alle åtte benchmarkforløp kjøres på nytt for å kontrollere eksakt beslutningsparitet.

Primærmål er nettosesongpoeng med arvet fast chipkalender. Uten chips er diagnostikk. 24 kandidatforløp og 8 benchmarkforløp gir 1088 beslutninger etter GW4.

## Begrensninger

Fire tidligere brukte evalueringssesonger er ikke en urørt holdout. Bootstrapintervaller over sesonger er beskrivende og korrigerer ikke for alle tidligere modellforsøk. Fire HGB-modeller har en annen samlet kapasitet og mindre data per modell enn én global HGB; forsøket måler hele konstruksjonen. Fremtidig kampprogram bruker samme nøytrale proxy som benchmarken, og historiske pris-, frist- og tilgjengelighetsproxyer videreføres.

## Reproduksjon

Fra repositoryroten, etter klargjøring av eksisterende data og avhengigheter:

```bash
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/position_specialist/build.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/position_specialist/run.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/position_specialist/summarize.py
```

`run.py` avviser gjenbruk av spor hvis kilder eller input er endret. Treningsrevisjon, vekter, prognoser, spor og filhash lagres i `results`. Ikke endre arkiverte forsøk for å tilpasse dem til denne runden.
