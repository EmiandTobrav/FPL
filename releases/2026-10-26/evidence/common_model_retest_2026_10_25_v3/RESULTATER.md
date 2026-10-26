# Felles modelltest på beriket FPL-grunnlag

25. oktober 2026. Alle modellene er kjørt på den samme fryste spiller–runde-tabellen. Tidligere resultater er bevart; de er ikke brukt som nye kontrollresultater.

**Dette er en sammenligning av prognoser. Ingen nye sesongsimuleringer eller dokumentert forbedring av managerens netto sesongpoeng inngår. Dagens operative modell er beholdt.**

## Datagrunnlag

Master v5 har 190 124 spiller–kamp-rader. Den nye tabellen har 182,939 spiller–runde-rader og 325 eksplisitt tillatte prognosefelt. Komplette kilder og sjekksummer følger [manifestet](../../datasets/fpl_common_training_v1/manifest.json).

| Sesong | Lagrede rader | Historikk-/treningskvalifiserte rader | Kjente H1-poengmål | Kjente H3-poengmål |
|---|---:|---:|---:|---:|
| 2019-20 | 22,313 | 0 | 0 | 0 |
| 2020-21 | 22,889 | 20,316 | 22,889 | 16,742 |
| 2021-22 | 23,230 | 19,795 | 23,230 | 16,080 |
| 2022-23 | 24,957 | 20,769 | 24,957 | 17,334 |
| 2023-24 | 28,742 | 22,865 | 28,742 | 19,885 |
| 2024-25 | 26,919 | 21,690 | 26,919 | 20,169 |
| 2025-26 | 29,338 | 23,350 | 29,338 | 21,163 |
| 2026-27 | 4,551 | 0 | 4,551 | 2,991 |

Tellingene over beskriver tabellen; faktisk treningsutvalg avhenger også av prognosetidspunktet og når hele målperiodens fasit var tilgjengelig. 2019/20 bidrar med historikk, men har ikke harmoniserte poengmål. 2026/27 lagres som nåtidsdel og brukes ikke til trening eller scoring i dette forsøket.

Spilleruniverset er observerte spiller–runde-rader. Det er ikke en fullt rekonstruert liste over alle kjøpbare spillere ved hver historiske frist. Ingen modeller får bruke rundens faktiske lag, posisjon, pris, motstander eller kampantall som input fra utfallsraden. Tidligere observert posisjon/pris/klubb og arkiverte kalendere brukes.

Ekte nullminutter og negative poeng beholdes. Dokumenterte strukturelle nuller utenfor PL inngår ikke som kvalifisert historikk eller treningsmål. Ukjente mål og manglende fremtidige rader blir ikke oppdiktede nuller. H3 summerer tre nøyaktige FPL-rundenumre; en ufullstendig målperiode er ukjent.

| Datagruppe | Felt |
|---|---:|
| availability | 33 |
| calendar | 17 |
| history | 43 |
| lagged_weather | 4 |
| role | 65 |
| set_piece | 67 |
| strength | 13 |
| workload | 83 |

Værfelt gjelder gjennomsnitt fra de tre siste tilgjengelige spillerkampene, ikke faktisk vær i målkampen. Ingen tidskvalifiserte historiske værvarsler er lagt til. Dødballer er rapporterte roller/scenarioer, ikke bekreftede takere. Cup og landslag er belastningskontekst med ufullstendig dekning; mangler betyr ikke at spilleren ikke spilte.

## Felles testoppsett

