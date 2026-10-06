> **Fullført 6. oktober 2026:** Kamp-/horisont-/chipforsøket er kjørt. 84 forløp, 2856 beslutninger. Beste observerte primærscore er 2351,50 for full H3 + adaptiv TC, men bare +7,75 mot kalenderkontrollen. Benchmarken beholdes. [Rapport](../research/current/fixture_strategy/README.md). Neste: kalender/frister og solverstabilitet, deretter tidligere-sesong-kalibrert chip-spareverdi. Planen nedenfor bevares som historisk protokoll.

# Neste forsøk: kampvise prognoser og chipstrategi

Oppdatert 6. oktober 2026 etter brukerens prioritering. **Planlagt, ikke implementert eller kjørt.** Aktiv benchmark er fortsatt `constant_h3`; `calendar_count_h3` er kontroll for kalenderens tilleggsverdi.

## Presisering av regelgrunnlaget

Simulatoren anvender et nyere lag-/bytte-/chipoppsett på alle fire historiske sesonger: opptil fem frie bytter, bevaring av frie bytter ved Wildcard/Free Hit og to sett chips. Oppgjøret bruker historiske spillerpoeng, ikke en full omberegning av årets poengregler. Historiske prosentplasseringer er derfor bare poengekvivalenter. Ingen ny kontroll mot offisielle 2026/27-regler er gjennomført i denne planoppdateringen.

## Forsøk A: hver kommende kamp får egen prognose

1. Revider dekningen av før-frist-kalendere, særlig 2025/26. Rapportér dekning per planleggingshorisont. Ikke bruk sluttkalenderen til å fylle historiske hull; behold eksplisitt fallback. Endres kalendergrunnlaget, kjør antall-kamper-kontrollen på samme grunnlag.
2. Bygg separat motstanderangrep og motstanderforsvar fra kamper avsluttet før beslutningstidspunktet. Test hjemme/borte separat og samlet med motstanderstyrke. Lær effektene på tidligere data; trekk usikre estimater mot ligagjennomsnittet.
3. Beregn prognose per planlagt kamp med spillerens tilstand ved beslutningen, ikke fremtidig observert form, minutter eller lagstyrke. Summér kamper i hver runde; kjent blank gir null. Unngå å legge kampeffekt oppå en prognose som allerede inneholder samme effekt.
4. Første isolerte test endrer bare fremtidsprognoser ved H3; aktuell prognose og fast chipkalender beholdes. Sammenlign antall alene, antall + hjemme/borte, antall + motstander, og alle tre. En senere test kan erstatte også aktuell prognose på samme kampvise grunnlag.
5. Når H3-resultatet er analysert, test forhåndsvalgte H5 og H8 med matchet antall-kamper-kontroll ved hver horisont. Ikke velg horisont ved å maksimere resultatet i hver evalueringssesong.

Motstanderforsvar skal kunne påvirke offensive bidrag, mens motstanderangrep skal kunne påvirke clean sheet og baklengs. Minutt-/rotasjonsjustering ved tett kampprogram er et eget etterfølgende forsøk; dobbelt antall kamper er ikke automatisk dobbelt antall minutter.

## Forsøk B: adaptiv bruk av hver chip

Lås prognosegrunnlaget før chipforsøket. Test én adaptiv chiptype om gangen mot samme faste kalender for de øvrige, deretter kombinasjonen. Reserverte runder kan ikke gi to chips samtidig. Modellér beholdning, utløp og lovlige kombinasjoner eksplisitt.

| Chip | Beslutningsgrunnlag |
|---|---|
| Triple Captain | Forventet ekstra kapteinspoeng nå mot verdien av å spare chipen til senere kjente muligheter; inkluder minuttusikkerhet. |
| Bench Boost | Forventet netto merverdi av tellende benk, med ordinære autosubs i alternativet og kostnad ved å bygge/avvikle benken. |
| Free Hit | Forventet forbedring over beste ordinære plan, inkludert bytter og hits, og at opprinnelig tropp returnerer. |
| Wildcard | Flerunders gevinst ved varig troppsendring relativt til ordinær bytteplan, med bank, frie bytter og senere chipmuligheter. |

Start med Triple Captain, så Bench Boost, Free Hit og Wildcard. Bruk rullerende beslutninger og eksplisitt verdi av gjenværende chips utover kort planleggingshorisont. Ingen dato velges etter realiserte sesongpoeng. Kalibrér spareverdi/terskler bare på tidligere sesonger. Felles strategi må testes fordi individuelt gode chipvalg kan konkurrere om samme runde eller ressurser.

## Evaluering

Rapportér netto sesongpoeng mot aktiv benchmark og matchet kontroll på 2022/23–2025/26, med alle sesongresultater, hits, bytter, kapteinspoeng, kalenderdekning og solvergap. Kampforsøket kjøres både med fast chipkalender og uten chips. Chipforsøket måler hele sesongforløpet, ikke bare poengene i chiprunden. Behold samme overlevering, priser og ressurser. De fire sesongene er allerede brukt til modellvalg; resultater er utforskende og må følges av låst prospektiv evaluering.

---

## Tidligere forsøkslogg

