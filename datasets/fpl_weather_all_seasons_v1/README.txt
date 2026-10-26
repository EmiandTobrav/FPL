VÆRDATA FOR FPL — ALLE OBSERVERTE SESONGER, VERSJON 1

Omfang
2019/20–2025/26: alle 380 kamper i hver av de sju sesongene.
2026/27: bare de 50 kampene som allerede finnes i originaldatasettet,
fra 21. august til 20. september 2026. Dette er ingen oppdatering av
kamp-/spillergrunnlaget til dagens dato og ingen innhenting av fremtidig vær.
Samlet forventet dekning: 2 710 kamper og 187 111 spillerkamper.
2019/20 er fortsatt historisk referanse i poenggrunnlaget. Poengmål,
kvalitetsflagg, splitter og modeller er uendret.

Filer
match_weather.csv: samlet kamptabell. Én rad per (season, fixture).
weather_key har formen 2021-22:263 og er unik på tvers av sesonger.
player_match_weather_links.csv.gz: bro til originaltabellens spillerkamper,
med season, fixture og element som unik spillerkampnøkkel.
stadiums.csv: sesongspesifikke hjemmearenaer med koordinater og kilder.
season_summary.csv: dekning og usikkerhetsflagg per sesong.
sunrise_sunset_flags.csv: alle rader der ujusterte solminutter overstiger dagslys.
kickoff_conflicts.json: avvik mellom spillerens tidsfelt og kampens tidsfelt.
verification.json: samlet kontrollresultat, inkludert sammenligning med piloten.
RESULTATER.txt: kort lesbar resultatoversikt.
manifest.json: SHA256 for alle leveransefiler og originaltabellen.
Hver sesongmappe inneholder også normaliserte timeverdier, per-kamp-tabell,
råsvar, URL-er, hentetidspunkt og separate kontrollresultater.

Kilder og modell
Weather data by Open-Meteo, ECMWF IFS.
https://open-meteo.com/en/docs/historical-weather-api
Alle værkall bruker eksplisitt models=ecmwf_ifs, timezone=GMT og m/s for vind.
Modellens historikk begynner i 2017 og dekker dermed alle aktuelle sesonger.
Dette er værrekonstruksjoner for geografiske ruter, ikke stadionmålinger.
Open-Meteo oppgir CC BY 4.0 for værdata; andre kilder beholder egne vilkår.

Kampkontroll: offentlig Vaastav/Fantasy-Premier-League-arkiv per sesong.
2026/27 bruker den bevarte offisielle FPL-snapshoten fra 8. oktober 2026.
Kampkildene kan ha felles opphav med mastertabellen; separat innhenting
er ikke en uavhengig måling av faktisk spilletid eller kampsted.
Stadioner velges fra hver sesongs lag-/stadiontabell, ikke dagens hjemmearena.
Koordinater fra List of Premier League stadiums; Hill Dickinson fra egen artikkel.
Kilder og korreksjoner er eksplisitte i stadiums.csv og råkildenes metadata.

Historiske unntak
Everton: Goodison Park til og med 2024/25, Hill Dickinson Stadium fra 2025/26.
Stadionoversiktens koordinat for Hill Dickinson avviker fra stadionartikkelen.
Vi bruker 53.4251, -3.0028 fra den dedikerte artikkelen, med merking.
Etihad Stadium og City of Manchester Stadium behandles som samme arena.
Brighton–Aston Villa, 26. februar 2022, fixture 263: native spillerrader sier
15.00 UTC, kampoversikten sier 15.30 UTC. Kampen ble utsatt 30 minutter
på grunn av trafikk. Været bruker 15.30, og de 78 originale spillerradene
bevares med synlig avviksmerking i den nye koblingen/kamptabellen.
https://www.brightonandhovenews.org/2022/02/26/traffic-delays-kick-off-as-brighton-and-hove-albion-prepare-to-host-aston-villa/

Tidskobling og metode — samme som piloten
Vindu: [registrert avspark, avspark + 120 minutter). Fast totimersproxy,
ikke individuelt spilte minutter eller dokumentert faktisk sluttsignal.
UTC internt; Europe/London brukes for lokal tid, med historisk sommertid.
Temperatur, luftfuktighet, skydekke og vind interpoleres lineært mellom
timene. _kickoff er ved avspark; _mean er tidsvektet middel gjennom vinduet.
Nedbør, solskinn og stråling gjelder foregående time ved hver API-tidsstempel.
Vi vekter overlapp med (t-1 time, t], slik at halv- og kvartersavspark håndteres.
Summene forutsetter jevn fordeling innen hver time. Ingen minuttpresisjon påstås.

