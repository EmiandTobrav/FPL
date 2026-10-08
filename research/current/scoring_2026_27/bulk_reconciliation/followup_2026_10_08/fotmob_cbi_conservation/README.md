# CBI-komponenter V1: kontrollen feiler, ingen verdier anvendt

Fryst 8. oktober 2026. De 341 manglende CBI-verdiene gjelder alle keepere.
V1 prøvde en generell CBI-mapping med klareringer, shot_blocks og interceptions,
med eksplisitte spillerverdier og eksakt avstemming mot lagtotaler.
329 berørte kamper og fem ikke-berørte kontrollkamper per sesong 2019/20–2025/26
ble valgt før kontrollsammenligning. 50 tidligere råsvar ble gjenbrukt; 314 nye
public FotMob-svar ble hentet. Alle 364 råsvar og bytehash er bevart.

**Ingen krav er lukket, og gjeldende ledger er uendret av denne studien.**
De opprinnelige null-avvik-gatene feiler på ni kontrollsammenligninger:

- I Liverpool–Norwich 2019/20 fixture1 oppgir FotMob null blokker for begge lag.
  Primærdata har to og tre, fordelt over fem spillere. Det gir sju avvik.
- I Forest–Brentford 2025/26 fixture4 har Kevin Schade og Michael Kayode hver
  én mindre CBI i FotMob-projeksjonen enn i autoritativ FPL. Begge er utespillere.
- Den gamle primærkomponentprojeksjonen dekker ikke 2025/26; V1s krav om slike
  primærkomponentkontroller i denne sesongen kan heller ikke oppfylles derfra.

Kontrollene har dermed ikke kvalifisert en generell mapping. Samlet sammenligning
av kontroller og aktuelle kamper har 86 avvik. Terskler, native FPL-verdier,
kjente konflikter og tidligere rekonstruksjoner er bevart. Ingen fortolkning av
utelatte komponenter som null eller masseanvendelse er godkjent.

Et nytt spor må dekke den faktiske målpopulasjonen, alle 341 keeperrader, og ha
nye, fryste kontrollkrav som passer tilgjengelige primærkilder. Gjenbruk disse
råsvarene; ikke gjenta innhentingen eller V1s generelle validering. Eksakte
primære komponentgrenser kan brukes der de er kvalifisert. Kildeuenighet må
beholdes; en utelatt primærtotal er ikke null.

[Protokoll](protocol.json), [plan](plan.csv), [råsvarmanifest](inputs/source_manifest.csv),
[komponentkontroller](results/source_comparisons.csv),
[kontrollstatus per sesong](results/source_quality_by_season.csv),
[funn](results/findings.json) og [offline-reproduksjon](reproduction_verification.json)
dokumenterer det mislykkede forsøket. Resultat-ledgeren er et uanvendt
kontrollsnapshot og er ikke dagens restliste.

```bash
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/fotmob_cbi_conservation/reproduce.py
```

Tolv resultater, inklusive de mislykkede utfallene, gjenskapes byteidentisk i
separat kopi uten nettverk.
