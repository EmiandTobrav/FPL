# Løpende retrening og selvstendig spilletids-/hendelsesmodell

Forsøksrunde 6. oktober 2026. **Primærmålet er gjennomsnittlig nettosesongpoeng med den eksisterende faste chipkalenderen.** Uten chips er diagnostikk. Protokollen og ni kandidater ble bestemt før modelltrening og sesongresultater. Alle sesongene er tidligere undersøkt; dette er ikke en urørt holdout.

## Kandidater og kontroller

| ID | Modell |
|---|---|
| `hgb_refresh` | Opprinnelig HGB og BASE+FX, retrenes hver fjerde runde |
| `hgb_recent` | Samme, med eksponentiell tidsvekting med halveringstid 365 dager |
| `rich_frozen` | HGB med utvidede variabler, sesongfrossen |
| `rich_refresh` | Samme utvidede HGB, retrenes hver fjerde runde |
| `events_frozen` | Selvstendig spilletids-/hendelsesmodell, sesongfrossen |
| `events_refresh` | Samme hendelsesmodell, retrenes hver fjerde runde |
| `blend_events_direct` | 50/50 oppdatert utvidet HGB og oppdatert hendelsesmodell |
| `blend_three` | Lik blanding av de to foregående enkeltmodellene og den fryste dekomponerte totalpoengmodellen fra `horizon_upside` |
| `blend_reference_mixture` | 50/50 sterk Ridge/Extra Trees-referanse og fryst dekomponert totalpoengmodell |

Den siste blandingen er et lite kontrollforsøk; de nye modellfamiliene kan brukes helt uten referansens prognoser. Ingen blandingsvekter velges etter resultatene. Seks sesonger 2020/21–2025/26 × ni kandidater × to chipregimer gir **108 nye sesongforløp**. Den opprinnelige HGB og sterke referansen brukes som fryste kontroller: 132 forløp sammenlignes totalt.

Samme faktiske GW4-overlevering, priser, spillerpool, énrundes beslutningsmotor, treffkostnader og chipkalender som det opprinnelige forsøket. Fire-rundersplanleggeren fra siste forsøk brukes ikke her, slik at forbedringer ikke blandes med endret optimizer.

## Tidsriktig retrening

Frosne modeller trener på eldre sesonger med utfall tilgjengelige før GW1. Oppdaterte modeller trener ved GW5, 9, 13, 17, 21, 25, 29, 33 og 37. De kan da bruke tidligere kamper fra inneværende sesong, men bare rader med `available < cutoff`. Ingen utfall fra den aktuelle beslutningen brukes. Modellen fryses mellom oppdateringene, mens før-frist-variablene oppdateres hver runde.

`hgb_recent` beholder alle treningsrader, med vekt `2^(-age_days/365)`. Alder beregnes fra utfallets tilgjengelighetstid til treningsfristen. Dette bruker ingen fremtidig poengscore eller et utvalg av senere stjernespillere.

Utvidelsen legger til kortsiktig spilletid/tilstedeværelse/60+-andel over tre kamprader, minutter3 minus minutter12, dager siden siste tilgjengelige observasjon, lagget xG/xA, saves/bonus over seks observasjoner og separate `team_ga`/`opp_gf`. De eksisterende `team_gf`/`opp_ga`-variablene beholdes. Manglende xG forblir manglende. Modellen får ikke nye før-frist-skadeopplysninger, bekreftede startellevere, direkte taktiske roller eller konkurrenttilgjengelighet som datasettet ikke har.

## Hvordan hendelsesmodellen beregner poeng

En HGB-klassifikator estimerer sannsynlighet for 0 minutter, 1–59 minutter og 60+ minutter. Dette er ikke en eksplisitt start-sannsynlighet eller en full minuttfordeling.

Fire HGB-regresjoner trener på opptredener med spilletid. De estimerer mål, assists, clean-sheet-poeng og øvrige historiske poeng betinget på kort/lang opptreden, i tillegg til de utvidede før-frist-variablene. Ved prediksjon beregnes begge spilletidsalternativer; faktiske minutter er aldri input. Forventningen vektes med de estimerte kategorisannsynlighetene, med ett/to appearance-poeng. 0 minutter antas å gi 0 poeng. Dette overser eventuelle sjeldne disiplinærpoeng uten spilletid.

Regresjonene er kvadratisk HGB-regresjon, ikke en Poisson-prosess eller en full felles hendelsesfordeling. Mål/assists klippes ved null; clean-sheet-poeng begrenses til posisjonens maksimum. Hendelsesmodellen har større samlet kapasitet enn én HGB. En eventuell effekt gjelder derfor hele modellkonstruksjonen, ikke en isolert kausal effekt av én variabel.

