# Kontroll av poengfølsomme minuttkonflikter

7. oktober 2026. Videreført fra `579fe37` på PR #1, med brukerens valg om
endelig korrigerte hendelser etter 2026/27-reglene. Ingen historiske
kilderader, keeperverdier eller låste etiketter er overskrevet.

## Resultat

Alle **710** gjenværende poengfølsomme minuttkonflikter er undersøkt mot
arkivets bytter, startoppstillinger og periodeklokker.

| Resultat | Unike spillerkamper |
|---|---:|
| Hele minuttbidraget dokumentert | **320** |
| Grunnpoeng dokumentert, BPS-avrunding uavklart | **364** |
| Særtilfelle, motstridende klokke eller manglende hendelser | **26** |
| Fortsatt åpne poengfølsomme minuttbehov | **390** |

De 320 avklaringene gir **880 389 åpne poengbehov** i den samlede køen,
fortsatt fordelt på **77 280 unike spillerkamper**. Råstatistikk-/regelresten
på **881 632** er uendret: minuttkildenes ulike heltall beholdes til
minuttdefinisjonene er normalisert. Dette er dokumenterte poengkomponenter,
ikke 320 nye råtellerverdier, komplette poengsummer eller bonusetiketter.
Fergusons tidligere avklaring inngår allerede i forrige kø og telles ikke igjen.

## Hvorfor kildenes minuttall ikke kan sammenlignes direkte

[FPLs egen forklaring](https://www.premierleague.com/en/news/4661030) sier at
60-minuttersgrensen gjelder faktisk fullførte ordinære minutter. Et bytte
ved eksempelvis 59:40 ligger i kampens 60. minutt, men gir 59 fullførte
minutter. Mange av avvikene følger nettopp dette mønsteret: FPL 59,
FotMob/arkiv 60, og en byttehendelse med minutt 59 og et sekundtall.

For godkjenning krever byggeren:

1. Entydig spiller-/kamp-/lagkobling og startoppstilling med elleve startere.
2. Sammenfallende startplass- og posisjonslister; ingen innbytte-/retursekvens for spilleren.
3. Begge perioders eksplisitte start- og slutthendelser, med andre omgang fra 45 minutter.
4. Én utbyttehendelse i andre omgang og like mange inn-/utbytter ved samme tidspunkt på samme lag.
5. Samsvar mellom fullførte minutter fra klokken og den registrerte FPL-verdien.
6. Samme BPS-bånd enten varigheten leses som fullførte, påbegynte eller faktiske minutter.

Første omgangs tilleggstid tas dermed ikke med i andre omgangs ordinære
klokke. Avbrudd, utvisninger og ikke-kontinuerlig deltakelse holdes utenfor
standardmetoden. Slettede hendelser tolkes ikke som aktive bytter.
Krav om samtidige byttepar er konservativt og kan avvise reelle bytter
som har litt forskjellige registreringstidspunkter.

**BPS ved 60:01–60:59 er ikke kvalifisert.** Den publiserte
[BPS-tabellen](https://www.premierleague.com/en/news/4661029) skiller mellom
1–60 og over 60 minutter, men forklarer ikke tydelig hvordan sekunder
omsettes til BPS-minutter. Å bruke FPLs avrunding for grunnpoeng automatisk
også i BPS ville være en ny antakelse. Derfor er 364 rader eksplisitt
flyttet til `rule_unresolved` for poengberegningen. Deres tidligere
`source_conflict`-status og råverdier er bevart. Grunnpoengbevisene finnes
i `decisions.csv`, men ingen komplett minuttavklaring telles for disse.

## De 26 særtilfellene

| Kontroll som gjenstår | Spillerkamper |
|---|---:|
| Hendelsesklokken avviker fra fullførte FPL-minutter | 9 |
| Tidlig slutt eller avbrudd i kildedekningen | 4 |
| Kamp mangler i arkivet | 4 |
| Utvisning krever egen klokkevurdering | 3 |
| Innbytterintervall må rekonstrueres | 2 |
| Inn-/utbytte har ikke balansert registreringstidspunkt | 2 |
| Ikke-kontinuerlig deltakelse | 1 |
| Klokkehendelser mangler | 1 |

Se `remaining_sensitive_minutes.csv` for navn, kamp, kildeverdier,
hendelses-ID og konkret årsak. Særtilfellene omfatter blant annet Schärs
avbrutte deltakelse, Zinchenko/João Pedro/Krejčís utvisninger og Brownhill/
Veltmans innbytterintervaller. Ingen av disse er fylt med antatte verdier.

## Filer og videre arbeid

- `minute_component_supplement.csv`: 320 avklarte grunnpoeng-/BPS-minuttbidrag.
- `decisions.csv`: alle 710 undersøkte spillerkamper, inkludert delvise bevis.
- `resolution_queue.csv.gz`: ny samlet kø med tidligere beslutninger bevart.
- `field_summary.csv`: rest per felt, delt i datamangel, konflikt og regelberegning.
- `remaining_player_matches.csv.gz`: én rad per unik berørt spillerkamp med alle åpne felt.
- `match_summary.csv`: feltbehov og unike berørte spillere per kamp.
- `inputs/`: 710 målposter og 37 394 relevante hendelser fra det hash-låste arkivet.
- `inputs/provenance.json`: kildehash, uttrekksfiltre, regler og parserreferanse.

Bruk denne køen som nyeste arbeidsgrunnlag. Tidligere mål-/selvmålsrettinger,
Fergusons minuttbidrag og keeperavklaringer anvendes fortsatt som separate
tillegg. Full BPS/bonus må vente på resterende råfelt og regelavklaringer.

Neste effektive steg er å kvalifisere **én felles BPS-minuttkonvensjon**
for de 364 grensefallene gjennom offisiell dokumentasjon eller en isolerbar,
uavhengig kontroll av publiserte BPS-komponenter. Det er mer nyttig enn å
hente 364 nye kopier av samme avrundede minuttall. De 26 særtilfellene har
konkrete hendelsesbehov som kan følges opp separat. Ingen ny holdout eller
modelltrening er utført. Kostnad 0 NOK.

## Reproduksjon og begrensninger

Bygg fra repositoryroten med pandas:

```sh
python3 research/current/scoring_2026_27/minute_reconciliation/build.py
python3 -m unittest discover -s research/current/scoring_2026_27/minute_reconciliation -p 'test_*.py'
```

`prepare_inputs.py /path/to/events_EPL.parquet` kan gjenskape uttrekket med
pyarrow. Det krever nøyaktig den allerede dokumenterte SHA-256-versjonen;
vanlig bygg bruker de versjonerte uttrekkene uten nettverksinnhenting.
Kildearkivet er et offentlig supplerende arkiv, ikke et nytt offisielt
API-svar. Parserens kodeoversikt er publisert, men ikke leverandørsertifisert.
Dette er en avgrenset rekonstruksjon med FPL-korroborasjon og eksplisitte
strukturkontroller, ikke bevis for at hele hendelsesarkivet er komplett.

16 nye og 48 eksisterende fokuserte tester består. Ni genererte filer er byte-identiske ved ny kjøring. Full repositoriesuite og GitHub CI er ikke verifisert.
