# Felles kalender og løpende kalibrering – ny test

Ny retrospektiv sammenligning for 2023/24, 2024/25 og 2025/26. Dagens aktive modell er ikke endret. Referansen bruker dagens modelloppskrift med de nye felles kalender- og oppdateringsreglene.

## Datagrunnlag

| season | rows | rounds | calendar_h1_known | calendar_h3_known | strict_calendar_snapshots | training_rows |
| --- | --- | --- | --- | --- | --- | --- |
| 2022-23 | 25471 | 37 | 0.973 | 0.929 | 37 | 24816 |
| 2023-24 | 29428 | 38 | 0.975 | 0.941 | 38 | 28573 |
| 2024-25 | 27089 | 38 | 1 | 1 | 38 | 26169 |
| 2025-26 | 29574 | 38 | 0.996 | 0.993 | 38 | 29236 |

Samme regel i alle sesongene: siste fysisk arkiverte Git-versjon med både forfatter- og lagringstid før dokumentert offisiell frist. Kalenderen videreføres uansett alder. Uavklarte kamper gir ukjent kalender, ikke blankrunde. Nettsideendringer uten arkivert historisk versjon og fremtidig cupkalender fra slike sider er utelatt.

Begge modellene trener nye grunnprognoser og kalibrerer på fire-runders rytme. Kalibreringen bruker identiske spiller-/rundeobservasjoner fra 2022/23 og fremover, bare når hele målvinduet var ferdig og tilgjengelig før ny frist. Historiske kampdata bruker fortsatt den dokumenterte tilgjengelighetsregelen kampstart pluss24 timer; dette er ikke full dokumentasjon av alle tidligere statistikkversjoner.

## Resultater

| season | component | operational_matched | delta |
| --- | --- | --- | --- |
| 2023-24 | 2547 | 2456 | 91 |
| 2024-25 | 2495 | 2476 | 19 |
| 2025-26 | 2213 | 2119 | 94 |

Poengene er netto etter betalte bytter. Samme startbudsjett, spillerutvalg, priser, manager, spilleregler og chiptilgang. Alle tilgjengelige beslutninger er kontrollert og poengsummene beregnet på nytt. Ufullførte forsøk får ingen sesongsum.

Dette er en utviklingstest på sesonger vi allerede har undersøkt, ikke en urørt fremtidstest. Ulikheter i faktisk spillerprestasjon eller arkivets alder er ikke gjort kunstig like. Dekning per variabel ligger i feature_coverage.csv; kalenderens kilde og alder per frist ligger i calendar.csv.
