# Assists: selvtatte straffer med regelkompatible historiske kontroller

**635 tomme assistkrav er lukket**, fra **11 949 til 11 314** åpne feltkrav.
**622 nye spillerkamper og 12 nye hele kamper** får komplette input. Nå har
**66 458 spillerkamper og 824 hele kamper** komplette input. Ingen ny scoring
eller trening er gjennomført.

## Nytt bevis og uendret regel

Premier League dokumenterer i [veiledningen fra august 2019](https://www.premierleague.com/en/news/827842)
og [reglene fra juli 2026](https://www.premierleague.com/en/news/2174909)
at en spiller som vinner og direkte konverterer samme straffe, ikke gir en
assist. Ordinært foul med en annen skytter følger også samme regel.
[2025-endringene](https://www.premierleague.com/en/news/4362187) gjelder andre
forløp, blant annet avbøyninger og hands, som er utenfor denne strenge ruten.

Det gir et separat, begrunnet kontrollopplegg: historiske FPL-assists er
sammenlignbare **bare for denne uendrede strafferegelen** når laget scoret
nøyaktig ett mål. Hele lagvektoren kontrolleres uten subtraksjon av andre mål
eller FPL-avledede målavgjørelser. Generelle historiske assisttotaler kopieres
aldri til target.

Den fryste fysiske [straffefoul-regelen](../penalty_foul_recovery/rule.py) og
prediksjonene er **uendret**: direkte straffemål, entydig foul-paring, eksplisitt
skytter-ID, straffe-/foulmarkører, speilede koordinater, samme klokke og ingen
mellomliggende spill/gap. Hands og returer utelukkes. De gamle 2025/26-pilotene
og deres utilstrekkelige kontrollgater beholdes uendret.

## Kontroller og utfylling

[Protokoll](protocol.json), prediksjoner og enmålsutvalg ble fryst før nye
sammenligninger. **53 mål i 764 spillerkamper** kontrolleres: **41 ordinære
straffer og 12 selvtatte**, fra alle syv historiske sesonger, inkludert seks
2025/26-mål. Ingen kontrollavvik, konflikter med godkjente avgjørelser eller
kandidatvetoer. Minimum 20 mål totalt og fem per beslutningstype beholdes.
Dette er historisk regresjon med delt Opta-opphav og tidligere sett fasit,
**ikke uavhengig holdout** eller kontroll av andre assistdefinisjoner.

**53 uløste selvtatte straffemål** får dokumentert «ingen assist». Ordinære
avgjørelser var allerede kjent. Alle målbidrag summeres med eksisterende
aggregator; ukjente bidrag fra andre mål forblir ukjente. 635 hele totaler
avklares: **604 nuller og 31 positive**. De positive summene kommer fra
allerede kjente bidrag ved andre mål. Fordeling: 97 i 2019/20, 139 i 2020/21,
135 i 2021/22, 109 i 2022/23, 96 i 2023/24 og 59 i 2024/25.

**67 354 tidligere komplette assisttotaler**, **774 613 andre ledger-rader**
og alle opprinnelige kildekolonner bevares. Nye felter beholder kvalitetsflagg.
Ledgeren kaller de tomme targetkravene `rule_recalculation` eller
`missing_data`. [Anvendelsesprotokollen](application_protocol.json) presiserer
før utfylling at begge er åpne, tomme rekonstruksjoner. Den korrigerer
statusbetegnelsen i første anvendelsesbeskrivelse; regel, utvalg, kontrollfasit
og akseptkrav er uendret. Ingen fylt, lukket eller beskyttet verdi overskrives.

## Reproduksjon og rest

Fra denne mappen:

```bash
python -m unittest -v test_penalties.py
python reproduce.py
```

Syv tester består. **14 resultatfiler**, fryste prediksjoner, kontrollplan og
anvendelsesfrys gjenskapes byteidentisk i isolert offline-replay, uten nettverk,
store råarkiver eller bootstrap. Se [kontroller](results/validation.json),
[dekning og resultater](results/findings.json), [innganger](inputs/manifest.json),
[publikasjonsmanifest](publication_manifest.json) og [reproduksjonsbevis](reproduction_verification.json).
[CURRENT.json](../../CURRENT.json) velger gjeldende rest og assisttotaler.

**9 291 assistkrav gjenstår**, med 1 238 times tackled, 545 CBI,
48 mållinjeklareringer og mindre grupper. Samlet kvalitet, scoring og fristsikre
features gjenstår. Datasettet er ikke treningsklart.
