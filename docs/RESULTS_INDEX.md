# Hva er testet, og hva lærte vi?

[Startside](../README.md) · [Publiseringskart](REPOSITORY_MAP.md) · [Neste oppgaver](ROADMAP.md)

Datert oversikt: 16. oktober 2026. Tabellen er et utvalg av sentrale funn. Hver lenket rapport er autoritativ for sin egen kontrakt. Ulike poengmål, kontroller, sesonger og chips gjør at radene **ikke er en felles rangering**.

## Historisk metodegrunnlag — i main

| Forsøk | Resultat og læring | Beslutning / kilde |
|---|---|---|
| Kampjustering, H3 og adaptiv TC | Historisk benchmark: 2351,50 poeng i snitt over 2022/23–2025/26; eldre poengmål | [Benchmark og metode](../research/current/fixture_strategy/README.md) |
| Retrening og blandinger | Extra Trees +37,2 med chips, −39,0 uten mot daværende referanse. Gevinsten avhenger av kontrakten | [Utfordrer, ingen automatisk oppgradering](../research/current/retrained_ensemble/README.md) |
| Global HGB-vekt og H3 | +70 med chips mot daværende referanse; bare +15,75 mot egen H1, med usikkert intervall | [Behold som forskningskandidat](../research/current/global_horizon/README.md) |
| Posisjonsspesialisering | Ingen kandidat slo primærbenchmark med chips | [Ingen oppgradering](../research/current/position_specialist/README.md) |

Flere historiske metoder og rapporter: [tidligere prosjektinngang](PROJECT_ENTRY_2026_10_07.md).

## Nyere managerforsøk — publisert i åpne PR-er

| Forsøk | Resultat | Beslutning / kilde |
|---|---|---|
| Lært TC/BB-policy | +53 / +41 poeng, snitt +47 mot benchmark i to sesonger | Avgrenset pilot, ikke generell managergevinst. [PR #2](https://github.com/EmiandTobrav/FPL/pull/2) |
| Episodisk manager, alle chips | −243 i sesongsnitt mot benchmark; −297,5 mot samme forslag uten læring | Forkastet som oppgradering. [PR #3](https://github.com/EmiandTobrav/FPL/pull/3) |
| H2 uten reservekostnad | −37 / −65 / −106 mot samme planner med reserve; −55,7 i snitt mot historisk benchmark | Forkastet. [PR #4](https://github.com/EmiandTobrav/FPL/pull/4) |

## Prognoseforsøk — rapportkopier fra 16. oktober

Prosentene gjelder endring i prognosefeil, ikke sesongpoeng. «Kandidater» er en fast liste av aktuelle lagspillere. MSE er gjennomsnittlig kvadratfeil; lavere er bedre. Historisk periode er allerede undersøkt, og GW1–6 er en retrospektiv pilot.

| Forsøk | Resultat | Beslutning og rapport |
|---|---|---|
| Kampkontekst, faste minutter | MSE redusert 1,604 % totalt og 3,288 % blant kandidater i 2025/26 | [Beholdt som forskningskandidat](evidence/2026-10-16/point_context.md); ingen manageroppgradering |
| Fryst pakke, GW1–6 | MSE redusert 0,27 % totalt og 0,07 % blant kandidater; svært liten effekt | [Pilot består; GW7 lagret](evidence/2026-10-16/temporal_2026_27.md). Prospektiv blokk ikke ferdig |
| Dempet styrkekorreksjon | Kandidat-MSE bedre 0,033 % historisk, verre 0,078 % i piloten | [Ikke bestått](evidence/2026-10-16/strength_attenuation.md) |
| Motstanderstyrkeablasjon | Ingen av tre varianter består alle MSE-krav | [Ikke bestått](evidence/2026-10-16/opponent_strength_ablation.md) |
| Feltutelatelse bare for spisser | Kandidat-MSE bedre i begge perioder, men total pilot-MSE verre 0,0385 % | [3 av 4 krav; ikke bestått](evidence/2026-10-16/forward_only_ablation.md) |
| Start/innhopp/fravær-modell | Kandidat-minutt-MSE verre 0,150 % historisk og 0,495 % i pilot | [2 av 12 krav; ikke bestått](evidence/2026-10-16/role_model.md) |

## Managerens sluttverdi — rapportkopier fra 16. oktober

Alle tre sammenlignes med A, samme H3-rollout og faste prognoser, i 2023/24 og 2024/25. Tallene er forskjell i netto sesongpoeng, i denne rekkefølgen.

| Forsøk | Resultat mot A | Beslutning og rapport |
|---|---|---|
| B: lært sluttverdi | −76 / −49 | [Forkastet](evidence/2026-10-16/terminal_value.md) |
| B2: parvis sluttverdi | +19 / −89; snitt −35 | [Forkastet](evidence/2026-10-16/paired_terminal.md) |
| B3: fast tropp H4–H8 | −38 / +44; snitt +3 | [Begge-år-kravet feiler](evidence/2026-10-16/hold_tail.md); dette er ikke full H8-planlegging |

Rapportkopiene er bevart byte for byte med [kildebaner og SHA-256](evidence/2026-10-16/MANIFEST.json). Filreferanser inne i rapportene peker til originalt arbeidsområde. Disse kopiene dokumenterer funn og tidligere kontroller, men inneholder ikke alle input eller en kjørbar utgivelse. Ingen modellresultater er kjørt på nytt som del av dokumentasjonsendringen.

## Legg til et resultat

Legg raden i riktig forsøksfamilie. Oppgi kontroll, periode, metrikk, faktisk forskjell, bestått/ikke bestått og rapportlenke. Behold negative funn. Ved ny korrigering: lenk til opprinnelig versjon og forklar hva som er endret.