For å bevare historisk poengregnskap defineres øvrig-målet som faktisk historisk poeng minus appearance-, mål-, assist- og clean-sheet-komponenter. Bokføringsvektene for mål er GK6/DEF6/MID5/FWD4, assists3 og clean sheets4/4/1/0. Historiske regelavvik, inkludert eventuelle endringer i keeperpoeng og nye poengtyper, inngår i restleddet. Dette er ingen full omregning til dagens poengregler. Treningsdekomponeringen summerer nøyaktig til målet; predikerte komponenter er naturligvis ikke garantert å summere til fasit.

Dette er en første selvstendig hendelsesmodell. Den har foreløpig ingen eksplisitt modell for lagets forventede mål og spillerandeler, ingen særskilt Bayes-modell for nye spillere og ingen separat kalibrert sannsynlighetsfordeling for totalpoeng. Globale trær deler informasjon mellom spillere via de tilgjengelige variablene.

## Resultater

**En liten beskrivende seier på primærmålet, men ingen robust ny totalvinner.** `rich_refresh` får 2224,7 poeng med fast chipkalender, **+8,3** mot referansens 2216,3. Den vinner i 3/6 sesonger, og et beskrivende 95 %-intervall for gevinsten er [−62,7; 79,7]. Vi beholder den som utfordrer; ingen automatisk produksjonsendring.

### Alle kandidater

| Modell | Med chips, poeng | Mot referansen | Uten chips, poeng | Mot referansen |
|---|---:|---:|---:|---:|
| Sterk referanse | 2216,3 | — | 2155,7 | — |
| HGB, retrening | 2200,5 | −15,8 | 2169,7 | +14,0 |
| HGB, retrening og tidsvekter | 2153,3 | −63,0 | 2104,2 | −51,5 |
| Utvidet HGB, frossen | 2159,7 | −56,7 | 2075,8 | −79,8 |
| Utvidet HGB, retrening | **2224,7** | **+8,3** | 2147,8 | −7,8 |
| Hendelser, frossen | 2137,5 | −78,8 | 2100,3 | −55,3 |
| Hendelser, retrening | 2127,2 | −89,2 | 2104,7 | −51,0 |
| Direkte/hendelser 50/50 | 2194,8 | −21,5 | **2177,8** | **+22,2** |
| Treveis blanding | 2173,3 | −43,0 | 2135,8 | −19,8 |
| Referanse/dekomponert 50/50 | 2196,0 | −20,3 | 2151,8 | −3,8 |

### Den tydeligste forbedringen er retrening

Med uendrede BASE+FX-variabler forbedrer retrening vanlig HGB med **+54,7 poeng med chips og +85,8 uten chips**. Den vinner mot sesongfrossen HGB i 5/6 sesonger i begge regimer. Beskrivende intervaller er [22,5; 86,3] og [25,0; 147,3]. Dette er et mer konsistent funn enn den lille fordelen til rundens beskrivende vinner over den sterke referansen. Sammenligningen gjelder HGB; retrening av selve Ridge/Extra Trees-referansen er ikke testet her.

Retrening forbedrer utvidet HGB med +65,0/+72,0 mot dens frosne kontroll (med/uten chips), men gevinsten er langt mer ujevn: +391 poeng i én sesong med chips, og intervallet inkluderer null. Vi kan ikke tilskrive hele denne gevinsten xG alene; det er en samlet featurepakke, og xG-data starter først i 2022/23. Den frosne 2022/23-modellen har ingen observerte xG-treningsverdier, mens løpende retrening kan begynne å bruke dem.

Tidsvekting med 365 dagers halveringstid svekker oppdatert HGB med −47,2/−65,5. Denne konkrete vektingen beholdes ikke som forbedring. Vektene er ikke normalisert til middel 1, så sammenligningen omfatter også deres virkning på effektiv regularisering.

Hendelsesmodellen alene taper klart mot den oppdaterte direkte modellen med samme variabler: −97,5 med chips og −43,2 uten chips. Bedre struktur i seg selv er ikke nok. Vi har ikke dokumentert kalibrerte spilletidssannsynligheter eller avklart hvilke komponenter som forklarer tapet.

### Sesongvariasjon for primærvinneren

| Sesong | Utvidet HGB med retrening | Referanse | Gevinst |
|---|---:|---:|---:|
| 2020/21 | 2256 | 2127 | +129 |
| 2021/22 | 2077 | 2218 | −141 |
| 2022/23 | 2374 | 2259 | +115 |
| 2023/24 | 2179 | 2169 | +10 |
| 2024/25 | 2375 | 2404 | −29 |
| 2025/26 | 2087 | 2121 | −34 |

Fordelen er liten samlet, og kandidaten taper i de to seneste sesongene. Modellvalget som bare ser eldre sesonger, beholder referansen i alle fire ytre evalueringssesonger med chips: **0 ekstra poeng**. Diagnostikken uten chips velger andre kandidater og gir −28,5 i gjennomsnitt over fire evalueringssesonger. Vi bruker derfor ikke den beskrivende vinneren som et bevis på at vi ville valgt bedre i sanntid.

