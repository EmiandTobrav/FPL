# Arbeidsrekkefølge: datagap først, deretter kvalitet og harmonisering

Oppdatert 9. oktober 2026 etter brukerens omprioritering og sesongblokkavstemmingen. [CURRENT.json](CURRENT.json) peker til gjeldende
ledger. Eldre avviks-, minutt- og restlister er historiske diagnoser.

## Gjeldende mål og faseorden

**Førsteprioritet er å lukke datagapene så effektivt og raskt som mulig.**
Den konkrete [operative målbeskrivelsen](../../../../docs/DATA_GAP_GOAL.md)
styrer arbeidet nå, med målbare leveranser og overgangskriterier for fasen.
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

**11 257 åpne feltkrav i 10 821 spillerkamper.** **66 459 spillerkamper og
824 hele kamper** har komplette input, av 77 280 og 2 660. [FPL-historikken](followup_2026_10_08/ferguson_fpl_history/README.md)
avklarer ett uttrekksunntak og gjør én spillerkamp komplett. Seks faktarettelser
lagres separat; native BPS 4 beholdes. Totalt **3 636 krav** er lukket siden
omprioriteringen. Alle straffemålkrav er allerede lukket. ESPN-foul/tackle/CBI-
rutene feiler og legges til side uten nye fakta. CURRENTs native_fpl_corrections-
peker skal brukes når neste kanoniske/poengversjon bygges; gamle labels bevares.
374 av 380 kamper i 2025/26 har tidligere kvalifiserte poengetiketter.
Ny omregning og full før-frist-/treningsintegrasjon følger senere.

Numerisk rest: 48 mållinjeklareringer, 1 238 times tackled, 545 CBI (341
manglende keeperverdier og 204 beskyttede konflikter), 2 keeperlokasjoner og
mindre grupper. Assists gjenstår i 9 291 rader. Alle 994 skuddkrav er allerede
lukket. [Keeperlokasjon](followup_2026_10_08/fotmob_keeper_location/README.md)
er direkte telt. [Primærens hele sesonger](followup_2026_10_08/primary_keeper_location/README.md) lukket ytterligere 14. De to siste Sánchez-kravene er sperret fordi kilde-/FPL-minutter avviker i kamp 47.
[CBI-V1](followup_2026_10_08/fotmob_cbi_conservation/README.md) feilet.
[Keeper-CBI-piloten](followup_2026_10_08/fotmob_keeper_cbi/README.md) gjenbrukte
640 råkamper og feilet på seks native avvik blant 569 keeperkontroller. Ingen
av 341 manglende keeperverdier anvendes. Ikke gjenta noen av disse rutene uten
fakta som forklarer avvikene eller en annen kompatibel kilde. Den nye
[arkivkildekontrollen](followup_2026_10_08/keeper_cbi_source_check/README.md)
gir samme klareringstall i de seks native vetoene; fem klareringstall alene
overstiger FPL-CBI. Ingen arkiv-only-rute eller ny primærbatch kvalifiseres.
Kvalitetsflagg er grupper for kilde-/feltdefinisjon, ikke manuelle celleoppgaver.
Gamle BPS-kontroller legges til side frem til nye fakta kan avklare motsetninger.

## Prioritert gjennomføring

**Innhenting styrer køen nedenfor.** De regelbaserte assistgruppenes betingede
tak skal ikke prioriteres som om alle var rene kildegap. Start fra
[innhentingsvisningen](priority/ACQUISITION_CURRENT.json): **2 549 krav**,
fordelt på manglende data/inventarer og kildekonflikter. Uttrekksunntaket er avklart.
Velg en kilde som faktisk kan tilføre manglende felt eller komplette hendelser;
bruk eksisterende kvalifiserte utfyllinger før utvikling av nye regler.
De **8 708 regelomregningskravene** er fortsatt åpne. Hent deres manglende
årsaksbevis i første fase; nye regelberegninger og større kontrollstudier
følger etter innhentingen. Ingen av disse tallene er et bevis på full dekning.

`python priority/acquisition_build.py` gjenskaper denne arbeidsvisningen fra
hashkontrollert CURRENT-restliste uten å endre ledgeren. Den separate
gruppefilen viser felt, sesong og type hindring; den hevder ingen forventet
lukking eller innbyrdes rangering uten et konkret gjennomførbart kildeforsøk.