> **Nyeste oppdatering 6. oktober 2026:** Første kalendertest er fullført: +35,5 med chips / +45,5 uten chips mot `constant_h3`, men ujevn gevinst og svak 2025/26-dekning. Benchmarken beholdes. [Resultater](../research/current/calendar_counts/README.md). Neste: bedre dekning og separat motstander-/hjemme-borte-test. Eldre oppdateringer og protokoll følger nedenfor.

> **Seneste oppdatering 6. oktober 2026:** Etter brukerens valg av `constant_h3` som benchmark er posisjonsspesialisering nå testet og fullført. Ingen kandidat slår den på primærmålet. [Posisjonsrapport](../research/current/position_specialist/README.md). Neste prioritet er tidsriktig kalender/tilgjengelighet og prospektiv evaluering. Dokumentet nedenfor er den historiske protokollen og beslutningen ved avslutningen av kombinasjonsforsøket; benchmarkvalget kom etterpå.

# Kombinasjonsforsøket: global HGB-vekt med tre-rundersplanlegging

Status 6. oktober 2026: **fullført**. [Resultatrapport](../research/current/global_horizon/README.md): +70,0/+23,75 mot referansen med/uten chips, men bare +15,75/−16,75 mot globalvekt med H1. Primær tilleggsgevinst kommer fra én av fire sesonger. De aktive utfordrerne beholdes; kombinasjonen registreres som forskning. Resten av dokumentet bevarer testopplegget som ble avtalt før kjøring. Brukeren har bekreftet at oppdatert Ridge/Extra med H3 og global, tidsordnet lært HGB-vekt skal videreføres som utfordrere. [Kandidatregister](../research/current/challengers.json). Ingen produksjonsmodell er byttet.

## Spørsmålet

Gir global HGB-vekting og tre-rundersplanlegging en bedre kombinasjon enn hver av forbedringene alene? Ikke anta at gevinstene summeres: endret prognose kan endre både plan og hvor nyttig horisonten er.

## Matchet 2 × 2-design

| Prognose | Én runde | Tre runder |
|---|---|---|
| Oppdatert Ridge/Extra 50/50 | Eksisterende matchet kontroll | Eksisterende H3-utfordrer |
| Global, lært HGB-vekt | Ny matchet motorkontroll | Ny kombinasjon |

Alle fire bruker samme planlegger, shortlist-regler, solvertoleranse, faktiske GW4-overlevering, budsjett, priser og chipkalender. Den opprinnelige énrundersmotorens globalvektresultat beholdes som ekstern kontroll; det kan ikke uten videre brukes som den matchede H1-cellen, fordi likeverdige valg kan gi ulike forløp mellom motorer.

Evaluer alle celler på **2022/23–2025/26**. 2020/21 og 2021/22 er innledende metatreningssesonger, og skal ikke gis etterpåtilpassede vekter. Gjenbruk den eksisterende globale læringsregelen og de tidligere beregnede vektene. Ingen ny tuning av vekt, horisont, friksjon eller chipdatoer.

Med fire sesonger og to chipregimer er det 32 sesongforløp i den matchede matrisen. 16 Ridge/Extra-kontrollforløp kan gjenbrukes dersom kilder og input er identiske; de to globalvektcellene krever **16 nye forløp**. Opprinnelig referanse, original globalvekt-H1 og retrent Extra Trees brukes i tillegg som eksterne benchmarks på samme fire sesonger.

## Før-frist-prognoser

For aktuell runde gjenbrukes den globale blandingens prognose. Fremtidige runder bygges med samme `future_proxy` som i forrige H3-test: aktuell per-kamp-forskjell mot frossen referanse korrigerer dens nøytrale rate, aktuell kampeffekt halveres fremover, og blank aktuell runde bruker referansenøytral fallback. Ingen fremtidige `games`-rader leses. Alternativt bedre kalendergrunnlag må testes i et separat forsøk, ikke blandes inn her.

Dette beholder én nøytral fremtidig kamp per runde, frosne priser og eksisterende begrensninger for spillerpool og salg/gjenkjøp. Kandidaten er derfor en test av en bestemt proxy, ikke en bekreftelse på planlegging med faktisk kjent fremtidig kampprogram.

## Hva som avgjør om sporet er bedre

Primærmål er nettosesongpoeng med fast chipkalender. Rapporter særlig:

1. Ny kombinasjon minus globalvekt med matchet H1: isolert horisonteffekt for samme prognose.
2. Ny kombinasjon minus oppdatert Ridge/Extra med H3: isolert prognoseeffekt med samme horisont.
3. Samspill: `(global H3 − global H1) − (Ridge/Extra H3 − Ridge/Extra H1)`.
4. Gevinst mot opprinnelig referanse og retrent Extra Trees på identiske sesonger.

Rapporter middel, alle sesongvise forskjeller, seire, treffkostnad, solvergap og parete beskrivende intervaller. Uten chips er diagnostikk. En positiv middelgevinst mot referansen alene er ikke nok til å kalle kombinasjonen bedre enn de to eksisterende utfordrerne. Verken statistisk sikkerhet eller produksjonsklarhet skal konkluderes ut fra fire gjenbrukte sesonger.

## Etter kombinasjonsforsøket

Prioriter deterministiske valg ved like prognoseverdier, før-frist-kalender/tilgjengelighetsdata og en låst prospektiv evaluering. Ingen nye historiske vektsøk eller nye gate-terskler foreslås nå. Situasjonsstyrt gate beholdes som forskning; den har ikke dokumentert stabil tilleggsverdi over global vekt.
