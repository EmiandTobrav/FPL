# Gjeldende restliste: FPL som fasit

Oppdatert 7. oktober 2026. Denne listen **erstatter** arbeidskøene i
`remaining_ledger/`, `resolution_priority/`, `official_revision/`,
`minute_reconciliation/` og `bps_minute_qualification/`. Tidligere køer beholdes
som historikk, ikke som gjeldende feil- eller mangeltall.

## Kildeprioritering og metode

Historiske FPL-verdier er fasiten når definisjonen kan videreføres til 2026/27.
En annen minuttverdi eller et flertall eksterne kilder overstyrer ikke FPL.
Null fra FPL er en verdi. Et tomt felt hos en ekstern kilde er ikke null.
Eksterne data brukes til manglende/nye statistikker og dokumentert regelomregning.
Alle 77 280 FPL-minuttverdier beholdes. Ingen minuttforskjeller er restkrav.

Historisk FPL-BPS brukes som grunnlag: trekk fra gamle bidrag og legg til nye
**bare for endrede regelledd**. Uendrede minutt-, pasnings-, kort-, sjanse- og
andre bidrag er allerede med i FPL-BPS og skal ikke rekonstrueres fra ufullstendige
arkiver. Historisk bonus og totalpoeng er referanser, ikke ferdige 2026/27-etiketter.
Bonus må rangeres på nytt for hele kampen etter omregning av BPS; totalpoeng må
justeres for endrede grunnpoeng og ny bonus.

Dette er en **avhengighets- og arbeidsliste**, ikke en ferdig kvalifisert
omregningsmotor. Sesongkoeffisienter, heltalls-/klipperegler og sammenlignbarhet
mellom gamle FPL-bidrag og eksterne tellere må godkjennes før nye etiketter lages.
Se [regelgrunnlag og globale kontrollpunkter](rule_dependencies.json).

## Resultat

| Kategori | Feltkrav | Unike spillerkamper |
|---|---:|---:|
| Åpne data-/regelkrav samlet | 363 517 | 77 248 |
| Eksterne verdier tilgjengelige, separat kvalitetskø | 245 489 | 66 584 |
| Union av begge arbeidskøene | 609 006 | 77 280 |

De åpne kravene består av **314 595 manglende verdier**, **205 eksterne
kildekonflikter**, **48 716 assistomregninger** og **ett kjent FPL-uttrekksunntak**.
Dette er ikke 363 517 feil i FPL. En spillerkamp kan ha mange feltkrav;
unikantallene over er deduplisert på sesong, kamp og spillerkode. Ikke summer
unikantall på tvers av felt eller køer.

Totalt krever metoden 775 248 feltceller. I tillegg til de åpne og eksterne
kvalitetskravene er 143 827 dekket direkte av FPL, 17 072 av dokumenterte
nullgrenser og 5 343 av godkjente keeperrekonstruksjoner. De 38 uløste
storsjanseredningene står fortsatt åpne. Ingen xG-imputering.

| Felt | Åpne krav |
|---|---:|
| Antall ganger taklet (`times_tackled`) | 76 935 |
| Gammel netto taklingsteller (`legacy_net_tackles`) | 65 788 |
| Klareringer på mållinjen | 65 301 |
| Assists etter målreglene | 48 716 |
| Vunne taklinger | 38 081 |
| Frispark vunnet | 30 049 |
| Skudd på mål | 28 590 |
| Klareringer + blokkeringer + interceptions | 4 818 |
| Straffemål | 4 435 |
| Redninger utenfor boksen | 764 |
| Storsjanseredninger | 38 |
| Ballgjenvinninger | 1 |
| Kjent FPL-uttrekksunntak | 1 |

For hvert felt tilsvarer antallet åpne krav antallet unike berørte spillerkamper
for akkurat dette feltet. Nulltelling i feltoppsummeringene er en **overlappende
verdiegenskap**, ikke en ekstra statuskategori.

`times_tackled`, `legacy_net_tackles` og `saved_obox` er ikke fullstendig hentet ut
av eksisterende råarkiver. «Mangler» betyr utilgjengelig i de gjennomgåtte
uttrekkene, ikke bevist fravær hos alle kilder. Netto taklinger skal ikke gjettes
fra totalt antall taklinger; antall ganger taklet skal ikke imputeres fra
balltap/driblinger. At FPL-totaler er kjent, gir ikke automatisk null for deltellere.

## Sesongavhengigheter

- Alle historiske sesonger: endret CBI-vekt, fjerne fratrekket for å bli taklet,
  keepernes nye redningsledd og historisk BPS som grunnlag.
