# Forsiktig styrkekorreksjon ved lav forventet spilletid

Forsøket er fullført og verifisert. Den forhåndsbestemte kandidaten består ikke kravene. Vi beholder funnet som et negativt forskningsresultat; den fryste prognosepakken endres ikke.

## Fast forsøksdesign

Én kandidat, registrert i `protocol.json` før kjøring: Ved under 60 forventede minutter halveres forskjellen mellom full poengmodell og kalenderankeret. Ved minst 60 forventede minutter beholdes fullprognosen nøyaktig. Kalenderankeret bruker samme historiske egenskaper, varighet, sannsynlighet for minst 60 minutter og seks kalenderfelt, men utelater de fire feltene for lag-/motstanderstyrke. Formelen er kalender + 0,5 × (full − kalender) for lavminuttgruppen.

Grensen 60 og vekten 0,5 ble valgt på forhånd. Ingen parametersøk eller posisjonsspesifikk tilpasning. Dette er demping av forskjellen mellom to modeller, ikke en identifisert kausal eller rent additiv featureeffekt. Kalendergrunnlaget og minuttprognosene er faste; kalenderankerets nivå beholdes i blandingen.

Perioder: 2025/26 GW1–38 og allerede undersøkt pilot 2026/27 GW1–6. Ingen GW7–38-observasjoner eller prognoser er brukt. Begge periodene er utviklingsmateriale, ikke uavhengig bekreftelse. Hovedmål er MSE mot samme poengmål, samme kvalifiserte rader og samme faste lagkandidatliste. Kravet er strengt lavere MSE enn fullmodellen i begge perioder, både totalt og blant kandidater. Minutter og sannsynligheter skal være uendret, dermed også Brier.

## Hovedresultat

Lavere MSE er bedre. Endring er kandidat minus fullmodell.

| Periode | Utvalg | Rader | Full MSE | Dempet MSE | Endring | Relativ forbedring |
|---|---|---:|---:|---:|---:|---:|
| 2025/26 | Alle | 29 144 | 3,603974 | 3,602969 | −0,001004 | 0,0279 % |
| 2025/26 | Lagkandidater | 2 070 | 12,935643 | 12,931425 | −0,004218 | 0,0326 % |
| 2026/27 GW1–6 | Alle | 3 353 | 5,213553 | 5,211912 | −0,001641 | 0,0315 % |
| 2026/27 GW1–6 | Lagkandidater | 330 | 13,049066 | 13,059226 | +0,010161 | −0,0779 % |

Tre av fire MSE-krav bestås. Kandidatkravet i piloten feiler. Minutt- og Brier-kravene er oppfylt gjennom identiske prognoser. Ingen toleranse eller undergruppe brukes til å overstyre utfallet.

Blant lagkandidater under 60 forventede minutter faller MSE fra 7,986965 til 7,909706 i 2025/26 (113 rader), men øker fra 4,210685 til 4,285196 i piloten (45 rader). Den tidligere diagnosen viste at hele kampkontekstpakken skadet lavminuttgruppen i begge perioder sammenlignet med modellen uten kampkontekst. Dette forsøket viser at det ikke betyr at styrkedelen skader gruppen i begge perioder: I piloten har fullmodellen lavere MSE enn kalenderankeret alene (4,368497). Dempingen fjerner dermed noe nyttig korreksjon.

## Håndterer dette forskjellene per posisjon?

Ikke på en stabil måte. Tabellen gjelder hele den faste kandidatlisten per posisjon, inklusive spillere som ikke endres. Berørt er antallet med under 60 forventede minutter.

| Posisjon | 2025/26 berørt / totalt | Endring MSE | Pilot berørt / totalt | Endring MSE |
|---|---:|---:|---:|---:|
| Keeper | 0 / 187 | 0 | 1 / 30 | +0,000103 |
| Forsvar | 30 / 752 | −0,002972 | 13 / 120 | −0,001125 |
| Midtbane | 46 / 755 | −0,006006 | 17 / 120 | +0,021235 |
| Angrep | 37 / 376 | −0,005215 | 14 / 60 | +0,015611 |

Forsvar har en liten forbedring i begge perioder. Midtbane og angrep skifter fortegn. Keeperutvalget som endres er for lite til å tolkes. Bare 5,5 % av kandidatradene i 2025/26 og 13,6 % i piloten påvirkes, så dette er en smal mekanisme.

Spissproblemet finnes også ved minst 60 forventede minutter: Fullmodellens MSE overstiger kalenderankerets med 0,077756 i 2025/26 og 0,094162 i piloten. Disse prognosene endres ikke av forsøket. Etter demping har spissene samlet fortsatt høyere MSE enn kalenderankeret i begge perioder (14,570292 mot 14,497079 og 9,126957 mot 9,074512). En regel for lav spilletid kan derfor ikke alene forklare eller løse posisjonsforskjellene. Det er heller ikke grunnlag her for å konkludere med at egne modeller per posisjon vil vinne.

Alle forhåndsdefinerte posisjons-, eksponerings- og enkeltrundegrupper er lagret i `groups.csv`, også negative resultater.

## Stabilitet og begrensninger

Når én runde fjernes om gangen, ligger endringen blant kandidater mellom −0,004847 og −0,003283 i 2025/26. I piloten ligger den mellom +0,007327 og +0,012600: Forverringen skyldes ikke bare én enkelt av de seks rundene. For alle spillere i piloten skifter effekten derimot fortegn ved utelatelse av en runde. Dette er en følsomhetsanalyse, ikke konfidensintervaller eller signifikansbevis.

Gevinstene er svært små. Mange lavminuttspillere ligger utenfor kandidatlisten, og en totalforbedring kan derfor skjule dårligere prognoser for aktuelle valg. MAE blant alle pilotspillere forverres litt selv om MSE forbedres; MSE forblir avgjørende som avtalt. Utvalgene er gjentatte spillerobservasjoner, og de små posisjonsgruppene gir begrenset grunnlag for generalisering. Eksisterende tidsproxyer og datakvalitetsbegrensninger videreføres.

## Kontroll og videre arbeid

15 poengfit og null minuttfit: Kalenderankeret ble gjenskapt for tre historiske kontrollrunder og seks pilotrunder; fullmodellen ble gjenskapt for alle seks pilotrundene. Historiske ankerprognoser og pilotens fullprognoser samsvarer med arkivet innen 1e−12. Pilotens treningsnøkler og antall treningsrader samsvarer med opprinnelig kjøring. Treningsopprinnelser og tilgjengelighetstidspunkter for poeng- og minuttmål er før hver frist. Prognosene ble forseglet før scoring.

En separat kontroll (`verification.json`) bekrefter kandidatregelen, identiske minutt-/sannsynlighetsprognoser, kalenderanker, kvalifiserte rader, kandidatgrupper og beregnet MSE. Alle registrerte inputkontrollsummer er uendret, inkludert den fryste pakken. `complete.json` registrerer eksplisitt at forsøket feiler og at ingen modell er oppgradert.

Anbefalt neste arbeid er en separat diagnose av styrkekorreksjonen for spisser med minst 60 forventede minutter: Er retningen knyttet til eget lags angrep, motstanderens forsvar, hjemme/borte eller styrkegrunnlagets alder og dekning? Bruk bare informasjon tilgjengelig før fristen, behold de allerede undersøkte periodene som utviklingsmateriale, og registrer eventuelle nye modellkandidater før testing. Ikke velg en ny vekt ut fra dette forsøket. Den fryste pakken og den prospektive GW7–38-testen fortsetter uendret.
