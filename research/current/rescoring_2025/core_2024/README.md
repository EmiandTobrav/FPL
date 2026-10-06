# Funnet: kampvise defensive data for 2024/25

Undersøkt 6. oktober 2026. Brukerens «25/25» er tolket som 2024/25 fra foregående diskusjon.

Kilde: [olbauday/FPL-Core-Insights](https://github.com/olbauday/FPL-Core-Insights). Dataene beskrives av vedlikeholderen som manuelt kuraterte, Opta-lignende kampstatistikker koblet til FPL-ID-er. Dette er ikke en garanti om identiske Opta/FPL-definisjoner. Kilden tillater bruk og ber om lenke tilbake. Originale CSV-er fra kildetreet `1c9191ab6b0c191378ea27f257fdab2bae63caba` er bevart under `raw/`, med lokale SHA-256 i `sha256.json`. Originale stier er `data/2024-2025/playermatchstats/GW{n}/playermatchstats.csv`, `players/players.csv` og `matches/matches.csv` under samme sesongmappe.

## Faktisk kontroll, ikke bare README-påstander

Kjør `python research/current/rescoring_2025/core_2024/audit.py` etter klargjøring av prosjektets eksisterende FPL-data.

- 38 rundefiler, 380 unike kamper, 562 spillere, 11 567 spiller-/kamprader.
- Ingen duplikate spiller-/kampnøkler eller tomme celler i rundefilene.
- Taklinger, vunne taklinger, interceptions, gjenvinninger, blokkeringer og klareringer finnes på kampnivå. Straffemål finnes også.
- Diagnostisk kobling på FPL-spiller-ID og kampdato finner alle 11 566 offisielle FPL-rader med spilletid. Én ekstra kilderad beholdes som avvik; se `unmatched.csv`.
- Blant matchede rader avviker minutter i 2 942 tilfeller, mål i ett og assists i 169. Avvikene er ikke ferdig årsaksforklart. Behold offisielle FPL-felt; ikke erstatt dem med kildefeltene.
- Dato-/ID-koblingen er diagnostikk. Produksjonskobling må låse kamper med begge lag og fixture-ID, samt bekrefte spilleridentitet. Sluttdata må ikke brukes som før-frist-informasjon.

## Hva funnet løser

Dette er et vesentlig bedre grunnlag for historiske defensive bidrag enn sesongsummer. Vi kan prøve CBIT = clearances + blocks + interceptions + tackles og CBIRT med recoveries, men må først kontrollere at `blocks` og `tackles` har riktig FPL-definisjon. `tackles_won` er et separat felt og skal ikke legges til automatisk. Null i en ikke-tom celle er heller ikke uavhengig bevis for at hendelser er komplett registrert.

Neste validering bør bruke samme leverandør i et matchet 2025/26-utvalg mot offisielle FPL-tellinger og terskelpoeng. Deretter kan 2024/25 få eksplisitt kvalitetsmerket defcon. Ingen omregnet sesongscore eller ny modellsimulering er kjørt nå.

## Det som fortsatt mangler for eksakt bonus

Spillerfilene har ikke eksplisitte felt for redninger etter skuddsted, mållinjeklareringer eller assists verifisert etter 2025/26-definisjonen. Totale skudd innenfor feltet på lagnivå kan ikke erstatte keeperens redninger av slike skudd. Gammel BPS pluss en fullstendig, verifisert regelendring kan være mulig, men feltene her beviser ikke at vi har en slik bro. Gamle assists og bonus skal derfor ikke merkes som eksakt ny-regel-fasit.

[Premierlytics](https://premierlytics.com/) er et ytterligere API-spor, men oppgir at nesten all kampstatistikk kommer fra FPL-Core-Insights og underliggende FotMob. Det er dermed ikke en uavhengig valideringskilde. API-et krever personlig utstedt nøkkel; ingen konto, kontakt eller kjøp er gjort. Deres [datakvalitetsside](https://premierlytics.com/data/quality/) dokumenterer også mangler i 2025/26 som må hensyntas ved en slik validering.

Sesongsummer fra alternative 2024/25-datasett ble nedprioritert: de kan ikke avgjøre hvor mange enkeltkamper en spiller passerte defcon-terskelen i.