- Trening fra 2020/21 og fremover, med ekspanderende historikk. Oppdatering før GW1, 9, 17, 25 og 33 i hver evalueringssesong. Samme rader per treningsfold og horisont for alle modeller; betingede modellhoder bruker naturlig sine kategorier innen denne felles treningsdelen.
- H1 og H3 trenes separat. Hele målperiodens statistikk må være tilgjengelig strengt før oppdateringen. H3-prognoser er direkte rundesummer, ikke åtte fremtidige enkeltprognoser til en manager.
- 2022/23–2024/25 er tidligere undersøkte utviklingssesonger. 2025/26 rapporteres separat som en tidligere undersøkt senere kontroll, ikke en urørt holdout.
- Prognosegrensen er den felles operasjonelle tidsproxyen. 2021/22 GW18 og 2024/25 GW15 utelates helt fordi den opprinnelige grensen var etter faktisk frist. Ingen sen prognose får bare et tidligere tidsstempel.
- Imputering og eventuell skalering læres bare på treningsdelen. Alle numeriske felt har eksplisitte mangelflagg. Kildeidentiteter, fritekst og kvalitets-/utfallsflagg er ikke modellfeatures.
- Fabrikkparametre er låst før kjøring. Ingen søk etter beste innstillinger eller resultatstyrte gjentakelser. Tidligere forkastede familier testes i nye, navngitte konfigurasjoner med de nye opplysningene.
- Ridge trent på de samme nye dataene er den felles modellreferansen. Den aktive operative modellen `fixed_season_h8_adaptive_v1` er også scoret som fryst ekstern referanse på identiske evalueringsrader i de to sesongene med arkiverte prognoser. Den beholder sin opprinnelige trening og er ikke en nytrenet arm i den kontrollerte arkitektursammenligningen. Ingen operativ oppgradering er dokumentert av dette alene.

## Resultater for forventede poeng

Lavere MSE er bedre. Utviklingssnittet gir hver sesong lik vekt. Prosenten sammenligner med den nytrente felles Ridge-referansen. «Alle 3» krever lavere MSE i hver av de tre utviklingssesongene.

### H1

| Modell | Utviklings-MSE | Mot Ridge | Bedre i alle 3? | MSE 2025/26 |
|---|---:|---:|:---:|---:|
| Todelt deltakelsesmodell | 4.9294 | +4.13 % | Ja | 4.5354 |
| Start/innhopp/ingen minutter | 4.9386 | +3.95 % | Ja | 4.5229 |
| LightGBM | 4.9397 | +3.93 % | Ja | 4.5355 |
| HGB | 4.9492 | +3.74 % | Ja | 4.5232 |
| Extra Trees | 4.9555 | +3.62 % | Ja | 4.5333 |
| CatBoost, alle felt | 4.9647 | +3.44 % | Ja | 4.5457 |
| 50/50 Ridge + Extra Trees | 4.9793 | +3.16 % | Ja | 4.5438 |
| Komponentmodell | 4.9860 | +3.03 % | Ja | 4.5581 |
| Poengfordeling med lærte forventninger | 5.0155 | +2.45 % | Ja | 4.5644 |
| Ridge | 5.1417 | +0.00 % | Referanse | 4.6590 |
| Fast sesongvektet historikk | 5.9498 | -15.72 % | Nei | 5.4888 |

### H3

| Modell | Utviklings-MSE | Mot Ridge | Bedre i alle 3? | MSE 2025/26 |
|---|---:|---:|:---:|---:|
| LightGBM | 20.1773 | +4.90 % | Ja | 18.0984 |
| Todelt deltakelsesmodell | 20.1862 | +4.86 % | Ja | 17.9878 |
| HGB | 20.2003 | +4.79 % | Ja | 18.1375 |
| Start/innhopp/ingen minutter | 20.2099 | +4.74 % | Ja | 17.9974 |
| CatBoost, alle felt | 20.2627 | +4.50 % | Ja | 18.0996 |
| Komponentmodell | 20.3503 | +4.08 % | Ja | 18.1922 |
| Extra Trees | 20.4111 | +3.80 % | Ja | 18.1513 |
| 50/50 Ridge + Extra Trees | 20.4138 | +3.78 % | Ja | 18.0652 |
| Poengfordeling med lærte forventninger | 20.8691 | +1.64 % | Ja | 18.1816 |
| Ridge | 21.2165 | +0.00 % | Referanse | 18.6162 |
| Fast sesongvektet historikk | 36.3006 | -71.10 % | Nei | 28.0297 |

## Sammenligning med dagens operative modell

Her scores dagens fryste operative prognoser og samtlige nye varianter mot de samme nye masterfasitene, på nøyaktig de samme kjente og arkivert kjøpbare radene. Bare 2023/24 og 2024/25 har denne operative prognosepakken. Dette er et annet og mindre evalueringsutvalg enn hovedtabellene over.

Den operative modellens historiske trening er bevart. Forskjellene her kan derfor skyldes både trening, modell og informasjon. Tabellen dokumenterer felles evaluering, ikke at dagens modell er trent om på alle nye felt. Lavere MSE er bedre.

