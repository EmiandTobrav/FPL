# Managerlæring gjennom hele sesongen

Forsøk `season-manager-20261015-v1` bygger videre på den kontrollerte TC/BB-piloten. Brukeren ba om en modell som lærer hvordan det er å styre runde for runde, med alle chips og øvrige managerbeslutninger. Dette er en separat kampanje med én konfigurasjon. Eldre kampanjer og resultater er bevart.

**Fullført og etterkontrollert.** Denne versjonen tapte mot samme forslag uten læring i begge år: −553 og −42 poeng. Den erstatter ikke benchmarken. Se [resultatet](RESULTATER.md) og [vurderingen av hva som gikk galt](VURDERING.md). Ingen parametere ble endret under forsøket.

## Hva policyen styrer

Policyen velger mellom komplette lovlige handlinger: tropp/bytter, å beholde laget og spare gratisbytter, startellever, benkerekkefølge, kaptein/visekaptein og alle fire chips. Forslag kommer fra den eksisterende H3-planleggeren, en H1-plan og varianter av beholdt lag, lagoppstilling, kaptein og benk. Alle tilgjengelige chiptyper skal foreslås. Den lærte rangeringen velger handlingen.

Dette dekker beslutningstypene innen et håndterbart forslagssett. Det utforsker ikke hver mulig spillerkombinasjon. Ingen utfallsdata eller spiller-ID-er brukes som features. Samme regelmotor håndhever budsjett, gratisbytter, hitkostnader, chips og Free Hit-gjenoppretting.

Les også [modellens konkrete kapasitetsbegrensninger](BEGRENSNINGER.md). Blant annet mangler den egne features for hver benkeplass; ulike rene benkerekkefølger kan derfor følge den faste poenglikhetsregelen. Hele handlingen velges, men hver detalj er ikke nødvendigvis lært separat.

## Hva treningen lærer

Belønningen er faktisk netto poengsum fra den valgte runden helt til GW38. En Ridge-modell lærer justeringen av en felles kortsiktig forventningsverdi ut fra 40 felt om handlingen, laget, fremtidige uendrede prognoser, bank, bytter, chipbeholdning og før-frist-historikk for spilletid.

Modellen starter med tidligere kontrollerte sesongforløp. Deretter prøver den alternative lovlige handlinger i to nye historiske sesongforløp, med fast utforsking på 30 og 15 prosent. Modell og skalering oppdateres etter fullført forløp og fryses før evaluering. Alle målene går til sesongslutt; de er ikke bare bonusen i chiprunden.

2023/24 evalueres etter trening bare på 2022/23. 2024/25 evalueres etter trening på tidligere år til og med 2023/24. De tidligere 2022/23-treningsforløpene gjenbrukes. Totalt er det fire nye treningsforløp og fire nye evalueringsforløp, høyst 304 nye beslutninger og seks små modelltilpasninger. 2025/26 brukes ikke.

## Kontroller

- Dagens benchmark og den første lærte chip-policyen gjenbrukes fra forrige fullførte, etterkontrollerte forsøk med identiske input og løsergrenser.
- En ny kontroll bruker samme forslagssystem og kortsiktige rangering uten læring. Den viser om den lærte rangeringen tilfører noe utover forslagsutvidelsen.
- Samme fryste prognoser, data, startregler og regelmotor. Begge nye policyer har én tråd, 16 noder per løserkall og høyst 40 kall per beslutning.
- Trening er ekstra arbeid og rapporteres separat. Lik ressursramme betyr ikke lik faktisk CPU eller samme antall løserkall.

Kravet for en positiv pilot er gevinst mot alle tre kontroller i begge evalueringsår. Ingen automatisk oppgradering av benchmark. Modellen trenes for netto poeng; en modell av konkurrenter og vinnsannsynlighet inngår ikke.

## Status og filer

Les `orchestration_state.json` for siste registrerte status. `protocol.json` og `registration.json` fryser hypotesen, datagrunnlaget, ressursene og stoppreglene. `training/` inneholder hver modelltilpasning og dens treningsrader; `models/` inneholder fryste evalueringsmodeller. `episodes/` bevarer alle lovlige forslag, valgt handling og etterfølgende oppgjør. Et forløp som har startet skal ikke kjøres en gang til automatisk.

Etter fullføring skal `audit.json` kontrollere alle 304 runder, lovligheten og før-frist-features i hvert forslag, faktisk valg, fryste modeller, sesonglange treningsmål, treningsfrister, uendrede prognoser og løsergrenser. `RESULTATER.md` og tabellene er først gyldige når denne kontrollen består.

Det eksisterende best-effort-poengmålet og historiske tilgjengelighetsproxyer er beholdt. To tidligere studerte evalueringssesonger og gjentatte forløp gjennom samme historiske utfall gir begrenset bevis for generalisering. Fire simulerte treningsforløp er ikke fire nye uavhengige fotballsesonger.

## Kode og gjentakelse

`model_lab/manager_policy.py` definerer handlinger, features, mål og lært rangering. `model_lab/manager_learning.py` styrer fristkontrollert trening, evaluering, etterkontroll og rapport. Seks målrettede tester og en før-frist-integrasjonsprøve bestod før forsøket ble fryst.

Kjøreren bruker allerede registrert `config.json` og hele det lokale, fryste inputarkivet. Den nekter å starte en kopi når `started.json` finnes. Ikke rediger fryst kode eller kjør om igjen for å finne bedre parametere. Nye hypoteser registreres som egne versjoner. Git-publikasjonen kan kontrollere publiserte forsøksfiler, men full kjøring krever det separate lokale forecast- og oppgjørsarkivet.
