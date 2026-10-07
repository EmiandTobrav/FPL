# Restkontroll 7. oktober 2026: ingen nye eksakte avklaringer

**38 keeperobservasjoner i 22 kamper står fortsatt åpne.** Dekningen er
uendret: 5 343 / 5 381 (99,29 %). Ingen godkjente felt, poeng, bonus eller
modellresultater er endret i denne kontrollen.

## Hva som faktisk er undersøkt

- Alle 22 offisielle Premier League-hendelseslogger er hentet og lagret.
  De inneholder totalt **2 295 kommentarer**. Sidetall og antall oppføringer
  stemmer for samtlige kamper; ingen sider er utelatt.
- Hendelsene inneholder bare `id`, `playerIds`, `text`, `time` og `type`.
  Ingen av disse loggene gir et strukturert storsjansemerke eller
  kvalifikatorliste. En tekstbeskrivelse av skuddets posisjon brukes ikke som
  erstatning for Optas faktiske klassifisering.
- Den nyere offisielle SDP-kampstatistikken for Bournemouth–Aston Villa
  1. februar 2020 er kontrollert. Villas `bigChanceMissed` og Bournemouths
  `bigChanceSaves` er utelatt, ikke eksplisitt null.
- Fire nye GitHub-kandidater er kontrollert med fullstendige, ikke avkortede
  filtrær: `InigoG99/whoscored_dataset`, `Sportshero-sh/whoScoredDataImport`,
  `HalcyonVector/FootIQ` og `drinkdata/Scrape-Whoscored-Event-Data`.
  De gir henholdsvis spiller-/sesongsummer, data publisert før målperioden,
  Premier League-partisjoner fra 2023/24 eller ingen relevant råeksport.
  Konkrete filtrær, revisjoner og begrensninger står i `source_checks.json`.
- Pannadatas 11 publiserte releases er kontrollert for alternative eksporter.
  Ingen separat navngitt WhoScored-hendelseseksport ble funnet. Dette betyr
  ikke at alle publiserte filers innhold er revidert.

## Ramsdale: samme hull i flere framstillinger

Den offisielle tekstloggen inneholder tre Villa-avslutninger merket
`attempt saved`: Grealish ved 45+1, Davis ved 74 og Samatta ved 74. De
tilsvarer de tre tilgjengelige skudd-/redningsparene i råhendelsesarkivet.
Keeperens offisielle statistikktall er fire redninger. Tekstloggen gir
derfor heller ikke en komplett skuddpartner til den fjerde redningen.
Fravær i begge hendelsesframstillinger er ikke bevis for en ordinær sjanse.

## Konkret gjenværende databehov

`required_observations.csv` er en ferdig liste med alle 38 observasjoner,
sesong, dato, begge lag, hjemme/borte, FPL-kampkode, PL-kamp-ID og spiller-ID.
Den kan brukes direkte til å avgrense et nytt datatrekk:

1. **37 observasjoner i 21 kamper:** komplette skudd- og redningshendelser
   med eksplisitte storsjanse- og blokkeringsmerker, spiller/lag, periode,
   tidspunkt og kildeversjon. Et eksplisitt, verifiserbart keeper-/kamptall
   for storsjanseredninger er også tilstrekkelig.
2. **Ramsdale, kampkode 1059942 / PL-kamp 46845:** korrigert skudd-/redningsstrøm
   som forklarer alle fire redninger, eller et eksplisitt keeper-/kamptall.

Neste eksakte avklaring avhenger av nytt kvalifisert kildegrunnlag. Det er
ikke dokumentert at slike data ikke finnes, men kildene som er kontrollert
her kan ikke levere dem. Ingen abonnement, innlogging, kjøp eller henvendelse
til dataleverandører er gjort. Kostnad 0 kr.

## Reproduksjon

`../audit_remaining.py` gjenskaper oversikten fra de lagrede tekstloggene;
ved manglende cache henter den én kamp om gangen og stanser ved HTTP-feil.
`sources.json` har URL og SHA-256 for samtlige svar.
`commentary_audit.json` bevarer sidetallkontrollens resultater, hendelsestyper
og tilgjengelige feltnavn. `raw/` inneholder kildegrunnlaget.

Dette er en kildekontroll, ikke en ny godkjenningsregel. Hoveddatasettet og
de 25 tidligere transformasjonstestene er uendret.
