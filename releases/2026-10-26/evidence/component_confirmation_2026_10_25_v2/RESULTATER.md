# Komponentmodellen: ny test og hva som gjenstår før bruk

**Ny historisk kontroll: IKKE BESTÅTT.** Begge modellene er testet på hele 2025/26, med samme daterte spillerutvalg, priser, åpningsbudsjett og manager. Det separate forsøket uten chips bruker samme begrensning for begge.

| Test | Komponentmodell | Dagens modell | Forskjell, netto poeng | Status |
|---|---:|---:|---:|---|
| Samme adaptive manager med chips | 2147 | 2150 | -3 | Ikke bestått |
| Samme manager uten chips | 2125 | 2024 | +101 | Bestått |

Kravene ble låst før denne testens sesongresultater: begge modellene må fullføre begge oppsett, alle kontroller må bestås, og komponentmodellen må gi strengt flere netto poeng i både hovedtesten og testen uten chips. Ingen justering av modeller, innstillinger eller ressursgrenser etter resultatene.

4 komplette sesonger; 0 tekniske stopp. Alle 152 lagrede rundevalg og poengoppgjør er kontrollert mot regler, budsjett, kaptein, benk, chips og byttekostnader. Ufullførte forsøk har ingen konstruert sesongtotal.

## Hva resultatet betyr

Det forhåndsvalgte kravet for å gå videre til praktisk innkobling er ikke dokumentert. Dagens modell beholdes. Et manglende eller negativt resultat skal ikke skjules med et nytt oppsett eller en ny tilfeldig kjøring.

2025/26 er en ny sesong for denne konkrete managerpakken, men sesongen var tidligere undersøkt for prognosefeil og andre modeller. Dette er en tidsmessig utvidet historisk kontroll, ikke urørt bekreftelse. Testen bruker ett felles fryst regelsett, inkludert fem oppsparte gratisbytter. Historiske markedsdata, tidsstempler og registrert spillerutvalg har fortsatt dokumenterte proxyer.

## Kort vurdering av forskjellen

Tre poeng i hovedtesten er en svært liten observert forskjell. Det er ikke dokumentasjon på at komponentmodellen generelt er dårligere, men det oppfyller heller ikke det forhåndslåste kravet om flere netto poeng i hovedoppsettet. Testen uten chips peker i positiv retning. Begge resultater skal beholdes.

Komponentmodellen har lavere poeng-MSE enn referansen på de samme kjente fasitene etter åtterundersberegningen:

| Horisont | Komponentmodell MSE | Dagens modell MSE | Lavere feil |
|---|---:|---:|---:|
| 1 runder | 4.5923 | 4.8874 | 6.04 % |
| 3 runder | 18.4287 | 20.0190 | 7.94 % |
| 8 runder | 84.6894 | 90.3728 | 6.29 % |

Bedre prognosefeil ble dermed ikke en ny seier i managerens hovedoppsett. Chipstidspunkter, bytter, kaptein og lagutvikling ble forskjellige. Forskjellen mellom kjøring med og uten chips isolerer ikke effekten av én bestemt chip, siden resten av beslutningene også endres.

Historisk kalender er en viktig praktisk begrensning: kvalifiserte kampantall i den felles H8-beregningen var kjent for 32.7 % av spiller–rundene, med minst noe dekning ved 13 av 38 tidspunkter. Resten beholdes som ukjent. Den aktive referansens arkiverte kalender hadde 10 ferske, 24 foreldede og 4 manglende tidspunkter. Dette er en kontroll under rekonstruerte kilder, og gir ikke direkte svaret på resultatet med ferske førfristdata.

Før utskifting trenger vi derfor en sammenligning med fersk, datert kalender og komplette innganger, med prognoser lagret før utfall. Resepten bør holdes fast i den testen; resultatene fra 2025/26 skal ikke brukes til å velge nye chipstidspunkter i ettertid.

[Chipstidspunkter og hele rundens netto poeng](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/component_confirmation_2026_10_25_v2/chip_diagnostics.csv) · [Rundeoppgjør for begge oppsett](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/component_confirmation_2026_10_25_v2/round_diagnostics.csv) · [Prognosefeil](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/component_confirmation_2026_10_25_v2/forecast_diagnostics.csv) · [Kalenderdekning](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/component_confirmation_2026_10_25_v2/calendar_diagnostics.csv)

