# Arbeidsrekkefølge: datagap først, deretter kvalitet og harmonisering

Oppdatert 9. oktober 2026 etter brukerens omprioritering og sesongblokkavstemmingen. [CURRENT.json](CURRENT.json) peker til gjeldende
ledger. Eldre avviks-, minutt- og restlister er historiske diagnoser.

## Gjeldende mål og faseorden

**Førsteprioritet er å lukke datagapene så effektivt og raskt som mulig.**
Sluttleveransen er fortsatt et reproduserbart, treningsklart datasett for
2019/20–2025/26 og avsluttede runder i 2026/27. Brukerens nye rekkefølge
erstatter tidligere prioritering av scoring, labels og features:

1. Innhent manglende statistikk og hendelsesbevis, og anvend kvalifiserte
   utfyllinger gruppevis på den gjeldende restlisten. Ta med manglende relevante
   modellstatistikker og nødvendige historiske inventarer i innhentingen.
2. Kvalitetssikre det samlede datagrunnlaget: definisjoner, identiteter,
   dekning, duplikater, konsistens og sammenlignbarhet mellom sesonger.
3. Omregn BPS, bonus, assists, defcon og øvrige poeng til 2026/27; bygg nye
   poengetiketter etter at nødvendig datagrunnlag er kvalifisert.
4. Bygg fristsikre features og treningsvisninger, og verifiser innlesingen.
   Modelltrening er fortsatt en senere oppgave.

Faste kilde-/regelkontroller som kreves før en masseutfylling, inngår i fase 1.
Den samlede kvalitetssikringen i fase 2 skal ikke brukes som grunn til å utsette
innhenting fra uavhengige feltgrupper. Rekonstruksjon av manglende statistikk
fra hendelser er datagaparbeid; ny BPS-/bonus-/totalpoengberegning er fase 3.
Eksisterende kvalifiserte poengversjoner bevares, men utvides ikke nå.

## Effektivitet og rapportering i datagapfasen

- Velg neste batch etter forventede dokumenterbare feltlukkinger per tidsbruk,
  gjenbrukbarhet og mulighet for å fullføre hele kamper. Store grupper er
  kandidater, ikke et krav om å bli stående i den vanskeligste gruppen.
- Gjenbruk rådata, identitetskoblinger, kvalifiserte regler og kontroller.
  Kjør et lite, målrettet kildeforsøk før en stor innhenting.
- Hvis forsøket mangler nødvendige felt eller feiler kontrollen, registrer den
  konkrete hindringen og gå videre til neste gjennomførbare gruppe. Gjenta
  forsøket bare når nye fakta eller en annen kompatibel kilde gir grunnlag.
- Rapporter faktisk antall lukkede krav og resttall før/etter hver batch,
  nye inputkomplette spillerkamper/hele kamper og kildebelegg. Dokumentasjon,
  kildefunn og poengberegninger teller ikke som lukkede datagap.
- Bevar manglende verdier og beskyttede konflikter. En dokumentert hindring
  er fortsatt et åpent krav, og betingede gruppetak er ikke realiserte lukkinger.
- Ikke gjenta omfattende replay eller bygge scoring/features for hver
  datainnhentingsbatch. Verifiser de berørte utfyllingene og deres reproduksjon;
  samlet kontroll følger i fase 2. Eksisterende kontrollgater beholdes.

## Nåværende status

**12 476 åpne feltkrav i 11 834 spillerkamper.** **65 446 spillerkamper og
768 hele kamper** har komplette input, av 77 280 og 2 660. Siste
[sesongblokkavstemming](followup_2026_10_08/goal_line_season_blocks/README.md)
lukket 303 krav og ga 241 nye komplette spillerkamper. Den forrige
[hendelsesbatchen](followup_2026_10_08/goal_line_events/README.md) lukket 2 114
krav og ga 1 656 nye komplette spillerkamper og to hele kamper.
374 av 380 kamper i 2025/26 er poengkvalifisert: 11 315 spillerkamper med
ny BPS, helkampbonus og avstemte totalpoeng. Se
[utvidet sesongversjon](../../training_dataset/scoring/season_2025_extension/README.md).
Alle eldre regelsesonger og full før-frist-/treningsintegrasjon gjenstår.

