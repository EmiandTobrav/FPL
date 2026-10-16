# Bidra til FPL

[Startside](README.md) · [Resultater](docs/RESULTS_INDEX.md) · [Prioriteringer](docs/ROADMAP.md)

## Første økt

1. Les startsiden og resultatoversikten. Velg data-, prognose- eller managersporet.
2. Bruk [GitHub-kartet](docs/REPOSITORY_MAP.md) for å finne grenen som faktisk inneholder arbeidet. Main og lokalt arbeidsarkiv har ulikt innhold.
3. Velg én avgrenset oppgave og oppgi hvem som tar den. Bruk issue-malen; søk etter tidligere forsøk før ny kjøring.
4. Lag en egen gren fra avtalt grunnlag. Åpne en liten PR med resultat, kontroll og lenker til bevis.

## Kjøre den eldre kodebasens tester

Bruk Python 3.12 fra repoets rot. Disse kommandoene starter ikke en full modellstudie:

```sh
python -m venv .venv
source .venv/bin/activate
python -m pip install -r research/current/requirements_versions.txt pytest requests pyarrow
python scripts/prepare_data.py
PYTHONPATH=src OMP_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1 python -m pytest -q
```

På Windows aktiveres miljøet med `.venv\Scripts\Activate.ps1`; sett miljøvariablene med PowerShell-syntaks. Nyere Model Lab har egen oppskrift i [model_lab/README.md](model_lab/README.md). Følg forsøkskontrakten ved replay og bevar de opprinnelige resultatfilene.

## Ett forsøk skal gi ett svar

Før kjøring: skriv hypotese, forskjell fra tidligere forsøk, dataversjon/hash, kontroll, sesonger, informasjonstid, målemetode, suksesskrav og ressursgrense. Skill mellom forbedring av prognoser og forbedring av managerens netto poeng. Bruk bare tidsordnet validering og historisk tilgjengelig informasjon.

Etter kjøring: oppgi kandidat og kontroll per sesong, forskjell, usikkerhet, kontroller, begrensninger og beslutning. Velg **forkast**, **behold som forskningskandidat** eller **send til oppgraderingsvurdering**. Ingen automatisk benchmarkendring. Negative funn skal være like lette å finne som positive.

## Hva oppdaterer vi i samme PR?

- Rapport med protokoll, resultat og bevislenker; oppgi hva som kreves for gjentakelse.
- Én rad eller lenke i `docs/RESULTS_INDEX.md` og eventuelt neste oppgave i `docs/ROADMAP.md`.
- På nyere forskningsgrener: oppdater også `overview/` gjennom deres dokumenterte arbeidsflyt.
- Relevante tester ved kodeendring. For rene dokumentasjonsendringer: kontroller lenker og faktapåstander.

Ikke overskriv fryste referanser, rådata eller gamle forsøksresultater. En korreksjon får ny versjon med forklaring. Unngå full datakopi per forsøk; publiser bare avtalte filer, og oppgi tydelig når full replay krever et separat arkiv.
