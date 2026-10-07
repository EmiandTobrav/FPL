# BPS-minuttregel: hypotesetest og fire avklarte særtilfeller

> **Superseded as the current work queue:** see [FPL-authoritative ledger](../fpl_authority/README.md). Historical diagnostics and approved evidence below are retained; provider differences do not override compatible FPL values.

7. oktober 2026. Videreført fra `84da2fd` på PR #1.
**BPS-minuttkonvensjonen er fortsatt ikke kvalifisert.** Fire konkrete
minuttbidrag er derimot dokumentert uten å velge en ny generell regel.

## Hva den eksisterende BPS-kontrollen viser

Den tidligere 2026/27-kontrollen består av 622 spillerkamper fra GW1/GW2.
Vi varierer bare minuttleddet i den eksisterende diagnostiske formelen:

| Hypotese | Minuttleddet gir 6 BPS når | Eksakte totale BPS-treff |
|---|---|---:|
| Eksisterende formel | FPL-minutter > 60 | 620/622 |
| Primærkildens heltall | Premier League `mins_played` > 60 | 621/622 |
| Inklusiv FPL-grense | FPL-minutter ≥ 60 | 621/622 |

**Bare én rad skiller hypotesene i dette materialet:** Jaidon Anthony,
2026/27, kamp 17, spillerkode 444180. FPL oppgir 60 minutter, primærkilden
61 og offisiell BPS er 4. Den eksisterende formelen gir 1; begge alternative
minuttledd gir 4. Dermed kan de to alternative forklaringene ikke skilles
fra hverandre med disse kontrollene. Dette er et nyttig feilsøkingsspor,
ikke bevis for en generell regel eller en uavhengig holdout.

Diagnostikken gjenbruker uttrykkelig den tidligere diagnostiske behandlingen
av sparsomme tellere. Anthony har 17 utelatte primære inngangsfelt utenom
minutter. Dette er **ikke** 17 nye sammenslåtte restmangler: enkelte kan
ha andre kildebevis, mens andre trenger egne avklaringer. Ingen utelatelse
blir godkjent som null. Minuttbidraget er derfor ikke isolert fra en
uavhengig, komplett beregning av resten av BPS. Ingen av de 364 historiske
regelspørsmålene lukkes på grunnlag av dette resultatet.

`current_diagnostic.csv` inneholder alle 622 rader, hypoteseresultater og
manglende primærinnganger. `current_discriminating_cases.csv` inneholder
Anthony-raden. Disse filene er diagnostikk og må aldri brukes som nye
poengetiketter. Den tidligere formelen er uendret.

## Regelkildene og neste kontroll

