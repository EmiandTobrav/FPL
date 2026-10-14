# Arbeidsflyt for forbedring av FPL modellen

Hver ny runde skal bygge på et kjent datagrunnlag, en tydelig hypotese og resultater fra tidligere forsøk. [Prosjektregisteret](PROJECT.json) angir data, pipeline og benchmark. [Arbeidsstatus](STATUS.md) og [forsøksregisteret](research_catalog.json) viser hva som allerede er gjort.

[Arbeidshistorikken](TIMELINE.md) viser hendelsene underveis, inkludert feil, endringer og stopp. Fullstendige detaljer beholdes i den opprinnelige kampanjeloggen.

## Før et nytt forsøk

1. Les [neste steg](NEXT.md) og den nyeste kildestatusen. Avklar om et tilsvarende forsøk allerede er registrert eller pågående. Et gammelt prosessnummer eller en lock-fil beviser ikke at arbeid kjører eller har stoppet.
2. Søk etter metodefamilie, kandidatnavn og mekanisme i registeret. Les resultatet og konklusjonen fra treffene. Kontroller også [eldre metodefamilier](METHODS.md) og den eksisterende kampanjeloggen; katalogen er et sammendrag, ikke en full kopi av alle arbeidsnotater.
3. Skriv én hypotese: hva skal forbedres, hvilken mekanisme forventes å gi gevinst, og hva skiller forsøket fra tidligere arbeid? Et nytt navn alene er ingen ny hypotese. Et uendret mislykket forsøk trenger en konkret grunn for ny kjøring, som korrigerte data eller dokumentert reproduksjonsbehov.
4. Bind forsøket til faktiske inputfiler med SHA256, inkludert datasettmanifest, featuretabell, pipelinekode og relevant modell-/policykode. Angi sesonger, tidsregel, benchmark, ressursbudsjett, maksimalt antall kjøringer, suksesskriterium og stoppregel før resultatene leses.
5. Registrer forsøket. Registrering starter ingen trening og overstyrer ikke en eksisterende kampanjes begrensninger eller låste protokoll. Nye forsøk må passe innenfor kampanjens vedtatte rammer.

## Kjør fra eksisterende utgangspunkt

Bruk eksisterende innleser og pipeline. Unngå en ny full datakopi per forsøk. Frys filhashene som skal gjenbrukes, og lagre bare nye prognoser, beslutninger, resultatfiler og nødvendige kontrollspor i forsøksområdet.

Velg den minste kontrollen som kan avvise hypotesen tidlig. Først kontrolleres input, tidstilgjengelighet og en liten prognose-/policyprøve. Kjør full sesong først når prøven og den relevante protokollen tillater det. Behold negative poeng, manglende utfall og kvalitetsflagg i henhold til datakontrakten.

Primærmålet er netto sesongpoeng etter overgangskostnader. RMSE og MAE hjelper til å forklare prognoseendringen. Sammenlign kandidaten med benchmark på identiske sesonger, mål, starttilstand, informasjon, chip-/beslutningspolicy og ressurser. Hvis policyen er selve intervensjonen, dokumenteres dette eksplisitt og sammenligningen tolkes som en systemsammenligning.

## Avslutt og lær

Resultatkortet skal inneholde poeng per sesong, benchmarkens poeng, forskjeller, relevant ressursbruk og kontrollstatus. Koble hver påstand til resultatfil og filhash. Skill mellom observert forbedring og bestått oppgraderingskrav.

Avslutt med én beslutning: forkast, behold som forskningskandidat, eller send til separat vurdering for oppgradering. Skriv hva forsøket lærte oss, hvorfor det ble stoppet, og hva som må endres før det er verdt å gjenta. Negative resultater beholdes og er søkbare.

En positiv enkeltkjøring endrer ikke automatisk benchmark eller produksjonsmodell. Oppdater prosjektregisteret først etter en dokumentert vurdering. Arkiver gamle filer når en minimal utgivelse og nødvendig etterkontroll er verifisert.

## Praktiske verktøy

Alle kommandoer kjøres fra hovedmappen. De starter ingen modellarbeidere.

```sh
python3 scripts/research.py status
python3 scripts/research.py search "spilletid"
python3 scripts/research.py refresh
```

`status` leser gjeldende lagret kampanjestatus direkte. `search` søker i arbeidstrinn, funn og lokale forslag. `refresh` oppdaterer den lesbare oversikten. For søk på tekniske modellnavn kan for eksempel `minutes`, `fixture` og `horizon` brukes.

Bruk [forsøksmalen](EXPERIMENT_TEMPLATE.json) til et nytt forslag. Fyll alle felt og oppgi ID-er fra katalogen i `related_work`. Egen versjon av en kandidat må forklare en faktisk endring. Et tomt forslag blir avvist.

```sh
python3 scripts/research.py check /absolutt/sti/til/forslag.json
python3 scripts/research.py register /absolutt/sti/til/forslag.json
```

Kontrollen verifiserer filhashene, aktiv dataversjon, benchmark, referanser til tidligere arbeid og at kandidat-ID og forsøkskontrakt ikke allerede er registrert. Nye forslag lagres separat under `experiments/`. Originale kampanjeregistre og fryste resultater overskrives ikke. Kontroll av byte-identitet dekker nye lokale registreringer; eldre forsøk sammenlignes også gjennom kandidat-ID og manuell gjennomgang av relatert arbeid.

Bruk [resultatmalen](RESULT_TEMPLATE.json) ved avslutning. `decision` skal være `reject`, `retain_for_research` eller `promote_to_review`. `results` må inneholde de konkrete resultatene, og `evidence_hashes` må binde eksisterende resultatfiler.

```sh
python3 scripts/research.py complete FORSØKS_ID /absolutt/sti/til/resultat.json
```

Resultatet lagres separat med eksklusiv oppretting, så en tidligere registrering eller konklusjon ikke overskrives. Korrigeringer registreres som en ny eksplisitt versjon og lenkes til det opprinnelige forsøket. Ved parallelt arbeid deles hypoteser og ansvar før kjøring; verktøyet reserverer bare registreringer og styrer ikke arbeidere eller prosesser.
