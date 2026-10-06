# Kampvise justeringer, lengre horisonter og adaptive chips

Fullført 6. oktober 2026. 84 nye sesongforløp, 2856 hovedmodellbeslutninger på 2022/23–2025/26. **Arbeidsbenchmarken `constant_h3` beholdes.** Dette er utforskende tester på fire allerede gjenbrukte sesonger, ikke en urørt validering eller en historisk rangbevisføring.

## Resultat og beslutning

Høyest observert snitt med chips er **2351,50** for fulljustert H3 med adaptiv Triple Captain: +43,25 mot benchmark, men bare +7,75 mot den enklere kalenderkontrollen. Den isolerte TC-gevinsten er +3,50 mot samme fulljusterte prognose med faste chipdatoer, med gevinst i to av fire sesonger. Full kampjustering alene gir +4,25 med chips og −36,00 uten chips mot kamptelling ved H3. Dette er ikke en robust bekreftet forbedring.

Ingen H5/H8-variant vinner med chips. Uten chips gir ren kamptelling ved H8 2232,00 poeng, +13,75 mot H3, men 91 av 136 handlinger er tidsbegrensede solverløsninger. Det beholdes kun som diagnostisk spor. Alle adaptive chips samlet taper 48,50 mot faste datoer på samme prognose; adaptiv Wildcard taper i alle fire sesonger.

Behold kalenderutfordreren og fulljustert H3/TC som forskning, og behold arbeidsbenchmarken. Neste prioritet er bedre kalender-/fristdekning, en mer stabil solver for lange planer, og chip-spareverdi kalibrert på eldre sesonger før en ny låst/prospektiv evaluering. Resultatene avviser ikke muligheten for bedre chipoptimalisering; de viser at akkurat denne heuristikken stort sett ikke forbedrer den faste kalenderen.

Sesongene for den beste observerte chipkandidaten:

| season | full_h3_adaptive_tc | constant_h3 | calendar_count_h3 | gain_vs_calendar | gain_vs_benchmark |
| --- | --- | --- | --- | --- | --- |
| 2022-23 | 2343 | 2334 | 2305 | 38 | 9 |
| 2023-24 | 2324 | 2171 | 2314 | 10 | 153 |
| 2024-25 | 2487 | 2490 | 2518 | -31 | -3 |
| 2025-26 | 2252 | 2238 | 2238 | 14 | 14 |

Gevinsten mot kalenderkontrollen er positiv i tre av fire sesonger, men et beskrivende 95 % paret bootstrapintervall for middelgevinsten er [−19,75; +31,00]. Dette inkluderer ikke korreksjon for alle forsøkene.

## Kampvise prognoser og horisonter

`count` er antall-kamper-kontrollen. `venue` legger til hjemme/borte, `opponent` separate motstanderangrep/-forsvar, `full` begge. H3, H5 og H8 betyr maksimalt antall runder i planen; kjente kommende Wildcard/Free Hit forkorter den. GW38 avslutter alle planer. Aktuell prognose, overlevering, priser, ressursregler og fast chipkalender er beholdt.

Tabellen viser netto poeng, gevinst mot benchmark (2308,25), og gevinst mot `count` ved **samme horisont**. `nonoptimal` er antall tidsbegrensede hovedbeslutninger, og gap er solverens relative objektivgap, ikke usikkerhet i sesongpoeng.

| model | points | gain | matched_gain | hits | nonoptimal | max_solver_gap |
| --- | --- | --- | --- | --- | --- | --- |
| full_h3 | 2348.000 | 39.750 | 4.250 | 23.000 | 1 | 0.002 |
| count_h3 | 2343.750 | 35.500 | 0.000 | 18.000 | 0 | 0.000 |
| count_h5 | 2323.750 | 15.500 | 0.000 | 22.000 | 16 | 0.010 |
| opponent_h3 | 2318.250 | 10.000 | -25.500 | 21.000 | 0 | 0.000 |
| full_h8 | 2317.500 | 9.250 | 39.250 | 17.000 | 35 | 0.016 |
| full_h5 | 2290.000 | -18.250 | -33.750 | 19.000 | 15 | 0.007 |
| count_h8 | 2278.250 | -30.000 | 0.000 | 22.000 | 34 | 0.016 |
| venue_h3 | 2248.500 | -59.750 | -95.250 | 19.000 | 0 | 0.000 |

Uten chips (benchmark 2172,75):

| model | points | gain | matched_gain |
| --- | --- | --- | --- |
| count_h8 | 2232.00 | 59.25 | 0.00 |
| count_h3 | 2218.25 | 45.50 | 0.00 |
| full_h5 | 2214.75 | 42.00 | 27.50 |
| venue_h3 | 2206.75 | 34.00 | -11.50 |
| full_h8 | 2192.50 | 19.75 | -39.50 |
| count_h5 | 2187.25 | 14.50 | 0.00 |
| full_h3 | 2182.25 | 9.50 | -36.00 |
| opponent_h3 | 2178.75 | 6.00 | -39.50 |

## Adaptive chips på låst `full_h3`

