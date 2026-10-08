# Avsluttende FPL-historikk for 2022/23 — samlet, ennå ikke kvalifisert

Alle **778** spillerhistorikker er hentet fra vaastav/Fantasy-Premier-League,
låst til commit `9779cdbc0c07f6c900c2d0c181ddf6bb9c800f88`. De inneholder
akkurat de **26 505** kanoniske spillerkampradene for 2022/23. Ingen identiteter,
minutter eller andre kontrollerte hendelsesankre avviker fra originalpopulasjonen.

Dette er en ny versjon av **FPLs egen element-summary-historikk**, arkivert som
spillerfiler. Den er forskjellig fra de ukentlige `gws`-filene: spillerhistorikken
har tilbakefylte starter og xG/xA/xGI/xGC fra sesongstart. Kildekode i
`provenance/` viser den direkte FPL-forespørselen og eksport av history-radene,
uten xG-estimering eller fordeling av sesongtotaler til kamper.

Rå byte for alle filer er bevart i `raw_inputs.tar.gz`, med kilde-URL, arkivcommit
og SHA-256 i `raw_manifest.json`. Lokal nedlastingsbuffer er ignorert i Git.
Den nye kilden erstatter ingen eksisterende FPL-filer, hendelsesavgjørelser,
poeng/BPS/bonus eller modeller.

## Frosne kontroller og resultat

Tre diagnostiske pilotspillere (Haaland, Ward-Prowse og Andreas Pereira) er
uttrykkelig markert som allerede undersøkte. Den nye planen valgte alle 778
registeridentiteter før full innhenting; disse tre inngår ikke i den senere
kontrollpopulasjonen. Kontrollene deler offisiell FPL-opprinnelse; ingen uavhengig
leverandørholdout påstås.

- Alle 26 505 kanoniske nøkler har nøyaktig én kilderad; ingen manglende/ekstra rader.
- 244 senere kamper og 775 kontrollspillere oppfyller omfangsgatene.
- Alle senere FPL-starter og 5 435 direkte roller fra 136 tidlige primærkamper stemmer.
- xGI i sluttarkivet er konsistent med xG+xA innen forhåndsdefinert 0,01-toleranse.
- Alle 3 890 spiller-/feltsummer stemmer med det fryste offisielle sesongregisteret
  innen forhåndsdefinert summerings-/avrundingstoleranse. Sesongsummer brukes
  som kontroll, aldri til å fordele ukjente kampverdier.
- **482 senere feltkontroller feiler kompatibilitetsgaten. Ingen xG-gruppe er godkjent.**

Avvikene er konsentrert i to grupper:

| Runde | Felt | Avvik uten pilotspillerne |
|---|---|---:|
| GW16 | xG | 26 |
| GW16 | xA | 4 |
| GW16 | xGI | 33 |
| GW16 | xGC | 125 |
| GW29 | xGI | 294 |

Det originale GW16-uttrekket har høyere presisjon og verdier som avviker fra
slutthistorikken. Dette er ikke bare avrunding. Årsak/versjon/revisjon må
dokumenteres før kvalifisering; ingen automatisk overskriving er utført.

En separat audit av hele originalpopulasjonen finner **296** GW29-rader der
original xGI er null, men xG+xA er positivt utover toleransen. To er pilotrader
og teller derfor ikke blant de 294 kontrollfeilene. FPL definerer xGI som
summen av xG og xA; dette er en konkret semantisk konflikt i originalfeltet,
ikke et behov for å anslå hendelser. Se den offisielle
[FPL-forklaringen av forventede statistikker](https://www.premierleague.com/en/news/3118332).

## Leveranse og neste handling

[Alle kildeverdier](late_player_history.csv.xz),
[kvalitetsstatus](validation_summary.json),
[avviksgrupper](disagreement_groups.csv),
[originale xGI-konflikter](original_xgi_semantic_conflicts.csv) og
[kontroll mot sesongtotaler](season_total_checks.csv.xz) er versjonert separat.

Neste arbeid skal avklare den offisielle versjonen/revisjonen av GW16-data og
en eksplisitt xGI-rettelse for GW29. Behold den mislykkede kontrollen og dens
terskler; ikke ekskluder feilkampene og kall resten full kvalifisering. Tidlige
8 491 rader er tilbakefylte kandidater inntil kildegatene er avklart.

Dette arkivet dokumenterer post-match-verdier og senere backfill. Det etablerer
ikke når hver verdi var offentlig kjent før historiske FPL-frister. Ingen
historiske beslutningsfeatures eller treningslabels godkjennes her.

Reproduksjon fra repo-roten: `python research/current/training_dataset/reproduce.py`.
Tre nye kontroller tester eksakte nøkkelfelt, endrede minutter og manglende
kildeverdier. Samlet fokuserte testsamling er nå 42 tester; full repo-/CI-test
er ikke bekreftet.
