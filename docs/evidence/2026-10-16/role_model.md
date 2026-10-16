# Rollemodell for start, innhopp og fravær

**Forsøket er fullført og verifisert. Rollemodellen består ikke de uendrede MSE-/Brier-kravene.** Minutt-MSE forverres i begge perioder, både for hele spillerutvalget og den faste kandidatlisten. Ingen endring gjøres i den fryste prognosepakken, og ingen prospektive observasjoner er brukt.

## Låst forsøk

Kandidaten predikerer tre roller: ingen minutter, innhopp og start. For hver spillende rolle predikeres også sannsynlighet for minst 60 minutter og betinget varighet. Forventede minutter beregnes slik:

`P(innhopp) × E[minutter | innhopp] + P(start) × E[minutter | start]`.

Varigheten innen hver rolle er selv en blanding av kort og lang deltakelse. Det gir fire varighetsmodeller: kort/langt innhopp og kort/lang start. Korte forventninger avgrenses til 1–59 minutter, lange til 60–90. Sannsynligheten for minst 60 minutter beregnes fra samme rolleblanding, ikke ved å sette den lik startsannsynligheten. Dette sikrer sammenheng mellom forventet spilletid og sannsynlighetene.

Modellen bruker eksisterende numeriske historikkfelt, posisjonsindikatorer og den eksisterende tilgjengelighetspakken. Ingen nye treningsmeldinger, konkurrentdata, terskelsøk eller parameterjusteringer er innført. HGB-parametre er uendret: 100 iterasjoner, maksimalt 15 bladnoder, minst 60 observasjoner per blad, L2=20, seed=173 og én tråd.

Varighetsmodellene er trent én gang med frist 2024/25 GW37 og deretter faste. Rollesannsynligheter og betingede 60-minuttersmodeller oppdateres ved GW1,5,…37 historisk og GW1,5 i piloten. Dette beholder oppdateringsrytmen og tidspunktet for frosne varighetsmodeller. Alle tre rolleutfall og varighetsmodeller trenes på kvalifiserte enkeltrunder på tvers av posisjoner, slik at spissene får støtte fra en større treningspopulasjon.

Kandidaten brukes bare når før-frist-informasjonen viser FWD, minst fem historiske runder, noe nylig spilletid, usikker rolle etter den tidligere låste definisjonen, og én kjent planlagt kamp. Ingen terskel på forventede minutter brukes. Andre spillere og kampsituasjoner beholder den fryste modellens prognoser nøyaktig.

En ekstra diagnostisk kontroll beholder tre vanlige minuttkategorier, men bruker kandidatens identiske treningsutvalg, egenskaper og oppdateringsrytme. Den har to faste varighetsmodeller. Dette skiller rolleoppdeling fra felles endringer i modellgrunnlaget. Mot den fryste modellen er forsøket en samlet ombygging: varighetsmodellene bruker også eksisterende tilgjengelighetsfelt, og treningsutvalget er avgrenset til kvalifiserte enkeltrunder. Vi hevder derfor ikke at alle forskjeller mot fryst modell skyldes rolleoppdelingen alene.

## Tidskvalifisering og etiketter

Historiske native starter er kontrollert mot startkvalitetsflagg og summer av registrerte kampminutter/-starter. Nullutfall krever null minutter og null native starter. Spilte utfall krever én spilt kamp, samsvar mellom kamp- og rundedata og kvalifisert startetikett. Starter er ikke utledet av en 60-minuttersgrense.

De eldste sesongene har startetiketter, men mangler kjent kalendergrunnlag for dette enkeltkampforsøket. Rolle- og ekstrakontrollen får derfor kvalifisert trening fra 2022/23 og videre. To rader i 2024/25 der den planlagte enkeltkampen faktisk ga to spilte kamper holdes også utenfor disse treningssettene. Dette er dokumenterte treningsavgrensninger; evalueringspopulasjonen endres ikke. 2024/25 GW15 forblir utelukket som før.