Numerisk rest: 575 mållinjeklareringer, 1 238 times tackled, 545 CBI (341
manglende keeperverdier og 204 beskyttede konflikter), 2 keeperlokasjoner og
mindre grupper. Assists gjenstår i 9 926 rader. Alle 994 skuddkrav er allerede
lukket. [Keeperlokasjon](followup_2026_10_08/fotmob_keeper_location/README.md)
er direkte telt. [Primærens hele sesonger](followup_2026_10_08/primary_keeper_location/README.md) lukket ytterligere 14. De to siste Sánchez-kravene er sperret fordi kilde-/FPL-minutter avviker i kamp 47.
[CBI-V1](followup_2026_10_08/fotmob_cbi_conservation/README.md) feilet.
[Keeper-CBI-piloten](followup_2026_10_08/fotmob_keeper_cbi/README.md) gjenbrukte
640 råkamper og feilet på seks native avvik blant 569 keeperkontroller. Ingen
av 341 manglende keeperverdier anvendes. Ikke gjenta noen av disse rutene uten
fakta som forklarer avvikene eller en annen kompatibel kilde.
Kvalitetsflagg er grupper for kilde-/feltdefinisjon, ikke manuelle celleoppgaver.
Gamle BPS-kontroller legges til side frem til nye fakta kan avklare motsetninger.

## Prioritert gjennomføring

| Prioritet | Gruppe / forventet gevinstgrunnlag | Neste avgrensede handling |
|---|---|---|
| 1 | Straffer: 185 mål, betinget 2 245 lukkbare krav; direkte frispark ytterligere 273 | Del ordinært foul, selvtatt straffe og hands etter faktisk hendelsesbevis. Gjenbruk den frosne straffefoul-prediktoren og kildene; ordinære positive avgjørelser er allerede anvendt fra tidligere rute. Nye selvtatte tilfeller trenger tilstrekkelig målspesifikk tidsordnet eller uavhengig kontroll. Den gamle piloten har bare seks relevante enmåls-kontroller og ingen selvtatte: ikke senk gaten eller gjenta den som ny validering. Planlegg ny kontroll før fasit, og mål hvilke hele kamper den kan ferdigstille. |
| 2 | Pasninger med mellomliggende hendelser: 1 711 betinget lukkbare krav og 243 hele kamper | Bruk de gjenværende faktiske kandidatene og samle like årsaksforløp. Kvalifiser mottaker, intensjon/mottakssted, forsvarskontakt, returer og kontinuitet før målavgjørelse. Skill slettede rader og dueller fra faktiske berøringer. Alle fire nye kandidatregler er allerede brukt over hele populasjonen; et nytt trekk må tilføre nye fakta eller en ny kvalifisert årsaksregel. |
| 3 | Mållinjeklareringer: 575 etter 2 114 hendelseslukkinger og 303 sesongavklaringer | Alle 120 primære lag–sesong-blokktotaler er eksakt avstemt og lukker hele den gamle gruppen med 249 ukvalifiserte blokkinventarer, samt 54 minuttilfeller med en ny bevis for null for hele laget uavhengig av individuelle minutter. FPL-minutter bevares. Resterende 536 spiller-minuttilfeller trenger feltspesifikk identitets-/inventarkvalifisering; 39 positive-blokk-arkivgap trenger faktiske hendelser. Ikke gjenkjør gamle BPS/minutt- eller tomme mållinjerangeringer. |
| 4 | Øvrige assistårsaker: source-not-assisted, uklart pasningssertifikat, selvmål og returer | Bruk oppdaterte mål–spiller-avhengigheter nedenfor. Source-not-assisted har 2 071 betinget lukkbare krav, men er ikke i seg selv et nullbevis. Prioriter positive, sammenhengende handlingsforløp og de tilfellene som faktisk fullfører kamper; behold usikre utfall. |
| 5 | Resterende tellere og arkivgap | 1 237 times-tackled-krav er fra 2019/20; ett er en beskyttet 2025/26-konflikt. Den gamle spiller-API-en og den nye SDP-kamppiloten gir ikke dette manglende spillerfeltet. Prioriter schema/paring av faktiske forsvarshendelser og komplett inventar, ingen dribleproxy. Alle manglende CBI-verdier er keepere; kvalifiser en relevant primær-/FotMob-komponentrute med fryste kontrollkrav. Keeperlokasjon har nå to beskyttede Sánchez-krav med én minutts kildeavvik i sesonginventaret; ingen lokasjonsproxy eller differanseberegning. De 21 tidligere arkivkampene har fortsatt 761 åpne krav; statistikk/identiteter er allerede hentet, men komplette hendelsesinventarer mangler. |
| 6 | Andre manglende modellstatistikker og historiske inventarer | Fullfør innhenting av relevante xG/xA/xGI/xGC, kampstarter, defensive tellinger og faktiske frister/roster-/statistikkversjoner der disse mangler. Gjenbruk allerede innhentede data; ukvalifiserte felter beholdes separat til samlet kvalitetssikring. Ikke bygg features eller nye poenglabels i denne fasen. |

