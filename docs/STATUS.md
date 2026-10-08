# Fortsett her

Oppdatert 8. oktober 2026. Brukeren ønsker GitHub som sentral for kode og fremgang på tvers av enheter. Denne mappen og repositoryet skal være tilstrekkelig kontekst uten den gamle samtalen eller ZIP-filene.

## Gjeldende kø og gjennomføringsplan – 8. oktober 2026, batch 3

**16 227 åpne feltkrav i 14 990 unike spillerkamper.**
**62 290 spillerkamper og 490 hele kamper har komplette inputfelt**, av
77 280 og 2 660. Dette er inputtilgjengelighet, ikke ferdig harmoniserte poeng.

Siste batch lukket **8 058 krav (33,18 % av 24 285)**, alle innen target-assists.
7 506 nye spillerkamper og én ny hel kamp er inputkomplette. Assists gjenstår i
9 926 spillerkamper. Positive hendelsesgrenser avklarer tidligere kandidater,
men mange faktiske gjenværende målbidrag er fortsatt usikre. Ingen nye mål-assists
er tildelt; 367 nye positive kampverdier består av tidligere kvalifiserte awards
og nye sikre nullbidrag fra andre mål. 7 691 nye verdier er null med belegg.

[Gjeldende restliste](../research/current/scoring_2026_27/bulk_reconciliation/README.md),
[CURRENT](../research/current/scoring_2026_27/bulk_reconciliation/CURRENT.json),
[arbeidsrekkefølge](../research/current/scoring_2026_27/bulk_reconciliation/WORK_ORDER.md).
Nå prioriteres straffe-/dødballårsak med ny tilstrekkelig kontroll, resterende
pasningsforløp med stor kampgevinst, dokumentert nye mållinjekilder og øvrige
felles årsaksgrupper. De nye kandidatreglene er allerede kjørt over hele populasjonen.

Hver ny rute bestod sine frosne kontrollgater. Samlet kontroll av snittet mellom
alle gamle og nye kvalifiserte kandidatsett, med tidligere awards tvunget inn,
bestod for 566 lagvektorer i 353 kamper. Dette er tidsordnet regresjon med tidligere
sett fasit og delt Opta-kilde, ikke uavhengig holdout. 15 nye testmetoder bestod;
63 resultatfiler ble gjenskapt identisk i separat offline reproduksjon. Full repo-/CI-
test er ikke bekreftet. Ny SDP-kildepilot ga ikke de manglende numeriske feltene.

581 858 kvalitetsflagg er samlet i 73 felt-/sesonggrupper. Rå FPL, godkjente
keeperverdier, offisielle rettelser, eldre frosne filer og låste poeng/BPS/bonus/
modeller/benchmark er bevart. Ingen scoring, trening eller main-merge. Internt
`published=false` i kjørerresultater beskriver lokal kjøring før publisering.

## Historikk: masseavklaring fra eksplisitte totaler – 8. oktober 2026

**Tidligere restliste: [bulk_reconciliation/](../research/current/scoring_2026_27/bulk_reconciliation/README.md).**
Arbeidsrekkefølgen med store feltgrupper  liten kildeprøve  masseberegning og
måling av komplette spillerkamper/kamper er gjennomført.

**138 522 feltkrav er gjort tilgjengelige (53.6 % av forrige rest).**
Ny rest: **119 780 feltkrav i 63 882 unike spillerkamper**.
Taklinger  frispark vunnet  skudd på mål og mållinjeklareringer avledes bare fra
eksplisitte foreldreverdier eller komplette summer mot offisielle lagtotaler.
Tom lagtotal  positiv restsum eller kildeavvik gir ingen automatisk null.
Gammel netto taklingsteller beholdes signert; BPS-klipping er fortsatt uavklart.

2 280 offisielle kampsvar er hentet for 2019/20–2024/25. Tolv små prøvekampers
resultater ble bekreftet på tolv separat valgte senere kamper: 194 eksplisitte
lag-/feltsammenligninger stemmer  ingen avvik. Dette er kontroll av summer og
feltdefinisjoner  ikke et estimat for individuell spillerpresisjon eller en
uavhengig Opta-leverandørtest. Hver eneste lag-/feltgruppe kontrolleres før bruk.
Tre moteksempler avviser en snarvei for mållinjeklareringer fra klareringer og
blokkeringer. Normaliserte nuller fra et alternativt arkiv er heller ikke brukt.

**2 205 nye spillerkamper har komplett tallgrunnlag**  totalt 13 398.
**0 nye kamper har komplett tallgrunnlag**  totalt 119.
Dette er tilgjengelige innganger  ikke nye godkjente poeng-/BPS-/bonusetiketter.
Ingen kamper får ny ferdig bonusberegning i denne fasen. Globale scorings- og
kvalifiseringskrav beholdes separat.

478 305 eksterne verdier har fortsatt kildekvalitetsforbehold.
Dette er ikke like mange manuelle oppgaver: kontroll av alle 775 248 kravrader
kombineres med grupper etter felt/sesong og egne avvikslister. Unionen av åpne
krav og kvalitetsforbehold er 77 214 spillerkamper  uten dobbelttelling.
Rå FPL  alle assistavgjørelser  keeperverdier og låste poeng/BPS/bonus/modeller/
benchmark er uendret. Ingen main-merge eller betalte data.
24 nye og 145 eksisterende fokuserte tester består. Alle 2 280 råsvar er
hashkontrollert; 2 332 data-/kontroll-/evidensfiler er identiske ved lokal
omkjøring uten nettinnhenting. Full repository-test og GitHub CI er ikke verifisert.

## Assists: fire arbeidssteg gjennomført – 7. oktober 2026

**Forrige restliste: [assist_reconciliation/](../research/current/scoring_2026_27/assist_reconciliation/README.md).**
Regelvurdering, separat kontrollutvalg, historisk målkjøring og aggregering til
spillerkamper er nå gjennomført. Manglende årsaksdata betyr fortsatt uavklart;
full harmonisering av poeng/BPS/bonus er ikke ferdig.

7 543 tilgjengelige mål er behandlet. **9 681 assistverdier er avklart**, hvorav
820 positive kampverdier og 8 861 dokumenterte nuller. 39 035 gjenstår:
583 mangler komplett målinventar, 38 452 trenger ytterligere årsaksbevis eller
kvalifisering av automatisk hendelsestolkning. Fire komplette kampverdier
endres fra 0 til 1: Marmoush, Pedro Porro, Alex Scott og Pickford, alle tidligere
dokumenterte offisielle eksempler fra 2024/25. Øvrige ferdige historiske
kampverdier stemmer med FPL. Alle 11 492 FPL-assistverdier fra 2025/26 beholdes.

Nytt fryst utvalg: 40 mål i 30 kamper, valgt uten assistfasit og uten gamle
utviklingseksempler. **18 riktige avgjørelser, 0 feil, 22 uavklarte**.
15 direkte pasningsassists og 3 foul-winner-assists gir kontrollstøtte for disse
to automatiske rutene. Andre ruter holdes igjen. Dette er et separat tidsbasert
kontrollutvalg fra eksisterende FPL-uttrekk, ikke uavhengig Opta-validering eller
bevis for alle sesonger. De gamle ti eksemplene teller ikke som holdout.

Ny totalrest: **258 302 feltkrav i 66 087 unike spillerkamper**. Fordeling:
219 615 manglende data, 234 eksterne konflikter, 38 452 assistvurderinger og
ett kjent FPL-uttrekksunntak. 339 783 tilgjengelige eksterne felt har fortsatt
individuelt kvalitetsbehov; unionen med åpne krav er 77 214 spillerkamper.
At 9 681 assistkrav lukkes reduserer den globale spillerkampkøen med bare 22,
fordi de fleste fortsatt har andre manglende felt.

4 604 tilgjengelige mål før 2025/26 trenger videre assistbevis. Dette er en
separat målkø, ikke ekstra spillerkampmangler som skal summeres inn. 21 manglende
arkivkamper og tre ytterligere kamper uten hendelser beholdes som datagap.
Ingen dokumenterte målscorerkonflikter gjenstår etter de allerede godkjente
mål-/selvmålsrettelsene. Manglende hendelser er ikke registrert som observerte nuller.

Rå FPL, alle andre kravfelt, keeperverdier og låste poeng/BPS/bonus/modeller/
benchmark er bevart. Videre arbeid bør skaffe årsaksbevis for de 4 604 målene
og egne kontroller for flere assistforløp, parallelt med de øvrige eksterne
statistikkmanglene. Ingen modelltrening eller endelig bonusrangering er kjørt.
38 nye og 107 eksisterende fokuserte tester består; 34 data-/kontrollfiler er
identiske ved full ny kjøring. Full repository-test og GitHub CI er ikke verifisert.

## Historikk: uttrekk og kvalitetskontroll – 7. oktober 2026

**Forrige restliste: [delta_input_audit/](../research/current/scoring_2026_27/delta_input_audit/README.md).**
Kildepolitikken i `fpl_authority/` gjelder fortsatt. Punkt 1 og 2 er gjennomført
som reproduserbart uttrekk og kildekontroll; ikke som godkjenning av hele
scoringsmotoren eller hver enkelt ekstern verdi.

