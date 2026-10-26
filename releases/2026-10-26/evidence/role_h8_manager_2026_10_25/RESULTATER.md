# Rollemønstre: åtte-runders prognoser og full sesongsimulering

Rollekandidaten består ikke kravet om flere netto sesongpoeng i begge utviklingsår. Den aktive modellen beholdes.

Begge varianter er kjørt på nytt gjennom GW1–38 i 2023/24 og 2024/25, med samme spillerpool, priser, tomme starttilstand, manager, chips og løsergrenser. Ingen produksjonsmodell eller masterpeker er endret.

## Netto sesongpoeng etter overgangstrekk

| Sesong | Felles kontroll | Rollekandidat | Forskjell |
|---|---:|---:|---:|
| 2023/24 | 2353 | 2036 | -317 |
| 2024/25 | 2394 | 2447 | +53 |

Kontrollen er en ny kjøring av den korrigerte historikkvarianten, med samme etikettgate og fristretting som kandidaten. De gamle 2452/2498 eller 2429/2461 poengene er ikke brukt som parvis kontroll. Å sammenligne bare med en tidligere høyere/lavere sesongsum ville blande input- og modellendringer.

| Sesong | Variant | Overgangstrekk | Løserkall |
|---|---|---:|---:|
| 2023-24 | control | 24 | 436 |
| 2023-24 | roles | 40 | 419 |
| 2024-25 | control | 16 | 443 |
| 2024-25 | roles | 4 | 436 |

## Prognosefeil

MSE vurderes på samme kjente kjøpbare spiller–runde-utfall. Positive prosenter betyr lavere feil enn kontrollen. H3 og H8 gjelder summen av de neste henholdsvis tre og åtte rundenes poeng, med hele målet kjent.

| Sesong | Horisont | Kontroll MSE | Rolle MSE | Reduksjon |
|---|---:|---:|---:|---:|
| 2023-24 | 1 | 5.2513 | 5.1703 | +1.54 % |
| 2023-24 | 3 | 21.8345 | 21.5766 | +1.18 % |
| 2023-24 | 8 | 91.5114 | 92.3703 | -0.94 % |
| 2024-25 | 1 | 5.0126 | 4.9489 | +1.27 % |
| 2024-25 | 3 | 20.3873 | 20.1134 | +1.34 % |
| 2024-25 | 8 | 87.2017 | 86.9018 | +0.34 % |

Det forhåndsregistrerte prognosekravet for H1 og summert H3 i begge sesonger er bestått. H8 var en separat diagnostikk, og har svakere resultat i 2023/24. På den faste kandidatlisten er gevinstene fortsatt små; metrics.csv viser både kandidat- og kvalitetsutvalg.

## Metode og kontroll

- Samme 66 førfrist-rolleegenskaper som H1-forsøket, fra masterens frosne beregning. Ingen nye styrke-, vær-, skade- eller dødballfelt blandes inn i dette forsøket.
- Egne koeffisienter, treningsutvalg og imputering/skala for hver posisjon og hvert fremtidig offset 0–7. H1-korreksjonen gjentas ikke åtte ganger.
- Egenskapene fryses ved prognoseopprinnelsen. Ingen senere observert rolle, start eller kampopplysning fyller fremtidsrundene. Den lagrede basisprognosen inneholder allerede den daterte kampkalenderen som var tilgjengelig ved opprinnelsen.
- Bare tidligere prognoseopprinnelser og de konkrete målrundenes etiketter som var tilgjengelige strengt før refit, kan bli treningsdata. Oppdatering GW1,5,9,…37.
- Fast sesongvekting, samme ridge-straff 0,01 og treningsbasert imputering/skalering. Ingen resultatstyrt tuning. Negative poeng og reelle nullminutter beholdes; dokumenterte utenfor-PL-rader er maskert i treningsmålene.
- 1 280 hovedtilpasninger og 812 608 prognoseverdier er gjenspilt og kontrollert. Etikettid, treningsnøkler, transformasjoner og regulariserte normalligninger er kontrollert for hvert fit.
- Prognosene ble lagret og låst før scoring. Alle 152 managerbeslutninger ble lagret før oppgjøret for runden. Lovlig tropp, ellever, kaptein, benk, autosubstitusjoner, chips, priser og betalte overganger er kontrollregnet.
- Samme eksisterende adaptive manager med H3-planlegging og H8-prognoser; 16 noder per løserkall, maksimalt 40 kall per beslutning og én tråd per løser. Nodegrensen er en arbeidsgrense, ikke en lik tidsgrense.

## Fristretting

2024/25 GW15 hadde en arkivert prognose kl.13.30 UTC etter den faktiske fristen kl.11.00. I H1-forsøket ble runden utelatt. Her må en hel sesong beholdes, så basisprognosen er faktisk bygget på nytt ved kl.11.00, for begge varianter. Den gamle filen er bevart. Vi har ikke bare gitt en sen prognose et tidligere tidsstempel.

Poolens pris-, posisjons- og klubbmetadata var alle tilgjengelige før kl.11.00. Det relevante arkiverte kampoppsettet og de siste kampobservasjonene var også tidligere. Basismodellene ble tilpasset ved de opprinnelige tidligere refit-tidene, og rollehistorikken er beregnet ved riktig tidligere frist. repaired_base_audit.json bevarer tidskontroller og den gamle opprinnelsen. Denne lokale rettingen endrer ikke eldre forsøksfiler eller påstår at hele den eldre kildehistorikken nå har strengt kvalifisert mottakstid.

## Regnskap for poengforskjellen

| Sesong | Grunnpoeng | Kapteinstillegg | Endring i overgangstrekk | Netto |
|---|---:|---:|---:|---:|
| 2023-24 | -270 | -31 | +16 | -317 |
| 2024-25 | +58 | -17 | -12 | +53 |

Nettoendring er endring i grunnpoeng pluss kapteinstillegg minus endring i overgangstrekk. Grunnpoeng inkluderer autosubstitusjoner og benkebonus når brukt. Dette er bokføring av de faktiske forløpene, ikke et isolert årsaksbevis for bestemte felt eller beslutninger. round_comparison.csv viser hver runde.

## Hva konkluderer vi?

Forkast denne konfigurasjonen som fullsesong-manageroppgradering. Et positivt prognosemål eller et positivt år overstyrer ikke kravet om flere netto poeng i begge år. H1-rollefeltene beholdes i masteren, og den tidligere kortsiktige prognosekandidaten er fortsatt dokumentert; det gjør ikke denne H8-managerkonfigurasjonen bestått. Ikke juster horisontvekter eller velg gunstige runder etter disse resultatene.

Neste eventuelle modellforsøk må ha en egen mekanisme og låses før nye utfall brukes. Den eksisterende aktive modellen og dens oppfølgingsregler er uendret. Ingen 2025/26- eller 2026/27-utfall er brukt til trening eller resultatvalg i dette forsøket. Historiske kilde-/statistikkversjoner og tilgjengelighet har fortsatt dokumenterte proxybegrensninger.

## Filer

proposal.json binder hypotesen, parametrene, ressursene og inputhashene. prediction_lock.json låser prognosene. forecast_verification.json og manager_verification.json dokumenterer kontrollene. metrics.csv og forecast_comparison.csv viser prognosefeil. paired.csv og scores.csv viser sesongpoeng og overgangstrekk; chips.csv viser chiprunder. manager/ inneholder alle daterte beslutninger og oppgjør. Alle tidligere resultater og kilder er bevart.