- Før 2025/26: gammel/ny taklingskomponent, mållinjeklareringer, straffemålenes
  BPS for MID/FWD, nye defensive bidrag og assistreglene. Keepernes redningssted
  må også være kjent. Straffemålsplitt kreves bare ved positive/ukjente mål.
- Før 2024/25: nye BPS-ledd for skudd på mål, frispark vunnet og baklengsmål for
  GK/DEF. Keepermål må justeres fra gammel grunnpoengverdi.
- 2025/26: FPL-assists og defensive bidrag kan videreføres under samme regler.
  Keepere trenger både den gamle innenfor- og utenfor-boksen-komponenten;
  summen antas ikke automatisk å være identisk med FPL-redninger.

Regelendringene er dokumentert i offisielle PL-kilder lenket fra
[rule_dependencies.json](rule_dependencies.json). Uendrede råstatistikker og
historiske BPS/bonus/totalpoeng finnes i [FPL-grunnlaget](fpl_baseline.csv.gz).

## Godkjente unntak og separate kontrollpunkter

De fire tidligere godkjente offisielle målomgjøringene er bevart som åtte
mål-/selvmålsrettelser i den avledede visningen. FPL-originalene er uendret.
[Hendelseskontrollen](official_event_review.csv) viderefører tolv avhengigheter
for assists, skudd og vinnermål. Dette er hendelsesrettelser som må behandles
samlet før poengberegning, ikke tolv ekstra manglende spillerkamptotaler.
Tidligere målspesifikke assistbevis i `assist_rules/` og `assist_schema/` beholdes;
et bevis for ett mål fastsetter ikke automatisk spillerens assisttotal i kampen.

Ferguson, 2024/25 kamp 239: det tidligere dokumenterte deltakelsesavviket
beholdes som ett uttrekksunntak for FPL-BPS-grunnlaget. Originalt FPL-minutt 0
står urørt; ingen gjetning på 17 minutter er brukt. Dette unntaket gir ingen
hjemmel til generelt å erstatte FPL med eksterne minutter.

## Filer og etterprøving

- `policy.json`: eksplisitt kildehierarki og bevaringsregler.
- `requirements.csv.gz`: ett nødvendig felt per spillerkamp, alle kildeverdier,
  valgt verdi, status, proveniens og spiller-/kampidentitet.
- `remaining_fields.csv.gz`: bare åpne data-/regelkrav.
- `external_quality_queue.csv.gz`: tilgjengelige eksterne verdier, separat kvalitetssjekk.
- `field_summary.csv`, `field_summary_by_season.csv`: behov per felt og sesong.
- `remaining_player_matches.csv.gz`, `player_summary.csv`, `match_summary.csv`:
  åpne behov per spillerkamp, spiller og kamp.
- `all_work_player_matches.csv.gz`: deduplisert union, med antall åpne og eksterne kvalitetskrav.
- `authoritative_values.csv.gz`: valgt råstatistikk med bevarte FPL-verdier og
  eksplisitte offisielle unntak; ikke ferdige harmoniserte poeng.
- `fpl_external_differences_not_blockers.csv.gz`: kildeforskjeller til informasjon,
  ikke automatisk FPL-feil eller arbeidskrav.
- `reclassification_summary.csv`: avstemming mot forrige kø. Reduksjonen fra
  880 385 skyldes metode/kildeprioritet, ikke tilsvarende ny datainnsamling.
  Av de gamle kravene faller 651 527 utenfor nødvendig sesong-/komponentscope,
  8 829 er ikke lenger åpne med FPL-prioritet, og 220 029 står fortsatt åpne.
  143 488 nye krav til delta-tellere gir samlet 363 517. Disse nye kravene er
  ikke nye feil i FPL; de trengs for å fjerne/endre gamle BPS-komponenter.
- `manifest.json`: SHA-256 for alle innganger. Kildedata, godkjente keeperverdier,
  låste poeng/BPS/bonus, modeller og benchmark er ikke endret.

Validering: 16 nye og 80 eksisterende fokuserte tester består. 17 resultat-/manifestfiler
er byte-identiske ved ny kjøring. Hele repositoryets testsuite og GitHub CI er ikke
verifisert; se [validation.json](validation.json).

Kjør `python build.py` og `python -m unittest test_authority.py` fra denne mappen
med pandas tilgjengelig. Ingen nettverk eller nye kjøp kreves. Kostnad: 0 NOK.

Neste arbeid: hent ut de nye delta-tellerne fra råarkivene, kvalifiser
gamle/nyere komponentdefinisjoner mot offisielle FPL-kontroller, og behandle
manglende eksterne data og assistregler. Ingen generell minuttjakt.