95 551 tidligere åpne feltkrav er nå tilgjengelige: 67 431 for antall ganger
taklet, 27 698 for signert gammel netto taklingsteller og 422 for redninger
utenfor boksen. 17 tidligere tilgjengelige taklingsfelt flagges som konflikter.
**267 983 åpne feltkrav i 66 109 unike spillerkamper** gjenstår, mot 363 517.
Fordeling: 219 032 manglende verdier, 234 eksterne konflikter, 48 716
assistomregninger og ett kjent FPL-uttrekksunntak.

De 28 forhåndsvalgte nye kontrollene gir 160/160 eksplisitte feltsamsvar.
1 240 nødvendige eksterne verdier stemmer direkte med primærkontroller;
339 783 andre tilgjengelige verdier har kilde-/formatkontroll, men er ikke
individuelt primærbekreftet. Åpne krav og videre kvalitetsbehov har en union
på 77 215 spillerkamper. Felles Opta-opphav er ikke uavhengig validering.

Alle 576 sammenlignbare historiske positive mållinjeklareringer stemmer med
hendelser, men ingen av de tomme tellerne er gjort om til null. Netto taklinger
beregnes bare fra to eksplisitte tellere; gammel BPS-klipping er fortsatt en
separat regelgate. Eksterne/FPL-avvik i 2025/26 endrer ikke FPL-fasiten.

Kontroll mot 16 publiserte sesongsummer finner tre forskjeller. Nåværende
PL-API støtter arkivet for Bowen og Ndiaye. Alle 30 Doku-opptredener er kontrollert:
forskjellen ligger i 2025/26 kamp 356, arkiv 4 mot PL 5. Denne konflikten står
åpen, uten gjetting på historisk BPS. Tidligere godkjente målrettelser,
5 343 keeperverdier og de 38 uløste keeperobservasjonene er bevart.
Ingen rå FPL-data, låste poeng/BPS/bonus, modeller eller benchmark er endret.

Assistberegningen (punkt 3) og videre innhenting/full poengomregning (punkt 4)
er ikke utført i denne fasen. Nye etiketter er ikke produsert. Kostnad 0 NOK.
15 nye og 104 eksisterende fokuserte tester består; 25 resultatfiler er identiske
ved ny kjøring. Full repository-test og GitHub CI er ikke verifisert.

## Historikk: første FPL-prioriterte restliste – 7. oktober 2026

[fpl_authority/](../research/current/scoring_2026_27/fpl_authority/README.md)
etablerte FPL-prioriteten. Tallene nedenfor er nå historikk; se nyeste kø over.
Historisk FPL er fasiten for kompatible felt, inklusive minutter og eksplisitte
nuller. Eksterne kildeforskjeller er ikke automatisk FPL-feil. Ingen generell
minutt- eller pasningsrekonstruksjon skal prioriteres videre.

Metoden bruker historisk FPL-BPS og endrer bare regelledd som har endret seg
mot 2026/27. Bonus må rangeres på nytt etter dette; historisk bonus/totalpoeng
skal ikke merkes som ferdig harmonisert. Sesongavhengigheter og globale
kvalifiseringskrav står i `fpl_authority/rule_dependencies.json`.

Ny rest: **363 517 åpne feltkrav i 77 248 unike spillerkamper**:
314 595 manglende eksterne verdier, 205 eksterne kildekonflikter,
48 716 assistomregninger og ett kjent FPL-uttrekksunntak (Ferguson).
Separat finnes **245 489 tilgjengelige eksterne verdier i 66 584 spillerkamper**
for kvalitetskontroll. Unionen berører 77 280 spillerkamper, uten dobbelttelling.
Reduksjonen fra 880 385 er korrigert metode/prioritering, ikke ny datadekning.

Alle 77 280 FPL-minuttverdier, 5 343 godkjente keeperverdier og 38 uløste
keeperobservasjoner er bevart. De fire godkjente offisielle målomgjøringene
videreføres som åtte avledede mål-/selvmålsrettelser med separate hendelsesgater.
Ingen kilder eller låste etiketter/modeller/benchmark er endret.
16 nye og 80 eksisterende fokuserte tester består; 17 filer er identiske ved ny kjøring.

Neste prioritet er å projisere `times_tackled`, gammel netto taklingsteller og
redninger utenfor boksen fra tilgjengelige råarkiver, kvalifisere delta-leddene,
og deretter håndtere manglende eksterne data og assists. Uprojiserte felt er
ikke bevist fraværende hos kildene. Nye målpoeng/BPS/bonus er ikke produsert.

## Historikk – tidligere køer er erstattet

## BPS-hypoteser kontrollert; fire minuttunntak avklart – 7. oktober 2026

[Nyeste restliste og BPS-minuttkontroll](../research/current/scoring_2026_27/bps_minute_qualification/README.md)
viderefører `84da2fd`. BPS-regelen for de 364 grensefallene er **fortsatt åpen**.
I eksisterende 622 utviklingskontroller gir både primærminutter > 60 og
FPL-minutter ≥ 60 621 eksakte BPS-treff, mot 620 for dagens formel.
Bare Anthony, 2026/27 kamp 17, skiller seg ut: FPL 60 / primær 61,
offisiell BPS 4 mot diagnostisk 1. Alternativene gir begge 4. Øvrige
BPS-tellere er ikke komplette, og dette er ikke en ny holdout eller et
uavhengig isolert minuttbevis. Ingen generell regel er valgt eller endret.

Pulisic og Schade har entydige inn-/utregistreringer ett sekund fra hverandre
innenfor samme poengbånd. Lo Celsos videodekningsavbrudd ligger etter utbyttet.
Zinchenkos andre gule ved 59:59 bekreftes av FPL og offisiell kamprapport.
**Fire minuttbidrag er avklart**, hver med 1 grunnpoeng og 3 BPS.

Nyeste kø har **880 385 åpne poengbehov**, **881 632 råstatistikk-/regelbehov**
og **77 280 unike berørte spillerkamper**. 386 poengfølsomme minuttbehov
gjenstår: 364 regelspørsmål og 22 særtilfeller. Bruk `bps_minute_qualification/`
som nyeste kø; tidligere køer er historiske øyeblikksbilder.

Neste BPS-kontroll må skille hypotesene, eksempelvis FPL/primær 60/60 eller
59/61 med publisert minuttkomponent eller uavhengig komplette øvrige tellere.
Flere 60/61-eksempler alene er ikke tilstrekkelig. Historiske totaler krever
sesongriktige BPS-vekter. Keeperverdier og låste poeng/BPS/bonus/modeller/
benchmark er uendret. Ingen nye komplette BPS-/bonusetiketter.
16 nye og 64 eksisterende fokuserte tester består; tolv data-/evidensfiler
er identiske ved ny kjøring. Kostnad 0 NOK.

## Minuttgrenser: 320 avklaringer og 364 regelspørsmål – 7. oktober 2026

[Nyeste kø og minuttkontroll](../research/current/scoring_2026_27/minute_reconciliation/README.md)
viderefører `579fe37`. Alle 710 gjenværende poengfølsomme minuttkonflikter
er undersøkt mot bytter, startoppstillinger og periodeklokker. **320** har
nå dokumentert minuttbidrag, **364** har bekreftede grunnpoeng men uavklart
BPS-avrunding, og **26** krever særskilt hendelseskontroll eller mangler kilder.

Mange kildeavvik er fullførte minutter versus påbegynt kampminutt. FPLs
regel om 60 fullførte ordinære minutter og sekunder i byttehendelsene
understøtter avklaringene. Metoden krever dokumentert starter, sammenhengende
deltakelse, periodegrenser, samtidige inn-/utbytter og samsvar med FPL.
Ingen overføring av grunnpoengenes avrunding til BPS ved 60:01–60:59 uten
regelbevis. Disse 364 poengbehovene er merket `rule_unresolved`, med tidligere
kildekonflikt bevart. Ingen ny komplett BPS-/bonusberegning.

Samlet gjenstår **880 389 poengbehov i 77 280 unike spillerkamper**.
Råstatistikk-/regelresten er fortsatt **881 632**, fordi kildeheltallene ikke
er overskrevet. 390 poengfølsomme minuttbehov gjenstår; Fergusons tidligere
avklaring er videreført uten dobbelttelling. Nye felt-, spillerkamp- og
kampoppsummeringer finnes i `minute_reconciliation/` og erstatter forrige
kø som arbeidsgrunnlag. Tidligere rapporter er historiske øyeblikksbilder.

Neste prioritet er én dokumentert BPS-minuttkonvensjon for de 364 tilfellene,
og konkrete oppfølgingskontroller for de 26 særtilfellene. Flere kopier av
samme avrundede minuttall vil ikke alene løse regelspørsmålet.
16 nye og 48 eksisterende fokuserte tester består; ni resultatfiler er identiske
ved ny kjøring. Keeperverdier og låste
poeng/BPS/bonus/modeller/benchmark er uendret. Kostnad 0 NOK.

