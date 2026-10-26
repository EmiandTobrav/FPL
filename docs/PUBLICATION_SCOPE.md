# Hva finnes på GitHub, og hva er lokalt?

**Oppdatert 26. oktober 2026:** [Utvidede datasett, korrigert kalender og valgt komponentmodell med fem runders planlegging](../releases/2026-10-26/README.md). Historisk gevinst +104 / −13 / +37 mot samme-kalender-kontroll. Selve observasjons- og modelltabellene følger med; full live-/modellreplay krever fortsatt arbeidsarkivet. Eldre daterte statusavsnitt nedenfor gjelder sitt opprinnelige tidspunkt.

[Startside](../README.md) · [Demo](QUICKSTART.md) · [Detaljert Git-struktur](GIT_LAYOUT.md)

Kontrollert 22. oktober 2026 mot offentlig `EmiandTobrav/FPL`, main-commit `db1a9e7dbeefb22aa310747cb3064e9c5e4ecf71`. Den lokale arbeidskopien som ble brukt til presentasjonen hadde samme Git-tre som main. Presentasjonsendringene må godkjennes før publisering.

## Hva en utenforstående kan etterprøve

| Materiale | I publisert main ved kontrollen? | Mulig kontroll fra repoet |
|---|---|---|
| Historisk kode, tekniske rapporter og tidligere PR-er | Ja | Lese metode, kode og historikk; eldre kjøring har egen oppskrift |
| Rekonstruert datasett, featuregrunnlag og modellpipeline | Ja | Lese datakort og kjøre den avgrensede prognosedemoen |
| Model Lab og liten simuleringspakke | Ja | Kjøre demoer og tester uten privat arkiv |
| Chip-policy, episodisk manager og H2-planlegging fra 15. oktober | Kode og utvalgte input/resultatbevis, inkludert komprimerte logger | Kontrollere publiserte hasher; full replay trenger separate lokale input |
| Utvalgte prognose-/sluttverdirapporter fra 16. oktober | Rapportkopier og kildemanifest | Lese funn og kontrollere rapportidentitet; ikke full reproduksjon |
| Full rekonstruksjonskø, kildearkiv og detaljert agenthistorikk | Ikke samlet i denne utgaven | Lokale kilder kan ikke åpnes fra klonen |
| Senere kalibrerings- og overtakelsesforsøk fra 17. oktober i lokalt arkiv | Ikke i dette Git-treet | Ikke brukt som publiserte resultatbevis i de tre eksemplene |

«Publisert» betyr her at filen ligger i repoet, ikke at alle underliggende kilder er uavhengig kvalifisert. «Fullført» i en statusfil betyr heller ikke at alle nødvendige replay-input er inkludert.

## Det større lokale prosjektet

Kartleggingen omfattet alle toppnivåmapper: de to eldre checkoutene `FPL/` og `FPL_training_dataset/`, publiseringskopien `repo-onboarding/`, samt `datasets/`, `experiments/`, `model_lab/`, `lab_results/`, `overview/`, `reports/`, `research/`, `scripts/` og `sources/`. Struktur og filomfang ble inventert; relevante inngangsdokumenter, kontrakter, rapporter, kode og registre ble lest. Dette er ikke en påstand om manuell gjennomlesning av hver rådatafil eller full faglig revisjon av alle forsøk.

Lokalt finnes mer detaljert kildearbeid, agentkoordinering, cache, prognoser og videre eksperimenter enn på GitHub. Sammendraget av agentorganisering i [arbeidsmetodikken](AI_WORKFLOW.md) bygger blant annet på det lokale dokumentet `FPL_training_dataset/docs/AGENTIC_DATA_WORK.md`. Det dokumentet er ikke kopiert hit. Interne chatidentifikatorer, store arbeidsdatasett og fullstendige kildesamlinger inngår ikke i presentasjonsendringen.

De eksisterende rapportkopiene har [manifest med kildebaner og SHA-256](evidence/2026-10-16/MANIFEST.json). Originale lokale rapporter og disse kopiene ble sammenlignet ved gjennomgangen; alle ni rapportkopiene samsvarte med manifestet og den lokale kilden. Filhenvisninger inne i fryste rapporter kan peke utenfor denne klonen. Slike historiske referanser er bevart, ikke omskrevet til tilsynelatende kjørbare oppskrifter. Lenkeinventaret fant ni slike manglende mål: `protocol.json`, `audit.json` og `rounds.csv` i hver av rapportkopiene `terminal_value.md`, `paired_terminal.md` og `hold_tail.md`. De nye navigasjonsdokumentene lenker bare til eksisterende filer.

## Tilgjengelighet og begrensninger

Repoet er offentlig og kan leses uten innlogging. About-beskrivelse og topics var tomme ved kontrollen. [Demooppskriften](QUICKSTART.md) er prøvd med filer fra Git alene; full gjentakelse av avanserte forskningsforsøk krever fortsatt lokalt arkiv.

Ingen lisens var registrert i repoet ved kontrollen. Offentlig innsyn er derfor ikke det samme som en eksplisitt tillatelse til viderebruk. Lisensvalg og rettigheter til tredjepartsdata må avklares separat; denne dokumentasjonsendringen innfører ingen ny lisens.

Eldre statusdokumenter og rapporter er tidsbilder. Bruk de daterte originalrapportene for hver kontrakt, [resultatoversikten](RESULTS_INDEX.md) for navigasjon og [GitHub-kartet](REPOSITORY_MAP.md) for publiseringshistorikk.
