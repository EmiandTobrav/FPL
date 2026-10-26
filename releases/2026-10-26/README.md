# Data, komponentmodell og fem runders planlegging – 26. oktober 2026

Denne oppdateringen samler det utvidede datasettet og forbedringene etter forrige GitHub-oppdatering. Den eksisterende demoen og eldre forsøk er bevart. Den operative løsningen er valgt og kontrollert i det lokale arbeidsarkivet; dette er ikke en påstand om at den fulle livekjøringen kan gjentas fra GitHub alene.

## Faktiske datasettfiler

| Leveranse | Innhold | Inngang |
|---|---|---|
| Samlet observasjonsmaster v5 | 190124 PL-observasjoner i åtte sesonger, vær/sol, utlån/historikk, kampbelastning, tilgjengelighet, dødballroller og rolle-/styrkefelt | [Master](../../datasets/fpl_master_enriched_v5/README.txt) |
| Observert vær | Kampvær og spillerradkoblinger; usikkerhet og kilder bevart | [Værdata](../../datasets/fpl_weather_all_seasons_v1/README.txt) |
| Felles modelltabeller | 135441 treningsrader og 111562 poolrader; korrigert kalender, 341 forskningsfelt og separat valgt liste med 325 | [Tabeller og skjema](../../datasets/fpl_component_common_20261026/README.md) |
| Fersk ekstern oppdatering | Klubb- og landslagskamper, bekreftede identiteter, kontrollerte minutter og eksplisitte hull | [Eksterne observasjoner](../../datasets/fpl_external_live_2026_10_26/README.md) |

[Ferske offisielle observasjoner gjennom GW8](../../datasets/fpl_live_observations_20261026/README.md) følger også med: 4866 kvalifiserte rader, offisiell spillerpool og380kampers kalender.

Den historiske masterens 2026/27-del slutter ved GW7. Den nye operative offisielle kildefangsten omfatter ferdige kamper gjennom GW8 og neste prognose i GW9; den publiseres som en separat liveutvidelse. Den historiske masteren er ikke ommerket som en komplett GW8-master.

## Sammenlignbar test av planlegging

Netto sesongpoeng etter byttekostnader. Samme korrigerte kalender og identiske prognoser i alle varianter.

| Planhorisont | 2023/24 | 2024/25 | 2025/26 |
|---|---:|---:|---:|
| Kontroll, 3 runder | 2465 | 2604 | 2322 |
| Valgt, 5 runder | 2569 | 2591 | 2359 |
| Forskjell | +104 | −13 | +37 |
| 8 runder | 2528 | Ikke fullført | 2322 |

Fem runder gir +42,7 poeng i snitt over alle tre sesonger og +12 over de siste to. Brukeren har valgt avveiningen selv om 2024/25 blir svakere. Åtte runder stoppet før GW6 i 2024/25 på den uendrede nodegrensen; delsesongen får ingen sesongscore eller aggregert snitt. Det er ikke et nullresultat.

Den detaljerte lag-/bytteplanen er utvidet til fem runder. De eksplisitte framtidige chipdatoene som prøves, er fortsatt de to nærmeste rundene. Dette er ikke et fullstendig søk over alle chipsekvenser gjennom fem eller åtte runder. Alle tre sesonger er tidligere undersøkte utviklingsdata, ikke urørte framtidsresultater.

[Full horisontrapport](evidence/manager_horizon_2026_10_26_v2/RESULTATER.txt) · [Aktiveringskontroller](evidence/component_plan5_activation_2026_10_26/RESULTATER.txt).

## Andre forbedringer og bevarte negative funn

- Felles tidsstyrt treningsgrunnlag med vær fra tidligere kamper, eksterne turneringer, dødballroller, tilgjengelighet og rolle-/styrkefelt. Mål og prediktorer holdes adskilt.
- Historikk etter dokumenterte avganger er rettet uten å slette gyldige tidligere kamper. Bekreftet utilgjengelige spillere sperres for kjøp, start, kaptein og vice; Bench Boost krever 15 tilgjengelige.
- Komponentmodellen er valgt med løpende kalibrering, 180 dagers halveringstid og Ridge 0,01. Grunnmodell og kalibrering oppdateres fortsatt hver fjerde runde. Like radvekter i grunnmodellen beholdes.
- xG/xA er kilde- og tidskvalifisert som forskningsfelt og testet alene og sammen med raskere kalibrering. Det er ikke med i den valgte modellen.
- Kalibreringsbrems, kandidatvekter og hyppigere grunnmodelltrening er undersøkt separat; negative og blandede resultater følger med og er ikke skjult bak den valgte varianten.
- Diagnosen av den svake 2025/26-sesongen er sporet til konkrete spillere og lagvalg. Kalenderkorrigeringen valgte 30 nyere opptak før fristen, reduserte medianalder fra 27,49 til 1,90 dager og rettet 233 undervurderte doble spiller-/rundeobservasjoner.

[Alle rapportkopier](evidence/) inneholder også tidligere forkastede varianter og tekniske stopp. Poeng fra ulike kalender- eller modellgrunnlag er ikke én rangering.

## Publiseringsomfang og kontroll

`implementation/` er en kildekopi fra arbeidsarkivet, ikke en erstatning for den gamle kjørbare demoen i repoets rot. Den inneholder senere pipeline- og managerimplementasjon, men noen importbaner og manifestevidens peker fortsatt til det større lokale arkivet. Full råbuffer, alle base-/kalibreringsmodeller, opprinnelige pickle-matriser og full historisk lærerpakke er ikke publisert. CSV-tabellene, masteren, kildekvitteringer og rapportene er faktisk inkludert.

Kjør `python releases/2026-10-26/verify_publication.py` fra repoets rot for filintegritet, nøkkel-/radkontroller og valgt feltskjema. Kontrollen gjentar ikke modelltrening eller sesongsimulering.

## Fersk modellkontroll

Den aktive lokale modellen er klar til å beregne nye forslag:669spillerprognoser,8prognoserunder og5runders planlegging.671offisielle svar og482eksterne kildekvitteringer er kontrollert.5352belastningssummer er kontrollert direkte mot spillertabellen. Ferskhet gjelder kontrolltidspunktet og må fornyes innen 2026-10-27 21:47:03.199335+00:00. [Kontrollstatus](READINESS.json) og [full rapport](evidence/component_freshness_2026_10_26/RESULTATER.txt). Et personlig bytteforslag krever i tillegg bekreftet nåværende tropp, bank, fribytter og chips; privat lagstatus er ikke bekreftet eller publisert. Ingen FPL-ordre er sendt.

Validering før publisering: begge CSV-eksportene er lest tilbake med eksakt samsvar for alle prediktorer, mål, nøkler og egnethetsmarkører. Den eksisterende Model Lab-suiten består52tester. En egen GitHub-kontroll verifiserer publiserte filer og radunivers ved push/PR.