## Offisielle målrettinger og minuttbevis – 7. oktober 2026

[Nyeste restliste og revisjonstillegg](../research/current/scoring_2026_27/official_revision/README.md)
viderefører `4883ccc`. Brukeren har valgt **endelig korrigerte offisielle
hendelser omregnet etter 2026/27-reglene**. Historiske FPL-låsefrister
rekonstrueres ikke, og historiske FPL-verdier bevares separat.

Alle fire målkonfliktene er forklart av offisielle omgjøringer. McTominay,
March, Gabriel og Wissa får ett mål mer; tilhørende selvmål hos Pröpper,
Harrison, Henderson og Harry Clarke fjernes i samme korreksjon. Dette gir
**åtte korrigerte tellere i åtte spillerkamper, men fire lukkede konflikter**.
Begge lagenes målsummer er kontrollert mot sluttresultatet. Ingen automatisk
videreføring av historiske own-goal-assists; målregel-assists er fortsatt åpne.

Brightons egen rapport beviser Fergusons innhopp mot Forest 01.02.2025.
Null minutter avvises; **1 grunnpoeng og 3 BPS i minuttkomponenten** er bevist.
Eksakt minuttall forblir ukjent. 710 av de opprinnelige 711 poengfølsomme
minuttkonfliktene gjenstår. Dette er neste prioritet.

Ny kø har **880 709 åpne poengbehov**, **881 632 råstatistikk-/regelbehov**
og **77 280 unike berørte spillerkamper**. Felt-, spillerkamp- og kampfiler
bruker samme nøkler uten dobbelttelling. Tolv hendelsesavhengigheter er
kontroller av assists/skudd/kampvinnende mål, ikke ekstra manglende felt.
Tidligere køer nedenfor er historiske øyeblikksbilder; bruk `official_revision/`
som nyeste kø sammen med de eksplisitte teller- og minuttilleggene.

12 nye tester og 36 eksisterende fokuserte tester består. To bygg gir
identiske resultatfiler. Keeperverdier, låste poeng/BPS/bonus/modeller og
benchmark er uendret. Ingen komplette nye BPS-/bonusetiketter eller holdout.
Full harmonisering er fortsatt uferdig. Kostnad 0 NOK.

## Prioritert avklaringskø og 1 194 avklarte poengbehov – 7. oktober 2026

[Ny prioritering](../research/current/scoring_2026_27/resolution_priority/README.md)
viderefører PR #1 fra `2aded7f`. Offisielle sluttresultater beviser **272 nye
nuller for kampvinnende mål**, lagret separat. **922 ukjente straffemålsfordelinger
for GK/DEF** er uten betydning for poeng, men råtellerne forblir ukjente.
Dette løser 1 194 feltbehov i **1 146 unike spillerkamper**. Etterpå står
880 714 poengbehov åpne i 77 280 spillerkamper; råstatistikk-/regelrest er
881 636 fordi de 922 fordelingene ikke er rekonstruert.

16 649 av 17 360 minuttkonflikter gir samme minuttpoeng for registrerte
kildealternativer; **711 krysser en poenggrense**. 81 av 120 spillerkamper
med pasningskonflikt gir samme BPS-bånd. Dette er betingede kandidatkontroller,
ikke sanne verdiintervaller eller nye godkjente totalscorer. Konfliktene beholdes.

Først i neste kontroll står fire måltilordninger: McTominay 10.11.2019,
March 11.03.2023, Gabriel 20.01.2024 og Wissa 26.10.2024. Historisk FPL har
ett mål mindre enn FotMob/arkivet i hver kamp. Offisielt revisjonsgrunnlag
og tilhørende selvmål/assists må avklares før en kildepolitikk velges.
Målkonfliktene, minuttgrenseavvikene og øvrige prioriterte konflikter omfatter
samlet **1 442 unike spillerkamper**, uten dobbelttelling.

En mulig nullgrense for vunne taklinger har 28 522 kandidater og ingen
moteksempler i 32 344 eksplisitte sammenligninger, men er ikke godkjent uten
definisjonsbevis. Grensen «store sjanser skapt ≤ sjanser skapt» har **42
moteksempler** og kan ikke brukes generelt. Ingen kandidatnuller er imputert.
Kø, tiltaksbevis, felt-/spillerkampoppsummeringer og konservative defensive
terskelkontroller er versjonert. Dekningspotensial er ikke en suksessprognose.

34 fokuserte tester består; to kjøringer gir identiske resultatfiler.
Keeperverdier, tidligere restliste og låste poeng/BPS/bonus/modeller/benchmark
er uendret. Ingen komplett BPS-/bonusberegning eller ny holdout; full historisk
harmonisering er fortsatt uferdig. Kostnad 0 NOK.

## Samlet restliste etter kildekobling – 7. oktober 2026

[Ny spiller-/kamp-/feltoversikt](../research/current/scoring_2026_27/remaining_ledger/README.md)
viderefører PR #1 fra `f799229`. FPL, FotMob, det supplerende arkivet,
primærkontroller og eksisterende rekonstruksjoner er koblet på samme nøkkel.
**77 280 unike spillerkamper / 2 660 kamper** er med. Ingen aktive historiske
FPL-rader faller utenfor; én leverandøraktiv Ferguson-rad har null FPL-minutter.

Av 2 355 867 nødvendige felt–spillerkamper er 673 347 dokumenterte positive
verdier og 800 612 dokumenterte nuller. **806 298 mangler data, 18 322 har
kildekonflikt og 57 288 har uavklart assistberegning**: 881 908 åpne felt,
men **77 280 unike berørte spillerkamper**, uten dobbelttelling.
18 016 spillerkamper har konflikt; 793 har konflikt utenom minuttfeltet.
Dette er konservativ eksakt tellerdekning, ikke antallet nødvendige nye
datatrekk eller dokumenterte poengfeil. De gamle 3 003 033 arkivblankene er
ikke brukt som restmål. CBI-delkomponenter telles ikke igjen når summen er behovet.

Lagets offisielle null mål gir separat nullbevis for assists i **19 992
spillerkamper**. Fire offisielle målspesifikke assisttillegg bevares, men
tolkes ikke som komplette kamptotaler. Keeperverdiene er identiske:
5 343/5 381 godkjent, 38 uløste. Arkivhullet er fortsatt 593 spillerkamper
i 21 kamper; ytterligere tre kamper med 95 spillerkamper mangler hendelser
for ni mål. Disse er overlappende kildeflagg, ikke ekstra spillerkamper.

`remaining_fields.csv.gz` inneholder navn, kamp-/spiller-ID-er, felt, alle
kildeverdier, status og grunn. Felt-, sesong-, spiller- og kampoppsummeringer
følger med; globale regel-/formelsperrer ligger separat i `rule_gates.json`.
Neste arbeid: dokumenter sparsomfeltenes nullsemantikk, avklar konkrete
kildekonflikter og hendelseshull, og fullfør assistkandidat-/regelsporet.
Ingen mangler er automatisk null, ingen xG-imputering og ingen endring i
låste poeng/BPS/bonus/modeller/benchmark. Full harmonisering er fortsatt uferdig.
13 nye og 72 relevante eksisterende tester består; to offline-kjøringer
gir byte-identiske dataresultater. Valideringen står i den nye rapportmappen;
full testsuite og GitHub CI er ikke kontrollert her.

## Eksplisitte berøringsmerker – 7. oktober 2026

[Ny kode- og dekningskontroll](../research/current/scoring_2026_27/assist_schema/README.md)
viderefører `fcbef323` på PR #1. En versjonert, offentlig parserordbok beskriver
383/384/385 som kontroll/pasning/klarering og 328 som skudd på første berøring.
Dette er ikke en leverandørsertifisert kodeoversikt. Rådatakontrollen går fra tre
til fire riktige negative avgjørelser av ti; seks er fortsatt uavklart. Jensen
er den nye avklaringen. Ingen nye historiske assistetiketter er godkjent.

4 125 av 7 543 mål har eksplisitt førstegangsmerke. Blant 136 432 taklinger og
brytninger har 31 063 pasningsmerke. Berøringstype mangler for 20 246 av 20 337
hendelser i 2019/20 og 301 i 2025/26; fravær kan ikke tolkes som ikke-pasning.
Åtte nye tester består. Neste arbeid er kandidatvalg og nye uavhengige kontroller;
intensjon og fullstendige berøringsforløp gjenstår. Keeperstatus er fortsatt
5 343 / 5 381, med 38 uløste. Poeng, BPS, bonus og modeller er uendret.
Eldre avsnitt nedenfor viser fremdriftshistorikken.

## Assistregler og hendelseskontroll – 7. oktober 2026

[Regelkontroll med kildegrenser](../research/current/scoring_2026_27/assist_rules/README.md)
er lagt til på eksisterende PR #1, videreført fra `e867704`.
Seks tidligere eksempler og fire ekstra offisielle avgjørelser er kontrollert.
Reglene gjenskaper alle ti når offisielt beskrevne situasjonsfakta legges inn;
dette er utviklingskontroller, ikke ti automatiske prediksjoner eller en ny
uavhengig test. Råhendelsene alene støtter tre negative avgjørelser. Sju forblir
uavklart, og ingen nye historiske assistetiketter er godkjent.

