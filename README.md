# FPL — data, prognoser og managerbeslutninger

Vi utvikler og tester en FPL-manager med historiske data, tidsriktige prognoser og lovlige lagvalg. Målet er flere **netto sesongpoeng etter overgangskostnader**. Prognoseforsøk måles separat før eventuell testing i manageren.

## Start her

| Jeg vil … | Gå til |
|---|---|
| Forstå prosjektet og komme i gang | [Bidragsguide](CONTRIBUTING.md) |
| Se hva som er gjort og hva vi lærte | [Resultatoversikt](docs/RESULTS_INDEX.md) |
| Finne riktig gren og publisert materiale | [GitHub-kart](docs/REPOSITORY_MAP.md) |
| Velge neste oppgave | [Prioriteringer](docs/ROADMAP.md) |
| Se eldre forsøk i denne grenen | [Historisk prosjektinngang](docs/PROJECT_ENTRY_2026_10_07.md) |

## Hvor står vi?

**Statusbilde: 16. oktober 2026.** `main` samler den historiske forskningsbasen, nyere datasett, Model Lab og de publiserte managerforsøkene. Resultater fra 16. oktober er her publisert som rapportkopier med kildehash; komplette kjørbare pakker følger ikke med denne dokumentasjonsoppdateringen.

- Ingen ny produksjonsmanager er godkjent. Positive enkelttall er ikke automatisk en oppgradering.
- Den historiske benchmarken er `fixture_full_h3_adaptive_tc`. Nyere forsøk bruker den omregnede familien `fixture_full_h3_adaptive_tc_harmonized_causal_v1`; poeng fra de to grunnlagene skal ikke rangeres sammen.
- Den fryste prognosepakken `forecast-package-20261016-v1` er et separat forskningsspor. GW1–6 er retrospektivt evaluert; GW7-prognosene er lagret for senere vurdering. Se [resultater og forbehold](docs/RESULTS_INDEX.md).

## Slik holder vi orden

Én hypotese og én ansvarlig per oppgave. Lås kontroll, data, mål og suksesskrav før kjøring. Publiser også negative resultater, og lenk fra resultatoversikten til rapport og bevis. Bruk [bidragsguiden](CONTRIBUTING.md) og repoets issue-/PR-maler.

Gamle rapporter beskriver tidspunktet de ble skrevet. Mappenavnet `research/current` betyr ikke at alt der fortsatt er aktivt. Gjeldende data og metodekontrakter finnes i [prosjektregisteret](overview/PROJECT.json), og kjøreoppskrifter i [Model Lab](model_lab/README.md). [GitHub-kartet](docs/REPOSITORY_MAP.md) skiller sammenslått kode, åpne forslag og rapporter uten full replaypakke.