Før hvert fit må både historisk prognoseopprinnelse, poengmålets tilgjengelighet og minuttmålets konservative tilgjengelighet være strengt før fristen. Tilgjengelighetssnapshotene er kontrollert før sine respektive frister. Eksisterende historiske kilde- og tidsproxyer videreføres; dette er ikke en ny streng mottakslogg.

Den opprinnelige kategoriklassifikatoren er gjenskapt ved alle 12 oppdateringene med identiske opprinnelige treningsnøkler. Dens sannsynligheter samsvarer med arkivet for alle 44 prognosefrister. Prognoser er lagret før scoring.

## Hovedresultat: forventede minutter

MSE er her **minutter²**, ikke poeng². Lavere er bedre.

| Periode | Utvalg | Fryst MSE | Rollemodell MSE | Forverring |
|---|---|---:|---:|---:|
| 2025/26 | Alle, N=29 144 | 440,957736 | 441,304719 | 0,079 % |
| 2025/26 | Faste kandidater, N=2 070 | 591,322732 | 592,208667 | 0,150 % |
| 2026/27 GW1–6 | Alle, N=3 353 | 593,821989 | 594,762590 | 0,158 % |
| 2026/27 GW1–6 | Faste kandidater, N=330 | 510,567849 | 513,092734 | 0,495 % |

Alle fire MSE-krav feiler. Den gjennomsnittlige endringen er liten på hele utvalget fordi bare 1 339 historiske og 203 pilotrader endres. På kandidatlisten endres 116 og 23 rader.

Blant de usikre spissene som faktisk får rollemodellen, øker MSE fra 642,627 til 650,179 historisk og fra 702,795 til 718,331 i piloten. Blant de berørte lagkandidatene øker den fra 767,360 til 783,170 og fra 704,089 til 740,316. Negativt funn skjules altså ikke bare av et stort uendret spillerutvalg.

Historisk består forverringen på begge hovedutvalg når én runde fjernes. I piloten skifter fortegnet ved utelatelse av en runde. Dette er følsomhetsanalyse, ikke konfidensintervaller. MSE forblir hovedmålet selv om MAE for pilotkandidatene faller litt.

## Brier: sannsynlighetene består heller ikke samlet

| Periode og utvalg | Spill, fryst → rolle | Minst én kamp ≥60, fryst → rolle |
|---|---:|---:|
| 2025/26 alle | 0,068650 → 0,068695 | 0,075048 → 0,075056 |
| 2025/26 kandidater | 0,038918 → 0,038917 | 0,097455 → 0,097389 |
| Pilot alle | 0,113635 → 0,113719 | 0,105989 → 0,106132 |
| Pilot kandidater | 0,055083 → 0,055381 | 0,093032 → 0,093539 |

Bare de to historiske kandidat-Brier-kravene består. Totalt består 2 av 12 låste MSE-/Brier-krav. De små forbedringene kan ikke overstyre MSE-feilene eller de øvrige Brier-forverringene. Ingen toleranse er innført etter resultatene.

## Hva forteller ekstrakontrollen?

Den diagnostiske modellen med vanlige minuttkategorier og samme nye treningsgrunnlag feiler også alle fire MSE-sammenligninger mot fryst modell. Dens MSE er 441,151934/593,534652 historisk for alle/kandidater, og 594,329039/512,856637 i piloten.

Rollemodellen er svakere enn denne kontrollen på hele utvalget i begge perioder. Den er bedre blant historiske kandidater, men svakere blant pilotkandidatene. Det er dermed ikke stabil støtte for at eksplisitt rolleoppdeling i seg selv er bedre med denne oppskriften og eksisterende egenskaper. Samtidig viser den negative ekstrakontrollen at endret treningsstøtte og varighetsmodellgrunnlag også kan bidra til forskjellen mot den fryste modellen.

## Hvor modellen bommer

Historisk ligger gjennomsnittlige rolleandeler nær de observerte: 34,4 % forventede starter mot 33,9 % faktiske, 34,2 % innhopp mot 34,8 %, og 31,4 % fravær mot 31,3 %. Det forhindrer ikke dårligere feil på enkeltprognoser.

