# Modelltest av rollemønstre og dynamisk motstanderstyrke

Forsøket er fullført og etterkontrollert. Rollemønstre består det forhåndsregistrerte H1-kravet for både poeng og minutter i begge utviklingssesongene. Kombinasjonen består også; dynamisk styrke alene består ikke. Ingen produksjonsmodell, manager eller datasettpeker er endret.

## Poengprognoser for neste runde

Prosentene viser reduksjon i MSE mot den felles kontrollen; positivt tall er bedre.

| Variant | 2023/24 MSE | Endring | 2024/25 MSE | Endring |
|---|---:|---:|---:|---:|
| Felles kontroll | 5.2513 | +0.00 % | 5.0280 | +0.00 % |
| Rollemønstre | 5.1703 | +1.54 % | 4.9628 | +1.30 % |
| Dynamisk styrke | 5.2755 | -0.46 % | 5.0400 | -0.24 % |
| Begge | 5.1908 | +1.15 % | 4.9724 | +1.11 % |

Hovedutvalget har 22 636 kjente spiller–runde-utfall i 2023/24 og 21 502 i 2024/25. Alle varianter bruker nøyaktig samme utfall og kjøpbare spillerpool. Henholdsvis 731 og 229 forespurte rader mangler kvalifisert utfall og holdes utenfor alle variantene; de fylles ikke med null.

Den uendrede aktive modellens arkiverte poengprognose vises som egen `original_active_anchor` i metrics.csv. Den er ikke identisk med hovedkontrollen: hovedkontrollen har samme korrigerte spillerpool og treningsetikettgate som kandidatene, og utelater runden med for sen historisk prognose. Kontroll og kandidater har ellers samme faste sesongvekting og kalibreringsdesign. Nye felter legges til kalibreringen rundt tidligere lagrede baseprognoser; dette er ikke en retrening av alle underliggende basisestimater.

Den faste kandidatlisten har langt mindre poenggevinst: rollemønstre reduserer MSE med omtrent 0,17 % og 0,10 % mot felles kontroll. Mot den originale aktive modellen er kandidat-MSE litt høyere i 2023/24 og lavere i 2024/25. Dette begrenser hvor mye H1-resultatet sier om praktiske lagvalg. Rollemønstre alene gir også høyere minuttfeil blant kandidatene i 2024/25, selv om hovedutvalget forbedres.

## Minuttprognoser

Dette er en separat, felles regresjonskontroll for forventede minutter, ikke dokumentasjon på forbedring over dagens operative minuttmodell. Begge minuttmål og poengmål vurderes separat.

| Variant | Reduksjon MSE 2023/24 | Reduksjon MSE 2024/25 |
|---|---:|---:|
| Felles kontroll | +0.00 % | +0.00 % |
| Rollemønstre | +16.20 % | +14.59 % |
| Dynamisk styrke | +0.16 % | -0.07 % |
| Begge | +17.78 % | +15.48 % |

Minuttkontrollen og kandidatene bruker identisk estimator, tap, forutgående treningsutvalg og oppdateringsrytme. Varighet ved start og innhopp er førfrist-historikk, ikke fasit på rollen i målrunden. Ingen startsannsynligheter eller Brier-forbedringer hevdes.

## Hva er testet?

- Fire varianter: felles kontroll, +rollemønstre, +dynamisk styrke og +begge.
- 66 numeriske/indikatorbaserte rolleegenskaper fra masterens frosne beregning, inklusive eksplisitt siste rolle.
- 19 styrke-/kalenderegenskaper fra samme styrketilstand. Motstanderaggregater lages fra daterte kampoppsett før opprinnelsen, ikke fra det endelige kampoppsettet.
- 2022/23 gir innledende trening. Tidligere avsluttede evalueringsrunder kan brukes ved senere oppdateringer, alltid med både prognose- og etikettid strengt før fit.
- Separate posisjoner og oppdatering GW1,5,9,…37; 640 modelltilpasninger i hovedforsøket, uten parametersøk.
- Samme faste ridge-straff 0,01; ekstra egenskaper imputeres og skaleres bare fra den enkelte treningsdelen. Mangelflagg følger med.
- 2024/25 GW15 er utelatt fra trening og evaluering i alle varianter fordi den gamle prognoseopprinnelsen er etter den faktiske tidligere FPL-fristen.
- Negative poeng beholdes. Reelle nullminutter inngår i målene; dokumenterte utlåns-/utenfor-PL-rader brukes ikke som negative treningsetiketter.

## Kontroller og usikkerhet

Kontrolloppskriften er gjenskapt for alle fire posisjoner. Førfrist-egenskapene samsvarer med eksisterende master der kampobservasjoner finnes. Alle 640 fit er kontrollert mot treningsnøkler, tilgjengelighet, treningsbasert imputering/skalering og de regulariserte normalligningene. 446 592 lagrede kandidat-/kontrollverdier er gjenspilt, og 198 resultatlinjer er kontrollregnet. Alle opprinnelige inputhash er uendret.

metrics.csv viser også fast referansekandidatliste, posisjon, sesongstart, kjent enkelt-/dobbelrunde, ukjent kalender og kvalitetsutvalg. intervals.csv viser parvise fire-runders blokkintervaller med 2 000 trekk. Intervallene er beskrivende: tre kandidater er sammenlignet, sesongene er allerede undersøkt og gjentatte spillere/runder er avhengige. Historisk mottakstid, senere statistikkrevisjoner og den eldre basisprognosens kildekvalitet har fortsatt dokumenterte proxybegrensninger.

## Beslutning

Behold rollemønstre som forskningskandidat. Kombinasjonen beholdes som sekundær sammenligning; den gir mindre poenggevinst enn rollemønstre alene i begge år, men større minuttgevinst mot den diagnostiske minuttkontrollen. Dynamisk styrke alene tas ikke videre uendret som selvstendig poengtillegg. Alle datafelt beholdes i masteren.

Dette forsøket tester H1. Ingen H1-korreksjon kopieres inn i H2–H8, og ingen påstand om flere netto sesongpoeng eller bedre faktiske lagvalg gjøres. Neste modelltrinn er en separat låst flerhorisonttest av rollekandidaten, deretter sesongsimulering med samme manager, chips, spillerpool og ressursgrenser. Den aktive modellen beholdes til en eventuell senere dokumentert vurdering.

## Filer

proposal.json og sentral registrering låser metode, felt, filhash og krav. prediction_lock.json låser alle prognoser før scoring. verification.json dokumenterer etterkontrollen. comparison.csv er den korte sammenligningen; metrics.csv, coverage.csv og intervals.csv viser detaljene. data.pkl er et forsøksgrunnlag, ikke en ny aktiv master.