## Kontroller før komponentmodellen kan bli hovedmodell

1. **Modellpakken må kunne kjøres på ferske data.** Samme komponentberegning, minuttprognoser og åtte separate fremtidige rundeanslag som i forsøket må inngå i den operative kjøringen. Modell, featureliste og oppdateringsrytme må være versjonert, og eksport/innlesing må gjenskape forskningsprognosene.
2. **Én felles, fersk inngang ved faktisk tidspunkt.** Hele kjøpbare spillerutvalget, priser, posisjoner, klubber, full kvalifisert historikk, fravær, dødballroller, belastning og datert kampkalender må samles før fristen. Begge modeller skal få samme informasjon og den faktiske lagtilstanden. Faktisk fremtidig kampvær inngår ikke i denne komponentpakken.
3. **Praktisk kontroll av ditt lag.** Begge modellene kjøres fra samme eierskap, kjøpspriser, bank, gratisbytter og tilgjengelige chips. Forskjeller i bytter, kaptein, benk og prognoser skal vises, og valgene kontrolleres for lovlighet og budsjett.
4. **Lagring før utfallet.** Første nye prognoser og anbefalinger må få en tidsstemplet kvittering før runden starter. Deretter scores begge fortløpende på de samme utfallene. En etterberegnet prognose får aldri et tidligere tidsstempel.

Bestått historisk test åpner for denne driftskontrollen. Første kontroll på ferske innganger skal avdekke koblingsfeil; én fremtidig runde alene avgjør ikke langsiktig modellkvalitet. Dagens modell beholdes som sammenligningsgrunnlag også ved et senere bytte. Ingen FPL-overganger er utført og aktiv modell er ikke endret av dette forsøket.

## Hva som faktisk er testet

- Samme valgte komponentoppskrift og 325 tillatte grunnfelt som i hovedforsøket. Ti allerede låste, tidskontrollerte H1/H3-modellpakker for 2025/26 er gjenbrukt. Ingen ny arkitektur eller innstillingssøk.
- Åtte uavhengige fremtidshoder med samme residualmetode som før, oppdatert ved GW1, 9, 17, 25 og 33. Bare tidligere prognoseopprinnelser med komplett og tilgjengelig fasit inngår. 40 hoder totalt; 32 ferdige hoder ble bevart byte for byte etter en teknisk eksportretting.
- Referansen bruker den aktive faste sesongkalibreringen og dens opprinnelige treningsarkiv fra 2022/23–2024/25, med fire runders oppdateringsrytme. Underliggende lagrede baseprognoser er kontrollert mot kildehash, spillerutvalg og tidligere tilgjengelig statistikk. Den kjente historiske nullradsvakheten i den aktive referansen er bevart og dokumentert. Dette sammenligner operative pakker, ikke to nytrente arkitekturer med identisk treningsoppskrift.
- Begge starter med tom tropp, £100 millioner og samme regler. Åtte runders prognoser, tre runders planlegging, inntil 40 løserkall og 16 noder per kall; én tråd. Ingen mislykket sesong er kjørt om igjen med mer ressurser.
- 29 574 spiller–runde-rader fra daterte arkivutvalg. 409 manglende observasjonsrader er rekonstruert med tidligere informasjon. Ukjent fasit fylles ikke med null. Ved sesongslutt fylles bare ubrukte felt for runder etter GW38; ingen gyldig prognose er endret.

[Poeng og byttekostnader](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/component_confirmation_2026_10_25_v2/scores.csv) · [Etterkontroll av sesongene](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/component_confirmation_2026_10_25_v2/manager_verification.json) · [Kontroll av prognoser og modelltilpasninger](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/component_confirmation_2026_10_25_v2/forecast_verification.json) · [Låst testoppsett](/Users/emil/.codex/.chatgpt-projects/g-p-6ac36cd84d88819194c8f3d5ce43b378/reports/component_confirmation_2026_10_25_v2/proposal.json)