### H1, felles operativt utvalg

| Modell | 2023/24 MSE | 2024/25 MSE |
|---|---:|---:|
| Todelt deltakelsesmodell | 4.9086 | 4.7420 |
| LightGBM | 4.9167 | 4.7532 |
| Start/innhopp/ingen minutter | 4.9224 | 4.7562 |
| HGB | 4.9387 | 4.7490 |
| Extra Trees | 4.9385 | 4.7721 |
| Uten kampbelastning/hvile | 4.9488 | 4.7625 |
| CatBoost, alle felt | 4.9537 | 4.7707 |
| Uten tidligere kampvær | 4.9528 | 4.7758 |
| Uten dødballroller | 4.9622 | 4.7761 |
| 50/50 Ridge + Extra Trees | 4.9608 | 4.7929 |
| Uten rollemønstre | 4.9716 | 4.7869 |
| Komponentmodell | 4.9799 | 4.7966 |
| Uten dynamisk styrke | 4.9827 | 4.7965 |
| Poengfordeling med lærte forventninger | 5.0060 | 4.8180 |
| Ridge | 5.1216 | 4.9306 |
| Uten tilgjengelighet/fravær | 5.1479 | 4.9493 |
| Dagens fryste operative modell | 5.2478 | 5.0307 |
| CatBoost, bare grunnhistorikk | 5.4152 | 5.1322 |
| Fast sesongvektet historikk | 5.9183 | 5.6548 |

### H3, felles operativt utvalg

| Modell | 2023/24 MSE | 2024/25 MSE |
|---|---:|---:|
| LightGBM | 20.2152 | 18.8775 |
| HGB | 20.2404 | 18.9268 |
| Todelt deltakelsesmodell | 20.2813 | 18.9219 |
| Start/innhopp/ingen minutter | 20.3097 | 18.8965 |
| Uten tidligere kampvær | 20.3204 | 18.9242 |
| Uten dødballroller | 20.3325 | 18.9202 |
| Uten kampbelastning/hvile | 20.3434 | 18.9206 |
| CatBoost, alle felt | 20.3482 | 18.9554 |
| Uten dynamisk styrke | 20.4177 | 18.9541 |
| Uten rollemønstre | 20.5025 | 19.0082 |
| Extra Trees | 20.4723 | 19.0486 |
| Komponentmodell | 20.4683 | 19.0584 |
| 50/50 Ridge + Extra Trees | 20.4597 | 19.1099 |
| Poengfordeling med lærte forventninger | 21.0269 | 19.4813 |
| Ridge | 21.2233 | 19.8947 |
| Uten tilgjengelighet/fravær | 21.4019 | 19.8162 |
| Dagens fryste operative modell | 22.1039 | 20.5041 |
| CatBoost, bare grunnhistorikk | 22.5073 | 20.7243 |
| Fast sesongvektet historikk | 34.0661 | 28.7160 |

## Bidrag fra de nye datagruppene

Samme CatBoost-oppsett brukes i alle disse armene. Positiv prosent betyr at fullpakken har lavere feil enn varianten uten datagruppen. Effektene kan overlappe og skal ikke summeres. Dette måler disse faste modellkonfigurasjonene, ikke informasjonens maksimale mulige verdi.

| Gruppe tatt bort | H1: gevinst av å beholde gruppen | H3: gevinst av å beholde gruppen | H1 bedre i alle 3 utviklingsår? |
|---|---:|---:|:---:|
| Uten tilgjengelighet/fravær | +3.48 % | +4.33 % | Ja |
| Uten dødballroller | +0.12 % | -0.02 % | Ja |
| Uten kampbelastning/hvile | -0.09 % | -0.02 % | Nei |
| Uten rollemønstre | +0.36 % | +0.49 % | Ja |
| Uten dynamisk styrke | +0.51 % | +0.25 % | Ja |
| Uten tidligere kampvær | +0.01 % | +0.05 % | Nei |

Hele utvidelsen mot CatBoost med bare grunnhistorikk, H1: +7.89 % lavere MSE.

Hele utvidelsen mot CatBoost med bare grunnhistorikk, H3: +8.75 % lavere MSE.

## Forventede minutter og sannsynligheter

Minutter vurderes separat fra poeng. Poengmodellene får dermed ikke en samlet karakter som skjuler en forverring i minutter.

