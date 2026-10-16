# Planlegging uten reservekostnader

Forsøk `explicit-planning-20261015-v1`. Prognoser og tidligere forsøk beholdes uendret. Dette er en ny beslutningsmetode, ikke en ny prognosemodell eller en ferdig trent sesongagent.

## Hva planleggeren sammenligner

Ved hver frist sammenlignes lovlige planer for inneværende og neste runde. Planene kan bruke en chip nå, senere eller ikke bruke den. Målet er summen av forventede poeng fra tellende spillere og kaptein, minus fire poeng per betalt bytte. Ingen reservekostnad, bonus for chipbruk, rabatt på fremtidige poeng, kunstig benkverdi eller lært korreksjon legges til.

Bare første handling utføres. Neste runde planlegges på nytt med informasjonen som da er tilgjengelig. Gratisbytter, bank og chipbeholdning følger regelmotoren. Ved Free Hit gjenopprettes opprinnelig lag og bank før neste runde. Chipsettet før GW20 kan ikke flyttes til andre halvdel. Etter siste lovlige bruksrunde finnes ingen handling som kan bruke den gamle chipen.

Eksempel: Gir Triple Captain fem ekstra forventede poeng nå og tjue neste runde, kan planen foretrekke å vente. Hvis neste runde ligger etter utløp, er den gamle chipen utilgjengelig der. Det kreves ingen kunstig kostnad for å uttrykke dette.

## Viktige begrensninger

To runder fram er kort. Det finnes foreløpig ingen lært verdi av tilstanden etter horisonten. Planleggeren kan derfor bruke chips for tidlig og overse gode muligheter lenger fram. Sesongresultatet vurderes gjennom alle 38 runder, men hvert valg bruker to runders planlegging. Dette beviser ikke sesongoptimalitet.

Alle lovlige chipsekvenser innen horisonten prøves. Hvert lagforslag bruker den eksisterende spillerlisten og begrenset heltallsoptimering. Det er ingen garanti for globalt beste lag. Ved Free Hit løses segmentene sekvensielt; de er ikke én globalt optimal felles løsning. Priser, klubb, posisjon og kjøpbarhet holdes på verdiene kjent ved planens frist. Gjenkjøp av en opprinnelig eid spiller innen samme plan støttes ikke.

Poengmålet bruker spillerprognoser direkte. Det har ikke en egen sannsynlighetsmodell for automatiske innbyttere eller visekaptein. Faktiske resultater avregnes med den eksisterende regelmotoren, inkludert innbyttere og visekaptein.

## Kontrollert sammenligning

Den nye kandidaten sammenlignes med samme H2-planlegger som trekker fra de gamle reservekostnadene. Begge får samme prognoser, lovlige forslag og øvre ressursgrenser: én tråd, 16 noder per optimering og maksimalt 40 optimeringer per beslutning. Faktisk ressursbruk rapporteres separat.

Begge kjører hele utviklingssesongene 2022/23, 2023/24 og 2024/25. Tidligere etterkontrollerte benchmark- og chip-policyresultater gjenbrukes som sekundære referanser. Disse har en annen beslutningsmetode og horisont; den parede reservekontrollen isolerer reserveendringen. Ingen modell trenes. Ingen beslutninger eller resultater fra 2025/26 brukes til valg, trening eller evaluering. Ingen automatisk oppgradering av benchmark.

Protokoll og forsøksregister fryses før sesongresultater leses. Beslutning og alle planer lagres før rundens faktiske utfall hentes. Etterkontrollen beregner lovlighet, poengmål, handlingsvalg og faktisk avregning på nytt uten nye optimeringer.

## Videre utvikling

Målet er forventede netto poeng gjennom resten av sesongen. Et naturlig neste trinn er lengre eller scenarioavhengige forløp og en forsiktig lært verdi av gjenværende tilstand. En slik verdi må komme fra fremtidige netto poeng i treningsforløp, være null ved sesongslutt og valideres mot eksplisitte planer. En ny læringsvariant må registreres separat før testing; gamle reservekonstanter skal ikke innføres under et nytt navn.

## Kjøring

`python -m model_lab.planning_experiment preflight`, deretter `freeze`, `run` og `audit`. Hvert trinn oppretter nye, låste filer. En startet kjøring kan ikke automatisk startes på nytt. Full kjøring krever det lokale, frosne prognosearkivet og datagrunnlaget; Git alene inneholder ikke alle disse inngangsfilene.