Straffe-par-piloten ga samme prediksjonsomfang som før og bare ett isolerbart
selvtatt kontrollmål. Den gir ingen ny kvalifisering eller lukking; se
[avsluttet kildeforsøk](followup_2026_10_08/penalty_pair_recovery/README.md).
Gå videre til en gjennomførbar inventargruppe mens nye straffebevis mangler.

Tabellen er en startkø for fase 1. Velg en annen gjennomførbar gruppe hvis
den gir raskere dokumenterbar lukking enn gruppen foran. Samlet kvalitet,
regelgater for scoring, helkampbonus og treningsintegrasjon følger faseordenen
over. Ingen omprioritering reduserer datakrav eller senker kontrollgater.

## Oppdaterte assistavhengigheter

Dette er **betingede tak hvis alle resterende målbidrag i gruppen avklares**, ikke
prognoser eller nye avklaringer. Berørte krav overlapper og skal ikke summeres.
Tallene er beregnet etter alle kandidatgrenser; 583 inventar-/identitetsgap står
utenfor målgruppene. Gruppetak kan øke når andre blokkeringer fjernes.

| Gruppe | Mål | Berørte krav | Betinget lukkbare krav | Nye komplette spillerkamper | Nye hele kamper |
|---|---:|---:|---:|---:|---:|
| penalty | 185 | 2449 | 2245 | 2163 | 37 |
| source_not_assisted_marker | 758 | 2295 | 2071 | 2048 | 207 |
| paired_pass_with_intervening_events | 1028 | 1948 | 1711 | 1657 | 243 |
| assisted_goal_without_unique_pass_certificate | 391 | 1167 | 975 | 939 | 73 |
| own_goal | 228 | 890 | 817 | 799 | 47 |
| no_positive_goal_assist_certificate | 352 | 817 | 731 | 654 | 47 |
| direct_free_kick | 23 | 308 | 273 | 265 | 4 |

## Kontroller og kildeprioritet

Historisk FPL er fasit for eksisterende, regelkompatible felt, minutter og
uttrykkelige nuller. Eksterne kilder fyller bare manglende/nye variabler og
nødvendige regelomregninger. Manglende data er ikke null; ingen xG-imputering av
storsjanseredninger. Rå FPL, godkjente keeperverdier, offisielle hendelsesrettelser,
frosne kontroller og låste modeller beholdes. Manuell kontroll brukes på unntak.

De nye reglene har hver sine frosne prediksjoner og beståtte kontrollgater.
Alle kvalifiserte gamle og nye kandidatgrenser er dessuten kontrollert sammen:
566 lagvektorer i 353 kamper, ingen uforenlige summer eller konflikt med tvungne,
tidligere godkjente mål-assists. Kontrollene deler Opta-kilde og tidligere sett
fasit; de er regresjon, ikke nye uavhengige holdout-observasjoner.

`python priority/build.py` bygger prioriteringsfilene. ID-kolonnen leses nå som
tekst, slik at et enkelt mål-ID ikke feiltolkes som flyttall i pandas-chunker.
`python followup_2026_10_08/fotmob_keeper_location/reproduce.py` gjenskaper den nye keeperlokasjonsbatchen i
separat kopi uten nettverk eller bootstrap. Ti nye lokasjonstester består. Elleve keeperresultater gjenskapes byteidentisk;
den tidligere skuddbatchens tolv og den mislykkede CBI-studiens tolv resultater
er også reprodusert byteidentisk. Eldre
94 beregnings-/kontrollresultater bevares og reproduseres med originalpeker. Full
repositorietest og GitHub CI er ikke bekreftet. Se replayrapporten for filkontrollen.

## Bevarte reproduksjonsresultater og innhentet arkivkilde

Primærbatchens syv tester og fem nye integrasjonstester består. Tolv
primærresultater, tolv utvidede poengresultater og syv kanoniske resultater
har egne byteidentiske replays. Samlet treningsdatasett-replay gjenskaper
145 resultatfiler, med alle tidligere fryste versjoner bevart.

[Bootstrap-arkivpiloten](../../bootstrap_availability_pilot/fplcache/README.md)
bevarer ett faktisk 2025/26-snapshot før GW1-fristen, 685 spillerkoder,
kildeversjon og collector-oppsett. Før-frist-kvalifisering er fortsatt false;
hele tids-/univers-/statistikk-kontrollen og de tidlige sesongene gjenstår.
