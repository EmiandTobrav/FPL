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
