# Lært managerpolicy med uendrede prognoser

Dette er ett avgrenset forsøk registrert 15. oktober 2026. Det sammenligner en lært verdi av å spare Triple Captain og Bench Boost med benchmarkens eksisterende reserveheuristikk. Alle spillerprognoser er uendret. Ingen ny produksjonsmodell velges automatisk.

Forsøket er nå **fullført og etterkontrollert**: +53 og +41 netto poeng i de to lærte evalueringsårene, +47 i snitt. Les [resultatet](RESULTATER.md). Dagens benchmark beholdes inntil en separat vurdering.

Ikke start kjørerne på nytt for dette fullførte forsøket. `verify_saved.py` kontrollerer resultatbundne filer uten nye løserkall. `audit.py` gjentar den grundigere kontrollen og krever hele det lokale, fryste inputarkivet. Git-utgaven bevarer rundelogger komprimert i `round_evidence.tar.gz`; `verify_saved.py` kontrollerer også disse uten utpakking. Protokollens opprinnelige lokale stier er bevart, og full inputreplay krever arkivet, ikke bare Git-publikasjonen.

## Sammenligningen

| Forhold | Kontrakt |
|---|---|
| Datasett | fpl_2026_27_best_effort_v1, samme omregnede poengmål og kvalitetsbegrensninger |
| Benchmark | fixture_full_h3_adaptive_tc_harmonized_causal_v1, adaptiv manager fra GW1 |
| Sesonger | 2022/23, 2023/24 og 2024/25, samme fryste prognosefiler ved 114 tidspunkter |
| Endring | Kun reserve_value for TC og BB; øvrig policy og eksisterende vurdering av fremtidige chipmuligheter er uendret |
| Læring | Separat Ridge per chip, alpha 10, åtte før-frist-features og StandardScaler tilpasset treningsdelen |
| Treningstid | Modeller fryses ved sesongstart og bruker bare tidligere sesonger med tilgjengelige utfall |
| Kald kontroll | 2022/23 bruker uendret benchmarkpolicy fordi tidligere treningslogger ikke finnes i denne kontrakten |
| Løserressurser | Én arbeider/tråd, samme frø, 16 noder per kall, høyst 40 kall per beslutning; ingen automatisk ny kjøring ved løserfeil |
| Fitting | Felles øvre ramme på fem CPU-sekunder per sesong; kandidaten bruker to små Ridge-tilpasninger i hvert av de to lærte evalueringsårene |
| Mål | Netto sesongpoeng etter overgangskostnader; faktiske ressursmengder rapporteres separat |

Dette er en lært beslutningskomponent, ikke en full manager trent med end-to-end reinforcement learning. Forventede poeng og lovlighetsmotor beholdes. Effekten vurderes gjennom faktiske, hele managerforløp.

## Hva modellen lærer

Treningsmålet er den diskonterte merverdien av chipbruk på det tidspunktet benchmarken faktisk brukte chipen senere i samme halvdel av en tidligere sesong. Merverdien beregnes ved å poengberegne det samme observerte laget med og uten chip, inkludert autosubstitusjoner.

Modellen får ikke vite hvilken fremtidig runde som ville vært best. Det søkes ikke etter den beste runden i ettertid. Dager da benchmarken allerede brukte chipen, eller der ingen senere observert bruk finnes, inngår ikke som oppdiktede nullmål.

Dette anslår en verdi av å fortsette langs benchmarkens observerte atferd. Det identifiserer ikke hva som faktisk ville skjedd dersom en annen manager hadde ventet med chipen og deretter valgt andre lag. Første test undersøker om denne beskjedne læringen likevel forbedrer beslutningene i en ny sesong.

## Kontroller og begrensninger

Referansen kjøres på nytt med de samme prognosene og grensene. Tidligere sesongsummer brukes ikke som sammenligningsresultat. De tidligere loggene brukes som treningshistorikk for senere år og som en separat kontroll av at den nye referansekjøringen gjenskaper benchmarken.

Avgjørelsen låses før oppgjørsdata leses. Kvalifisert håndtering av blankrunder gjenbrukes fra den eksisterende simulatoren. Manglende valgte utfall blir ikke nuller. Poeng, tilstandsoverganger, modellkoeffisienter, treningsdatoer, prognosehash og løsergrenser etterkontrolleres i audit.py.

Alle evalueringssesonger er allerede studert i prosjektet. Bare to år evaluerer en faktisk trent policy; 2022/23 er kald kontroll. 2025/26 brukes ikke. Positivt resultat i denne prøven vil derfor ikke alene dokumentere generell overlegenhet eller større vinnsannsynlighet.

## Mekanisk retting under kjøring

Første referansesesong ble fullført og alle 38 runder lagret, men en variabel for tidsmåling ble overskrevet av en liste over startspillere ved blankrunden. Det ga en feil ved sluttoppsummeringen. Original kode, feil og de 76 låste avgjørelses-/oppgjørsfilene er bevart.

En avgrenset retting i resume_v002.py validerer og gjenbruker de lagrede rundene uten nye løserkall, og kjører bare arbeid som ennå ikke var startet. Policy, treningsmål, prognoser, parametere og kriterier er uendret. mechanical_resume_v002.json binder den nye kjøreren og den bevarte filrekken.

Den opprinnelige totalmålingen av prosess-CPU og veggklokketid for denne ene referansesesongen kan ikke gjenopprettes sikkert og rapporteres som ukjent. Registrerte løserkall, noder, opsjoner og per-kall-tider er bevart. Ressurslikhet gjelder identiske grenser, ikke en påstand om identisk faktisk CPU-bruk.

## Filer

protocol.json fryser forsøket før den lærte sammenligningen. registration.json peker til det sentrale forsøksregisteret. training inneholder tidsavgrensede treningsrader og koeffisienter; runs inneholder låste avgjørelser, oppgjør og sesongkvitteringer. Resultatet skal først tolkes etter en bestått audit.json og en samlet resultattabell.