Konkrete sperrer: mottakssted er forskjellig fra skuddsted; luftduell/klarering
kan beskrive samme berøring; taklinger/brytninger kan være klassifisert som
pasninger; VAR-forsinkelse og perioder må bevares. Qualifier 384 forekommer i
to offisielt beskrevne pasningsberøringer, men er ikke godkjent som universell
kodeoversettelse. Fullstendige hendelser fra de tre nye eksempelkampene er lagret.
17 tester består, og offline-gjenkjøring er byte-identisk. Neste arbeid er
verifiserbar berøringsklassifisering, mottaks-/intensjonsdata og kandidatvalg før
reglene kan kjøres som eksakt historisk beregning. Keeperstatus er uendret:
5 343 / 5 381, med 38 uløste. Poeng, BPS, bonus, modeller og benchmark er uendret.

## BPS-kildeaudit og assistgrunnlag – 7. oktober 2026

Arbeidet er videreført på PR #1-grenen fra `dfa2ff30b36e33c4b16f5402d25af9337266af3f`,
ikke innlemmet i main. [Ny rapport](../research/current/scoring_2026_27/bps_recovery/README.md):
76 687 av 77 280 historiske spillerobservasjoner er koblet til det frosne arkivet.
De 593 hullene er fra 21 manglende kamper; ingen navnekoblinger gjenstår.
Alle 3 244 eksplisitte tellingpar i 327 historiske primærkontroller stemmer.
Manglende felt forblir manglende. I de tidligere brukte 622 GW1/GW2-kontrollene
har arkivvarianten riktig bonus for alle og riktig BPS for 615, mot 620 med
primærtellingene. Dette er ikke en ny uavhengig validering.

Assistsummen fra arkivets kategorier gjenskaper nesten alle gamle FPL-awards,
men ingen av de fire kjente offisielle tilleggene etter nyere kriterier.
Fullstendige hendelser fra de seks offisielle eksempelkampene, en målbasert
vurderingskø og en eksplisitt ufullstendig assistkandidat-liste er lagret.
Ingen nye assistetiketter er godkjent. Neste arbeid: hendelsesbaserte kriterier,
med mottakssted og defensive berøringer, deretter nye kontrollkamper.

**Gjeldende keeperstatus fra overleveringen er 5 343 / 5 381 (99,29 %), med
38 uløste i 22 kamper.** Både 2024/25 og 2025/26 er dekket. Sánchez er avklart
i `keeper_recovery/resumption/`; eldre statusavsnitt nedenfor er historikk.
Full keepergjenkjøring er `recover.py`, `reconcile_followup.py`, deretter
`reconcile_match_totals.py`. Ingen keeperverdier er endret i denne BPS-auditen.
Åtte nye identitetstester består. Full historisk 2026/27-harmonisering er fortsatt
uferdig; låste poeng/BPS/bonus, modeller og benchmark er uendret. Kostnad 0 NOK.

## Keeperrestlisten – 18 nye avklaringer, 7. oktober 2026

[Oppfølgingsrapport](../research/current/scoring_2026_27/keeper_recovery/followup/README.md):
57/57 primære spiller-/kamprader er hentet. 18 av 57 uløste observasjoner er
avklart, slik at dekningen er **5 342/5 381 (99,28 %)**. Hele 2024/25 er nå dekket.
39 observasjoner i 23 kamper gjenstår: 37 fra 21 manglende kildekamper, pluss
Ramsdale mot Villa 1. februar 2020 og Sánchez mot Spurs 19. mai 2026.
De 39 feltene forblir manglende. Tjue transformasjonstester består. Kjør
`recover.py` og deretter `reconcile_followup.py` for full gjenkjøring.
Bevis, primærresponser og vedtak er versjonert. Ward har et dokumentert avvik
mellom oppdatert redningstall og historisk FPL. Låste poeng og benchmark er
uendret; kostnad 0 kroner. Avsnittene nedenfor er tidligere kontrollpunkter.

## Storsjanseredninger – ny løsning, 7. oktober 2026

[Rekonstruksjon og restliste](../research/current/scoring_2026_27/keeper_recovery/README.md): Et offentlig Opta-basert hendelsesarkiv er funnet og kontrollert. **5 324 av 5 381 historiske keeperobservasjoner (98,94 %) har nå en kontrollert telling.** Alle observasjonene i 2021/22 og 2023/24 er dekket. Skudd med eksplisitt storsjansemerke skilles fra utespillerblokker; keeperbytter håndteres med periode og redningshendelser. Ingen xG-anslag brukes.

57 observasjoner i 32 kamper er fortsatt uløste: 42 observasjoner i 21 kamper som mangler i arkivet, og 15 observasjoner i 11 kamper med manglende merker eller kildekonflikter. I en nyere kontroll av 100 keeperobservasjoner stemmer alle 52 eksplisitte storsjanseredningstall. Dette er en kontroll mellom Opta-baserte datatyper, ikke en uavhengig leverandørkontroll. Ti tester består. Kode, versjonerte kildeuttrekk, hendelsesbevis, koblinger og konkret restliste er lagret i keeper_recovery.

**Keeperdekningen er ennå ikke komplett.** Godkjente tellinger ligger separat; låste poeng/BPS/bonus og benchmark er uendret. Kostnad 0 kroner. Neste keeperarbeid skal rette seg mot restlisten, ikke gjenta det brede kildesøket. Historiske assists og øvrig BPS-innhenting gjenstår separat. Eldre statusavsnitt nedenfor beskriver tidligere kontrollpunkter.

## Oppfølging av datainnhenting – 7. oktober 2026

[Innhenting og offisielle assistkorreksjoner](../research/current/scoring_2026_27/acquisition_followup/README.md): 119 nye primære spiller-/kamprader fra fire 2024/25-kamper er hentet, med null feil og 119/119 like minuttall mot FotMob. Fire offisielt dokumenterte assisttillegg er koblet til kamp-/spiller-ID: Marmoush, Pedro Porro, Alex Scott og Pickford. To negative eksempler er bevart. Tilleggene gir 12 direkte spillerpoeng før bonus, men er ikke skrevet inn i det låste datasettet. Gjeldende 2026/27-assistkriterier er kontrollert mot FPLs regelkomponent.

En gjenopptakbar innhenter lagrer kontrollpunkt etter hvert svar og stopper på 401/403/429. Full 2024/25-kø er bygget med 11 567 rader / 380 kamper og ingen uløste ID-er; hele køen er ikke kjørt. Åtte nye tester består, og gjentatt kjøring av kontrollkøen hentet ingen svar på nytt. Kode, komprimert kø, normaliserte nye data, kildehash og rapport er lagret. Lokale råcacher/kontrollpunkt er ikke publisert; se rapporten for oppstart på ny checkout.

**Full historisk 2026/27-harmonisering er fortsatt IKKE ferdig.** Ingen av de åtte nye keeperradene har eksplisitt storsjanseredningsfelt. Nye kildeundersøkelser ga ikke en full historisk hendelseseksport; Opta-datatjenesten svarte 403 og ble ikke omgått. Ingen modelltrening, benchmarkendring eller kostnad. Neste konkrete arbeid: bolkvis primærinnhenting med fast manifest; flere offisielle assistavgjørelser; en faktisk hendelseskilde for historiske storsjanseredninger. Ikke merke approximasjoner som fasit.

## Målet er 2026/27 – datakrav kontrollert og nye BPS-data hentet

7. oktober 2026: [2026/27-audit og kildevalidering](../research/current/scoring_2026_27/README.md). Brukeren har presisert at målregelverket er 2026/27. Regelvektene er hentet fra FPLs faktiske regelkomponent/API. Alle 2660 tidligere råkamper er gjennomgått; flere BPS-felter er trukket ut for 77280 aktive kildeobservasjoner. 830 nye primære spiller-/kampresponser er hentet, inkludert hele GW1–2 i 2026/27.

GW1 utvikling: 309/310 eksakt BPS og 310/310 bonus. Forhåndsdefinert GW2-kontroll: 311/312 eksakt BPS og 312/312 bonus, uten videre formeltilpasning. Seks tester består. Kode, data, kildehash, dekningsrapporter og kontroller er lagret.

**Full historisk 2026/27-harmonisering er IKKE ferdig.** `big_chance_saves` mangler i FotMob og har utilstrekkelig historisk dekning i PL-kilden. Historiske FPL-assists er ikke omregnet og påvirker også BPS. Resterende primære historiske komponenter er bare innhentet i kontrollutvalg, ikke hele korpuset. Sofascore/WhoScored svarte 403 og ble ikke omgått. Ikke fyll slike hull med null. `results/readiness.json` sperrer full omregning. Det tidligere låste datasettet er et mellomsteg med 2025/26-defcon, ikke en komplett 2026/27-fasit. Ingen modelltrening, benchmarkendring eller kostnad.

## Felles defcon-grunnlag låst 7. oktober 2026