| Arbeidsspor | Gjeldende omfang | Neste avgrensede handling |
|---|---|---|
| Manglende kildefelt og inventarer | 2 315 krav; blant annet 1 237 times tackled, 583 assistinventarer, 341 keeper-CBI og 48 mållinjekrav | Gjenbruk allerede innhentede spillerstatistikker og koblinger. Søk faktiske manglende tellere og komplette hendelser, med et lite kildeforsøk før masseinnhenting. De 21 tidligere arkivkampene har allerede statistikk/identiteter; deres hendelsesinventarer er fortsatt mangelfulle. Gamle API-/SDP-forsøk for times tackled og de feilede CBI-rutene skal ikke gjentas uten nye fakta. |
| Kildekonflikter og FPL-uttrekk | 234 konflikter; ingen åpne uttrekksunntak | Innhent manglende bevis eller en kompatibel kildeversjon som kan forklare avviket. Bevar FPL og godkjente verdier. Keeperlokasjonens to Sánchez-krav inngår blant manglende data, men er sperret av kilde-/minuttavvik; ikke fyll dem med proxyer. Ingen ny scoring for å omgå sperren. |
| Hendelsesbevis til senere assistomregning | 8 708 krav merket regelomregning, i tillegg til de 583 inventargapene over | Skaff faktisk mottak, foul/hands, berøringer, returer, intensjon og kontinuitet der dette mangler. Betingede lukkingstak nedenfor er hjelp til å velge kildeomfang, ikke forventet gevinst. Utsett nye assistregler og store kontrollstudier; bruk eksisterende kvalifiserte regler når nytt kildebevis gir rask utfylling. |
| Andre modellstatistikker og historiske inventarer | Egen dekningskartlegging; ikke talt som lukkede poengkrav | Hent manglende relevante xG/xA/xGI/xGC, defensive tellinger og faktiske frist-/roster-/statistikkversjoner. Gjenbruk kvalifiserte kampstarter og eksisterende statistikk. Ikke bygg features eller nye poengetiketter nå. |

Den gamle native2025-straffe-par-piloten ga samme prediksjonsomfang og bare ett
isolerbart selvtatt kontrollmål. Den beholdes som mislykket; se
[avsluttet kildeforsøk](followup_2026_10_08/penalty_pair_recovery/README.md).
Den nye historiske regelen er separat begrunnet med offisiell regelkompatibilitet,
53 kontrollmål og null feil; 53 selvtatte mål er allerede anvendt. Gjenværende
hands og uparrede fouls krever andre faktiske bevis.

Tabellen viser arbeidsspor i fase 1, ikke en tvungen rangering av felter.
Velg den konkrete innhentingen som gir raskest dokumenterbar utfylling. Samlet kvalitet,
regelgater for scoring, helkampbonus og treningsintegrasjon følger faseordenen
over. Ingen omprioritering reduserer datakrav eller senker kontrollgater.

## Oppdaterte assistavhengigheter

Dette er **betingede tak hvis alle resterende målbidrag i gruppen avklares**, ikke
prognoser eller nye avklaringer. Berørte krav overlapper og skal ikke summeres.
Tallene er beregnet etter alle kandidatgrenser; 583 inventar-/identitetsgap står
utenfor målgruppene. Gruppetak kan øke når andre blokkeringer fjernes.

| Gruppe | Mål | Berørte krav | Betinget lukkbare krav | Nye komplette spillerkamper | Nye hele kamper |
|---|---:|---:|---:|---:|---:|
| penalty | 132 | 1753 | 1610 | 1576 | 30 |
| source_not_assisted_marker | 758 | 2295 | 2076 | 2066 | 223 |
| paired_pass_with_intervening_events | 1028 | 1948 | 1732 | 1698 | 262 |
| assisted_goal_without_unique_pass_certificate | 391 | 1167 | 980 | 956 | 81 |
| own_goal | 228 | 890 | 818 | 804 | 50 |
| no_positive_goal_assist_certificate | 352 | 817 | 747 | 690 | 57 |
| direct_free_kick | 23 | 308 | 285 | 272 | 4 |

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

`python priority/build.py` bygger prioriteringsfilene fra gjeldende CURRENT
og den nye eksplisitte assisttotalpekeren (med gammel kompatibel fallback). ID-kolonnen leses nå som
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
