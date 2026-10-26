SKADESTATUS OG LAGKAMERATERS FRAVÆR FOR ALLE SESONGER
Utvidelse av piloten, 25. oktober 2026

SAMLET MASTER
datasets/fpl_master_enriched_v3/player_matches.csv.xz har nå én samlet
tabell med alle 190 124 PL-observasjoner fra 2019/20 til 2026/27.
80 av_-felt er lagt til, med samme status-/lagkameratberegninger som
2023/24-piloten og ekstra opplysninger om kilde, tidsgrense og usikkerhet.
Alle opprinnelige felt fra master v2 er bevart: poeng, vær/sol, utlån,
kampbelastning, landskamper, hvile og kalender. 2026/27 går til GW7.
MASTER_ACTIVE.json peker direkte på v3. Ingen modell er trent eller endret.

DEKNING
154 506 PL-rader har en godkjent kilde (81,3 %). 35 618 er ukjente.
coverage.csv viser dekningen per sesong. Hoveddelen av hullene ligger i
2019/20 og 2020/21. Alle 272 prognosetidspunkter har en undersøkt arkivkilde,
men bare 214 passerer krav til alder og tidsgrense.

Nyere sesonger bruker hele FPL-øyeblikksbilder fra Randdalf/fplcache.
Arkivet starter 18. april 2021. Eldre perioder suppleres med daterte
players_raw.csv-versjoner fra vaastav/Fantasy-Premier-League. Disse må også
være publisert før tidsgrensen og høyst 24 timer gamle. Gamle tabeller
blir ikke gjort om til oppdatert skadestatus. Mange eldre runder blir
derfor ukjente. Manglende spiller gir ikke en oppfunnet klubb eller status.

Eldre spillertabeller mangler hendelsesmetadata som binder neste-/denne-
rundes spillesjanse til målrunden. Da brukes bare status og tropp, mens
av_reported_chance er ukjent og av_status_only_source=True. Null spillesjanse
blir aldri erstattet av 100 %. Kildens status er ikke en startprognose.

STATUS OG LAGKAMERATER
Samme regler som den kontrollerte piloten:
- a: FPL rapporterer tilgjengelig; d: tvilsom; i: skade-/sykdomsflagg;
  s: suspensjon; n: blant annet spilleberettigelse/andre forhold;
  u: blant annet overgang eller utlån. Dette er kildeopplysninger, ikke
  sikre medisinske diagnoser eller bekreftede laguttak.
- Spillerens egen nyhet, oppdateringsdato, rapportalder og returtekst
  følger med. Nyhetsdato er ikke skadedato. Entydig skadedato og returdato
  er ukjente; vi fyller ikke inn en sikker dato fra tvetydig tekst.
- Lagkamerater gjelder registrerte FPL-spillere i førfristkilden. Egen
  spiller utelates alltid. Samme posisjon betyr FPLs GK/DEF/MID/FWD-gruppe,
  ikke nødvendigvis samme taktiske rolle eller én direkte konkurrent.
- Tilgjengelige, tvilsomme, skade-/sykdomsrapporterte, suspenderte og andre
  utilgjengelige holdes adskilt. Utlån og overgangsrapporter er ikke skader.
  Rapporterte avganger utelates fra den vektede aktive troppen.
- Antall fravær og andel tidligere PL-minutter (28/90 dager) følger med.
  Bare tilgjengelig historikk i spillerens kildeoppgitte klubb teller.
  Strukturelle nuller fra utlån utelates fra vektingen. Null tidligere
  minutter betyr ikke uviktig spiller. Null nevner gir ukjent andel.
- Assistant Manager-brikkene i 2024/25 er ikke fotballspillere og utelates
  fra lagkamerattallene. 320 kildeobservasjoner av slike brikker er utelatt.
  De opprinnelige PL-observasjonene i masteren er ikke fjernet eller endret.

TIDSGRENSER OG KVALITET
Kildetid er seneste forfatter-/committertid i Git, kontrollert mot egen
metadatafil og innholdets sjekksum/Git-blob. Kilden må ligge strengt før
grensen og være høyst 24 timer gammel. Nyhetstid kan ikke ligge etter
kildetiden. Kildeformat, kildealder og avvisningsårsak følger radene.
Git-tid er en historisk proxy, ikke en uavhengig mottakskvittering.
av_strict_historical_qualified=False på alle rader. Ingen nyere kilde
eller sesongsluttstatus fyller tilbake historiske hull.

Faktisk FPL-frist brukes når den kan leses fra kilden. Den effektive
grensen er den tidligste av denne fristen og masterens operative prognose.
2019/20 og eldre CSV-perioder mangler bekreftet frist i selve kilden;
der beholdes masterens operative tidsproxy og dette merkes eksplisitt.

To tidsavvik er håndtert: 2021/22 GW18 bruker 18. desember 2021 kl.13:30 UTC,
og 2024/25 GW15 bruker 7. desember 2024 kl.11:00 UTC. Begge er tidligere
enn masterens eksisterende belastningsklokke. De nye tilgjengelighetsfeltene
bruker den tidligere fristen; de gamle masterfeltene bevares og avviket
merkes med av_mixed_origin_with_workload=True. En streng modelltest må
avklare felles tidsgrense for alle felt eller holde slike runder utenfor.

FILER OG KONTROLLER
player_match_context.csv.xz: én rad per season/fixture/code (190 124).
player_round_context.csv.xz: én rad per season/round/code (182 939).
source_player_status.csv.gz: kildeuttrekk uten kampresultater eller egne
prognoser. Uegnede kildeuttrekk beholdes bare som merket revisjonshistorikk.
snapshot_audit.csv: alle 272 kilder, alder, format og godkjenning/avvisning.
selected_sources.json: utvalg låst på metadata før tolkning av spillere.
metadata_verification.json: egen kontroll av kildecommit og tidsstempel.
verification.json: uavhengige lagkamerattall, minuttvekter og andeler,
tidsgrenser, kildekoblinger og bevaring av alle opprinnelige masterfelt.
Alle 28 742 spiller–runde-verdier fra den fullførte 2023/24-piloten er bevart.

De tidligere pilot- og masterutgivelsene er bevart. Den gamle pilotens
beskrivende diagnose er fortsatt et historisk kontrollresultat, ikke en
test av modellforbedring for denne utvidelsen. Ingen ny modellfit eller
automatisk aktivering er utført. Treningspekeren ACTIVE.json er bevart.

BRUK OG REPRODUSERING
Master v3 har samme iter_records-grensesnitt som v2. Observasjonsvisningen
inkluderer alle felt; historikkvisningen utelater strukturelle nuller og
retrospektivt vær som standard. av_source_known og kildeflaggene må følge
videre bruk. Alle nye tilgjengelighetsfelt er forskningsproxyer.
Denne pakkens loader.py leser separate proxy- og strenge kontekstvisninger;
den strenge visningen gir ingen rader fordi kravet ikke er oppfylt.

Kjør fetch.py, build.py, verify.py, verify_metadata.py, release.py. Ingen
utvalg gjøres etter kampresultater. Metadata og kilder beholdes lokalt med
sjekksum og eksplisitte referanser til tidligere arkiver. Masterarkivet
inneholder den samlede tabellen og innleseren; analysearkivet utelater de
store råkildene, som er låst i kildeinventaret.
