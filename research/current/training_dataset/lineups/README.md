# Kvalifiserte kampstarter og dokumenterte strukturelle nuller

Oppdatert 8. oktober 2026. Dette er et separat statistikklag. Historiske
poeng/BPS/bonus/assists/defcon er fortsatt ikke kvalifisert til trening.

## Leveranse og dekning

`starts_qualified.csv.xz` har de samme 185 573 kanoniske spillerkampnøklene
som den historiske grunnoversikten. Originale starter beholdes i
`starts_original`; kvalifisert verdi og status ligger i egne kolonner.

- 152 901 rader har kvalifisert startverdi.
- Alle 77 279 observasjoner med FPL-minutter >0 er dekket i alle syv sesonger.
- Alle 2 660 kamper har nøyaktig 22 kvalifiserte starter.
- 42 697 tidligere manglende verdier er fylt for 2019/20–2021/22 med
  eksplisitte start-/innbytterroller fra komplette lagoppstillinger.
- 5 435 rader før GW16 i 2022/23 har direkte offisielt dokumentert rolle;
  disse inkluderer 2 992 starter som feilaktig stod som null i råuttrekket.
- 32 672 null-minutt-observasjoner mangler fortsatt kvalifisert startverdi,
  inkludert 3 056 tidlige 2022/23-rader uten direkte lagoppstillingsmedlemskap.
  Ingen slike utelatelser blir automatisk null.

[Dekning per sesong](starts_coverage.csv), [avledet manifest](application_manifest.json),
[gjeldende kontroll](validation_summary_v4.json),
[rå skjemaaudit](primary_reference/raw_schema_audit.csv).

Kvalifisering av hele kamper **for starter** er forskjellig fra godkjent
poengomregning. Sistnevnte har fortsatt null godkjente historiske kamper.

## Kilder og tidsordnet arbeid

Den nye Pannadata/Opta-kildeversionen er låst i `source_assets.json` med
release-asset-ID, størrelse og SHA-256. Begge rå Parquet-filer er hashkontrollert;
alle EPL-kolonner og -rader er beholdt i de kompakte kildeprojeksjonene.
Dette erstatter ingen eldre fryste kildearkiver. Binærbufferen er ignorert i Git.
`project_sources.py` bruker pyarrow 18.1.0; vanlig offline-replay trenger ikke
Parquet eller pyarrow fordi de verifiserte projeksjonene er versjonert.

Leverandørens `is_starter` og rekonstruerte minutter brukes ikke som fasit:
innsamlingskoden har posisjonsfallback og erstatter enkelte manglende minutter
med antatte minutter. Arkivprediktoren bruker bare eksplisitte slot 1–11 eller
innbytterposisjon i en komplett oppstilling, samt tidligere entydige,
godkjente identitetsankre og korrekt klubbside. Primærkilden bruker direkte
personkode i offisielle lineup-/substitutes-arrays.

V1 ble revidert til V2 før noen sammenligning med FPL-starter. V1-kode,
kontrollplan, prediksjoner og lock er beholdt. V2 ga 59 304 kontroller i
1 520 kamper. De tre senere kontrollsesongene stemte, mens 2022/23 hadde
2 992 avvik i nøyaktig 136 kamper før GW16. Den mislykkede kontrollen er bevart.

En ny **etterdiagnostisk** referanseplan ble låst før innhenting av offisielle
fullkampoppstillinger: alle de 136 tidlige kampene og faste kamper 1, 2, 3
fra både 2023/24 og 2024/25. Alle 142 svar er bevart med bytehash i
`primary_reference/raw_inputs.tar.gz`. Kampidentitet, dato, sluttresultat,
klubbside, elleve startere og unike personkoder kontrolleres før bruk.

Primærkilden dokumenterer de 2 992 starterne, mens alle 8 491 tidlige
FPL-observasjoner har `starts=0`. Dette beviser at tidlig rå `starts` ikke
representerer faktisk startrolle. Det beviser ikke datoen da FPL innførte feltet.
Alle fire xG-felter har også bare nuller i denne perioden. Disse nullene er
en uløst semantisk dekningssak, ikke kvalifisert xG-historikk. Ingen xG-verdier
er endret eller estimert i dette arbeidet.

V3 beholdt V2-prediksjonene og alle terskler. Den hadde ingen observerte avvik
mot kompatible referanser, og alle 240 senere primærroller stemte med FPL,
men den ekstra kontrollgaten feilet fordi fem innbyttere manglet prediksjon.
Denne feilen og årsaken er bevart; manglende prediksjon skilles fra feil verdi.

V4 tilfører **bare direkte primærmedlemskap** fra det låste utvalget. Den nye
planen og prediksjonene ble fryst før V4-kontrollen, uten å lese FPL-starter i
prediksjonskoden. Ingen kjent V2-prediksjon ble endret; 109 tidligere manglende
medlemskap ble dekket. Alle fire sesonggater er uendret: minst 300 kamper,
5 000 positive, 1 500 negative og null avvik per sesong. 59 413 kontroller i
1 520 kamper består. Alle 240 senere primærkontroller har nå prediksjon og
stemmer. Resultatet er regresjon på tidligere undersøkte sesonger og delt
Opta-opphav; det er ikke en ny blind eller uavhengig holdout.

## Reproduksjon og neste arbeid

Fra repo-roten:

```sh
python research/current/training_dataset/reproduce.py
python -m unittest discover -s research/current/training_dataset/lineups -p 'test_*.py' -v
```

Samlet offline-replay lager og sammenligner 50 resultatfiler i en separat
kopi, uten de lokale binærbufferne. Alle 50 er byteidentiske. Elleve nye tester
kontrollerer identitetsfeil, ufullstendige oppstillinger, feil resultat,
leverandørfallback, originalbevaring og sperrer mot ukvalifisert anvendelse.
Til sammen består 33 fokuserte tester; full repo-/CI-test er ikke bekreftet.

Neste startarbeid kan undersøke kvalifisering av eksplisitte nuller utenfor
troppen gjennom et bevist komplett sett med elleve startidentiteter på hver
klubbside. Dette trenger en egen fryst regel og kontroll av hele populasjonen;
det er ikke generell nullfylling fra manglende statistikk eller minutter.
Det gjelder bare startrollen, aldri endrede scoringskomponenter.

Den større leveransen trenger fortsatt ekte eldre xG-dekning, resterende
scoringsinput/årsaker, regel- og kildekvalifisering, poengetiketter, tidsriktige
features og innlesing gjennom den aktive treningspipelinen.
