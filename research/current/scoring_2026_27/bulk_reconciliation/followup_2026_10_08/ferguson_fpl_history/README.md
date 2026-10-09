# Ferguson: FPL-spillerhistorikk avklarer uttrekksunntaket

Et versjonsfestet FPL-speil ved commit 59c767596750f554ba464de94cf4fce8664a6cbe
har to forskjellige kildesnapshots for 2024/25 kamp 239, Evan Ferguson, kode
487117/element 123. GW24-uttrekket har minutter 0, poeng 0, baklengsmål 0.
Spillerens avsluttende historikk har minutter 17, poeng 1, baklengsmål 2;
begge har BPS 4. Historikken retter også xA 0 → 0,01, xGI 0 → 0,01 og
xGC 0 → 0,74. Alle seks rettelser lagres separat; originalene bevares.

38 kampnøkler og alle kamp-/spillerankre stemmer. 982 av 988 felt er identiske;
de seks avvikene gjelder kun det tidligere dokumenterte uttrekksunntaket.
Alle 19 sesongsummer stemmer mot samme versjons FPL-spillerregister,
inkludert 385 minutter, 97 BPS, 28 poeng og 9 baklengsmål. Dette er kildeversjons-
avstemming i samme FPL-speil, ikke en uavhengig holdout eller kildeavstemning
ved flertall. BPS 4 støttes av den fullstendige spillerhistorikken og beholdes.
Ingen eksterne minutter legges over FPL.

**Ett krav lukkes:** historical_bps skifter fra fpl_extract_exception til
 dokumentert FPL-uttrekksavstemming. Ingen numerisk BPS-verdi endres.
results/native_fpl_corrections.csv.gz er de seks godkjente faktarettelsene;
results/native_player_season_corrected.csv.gz er en komplett 38-kampvisning
for spilleren. CURRENTs native_fpl_corrections-peker skal anvendes når den
neste poeng-/kanoniske versjonen bygges. Gamle labels og råtabeller endres ikke.
Historisk FPL-poeng 1 er en kilderettelse, ikke en omregnet 2026/27-label.

Kjør `python test_reconciliation.py` og `python reproduce.py` fra denne mappen.
Replay bruker de små, versjonerte råfilene og hashfestet foreldreledger; ingen
nettverk eller større arkiv er nødvendig. Fire tester består, og 14 resultat-/anvendelsesfiler gjenskapes byteidentisk offline.
Resttall og komplette kamper finnes
i results/findings.json. Samlet kvalitet og full treningsklarhet gjenstår.