### Billige spillere og kort historikk

Blandingen av oppdatert direkte modell og hendelsesmodell øker 8+-treff blant topp 10 billige spillere fra **16,89 % til 18,87 %**; gjennomsnittlige faktiske poeng i dette utvalget øker fra 4,10 til 4,28. Topplisten innen kort historikk øker marginalt fra 5,42 % til 5,52 % i 8+-treff. Totalt topp-20-treff går fra 23,97 % til 24,59 %.

Dette kan gjøre blandingen interessant som en kandidat for budsjettvalg, men det er ikke testet som en separat pris-/posisjonsspesialist. Den taper fortsatt 21,5 sesongpoeng på primærmålet. Kort historikk betyr færre enn 12 observerte kamprader, ikke en sikkert identifisert gjennombruddssesong. Billiggrenser er lagget pris ≤4,5 keeper, ≤5,0 forsvar og ≤6,0 midtbane/angrep.

### Hva vi tar videre

Løpende retrening bør videreføres som et hovedspor. `rich_refresh` er en dokumentert utfordrer til referansen, men den har ikke vist stabil overlegenhet. Et naturlig kontrollforsøk er å undersøke om den sterkere referansefamilien også tjener på retrening, uten å gjøre den til et krav for nye modeller. Hendelsesmodellen trenger komponent-/kalibreringsdiagnostikk og bedre tilgjengelighets-/rollesignaler før den eventuelt videreføres som selvstendig hovedmodell. Ingen nye vekter, undergrupper eller modeller er valgt etter fasit i denne runden.

[Sesongresultater](results/season_results.csv), [modelloversikt](results/model_summary.csv), [parete effekter og intervaller](results/paired_summary.csv), [tidsordnet modellvalg](results/chronological_selection.csv), [rangeringssammendrag](results/ranking_summary.csv) og [kontrollrapport](results/checks.json).

## Kontroller og reproduksjon

Etter miljøoppsett fra rot-README og `python scripts/prepare_data.py`, fra repositoryroten:

```bash
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/adaptive_events/run.py
OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python research/current/adaptive_events/summarize.py
```

Dette bruker lagrede prognoser og beslutningsspor. For identisk avspilling fjernes bare `adaptive_events/results/trace_*.json.gz` i en separat arbeidskopi. Full retrening bruker `build.py`, som trener to sesonger samtidig og gjenbruker ferdige sesongfiler. Ved endret modell/input må prognoser, sesongauditer, gamle spor og `run_manifest.json` fjernes i en ny forsøkskopi; ikke gjenbruk gamle sesongfiler med ny kode.

`features.py` bygger variabler og målkomponenter; `models.py` inneholder hendelsesmodellen; `build.py` trener; `run.py` simulerer; `summarize.py` kontrollerer og rapporterer. `training_audit*.csv` inneholder tidsgrenser og antall inneværende-sesong-observasjoner. Original HGB trenes på nytt som kontroll og må gjenskape gamle prognoser innen 1e-7 før nye prognoser lagres.

Prognosefilenes `p_play_sum` og `p_60_sum` er summer av kampvise sannsynligheter i en runde. I dobbeltrunder kan de overstige 1; de er ikke sannsynligheten for minst én opptreden. Invariantene 0 ≤ p60sum ≤ pplaysum ≤ kampantall kontrolleres. Ingen kalibreringsgevinst påstås ut fra disse kontrollene alene.

Modellvalg for 2022/23 og senere bruker bare tidligere sesongers middelgevinst minus 0,25 standardavvik; behold referansen hvis den er innen to poeng fra beste merit. Dette rapporteres separat fra den beskrivende vinneren over alle seks sesonger. Fordi modellfamiliene er foreslått etter tidligere undersøkelser av de samme sesongene, er heller ikke denne seleksjonsanalysen en uavhengig holdout.

Poengregnskap, lovlige posisjoner, bank, FT og identisk åpning kontrolleres. Parete bootstrapintervaller bruker 50 000 resamplinger av seks sesonger og korrigerer ikke for de mange historiske modellforsøkene. Priser, registrering, skader og aktuell kampkalender har de samme historiske proxybegrensningene som hovedforsøket. Ingen produksjonsmodell byttes automatisk.

172 tester bestått lokalt på ferdig kode. Alle 108 nye simuleringer og 3672 beslutninger har godkjent regnskap og optimal solverstatus innen solverens toleranse; maksimalt rapportert gap er omtrent 2,75 × 10⁻⁸. De 60 treningsvinduene er kontrollert mot tilgjengelighetstid før frist. Kontroll-HGB gjenskaper tidligere prognoser med avvik 0,0 før CSV-lagring i alle seks sesonger. GitHub CI-status er ikke verifisert.