[Harmonisert datasett og reproduksjon](../research/current/rescoring_2025/harmonized/README.md): `historical_points_plus_harmonized_defcon_v1` er låst som forskningsgrunnlag etter åtte beståtte kvalitetskrav. Alle 2660 kamper fra 2019/20–2025/26 og 71898 aktive utespillerobservasjoner er dekket, uten uløste etiketter. Ett sett FotMob-definisjoner brukes over hele perioden; offisiell FPL-fasit beholdes i 2025/26.

Full 2025/26-kontroll: 10698/10725 like defcon-poengtildelinger (99,748 %), 22 falske positive og 5 falske negative. Positive utslag: presisjon 98,466 %, recall 99,647 %. Eksakt tellelikhet 96,858 %. 404 historiske tildelinger korrigeres (−808 poeng i hele spillerpopulasjonen, ikke managerscore). 2024/25 er uendret. Alle kildehash og normaliserte rådata er kontrollert; 14 sesongfiler gjenoppbygges byte-identisk; seks transformasjonstester består. Kode, plaintext-datapartisjoner, etiketter, kildehash og auditer er lagret.

Historiske assists og bonus er fortsatt historiske: dette er ikke full omregning til alle 2025/26-regler. Ingen modelltrening eller benchmarkendring. `fixture_full_h3_adaptive_tc` og arkivert snitt 2351,50 står uendret på sin opprinnelige poengbasis. Neste steg: kjør referansen på det nye låste poenggrunnlaget med like ressurser/regler, deretter et separat defcon-komponentforsøk med tidsriktig retrening. Kostnad 0 NOK.

## Siste kartlagte defcon-hull lukket og klareringsavvik identifisert

7. oktober 2026: [2022/23–2023/24 og kildekontroll](../research/current/rescoring_2025/final_gaps/README.md). Alle 119 + 14 gjenstående etiketter er fylt; dermed er alle kartlagte aktive utespillerhull i 2019/20–2023/24 lukket. 455/455 kontrollutfall stemmer med arkivet; alle 133 nye etiketter har samme poeng ved ren FotMob som ved bevaring av kjente arkivfelter.

En målrettet kontroll av 50 offisielle PL spiller/kamp-responser viser i 50/50 tilfeller at arkivert FBref Clr = PL total_clearance + blocked_cross. FotMob følger PL-klareringer i 30/30 historiske kontroller. Korreksjonen fjerner 7/10 tidligere feilutslag i 2025/26; tre avvik i recoveries/interceptions står igjen og offisiell FPL-fasit beholdes. Dette er en utvalgt diagnose, ikke en generell presisjonsmåling.

Dekningen er komplett, men hele korpuset er ennå ikke harmonisert etter den dokumenterte kildeprioriteten. Neste steg: hent konsistente defensive tellinger for hele historikken, valider mot full offisiell 2025/26 og lås deretter felles poenggrunnlag før nye modelltester. Historiske assists/bonus og benchmarken står uendret. Kostnad 0 NOK.

## 2021/22-gapet fylt 7. oktober 2026

[FotMob-rekonstruksjonen](../research/current/rescoring_2025/missing_2021/README.md) fyller alle 1238 gjenværende aktive utespilleretiketter fra 76 kamper. 9722/9722 dekning; 1211 recovery-fyll og 27 fullstendige defensive tellinger. 20 kontrollkamper: recoveries/taklinger/skuddblokker/interceptions er like på 509/509 observasjoner; klareringer 447/509 og defcon 505/509. Nye tellinger er derfor fortsatt kvalitetsmerket som foreløpige. Alle ti lagtotaler for Brentford–Wolves samsvarer med offisiell PL-statistikk. 178 nye to-poengsutfall er spillerpopulasjonens tillegg, ikke en managers gevinst. Ingen modelltrening, benchmarkendring eller kostnad. Kode, normaliserte kildetellinger, patcher, auditer og kildehash er lagret. Neste: undersøk samme kilde for 2022/23 og 2023/24, og avklar klareringsavvik før et felles nytt poenggrunnlag låses.

## Datagap reparert 7. oktober 2026

[Reparasjoner og usikkerhet](../research/current/rescoring_2025/gap_repair/README.md): tre feil i ID-kartet rettet, 59 duplikatnøkler avgjort fra offisiell kampdato/runde og fire defcon-utfall bevist fra delvise tellinger. Gjenværende aktive utespillerhull: 0 / 0 / 1238 / 119 / 14 i 2019/20–2023/24. Ukjent beholdes som manglende med eksplisitt 0–2-poengsintervall. Alternativ RDS-kilde inneholder samme recovery-data; ingen ekstra kampstatistikk gjenfunnet. Benchmarkens lagrede tellende spillere i GW5–38 har null eksponering mot de gjenværende hullene i 2022/23 og 2023/24; dette gjelder ikke nye lagvalg eller åpningsrundene. Ingen modelltrening, benchmarkendring eller kostnad. Neste: målrettet innhenting fra listen over manglende kamper og felles evaluering med eksplisitt usikkerhet. Eldre statusavsnitt nedenfor er historikk.

## Historikken utvidet

[FBref-arkivet](../research/current/rescoring_2025/historical_fbref/README.md) er hentet og foreløpige etiketter er bygget for 2019/20–2023/24. Aktiv utespillerdekning: 99,98 / 100 / 87,19 / 98,53 / 99,46 %. Ny kilde er kontrollert på 1129 rader fra 40 kamper i 2025/26: 99,11 % poengenighet når bare skuddblokkeringer brukes. Hull er manglende, ikke null; 32 motstridende FPL-nøkler fra 2019/20 er sperret. Kan brukes som kvalitetsmerket, delvis treningsgrunnlag; full sesongevaluering krever en eksplisitt plan for hullene. Ingen benchmarkendring eller kostnad.

## Nyeste datasett

Brukeren godkjente videreføring av gratisdataene. [2024/25 med rekonstruert defcon](../research/current/rescoring_2025/defcon_2024/README.md) er nå bygget og lagret: 27 283 spiller-/kamprader, 380 kamper, null manglende aktive defcon-etiketter. 1 253 utslag / 2 506 tilleggspoeng i spillerpopulasjonen. Historiske assists og bonus er beholdt; ikke full 2025/26-omregning. Benchmark og modellresultater er uendret. Neste: separat forsøk med felles nytt poenggrunnlag og tidsriktig retrening.

## Nyeste validering

[Sammenligning mot offisiell 2025/26](../research/current/rescoring_2025/core_2025_validation/README.md) fullført: alle 11 492 aktive FPL-rader koblet. Defcon er riktig i 10 423 av 10 457 komplette utespillerrader; 268 utespillerrader mangler nødvendig statistikk. 18 falske positive og 16 falske negative. Totale taklinger fungerer klart bedre enn vunne. Gratisdata kan videreføres med kvalitetsflagg; ingen eksakt eldre testfasit eller ny modellsimulering er hevdet. Ingen kostnad; brukerens totale tak for eventuell datatilgang er 500 NOK.

## Nyeste kildefunn

FPL-Core-Insights 2024/25 er hentet: 38 CSV-er, 380 kamper, 562 spillere og 11 567 spiller-/kamprader med defensive tellinger. Alle 11 566 FPL-rader med spilletid kan kobles diagnostisk; minutt-/mål-/assistavvik og manglende BPS-detaljer er dokumentert. [Rapport og reproduserbar kontroll](../research/current/rescoring_2025/core_2024/README.md). Neste: valider defensive definisjoner mot offisiell 2025/26, før ny poengfasit. Benchmark uendret.

## Nyeste forsøksrunde: kampjustering, horisonter og chips

Fullført 6. oktober 2026: **84 sesongforløp / 2856 beslutninger**, med åtte nøyaktig gjenskapte kalenderkontroller. [Full rapport](../research/current/fixture_strategy/README.md).

- Full motstander-/hjemme-bortejustering ved H3: 2348,00 med chips (+4,25 mot kamptelling), men −36,00 uten chips mot samme kontroll.
- Full H3 med adaptiv Triple Captain: **2351,50**; +43,25 mot benchmark og +7,75 mot kalenderutfordreren. TC alene gir +3,50 mot samme fulljusterte prognose; to av fire sesonger bedres.
- Adaptive BB/FH/WC gir henholdsvis −13,75/−11,75/−44,75 mot samme prognose med faste chips. Alle adaptive chips samlet gir −48,50.
- Ingen H5/H8-variant vinner med chips. H8 med ren kamptelling gir +13,75 uten chips mot H3, men har tidsbegrensede løsninger i 91 av 136 beslutninger.
- To H8-forløp feilet først uten gjennomførbar solverløsning og ble gjenkjørt. Alle endelige løsningskall brukte 10 sekundersgrensen; betinget 60-sekundersfallback var ikke nødvendig. Ikke hevde at alle løsninger er optimale eller nøyaktig maskinreproduserbare.

**Etterfølgende brukerbeslutning:** Full H3 med adaptiv TC er nå arbeidsbenchmark (`fixture_full_h3_adaptive_tc`). Kalenderdekningen er uendret; kommende arbeid bør prioritere tidsriktig kalender/frister, solverstabilitet ved lange planer og spareverdien til chips lært fra eldre sesonger. Fire tidligere brukte sesonger gir ingen urørt validering.

