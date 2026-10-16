# Hvor ligger arbeidet?

[Startside](../README.md) · [Resultater](RESULTS_INDEX.md) · [Neste oppgaver](ROADMAP.md)

Kontrollert mot GitHub 16. oktober 2026. Statusen er et datert bilde; sjekk lenket PR før grenvalg.

| Inngang | Innhold | Publiseringsstatus |
|---|---|---|
| `main` | Eldre kode, historiske metoder og datakilder | Sammenslått grunnlag; ikke hele det lokale prosjektet |
| [PR #1](https://github.com/EmiandTobrav/FPL/pull/1) | Kildeautoritet og historiske poenginput | Åpent utkast mot main; beskriver et tidligere rekonstruksjonstrinn |
| [PR #2](https://github.com/EmiandTobrav/FPL/pull/2) | Portable datasett, forskningsregister, Model Lab, TC/BB-pilot | Åpen mot main; gren `codex/research-workspace-overview` |
| [PR #3](https://github.com/EmiandTobrav/FPL/pull/3) | Episodisk manager og kontroller | Åpen mot #2-grenen; `codex/episodic-manager-policy` |
| [PR #4](https://github.com/EmiandTobrav/FPL/pull/4) | H2-planlegging uten reservekostnad | Åpen mot #3-grenen; `codex/explicit-chip-planning` |
| [Rapportutdrag 16. oktober](evidence/2026-10-16/MANIFEST.json) | Utvalgte nyere forsøksrapporter, byteidentiske kopier | Rapportene publiseres her; input, kode og komplette bevis er fortsatt i lokalt arbeidsarkiv |

#2 → #3 → #4 er en kjede. Dokumentasjonsoppdateringen er separat mot main. Ved sammenslåing må README-konflikter løses slik at denne korte inngangen beholdes og de nye lokale lenkene kobles på. Ikke slå sammen hele kjeden bare for å få dokumentasjonen synlig.

## Navigasjon i en klone

- `docs/RESULTS_INDEX.md`: lesbar oversikt og beslutninger.
- `research/current/`: historiske protokoller, resultater og kildearbeid; behold fryste filer.
- `src/`, `tests/`, `scripts/prepare_data.py`: eldre kode og klargjøring.
- `datasets/`, `model_lab/`, `overview/`: finnes i #2 og påfølgende grener, ikke i dette main-grunnlaget. Les `docs/GIT_LAYOUT.md` på valgt gren før kjøring.
- `docs/evidence/2026-10-16/`: daterte rapportkopier. Interne filnavn i rapportene refererer til originalt forsøksområde, ikke nødvendigvis filer i Git.

Et sammendrag eller en bestått kodekontroll betyr ikke at hele forsøket kan gjenskapes fra denne klonen. Rapportene oppgir tidligere utførte kontroller; dokumentasjonsarbeidet kjører ikke modellforsøkene på nytt.
