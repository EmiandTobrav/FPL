# Direkte sluttverdi fra fast tropp og H4–H8-prognoser

Direkte sluttverdi: ikke bestått. Benchmark beholdes.

| Sesong | A: kontroll | B3: fast tropp etter H3 | Forskjell |
|---|---:|---:|---:|
| 2023-24 | 2457 | 2419 | -38 |
| 2024-25 | 2463 | 2507 | +44 |

Én forhåndsregistrert variant uten læring. Samme H3-rollout, to grener, prognoser, forslag, chipreserver og løsergrenser som A. Etter H3 beholdes den gjenstående troppen. Beste lovlige ellever og kaptein beregnes fra dagens lagrede prognoser for rundene H4–H8. Diskonterte poeng summeres; ingen nye bytter eller chipvalg etter H3. Free Hit bruker tilbakeført tropp. Ingen ekstrapolering etter H8 eller sesongslutt.

Dette er en terminal approksimasjon med fast tropp, ikke en full H8-planlegger. Den bruker flere av de allerede tilgjengelige prognosekolonnene enn A; prognosefilene er uendret. Bank, gratisbytter og ubrukte chips får ingen ny direkte sluttverdi. Ingen prognose- eller verdimodeller trenes.

Alle 152 kontroll- og kandidatrunder er avregnet på nytt. Lovlige overganger, alle H3-grener, haleverdier, prognosehash og løsergrenser er kontrollert. Kontrollens forslag og grener gjenskapes eksakt i tre utfallsblinde prøver. Kandidaten bruker ingen ekstra MILP-kall for sluttverdien; ulike sesongtilstander kan likevel gi ulikt antall totale kall.

Begrensninger: tidligere studerte utviklingsår, deterministiske punktprognoser, fast tropp etter H3 og ingen direkte ressursverdi. Faktiske senere bytter vil kunne endre verdien. Kalender, priser og tilgjengelighet følger tidligere proxyer. Ingen automatisk oppgradering.

## Ressurser og beslutninger

2023-24: endret valg mot A på samme tilstand i 4 av 38 runder. Kandidat 767 løserkall / 111.5 sekunder; kontroll 784 / 128.1. Hits: 8 mot 20.
Chipbruk kandidat: {'wildcard': [6, 23], 'free_hit': [29], 'bench_boost': [7, 24], 'triple_captain': [11, 25]}. Kontroll: {'wildcard': [7, 23], 'free_hit': [29], 'bench_boost': [13, 24], 'triple_captain': [11, 25]}.
Ubrukte chips kandidat: {'1': ['free_hit'], '2': []}. Kontroll: {'1': ['free_hit'], '2': []}.

2024-25: endret valg mot A på samme tilstand i 1 av 38 runder. Kandidat 728 løserkall / 117.2 sekunder; kontroll 728 / 119.8. Hits: 12 mot 4.
Chipbruk kandidat: {'wildcard': [6, 21], 'free_hit': [29], 'bench_boost': [7, 22], 'triple_captain': [9, 24]}. Kontroll: {'wildcard': [6, 21], 'free_hit': [29], 'bench_boost': [7, 22], 'triple_captain': [9, 24]}.
Ubrukte chips kandidat: {'1': ['free_hit'], '2': []}. Kontroll: {'1': ['free_hit'], '2': []}.

Resultatet gjelder denne sluttverdimodellen. En negativ prøve er ikke en generell avvisning av planlegging med sluttverdi. Ingen nye prognoser eller endringer i den fryste GW7–38-pakken.

[Protokoll](protocol.json) · [Kontroll og fulle detaljer](audit.json) · [Runder](rounds.csv)