## Mål og avklaringer

Maksimer robust FPL-sluttscore etter at hovedmodellen tar over fra startmodellen. Test enkeltmodeller, faste og lærte prognosekombinasjoner, og separate variabler for motstanderens angrep og forsvar. Startmodellens overlevering skal inneholde den faktiske troppen, bank, kjøpspriser og gratisbytter. Ikke tilpass startlaget til et kunstig idealmottakerlag. Startstrategiens delmål ved GW8,12,15,19 beholdes separat.

Kvantifisering av elite-managere var et tidligere spor. Brukeren gikk videre til hovedmodellen; dette er nå hovedprioriteten. Rå elite-eierskapsarkiv er ikke nødvendig for gjeldende eksperiment og er ikke flyttet inn som aktivt datasett.

## Gjeldende arbeidsreferanse

Brukeren har valgt **full kampjustering H3 + adaptiv Triple Captain** (`fixture_full_h3_adaptive_tc`). [Benchmarkmanifest](../research/current/benchmark.json) låser kilder, prognoser og beslutningsspor. Primærscore er **2351,50**: 2343 / 2324 / 2487 / 2252 i 2022/23–2025/26. WC/FH/BB følger faste datoer. Samme prognose uten chips gir 2182,25 som separat diagnostikk.

`constant_h3` (2308,25) er arkivert i `benchmarks/constant_h3_20261006.json`; den og `calendar_count_h3` (2343,75) beholdes som kontroller. Historiske rapporters referanser og konklusjoner står uendret. Dette er en brukerbestemt forskningsbenchmark, ikke uavhengig bekreftet overlegenhet eller produksjonssetting.

Neste spor er [versjonerte 2025/26-poeng](../research/current/rescoring_2025/README.md). Datakontrollen gjenskaper 29 747 unike 2025/26-rader uten avvik, men bruker offisielle assists/BPS. Eldre sesonger mangler defensive tellinger og verifiserte nye assist-/BPS-etiketter. Full historisk omregning er derfor ikke ferdig. Nytt poenggrunnlag krever at benchmarken kjøres på nytt; 2351,50 er ikke direkte sammenlignbart.

## Historisk referanse og opprinnelig forsøk

Startmodell: `handoff=4`, `look=3`, `carry=1`, `friction=0.5`, `prior_mix=0`, `chip_reserve=1000`, `scenario=neutral`. Modeller trenes på eldre sesonger; hovedmottakerens optimizer har én-rundes horisont. Alle ti kandidater får samme starttilstand. Friksjon 0,5, benkvekt 0,10. Fast chipkalender: WC6, TC15, FH18, BB19, WC24, FH33, BB36, TC37. Det kjøres også uten chips.

120 ferdige forløp: seks sesonger × ti modeller × to chipregimer, totalt 4080 hovedmodellbeslutninger. Modeller: Ridge, Bayesian Ridge, Extra Trees, HGB med grunnvariabler, HGB med utvidelser, Ridge/Extra Trees 50/50, Ridge/utvidet HGB med HGB-vekt 25/50/75 %, og treveis lik blanding.

50/50 Ridge + Extra Trees ga +37,17 uten chips / +55,67 med fast kalender mot Ridge, med positiv gevinst i 5/6 og 4/6 sesonger. Fritt modellvalg kun ut fra eldre sesonger ga +3,75/+2,25 i fire evalueringssesonger. Beskrivende vinner og tidsordnet modellvalg er ulike sammenligninger. Ingen urørt holdout gjenstår i disse dataene. Ingen produksjonsmodell er automatisk byttet.

Utvidet HGB mot enkel HGB ga +15,17 poeng uten chips og −6,50 med chips. Det er en samlet featurepakke, ikke en isolert xG-effekt. Eget lags/motstanderens mål for/mot, Elo og lagget xG finnes; `starts_m6` er en 60+-minuttersproxy. Enkle målrateprodukter og `exp(-lambda_against)` er ikke en kalibrert Dixon–Coles-modell.

## Hva som ble gjort ved GitHub-integrasjonen

- Mai-repositoryet gjennomgått og bevart; nytt arbeid integrert under `research/current`.
- Hele aktive forsøket med rådata, startinnganger, prognoser, 120 beslutningsspor og resultattabeller flyttet inn.
- Individuelle gzip-innganger med SHA-256 og automatisk klargjøring erstatter manuell ZIP-utpakking.
- Residualideen implementert som opt-in HGB-kandidat og kjørt som separat prediksjonstest. RMSE bedret seg bare i 1/6 sesonger mot direkte HGB; ingen ny sluttscore påstås.
- Eldre API-/feature-/ensemblekode beholdt. Metodeproblemene er dokumentert i REPOSITORY_REVIEW, ikke skjult ved å overskrive gamle resultater.

## Bekreftede aktive utfordrere

Brukeren bekreftet 6. oktober 2026 at `re_refresh_h3` og `constant` skal videreføres som aktive utfordrere. Reglene og evidensen er registrert i [challengers.json](../research/current/challengers.json). Den opprinnelige referansen beholdes som historisk kontroll. [Kombinasjonsforsøket](NEXT_EXPERIMENT.md) er nå fullført med 16 nye forløp. Kombinasjonen har +70,0 med chips mot referansen, men ustabil tilleggsverdi over global H1; brukeren har deretter valgt den som ny arbeidsbenchmark.

## Siste forsøk: posisjonsspesialisering

Fullført 6. oktober 2026: **32 nye forløp** mot `constant_h3` på 2022/23–2025/26. Posisjonsbestemte blandingsvekter gir −42,50 poeng med chips; egne posisjons-HGB gir −83,50; global/posisjons-HGB 50/50 gir −3,00. De to første taper alle fire sesonger. Hybriden har +53,25 uten chips, men bredt intervall [−0,25; +134,00] og en stor gevinst i 2023/24. Benchmarken beholdes. Hybriden lagres som forskningskandidat for uten-chips-regimet, ikke ny primær utfordrer.

Alle åtte benchmarkforløp gjenskaper nøyaktig beslutninger og poeng. 1088 beslutninger er kontrollert; syv målrettede tester består ved direkte kjøring. [Rapport og kontroller](../research/current/position_specialist/README.md), [sesongresultater](../research/current/position_specialist/results/all_seasons.csv). Ingen urørt holdout eller ny produksjonsmodell.

## Siste forsøk: historisk kampkalender

Fullført 6. oktober 2026: 82 historiske kalenderuttrekk er rekonstruert ved 136 beslutningstidspunkter. Med grense på 14 dagers alder er dekningen 31/34, 33/34, 33/34 og 8/34 runder i 2022/23–2025/26. Sluttkalender brukes bare til datakontroll, ikke fremtidsprognoser.

En isolert test av fremtidig **antall kamper** gir `calendar_count_h3` **2343,75 poeng med chips (+35,50 mot constant_h3)** og 2218,25 uten chips (+45,50). Sesonggevinst med chips: −29, +143, +28, 0. Primært 95 %-intervall [−14,75; +107,25]; ingen urørt holdout. Alle 8 kontrollforløp gjenskapes nøyaktig. Benchmarken beholdes, kalenderkandidaten registreres som lovende forskning.

[Kalenderrevisjon](../research/current/calendar_audit/README.md), [forsøksrapport](../research/current/calendar_counts/README.md). Nåværende rundeprognoser og frister beholder gamle proxybegrensninger. Neste steg: bedre arkivdekning og motstander/hjemme-borte i egen ablasjon. Lesbare CSV-/JSON-arkiver gjenopprettes automatisk av `scripts/prepare_data.py`; nye prognoser regenereres av forsøksbyggeren.

## Prioritert neste arbeid

Oppdatert etter første kalenderforsøk:

1. Bruk `constant_h3` som ny arbeidsbenchmark for alle kommende forsøk, i tråd med brukerens beslutning. Behold `re_refresh_h3`, `constant` og den gamle frosne referansen som kontroller. Rapporter gevinst mot ny benchmark på samme evalueringssesonger; ingen omskriving av historiske resultater.
2. Prioriter før-frist-kalender/tilgjengelighetsdata og en låst prospektiv evaluering. Flere historiske vekt-/horisontsøk gir ikke en urørt bekreftelse.
3. Gjør håndtering av likeverdige valg mer deterministisk før praktisk bruk. Global H1 gjenskaper arkivet i kombinasjonstesten, men tidligere motoravvik viser at dette fortsatt er relevant.
4. Første kalenderablasjon er fullført med positiv, men ujevn gevinst. Forbedre særlig 2025/26-dekningen og test deretter motstander/hjemme-borte i en separat ablasjon. Faktiske frister og aktuell kalender trenger en ny felles baseline.
5. Gate og nye spilleres roller/tilgjengelighet er fortsatt forskning. Ingen nye terskler eller blandingsvekter er valgt etter siste resultater.

Rapporter nettosesongpoeng med chips som forhåndsbestemt primærmål, treffkostnad, usikkerhet og sesongvise forskjeller. Uten chips er diagnostikk. Samme starttilstand og samme beslutningsmotor skal brukes for å isolere modellendringer.

