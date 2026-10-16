# Ablasjon av motstanderens scorede mål og baklengsmål

Forsøket er fullført og separat verifisert. **Ingen av de tre variantene består de uendrede MSE-kravene.** Motstanderens baklengsmål gir likevel et viktig posisjonsfunn: Å utelate feltet forbedrer spissene i begge perioder, men forverrer særlig midtbanespillerne historisk. Feltet bør derfor ikke fjernes generelt på dette grunnlaget.

Den fryste pakken er uendret. Ingen prospektive rader eller GW7-prognoser er brukt. Ingen variant er satt i produksjon eller valgt som erstatning for den fryste forskningspakken.

## Låst design

Tre varianter ble registrert før trening: uten motstanders baklengsmål (`ctx_opp_ga6`, hovedhypotese), uten motstanders scorede mål (`ctx_opp_gf6`), og uten begge. De to styrkefeltene for eget lag beholdes i alle varianter. Dette er utelatelse av de eksplisitte feltene; mulig overlappende informasjon i de øvrige historiske egenskapene beholdes også.

Hele poengmodellen trenes på nytt med identiske treningsnøkler, poengmål, tilgjengelighetskrav, parametre og seed. Kalenderfeltene, kalenderpolicyen, minuttprognosene og kategorisannsynlighetene er faste. Alle posisjoner omfattes; vi lager ingen etterpåvalgt kombinasjon av modeller.

Perioder: 2025/26 GW1–38 og tidligere undersøkt pilot 2026/27 GW1–6. Totalt 44 frister, 132 kandidatfit og 44 fit for gjenskaping av kontrollen: **176 poengfit og null minuttfit**. Kontrollprognosen samsvarer med arkivet ved hver frist innen avtalt toleranse 1e−12; treningsnøkler og antall treningsrader er identiske. Alle treningsopprinnelser og tilgjengelighetstidspunkter for mål er før den aktuelle fristen. Alle prognoser ble lagret og kontrollsummert før scoring.

Suksess krever strengt lavere MSE enn fullpakken i begge perioder, både på alle kvalifiserte rader og på den faste lagkandidatlisten. Ingen toleranse, periodegjennomsnitt eller undergruppe kan overstyre et feilet krav. Brier skal være uendret. MSE er hovedmål; RMSE, MAE og bias er også lagret.

## Hovedresultater

Lavere MSE er bedre. Positive prosenttall nedenfor betyr **forverring** mot fullpakken; negative betyr forbedring.

| Variant | 2025/26 alle MSE | Endring | Pilot alle MSE | Endring |
|---|---:|---:|---:|---:|
| Full kontroll | 3,603974 | — | 5,213553 | — |
| Uten motstanders baklengsmål | 3,610471 | +0,180 % | 5,209720 | −0,074 % |
| Uten motstanders scorede mål | 3,612656 | +0,241 % | 5,224761 | +0,215 % |
| Uten begge | 3,614869 | +0,302 % | 5,241285 | +0,532 % |

| Variant | 2025/26 kandidater MSE | Endring | Pilot kandidater MSE | Endring |
|---|---:|---:|---:|---:|
| Full kontroll | 12,935643 | — | 13,049066 | — |
| Uten motstanders baklengsmål | 12,978215 | +0,329 % | 12,972855 | −0,584 % |
| Uten motstanders scorede mål | 13,039471 | +0,803 % | 13,018691 | −0,233 % |
| Uten begge | 13,026015 | +0,699 % | 13,115442 | +0,509 % |

Alle tre forverrer begge historiske hovedutvalg. Uten baklengsmål består to av fire MSE-krav, uten scorede mål ett, uten begge ingen. Alle består kravet om identiske minutter og sannsynligheter. Utfallet er dermed negativt for alle tre generelle modellendringene.

Det likt vektede gjennomsnittet av de to periodenes kandidat-MSE forbedres litt uten baklengsmål (12,992354 → 12,975535), men dette kan ikke redde det feilede historiske kravet. Samme variants gjennomsnitt for alle spillere forverres. Periodene er dessuten en hel sesong og en seksrunders pilot, ikke to uavhengige hele sesonger. Begge er undersøkt tidligere.

## Hva lærte vi om spissene?

Endring i MSE mot fullpakken, for **faste lagkandidater med minst 60 forventede rundeminutter**:

| Variant | 2025/26: 339 spissrader | Pilot: 46 spissrader |
|---|---:|---:|
| Uten motstanders baklengsmål | −0,087619 | −0,205499 |
| Uten motstanders scorede mål | +0,162239 | −0,038459 |
| Uten begge | −0,048500 | +0,067469 |

Bare fjerning av baklengsmålsfeltet har positiv retning for denne gruppen i begge perioder. Historisk er forbedringen stabil når én runde fjernes (ΔMSE −0,128750 til −0,038948), men i piloten skifter den samlede spisseffekten fortegn (−0,356241 til +0,071657).

I den forhåndsdefinerte problemgruppen der motstanderen har sluppet inn minst to mål per kamp i de siste seks kampene, er effekten tydeligere:

| Variant | 2025/26: 59 spissrader | Pilot: 11 spissrader |
|---|---:|---:|
| Uten motstanders baklengsmål | −0,256603 | −1,188676 |
| Uten motstanders scorede mål | −0,007096 | −1,218772 |
| Uten begge | −0,500228 | −0,037239 |

