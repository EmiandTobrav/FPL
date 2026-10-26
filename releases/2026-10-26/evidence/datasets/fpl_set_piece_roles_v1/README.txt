DØDBALLROLLER OG FRAVÆRSSCENARIOER
25. oktober 2026

SAMLET MASTER
datasets/fpl_master_enriched_v4/player_matches.csv.xz er den samlede
masterfilen. Alle 190 124 opprinnelige PL-rader og alle v3-felt er bevart.
93 nye sp_-felt dekker dødballroller, kildekvalitet og fraværsscenarier.
MASTER_ACTIVE.json peker direkte på v4. Modellen er ikke endret.

Tre rollekategorier:
- penalties: straffer
- corners_indirect_freekicks: cornere og indirekte frispark, samlet slik FPL
  rapporterer dem. Kilden skiller ikke konsekvent de to kategoriene.
- direct_freekicks: direkte frispark

FPLs oppførte rekkefølge og eventuell tekst beholdes. Dette er rapportert
hierarki, ikke observerte dødballer, sannsynligheter eller bekreftede
kampoppgaver. Vi anslår ikke xG-gevinst eller faktiske dødballandeler fra
rekkefølgen. Per-rolle-oppdateringstid mangler selv når kildebildet er ferskt.

DEKNING OG MANGLENDE VERDIER
149 707 masterrader har brukbart rollegrunnlag (78,7 %). 40 417 er ukjente.
206 av de 272 undersøkte prognosetidspunktene har brukbart rolleskjema.
2019/20-kildene mangler disse feltene. Eldre og uegnede kilder beholder
ukjente roller. coverage.csv viser sesongvis dekning.

sp_<rolle>_source_known skiller mellom manglende kilde og et eksisterende
felt som er tomt. Et tomt ordre-felt i en gyldig kilde betyr ikke oppført:
listed_for_role=False, listed_order tom. Det betyr ikke at spilleren aldri
kan ta dødballen. Manglende skjema eller uegnet kilde gir ukjent, ikke False.
Null blir aldri gjort om til ordre 0 eller en oppfunnet sisteplass.

LAGLISTE OG KVALITET
Felt per rolle viser blant annet oppført ordre, oppført førstevalg,
antall oppførte spillere, førstevalg, delte plasser og hull i rekkefølgen.
Kildegrunnlaget er registrerte FPL-fotballspillere før tidsgrensen.
Assistant Manager-brikker og andre ikke-spiller-typer utelates.
Ingen nye spillere eller FPL-observasjoner legges til i masteren.

Delte plasser beholdes. Manglende ordre 1 eller et hull før spillerens
egen ordre blir ikke fylt med gjetning. Listene kan være ufullstendige
eller utdaterte selv om FPL-øyeblikksbildet er ferskt. Derfor er
sp_role_list_is_exhaustive=False og sp_role_update_time_known=False.

FRAVÆRSSCENARIOER
Tilgjengelighet hentes fra samme førfristkilde og samme identitet som
v3-laget for skadestatus. Antall spillere foran oppgis adskilt som
tilgjengelige (a), tvilsomme (d), utilgjengelige (i/s/n), rapporterte
avganger/utlån og ukjent status. Overgang/utlån regnes ikke som skade.

sp_<rolle>_potential_promotion=True krever at spilleren har en oppført
ordre etter førsteplassen, selv rapporteres tilgjengelig, og at alle
oppførte spillere foran rapporteres ute. Alle ordrenumre før spilleren
må finnes, og lagets rolleskjema må være komplett innen kildepoolen.
Tvilsom status er ikke fravær. Ukjent status, hull eller egen tvil gir
ingen sikker positiv indikator. Et oppført førstevalg trenger ikke
opprykk, og får derfor potential_promotion=False.

top_remaining_listed_candidate og unique_top_remaining_candidate beskriver
kandidater blant de oppførte spillerne som ikke rapporteres ute. Delte
plasser og ukjent status kan hindre en entydig kandidat. Egen utelatelse
og sammenligning bygger på stabile FPL-koder, ikke navnelikhet.

Indikatorene er mulige rolleendringer dersom spilleren velges til kampen.
Status a betyr ikke bekreftet start. En annen, ikke oppført spiller kan
overta. n kan gjelde spilleberettigelse i én kamp, også i en dobbelrunde.
Indikatoren beviser derfor ikke samme rolle i alle rundens kamper.
sp_actual_taker_confirmed=False og
sp_promotion_is_scenario_not_confirmed_role=True på alle rader.

TID OG KILDER
De tidligere låste FPL-kildene fra tilgjengelighetsutvidelsen gjenbrukes.
Kilden må ligge før effektiv prognosegrense og være høyst 24 timer gammel.
Samme kildebyte, spiller-ID, klubb og nyhetstidskontroll som i v3 brukes.
Grensen er samme av_forecast_at, inklusive de tidligere faktiske fristene
i 2021/22 GW18 og 2024/25 GW15. Ingen senere rolleopplysninger fyller hull.

Kildene er Git-tidsproxyer, ikke uavhengige historiske mottakskvitteringer.
sp_strict_historical_qualified=False. De øvrige v3-usikkerhetsflaggene,
inklusive blandede tidsgrenser i to runder, beholdes uendret.
Ingen kampresultater, senere dødballhendelser eller sesongsluttlister
brukes for å bestemme førfristrollen.

FILER
player_match_context.csv.xz: 190 124 rader, season/fixture/code.
player_round_context.csv.xz: 182 939 rader, season/round/code.
source_roles.csv.gz: kildeuttrekk med rå ordre-verdi som JSON, skjemastatus,
rapportert tekst, statuskobling og sjekksum. Inaktive eller uegnede
kildeuttrekk beholdes kun som tydelig merket revisjonsgrunnlag.
source_audit.csv: undersøkte runder og rollefeltenes dekning.
potential_promotion_scenarios.csv.gz: positive scenarioindikatorer med
spiller, rolle, oppført rekkefølge og oppførte spillere foran.
scenario_examples.csv: første tolv slike indikatorer, valgt uten utfall.
verification.json: uavhengige rolle-, gruppetalls- og scenariokontroller,
bevaring av alle masterfelt, entydige koblinger og fjorten grensetester.

REPRODUSERING OG BRUK
build.py beregner, verify.py kontrollerer, examples.py lager revisjons-
eksempler og release.py publiserer aktive pekere og arkiver. Originale
kilder gjenbrukes fra tidligere utgivelser, uten å endre disse.
input_hashes.json og manifest.json låser kilder og resultater med SHA256.
Analysearkivet inneholder eksplisitte råfilreferanser, ikke alle råkildene.
Masterarkivet inneholder den samlede tabellen, innleser og dokumentasjon.
loader.py tilbyr separat proxy- og streng kontekstvisning. Den strenge
visningen er tom. Ingen modell er trent, endret eller automatisk aktivert.
