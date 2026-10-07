# Endelige offisielle målrettinger og første minuttavklaring

> **Superseded as the current work queue:** see [FPL-authoritative ledger](../fpl_authority/README.md). Historical diagnostics and approved evidence below are retained; provider differences do not override compatible FPL values.

7. oktober 2026, videreført fra `4883ccc` på PR #1.
Brukeren har uttrykkelig valgt **endelig korrigerte offisielle hendelser,
omregnet etter 2026/27-reglene**, som fasit for det nye datasettet. Dette er
retrospektiv harmonisering; vi gjenskaper ikke den gamle FPL-låsefristen.
Historiske FPL-rader og tidligere rapporter bevares som egne kildeversjoner.

## Fire målkonflikter avklart, åtte tellerverdier korrigert

| Kamp | Endelig måltilordning | Selvmål fjernet | Offisiell avgjørelse |
|---|---|---|---|
| Man Utd–Brighton 10.11.2019 | McTominay 0 → 1 | Pröpper 1 → 0 | [13.11.2019](https://www.premierleague.com/en/news/1494715) |
| Leeds–Brighton 11.03.2023 | March 0 → 1 | Harrison 1 → 0 | [15.03.2023](https://www.premierleague.com/en/news/3110528) |
| Arsenal–Palace 20.01.2024 | Gabriel 1 → 2 | Henderson 1 → 0 | [26.01.2024](https://www.premierleague.com/en/news/3868439) |
| Brentford–Ipswich 26.10.2024 | Wissa 1 → 2 | Harry Clarke 1 → 0 | [29.10.2024](https://www.premierleague.com/en/news/4159875) |

Alle fire omgjøringene er kontrollert mot Premier Leagues egne avgjørelser,
stabile spillerkoder, reviderte målhendelser og offisielt sluttresultat.
En ensidig endring av målscorer ville gi ett ekstra mål i hver kamp.
`goal_balance_audit.csv` demonstrerer feilen og kontrollerer begge lagenes
målsummer etter parvis retting. De fire selvmålsnullene er dokumenterte
omgjøringer av eksplisitte ettall; de kommer **ikke** fra tomme arkivfelt.

`counter_supplement.csv` er et separat, godkjent retrospektivt tillegg med
åtte felt i åtte unike spillerkamper. Fire tidligere åpne målkonflikter
lukkes. De fire selvmålene var tidligere registrert som dokumenterte
historiske verdier, ikke som åpne konflikter; derfor faller resttallet med
fire, ikke åtte. Rå kildeuenighet bevares for sporbarhet.

Assists er fortsatt uavklart etter målreglene. Maguire, Saka og Damsgaard
har reviderte ordinære assistkandidater; March-hendelsen har ingen slik
kandidat i denne kontrollen. Dette beviser verken nye komplette assisttotaler
eller null assists for noen spiller. Historiske assisttotaler for
McTominay, Gabriel og Wissa må ikke videreføres automatisk til den omgjorte
scoringen. `affected_source_values.csv` viser de elleve berørte spillerrollene
med historiske og reviderte kildeverdier, med tomme målregel-assists.

`event_dependencies.csv` har tolv kontroller knyttet til fire hendelser:
assists, skudd på mål og kampvinnende mål. Disse er **avhengighetskontroller**,
ikke tolv nye manglende felt eller ferdige poengberegninger. Særlig må
målspesifikke assistbevis skilles fra komplette spillerkamptotaler.

## Ferguson: minuttpoeng bevist, eksakt minuttall fortsatt åpent

Brightons [egen kamprapport](https://www.brightonandhovealbion.com/media-article/albion-concede-seven-against-nottingham-forest)
for Forest–Brighton 01.02.2025 oppgir Ferguson som innbytter for Welbeck ved
72 minutter. Det avviser FPL-uttrekkets null minutter for spillerkode
487117, kamp 239. FotMob og arkivet oppgir begge 17 minutter. Kamprapporten
brukes ikke til å avgjøre avrundingen mellom hele minutters spilletid.

Innbyttet beviser intervallet 1–59 ordinære minutter og dermed **1 grunnpoeng
og 3 BPS i minuttkomponenten**. Eksakt minuttall forblir ukjent i tillegget.
Dette er ikke en ny komplett poengsum eller ny bonus. Av de opprinnelige
711 poengfølsomme minuttkonfliktene er denne komponenten nå avklart; 710
gjenstår. De 16 649 tidligere kandidatnøytrale avvikene er fortsatt råkonflikter.

## Oppdatert restliste uten dobbelttelling

| Behov | Etter denne kontrollen |
|---|---:|
| Åpne poengbehov | 880 709 |
| Åpne råstatistikk-/regelbehov | 881 632 |
| Unike spillerkamper med åpne poengbehov | 77 280 |
| Nye avklarte poengbehov | 5 |
| Nye eksakte minuttall | 0 |

Dette viderefører `resolution_priority/`: fire målkonflikter og én
minuttkomponent er avklart. Råresten faller bare med fire. De 922 tidligere
poengirrelevante GK/DEF-straffemålsfordelingene er fortsatt ukjente.
Feltantall må ikke summeres som om de var unike spillerkamper.

- `resolution_queue.csv.gz`: hele tidligere kø med beslutningsstatus og tiltak oppdatert.
- `field_summary.csv`: rest per felt, fordelt på manglende data, kildekonflikt og uavklart regelberegning.
- `remaining_player_matches.csv.gz`: én rad per fortsatt berørt spillerkamp med alle åpne felt.
- `match_summary.csv`: antall feltbehov og unike berørte spillere per kamp.
- `decisions.json`: eksplisitt kildepolitikk, manuelle evidensreferater og kilder.
- `manifest.json`: SHA-256 for alle lokale byggeinnganger, regelsett og keeperkontroll.

Tidligere restlister er historiske øyeblikksbilder; bruk denne køen som neste
arbeidsgrunnlag og anvend teller-/minuttilleggene eksplisitt. Byggeren er
offline og leser de manuelt kontrollerte kildereferatene; den hevder ikke
å automatisk tolke eller gjenverifisere nettartikler.

Neste arbeid: de 710 gjenværende poengfølsomme minuttkonfliktene, deretter
øvrige tellerkonflikter og målregel-assists. Beskytt nullbevis og ikke
behandle sjeldne utelatte arkivtellere som null. 38 storsjanseredninger,
593 spillerkamper uten supplerende arkiv og hendelseshullene er uendret.
Keeperverdier, låste poeng/BPS/bonus/modeller/benchmark er uendret.
Ingen nye fullstendige BPS-/bonusetiketter og ingen ny holdout. Kostnad 0 NOK.

## Reproduserbar kontroll

Kjør fra repositoryroten med Python/pandas:

```sh
python3 research/current/scoring_2026_27/official_revision/build.py
python3 -m unittest discover -s research/current/scoring_2026_27/official_revision -p 'test_*.py'
```

Testene kontrollerer parvis retting, avvisning av manglende verdier og dobbel
anvendelse, lagtilhørighet, målsummer, minuttgrenser, assistavgrensning,
unik opptelling og inngangenes fingeravtrykk.

12 nye og 36 eksisterende fokuserte tester består. To bygg gir byte-identiske resultatfiler.