Prognose og H3 ble låst til fulljustert modell før chipresultatene, uansett hvilken prognosevariant som vant. Én chiptype om gangen er adaptiv; de øvrige beholder opprinnelige datoer. `adaptive_all` velger alle fire adaptivt. Hver chip brukes én gang i hver halvdel, med én chip per runde og ingen to påfølgende Free Hits. Felles GW1–4-overlevering hadde ingen brukte chips.

`matched_gain` er mot fulljustert H3 med faste chips, **ikke** kalenderkontrollen eller benchmarken. Intervallene er beskrivende 95 % paret sesongbootstrap med 50 000 resamplinger, seed 173; de korrigerer ikke for modellutprøvingen.

| mode | points | gain | matched_gain | wins | ties | losses | matched_ci_low | matched_ci_high |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| adaptive_triple_captain | 2351.50 | 43.25 | 3.50 | 2 | 0 | 2 | -5.00 | 12.00 |
| adaptive_free_hit | 2336.25 | 28.00 | -11.75 | 1 | 0 | 3 | -20.25 | 1.00 |
| adaptive_bench_boost | 2334.25 | 26.00 | -13.75 | 1 | 0 | 3 | -35.00 | 7.50 |
| adaptive_wildcard | 2303.25 | -5.00 | -44.75 | 0 | 0 | 4 | -91.50 | -9.25 |
| adaptive_all | 2299.50 | -8.75 | -48.50 | 1 | 0 | 3 | -100.50 | 23.00 |

[Alle sesongvise resultater](results/all_seasons.csv) og [valgte chipdatoer](results/chip_dates.csv) viser variasjon og faktiske beslutninger. Chiprundens poeng alene er ikke en kausal chipgevinst, siden tropp og bytter endres gjennom sesongen.

## Metode og beslutningsgrunnlag

- Separate Ridge-koeffisienter per posisjon, lært kun fra tidligere sesonger med labels tilgjengelige før evalueringssesongen. Målet er historiske spillerpoeng; spillerens tidligere poeng og minutter samt eget lags mål for/mot er kontrollvariabler. Motstanderens rullerende mål for/mot og hjemme/borte gir kampjusteringen. Dette er en justering av totalprognosen, ikke en full kalibrert mål-/clean-sheet-komponentmodell.
- Lagstyrke og spillerens forventede minuttandel oppdateres med kamper avsluttet før beslutningen. Fremtidig form, minutter, skader og priser fryses ved beslutningen. Effekten skaleres med tidligere minutter/90 og avgrenses til ±2 poeng per kamp. Ridge alpha=100 var låst før kjøring.
- Den gamle fremtidsproxyen inneholder en avtakende effekt fra aktuell kamp. Vi trekker fra vår estimerte aktuelle kampeffekt med samme avtakingsfaktor før fremtidig kampeffekt legges til. Dette reduserer dobbelttelling, men er en tilnærming, ikke en eksakt dekomponering av ensemblet. Blank gir null og flere kamper summeres separat.
- Chipvalg sammenligner forventet nytte mot ordinær plan med hits og byttefriksjon. Free Hit-verdien inkluderer videre plan fra opprinnelig tropp/bank. Wildcard vurderer varig troppsendring over gjenværende H3-vindu. Bench Boost inkluderer tropps- og byttekostnad i vinduet, men bruker eksisterende benkvekt som autosubproxy; forventet autosubverdi er ikke modellert eksplisitt.
- Chipene kan vente på bedre prospektive alternativer én/to runder frem, med 0,9 avtakingsfaktor per runde. TC/BB har i tillegg en grov opsjonsverdi fra opptil åtte runder. Verdien av å spare utover synlig vindu bruker arvede startmodellkonstanter TC=8 og øvrige=12, avtakende mot utløp. Disse er forhåndsvalgte heuristikker, ikke nye terskler tilpasset evalueringsresultatene. Strategien er dermed en testbar adaptiv kandidat, ikke bevist global chipoptimum.
- Ingen realiserte fremtidige poeng inngår i chipvalget. Realiserte poeng brukes først ved oppgjør av valgt handling. Scorings-/regelgrunnlaget er fortsatt historiske spillerpoeng med nyere chip- og bytteregler.

## Kalenderdekning og begrensninger

Samme arkiver og 14-dagersregel som forrige kalenderforsøk. Vi har **ikke forbedret arkivdekningen** i denne runden. Ved eldre snapshots beholdes den eksisterende nøytrale proxyen, og sluttsesongens kalender brukes ikke til å fylle hull i fremtiden. Tabellen teller beslutninger med et ferskt nok snapshot, ikke garantert komplett kalender.

| season | rounds | fresh_snapshots |
| --- | --- | --- |
| 2022-23 | 34 | 31 |
| 2023-24 | 34 | 33 |
| 2024-25 | 34 | 33 |
| 2025-26 | 34 | 8 |

Aktuell runde og cutoff beholder benchmarkens historiske final-event/36-timersbegrensning. Gode resultater her dokumenterer derfor ikke en fullstendig tidsriktig live-backtest. H5/H8 gir mer beregningsarbeid og større eksponering mot usikker kalender og frosne spillerforutsetninger.

