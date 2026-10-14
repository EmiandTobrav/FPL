FPL-treningsdatasett etter 2026/27-reglene — praktisk versjon1

Status: ferdig til eksperimentell modelltrening med dokumenterte tilnærminger.
Brukeren har bedt om å ferdigstille datasettet så godt som mulig. Denne
versjonen bruker de valgte omregnede poengene og aksepterte estimatene som
treningsmål. Den gjør ikke uavklarte kilder til kildeverifiserte fakta.

Start her
training_rows.csv.xz er den ferdige modelltabellen. target_total_points
er poengene i prediction-round/round r. Features står i schema.json.
Bruk loader.py: den velger bare tillatte features og riktig tidsdeling.
Avhengigheter: Python3.12, pandas2.2 og numpy. Modelltrening er ikke utført.

Eksempel etter at pakken er pakket ut:
from loader import load_training_data
train = load_training_data(split="train")
valid = load_training_data(split="validation")
test = load_training_data(split="test")
X_train, y_train = train["X"], train["y"]

Innhold og dekning
- Alle2 280 aktive historiske kamper i2020/21–2025/26 er omregnet,
  med66 677 poengrelevante spillerkamper.
- 96 395 observerte, native nullutfall for historiske ikke-deltakere er
  tatt med som best-effort-nullmål. Kort på benken er egne beregnede
  negative utfall og inngår ikke i denne nullgruppen. Dette nuller ingen
  manglende eksterne statistikkfelt og etablerer ingen komplett kjøpsroster.
- 1 538 native spillerkamper og3 216 spiller–runde-utfall fra2026/27
  er bevart som en separat current_native-del.
- Mastertabellen bevarer187 111 spillerkamper fraalleåtte sesonger.
  164 610 har best-effort-poengmål. Den tidligere utsatte2019/20-sesongen
  har ingen nye poengmål og brukes kun som native historikk/reference.
- Modelltabellen har159 291 spiller–runde-rader. Oppsummering og komplett
  dekning ligger i summary.json og coverage.csv.

Tidsdeling
train: 2020/21–2023/24, 99 818 rader.
validation: 2024/25, 26 919 rader.
test: 2025/26, 29 338 rader.
current_native: 2026/27 GW1–GW5, 3 216 rader; utenfor standardtreningen.
Sesongene er tidligere brukt i forskningsarbeid. Dette er en kronologisk
evaluering, ikke en påstand om en tidligere urørt holdout.

Horisont-targets
H1 = target_total_points i runden r som skal predikeres.
H3 = target_points_h3 for r..r+2; H6 = target_points_h6 for r..r+5.
137 362 H3- og108 349 H6-targets har komplette observerte summer.
En manglende fremtidig spiller–runde blir ukjent, aldri en oppdiktet null.
Horisontene krysser ikke sesonggrenser. Dette er en prediksjonsrunde-
konvensjon, ikke de gamle kanoniske tabellenes ankerrunde r+1-konvensjon.

Features og tid
De21 numeriske features bruker kun spillerens tidligere native minutter,
mål, assists, clean sheets, starter og FPL-poeng, med3/5/10-observasjons-
gjennomsnitt, historikklengde og avstand til siste tilgjengelige observasjon.
Ingen current-round-statistikk, pris, eierskap, kvalitet/estimatflagg eller
fremtidig motstander-/kalenderfasit brukes som feature. Originale og
supplerende statistikker ligger fortsatt i egne tabeller for videre arbeid.
Ved manglende historikk bruker modellfeatures0 og et eksplisitt
f_history_missing-flagg. Rå statistikk og target-mangler imputeres ikke.

Faktiske historiske FPL-frister og statistikkvintager er ikke dokumentert.
Denne praktiske versjonen bruker derfor en synlig, konservativ proxy:
- forecast_cutoff_proxy = tidligste faktiske kamp i prediksjonsrunden -7d.
- available_after_proxy = siste faktiske kamp i historikkrunden +7d.
- Bare historikk som ligger strengt før cutoff tillates.
Det gir minst14d avstand fra historikkamp til første prediksjonskamp.
Tidskontrollen er bestått for denne proxykontrakten. Den beviser ikke
en historisk deadline-roster, publiseringsversjon eller produksjonsklar
FPL-beslutningssimulator. Det faktiske observerte spilleruniverset beholdes;
kjøpbare spillere som ikke finnes i materialet, oppfinnes ikke.

Kvalitet uten å stanse leveransen
March39, Gabriel53 og Wissa53 er eksplisitt aksepterte BPS-estimater.
847 tidligere aksepterte inputestimater er også bevart. Estimatmerking
følger hele kampen og videre inn i spiller–runde-tabellen.
De14 historiske BPS-kontrollavvikene beholdes, med egen merking av deåtte
kampene som er bonusfølsomme i +/-5-stresstesten. Stresstesten er ikke
en BPS-rettelse. De valgte verdiene beholdes i alle disse kampene.
Keeper-/kildekonflikter beholdes som fixture_source_conflict.
Alle rader er med i standardinnlesingen. exclude_flagged=True gir en
separat sensitivitetsvisning. Den er ikke et nytt fasituavhengig holdout-
utvalg eller automatisk kildegodkjenning.

Bevaring og bruk
player_matches.csv.xz beholder gamle original- og kvalifiseringskolonner.
De nye beste tilgjengelige målkolonnene heter target_total_points,
target_bps og target_bonus. Gamle tomme total_points_2026_27-felter betyr
streng gammel kvalifisering og er ikke modelltabellens standardtarget.
Manifestet setter training_ready_best_effort=true og oppgir samtidig at
streng kildekvalifisering ikke er komplett. Gamle gater, kilder, modeller
og benchmark er uendret. Dette er en egen dataversjon med egen innleser.
Når nye modeller senere evalueres, er fixture_full_h3_adaptive_tc primær-
benchmark. Den må kjøres på nytt på samme omregnede poengmål; gamle
benchmarkpoeng kan ikke overføres til det nye datasettet.

Filer
training_rows.csv.xz: modellfeatures, poengmål, splitter og kvalitetsflagg.
player_matches.csv.xz: originaler, valgte poengmål og masterstatistikker.
player_rounds.csv.xz: komplette observerte rundesummer og native historikk.
input_counters.csv.xz: ferdigstilt aktivt inputledger med kilde/estimatstatus.
feature_time_audit.csv.xz: cutoff og siste brukte historikk for hver modellrad.
schema.json: eksplisitt featureliste og targetdefinisjoner.
manifest.json: versjon, input-/outputhash og policy.
summary.json / coverage.csv / verification.json: tellinger og kontroller.
loader.py: fungerende, portabel innlesing; README.txt: dette datakortet.