## Reproduksjon og begrensninger

Se rot-README. `prepare_data.py` må kjøres før forsøkene på ny maskin. Prognosebygging bruker lokale rådata. Modellkandidater og dataendringer skal ha separate protokoller/resultater; gammel trace-cache må ikke brukes ved endringer.

Historiske poeng, moderne chips/FT-regler; priser er laggede proxyer; skader og spilleravganger er ufullstendige; endelig historisk kamptildeling i aktuell GW antas kjent ved frist. Dette er forskningssimulering, ikke dokumentert faktisk rank eller topp-prosent-sannsynlighet. De gamle Parquet-LFS-filene er ikke nødvendige for det aktive forsøket.

## Siste verifikasjon

156 tester bestått etter klargjøring (152 eksisterende funksjonstester, reparert mappestrukturtest og tre nye forskningstester). 367 deprecation/future-advarsler fra eldre pandas-kode; ingen testfeil. De 47 pakkede inngangene er kontrollert mot både lagret og gjenopprettet SHA-256. Residualpiloten er gjennomført for alle seks sesonger. GitHub Actions er konfigurert for samme testkommando; lokal teststatus er ikke det samme som bekreftet CI-status.


## Litteraturgjennomgang

Se [LITERATURE_REVIEW.md](LITERATURE_REVIEW.md) for primærkilder, kildekritikk og prioriterte forsøk. Flerukers planlegging, prognosediversitet og separat angrep/forsvar er prioritert. Crowd-signaler og beslutningsrettet læring er videre kandidater. ORiON-artikkelens topp-4 %-resultat har et dokumentert chipavvik; det brukes ikke som regelkorrekt benchmark. Ingen nye modeller er trent eller ny sluttscore produsert i litteraturgjennomgangen.


## Oppsidetest fullført

Se [forsøksrapporten](../research/current/upside/README.md). Fire kandidater er trent og kjørt gjennom 48 nye sesongforløp: ren oppside, 25 % oppsideblanding, relevansvektet HGB og 50 % relevansvektet blanding. Alle taper i gjennomsnitt mot Ridge/Extra Trees 50/50: henholdsvis −163,7/−134,2, −56,5/−35,0, −72,5/−100,2 og −46,7/−53,5 poeng uten/med fast chipkalender. Ingen produksjonsendring.

Topp-20-treff på 8+ forbedres opptil 0,67 prosentpoeng, men billige spillere og kort historikk får ikke bedre treffandel. Tidsordnet modellvalg beholder referansen i alle fire evalueringssesonger. Ren oppside er ikke kalibrert forventet totalpoeng; endret scoreskala påvirker også byttevilje. Ingen urørt holdout.

Kode, protokoll, prognoser, 48 spor, usikkerhet og kontroller er lagret under `research/current/upside`. 156 eksisterende tester og tre nye tester bestått lokalt. Kontroll-HGB gjenskaper alle tidligere prognoser nøyaktig. Neste arbeid bør prioritere eksisterende plan for flerukers optimizer og bedre minutter/rolle-signaler fremfor å lete videre etter blandingsvekter på samme fasit.


## Oppside som variabel og kapteinssignal fullført

[Oppfølgingstesten](../research/current/upside_feature/README.md) bruker tidsriktige historiske oppsideprognoser: indre modeller trener bare på eldre sesonger. Matchede hovedmodeller med/uten ekstra variabel får identiske treningsrader. 2019/20 og 2020/21 bygger treningsgrunnlaget, og fem sesonger 2021/22–2025/26 evalueres med 40 nye hovedmodellforløp og 10 isolerte kapteinsreplay.

Variabelen gir −12,0/+13,6 poeng mot matchet HGB-kontroll uten/med chips. I 50/50-blanding med sterk referanse gir den +27,2/−34,0 mot kontrollblandingen, men oppsideblandingen taper fortsatt −11,0/−37,6 mot sterk referanse. Kapteinsfilter innen 0,5 forventede poeng gir −5,0/+5,8, med brede intervaller over null. Ingen robust vinner og ingen produksjonsendring. Ingen egen hard kjøpspoolavgrensning ble testet.

Alle fem sesonger var allerede undersøkt; ingen urørt holdout. Kode, protokoll, historiske oppsidevariabler, prognoser, spor, kapteinsvalg og parete resultater er lagret under `research/current/upside_feature`. 162 tester bestått lokalt. Videre arbeid bør prioritere bedre informasjon og flerukers optimizer fremfor å tune oppsidesignalet på samme sesongfasit.


## Fire-runders planlegging og dekomponert oppside fullført

[Rapport](../research/current/horizon_upside/README.md): seks sesonger × tre modeller × to horisonter × to chipregimer = 72 nye forløp. Full flertrinns bytteplan med bank og eksakte FT-overganger; bare første handling utføres. Fremtidig kamparkiv mangler før-frist-snapshots, så prognosene bruker én nøytral kamp per fremtidig runde og gradvis tilbakevending mot nøytral motstander, uten fremtidige utfall eller prognoser.

Dekomponert forventning `p*E[Y|Y>=8]+(1-p)*E[Y|Y<8]` gir +30,0/+72,5 mot vanlig HGB ved én-rundesplanlegging, med seier i 3/6 og 5/6 sesonger. Den taper fortsatt −45,8/−18,5 mot matchet sterk H1-referanse. Ved H4 taper dekomponert modell −40,0/−15,2 mot vanlig HGB. Ingen ny totalvinner.

H4 mot matchet H1: Ridge/Extra −22,0/+25,3; HGB +37,3/+35,3; dekomponert −32,7/−52,3 (uten/med chips). Sterk H4 er best med chips, men ikke robust på tvers av regimer. Ingen produksjonsendring. De 287 tidsbegrensede H4-beslutningene (maks gap 1,552 %) gjør at små gevinster må kontrolleres med strammere solver før eventuell bruk.

168 tester bestått på ferdig kode. Alle 2448 beslutninger har gjennomførbart oppgjør og identisk åpning. Prognoser, kilde-/inputfingeravtrykk, 72 spor med fremtidige planer, sesongvise effekter, solverdiagnostikk og usikkerhet er lagret under `research/current/horizon_upside`. Ingen urørt holdout. Dekomponert modell blandet med sterk referanse er ikke testet her.


## Løpende retrening og hendelsesmodell fullført

[Rapport](../research/current/adaptive_events/README.md). Ni forhåndsbestemte kandidater, seks sesonger og to chipregimer ga 108 nye forløp. Primærmålet ble fast chipkalender; uten chips diagnostikk. Modeller trenes hver fjerde GW med kun før-frist-utfall, mot frosne kontroller. Selvstendig modell for 0/1–59/60+ minutter og betingede mål/assists/CS-/øvrige poeng. Tre faste blandinger inkludert.

Utvidet HGB med retrening er beskrivende primærvinner: 2224,7 poeng, +8,3 mot sterk referanse. Bare 3/6 seire, intervall [−62,7; 79,7], tap i de to siste sesongene. Ingen robust ny totalvinner; behold som utfordrer uten produksjonsendring. Tidsordnet modellvalg beholder referansen i alle fire primære evalueringssesonger (0 gevinst).

Det tydeligste funnet er retrening av vanlig HGB: +54,7 med chips / +85,8 uten mot samme sesongfrosne HGB, med 5/6 seire i begge regimer. 365-dagers tidsvekter svekket modellen. Oppdatert hendelsesmodell tapte −89,2/−51,0 mot sterk referanse; direkte/hendelsesblanding ga −21,5/+22,2. Blandingens treff blant billige spillere bedret seg, men primær sesongscore falt.

Neste kontrollforsøk kan teste retrening også av den sterke referansefamilien, samtidig som utvidet oppdatert HGB beholdes som selvstendig utfordrer. Hendelsesmodellen trenger komponentdiagnostikk og bedre rolle-/tilgjengelighetsdata. Ingen blending av nye undergrupper etter fasit. Data for xG starter i 2022/23; manglende verdier ble ikke fylt med framtidig informasjon.

172 tester bestått; 60 tidsriktige treningsvinduer kontrollert; alle 3672 nye beslutninger har optimal solverstatus innen toleransen. Kode, prognoser, treningsauditer, 108 spor og resultater ligger i `research/current/adaptive_events`. Ingen urørt holdout.


## Retrening av Ridge/Extra Trees og faste blandinger fullført

[Rapport](../research/current/retrained_ensemble/README.md). Fire nye kandidater og én matchet frossen treveiskontroll ga 60 nye sesongforløp. Utvidet HGB gjenbrukes uendret fra forrige runde. Samme før-frist-treningsvinduer, variabler, optimizer og åpning. 108 forløp sammenlignes totalt.

Retrenet Extra Trees er beskrivende primærvinner: 2253,5 poeng, +37,2 mot referansen, 4/6 seire og beskrivende 95 %-intervall [1,5; 73,3]. Den vinner i de tre siste sesongene. Retrenet 50/50 gir +30,5 og treveis +26,3. Retrenet Ridge alene gir −7,0. Extra Trees og Ridge forbedrer sine egne frosne kontroller med +68,8/+48,7, begge 5/6 seire.

