# Samlet avklaring av keeper-CBI

9. oktober 2026. Dette er det samlede fortsettelsespunktet for sporet.
**CBI-dataene er ikke ferdige:** alle 341 manglende keeperkrav står åpne.
Undersøkelsen av de innhentede kildene har nå en konkret, dokumentert
kildehindring. Gamle kildeprøver skal ikke startes på nytt uten nye kildefakta.
Brukeren har bekreftet at ingen annen kildetilgang er kjent.

Alle 341 manglende rader har komponentkandidater fra det tidligere forsøket.
334 oppfyller de historiske lag-/gruppekravene. Dette er potensielle verdier,
ikke kvalifiserte utfyllinger: hele native keepergaten feiler fortsatt.
204 CBI-konflikter gjelder utespillere og bevares separat.

## Hva som er ferdig undersøkt

- FotMob-ruten har 569 native keeperkontroller i 281 kamper, hvorav 392
  positive. Seks avvik feiler den opprinnelige null-feil-gaten. 388 kjente
  historiske kontroller samsvarer, men overstyrer ikke native FPL.
- Det innhentede Opta-spillerarkivet har samme klareringstall i alle seks
  tilfeller. I fem tilfeller overstiger klareringer alene native CBI.
  To eksisterende Premier League-primærresponser støtter arkivtallene;
  dette er samme kildelinje og gir ikke adgang til kildeavstemming ved flertall.
- ESPN-prøven feilet på første native veto, Donnarumma kamp 41. Den ble
  ikke masseinnhentet; det er ikke dokumentert at alle seks er testet der.
- Fem komplette native FPL-spillerhistorikker bekrefter alle seks gamle
  CBI-verdier. Eldre ukesuttrekk forklarer ingen av disse avvikene.
- Hendelsesarkivet er nå gjennomgått for hele den fryste kontrollpopulasjonen.
  Alle 479 567 hendelser i 281 kontrollkamper er bevart med kildefingeravtrykk.
  De seks avvikskampene har egne komplette hendelsesuttrekk.

En alternativ opptelling av hendelsestypene 11, 41 og 8 treffer tilfeldigvis
alle seks avvikene, men **feiler på 369 av de 569 keeperkontrollene**. Den
forkastes. Hypotesen ble oppdaget ved inspeksjon av de seks kjente avvikene;
kontrollen er diagnostikk, ikke en ny uavhengig holdout. Ingen tidsvinduer,
kalibrering eller unntak er tilpasset for å få utfyllingen til å passe.

## De seks åpne kildeavvikene

| 2025/26-kamp | Keeper | Native FPL og komplett historikk | Ekstern komponenttelling |
|---:|---|---:|---:|
| 41 | Gianluigi Donnarumma | 4 | 5 |
| 289 | Guglielmo Vicario | 1 | 3 |
| 307 | Dean Henderson | 0 | 2 |
| 310 | José Sá | 3 | 4 |
| 317 | Karl Darlow | 3 | 2 |
| 346 | Gianluigi Donnarumma | 1 | 2 |

Eksakte spillerkoder, Opta-ID-er, hendelsestellinger og native versjonsbevis
ligger i `results/six_case_decisions.csv.gz`. `remaining_keeper_targets.csv.gz`
bevarer alle 341 tomme krav med eksplisitt `applied=false` og separate
ukvalifiserte kildekandidater. Ingen ledgerverdi endres.

[Optas offentlige definisjoner](https://www.statsperform.com/opta-event-definitions/)
skiller blant annet klareringer, utboksing, interception og keeper-sweeper.
De dokumenterer ikke den konkrete koblingen mellom disse keeperhendelsene
og FPLs CBI-felt. Hendelsesforskjellene er derfor ikke en dokumentert
FPL-regel eller grunnlag for å endre de native tallene.

## Hva som trengs for å fullføre dataene

Det mangler enten en dokumentert FPL-kompatibel telling av keeperhendelsene,
eller en korrigert kildeversjon som kan forklare de seks native vetoene.
En ny kilde må kontrolleres mot hele det opprinnelige utvalget og de gamle
historiske, lag-, identitets- og minuttgatene. Ingen kontroll fjernes og ingen
terskel senkes. Sju måltilfeller har dessuten fortsatt historiske gruppevetoer.

Gjenåpning krever et **konkret nytt dataobjekt, kildeversjon eller
leverandørdefinisjon**. Flere uendrede FotMob-/Opta-/primærnedlastinger,
ny kjøring av native historikk eller en regel som bare treffer seks avvik,
er ikke nye fakta. `TRACK_CURRENT.json` angir kildehindringen, omfanget og
kravet til gjenåpning; den påstår ikke at dataene er utfylt.

## Reproduksjon

Normal offline-replay bruker den versjonerte hendelsesprojeksjonen og
hashkontrollerte eksisterende referanser:

```sh
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/keeper_cbi_resolution/reproduce.py
```

Originalarkivet kreves bare for å bygge hendelsesprojeksjonen på nytt:
`event_audit.py extract /path/to/events_EPL.parquet`. Råfilens SHA-256 er
fryst i `plan.json`. Native FPL, tidligere godkjente verdier, poengversjoner,
kanoniske tabeller og modeller er uendret.
