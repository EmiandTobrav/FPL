# Walk-forward-sammenligning av FPL-modeller

Kjøringen er fullført. Alle modellene er trent på nytt før hver observerte runde. Modellen valgt på utviklingssesongene er **todelt / 97 / all historikk**. Historikkregelen er **expanding**.

I 2025/26 får denne modellen RMSE **1.964** og MAE **1.020** poeng for neste runde. Referansen med vektet spillerhistorikk får RMSE **2.039** og MAE **1.162**. Relativ RMSE-forbedring er **3.7%**.

Modellene på utviklingsdata ligger svært tett. Små forskjeller i tabellene gir ikke grunnlag for å hevde at én modellfamilie generelt er bedre enn de andre. Dette er en rapporteringssesong med forhåndslåste innstillinger, men den er tidligere inspisert i prosjektet og omtales derfor ikke som en urørt test. Modellene oppdateres løpende med tidligere ferdige resultater også gjennom denne sesongen.

## Hva som faktisk er kjørt

- 151 observerte runder: 113 utviklingsrunder i 2022/23–2024/25 og 38 rapporteringsrunder i 2025/26.
- 2,567 modell/runde-forsøk og 1,869,252 prognoser på observerte spillerrader, fordelt på modellvarianter og horisonter. Dette er gjentatte prognoser for samme spillere, ikke antall unike datapunkter.
- H1: vektet historisk poengsnitt, Ridge, CatBoost, LightGBM og todelt deltakelse/poeng. Ridge og begge direkte tremodeller er sammenlignet med 21 og 97 variabler.
- Beste H1-kandidat på utviklingsdata sammenlignes med all historikk, siste 730 dager og eksponentielt vektet nyere historikk (halveringstid 365 dager).
- H3/H6: to beste ulike lærte modellfamilier fra H1-utviklingsresultatene, samt historisk referanse. Historikkregelen fra H1 låses også her. Dette er en målrettet sammenligning; alle modellfamilier og historikkregler er ikke uttømmende testet for H3/H6.
- Én konservativ tidskontroll for H1-modellen valgt på utviklingsdata. Modellinnstillinger er faste, uten bruk av prognoserundens utfall til tuning eller tidlig stopping. Sammenligningen gjelder disse konkrete innstillingene; den er ikke et uttømmende søk etter beste innstillinger for hver modellfamilie.

## Valg på utviklingsdata

| Modell | RMSE | MAE |
| --- | --- | --- |
| todelt / 97 / all historikk | 2.096 | 1.118 |
| ridge / 97 / all historikk | 2.096 | 1.134 |
| catboost / 97 / all historikk | 2.096 | 1.123 |
| todelt / 97 / 24 måneder | 2.096 | 1.116 |
| todelt / 97 / nyere vektet | 2.097 | 1.115 |
| lightgbm / 97 / all historikk | 2.101 | 1.123 |
| catboost / 21 / all historikk | 2.113 | 1.151 |
| ridge / 21 / all historikk | 2.117 | 1.179 |
| lightgbm / 21 / all historikk | 2.121 | 1.147 |
| Historisk poengsnitt / all historikk | 2.166 | 1.268 |

Utvelgelsen bruker samlet RMSE per observerte spillerrad. Det gir alle spillerprognoser lik vekt. Resultater for spilte kamper, null minutter og posisjoner vises separat i `subgroup_metrics.csv`; en modell som er god på de mange inaktive spillerne er ikke automatisk best til lagvalg.

## Rapportering 2025/26: neste runde

| Modell | RMSE | MAE | Skjevhet | Topp 10, poeng/runde | Kaptein, poeng/runde |
| --- | --- | --- | --- | --- | --- |
| todelt / 97 / all historikk | 1.964 | 1.020 | 0.027 | 43.921 | 6.289 |
| todelt / 97 / 24 måneder | 1.965 | 1.016 | 0.017 | 43.842 | 5.842 |
| lightgbm / 97 / all historikk | 1.965 | 1.017 | 0.016 | 44.000 | 6.000 |
| todelt / 97 / nyere vektet | 1.965 | 1.013 | 0.012 | 44.684 | 6.289 |
| catboost / 97 / all historikk | 1.966 | 1.027 | 0.018 | 46.053 | 6.421 |
| ridge / 97 / all historikk | 1.967 | 1.037 | -0.001 | 43.211 | 6.711 |
| catboost / 21 / all historikk | 1.979 | 1.041 | 0.042 | 42.763 | 5.395 |
| lightgbm / 21 / all historikk | 1.979 | 1.036 | 0.036 | 42.342 | 5.789 |
| ridge / 21 / all historikk | 1.984 | 1.071 | 0.043 | 42.947 | 6.079 |
| Historisk poengsnitt / all historikk | 2.039 | 1.162 | 0.058 | 43.526 | 6.079 |

Topp 10 og kaptein er rangeringstester blant observerte kandidater med kjent utfall. De håndhever ikke budsjett, posisjonskrav, maks tre fra et lag, overganger, benk eller chips. Dette er derfor ikke totalpoeng fra et lovlig FPL-lag og kan ikke sammenlignes direkte med det gamle strategibenchmarket. Gamle tall med tidligere poengregler er ikke gjenbrukt.

Blant spillere som faktisk spilte:

| Modell | Antall | RMSE | MAE |
| --- | --- | --- | --- |
| Historisk poengsnitt / all historikk | 11361 | 3.058 | 1.983 |
| ridge / 97 / all historikk | 11361 | 2.987 | 2.006 |
| todelt / 97 / all historikk | 11361 | 2.976 | 2.028 |

