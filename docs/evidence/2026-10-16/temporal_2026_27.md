# Fryst prognosepakke – 2026/27 GW1–7

Modellgrunnlaget er ferdigstilt, GW1–6 er evaluert, og kontroll (`base`) og kandidat (`full`) for GW7 er lagret før fristen. Prognosepakken er fortsatt `forecast-package-20261016-v1`; modellvalg, parametere, MSE som hovedmål og suksesskrav er uendret. Ingen produksjonspromotering eller endring av lagoptimaliseringen.

## GW1–6: retrospektiv kontroll

| Utvalg | Spiller–runder | MSE kontroll | MSE kandidat | Reduksjon i MSE |
|---|---:|---:|---:|---:|
| Alle kvalifiserte | 3353 | 5.227766 | 5.213553 | 0.27 % |
| Faste lagkandidater | 330 | 13.058070 | 13.049066 | 0.07 % |

Dekning: 3353 kjente av 3353 kvalifiserte observasjoner; 0 ukjente. Begge spor bruker nøyaktig samme spillere, minuttprognoser og kategorisannsynligheter. Lagkandidatene er valgt før resultatvurderingen med den fryste referansemodellen: 5 keepere, 20 forsvarere, 20 midtbanespillere og 10 spisser per runde, sortert på referanseprognosen med spillerkode som likhetsregel.

Pilotens krav: {"all": true, "identical_minute_probability_inputs": true, "team_candidates": true}. Dette er en kort, retrospektiv kontroll – GW1–5 var tidligere inspisert, og alle seks runder var ferdigspilt ved frysingen. Resultatet erstatter ikke den forhåndsdefinerte prospektive testen GW7–38 og utløser ingen justering av modellen. Intervaller i `intervals.csv` er kun beskrivende; seks runder gir svakt grunnlag for sesongkonklusjoner.

Minuttprognosene, som er felles for begge poengspor: MSE 593.822, MAE 16.433 minutter, Brier(spill) 0.113635, Brier(minst én kamp ≥60 minutter) 0.105989. Likheten mellom sporene bevarer Brier-kravet; dette er ikke et nytt forsøk på å slå en annen minuttmodell.

## GW7 lagret før fristen

- Begge prognosespor: **16.10.2026 kl. 17:49:50 norsk tid**.
- Frist: **17.10.2026 kl. 12:00 norsk tid**.
- 667 spillere. Råprognoser i `gw07_predictions.csv.gz`; lesbar eksport i `GW7_prognoser.csv`.
- SHA256 for originalfilen: `8c6150c9f7b02bd45b208e6e5ce55335c0dd7e5e9a8b49a09d20d8b9383f14ba`.
- Minuttverdier er rekonstruert fra de fryste 2024/25 GW37-hodene. Kategorisannsynligheter er oppdatert ved GW1 og GW5; begge poengmodeller er trent etter samme per-runde-oppskrift.
- Kilder til GW7 er de faktisk mottatte offisielle øyeblikksbildene fra 16. oktober. Opplysningene er dermed ikke et siste-minutt-bilde av fristen. Informasjonsgrensen er eksplisitt lagret; ingen framtidige resultater er brukt.

## Datagrunnlag og verifikasjon

4516 prognoserader over sju runder. Alle 667 spillerhistorikker fra det offisielle API-et er hentet med kontrollsum og mottakstid. GW6 tilfører 315 spilte spiller–kamp-rader. Offisielle resultater samsvarer med alle 3216 eksisterende spiller–runde-rader i GW1–5. Null minutter er bekreftet mot offisielle data; manglende resultat er aldri erstattet med null.

Historiske resultater beholder prosjektets tidsproxy: kampstatistikk etter 24 timer, minuttetiketter etter sju dager. Rundeavslutning og de eksisterende etikettidene for GW1–5 er bevart. Status/sjanse/nyheter er bundet til det daterte øyeblikksbildet og korrekt frist. Historiske Git-tider og senere hentede historiske kampresultater er fortsatt proxyer, ikke dokumentasjon på nøyaktig hva en bruker faktisk mottok på det historiske tidspunktet.

Den nye sesongen bruker den dokumenterte spillerlisten før hver frist og samme historiske egenskapsdefinisjoner. Dette er en datatilpasning fra tidligere sesongers eldre spillerlister; utvalgets dekning må derfor tolkes med dette forbeholdet. Nye spillere beholder den eksisterende håndteringen av manglende historikk.

Kontroller:

- Begge poengspor gjenskapt for alle 38 runder i 2025/26: 76 tilpasninger, avvik bare på avrundingsnivå.
- Egenskapsberegningen gjenskapt på tre historiske opphav (GW1, 20 og 38), alle 97 egenskaper.
- Fryste betingede minuttverdier gjenskapt med identiske treningsnøkler og numerisk samsvar.
- Tidsgrenser, unike spillernøkler, kildesjekksummer, gyldige sannsynligheter og forventede minutter kontrollert.
- GW7 lagret og referanselisten ferdigstilt før fristen, før vurdering av GW1–6-resultatene.

Under datatilpasningen ble en tidsformatfeil oppdaget: sekundpresisjon i forespørslene mot nanosekundpresisjon i historikken ga tom historikk. Tidsstemplene ble normalisert før modellene for den nye sesongen ble trent. Den uendrede beregningskoden bestod deretter historisk samsvarstest. Diagnose og tidligere byggelogger er bevart i `pre_fit_timestamp_diagnosis/`.

## Neste steg

Bevar GW7-filen uendret. Når GW7-resultatene er tilgjengelige og kvalifisert, knytt dem til den lagrede prognosen. Fortsett å lagre begge spor før hver frist for GW8–38, med samme forhåndsdefinerte oppdateringsrytme og krav. Registrer eventuelle manglende frister; ingen etterdatering. Den prospektive blokken vurderes samlet, uten resultatstyrt stopp eller justering underveis. Ingen automatisk innsamling eller kjøreplan er satt opp.