Variabler og enheter
temperature_2m: grader Celsius. relative_humidity_2m, cloud_cover: prosent.
wind_speed_10m, wind_gusts_10m: meter per sekund.
precipitation, rain: millimeter. snowfall: centimeter.
sunshine_duration_sum: estimerte solsekunder i kampvinduet.
sunshine_minutes: samme verdi i minutter, før dagslysavgrensning.
direct_radiation_mean, shortwave_radiation_mean: watt per kvadratmeter.
daylight_minutes, daylight_fraction: vinduets overlapp med soloppgang–solnedgang.
is_day finnes i timetabellene; dagslysvinduet bruker daglige soloppgangstider.
Solskinnsvarighet beregnes av kilden fra direkte normalinnstråling over 120 W/m².
Total solinnstråling inneholder også diffust lys og betyr ikke alene direkte sol.

Usikkerhet ved solnedgang og soloppgang
Timeverdier kan tilordne sol til et mørkt tidsvindu som overlapper en time
med dagslys. sunshine_minutes beholder rådataanslaget.
hourly_sunshine_exceeds_daylight markerer at anslåtte solminutter overstiger
antall dagslysminutter i kampvinduet, med 0,0001 minutts avrundingstoleranse.
sunshine_minutes_daylight_capped = min(sunshine_minutes, daylight_minutes).
Dette separate hjelpefeltet er en enkel avgrensning, ikke en korrigert måling.
Mørke kamper får 0 i dette feltet selv om timefordelingen ga positive solminutter.
Strålingsfeltene beholder samme timebegrensning; bruk dem sammen med dagslys.
daylight_transition i solkategorien synliggjør alle delvis opplyste kampvinduer,
også når estimatet ikke overstiger dagslyset.
Stadiontak, skygge på banen og lokal vindskjerming er ikke modellert.

sun_category_heuristic er en beskrivende regel, ikke meteorologisk fasit:
dark: ingen dagslysminutter; daylight_transition: 0–120 dagslysminutter;
mostly_sunny: fullt dagslys og minst 60 ujusterte solminutter;
some_sun: fullt dagslys og positivt solskinn under 60 minutter;
no_direct_sun: fullt dagslys og null solskinn.

Kontroller
Alle observerte fixture-ID-er, kanoniske avspark, lag-ID-er, hjemme/borte,
motstandere og runder kontrolleres mot kildeoversikten. Native tidsavvik
må ha en eksplisitt dokumentert løsning; ukjente avvik stopper arbeidet.
Hele sesonger krever 19 hjemme- og 19 bortekamper per klubb og 380 unike par.
Den pågående sesongen krever dekning av alle og bare de 50 observerte kampene.
Arenaer kontrolleres mot sesongtabell. Dette er ikke bevis for hvert enkelt
kampsted dersom en særskilt nøytral arena skulle være brukt.
Værsvar kontrolleres for enheter, unike timer, kontinuitet og avstand til stadion.
Manglende verdier blir ikke nuller. En tom verdi i kampvinduet stopper beregning.
Separat kontrollkode regner ut 11 aggregater per kamp på nytt direkte fra
rådata, med minuttbasert integrasjon og toleranse for fire desimalers avrunding.
Kontrollene bekrefter kobling og beregning, ikke værnøyaktighet mot målestasjoner.
Alle felt fra den opprinnelige 2022/23-piloten sammenlignes og kreves uendret.
Originaltabellens filhash kontrolleres før den samlede pakken ferdigstilles.

Bruksgrense
Historisk vær brukes til etteranalyse. Det er ikke et værvarsel som var kjent
ved FPL-fristen. Ingen fremtidig kampvær kan brukes som før-frist-feature uten
en separat, tidskvalifisert værvarselkilde. Ingen modell er trent her.

Gjenskaping fra prosjektmappen (Python 3.9+, standardbibliotek)
python3 datasets/fpl_weather_all_seasons_v1/collect_sources.py
python3 datasets/fpl_weather_all_seasons_v1/run_all.py prepare
python3 datasets/fpl_weather_all_seasons_v1/run_all.py fetch
python3 datasets/fpl_weather_all_seasons_v1/run_all.py build
python3 datasets/fpl_weather_all_seasons_v1/run_all.py verify
python3 datasets/fpl_weather_all_seasons_v1/assemble.py
Bevarte råsvar gjenbrukes. Originalpiloten og masterdata endres ikke.
