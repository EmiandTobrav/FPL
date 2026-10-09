# Keeper-CBI: alternativ arkivkilde løser ikke vetoene

De seks eksisterende FotMob/FPL-avvikene kontrolleres mot det hashfestede
Opta-spillerarkivet. Klareringstallene er de samme. I fem tilfeller overstiger
klareringer alene hele native FPL-CBI; tillegg av ikke-negative blokkeringer
eller interceptions kan ikke løse dette. To tidligere innhentede primærresponser
bekrefter arkivets klareringer for Donnarumma i kamp 41 og 346.
Dette dokumenterer kildeavvik, ikke at FPL skal endres.

Ingen CBI-krav lukkes, ingen gammel gate senkes, og ingen primærbatch hentes.
[Komponenter](archive_comparison.csv), [primærvitner](primary_comparison.csv),
[funn](findings.json) og [filhashene](manifest.json) dokumenterer stoppkriteriet.
Reproduksjon av arkivuttrekket krever samme hashfestede råfil og pyarrow:

```bash
python prepare.py /path/to/opta_player_stats.parquet
```

Årsaken til kilde-/FPL-forskjellene er fortsatt uavklart. Senere kildeversjoner
er en uverifisert hypotese og brukes ikke som nullbevis eller godkjent rettelse.
341 manglende keeperverdier og 204 beskyttede konflikter er fortsatt åpne.
