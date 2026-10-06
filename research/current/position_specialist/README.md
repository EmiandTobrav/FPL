# Posisjonsspesialisering mot constant_h3

Forsøksrunde 6. oktober 2026. **Fullført: ingen kandidat slår aktiv benchmark på primærmålet med chips.** Protokoll og kode ble lagt i GitHub før simuleringene: `2bf91eff3581a487f998d64c42d5f0f5277fcf70`.

## Resultater

Gjennomsnitt over de samme fire sesongene; gevinst er kandidat minus `constant_h3`.

| Modell | Poeng med chips | Gevinst med chips | Seire med chips | Poeng uten chips | Gevinst uten chips |
|---|---:|---:|---:|---:|---:|
| Benchmark `constant_h3` | 2308,25 | 0 | — | 2172,75 | 0 |
| Posisjonsvekter | 2265,75 | −42,50 | 0/4 | 2162,25 | −10,50 |
| Posisjons-HGB | 2224,75 | −83,50 | 0/4 | 2134,50 | −38,25 |
| Global/posisjons-HGB 50/50 | 2305,25 | −3,00 | 2/4 | 2226,00 | +53,25 |

Sesongvise gevinster med chips:

| Sesong | Posisjonsvekter | Posisjons-HGB | Hybrid |
|---|---:|---:|---:|
| 2022/23 | −7 | −102 | +28 |
| 2023/24 | −66 | −11 | +90 |
| 2024/25 | −92 | −65 | −19 |
| 2025/26 | −5 | −156 | −111 |

Hybridens beskrivende 95 % bootstrapintervall er **[−76,25; +62,75]** med chips. Uten chips er sesonggevinstene **−11, +172, +32, +20**, med intervall **[−0,25; +134,00]**. Den store gevinsten i 2023/24 trekker opp gjennomsnittet. Dette er ikke dokumentasjon på stabil overlegenhet uten chips.

Posisjonsvekter har intervall [−79,00; −6,00] med chips; posisjons-HGB [−133,25; −33,75]. Begge taper i alle fire sesonger. Fullstendige sekundærtall finnes i [modellsammendraget](results/model_summary.csv).

## Hva lærte vi?

Dagens globale modell bruker allerede posisjonsindikatorer, pris × posisjon og posisjonsavhengige interaksjoner med hjemmebane, Elo, motstanderforsvar og eget angrep. Separate modeller tilfører derfor ikke en helt ny posisjonsinformasjon. De endrer hvordan informasjon deles og reduserer datagrunnlaget per modell. Vi har ikke isolert hvor mye av tapet som skyldes dette kontra modellkapasitet eller regulering.

Posisjonsvektene gir litt bedre MSE for keepere, forsvarere og midtbanespillere, men taper likevel sesongpoeng. Hybridens topp-10-utbytte per posisjon endres med henholdsvis −0,0145, −0,0168, −0,0684 og +0,0084 poeng for GK/DEF/MID/FWD. Disse små, blandede forskjellene understreker at feil på hele spillerutvalget og sesonggevinst må vurderes separat. Diagnostikken er likt vektet over runder innen sesong og deretter over sesonger; den måler ikke faktisk kjøpte spillere alene.

Hybridens gjennomsnittlige treffkostnad faller fra 25 til 22 med chips, men bruttopoengene faller 6: netto −3. Uten chips øker treffkostnaden fra 26 til 27, mens bruttopoengene øker 54,25: netto +53,25. Dette er regnskapsdekomponering, ikke en kontrollert forklaring på chipmekanismen.

**Beslutning:** `constant_h3` beholdes som arbeidsbenchmark. Posisjonsvekter og ren posisjons-HGB videreføres ikke som primære utfordrere. Hybriden beholdes som forskningskandidat for regimet uten chips; ingen modell byttes ut fra sekundærmålet, og ingen posisjons-/sesongregel velges etter disse resultatene.

Neste prioritet er fortsatt bedre tidsriktig kampkalender og tilgjengelighetsinformasjon, eller en låst prospektiv evaluering. Denne runden begrunner ikke et nytt historisk søk etter posisjonsvekter.

## Kontroller

- **32 nye forløp / 1088 beslutninger**, med samme åpning, beslutningsmotor og ressurser.
- Alle **8 benchmarkforløp gjenskaper nøyaktig lag, startellever, benk, kaptein, visekaptein og poeng** fra arkivet. Arkivhashene er kontrollert mot benchmarkmanifestet.
- Nytrent global HGB gjenskaper alle tidligere rundeprognoser; største forskjell **1,78 × 10⁻¹⁵**.
- Alle solverkjøringer har optimal status innen toleransen; største gap **9,95 × 10⁻⁶**. Troppsposisjoner, maks tre per klubb, bank, FT og poengregnskap består kontrollene.
- Fire posisjoner × ni retreninger × fire sesonger gir **144 posisjonsvise treninger**. Alle treningsutfall er tilgjengelige før aktuell frist. De 61 registrerte treningsinputfilene er uendret etter kjøring.
- To nye tester og fem relevante eksisterende regresjonstester er utført direkte og består. `pytest` er ikke installert i dette kjøremiljøet; dette er ikke en full testkjøring eller verifisert GitHub CI.

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
