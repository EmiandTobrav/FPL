# Defensive tellinger: FPL-Core-Insights mot offisiell FPL 2025/26

Fullført 6. oktober 2026. Ingen kjøp. Brukerens ramme for eventuell senere datatilgang er maksimalt 500 NOK totalt; det er ikke et løpende månedsbudsjett.

## Resultat

38 Premier League-rundefiler og 38 kampfiler fra [FPL-Core-Insights](https://github.com/olbauday/FPL-Core-Insights), låst til treet `1c9191ab6b0c191378ea27f257fdab2bae63caba`. 12 754 kilderader inkluderer 1 262 med null spilletid. Alle 11 492 offisielle FPL-rader med spilletid ble koblet til kilden, fordelt på 380 kamper. Keeperrader holdes utenfor defcon-sammenligning; gjenstår 10 725 utespiller-/kamprader.

| Kontroll | Sammenlignbare rader | Avvik | Enighet |
|---|---:|---:|---:|
| Klareringer + blokkeringer + interceptions | 10 457 | 302 | 97,11 % |
| Totale taklinger | 10 725 | 282 | 97,37 % |
| Gjenvinninger | 10 725 | 163 | 98,48 % |
| CBIT | 10 457 | 557 | 94,67 % |
| Defcon-poeng med totale taklinger | 10 457 | 34 | **99,67 %** |
| Defcon-poeng med bare vunne taklinger | 10 457 | 307 | 97,06 % |

99,67 % gjelder bare radene med komplette nødvendige felt. **268 av 10 725 utespillerrader (2,50 %) mangler beregnbare poeng**, hovedsakelig fordi blokkeringstall mangler. De er ikke fylt med null. Av disse hadde 34 offisielt defcon-utslag. Manglene ligger i runde 25–38 og er derfor ikke tilfeldig fordelt over sesongen.

For komplette rader:

| Offisiell fasit | Kilde gir 0 | Kilde gir 2 |
|---|---:|---:|
| 0 poeng | 9056 | 18 |
| 2 poeng | 16 | 1367 |

Presisjon for tildelt defcon er 98,70 %, sensitivitet 98,84 %. Det er 18 falske positive og 16 falske negative, altså 68 absolutte feilpoeng, men bare +4 i netto sum over alle komplette spiller-/kamprader. Nettofeilen kan skjule feil spillerfordeling og er ikke en simulert managers sesonggevinst. 23 av poengavvikene er på forsvarere, 11 på midtbanespillere. Angripere har ingen avvik blant komplette rader, men bare ni offisielle utslag i hele sesongen; dette er et lite positivt utvalg.

## Metode og kontroller

Kjør `python research/current/rescoring_2025/core_2025_validation/compare.py` etter at de vanlige FPL-rådataene er klargjort. Skriptet bruker bare pandas og skriver resultater deterministisk.

- Kampkobling: sesong + hjemme-/bortelag, med eksplisitte navnealiaser; én kamp per ordnet lagpar i ligaen. Ikke rundemappen eller potensielt feil kilde-dato som nøkkel.
- Spillerkobling: kildefeltet player_id mot FPL element. Én-til-én-nøkler og komplett aktiv dekning kontrolleres.
- De ti duplikatene i FPL-arkivet kontrolleres for motstridende defensive felt før deduplisering.
- FPL-posisjonen og faktiske FPL-minutter bestemmer evalueringsutvalget.
- CBIT = clearances + blocks + interceptions + tackles. MID/FWD får i tillegg recoveries. DEF-terskel 10; MID/FWD-terskel 12. Keeper får null. Manglende nødvendige komponenter gir manglende poeng.
- Egne tester dekker terskelgrenser, keeper, irrelevante gjenvinninger for DEF og manglende nødvendige verdier.
- Varianten med vunne taklinger er diagnostikk, ikke en ettertilpasset korreksjon av originaldata.

`metrics.csv`, `summary.json`, `by_round_position.csv` og `point_disagreements.csv` inneholder resultatene. `sha256.json` låser input. Kjøringen genererer også `comparison.csv` med alle sammenligninger; denne trenger ikke versjoneres siden den rekonstrueres fra de arkiverte råfilene og koden. Råfilenes originale stier er `data/2025-2026/By Tournament/Premier League/GW{n}/{matches,playermatchstats}.csv`.

## Beslutning for 2024/25

Gratisdataene er gode nok til å videreføre en **kvalitetsmerket defcon-rekonstruksjon for trening og sensitivitetsanalyse**. Dette er ikke en godkjenning som eksakt testfasit. Telleavvik kan skyldes leverandørdefinisjoner, senere rettelser eller kildebehandling; årsaken er ikke identifisert for hver rad. Kontrollåret er 2025/26, så en generalisering til 2024/25 må fortsatt flagges. Ikke bruk lærte 2025/26-korreksjoner til å hevde tidsriktig 2024/25-backtest.

Behold offisielle FPL-tellinger og poeng i 2025/26. For 2024/25 finnes de defensive feltene uten nuller i det hentede utvalget, men dette garanterer ikke lik semantikk. Neste forsøk kan beregne poeng fra uendrede definisjoner, beholde usikkerhetsflagg og rapportere robusthet for feil nær tersklene. Full bonus/assists-omregning er fortsatt en separat, uløst oppgave. Benchmarken er uendret og ingen sesongsimulering er kjørt her.

## Betalt reserve, ikke kjøpt

[Sportmonks Starter](https://www.sportmonks.com/football-api/plans-pricing/) oppgir €29 per måned. Deres [statistikkbeskrivelse](https://www.sportmonks.com/football-api/football-stats-api/) lister blant annet recoveries, tackles, interceptions, clearance offline og saves insidebox. Det gjør den til en mulig kandidat for de manglende bonusfeltene, ikke en verifisert løsning. Faktisk 2024/25-dekning per spiller/kamp, definisjoner, historikktillegg, avgifter og valutakonvertert total må kontrolleres før et kjøp kan passe rammen på 500 NOK. Det er ikke dokumentert at denne leverandøren gir eksakt Opta/FPL-fasit. Ingen abonnement, prøveperiode eller kostnad er aktivert.

Anbefaling: fortsett gratis defcon-pilot først. Bruk eventuelt penger målrettet på de dokumenterte hullene i BPS-rekonstruksjonen, dersom et datautvalg beviser at en betalt kilde løser dem.