Dette er en etterkontroll, ikke et spillerutvalg modellen får vite på forhånd. MAE og RMSE kan favorisere ulike modeller, særlig når poengfordelingen har mange nuller og noen store utfall.

Positiv skjevhet betyr at poengene i gjennomsnitt overvurderes; negativ skjevhet betyr undervurdering.

## Tre og seks runder

| Modell | Antall kjente utfall | RMSE | MAE | Topp 10, poeng/prognose |
| --- | --- | --- | --- | --- |
| todelt / 97 / all historikk / H3 | 26840 | 3.940 | 2.328 | 133.722 |
| ridge / 97 / all historikk / H3 | 26840 | 3.946 | 2.386 | 130.417 |
| Historisk poengsnitt / all historikk / H3 | 26840 | 4.258 | 2.831 | 124.306 |
| todelt / 97 / all historikk / H6 | 23478 | 6.623 | 4.139 | 258.606 |
| ridge / 97 / all historikk / H6 | 23478 | 6.679 | 4.302 | 253.970 |
| Historisk poengsnitt / all historikk / H6 | 23478 | 7.441 | 5.271 | 240.818 |

H3/H6 er direkte prognoser for hele poengsummen, ikke H1 multiplisert med tre eller seks. Bare hele observerte og ferdige horisonter inngår i trening. Manglende fremtidige observasjoner gir ukjent mål og fylles ikke med null. Utfallene overlapper mellom prognoserundene; rangeringstallene er per prognose, ikke poeng som kan summeres til en sesongscore.

## Tidskontrollen

| Klokke | Antall | RMSE | MAE | Skjevhet |
| --- | --- | --- | --- | --- |
| conservative_v1 | 29338 | 2.043 | 1.103 | 0.030 |
| operational_proxy_v1 | 29338 | 1.964 | 1.020 | 0.027 |

Samme valgte H1-modell er trent på nytt med den konservative klokken. Dette undersøker virkningen av strengere tidsantakelser; det er ikke en ny sammenligning av alle modellfamiliene.

## Usikkerhet og kontroller

Parvise 95% intervaller er beregnet med 2 000 resamplinger av sammenhengende blokker på seks prognoserunder. Alle spillere i en runde følger samme blokk. For valgt H1-modell minus historisk referanse er RMSE-intervallet **[-0.089, -0.066]**. Negative tall favoriserer valgt modell. Intervallene er beskrivende og dekker ikke usikkerheten fra tidligere datavalg og modellsøk.

Alle 2,567 forsøk har bestått kontroll av at både treningsradens prognosetid og hele målhorisontens tilgjengelighetstid ligger før prognosen. Alle prognoser er endelige tall, alle observerte kandidatrader er med, og ingen poengmål eller prognoser er klippet. Negative poeng uten spilletid er beholdt i den todelte modellens gren for ingen deltakelse. Kildedatasettets filer er uendret og bekreftet med kontrollsummer.

Den operative klokken antar prognose 90 minutter før første faktiske kampstart i runden og resultattilgjengelighet 24 timer etter siste relevante kampstart. Den konservative kontrollen bruker syv dager før og etter. Ingen av disse gjenskaper dokumenterte historiske FPL-frister eller publiseringstidspunkter. Kampoppsett og motstanderdata er utelatt fordi historiske forhåndsversjoner ikke er verifisert. Pris følger siste tilgjengelige observerte pris og holdes fast mellom observasjoner.

Aksepterte estimater beholdes. En ekstra H1-rapport utelater kvalitetsmerkede mål fra evalueringen; modellene trenes ikke om på et annet datasett. Spilleruniverset er observerte rader, ikke et verifisert komplett utvalg av kjøpbare spillere før fristen. RMSE på alle rader kan belønne treff på inaktive spillere; derfor følger rangering, deltakelsesgrupper, posisjoner og kalibrering med.

## Leveranser og neste bruk

- `predictions.csv.xz`: samtlige prognoser med faktisk mål, tidsstempel og modellvariant.
- `metrics.csv`, `season_metrics.csv`, `round_metrics.csv`, `subgroup_metrics.csv`, `calibration.csv`: samlet, løpende og gruppert kvalitet.
- `paired_confidence_intervals.json`: parvise intervaller på rapporteringssesongen.
- `protocol.json`, `selection.json`, `verification.json`: oppsett, valg og dokumenterte kontroller.
- `checkpoints/`: prognoser og hvilke treningsrader, tider, vekter og behandlinger som ble brukt i hvert forsøk.
- `run.py` og `analyze.py`: gjenkjørbar studie. Modellbiblioteker er foreløpig installert i et midlertidig miljø; eksakte versjoner følger pakken.

Anbefalingen er å ta tre kandidater videre til samme simulering av lag og overganger: den todelte CatBoost-modellen med 97 variabler for best samlet prognosefeil, direkte CatBoost med 97 variabler for best topp-ti-rangering, og Ridge med 97 variabler som enkel referanse med best kapteinsrangering i 2025/26. Alle bruker all tilgjengelig historikk og ny trening før hver runde. Dette er en kortliste, ikke en produksjonsbeslutning basert på rapporteringssesongen. Den todelte modellens RMSE-forskjell mot Ridge og direkte CatBoost er så liten at de parvise intervallene inkluderer null. Rangeringstestene er utforskende; de gir ikke i seg selv bevis for hvilken modell som vil vinne en lovlig FPL-simulering.

Valgt modell er en prognosekandidat, ikke en ferdig optimal FPL-strategi. Et videre lag-/overgangsforsøk bør bruke samme omregnede mål og samme pris-/tidsregel for alle kandidater. Produksjonsmodell og beste lovlige FPL-strategi er ikke fastsatt av denne prognosestudien.