I pilotens 23 berørte lagkandidatrader forventer modellen **71,0 % starter**, mens **60,9 %** faktisk starter. Den forventer **14,8 % uten minutter**, mot **21,7 %** faktisk. Blant de fire som kommer inn, forventer den i snitt 21,5 minutter betinget på innhopp, mot 14,8 faktisk. Blant de 14 som starter, forventer den 83,8 minutter betinget på start, mot 87,7 faktisk.

Dette er små, etterpå observerte grupper, men de viser hvorfor «start/innhopp» som tydeligere modellstruktur ikke automatisk gjør forventningsverdien bedre. Modellen må fortsatt skille hvem som faktisk får rollen. Det er ikke dokumentert at en enkel justering av alle start- eller innhoppsverdier vil hjelpe.

Start- og innhopps-Brier er lagret i `role_diagnostics.csv`. Den gamle modellen har ingen eksplisitt start-/innhoppssannsynlighet, så det konstrueres ingen falsk sammenligning ved å kalle P(≥60) for P(start).

## Beslutning og neste prioritet

Behold den fryste modellen og registrer denne rollemodellen som ikke bestått. Ingen ny poengmodell er trent, og effekten på poeng eller lagvalg er ikke testet.

Neste avgrensede spørsmål bør være informasjonsverdien av eksplisitt rollehistorikk: nylige overganger mellom start/innhopp og historisk varighet gitt rolle, med tellinger for å håndtere få observasjoner. Test dette som et eget egenskapstillegg mot en fast modell, slik at informasjon og arkitektur ikke endres samtidig. Eventuelle konkurranse- eller treningsmeldinger må fortsatt tidskvalifiseres før bruk. Forsøket her beviser ikke at mer informasjon vil løse problemet, men gir ikke grunnlag for videreføring av denne arkitekturen alene.

Ingen ny hypotese er trent eller scoret etter dette resultatet. Periodene er allerede undersøkt, og et eventuelt senere utviklingspass vil fortsatt kreve separat uavhengig bekreftelse. Den eksisterende prospektive GW7–38-testen fortsetter med opprinnelig fryst pakke.

## Teknisk spor og verifikasjon

Forsøket har 66 unike modelltilpasninger: fire rollevarighetsmodeller, to varighetsmodeller for ekstrakontrollen, 36 rolle-/betingede sannsynlighetsmodeller, 12 kategorimodeller for ekstrakontrollen og 12 gjenskapinger av fryst kategorikontroll. Alle fire varighetsgruppene hadde minst 60 treningsobservasjoner; den forhåndsregistrerte konstantreserven ble ikke brukt. Den sjeldneste gruppen, langt innhopp, hadde 103 rader.

Første kjøring stoppet ved GW31 fordi prognosepoolen inneholdt spillere som manglet i treningstabellen. Ingen resultater var scoret. Koblingen ble rettet til de originale lagrede frist-egenskapene uten å endre trening, regel, parametre eller krav. GW1–28 ble gjenbrukt; GW29–30 ble gjenskapt og kontrollert mot de allerede forseglede prognosene. Gjentakelsen ga 11 ekstra tilpasninger, altså 77 fysisk utførte tilpasninger totalt. Feilkjøring, årsak, nytt protokollspor og prognoser er bevart separat. Dette var en teknisk fortsettelse, ikke resultatstyrt tuning.

`verification.json` bekrefter alle 44 fristkontroller, kildeparitet, uendrede prognoser utenfor målgruppen, korrekt blanding, uavhengig kontroll av grupperingen og 32 metrikkrader. `gate_verification.json` gjentar alle 12 hovedkrav. Hele den fryste pakkens kilde- og kodekontrollsummer er kontrollert uendret. Ingen filer under `sources/` er endret.

Se `protocol.json`, `label_coverage.csv`, `exclusion_reasons.csv`, `means_lock.json`, de daterte fit-/prognosekvitteringene, `metrics.csv`, `role_vs_matched.csv`, `role_diagnostics.csv`, `equal_period_mse.csv` og `complete.json` for etterprøvbare detaljer.
