# Sesongresultater på felles grunnlag

46 nye sesongforsøk: 18 modell-/feltvarianter, to referanser og tre separate værscenarioer i både 2023/24 og 2024/25. 43 komplette sesonger; 3 teknisk stoppet under de felles ressursgrensene. Alle 1,675 lagrede rundevalg og poengoppgjør er kontrollert i etterkant. Tallene under er netto FPL-poeng etter byttekostnader. Ufullførte sesonger gis ingen total eller plassering.

**Høyest snitt blant de 18 nye variantene:** Komponentmodell, 2584.5 poeng. Dette snittet må vurderes sammen med resultatet i hver sesong.

**Forhåndsvalgt nyttekrav bestått:** LightGBM, Todelt deltakelsesmodell, Komponentmodell. Disse slår begge referanser i begge sesongene.

Dagens operative modell er bevart. Dette er tidligere undersøkte utviklingssesonger og mange parallelle sammenligninger; resultatene er forskningsgrunnlag, ikke en urørt bekreftelse eller automatisk modellvalg.

## Netto sesongpoeng

![Netto poengforskjell mot operativ referanse i begge sesonger](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/common_season_comparison_2026_10_25/season_comparison.png)

| Modell/pakke | 2023/24 | 2024/25 | Snitt | Mot operativ, 23/24 | Mot operativ, 24/25 | Slår begge referanser i begge år |
|---|---:|---:|---:|---:|---:|---|
| Referanse: korrigert historikk | 2353 | 2394 | 2373.5 | -115 | -104 | Referanse |
| Referanse: dagens operative modell | 2468 | 2498 | 2483.0 | +0 | +0 | Referanse |
| Komponentmodell | 2565 | 2604 | 2584.5 | +97 | +106 | Ja |
| Todelt deltakelsesmodell | 2497 | 2636 | 2566.5 | +29 | +138 | Ja |
| LightGBM | 2535 | 2539 | 2537.0 | +67 | +41 | Ja |
| Uten tidligere kampvær | 2463 | 2600 | 2531.5 | -5 | +102 | Nei |
| HGB | 2461 | 2557 | 2509.0 | -7 | +59 | Nei |
| Uten kampbelastning/hvile | 2399 | 2591 | 2495.0 | -69 | +93 | Nei |
| Poengfordeling med lærte forventninger | 2365 | 2582 | 2473.5 | -103 | +84 | Nei |
| Uten tilgjengelighet/fravær | 2411 | 2526 | 2468.5 | -57 | +28 | Nei |
| Extra Trees | 2473 | 2440 | 2456.5 | +5 | -58 | Nei |
| Uten dødballroller | 2377 | 2522 | 2449.5 | -91 | +24 | Nei |
| CatBoost, alle felt | 2449 | 2403 | 2426.0 | -19 | -95 | Nei |
| Uten rollemønstre | 2315 | 2531 | 2423.0 | -153 | +33 | Nei |
| Ridge | 2513 | 2330 | 2421.5 | +45 | -168 | Nei |
| Uten dynamisk styrke | 2338 | 2486 | 2412.0 | -130 | -12 | Nei |
| CatBoost, bare grunnhistorikk | 2196 | 2502 | 2349.0 | -272 | +4 | Nei |
| 50/50 Ridge + Extra Trees | 2457 | — | — | -11 | — | Ufullført |
| Start/innhopp/ingen minutter | 2319 | — | — | -149 | — | Ufullført |
| Fast sesongvektet historikk | — | 2431 | — | — | -67 | Ufullført |

### Teknisk ufullførte forsøk

Et teknisk stopp er ingen målt sesonggevinst eller sesongnedgang. De opprinnelige modellene, grensene og delvise loggene er bevart; ingen kjøring er forsøkt på nytt med mer ressurser. Gjennomsnitt og nyttekrav krever begge komplette sesonger.

| Modell | Sesong | Ferdige runder | Årsak |
|---|---|---:|---|
| Fast sesongvektet historikk | 2023-24 | 21 | Løser overskred felles nodegrense |
| 50/50 Ridge + Extra Trees | 2024-25 | 12 | Løser overskred felles nodegrense |
| Start/innhopp/ingen minutter | 2024-25 | 8 | Løser overskred felles nodegrense |

## Vær i sesongsimuleringene

Faktisk vær og de to faste støyvariantene er også kjørt gjennom samme manager. De har informasjon fra målkampene og skal leses som optimistiske scenarioer. De inngår ikke i kravet for operativ forbedring. Sammenligningen under bruker CatBoost med alle øvrige felt som kontroll.

| Scenario | 2023/24 | 2024/25 | Snitt | Endring mot full CatBoost, 23/24 | Endring, 24/25 |
|---|---:|---:|---:|---:|---:|
| CatBoost, alle felt | 2449 | 2403 | 2426.0 | +0 | +0 |
| Vær: faktisk kampvær | 2430 | 2587 | 2508.5 | -19 | +184 |
| Vær: syntetisk feilnivå 1 | 2430 | 2545 | 2487.5 | -19 | +142 |
| Vær: syntetisk feilnivå 2 | 2430 | 2563 | 2496.5 | -19 | +160 |

## Hva som er likt i sesongtesten