[FPLs forklaring](https://www.premierleague.com/en/news/4661030) gjelder
fullførte minutter for grunnpoeng. [BPS-tabellen](https://www.premierleague.com/en/news/4661029)
skiller 1–60 fra over 60 minutter, men avklarer ikke uttrykkelig den
nødvendige omregningen fra sekundklokke til BPS-minutter.
Premier Leagues [publiserte komponenteksempel](https://www.premierleague.com/en/news/3038445/fantasy-premier-league-fpl-lessons-kieran-trippier-newcastle-united-bonus-points)
gjelder lange opptredener og skiller heller ikke grensehypotesene.
Kildesøk og beslutning er dokumentert i `evidence.json`.

En ny kontroll må gi publisert minuttkomponent eller uavhengig komplette
øvrige BPS-komponenter. Følgende kildekombinasjoner skiller hypotesene:

| FPL / primærminutter | FPL > 60 | Primær > 60 | FPL ≥ 60 |
|---|---:|---:|---:|
| 60 / 61 (Anthony) | 3 | 6 | 6 |
| 60 / 60 | 3 | 3 | 6 |
| 59 / 61 | 3 | 6 | 3 |

Flere 60/61-eksempler alene kan ikke skille de to siste forklaringene.
Historiske BPS-totaler kan bare brukes med den aktuelle sesongens vekter;
de skal ikke sammenlignes direkte med 2026/27-formelen. Ingen ny, uavhengig
komponentkontroll er hentet eller hevdet i denne oppfølgingen.

## Fire avklarte minuttbidrag

| Spiller og kamp | Gjennomgått bevis | Grunnpoeng / BPS fra minutter |
|---|---|---:|
| Pulisic, Chelsea–West Ham 03.09.2022 | Ut 59:53, innbytter registrert 59:54; samme poengbånd ved begge tidspunkter | 1 / 3 |
| Schade, Arsenal–Brentford 03.12.2025 | Ut 59:54, innbytter registrert 59:55; samme poengbånd ved begge tidspunkter | 1 / 3 |
| Lo Celso, Palace–Spurs 26.07.2020 | Ut 59:41; alle videodekningsavbrudd kommer etter at han er ute | 1 / 3 |
| Zinchenko, Spurs–Man City 02.02.2020 | Andre gule ved 59:59, første gule dokumentert, FPL bekrefter utvisning og 59 minutter | 1 / 3 |

[Premier Leagues kamprapport](https://www.premierleague.com/en/news/1599703)
bekrefter Zinchenkos andre gule i kampens 60. minutt. Det eksakte
sekundtallet kommer fra det allerede låste hendelsesarkivet.

Dette er snevre, eksplisitt gjennomgåtte unntak fra forrige kontroll:

- Ett sekund mellom ut- og innregistrering godtas bare når kandidaten er entydig og begge klokker gir samme poengbånd. Ingen presis erstatningskobling er oppfunnet.
- Videodekningsavbrudd ignoreres bare når samtlige ligger strengt etter spillerens dokumenterte utbytte. Tidlig kampslutt er ikke et videoavbrudd.
- Andre gule krever startoppstilling, første gule, entydig utvisningshendelse og samsvar med FPL. En vanlig utbyttehendelse konstrueres ikke.

Startoppstilling, kontinuerlig deltakelse og periodegrenser kontrolleres i
alle fire tilfeller. Bevisene gjelder minuttleddet alene; kortfradrag,
øvrige BPS-komponenter og bonus er ikke omregnet her.

## Oppdatert rest og filer

**880 385 åpne poengbehov i 77 280 unike spillerkamper.** Råstatistikk-/regelresten
forblir **881 632** fordi rå minuttverdier ikke endres. Det gjenstår
**386 poengfølsomme minuttbehov: 364 regelspørsmål og 22 særtilfeller**.
De fire avklaringene telles én gang hver; tidligere keeper-/mål-/minuttillegg
bevares og telles ikke på nytt.

- `minute_component_supplement.csv`: fire godkjente komponenter med hendelses-ID-er.
- `reviewed_cases.json`: eksplisitt gjennomgåtte spillerkamper og kontrollmetode.
- `remaining_sensitive_minutes.csv`: alle 386 gjenværende grensefall.
- `resolution_queue.csv.gz`: nyeste samlede kø.
- `field_summary.csv`, `remaining_player_matches.csv.gz`, `match_summary.csv`: felt-, spillerkamp- og kamprest uten dobbelttelling.
- `manifest.json`: fingeravtrykk for lokale innganger og kode.

Kjør fra repositoryroten med pandas:

```sh
python3 research/current/scoring_2026_27/bps_minute_qualification/build.py
python3 -m unittest discover -s research/current/scoring_2026_27/bps_minute_qualification -p 'test_*.py'
```

Keeperverdier, låste poeng/BPS/bonus/modeller/benchmark og tidligere rapporter
er uendret. Ingen full BPS-/bonusberegning er godkjent. Kostnad 0 NOK.

16 nye og 64 eksisterende fokuserte tester består. Tolv data-/evidensfiler er byte-identiske ved ny kjøring. Full repositoriesuite og GitHub CI er ikke verifisert.