## Kontroller og solverbegrensninger

Alle åtte `count_h3`-kontroller gjenskaper arkiverte kalenderbeslutninger og poeng nøyaktig. Verifisering kontrollerer tropp/posisjoner, inn-/utbytter, kjøps-/salgspriser, bank, frie bytter, hits, chipbeholdning, Free Hit-retur og poengregnskap. Treningslabels, lag- og spillerhistorikk ligger før cutoff. Funksjonstestene dekker blank/dobbel, fallback, separate effekter, minuttandel, chipmuligheter, utløp og reserverte runder.

Solveren bruker den arvede 10-sekundersgrensen og toleranse 1e-5. Tidsbegrensede løsninger beholdes når de er gjennomførbare. I H5/H8 utløste manglende gjennomførbar løsning en dokumentert teknisk feilretting: bare status=1 uten incumbent gjenkjøres med 60 sekunder, etter samme regel for kontroll og kandidat. Dette ble lagt til etter observert solverfeil, ikke valgt etter poengresultater. Se feasibility_policy.json og feasibility_runs.json. To forløp som feilet i første kjøring ble gjenkjørt separat og fullført. Ingen av gjenkjøringene trengte faktisk 60-sekundersforsøket; alle de arkiverte løsningene ble funnet med 10-sekunderskall. At gjenkjøring kunne lykkes uten økt grense understreker variasjon ved tidsbegrenset optimering. Chipforsøkets `nonoptimal` i råtabellen omfatter også forkastede/prospektive kandidater; tabellen under viser kun handlingen som faktisk ble valgt. Små forbedringer er ikke robuste bevis når optimeringen ikke er fullført. Kontroller/regnskap er bestått; det hevdes ikke at alle løsninger er bevist optimale.

| model | mode | decisions | selected_nonoptimal | selected_max_gap | mean_effective_horizon |
| --- | --- | --- | --- | --- | --- |
| count_h3 | fixed_chips | 136 | 0 | 0.0000 | 2.4706 |
| count_h3 | no_chips | 136 | 0 | 0.0000 | 2.9118 |
| count_h5 | fixed_chips | 136 | 16 | 0.0096 | 3.4706 |
| count_h5 | no_chips | 136 | 37 | 0.0115 | 4.7059 |
| count_h8 | fixed_chips | 136 | 34 | 0.0164 | 4.2647 |
| count_h8 | no_chips | 136 | 91 | 0.0292 | 7.1765 |
| full_h3 | adaptive_all | 136 | 0 | 0.0000 | — |
| full_h3 | adaptive_bench_boost | 136 | 1 | 0.0032 | — |
| full_h3 | adaptive_free_hit | 136 | 0 | 0.0000 | — |
| full_h3 | adaptive_triple_captain | 136 | 1 | 0.0032 | — |
| full_h3 | adaptive_wildcard | 136 | 0 | 0.0000 | — |
| full_h3 | fixed_chips | 136 | 1 | 0.0016 | 2.4706 |
| full_h3 | no_chips | 136 | 0 | 0.0000 | 2.9118 |
| full_h5 | fixed_chips | 136 | 15 | 0.0070 | 3.4706 |
| full_h5 | no_chips | 136 | 33 | 0.0108 | 4.7059 |
| full_h8 | fixed_chips | 136 | 35 | 0.0155 | 4.2647 |
| full_h8 | no_chips | 136 | 98 | 0.0282 | 7.1765 |
| opponent_h3 | fixed_chips | 136 | 0 | 0.0000 | 2.4706 |
| opponent_h3 | no_chips | 136 | 0 | 0.0000 | 2.9118 |
| venue_h3 | fixed_chips | 136 | 0 | 0.0000 | 2.4706 |
| venue_h3 | no_chips | 136 | 0 | 0.0000 | 2.9118 |

## Reproduksjon og arkivering

Kode/protokoll ble låst lokalt før simuleringene. GitHub-kodecommit `171990e5b779f76734cb5de000b65c34f59153e5` kom mens H3 kjørte, før chip- og langhorisontkjøringene. Kilde-/prognosehash, miljø, koeffisienter og tidsrevisjon er i `results`. Solverens tidsgrense kan gi ulike gjennomførbare løsninger ved ny kjøring på en annen maskin.

Fra repositoryroten:

```bash
python scripts/prepare_data.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/calendar_counts/build.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/fixture_strategy/build.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/fixture_strategy/run.py --stage h3
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/fixture_strategy/complete_long.py
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python research/current/fixture_strategy/chips.py
python research/current/fixture_strategy/summarize.py
python research/current/fixture_strategy/verify.py
python research/current/fixture_strategy/report.py
```

Prognoser regenereres fra kode og arkiverte innganger. `portable` bevarer oppgjør, faktiske handlinger og chipvurderinger som lesbar JSON; store interne fremtidsplaner er utelatt der. Hashene i `verified_runs.csv` gjelder de komplette lokale kjøringssporene. Det hevdes ikke byteidentisk gjenoppretting av disse fra de forkortede beslutningsarkivene.
