# Uttrekk og kvalitetskontroll av nødvendige eksterne felt

7. oktober 2026. Punkt 1 og 2 i arbeidsrekkefølgen er gjennomført som et
reproduserbart uttrekk og en kildekontroll. **Dette er gjeldende restliste.**
Den viderefører kildepolitikken i `../fpl_authority/`: kompatible historiske
FPL-verdier er fasiten. Ingen FPL-verdier, keepergodkjenninger, låste
poeng/BPS/bonus, modeller eller benchmark er endret.

## Resultat

| Felt | Åpent før | Åpent nå | Tidligere åpne felt gjort tilgjengelige |
|---|---:|---:|---:|
| Antall ganger taklet | 76 935 | 9 504 | 67 431 |
| Gammel netto taklingsteller | 65 788 | 38 090 | 27 698 |
| Redninger utenfor boksen | 764 | 342 | 422 |
| **Sum nye tilgjengelige feltkrav** | | | **95 551** |

I tillegg flagges 17 tidligere tilgjengelige taklingsfelt som kildekonflikter.
Samlet: **363 517 − 95 551 + 17 = 267 983 åpne feltkrav**,
i **66 109 unike spillerkamper**. Åpne krav er 219 032 manglende verdier,
234 eksterne konflikter, 48 716 assistomregninger og ett kjent
FPL-uttrekksunntak. Dette er ikke antall FPL-feil.

**1 240 nødvendige eksterne feltverdier har eksplisitt samsvar med
Premier League-kontroller.** 339 783 tilgjengelige verdier i 77 125
spillerkamper har gjennomgått den automatiske kilde-/formatkontrollen,
men er ikke individuelt bekreftet mot primærkilden. Disse står separat
fra manglende data. Unionen av åpne krav og sistnevnte kvalitetskø
berører 77 215 spillerkamper, uten dobbelttelling.

At et felt er tilgjengelig eller kontrollert mot primærkilden betyr ikke at
en komplett poengberegning er godkjent. Arkiv og Premier League har felles
Opta-opphav. Dette er ikke uavhengig leverandørvalidering eller en ny
holdout for scoringsmotoren.

## Punkt 1: definisjoner og uttrekk

Det eksisterende spillerstatistikkarkivet ble hentet på nytt og matchet den
låste SHA-256-kontrollsummen `2765b1771493c917ce7c544b01cf3a151e159a818abb889c7fcbd746353eaead`.
Alle 288 kolonner ble inventert. Femten relevante råtellere ble projisert for
77 902 spillerkamper, inklusive 622 eksisterende 2026/27-kontroller.
Historisk er fortsatt 76 687/77 280 koblet; 593 observasjoner i 21 kamper
mangler i arkivet. Ingen ny navnegjetting eller minuttbasert kobling er brukt.
Spiller-/kampnøkler, lag, dato og sesong er kontrollert mot eksisterende koblinger;
alle tidligere overlappende felt er identiske med det forrige uttrekket.

- `timesTackled` finnes direkte, med mange **eksplisitte nuller**. Det er ikke
  beregnet fra balltap eller mislykkede driblinger. Det mangler særlig i 2019/20;
  senere sesonger har telleren for alle koblede aktive arkivrader.
- `savedObox` finnes direkte. Det er ikke beregnet som FPL-redninger minus
  redninger innenfor boksen. Det finnes ingen eksplisitte nuller i dette arkivfeltet.
- Det finnes ingen egen netto taklingsteller. Opta definerer vunnet/tapt takling
  etter hvem som får ballen etter en lovlig takling. Når begge råtellerne er
  eksplisitte og gyldige, er den **signerte råtelleren**
  `wonTackle − (totalTackle − wonTackle)`. `challengeLost` er ikke samme begrep.
  Null eller negativt resultat fra denne differansen beholdes som beregnet verdi;
  manglende inngang blir fortsatt manglende resultat.

