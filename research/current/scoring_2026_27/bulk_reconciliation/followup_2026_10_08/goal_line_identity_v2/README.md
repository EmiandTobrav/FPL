# Mållinjeklareringer med kontrollert ettminuttsavvik

Denne datagapbatchen lukker **527 krav**, fra **12 476 til 11 949**.
**390 nye spillerkamper og 44 nye hele kamper** får komplette input.
Gjeldende dekning er **65 836 spillerkamper og 812 hele kamper**.
Ingen nye BPS-, bonus- eller poengetiketter beregnes.

## Kilde og avgrenset regel

Regelen teller de samme faktiske blokkhendelsene som den fryste
[v1](../goal_line_events/README.md): type 10 med eksplisitt defensiv blokk
(94) og mållinjemarkør (14). Komplett spillerinventar må avstemmes mot et
uttrykkelig blokktall, eller komplett laginventar mot primærens kamptotal.
Alle tidligere kontroller av aktører, markører og blokktellere beholdes.

Nytt bevis er et kompakt uttrekk av **2 639 faktiske kamper** fra det allerede
innhentede, hashfestede Opta-arkivet. Sesong, dato, hjemme-/bortelag,
lagidentitet og sluttresultat kontrolleres mot historisk FPL. Spillerens
FPL-kode må peke entydig til samme kilde-ID på tvers av kamper, med minst to
andre identitetsankre der kildens og FPLs minutter er like.

Denne versjonen kvalifiserer bare **hele kampens mållinjeteller** ved nøyaktig
ett minutts varighetsforskjell. FPL-minuttene beholdes. Unntaket gjelder ikke
CBI, keeperlokasjon, BPS eller andre gamle minuttgater. V1 og alle tidligere
poeng- og kontrollversjoner er uendret.

Protokoll, innganger og prediksjoner ble fryst før godkjente mållinjeverdier
ble sammenlignet i denne versjonen. Det finnes **62 166** prediksjoner med
nødvendig identitet og blokkinventar. Eksakte minutter inngår i regresjonen;
kun ettminuttsgruppen kan gi nye utfyllinger.

## Kontroller og utfyllinger

**59 534 tidligere lukkede kontrollverdier og 574 eksplisitte positive
kildeverdier stemmer uten avvik**; 478 nøkler overlapper. Gruppen med ett
minutts forskjell har **12 667 lukkede kontroller og 83 positive
kildekontroller**, uten avvik. Alle seks anvendte historiske sesonger har
minst 100 kontroller i denne gruppen. De opprinnelige minimumskravene per
sesong og for 2025/26 beholdes; de nye gruppegatene ble satt før sammenligning.

Kontrollene deler Opta-opphav og tidligere sett utviklingsbevis. Dette er
kildekompatibilitet og regresjon, **ikke uavhengig holdout eller native
FPL-observasjoner av mållinjeklareringer**. Samlet kvalitetssikring gjenstår.

Alle 527 nye tellinger er dokumenterte nuller: 134 i 2019/20, 153 i 2020/21,
115 i 2021/22, 11 i 2022/23 og 114 i 2024/25. 487 har kildeminutter én høyere
enn FPL, 40 én lavere. **774 721 øvrige ledger-rader og alle opprinnelige
kilde-/tidligere-verdi-kolonner for 775 248 rader er bevart**. Nye verdier
beholder flagget for senere kollektiv kvalitetssikring.

**48 mållinjekrav gjenstår:** 39 arkiv-/identitetsgap og ni varighetsavvik
større enn ett minutt (seks på +2, ett på −2, ett på −7 og ett på −11).
Disse er fortsatt åpne; manglende hendelser og større avvik blir ikke null.
Den store resten er assists (9 926), times tackled (1 238) og CBI (545).

## Reproduksjon

Fra denne mappen:

```bash
python -m unittest -v test_goal_line_identity.py
python reproduce.py
```

Syv tester består, inkludert feil kamp/lag/resultat/spilleridentitet,
utilstrekkelige identitetsankre, manglende/ufullstendig blokkinventar,
hele ledgerens bevaring og korrekt inputdekning. Isolert offline-replay
sammenligner hver resultatfil og fryste prediksjoner byte for byte.
Det trenger ingen ny nettinnhenting, rå parquet eller bootstrap.

For å gjenskape bare kildeuttrekket fra det samme arkivet:

```bash
python prepare.py /path/to/opta_fixtures.parquet
```

[Protokoll](protocol.json), [kildefiler og hashverdier](inputs/manifest.json),
[prediksjonsfrys](prediction_freeze.json), [resultater](results/findings.json)
og [reproduksjonsbevis](reproduction_verification.json) dokumenterer batchen.
Gjeldende restliste velges gjennom [CURRENT.json](../../CURRENT.json).
Inputkompletthet er ikke treningsklarhet; scoring, samlet kvalitet og
fristsikre features gjenstår.
