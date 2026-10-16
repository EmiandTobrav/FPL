# Hvor ligger arbeidet?

[Startside](../README.md) · [Resultater](RESULTS_INDEX.md) · [Neste oppgaver](ROADMAP.md)

Kontrollert mot GitHub 16. oktober 2026. Dette er oversikten for den samlede utgaven. PR-lenkene bevarer gjennomgang og historikk.

| Inngang | Innhold | Publiseringsstatus |
|---|---|---|
| `main` | Datasett, Model Lab, publiserte forsøk og navigasjon | Felles arbeidsgrunnlag; ikke hele det lokale prosjektet |
| [PR #1](https://github.com/EmiandTobrav/FPL/pull/1) | Kildeautoritet og historiske poenginput | Lukket historisk utkast; ikke innlemmet. Gren og kildehistorikk bevart |
| [PR #2](https://github.com/EmiandTobrav/FPL/pull/2) | Portable datasett, forskningsregister, Model Lab, TC/BB-pilot | Innlemmet; opprinnelig gren `codex/research-workspace-overview` |
| [PR #3](https://github.com/EmiandTobrav/FPL/pull/3) | Episodisk manager og kontroller | Innlemmet etter #2; negativt forsøksresultat bevart |
| [PR #4](https://github.com/EmiandTobrav/FPL/pull/4) | H2-planlegging uten reservekostnad | Innlemmet etter #3; negativt forsøksresultat bevart |
| [Rapportutdrag 16. oktober](evidence/2026-10-16/MANIFEST.json) | Utvalgte nyere forsøksrapporter, byteidentiske kopier | Rapportene publiseres her; input, kode og komplette bevis er fortsatt i lokalt arbeidsarkiv |

#2 → #3 → #4 var publiseringskjeden. Den er samlet med bidragsguiden fra #5. #1 gjelder eldre rekonstruksjonsarbeid og er bevart som historikk; den eldre CURRENT-statusen er ikke gjeninnført som gjeldende arbeidskø.

## Navigasjon i en klone

- `docs/RESULTS_INDEX.md`: lesbar oversikt og beslutninger.
- `research/current/`: historiske protokoller, resultater og kildearbeid; behold fryste filer.
- `src/`, `tests/`, `scripts/prepare_data.py`: eldre kode og klargjøring.
- `datasets/`, `model_lab/`, `overview/`: er del av main. Les `docs/GIT_LAYOUT.md` før kjøring.
- `docs/evidence/2026-10-16/`: daterte rapportkopier. Interne filnavn i rapportene refererer til originalt forsøksområde, ikke nødvendigvis filer i Git.

Et sammendrag eller en bestått kodekontroll betyr ikke at hele forsøket kan gjenskapes fra denne klonen. Rapportene oppgir tidligere utførte kontroller; dokumentasjonsarbeidet kjører ikke modellforsøkene på nytt.
