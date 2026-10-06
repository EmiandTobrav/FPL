# Historiske kampkalendere: datagrunnlag og revisjon

Undersøkt 6. oktober 2026. **82 arkivversjoner dekker 136 beslutningstidspunkter** i 2022/23–2025/26. Dette er kalenderen slik den forelå i et tidligere Git-arkiv, ikke sluttkalenderen gitt til modellen på forhånd.

## Kilde og utvalg

Kilden er [Vaastav/Fantasy-Premier-League](https://github.com/vaastav/Fantasy-Premier-League). `source_commits.json` registrerer alle filendringer som GitHub returnerte for sesongenes `fixtures.csv`: 38, 38, 37 og 12. Ingen liste nådde sidegrensen på 100. `downloads.json` gir82 eksakte commit-bundne kilde-URL-er. `SOURCE_LICENSE.txt` beholder kildeprosjektets lisens og datarettighetsmerknad.

For hver arvet benchmarkfrist velges siste commit hvor både author- og committer-tid ligger strengt før fristen. Commit-tid er en praktisk proxy for arkivets tilgjengelighet, ikke uavhengig attestasjon av første offentlige publisering. Det er heller ikke tidspunktet nyheten først ble kjent i fotballverdenen.

Alle uttrekk inneholder 380 unike kamper, 20 lag og 38 opptredener per lag. Modellen får bare `id,event,kickoff_time,team_h,team_a,provisional_start_time`. Kampresultater, statistikk og FDR-kolonner inngår ikke i de lagrede modelluttrekkene. Ukjent `event` beholdes ukjent.

## Dekning

| Sesong | Brukte arkivversjoner | Median alder | Maksimal alder | Beslutningsrunder med alder ≤14 dager |
|---|---:|---:|---:|---:|
| 2022/23 | 27 | 3,60 dager | 36,15 dager | 31/34 |
| 2023/24 | 24 | 3,59 dager | 14,19 dager | 33/34 |
| 2024/25 | 24 | 5,74 dager | 16,91 dager | 33/34 |
| 2025/26 | 7 | 32,16 dager | 96,33 dager | 8/34 |

De82 versjonene omfatter enkelte identiske kalenderuttrekk: kildefilen kan ha blitt endret bare fordi kampresultater/statistikk ble oppdatert.

Blant4060 fremtidige lag/runde-celler dekket av arkiv≤14 dager har 200 et planlagt kampantall ulikt én. I 98 celler er kampantallet forskjellig fra sluttkalenderen. Dette er gjentatte planleggingsobservasjoner, ikke98 unike kampflyttinger. Avviket kan skyldes nye annonseringer etter arkivet og/eller etter beslutningsfristen; sluttkalenderen brukes kun til denne revisjonen.

Randdalf/fplcache ble også undersøkt. Prosjektets README og `cache.py` beskriver fire daglige arkiver av **bootstrap-static**, ikke et arkiv av fixtures-endepunktet. Det er en mulig kilde til frister/tilgjengelighet, men vi har ikke brukt det som om det inneholdt hele kampkalenderen.

## Viktig begrensning i eksisterende benchmark

Benchmarkens nåværende rundeprognoser og beslutningstidspunkter bygger fortsatt på eksisterende historiske proxyer. Den opprinnelige `research.load_data` bruker endelig GW-tilordning og en cutoff 36 timer før første kamp. Vi har beholdt dette i den første sammenligningstesten for å isolere endringen i fremtidig kalender.

Selv innen ferske arkiver finner revisjonen 22, 2, 4 og 0 lag/runde-celler for **aktuell** runde med kampantall forskjellig fra sluttkalenderen. Dette viser at en full rekonstruksjon må behandle både faktisk frist, aktuell kampkalender og senere utsettelser. Antall avvik er ikke alene et bevis på når endringen ble offentlig kjent. Første kalenderforsøk reparerer ikke hele dette problemet.

## Lesbar lagring og reproduksjon

Automatisk godkjenningskontroll avviste en opplasting av ugjennomsiktig komprimert innhold. Kalenderuttrekk og simuleringsspor publiseres derfor som **lesbar CSV/JSON** i `portable`, med hashregister i `portable_manifest.json`. De inneholder kontrollerte offentlige kalenderfelt og modellgenererte simuleringsdata.

`python scripts/prepare_data.py` kjører `restore.py`, som verifiserer og gjenoppretter de 98 komprimerte filene koden forventer. Det kreves ingen manuell ZIP-utpakking eller nye nettverksnedlastinger. Alle 98 gjenopprettinger er kontrollert byte for byte i det registrerte Python 3.12.14/zlib-miljøet. Ved en annen komprimeringsimplementasjon feiler verifikasjonen eksplisitt fremfor å godta endrede arkivbytes.

`selector.py` gjenskaper utvalget. `audit.py` gjenskaper dekning og avvik fra de gjenopprettede kalenderne; sammenligning med sluttkalenderen holdes atskilt fra modellens `build.py`.

[Resultat av første test: bare antall kommende kamper](../calendar_counts/README.md).