| Modell | H1 minutt-MSE, utviklingssnitt | H1 minutt-MSE 2025/26 |
|---|---:|---:|
| LightGBM | 572.48 | 514.25 |
| HGB | 576.11 | 516.74 |
| Start/innhopp/ingen minutter | 583.60 | 533.12 |
| Extra Trees | 585.00 | 528.86 |
| Todelt deltakelsesmodell | 585.91 | 539.72 |
| 50/50 Ridge + Extra Trees | 590.78 | 534.91 |
| CatBoost, alle felt | 604.16 | 548.44 |
| Komponentmodell | 608.62 | 551.31 |
| Ridge | 637.68 | 574.35 |
| Poengfordeling med lærte forventninger | 750.91 | 675.38 |
| Fast sesongvektet historikk | 1010.30 | 915.14 |

Deltakelsessannsynligheter fra todelt modell og rollemodell vurderes med Brier, og poengkategoriene med normalisert RPS. Tabellen under gjelder H1; lavere er bedre. Disse målene sammenlignes innen samme hendelse, ikke med MSE.

| Sesong | Todelt: Brier deltakelse | Rollemodell: Brier deltakelse | Poengfordeling: RPS |
|---|---:|---:|---:|
| 2022-23 | 0.09641 | 0.09780 | 0.08418 |
| 2023-24 | 0.08927 | 0.09086 | 0.07739 |
| 2024-25 | 0.09294 | 0.09417 | 0.07931 |
| 2025-26 | 0.08523 | 0.08595 | 0.07573 |

## Hvordan resultatene skal tolkes

Alle modellfamiliene er testet på nytt på felles grunnlag, inklusive tidligere forkastede todelte, rolle- og komponentvarianter. En ny konfigurasjon som vinner her opphever ikke konklusjonen fra et eldre forsøk. Fast sesongvektet historikk i denne testen er en enkel nytreningsreferanse og er ikke den operative kalibreringspakken med samme ord i navnet.

Resultatene er utviklingsevidens fra flere allerede undersøkte perioder. Fire-runders blokkintervaller er lagret i intervals.csv. Mange modeller og overlappende tremålshorisonter gir usikkerhet; intervallene er beskrivende, uten korreksjon for alle sammenligningene. Små forskjeller bør ikke brukes som grunnlag for modellbytte alene.

Den faste topp60-gruppen i metrics.csv velges fra tidligere sesongvektet poenghistorikk, før utfall. Den er felles for alle armer og er en diagnostisk spillergruppe, ikke en lovlig tropp eller en modellspesifikk liste over de beste kjøpene. «Unflagged» er kun en sensitivitetsvisning.

For å avgjøre om en kandidat gir flere FPL-poeng må den få egne tidskontrollerte fremtidige enkeltprognoser og testes mot dagens operative modell med samme lovlige spillerpool, priser, åpningslag, manager, chips og ressursgrenser. H1-prognoser gjentas ikke kunstig over H8, og H3-summer fordeles ikke vilkårlig på fremtidige runder. Dette forsøket gjør ingen slik sesongpoengpåstand.

## Kontrollspor

- 920 primitive modelltilpasninger; 40 felles treningsfolder og 18 modell-/featurevarianter.
- Alle 720 prognosefiler er gjenspilt mot de lagrede modellene og kontrollert med sjekksummer.
- Samme treningsnøkler og prognosenøkler er kontrollert i hver fold. Alle imputeringers medianer er gjenberegnet fra den respektive treningsdelen.
- Masterens H1-poeng og minutter er kontrollsummert uavhengig. Tidligere historikk og H3-mål er etterregnet på et fast tilfeldig utvalg.
- Både prognoseopprinnelse og hele målets tilgjengelighet er kontrollert før hvert fit. Historiske statistikkversjoner og faktisk mottakstid er fortsatt dokumenterte proxybegrensninger.
- Kildedata, eldre resultater, aktiv modell og forseglede prospektive prognoser er bevart.

[Alle resultater per sesong og spillergruppe](metrics.csv) · [Felles resultatsammendrag](summary.csv) · [Parvise usikkerhetsintervaller](intervals.csv) · [Etterkontroll](verification.json) · [Låst forsøkskontrakt](proposal.json) · [Datakort](../../datasets/fpl_common_training_v1/README.md)