Dette dokumenteres med [Optas definisjoner](https://www.statsperform.com/opta-event-definitions/)
og [PLs beskrivelse av endringen i 2025/26](https://www.premierleague.com/en/news/4362127/whats-new-in-202526-fantasy-changes-to-bonus-points-system).
En tidligere [offisiell Kanté-kontroll](https://www.premierleague.com/en/news/661215)
oppgir netto 3; arkivet har total 3, vunnet 3 og `challengeLost=1`, som
understøtter dette skillet. Samme artikkels ballgjenvinninger avviker fra arkivet,
så eksempelet er ikke full validering av alle kampens tellere.

**Hvordan negativ nettoverdi ble behandlet i gammel BPS, er ikke kvalifisert
her.** Råtelleren er skilt fra BPS-komponenten. Ingen klipping til null eller
negativ BPS antas før sesongformelen er kontrollert. Regelen om å bruke FPL-BPS
som grunnlag krever dessuten at eksterne revisjoner stemmer med komponenten
som trekkes fra; en ferskere teller er ikke automatisk den gamle FPL-telleren.
Se [definitions.json](definitions.json).

## Punkt 2: kontrollene og funnene

**Alle projiserte tellere:** format, heltall, ikke-negative innganger,
spiller-/kampidentitet og kildeomfang kontrolleres. Tomme felt skilles fra null.
Ingen generelle nullutfyllinger eller xG-imputering er gjort.

**28 nye, forhåndsvalgte kontroller:** fire observasjoner per historisk sesong,
med eksplisitt null/positivt antall ganger taklet, mållinjeklarering og redning
utenfor boksen. Planen ble lagret før innhenting og utelukker tidligere
kontroller. Alle **160 eksplisitte sammenligninger stemmer**. De øvrige 260
feltparene mangler i begge kilder og er ikke bekreftede nuller. Utvalget er
målrettet for felttyper, ikke et tilfeldig estimat for hele datasettet.

**Eksisterende primærkontroller:** sammenlignes på nytt for de femten feltene.
Eksplisitte avvik og forskjeller i utelatte felt er lagret separat i
`primary_disagreements.csv`. Samsvar mellom kilder med felles Opta-opphav
begrunnes ikke som uavhengig bekreftelse.

**Hendelsesarkivet:** kontrollsummer er bevart. 43 458/43 474 sammenlignbare
positive total-taklingsteller og 32 707/32 718 vunnet-taklingsteller stemmer.
Avvik i hendelses- og aggregattellinger er bevart og berørte krav står åpne.
Hendelseskodene støttes av den tidligere låste parserordboken; denne er ikke
en leverandørsertifisert komplett beskrivelse av rapporteringspraksis.

**Mållinjeklareringer:** alle 576 historiske sammenlignbare positive verdier
stemmer med hendelsesmarkøren (583 inkludert nåværende kontroller). 64 123
historiske rader har tom statistikkteller og null kandidatmarkører i
hendelsesuttrekket. **Ingen av disse er automatisk godkjent som null.**
Samsvar på positive hendelser beviser ikke fullstendig negativ rapportering;
noen kamper mangler hendelser og andre tellere viser revisjonsforskjeller.
65 301 nødvendige mållinjefelt står derfor fortsatt åpne.

**FPL 2025/26:** 17 413 eksplisitte sammenligninger av taklinger,
ballgjenvinninger, redninger og komplette CBI-summer stemmer, mens 247 avviker.
28 308 feltpar har en manglende side. Dette er en kontroll av eksterne
statistikker; **FPL beholdes uansett**, og avvikene er ikke lagt inn som nye
FPL-restmangler. Bare CBI-rader med alle tre arkivkomponenter teller som
komplette summer; manglende komponenter er aldri summert som null.

**Offisielle sesongsummer:** 13 av 16 publiserte 2025/26-totaler for antall
ganger taklet stemmer med arkivets kampverdier. For Bowen og Ndiaye støtter
nåværende PL-API arkivets total, én lavere enn den publiserte artikkelen.
For Doku stemmer API-totalen med artikkelen, én høyere enn arkivet.
En målrettet kontroll av alle hans 30 opptredener lokaliserer forskjellen
til **2025/26 kamp 356: arkiv 4, PL 5**. Dette feltet står som en konkret
kildekonflikt, ikke som 30 ukjente felt eller en gjetning om BPS-korreksjon.
Disse 30 kontrollene er oppfølging av et funn, ikke en forhåndsvalgt holdout.
Se [sesongavstemming](official_season_comparisons.csv) og
[offisiell kilde](https://www.premierleague.com/en/news/4679946/).

## Gjeldende restliste

| Felt | Åpne krav |
|---|---:|
| Mållinjeklareringer | 65 301 |
| Assists etter målreglene | 48 716 |
| Gammel netto taklingsteller | 38 090 |
| Vunne taklinger | 38 087 |
| Frispark vunnet | 30 049 |
| Skudd på mål | 28 590 |
| Antall ganger taklet | 9 504 |
| CBI | 4 818 |
| Straffemål | 4 435 |
| Redninger utenfor boksen | 342 |
| Storsjanseredninger | 38 |
| Totale taklinger | 11 |
| Ballgjenvinninger | 1 |
| Kjent FPL-uttrekksunntak | 1 |
| **Sum** | **267 983** |

De godkjente mål-/selvmålsrettelsene og de tolv separate hendelsesavhengighetene
i `../fpl_authority/official_event_review.csv` er uendret. Keeperstatus er fortsatt
5 343 godkjente og 38 uløste. Assists er ikke omberegnet i denne fasen.

## Filer og gjentakelse

- `requirements.csv.gz`: gjeldende behov, med tidligere verdi/status,
  ny arkivverdi, primærkontroll, valgt verdi/status og kontrollnivå.
- `remaining_fields.csv.gz`: åpne data-/regelkrav.
- `external_quality_queue.csv.gz`: tilgjengelige, men ikke individuelt
  primærbekreftede verdier. De har gjennomgått kilde-/formatkontroll.
- `primary_checked_values.csv.gz`: nødvendige verdier som eksplisitt stemmer med PL.
- `field_summary.csv`, `field_summary_by_season.csv`, `player_summary.csv`,
  `match_summary.csv`, `remaining_player_matches.csv.gz`: dedupliserte oppsummeringer.
- `all_work_player_matches.csv.gz`: union av åpne krav og videre kvalitetsbehov.
- `field_coverage.csv`: eksplisitte nuller, positive verdier og utelatelser per sesong.
- `primary_comparisons.csv.gz`, `event_comparisons.csv.gz`,
  `fpl_2025_comparisons.csv.gz`: fullstendige sammenligninger, med separate avvik.
- `control_plan.csv`, `control_protocol.json`, `definitions.json`: utvalg og grunnlag.
- `manifest.json`, `primary_sources.json`, `season_check_sources.json`,
  `targeted_sources.json`: kontrollsummer og kildelenker. Råsvar er bevart i `inputs/`.

Fra denne mappen, med pandas: `python build.py` og
`python -m unittest test_audit.py`. Bygg og tester bruker bare lagrede innganger.
For å gjenta Parquet-uttrekkene med pyarrow: `python prepare.py --archive PATH`
og `python prepare_events.py --archive PATH`, med de opprinnelige hash-låste
arkivene. Innhentingsskriptene gjenbruker lagrede svar og stopper ved feil;
ikke erstatt et arkiv med en ny release uten separat vurdering.

Validering: 15 nye og 104 eksisterende fokuserte tester består. 25 resultatfiler
er byte-identiske ved ny kjøring. Hele repositoryets testsuite og GitHub CI
er ikke verifisert; se [validation.json](validation.json).

Kostnad 0 NOK. Nye komplette poeng/BPS/bonus er ikke produsert.
Punkt 3 (assistberegning) og punkt 4 (videre innhenting/full omregning) er ikke
påbegynt som del av denne leveransen.
