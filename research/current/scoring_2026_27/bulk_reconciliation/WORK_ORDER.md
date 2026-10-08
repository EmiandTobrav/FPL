# Arbeidsrekkefølge for å fullføre harmoniseringen

Oppdatert 8. oktober 2026, keeperlokasjon. [CURRENT.json](CURRENT.json) peker til gjeldende
ledger. Eldre avviks-, minutt- og restlister er historiske diagnoser.

## Nåværende status

**14 893 åpne feltkrav i 13 731 spillerkamper.** **63 549 spillerkamper og
766 hele kamper** har komplette input, av 77 280 og 2 660. Siste primærbatch
lukket 14 lokasjonskrav og ga 14 nye komplette spillerkamper og hele kamper.
374 av 380 kamper i 2025/26 er poengkvalifisert: 11 315 spillerkamper med
ny BPS, helkampbonus og avstemte totalpoeng. Se
[utvidet sesongversjon](../../training_dataset/scoring/season_2025_extension/README.md).
Alle eldre regelsesonger og full før-frist-/treningsintegrasjon gjenstår.

Numerisk rest: 2 992 mållinjeklareringer, 1 238 times tackled, 545 CBI (341
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
| 0 | 374 kvalifiserte 2025/26-poengkamper; felles tabeller/innlesing levert | Fullfør resterende lokasjonsteller-/times-tackled-konflikter og bevar Kellehers nye BCS-revisjon i kamp 337 som sperre. Kvalifiser historiske ikke-deltakelses-/blankrundelabels med null-minutt-kort bevart. Skaff faktiske frister, før-frist-rosters og statistikkversjoner; bygg features og verifiser nye treningsrader gjennom innlesingen. Fortsett hele den historiske restlisten. |
| 1 | Straffer: 185 mål, betinget 2 245 lukkbare krav; direkte frispark ytterligere 273 | Del ordinært foul, selvtatt straffe og hands etter faktisk hendelsesbevis. Gjenbruk den frosne straffefoul-prediktoren og kildene; ordinære positive avgjørelser er allerede anvendt fra tidligere rute. Nye selvtatte tilfeller trenger tilstrekkelig målspesifikk tidsordnet eller uavhengig kontroll. Den gamle piloten har bare seks relevante enmåls-kontroller og ingen selvtatte: ikke senk gaten eller gjenta den som ny validering. Planlegg ny kontroll før fasit, og mål hvilke hele kamper den kan ferdigstille. |
| 2 | Pasninger med mellomliggende hendelser: 1 711 betinget lukkbare krav og 235 hele kamper | Bruk de gjenværende faktiske kandidatene og samle like årsaksforløp. Kvalifiser mottaker, intensjon/mottakssted, forsvarskontakt, returer og kontinuitet før målavgjørelse. Skill slettede rader og dueller fra faktiske berøringer. Alle fire nye kandidatregler er allerede brukt over hele populasjonen; et nytt trekk må tilføre nye fakta eller en ny kvalifisert årsaksregel. |
| 3 | Mållinjeklareringer: 2 992; 2 598 bak fem manglende sesongtotaler | Krev en dokumentert ny kilde for eksplisitte totaler eller et kvalifisert komplett inventar. Tidligere fullstatistikk/rangeringer omitterer totalene. Nytt offisielt SDP-endepunkt for Man Utd 2019/20 omitterer også feltet; stats/comp/1-forsøket ga404. Ingen tom rangering, API-utelatelse eller positiv rest er null. Ikke kjør samme mislykkede kildebatch igjen. |
| 4 | Øvrige assistårsaker: source-not-assisted, uklart pasningssertifikat, selvmål og returer | Bruk oppdaterte mål–spiller-avhengigheter nedenfor. Source-not-assisted har 2 071 betinget lukkbare krav, men er ikke i seg selv et nullbevis. Prioriter positive, sammenhengende handlingsforløp og de tilfellene som faktisk fullfører kamper; behold usikre utfall. |
| 5 | Resterende tellere og arkivgap | 1 237 times-tackled-krav er fra 2019/20; ett er en beskyttet 2025/26-konflikt. Den gamle spiller-API-en og den nye SDP-kamppiloten gir ikke dette manglende spillerfeltet. Prioriter schema/paring av faktiske forsvarshendelser og komplett inventar, ingen dribleproxy. Alle manglende CBI-verdier er keepere; kvalifiser en relevant primær-/FotMob-komponentrute med fryste kontrollkrav. Keeperlokasjon har nå to beskyttede Sánchez-krav med én minutts kildeavvik i sesonginventaret; ingen lokasjonsproxy eller differanseberegning. De 21 tidligere arkivkampene har fortsatt 761 åpne krav; statistikk/identiteter er allerede hentet, men komplette hendelsesinventarer mangler. |
| 6 | Kvalitets- og regelgater, deretter scoring | Kvalifiser felt-/sesonggrupper samlet. Behold uendrede historiske BPS-komponenter; verifiser endrede ledd, klipping/avrunding og godkjente revisjoner før omberegning. Ranger bonus for alle deltakere i hele kvalifiserte kamper. Låste labels/modeller/benchmark beholdes, ingen modelltrening før datakvalifisering. |

## Oppdaterte assistavhengigheter

Dette er **betingede tak hvis alle resterende målbidrag i gruppen avklares**, ikke
prognoser eller nye avklaringer. Berørte krav overlapper og skal ikke summeres.
Tallene er beregnet etter alle kandidatgrenser; 583 inventar-/identitetsgap står
utenfor målgruppene. Gruppetak kan øke når andre blokkeringer fjernes.

| Gruppe | Mål | Berørte krav | Betinget lukkbare krav | Nye komplette spillerkamper | Nye hele kamper |
|---|---:|---:|---:|---:|---:|
| penalty | 185 | 2449 | 2245 | 2016 | 37 |
| source_not_assisted_marker | 758 | 2295 | 2071 | 1994 | 207 |
| paired_pass_with_intervening_events | 1028 | 1948 | 1711 | 1612 | 243 |
| assisted_goal_without_unique_pass_certificate | 391 | 1167 | 975 | 907 | 73 |
| own_goal | 228 | 890 | 817 | 783 | 46 |
| no_positive_goal_assist_certificate | 352 | 817 | 731 | 556 | 47 |
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

## Siste reproduksjon og konkret neste featurekilde

Primærbatchens syv tester og fem nye integrasjonstester består. Tolv
primærresultater, tolv utvidede poengresultater og syv kanoniske resultater
har egne byteidentiske replays. Samlet treningsdatasett-replay gjenskaper
145 resultatfiler, med alle tidligere fryste versjoner bevart.

[Bootstrap-arkivpiloten](../../bootstrap_availability_pilot/fplcache/README.md)
bevarer ett faktisk 2025/26-snapshot før GW1-fristen, 685 spillerkoder,
kildeversjon og collector-oppsett. Før-frist-kvalifisering er fortsatt false;
hele tids-/univers-/statistikk-kontrollen og de tidlige sesongene gjenstår.
