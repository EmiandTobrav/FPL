# Motstanders baklengsmål utelatt kun for spisser

Forsøket er fullført og separat verifisert. **Varianten består ikke alle uendrede krav.** MSE blant faste lagkandidater forbedres i begge perioder, men MSE for hele spillerutvalget forverres i 2026/27 GW1–6. Den fryste pakken beholdes uendret.

## Låst variant og datagrunnlag

Én regel ble registrert før beregning: For alle spillere med posisjon FWD brukes den lagrede prognosen fra modellen uten `ctx_opp_ga6` (motstanderens baklengsmål siste seks tilgjengelige kamper). For GK, DEF og MID brukes fullmodellens lagrede prognose uendret. Regelen gjelder alle forventede minuttverdier; ingen ekstra minutt- eller motstanderterskel er lagt til.

Posisjon hentes fra de opprinnelige prognosefilene, før resultater kobles på. Kalender og minuttprognoser er faste. De to poengmodellene ble tidligere trent og tidskontrollert under ablasjonsforsøket; her utføres null nye modellfit. Prognosekombinasjonen ble lagret og kontrollsummert før scoring.

Perioder: 2025/26 GW1–38 og tidligere undersøkt 2026/27 GW1–6. Ingen prospektive observasjoner eller GW7-prognoser er brukt. Datadekningen er identisk med tidligere forsøk: 29 574/3 849 prognoser, hvorav 29 144/3 353 kvalifiserte scorede rader og 2 070/330 faste lagkandidater. De øvrige 430/496 radene er ekskludert eller ukjente etter samme eksisterende regel; de er ikke nullfylt.

Suksess krever strengt lavere MSE mot fullpakken i hver periode, både totalt og blant lagkandidater, med uendrede minutter og Brier. Ingen toleranse eller undergruppe overstyrer hovedkravene. Dette er et utforskende oppfølgingsforsøk motivert av allerede observerte resultater i de samme periodene, ikke uavhengig validering.

## Hovedresultat

| Periode | Utvalg | Full MSE | Variant MSE | Relativ forbedring |
|---|---|---:|---:|---:|
| 2025/26 | Alle | 3,603974 | 3,603525 | +0,0125 % |
| 2025/26 | Faste lagkandidater | 12,935643 | 12,919674 | +0,1234 % |
| 2026/27 GW1–6 | Alle | 5,213553 | 5,215561 | −0,0385 % |
| 2026/27 GW1–6 | Faste lagkandidater | 13,049066 | 13,033693 | +0,1178 % |

Tre av fire MSE-krav bestås. Det feilede kravet er pilotens samlede spillerutvalg. Minutt- og Brier-kravene består gjennom identiske prognoser. Ingen oppgradering foretas.

Gevinstene er små. Når én runde utelates om gangen, er kandidatforbedringen historisk stabil (ΔMSE −0,022685 til −0,008023), mens pilotens kandidatresultat skifter fortegn (−0,044061 til +0,020131). Resultatet for alle spillere skifter også fortegn i begge perioder. Dette er følsomhetsintervaller, ikke konfidensintervaller. Seks pilotrunder, gjentatte spillere og flere foregående hypoteser begrenser sikkerheten.

RMSE, MAE, bias og likt vektet periodegjennomsnitt er lagret. MAE for pilotkandidatene forverres marginalt, fra 2,778662 til 2,779230, selv om MSE forbedres. Dette endrer ikke at MSE er hovedmålet.

## Hvor oppstår forskjellen?

Andre posisjoner er nøyaktig uendret. Tabellen viser variant minus fullmodell i MSE for spissene; negativt er bedre.

| Spissutvalg | N 2025/26 | ΔMSE | N pilot | ΔMSE |
|---|---:|---:|---:|---:|
| Alle spisser | 3 209 | −0,004076 | 372 | +0,018097 |
| Alle spisser, minst 60 forventede minutter | 548 | −0,033299 | 77 | −0,015474 |
| Alle spisser, under 60 forventede minutter | 2 661 | +0,001942 | 295 | +0,026859 |
| Spisser på kandidatlisten | 376 | −0,087911 | 60 | −0,084553 |
| Kandidatspisser, minst 60 forventede minutter | 339 | −0,087619 | 46 | −0,205499 |
| Kandidatspisser, under 60 forventede minutter | 37 | −0,090583 | 14 | +0,312841 |

Pilotens forverring kommer fra lavminuttgruppen. Blant spisser med minst 60 forventede minutter er retningen positiv i begge perioder, også i det bredere utvalget. Resultatet viser dermed at en regel for alle spisser er for bred på dette utviklingsgrunnlaget. Vi har ikke etterpå endret regelen eller scoret en ny kombinasjon med minuttgrense.

Dette er en annen endring enn det tidligere forsøket som halverte hele styrkekorreksjonen ved lav spilletid. Her bytter vi til en separat trent modell uten ett eksplisitt felt; resultatene kan ikke tolkes som effekten av samme mekanisme med motsatt vekt.

## Beslutning og videre arbeid

Registrer varianten som ikke bestått. Behold den fryste pakken og den prospektive GW7–38-testen uendret. Den positive effekten blant lagkandidater er et utviklingsfunn, ikke grunnlag for å endre det avtalte utvalget eller se bort fra det feilede totalmålet.

En eventuell neste hypotese kan avgrense feltutelatelsen til spisser med minst 60 forventede minutter, med fullpakken ellers. Den må registreres som et eget, resultatmotivert utviklingsforsøk før beregning; ingen slik variant er beregnet eller valgt her. Et eventuelt historisk pass vil fortsatt kreve en separat, framtidig evaluering før vi kan hevde generalisering. Nåværende prospektive periode skal fortsatt ikke brukes til å velge eller justere slike regler.

## Kontroll og filer

`protocol.json` låser regel, perioder, inputkontrollsummer og krav. `predictions_complete.json` forsegler prognosene før scoring. `complete.json` viser alle krav og samlet ikke-bestått. `verification.json` dokumenterer separat kontroll av 61 hovedmål/undergrupper, nøyaktig variantregel, kildeparitet, samme mål og utvalg, uendret kalender/minutter/sannsynligheter og Brier. Den fryste pakkens input og kodepakke er kontrollsummert uendret.

Resultater: `metrics.csv`, `groups.csv`, `per_round.csv`, `brier.csv`, `equal_period_mean_mse.csv` og `scores.csv.gz`. Ingen originalprognoser, kildefiler under `sources/`, målkontrakt eller aktive pakkepekere er endret.
