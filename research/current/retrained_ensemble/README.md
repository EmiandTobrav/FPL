# Retrening av Ridge, Extra Trees og faste blandinger

Forsøksrunde 6. oktober 2026. Primærmål: nettosesongpoeng med uendret fast chipkalender. Uten chips er diagnostikk. Kandidater, vekter og evalueringsregler er låst i [protokollen](protocol.json) før denne rundens trening og simulering. Alle seks sesongene er tidligere undersøkt; ingen urørt holdout.

## Forsøket

| ID | Modell |
|---|---|
| `ridge_refresh` | Ridge med retrening hver fjerde GW |
| `extra_refresh` | Extra Trees med samme retrening |
| `re_refresh` | 50/50 av de to oppdaterte modellene |
| `three_refresh` | Lik blanding av oppdatert Ridge, Extra Trees og utvidet HGB |
| `three_frozen` | Matchet kontroll: lik blanding av sesongfrosne Ridge, Extra Trees og utvidet HGB |

Utvidet HGB (`rich_refresh`) gjenbrukes uendret fra `adaptive_events`, både som selvstendig utfordrer og i den nye blandingen. Dens frosne versjon er `rich_frozen`; den gamle `mix_three` brukte en annen HGB-featurepakke og er derfor ikke den matchede kontrollen her. Opprinnelig frossen Ridge/Extra Trees 50/50 er fortsatt hovedreferansen.

Fire nye kandidater og én ny kontroll × seks sesonger × to chipregimer gir **60 nye sesongforløp**. Sammen med 48 eksisterende kontroll-/utfordrerforløp sammenlignes 108 totalt. Samme faktiske GW4-overlevering, én-rundes optimizer, spillerpool, prisproxyer, treffkostnad, friksjon og chipkalender som før. Ingen nye variabler eller tilpasning av blandingsvekter.

Retrening ved GW5, 9, 13, 17, 21, 25, 29, 33 og 37 bruker alle tidligere tilgjengelige rader, inkludert inneværende sesong, med streng `available < cutoff`. Ingen tidsvekting. Modellen fryses mellom oppdateringene; før-frist-variabler oppdateres hver runde. Ridge og Extra Trees beholder opprinnelig BASE+FX og hyperparametere. HGB beholder forrige rundes utvidede variabler.

## Resultater

**Retrenet Extra Trees er rundens beskrivende primærvinner: 2253,5 poeng, +37,2 mot den sterke referansen.** Den vinner i 4/6 sesonger og i alle de tre siste. Det parete beskrivende 95 %-intervallet er [1,5; 73,3]. Dette er et sterkere primærresultat enn forrige rundes +8,3, men ingen uavhengig bekreftelse etter mange modellforsøk.

| Modell | Med chips | Gevinst | Uten chips | Gevinst |
|---|---:|---:|---:|---:|
| Frossen Ridge/Extra 50/50 (referanse) | 2216,3 | +0,0 | 2155,7 | +0,0 |
| Frossen Ridge | 2160,7 | -55,7 | 2118,5 | -37,2 |
| Frossen Extra Trees | 2184,7 | -31,7 | 2144,8 | -10,8 |
| Utvidet HGB, retrening | 2224,7 | +8,3 | 2147,8 | -7,8 |
| Ridge, retrening | 2209,3 | -7,0 | 2103,8 | -51,8 |
| Extra Trees, retrening | 2253,5 | +37,2 | 2116,7 | -39,0 |
| Ridge/Extra 50/50, retrening | 2246,8 | +30,5 | 2125,7 | -30,0 |
| Treveis, retrening | 2242,7 | +26,3 | 2166,0 | +10,3 |
| Treveis, frossen kontroll | 2205,5 | -10,8 | 2167,5 | +11,8 |

### Matchede effekter og robusthet

Retrening av Extra Trees gir **+68,8 med chips** mot frossen Extra Trees, med 5/6 seire og intervall [33,5; 97,2]. Retrening av Ridge gir **+48,7**, også 5/6 seire, intervall [9,5; 80,7]. Ridge alene når likevel ikke den sterke blandingsreferansen.

Effekten snur uten chips: Extra Trees −28,2 og Ridge −14,7 mot sine egne frosne kontroller. Mot den sterke referansen taper oppdatert Extra Trees −39,0, med bare 1/6 seire; oppdatert Ridge/Extra taper −30,0. Gevinsten fra retrening kan derfor ikke beskrives som uavhengig av beslutningsregime. Dette viser en interaksjon i denne simuleringen, men identifiserer ikke hvilke chipbeslutninger eller etterfølgende troppsendringer som skaper den.

Treveisblandingen er positiv mot referansen i begge regimer: **+26,3 med chips og +10,3 uten**, med 4/6 seire i begge. Intervallene [−21,0; 72,3] og [−23,8; 40,0] inkluderer null. Mot sin matchede frosne treveisblanding gir retrening +37,2/−1,5 med/uten chips. Den frosne treveisblandingen er faktisk marginalt bedre uten chips. HGB-tillegget til oppdatert Ridge/Extra gir −4,2 med chips, men +40,3 uten; intervallene inkluderer null. Vi har ingen dokumentert universell gevinst av å legge til en tredje modell.

### Sesongvis gevinst mot referansen med chips