Uten baklengsmål er forbedringen i denne gruppen negativ i MSE-endring uansett hvilken runde som fjernes: −0,347462 til −0,159916 historisk og −1,511714 til −0,473023 i piloten. Dette styrker den tidligere mekanismehypotesen, men 11 pilotobservasjoner er svært lite og gruppen kommer fra en allerede undersøkt diagnose.

Fjerning av scorede mål hjelper også denne lille pilotgruppen, men ikke spissene historisk samlet. Og fjerning av begge gir ikke summen av de separate gevinstene. Modellen endrer bruk av de øvrige egenskapene ved retrening; dette er ikke uavhengige, additive effekter. Ablasjonen identifiserer konsekvensen av å utelate et felt fra denne treningsoppskriften, ikke en generell kausal effekt av motstanderens målstatistikk.

## Posisjonsforskjellene forklarer hvorfor hovedkravet feiler

Her vises hele kandidatlisten per posisjon, uansett forventede minutter, for varianten **uten motstanders baklengsmål**:

| Posisjon | N 2025/26 | ΔMSE | N pilot | ΔMSE |
|---|---:|---:|---:|---:|
| Keeper | 187 | +0,040554 | 30 | −0,106531 |
| Forsvar | 752 | +0,030522 | 120 | −0,030366 |
| Midtbane | 755 | +0,120058 | 120 | −0,110304 |
| Angrep | 376 | −0,087911 | 60 | −0,084553 |

Historisk blir spissene bedre, mens de tre andre posisjonene blir dårligere. Midtbanegruppen har det største negative bidraget til samlet kandidat-MSE. I piloten forbedres alle fire grupper, men hver posisjonsgruppes effekt skifter fortegn når en runde fjernes. Vi har dermed støtte for å undersøke ulik behandling per posisjon, ikke dokumentasjon for en universell forbedring.

Alle posisjoner, minuttgrupper og forhåndsdefinerte situasjoner er rapportert i `groups.csv`, også de som ikke støtter hypotesen. Ingen posisjon ble brukt til å velge en ny kandidat i denne kjøringen.

## Datadekning, Brier og usikkerhet

| Periode | Prognoser | Kvalifiserte scorede rader | Ekskludert/ukjent etter eksisterende regel | Faste lagkandidater |
|---|---:|---:|---:|---:|
| 2025/26 | 29 574 | 29 144 | 430 | 2 070 |
| 2026/27 GW1–6 | 3 849 | 3 353 | 496 | 330 |

Samme spiller–frist-nøkler, mål og kandidatlister brukes for alle varianter. De ekskluderte radene fylles ikke med null. Det opprettes ikke nye tidsantakelser: eksisterende kilde- og tilgjengelighetsproxyer videreføres. Delte kontekst-/featurefiler filtreres til GW1–6 før pilotberegninger; ingen prospektive prognosefiler leses.

Brier er identisk i alle spor. For lagkandidatene er spilldeltakelse/minst én kamp med 60 minutter henholdsvis 0,038918/0,097455 historisk og 0,055083/0,093032 i piloten. Sannsynlighetene er kontrollert mot de lagrede originalene. Her estimeres ingen ny poengfordeling eller sannsynlighet for 10+ poeng.

Alle tre varianters historiske forverring på begge hovedutvalg består når én runde fjernes. Pilotgevinsten uten baklengsmål er derimot rundtursfølsom: blant kandidater ligger ΔMSE mellom −0,134760 og +0,009233. Dette er beskrivende følsomhetsintervaller, ikke konfidensintervaller. Flere varianter og mange undergrupper er undersøkt; ingen signifikans- eller uavhengig bekreftelsespåstand gjøres.

## Beslutning og neste hypotese

Behold fullpakken uendret og registrer alle tre ablasjoner som ikke bestått. Ikke fjern motstanderstyrke generelt, og ikke bruk det gunstige gjennomsnittet eller spissgruppen til å overstyre de låste kravene.

Det mest avgrensede neste forsøket er en separat, forhåndsregistrert posisjonsregel: bruk prognosen uten motstanders baklengsmål for FWD og fullprognosen for de øvrige posisjonene. Dette er foreløpig bare en hypotese; **ingen slik kombinasjon er beregnet, scoret eller valgt her**. Den må vurderes mot samme hovedkrav og synlige posisjonskontroller, uten å tune terskler etter disse resultatene. Nåværende prospektive GW7–38-test fortsetter med den opprinnelig fryste pakken.

## Etterprøvbarhet

`protocol.json` låser inputkontrollsummer, varianter, perioder, krav og ressursbudsjett. Hver av de 44 fristene har egen prognosefil og kvittering med treningsnøkler, tidskontroll og kontrollparitet. `predictions_complete.json` forsegler alle prognoser før scoring. `complete.json` viser at alle tre varianter feiler.

`verification.json` dokumenterer separat kontroll av de 44 fristene, hovedmål, undergrupper, Brier, identiske prognose-/målpopulasjoner og uendret fryst pakke. `metrics.csv`, `secondary_metrics.csv`, `equal_period_mean_mse.csv`, `groups.csv`, `brier.csv` og `coverage.csv` inneholder tallgrunnlaget. Ingen gamle resultater eller filer under `sources/` er endret.
