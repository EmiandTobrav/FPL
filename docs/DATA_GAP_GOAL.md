# Operativt mål: lukk datagapene først

Omdefinert etter brukerens beskjed 9. oktober 2026. Dette styrer det aktive
arbeidet foran den opprinnelige, bredere målbeskrivelsen. Sluttleveransen om
et treningsklart datasett beholdes, men de senere fasene utsettes.

## Mål for arbeidet nå

Lukk flest mulig reelle datagap i FPL-datasettet for 2019/20–2025/26 og
avsluttede runder i 2026/27, så effektivt og raskt som mulig. Innhent og
innarbeid manglende statistikk og nødvendige hendelsesinventarer i en
versjonert dataversjon med dokumenterte kilder.

Start fra nyeste README, STATUS og
[CURRENT.json](../research/current/scoring_2026_27/bulk_reconciliation/CURRENT.json).
Utgangspunktet ved denne presiseringen er **12 476 åpne feltkrav**,
**65 446 inputkomplette spillerkamper** og **768 inputkomplette hele kamper**.
Følg alltid gjeldende filpeker ved videre arbeid; tallene her er et startpunkt.
Registrer også relevante manglende modellstatistikker utenfor poengrestlisten
separat, slik at lukking av denne listen ikke fremstilles som full datadekning.

Gjeldende utgangspunkt er nå **11 234 åpne krav**: **1 730 manglende
dataverdier/inventarer**, **234 kildekonflikter**, **ingen gjenværende FPL-uttrekksunntak**
og **9 270 assistkrav merket regelomregning**. De første tre kategoriene
utgjør en egen [innhentingskø med 1 964 krav](../research/current/scoring_2026_27/bulk_reconciliation/priority/ACQUISITION_CURRENT.json).
Dette er en arbeidsvisning, ikke en redusert restliste. Også assistkravene
kan mangle faktisk hendelsesbevis; innhent slike bevis nå, men utsett nye
regelberegninger og poengetiketter. Ingen kategori anses automatisk komplett.

548 tidligere assistinventargap har komplette mål etter siste kildebatch,
men deres ukjente årsaksbidrag er fortsatt åpne. Bare 20 faktiske assisttotaler
ble lukket i denne batchen; statusflyttingen teller ikke som 548 feltlukkinger.
Den siste kampen er nå innhentet: ett ytterligere assistkrav lukkes og 14
forblir åpne. Ingen assistinventargap står igjen; årsaksfakta for 9 270
assistkrav er fortsatt ufullstendige. Innhenting av disse bevisene fortsetter.

**Prioriteringsendringen gjelder også assistarbeidet:** let først etter
manglende kildefelt og komplette hendelsesinventarer. Ikke la utvikling av
nye assistregler eller større kontrollstudier overta innhentingsfasen.
Anvend eksisterende kvalifiserte regler når de gir raske, faktiske lukkinger.

Siste utfylling avklarer to taklingsfelt fra en eksplisitt godkjent nulltotal.
66 477 spillerkamper og 824 hele kamper har komplette input.

## Arbeidsregler

- Hovedresultatet i denne fasen er flere dokumenterte dataverdier i den
  gjeldende dataversjonen. Velg konkrete innhentingsbatcher foran nye
  analyse- og regelprosjekter. Statistikk til modellinput utenfor
  poengrestlisten inngår også; rapporter dekningen separat.
- Prioriter dokumenterbare lukkinger per tidsbruk. Bruk eksisterende rådata,
  koblinger og kvalifiserte regler før nye omfattende kildeinnhentinger.
- Løs felles årsaker og anvend utfyllinger gruppevis. Komplette spillerkamper
  og hele kamper er supplerende gevinstmål, ikke en grunn til å utsette en
  rask, pålitelig utfylling i andre grupper.
- Bruk et lite kildeforsøk til å avgjøre om en ny rute faktisk leverer de
  nødvendige feltene. Ved manglende bevis eller feilet kontroll: dokumenter
  hindringen, legg ruten til side og velg neste gjennomførbare gruppe.
- Skill innhentede rådata fra godkjente utfyllinger. Rapporter begge, men
  tell bare godkjente, tidligere åpne krav som lukkede. En pilot med for få
  kontroller skal legges til side uten en ny stor studie, med mindre et
  konkret nytt kildefunn gir utsikt til rask utfylling.
- Behold nødvendige kontroller av kilde, identitet, feltdefinisjon og
  hendelsesdekning før masseutfylling. Gjenbruk beståtte kontroller;
  ikke gjenta full datasettkontroll etter hver batch.
- Bevar rå FPL og godkjente verdier. Manglende er ikke null. Ingen
  udokumenterte proxyer, senkede kontrollgater eller fjerning av feltkrav.
- Etter hver batch: rapporter rest før/etter, faktiske lukkinger, nye komplette
  spillerkamper/hele kamper og neste konkrete datainnhenting. Kildefunn,
  dokumentasjon og beregninger alene teller ikke som lukkinger.

## Tidsbruk og valg av neste batch

- Bruk normalt høyst 15 minutter på den første undersøkelsen av en ny
  kilderute: finn om den faktisk leverer feltet, riktig sesong og identitet.
  Tidligere dokumenterte mislykkede ruter skal ikke undersøkes på nytt uten
  konkrete nye kildefakta.
- Etter senest 30 minutter uten konkrete utfyllingskandidater skal ruten
  legges til side med en kort begrunnelse og arbeidet flyttes til neste
  gjennomførbare gruppe. Langvarig innhenting kan fortsette når kilden
  allerede har vist kompatible data og et konkret batchomfang er kjent.
  Tidsgrensene gir aldri adgang til å hoppe over nødvendige kontroller.
- Når flere små utfyllinger bruker samme godkjente kilde og transformasjon,
  samle dem i en batch med felles kontroll og reproduksjon. Ikke bygg en ny
  omfattende leveranse eller kontrollstudie for hver enkelt celle.
- Rapporter per batch tidsbruk, godkjente feltlukkinger og innhentede
  råverdier som fortsatt venter på kvalifisering. Ved null lukkinger skal
  neste handling ha et konkret nytt datagrunnlag eller være en annen rute.
  Flytting av status, sletting av krav og dokumentasjon gir null lukkinger.

## Leveranse og overgang til neste fase

Lever oppdatert dataversjon, restliste, kildebelegg og reproduksjon for de nye
utfyllingene. For gjenværende gap skal det fremgå konkret hvilket felt eller
bevis som mangler, hvilke relevante ruter som er prøvd og hva som kan åpne
for videre innhenting. En dokumentert hindring er fortsatt et åpent krav.

Fortsett datainnhentingen så lenge en gjennomførbar rute kan gi flere
dokumenterbare utfyllinger. Når slike ruter er uttømt, oppsummer restene og
grunnlaget for å gå videre. Ikke erklær hele treningsdatasettet ferdig.

Samlet kvalitetssikring følger datagaparbeidet. Deretter kommer omregning av
BPS, bonus, defcon og øvrige poeng, nye poengetiketter og fristsikre
treningsvisninger. Ny scoring, featurebygging og modelltrening inngår ikke
i arbeidet nå. Tidligere kvalifiserte versjoner bevares.
