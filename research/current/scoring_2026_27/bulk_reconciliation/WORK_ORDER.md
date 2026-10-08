# Arbeidsrekkefølge for å fullføre harmoniseringen

Oppdatert 8. oktober 2026, etter batch 2. [CURRENT.json](CURRENT.json) er fasit for
filene. Eldre rest-, avviks- og minuttlister er historiske diagnoser.

## Gjeldende status

**24 285 åpne feltkrav i 22 496 unike spillerkamper.** 54 784 spillerkamper og
489 hele kamper har nødvendige inputfelt, av 77 280 og 2 660. Siste batch lukket
4 649 krav (16,07 %), ga 2 220 nye komplette spillerkamper og 10 nye hele kamper.

Assists står for **17 984 krav (74,1 %)**. Mållinjeklareringer: 2 992; times tackled:
1 238; skudd på mål: 994; CBI: 545; keeperlokasjon: 342. Se
[alle felt](followup_2026_10_08/bulk_batch2/results/field_summary.csv).
Kvalitetskontroll er separat: 573 800 flaggede rader i 73 felt-/sesonggrupper,
ikke like mange manuelle oppgaver. Kvalitets-/åpen-unionen er 77 214 spillerkamper.
Ingen nye poeng-, BPS-, bonus- eller modellresultater er kvalifisert.

## Neste arbeid, prioritert etter felles årsak og beviskostnad

| Prioritet | Gruppe | Avgrenset handling og skaleringskrav |
|---|---|---|
| 1 | Store assistgrupper med positivt hendelsesbelegg | Pilotér vanlige mellomliggende hendelsesforløp og normaliserte kildebelegg. Den kvalifiserte to-forsvarspasninger-regelen er allerede kjørt på hele populasjonen og skal ikke telles på nytt. Skill faktiske kontakter, dueller og slettede rader; slettede hendelser er bare undersøkt, ingen ny regel er anvendt. Frys nye kandidatutelukkelser eller årsaksregler før tidsordnet kontroll, og skalér bare beståtte undergrupper. Bruk oppdaterte avhengigheter nedenfor. |
| 2 | Mållinjeklareringer: 2 992 | 2 598 ligger fortsatt bak fem manglende eksplisitte lag-/sesongtotaler, 355 bak positive ufordelte rester og 39 i den tidligere arkivgruppen. Prøv bare en dokumentert ny kildevei. Team/12 season/274 fullstatistikk omitterer fortsatt telleren; stats/comp/1-piloten returnerte 404. Ingen ny runde med tomme rangeringer eller gjetting av URL-varianter. Krev eksplisitt total eller kvalifisert komplett inventar; positiv rest og manglende total gir ikke null. |
| 3 | Assists uten ferdig årsaksbevis, inkludert straffer | Source-not-assisted er fortsatt største betingede potensial, men markøren alene er ikke nullbevis. Kjør representative retur-/forsvarskontakt-/hands-/dødballpiloter. Straffefoul-piloten har bare seks relevante enmåls-kontroller og ingen self-won-kontroller: ingen anvendelse før tilstrekkelig ny evidens. Ikke senk kontrollkravet for å lukke felter. |
| 4 | Resterende numeriske fellesgrupper | 1 237 times-tackled-krav er fra 2019/20, ett er en beskyttet 2025/26-konflikt. De nye primærsvarene mangler fortsatt 2019-telleren; ikke repeter denne innsamlingsruten. Prioriter schema/paring og komplett inventar fra faktiske forsvarshendelser, uten drible-/balltapsproxy. For 994 SOT, 545 CBI og 342 keeperlokasjoner: grupper etter manglende komponent, kildeperiode og positiv rest før en avgrenset kildepilot. Eksplisitte konflikter holdes adskilt. |
| 5 | Gjenværende arkiv-/hendelsesgap | De 21 kampene har nå primæridentitet og statistikk for alle 593 aktive FPL-spillere. Kravene er redusert fra 3 106 til 761 (75,5 %): 520 assists, 104 times tackled, 49 straffemål, 39 mållinjeklareringer, 37 storsjanseredninger, fem won tackles, fem net tackles og to CBI. Hele hendelsesinventaret er fortsatt borte. De tre øvrige kampenes ni manglende mål gir ytterligere 63 assistkrav. Gjenbruk primærsvarene; innhent bare ny, relevant hendelsesdekning. |
| 6 | Kvalitets- og regelgater før scoring | Kvalifiser felt-/sesonggrupper samlet. Behold uendrede historiske BPS-komponenter; verifiser endrede ledd, avrunding/klipping og offisielle revisjoner før omberegning. Bonus rangeres for samtlige deltakere i hele kvalifiserte kamper. Låste labels/modeller/benchmark beholdes; ingen modelltrening før samlet datakvalifisering. |

Kildepiloter med manglende dekning dokumenteres og stoppes. Manuell kontroll
reserveres for unntak. Ingen xG-imputering; de 38 storsjanseredningene forblir åpne.
Historisk FPL er fasit for regelkompatible felt, minutter og eksplisitte nuller.
Rådata, godkjente keeperverdier, offisielle hendelsesrettelser og frosne kontroller
bevares. Kjent kontrollfasit er regresjon, aldri et nytt uavhengig holdout.

## Oppdaterte assistavhengigheter

Tallene er betingede tak **hvis alle resterende bidrag i hele gruppen avklares**,
ikke prognoser. Berørte krav overlapper; de skal ikke summeres. Kandidatutelukkelser
kan gjøre nye spillerverdier komplette uten å avgjøre alle mål i kampen. Derfor
kan et gruppetak øke etter at en annen gruppe er redusert.

| Gruppe | Mål | Berørte krav | Betinget lukkbare krav | Nye komplette spillerkamper | Nye hele kamper |
|---|---:|---:|---:|---:|---:|
| source_not_assisted_marker | 774 | 6170 | 5069 | 4884 | 202 |
| paired_pass_with_intervening_events | 1028 | 3668 | 2823 | 2667 | 232 |
| assisted_goal_without_unique_pass_certificate | 391 | 3638 | 2690 | 2482 | 68 |
| no_positive_goal_assist_certificate | 363 | 2342 | 2005 | 1647 | 47 |
| penalty | 185 | 2449 | 1869 | 1714 | 33 |
| own_goal | 228 | 890 | 768 | 736 | 43 |
| direct_free_kick | 23 | 308 | 218 | 213 | 4 |

583 assistkrav ligger i inventar-/identitetsgap uten målgruppe. Prioriter positivt
årsaksbelegg når dette har lavere beviskostnad enn markørbaserte grupper.

`python priority/build.py` gjenskaper tallene fra gjeldende ledger og komplette
assistbidrag. `python followup_2026_10_08/bulk_batch2/reproduce.py` verifiserer den
nye batchen offline etter snapshot-bootstrap. 22 fokuserte tester og 33 identiske
replayresultater er dokumentert; full repositorietest og GitHub CI er ikke bekreftet.
