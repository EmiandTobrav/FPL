# Arbeidsrekkefølge for å fullføre harmoniseringen

Oppdatert 8. oktober 2026, batch 3. [CURRENT.json](CURRENT.json) peker til gjeldende
ledger. Eldre avviks-, minutt- og restlister er historiske diagnoser.

## Nåværende status

**16 227 åpne feltkrav i 14 990 unike spillerkamper.** **62 290 spillerkamper og
490 hele kamper** har komplette inputfelt, av 77 280 og 2 660. Siste batch lukket
8 058 krav (33,18 %), ga 7 506 nye komplette spillerkamper og én ny hel kamp.
Assists er redusert fra 17 984 til **9 926**. Ingen nye poeng/BPS/bonus er beregnet.

Den store forskjellen mellom spiller- og kampfremdrift er reell: konservative
kandidatgrenser har avklart mange spillere, men mange mål har fortsatt én eller
få mulige assistgivere som ikke er endelig kvalifisert. Neste innsats bør derfor
avklare de resterende målbidragene, ikke gjenta allerede anvendte kandidatregler.

Numerisk rest er uendret i denne batchen: 2 992 mållinjeklareringer, 1 238 times
tackled, 994 SOT, 545 CBI, 342 keeperlokasjoner og mindre grupper. Se
[feltsammendraget](followup_2026_10_08/bulk_batch3/results/field_summary.csv).
Kvalitetsflagg: 581 858 kravrader i 73 felt-/sesonggrupper. Dette er ikke like
mange manuelle oppgaver. Åpen-/kvalitetsunionen er 77 214 spillerkamper.

## Prioritert gjennomføring

| Prioritet | Gruppe / forventet gevinstgrunnlag | Neste avgrensede handling |
|---|---|---|
| 1 | Straffer: 185 mål, betinget 2 245 lukkbare krav; direkte frispark ytterligere 273 | Del ordinært foul, selvtatt straffe og hands etter faktisk hendelsesbevis. Gjenbruk den frosne straffefoul-prediktoren og kildene; ordinære positive avgjørelser er allerede anvendt fra tidligere rute. Nye selvtatte tilfeller trenger tilstrekkelig målspesifikk tidsordnet eller uavhengig kontroll. Den gamle piloten har bare seks relevante enmåls-kontroller og ingen selvtatte: ikke senk gaten eller gjenta den som ny validering. Planlegg ny kontroll før fasit, og mål hvilke hele kamper den kan ferdigstille. |
| 2 | Pasninger med mellomliggende hendelser: 1 711 betinget lukkbare krav og 235 hele kamper | Bruk de gjenværende faktiske kandidatene og samle like årsaksforløp. Kvalifiser mottaker, intensjon/mottakssted, forsvarskontakt, returer og kontinuitet før målavgjørelse. Skill slettede rader og dueller fra faktiske berøringer. Alle fire nye kandidatregler er allerede brukt over hele populasjonen; et nytt trekk må tilføre nye fakta eller en ny kvalifisert årsaksregel. |
| 3 | Mållinjeklareringer: 2 992; 2 598 bak fem manglende sesongtotaler | Krev en dokumentert ny kilde for eksplisitte totaler eller et kvalifisert komplett inventar. Tidligere fullstatistikk/rangeringer omitterer totalene. Nytt offisielt SDP-endepunkt for Man Utd 2019/20 omitterer også feltet; stats/comp/1-forsøket ga404. Ingen tom rangering, API-utelatelse eller positiv rest er null. Ikke kjør samme mislykkede kildebatch igjen. |
| 4 | Øvrige assistårsaker: source-not-assisted, uklart pasningssertifikat, selvmål og returer | Bruk oppdaterte mål–spiller-avhengigheter nedenfor. Source-not-assisted har 2 071 betinget lukkbare krav, men er ikke i seg selv et nullbevis. Prioriter positive, sammenhengende handlingsforløp og de tilfellene som faktisk fullfører kamper; behold usikre utfall. |
| 5 | Resterende tellere og arkivgap | 1 237 times-tackled-krav er fra 2019/20; ett er en beskyttet 2025/26-konflikt. Den gamle spiller-API-en og den nye SDP-kamppiloten gir ikke dette manglende spillerfeltet. Prioriter schema/paring av faktiske forsvarshendelser og komplett inventar, ingen dribleproxy. Grupper SOT/CBI/keeperlokasjon etter felles manglende komponent eller restsum før kildepilot. De 21 tidligere arkivkampene har fortsatt 761 åpne krav; statistikk/identiteter er allerede hentet, men komplette hendelsesinventarer mangler. |
| 6 | Kvalitets- og regelgater, deretter scoring | Kvalifiser felt-/sesonggrupper samlet. Behold uendrede historiske BPS-komponenter; verifiser endrede ledd, klipping/avrunding og godkjente revisjoner før omberegning. Ranger bonus for alle deltakere i hele kvalifiserte kamper. Låste labels/modeller/benchmark beholdes, ingen modelltrening før datakvalifisering. |

## Oppdaterte assistavhengigheter

Dette er **betingede tak hvis alle resterende målbidrag i gruppen avklares**, ikke
prognoser eller nye avklaringer. Berørte krav overlapper og skal ikke summeres.
Tallene er beregnet etter alle kandidatgrenser; 583 inventar-/identitetsgap står
utenfor målgruppene. Gruppetak kan øke når andre blokkeringer fjernes.

| Gruppe | Mål | Berørte krav | Betinget lukkbare krav | Nye komplette spillerkamper | Nye hele kamper |
|---|---:|---:|---:|---:|---:|
| penalty | 185 | 2449 | 2245 | 2016 | 35 |
| source_not_assisted_marker | 758 | 2295 | 2071 | 1994 | 202 |
| paired_pass_with_intervening_events | 1028 | 1948 | 1711 | 1612 | 235 |
| assisted_goal_without_unique_pass_certificate | 391 | 1167 | 975 | 907 | 68 |
| own_goal | 228 | 890 | 817 | 782 | 44 |
| no_positive_goal_assist_certificate | 352 | 817 | 731 | 556 | 46 |
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
`python followup_2026_10_08/bulk_batch3/reproduce.py` gjenskaper den nye batchen i
separat kopi uten nettverk eller bootstrap. 15 nye testmetoder bestod. Full
repositorietest og GitHub CI er ikke bekreftet. Se replayrapporten for filkontrollen.