| Sesong | Ridge, retrent | Extra, retrent | 50/50, retrent | Treveis, retrent | Utvidet HGB, retrent |
|---|---:|---:|---:|---:|---:|
| 2020-21 | +161 | -20 | -40 | -44 | +129 |
| 2021-22 | +36 | +25 | +59 | +38 | -141 |
| 2022-23 | -28 | -11 | +83 | +123 | +115 |
| 2023-24 | +57 | +100 | -9 | -57 | +10 |
| 2024-25 | -132 | +43 | +36 | +50 | -29 |
| 2025-26 | -136 | +86 | +54 | +48 | -34 |

Modellvalget basert utelukkende på tidligere sesonger velger Ridge i 2022/23, 2023/24 og 2024/25, deretter Extra Trees i 2025/26. Gevinstene er −28, +57, −132 og +86: **−4,25 poeng i gjennomsnitt**. Uten chips gir samme valgregel −10,25. At vi etterpå kan identifisere Extra Trees som best, betyr altså ikke at den forhåndsdefinerte valgregelen ville gitt bedre sesonggevinst.

### Rangering av oppside

Oppdatert treveisblanding har 25,18 % 8+-treff blant topp 20, mot referansens 23,97 %. Faktiske poeng i dette utvalget øker fra 4,91 til 5,03. Blant topp 10 billige spillere øker treffandelen fra 16,89 % til 17,97 %; for kort historikk er den praktisk talt uendret, 5,417 % mot 5,420 %.

Dette er supplerende prediksjonsdiagnostikk, ikke et bevis på sesonggevinst. Extra Trees vinner primærmålet selv om treveisblandingen har bedre topp-20-rangering. Kort historikk betyr færre enn 12 observerte kamprader; billige spillere defineres med samme laggede prisgrenser som tidligere.

### Hva vi tar videre

- Behold retrent Extra Trees som primær utfordrer for den faste chipkalenderen. Behold treveisblandingen som utfordrer for bedre stabilitet mellom regimer. Ingen automatisk produksjonsendring.
- Neste målrettede spor bør isolere modellens samspill med chips og troppsendringer: først dekomponering av eksisterende spor, deretter matchede beslutninger fra identiske troppstilstander. En ren summering av poeng på chiprunder skiller ikke direkte chipgevinst fra tidligere bytter.
- Lås kandidatene før nye data og evaluer prospektivt. Ikke søk nye blandingsvekter eller retreningsfrekvenser på disse samme seks sesongene. Historiske før-frist-kalendere, tilgjengelighet og roller er fortsatt prioriterte databehov.

[Sesongresultater](results/season_results.csv), [modelloversikt](results/model_summary.csv), [parete effekter og intervaller](results/paired_summary.csv), [tidsordnet modellvalg](results/chronological_selection.csv), [rangeringssammendrag](results/ranking_summary.csv) og [kontrollrapport](results/checks.json).

173 tester bestått lokalt; GitHub CI-status er ikke verifisert. Alle 60 nye forløp og 2040 beslutninger har godkjent regnskap og optimal solverstatus innen toleransen, maksimalt rapportert gap 1,68 × 10⁻⁹. Alle 60 treningsvinduer matcher HGB-vinduene. Største avvik mellom refittede frosne Ridge-/Extra-prognoser og arkivet er 4,64 × 10⁻⁷.

## Kontroller og reproduksjon

Etter oppsett fra rot-README og `python scripts/prepare_data.py`, fra repositoryroten:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/retrained_ensemble/build.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/retrained_ensemble/run.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/retrained_ensemble/summarize.py
```

Ferdige sesongprognoser og spor gjenbrukes. For full retrening i en separat arbeidskopi fjernes denne forsøksmappens prognoser, trenings-/kontrollauditer, spor og `run_manifest.json` først. Ikke bland tidligere cache med endret kode eller input. HGB-prognosene ligger i `adaptive_events/results` og gjenbrukes; full regenerering av dem følger den rundens README.

`build.py` trener også de opprinnelige frosne Ridge-/Extra-modellene på nytt og krever avvik under 1e-5 mot arkiverte prognoser. Toleransen tillater arkivets float32-avrunding. `summarize.py` kontrollerer identiske treningsvinduer med HGB, ingen treningsutfall etter frist, riktig spiller-/fristkobling, identisk åpning, lovlig tropp og poengregnskap. Kilde-/inputfingeravtrykk lagres med sporene.

Tidsordnet modellvalg for 2022/23 og senere ser bare eldre sesongers gevinst: middel minus 0,25 standardavvik; referansen beholdes hvis den er innen to poeng fra best. Valgbare modeller er referansen, de fire nye kandidatene og `rich_refresh`. Den nye frosne treveisblandingen er bare kontroll. Kandidatfamiliene er foreslått etter tidligere undersøkelser av de samme sesongene; heller ikke dette modellvalget er en uavhengig sluttprøve.

Parete 95 %-bootstrapintervaller bruker 50 000 resamplinger av seks sesonger. De er beskrivende og korrigerer ikke for mange tidligere modellforsøk. Historiske poeng brukes med moderne FT-/chipregler; priser, registrering, skader og kjent aktuell kampkalender har dokumenterte proxybegrensninger. Resultatene er ikke faktisk historisk rank. Ingen produksjonsmodell byttes automatisk.