- Begge sesonger starter uten spillere og med £100 millioner. Alle armer får samme daterte spillerutvalg, priser, posisjoner, klubbtilhørighet og regler. Dokumenterte utlån/avganger brukes likt for alle. Ingen av de tidligere lagrede sesongtotalene er gjenbrukt.
- Samme manager velger overganger, startlag, benk, kaptein og chips. Prognosehorisonten er åtte runder og planleggingshorisonten tre. Hvert valg har samme grense på 40 løserkall og 16 søkenoder per kall, med én tråd. Faktisk forbruk kan variere.
- Alle 18 modell-/feltvarianter forsøkes, uavhengig av plassering i prognosetesten. De lagrede H1/H3-poeng- og minuttprognosene suppleres med samme enkle projeksjonsmetode, tilpasset separat for hver modell og hver fremtidige runde. H1 er ikke bare gjentatt åtte ganger.
- Projeksjonen lærer bare fra tidligere prognosetidspunkter med kjent fasit før oppdateringen. Også hele lærerobservasjonens H3-periode må være ferdig før den brukes, likt for alle modellene. Fremtidig kampmengde/hjemmeandel hentes fra datert kalender; motstanderstyrke fryses ved nåværende frist. Fremtidig observert spillerstatistikk brukes ikke.
- 1 440 separate projeksjonstilpasninger for de 18 hovedvariantene og 80 for faktisk-vær-varianten. De samme værkoeffisientene brukes ved begge støynivåer. Ukjent kampkalender beholdes som ukjent, og manglende fasit blir ikke null.
- De to referansene er eksisterende prognosesystemer med sin opprinnelige trening. De er kjørt på nytt gjennom samme manager og de samme kvalifiserte spillerutvalgene. Den operative referansen beholder den kjente svakheten med historiske strukturelle nullrader; den korrigerte referansen gjør denne forskjellen synlig. De er eksterne systemreferanser, ikke nytrente armer med de samme 325 feltene.
- GW15 i 2024/25 bruker den faktiske fristen 7. desember kl. 11 UTC. Prognoser som tidligere brukte kl. 13.30 er beregnet på nytt fra tidligere opplysninger. 3 305 manglende eller tidskorrigerte spiller–runde-rader er bygd fra tidligere data for å dekke hele spillerutvalget.
- Hvert valg ble lagret før de valgte spillernes utfall ble hentet. Etterkontrollen har gjenspilt alle lagrede ferdige runder: lovlighet, budsjett, priser, chips, benkeinnhopp, kaptein, poeng og byttekostnader. Dette dokumenterer reglene under de rekonstruerte kildene; historiske kilde- og tidsproxyer består.

## Prognosefeil for anslagene manageren faktisk mottar

Dette er poeng-MSE etter den felles åtterundersprojeksjonen, på identiske kjente fasiter og spillerutvalg per sesong/horisont. H3 og H8 summerer de konkrete enkeltanslagene. Resultatene skiller seg derfor fra den separate rå H1/H3-prognosetesten. Kun komplette kjente målperioder inngår; null minutter og negative kjente poeng beholdes.

| Modell/pakke | H1 MSE, snitt | H3 MSE, snitt | H8 MSE, snitt |
|---|---:|---:|---:|
| Referanse: korrigert historikk | 5.1337 | 21.3211 | 91.1491 |
| Referanse: dagens operative modell | 5.1315 | 21.3417 | 91.2689 |
| Komponentmodell | 4.8706 | 19.7631 | 85.8869 |
| Todelt deltakelsesmodell | 4.8069 | 19.5164 | 85.1606 |
| LightGBM | 4.8196 | 19.4935 | 85.1803 |
| Uten tidligere kampvær | 4.8479 | 19.6360 | 85.5297 |
| HGB | 4.8255 | 19.5390 | 85.2856 |
| Uten kampbelastning/hvile | 4.8405 | 19.6258 | 85.5421 |
| Poengfordeling med lærte forventninger | 4.8364 | 19.5950 | 85.0322 |
| Uten tilgjengelighet/fravær | 5.0366 | 20.6222 | 87.9950 |
| Extra Trees | 4.8325 | 19.5832 | 85.5538 |
| Uten dødballroller | 4.8512 | 19.6554 | 85.5381 |
| CatBoost, alle felt | 4.8451 | 19.6532 | 85.6008 |
| Uten rollemønstre | 4.8639 | 19.7633 | 86.0364 |
| Ridge | 4.9728 | 20.2169 | 87.0145 |
| Uten dynamisk styrke | 4.8746 | 19.6907 | 85.4196 |
| CatBoost, bare grunnhistorikk | 5.2106 | 21.4156 | 89.8778 |
| 50/50 Ridge + Extra Trees | 4.8616 | 19.7052 | 85.1685 |
| Start/innhopp/ingen minutter | 4.8197 | 19.5572 | 85.2688 |
| Fast sesongvektet historikk | 5.5740 | 23.9567 | 101.4128 |
| Vær: faktisk kampvær | 4.8533 | 19.6702 | 85.4688 |
| Vær: syntetisk feilnivå 1 | 4.8530 | 19.6694 | 85.4730 |
| Vær: syntetisk feilnivå 2 | 4.8536 | 19.6702 | 85.4735 |

[Alle sesongpoeng, byttekostnader og løserforbruk](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/common_season_comparison_2026_10_25/scores.csv) · [Chips per sesong](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/common_season_comparison_2026_10_25/chips.csv) · [Projeksjonsfeil per sesong og horisont](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/common_season_comparison_2026_10_25/trajectory_metrics.csv) · [Sesongkontroll](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/common_season_comparison_2026_10_25/manager_verification.json) · [Forsøkskontrakt](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/common_season_comparison_2026_10_25/proposal.json)
