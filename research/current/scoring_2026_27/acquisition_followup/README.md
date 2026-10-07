# Videre datainnhenting – 7. oktober 2026

**Delvis løsning, ikke full historisk harmonisering.** Fire historiske assists er nå dokumentert med offisielle avgjørelser. 119 nye spiller-/kampresponser er innhentet for de fire berørte kampene. En innhenter med varige kontrollpunkter og en kø for hele 2024/25 er klar. Keepernes historiske storsjanseredninger er fortsatt uløst. Ingen modelltrening, benchmarkendring eller kostnad.

## Verifiserte assisttillegg

Premier Leagues [egen gjennomgang](https://www.premierleague.com/en/news/4362187/whats-new-in-202526-fantasy-changes-to-assists-rules) navngir fire mål fra 2024/25 som skulle gitt assist etter regelendringen. Disse er koblet til arkivets spiller-ID, kamp-ID og faktiske målscorer. Alle fire hadde null historiske assists i den aktuelle kampen.

| Spiller | Kamp | Dato | FPL-kamp | Tillegg |
|---|---|---|---:|---:|
| Omar Marmoush | Man City–Aston Villa | 22.04.2025 | 336 | 1 assist |
| Pedro Porro | Arsenal–Tottenham | 15.01.2025 | 201 | 1 assist |
| Alex Scott | Bournemouth–Fulham | 14.04.2025 | 312 | 1 assist |
| Jordan Pickford | Brighton–Everton | 25.01.2025 | 223 | 1 assist |

Dette gir **12 direkte spillerpoeng**, før eventuell endring i bonus. Assistleddet i BPS øker med 9 for hver spiller. Bonus må beregnes på nytt for hele kampen; den er ikke beregnet her. De fire avgjørelsene er ikke bevis for at alle andre assistetiketter i kampene er ferdig vurdert.

De relevante kriteriene ble kontrollert mot den faktisk leverte 2026/27-regelkomponenten: mottak innenfor/utenfor feltet, defensive berøringer og siste angrepstouch før hands. Kilde- og regelhash ligger i `findings.json`. To offisielle avslag er bevart som negative kontroller: Bruno Fernandes før Ugartes mål mot Everton og Cunha før Dohertys mål mot Chelsea.

Korreksjonene finnes i `verified_assist_additions.csv`; alle seks avgjørelser i `assist_decisions.csv`. De er separate tillegg og er **ikke** skrevet inn i det låste datasettet. PL oppgir 41 ekstra assists for hele 2024/25; disse fire er bare et delsett. Eldre sesonger er ikke dermed løst.

## Innhenting som kan fortsette etter avbrudd

`collect_resumable.py` lagrer hvert godkjent svar atomisk og skriver kontrollpunkt etter hver fullført forespørsel. Ved omstart kontrolleres manifest og råfilhash, og ferdige svar hoppes over. Det er høyst seks samtidige forespørsler, minst 0,75 sekund mellom starttidene og 30 sekunders timeout. HTTP 401/403/429 stopper videre innsending; det finnes ingen omgåelse eller automatisk retry på tilgangssperrer.

Kontrollene avviser feil spiller-ID/Opta-ID, aggregerte flerkampssvar, dupliserte statistikkfelter, doble jobber og endret manifest. Utelatte tellinger beholdes som manglende.

Den nye kjøringen fullførte **119/119 rader, fire kamper, null feil**. Alle 119 minuttall samsvarer med de fryste FotMob-radene. En ny kjøring hoppet over alle ferdige svar og ga samme datasett uten nettverksinnhenting. Åtte målrettede tester består. Dette er kontroll av innhenting og de fire assistavgjørelsene, ikke en ny test av komplett BPS.

`collection/observations.csv` har alle nye normaliserte verdier. `collection/sources.json` dokumenterer URL og SHA-256 for hvert svar. Feltene inkluderer 54 eksplisitte tellinger av vunne taklinger, 20 av vellykkede innlegg uten cornere, fem skuddfeil og to målfeil. Andre rader er utelatt/ukjent, ikke automatisk null. Ingen av de åtte keeperradene har eksplisitt `big_chance_saves`.

`prepare_manifest.py` bygger køer fra prosjektets eksisterende kamper, Opta-koder og aktive kilderader. En full kø for 2024/25 er bygget og kontrollert: **11 567 rader, 380 kamper, ingen uløste ID-er**. Hele køen er ikke kjørt. Koden støtter 2019/20–2025/26, men full købygging for de andre seks sesongene er ikke testet i denne oppfølgingen.

Fra en full checkout:

```bash
python research/current/scoring_2026_27/acquisition_followup/prepare_manifest.py --season 2024-25 --output queue.csv
python research/current/scoring_2026_27/acquisition_followup/collect_resumable.py queue.csv primary_2024 --limit 500
# Kjør samme kommando igjen for neste bolk; behold samme kø og outputmappe.
python research/current/scoring_2026_27/acquisition_followup/build_assist_patch.py
python research/current/scoring_2026_27/acquisition_followup/test_collection.py
python research/current/scoring_2026_27/acquisition_followup/test_assist_patch.py
```

På en ny checkout er de 119 normaliserte radene bevart. Den lokale råcachen/kontrollpunktet er ikke del av denne publiseringen; start en ny outputmappe for nye innhentinger. En full kø vil hente de fire kontrollkampene på nytt dersom de ikke allerede finnes i akkurat den køens cache.

## Nye kilder undersøkt

| Kilde | Faktisk resultat |
|---|---|
| Premier Leagues nyere SDP-API | Historisk 2019/20-kamp, lagoppstillinger, lagstatistikk og kommentarfelt tilgjengelig. De undersøkte rutene gir ikke full spiller-/kamphendelsesstrøm med storsjanseflagg. Spillerens sesongkampliste inneholder kampmetadata, ikke BPS-tellingene. |
| `imadeddine-belkat/Premier-League-Stats` | Hele filtreet kontrollert. README beskriver spiller-/kampfiler, men ingen `players_match_stats`-filer finnes i det kontrollerte treet. Lagets `events_stats` er aggregerte lag-/kamptellinger. |
| `Akshat29-shah/epl-analysis` | Faktisk hendelsesfil kontrollert: kamp, hjemme/borte, minutt og hendelsestype. Ingen spiller-ID eller storsjansekvalifikator i den kontrollerte filen. |
| Opta Analyst / Perform | Offentlig side og klientkode tilgjengelig; én kalenderforespørsel til datatjenesten ga HTTP 403. Stoppet uten alternative headere, proxyer eller andre omgåelser. |
| Publisert bonusomregning på Reddit / fpl.red | Forfatteren presiserer at storsjanseredningene er anslått fra xG. Den er derfor ikke en eksakt kilde til dette feltet. |
| Åpne datasettoversikter og en nyere forskningsartikkel | Fant beskrivelser av relevante hendelsesdata, men ingen verifisert nedlastbar eksport som dekker de nødvendige sesongene og feltene. |

Detaljer og kildehenvisninger: `source_checks.json`.

## Hva dette løser – og hva som fortsatt stopper fullføringen

Den operative innhentingen kan nå kjøres i avgrensede, gjenopptakbare bolker. Det gjør det mulig å fylle de tilgjengelige primære BPS-feltene uten å miste hele jobben ved avbrudd. Offisielle tilbakevirkende assistavgjørelser kan inngå som dokumenterte tillegg; fire er nå klare.

En full eksakt 2026/27-fasit krever fortsatt kampvise historiske storsjanseredninger og flere dokumenterte assistavgjørelser/hendelser. Verken xG-terskler, sesongtotaler fordelt på kamper eller manglende verdier satt til null oppfyller det kravet. Mer masseinnhenting fra samme feltfattige endepunkt løser ikke alene disse to manglene. `../results/readiness.json` beholdes sperret.
