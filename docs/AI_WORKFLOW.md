# Slik arbeider jeg med KI-agenter

[Startside](../README.md) · [Eksempler](CASE_STUDIES.md) · [Teknisk arbeidsflyt](../overview/WORKFLOW.md)

Jeg bruker KI til Python-utvikling. Min rolle er å gjøre et åpent problem om til avgrensede oppgaver med tydelige krav, koordinere arbeidet, utfordre forslag og evaluere resultatene. Agentene utfører kodeimplementering, kildearbeid, tester og analyser innenfor disse rammene. Dette er ikke en påstand om at jeg har skrevet all koden selv eller manuelt kontrollert hver beregning.

## Rollefordeling

| Rolle | Ansvar | Leveranse som kan vurderes |
|---|---|---|
| Jeg som prosjekteier | Mål, prioritering, krav, rammer, korrigering av retning og vurdering av resultat | Avgrenset problem, akseptkriterier og beslutning om videre arbeid |
| Koordinerende agent | Dele opp arbeidet, følge avhengigheter og samle leveranser innen avtalte rammer | Arbeidsfordeling, status, samlet forslag og åpne spørsmål |
| Implementerings-/analyseagent | Utvikle kode, gjennomføre avgrenset forsøk og bevare bevis | Kode, tester, protokoll, målinger og begrensninger |
| Kontrollagent og kontrollkode | Prøve å avdekke feil i data, tidstilgjengelighet, sammenligning og utfall | Konkrete funn, kontrollkvitteringer og korrigeringsbehov |

En ekstra agentvurdering er ikke en garanti for korrekthet. Maskinelle kontroller, kildebevis og eksplisitte begrensninger må støtte konklusjonen. Når etterkontrollen gjenbruker simulatorens regelmotor, er den heller ikke en ekstern validering av reglene.

## Fra idé til etterprøvbar beslutning

1. **Formuler problemet.** «Bedre prognoser» og «bedre lagvalg» er ulike mål. Prognosefeil måles separat; manageren vurderes på netto sesongpoeng etter overgangskostnader.
2. **Les tidligere arbeid.** Søk etter samme mekanisme og negative funn før et nytt forsøk. Et nytt kandidatnavn er ikke en ny hypotese.
3. **Spesifiser før kjøring.** Lås dataversjon og filhash, kandidat, kontroll, sesonger, informasjonstid, målemetode, ressursgrense, suksesskrav og stoppregel. [Forsøksmalen](../overview/EXPERIMENT_TEMPLATE.json) gjør kravene konkrete.
4. **Deleger avgrenset.** Avklar eier, input, tillatte endringer, leveranse og ferdigkriterier. Parallelle oppgaver må ha adskilt ansvar. Koordinatoren samler resultater; arbeiderne skal ikke konkurrere om å endre samme fasit.
5. **Kontroller før utvidelse.** Kontroller input og tidsregler, kjør en liten funksjonsprøve og utvid bare innen den låste kontrakten. Registrering gir ikke automatisk klarsignal til en ny stor kjøring.
6. **Evaluer mot samme kontroll.** Hold data, sesonger, prognoser og ressurser like når de ikke er det forsøket skal endre. Lagre beslutninger før utfall leses. Skill teknisk feil fra et faglig negativt resultat.
7. **Ta en eksplisitt beslutning.** Forkast, behold som forskningskandidat eller send til separat oppgraderingsvurdering. Bevar negative funn, feil og rettinger; ikke skriv om historikken etter resultatet.

Registeret i [scripts/research.py](../scripts/research.py) binder kontrakter og resultatbevis. Det er ikke et system som selv starter eller overvåker agentarbeidere. [Issue-malen](../.github/ISSUE_TEMPLATE/experiment.md) og [bidragsguiden](../CONTRIBUTING.md) gir samme struktur ved samarbeid.

## Hva historikken faktisk viser

Den publiserte [arbeidshistorikken fra 14. oktober](../overview/TIMELINE.md) viser låsing av protokoll før kjøring, separate forhåndskontroller, bevarte kontrollfeil og kandidater som stoppes når kravene ikke oppfylles. Hendelsene viser arbeidsprosessen; de gir ikke grunnlag for å tilskrive hver teknisk handling til meg personlig.

Et lokalt arbeidsnotat fra dataklargjøringen dokumenterer også hvordan agentstrukturen ble endret: fra flere ledelseslag til én koordinator/skriver og inntil fire avgrensede arbeidere. Oppgavene hadde eierskap, adskilte køer og gjenbruk av kildebevis. Overlevering krevde kontrollert avslutning av tidligere arbeidere før ny skriver overtok. Dette illustrerer styring og korrigering av arbeidsformen. Det foreligger ikke her dokumentert kostnads- eller hastighetsgevinst.

Denne siste beskrivelsen er et sammendrag av **lokal historikk**, ikke en publisert agentlogg. Kilden er `FPL_training_dataset/docs/AGENTIC_DATA_WORK.md` i det separate arbeidsarkivet; den følger ikke med denne klonen. Interne chatidentifikatorer og fulle kildearkiver er utelatt. Se [publiseringsomfang](PUBLICATION_SCOPE.md).

## Eksempel på en oppgavespesifikasjon

Følgende er en lesbar oppsummering av det gjennomførte chip-forsøket, ikke en gjengivelse av en original prompt:

> Undersøk om læring av verdien av å spare Triple Captain og Bench Boost kan gi flere netto sesongpoeng. Behold prognoser, regelmotor og ressursgrenser. Tren bare på tidligere sesonger og frys modellen før evalueringsåret. Rapporter kandidat og kontroll per sesong, kontroller handlinger og oppgjør, og vurder resultatet mot den låste protokollen. En bestått pilot endrer ikke benchmark automatisk.

[Protokollen](../reports/learned_manager_2026_10_15/protocol.json) og [resultatrapporten](../reports/learned_manager_2026_10_15/RESULTATER.md) viser den faktiske kontrakten og utfallet. [De tre eksemplene](CASE_STUDIES.md) viser hvordan samme arbeidsform også fører til at lovende forslag forkastes.
