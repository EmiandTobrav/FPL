# Arbeidsrekkefølge for å fullføre harmoniseringen

Oppdatert 8. oktober 2026, keeperlokasjon. [CURRENT.json](CURRENT.json) peker til gjeldende
ledger. Eldre avviks-, minutt- og restlister er historiske diagnoser.

## Nåværende status

**14 907 åpne feltkrav i 13 745 spillerkamper.** **63 535 spillerkamper og
752 hele kamper** har komplette input, av 77 280 og 2 660. Siste batch lukket
326 lokasjonskrav og ga 326 nye komplette spillerkamper og 244 nye hele kamper.
363 av 380 kamper i 2025/26 er nå også poengkvalifisert: 10 971 spillerkamper
med ny BPS, helkampbonus og avstemte totalpoeng. Se
[egen sesongversjon](../../training_dataset/scoring/season_2025/README.md).
Alle eldre regelsesonger og full før-frist-/treningsintegrasjon gjenstår.

Numerisk rest: 2 992 mållinjeklareringer, 1 238 times tackled, 545 CBI (341
manglende keeperverdier og 204 beskyttede konflikter), 16 keeperlokasjoner og
mindre grupper. Assists gjenstår i 9 926 rader. Alle 994 skuddkrav er allerede
lukket. [Keeperlokasjon](followup_2026_10_08/fotmob_keeper_location/README.md)
er direkte telt; de siste 16 kravene har uenige redningsantall.
[CBI-V1](followup_2026_10_08/fotmob_cbi_conservation/README.md) feilet. Gjenbruk
råsvar for et korrekt keeperrettet kontrollopplegg; ikke gjenta generell mapping.
Kvalitetsflagg er grupper for kilde-/feltdefinisjon, ikke manuelle celleoppgaver.
Gamle BPS-kontroller legges til side frem til nye fakta kan avklare motsetninger.

## Prioritert gjennomføring

| Prioritet | Gruppe / forventet gevinstgrunnlag | Neste avgrensede handling |
|---|---|---|
| 0 | 363 kvalifiserte 2025/26-poengkamper; 17 sperrede kamper | Scoringversjonen er levert og kvalifisert. Fullfør resterende lokasjonsteller-/times-tackled-konflikter og avstem Kellehers nye BCS-revisjon i kamp 337 med kildene; godkjent gammel keeperverdi bevares. Bygg kanoniske runde-/ikke-deltakelseslabels, før-frist-features og faktisk treningsinnlesing. Fortsett hele den historiske restlisten; ikke gjenta ferdig kvalifisering uten nye avvik. |
| 1 | Straffer: 185 mål, betinget 2 245 lukkbare krav; direkte frispark ytterligere 273 | Del ordinært foul, selvtatt straffe og hands etter faktisk hendelsesbevis. Gjenbruk den frosne straffefoul-prediktoren og kildene; ordinære positive avgjørelser er allerede anvendt fra tidligere rute. Nye selvtatte tilfeller trenger tilstrekkelig målspesifikk tidsordnet eller uavhengig kontroll. Den gamle piloten har bare seks relevante enmåls-kontroller og ingen selvtatte: ikke senk gaten eller gjenta den som ny validering. Planlegg ny kontroll før fasit, og mål hvilke hele kamper den kan ferdigstille. |
| 2 | Pasninger med mellomliggende hendelser: 1 711 betinget lukkbare krav og 235 hele kamper | Bruk de gjenværende faktiske kandidatene og samle like årsaksforløp. Kvalifiser mottaker, intensjon/mottakssted, forsvarskontakt, returer og kontinuitet før målavgjørelse. Skill slettede rader og dueller fra faktiske berøringer. Alle fire nye kandidatregler er allerede brukt over hele populasjonen; et nytt trekk må tilføre nye fakta eller en ny kvalifisert årsaksregel. |
| 3 | Mållinjeklareringer: 2 992; 2 598 bak fem manglende sesongtotaler | Krev en dokumentert ny kilde for eksplisitte totaler eller et kvalifisert komplett inventar. Tidligere fullstatistikk/rangeringer omitterer totalene. Nytt offisielt SDP-endepunkt for Man Utd 2019/20 omitterer også feltet; stats/comp/1-forsøket ga404. Ingen tom rangering, API-utelatelse eller positiv rest er null. Ikke kjør samme mislykkede kildebatch igjen. |
| 4 | Øvrige assistårsaker: source-not-assisted, uklart pasningssertifikat, selvmål og returer | Bruk oppdaterte mål–spiller-avhengigheter nedenfor. Source-not-assisted har 2 071 betinget lukkbare krav, men er ikke i seg selv et nullbevis. Prioriter positive, sammenhengende handlingsforløp og de tilfellene som faktisk fullfører kamper; behold usikre utfall. |
| 5 | Resterende tellere og arkivgap | 1 237 times-tackled-krav er fra 2019/20; ett er en beskyttet 2025/26-konflikt. Den gamle spiller-API-en og den nye SDP-kamppiloten gir ikke dette manglende spillerfeltet. Prioriter schema/paring av faktiske forsvarshendelser og komplett inventar, ingen dribleproxy. Alle manglende CBI-verdier er keepere; kvalifiser en relevant primær-/FotMob-komponentrute med fryste kontrollkrav. Keeperlokasjon har nå 16 konkrete redningskonflikter; ingen lokasjonsproxy eller differanseberegning. De 21 tidligere arkivkampene har fortsatt 761 åpne krav; statistikk/identiteter er allerede hentet, men komplette hendelsesinventarer mangler. |
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