Uten chips snur retreningseffekten for Extra og Ridge: −28,2/−14,7 mot egne kontroller. Mot sterk referanse gir Extra −39,0 og 50/50 −30,0. Treveisblandingen gir +10,3 uten chips, men −1,5 mot sin matchede frosne treveiskontroll. Ingen universell blandings- eller retreningsgevinst er dokumentert. Tidsordnet modellvalg gir −4,25 med chips og −10,25 uten. Ingen automatisk produksjonsendring.

Retrenet treveisblanding øker topp-20-treff på 8+ fra 23,97 % til 25,18 %, men dette forklarer ikke alene sesongscore. Behold Extra Trees som primær utfordrer og treveis som utfordrer på tvers av regimer. Neste spor er samspillet med chips/troppsendringer og prospektiv evaluering med låste regler.

173 tester bestått lokalt; 60 tidsriktige treningsvinduer, 2040 nye beslutninger og identisk åpning kontrollert. Alle nye solveravgjørelser er optimale innen toleransen. Kode, prognoser, auditer, 60 spor og resultater er lagret under `research/current/retrained_ensemble`. Ingen urørt holdout eller bekreftet GitHub CI-status.


## Chipmekanismer og scenariodiagnostikk fullført

[Rapport](../research/current/behavior_diagnostics/README.md). 12 prognosemodeller, 140 455 planlagte spiller–runder, 4536 nye beslutninger fra identisk referansetilstand og 144 nye chipablasjonsforløp. Ingen ny modelltrening. Opprinnelig diagnostikk låst før resultater; separat eksplorativ chipablasjon spesifisert etter de første regnskapsfunnene.

Extra Trees-retrening gir −28,2 uten chips og +68,8 med chips mot egen frossen kontroll: omslag +97,0. Direkte ekstra TC/BB-poeng forklarer bare +1,5; +70,7 kommer fra vanlig ellever, +18,2 vanlig kaptein og +6,7 endret treffkostnad. Mot sterk referanse er omslaget +76,2 og direkte bonuser −2,0. Dette er bokføring, ikke kausal allokering til tidligere bytter.

Kontrollerte hele-sesongablasjoner (retrent minus egen frossen): WC alene gir Ridge +20,0, Extra +39,0, 50/50 +31,2. WC+FH gir +37,8/+31,0/+44,8. TC+BB gir −9,2/+15,7/−6,5. Det finnes store samspillseffekter; mekaniske poengmultiplikatorer alene forklarer ikke resultatene. Fra identisk tropp gir retrent Extra bedre umiddelbare WC-valg, men dette gjelder ikke Ridge. Langsiktig troppshistorikk er viktig.

RMSE blant samme referanse-topp60 bedres litt av retrening av både Ridge og Extra i 6/6 sesonger, selv om deres chipfrie sesonggevinst faller. Utvidet HGB slår sterk referanse i topp10-rangering ved fallende minutter (+0,369 faktisk poeng per valgt spiller) og rotasjon (+0,270), begge 6/6 sesonger. Treveisblandingen gir +0,116 i samlet topp20 (5/6) og lavere relevant RMSE (6/6). Retrenet Ridge/Extra sliter relativt ved kort historikk; ingen gjennombruddsmodell er dokumentert. Dobbeltrunder er lovende for treveis, men har få kvalifiserende runder.

Ingen situasjonsstyrt ekspertregel er trent eller tatt i bruk. Scenarioer er overlappende og utforsket på kjente sesonger; konsistens er ikke en korrigert signifikanstest. 176 tester bestått lokalt. Alle nye 4536 matchede og 4896 ablasjonsbeslutninger har optimal status innen toleransen; 408 kontrollvalg gjenskaper arkivet. Kode, protokoller, scenariodata, beslutningsspor, auditer og fingeravtrykk er lagret under `research/current/behavior_diagnostics`. GitHub CI-status er ikke verifisert.


## Tre-rundersplanlegging og lært HGB-spesialist fullført

[Rapport](../research/current/decision_specialist/README.md). 72 nye H1/H3-forløp for frossen referanse, oppdatert Extra Trees og oppdatert Ridge/Extra 50/50 over seks sesonger. 16 nye gate-/globalvektforløp over fire sesonger, med to innledende metatreningssesonger. Primærmål er fortsatt nettosesongpoeng med fast chipkalender.

H3 med oppdatert 50/50 gir 2267,3 med chips, +51,0 mot referansen, 5/6 seire, beskrivende intervall [11,8;87,0]. Uten chips +31,2, 4/6, intervall over null. Mot egen H1 er gevinsten +20,5/+61,2 med/uten chips; primærintervallet inkluderer null, uten chips er intervallet [30,0;92,5]. Frossen referanse og Extra Trees får ingen stabil H3-gevinst. Kandidaten taper −37 mot referansen siste sesong. Tidsordnet primærvalg gir +35,5 over fire sesonger; uten chips −7,25.

Gate er en sigmoid-vekt mellom oppdatert 50/50 og utvidet HGB, med før-frist-spilletid og endring i spilletid. Globalvektkontrollen lærer bare konstantleddet. Begge bruker identiske eldre, tidsriktige komponentprognoser og labels tilgjengelige før GW1; ingen labels fra evalueringssesongen. Evalueringssesonger 2022/23–2025/26. Global HGB-vekt øker fra 42,5 % til 49,4 %; gate gir omtrent 55–59 % til HGB i rotasjonsgruppen.

Gate gir +62,0/+12,0 mot referansen med/uten chips; global vekt +54,25/+40,5. Begge vinner 4/4 med chips. Gate mot global kontroll er bare +7,75 med chips, bredt intervall [−68,25;62,5], og −28,5 uten. Gate mot fast treveis er +21,0/−22,5. Supplerende, etterfølgende benchmark mot retrent Extra på samme fire sesonger gir gate +7,5 med chips, men bare 1/4 seire; global vekt −0,25 med chips og +67,5 uten. Ingen robust generell ekspertregel er dokumentert. Tidsordnet gate/global/treveis-valg gir +28,5 med chips over bare to sesonger, +8,5 uten.

Fremtidsprognosen er en nøytral proxy: gammel frossen referansenøytral rate pluss aktuell oppdatert per-kamp-forskjell; aktuell kampeffekt halveres fremover, én kamp per runde. Blank aktuell runde bruker referansens nøytrale fallback. Ingen faktisk arkivert fremtidig før-frist-kalender. H3 kan ikke selge og gjenkjøpe en opprinnelig spiller innen samme plan. Samme historiske pris-/tilgjengelighets-/chipregelbegrensninger som før.

H1-motorparitet er eksplisitt målt. 50/50 gjenskaper alle gamle troppsvalg og sesongscorer; Extra/ref kan avvike gjennom likeverdige valg og små solvertoleranser. Dette er ikke horisontgevinst. Alle 2992 nye beslutninger er optimale innen sine toleranser, største H3-gap omtrent 1e-5. 179 tester bestått lokalt. Prognoser, koeffisienter, eldre-sesong-auditer, 88 spor, usikkerhet, valg og fingeravtrykk ligger i `research/current/decision_specialist`. Ingen urørt holdout eller bekreftet CI-status. Globalvekt+H3 er et forslag, ikke et utført forsøk.


## Global HGB-vekt med H3 fullført

[Rapport](../research/current/global_horizon/README.md). 16 nye forløp, 544 beslutninger, 32 forløp i matchet 2 × 2-design og 56 inkludert eksterne kontroller. Samme fire sesonger 2022/23–2025/26, samme lærte globale vekter, samme planlegger og fremtidsproxy. Ingen ny modelltrening.

Global H3 gir 2308,25 med chips, +70,0 mot referansen (4/4, beskrivende intervall [23;106,5]), og 2172,75 uten, +23,75 (3/4). Mot global H1 er det +15,75 med chips (bare 1/4, intervall [−10;58,25]) og −16,75 uten. Sesongvise primære horisonteffekter er −1,−13,+78,−1. Mot Ridge/Extra H3 er det +34,5 med chips (2/4) og −1,25 uten. Mot retrent Extra er det +15,5/+50,75, med brede intervaller over null.

Samspill mellom globalvekt og H3 er +21,25 med chips, usikkert, men −78,25 uten og negativt i alle fire sesonger. Tidligere forbedringer kan ikke summeres. Global H1 gjenskaper alle åtte gamle globalvektspor med samme tropper og poeng. Alle 544 nye beslutninger er optimale innen toleransen, maks gap 9,55e-6. Poengregnskap, starttilstand, spillerkobling og matchede før-frist-prognoser er kontrollert. Tre relevante eksisterende regresjonstester er kjørt på nytt og består; ingen ny full testkjøring påstås.

De to bekreftede utfordrerne beholdes; `constant_h3` legges til som forskningskandidat. Kode, protokoll, prognoser, spor, parete resultater og hashkontroller er lagret under `research/current/global_horizon`. Ingen produksjonsendring, urørt holdout eller verifisert GitHub CI-status.

