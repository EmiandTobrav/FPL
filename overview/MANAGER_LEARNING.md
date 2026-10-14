# Lære en modell å være FPL manager

Forskningsidé fra brukeren 14. oktober 2026. Hypotesen er at modellen kan forbedres ved å lære verdien av managerhandlinger over tid, i tillegg til å predikere spillerpoeng. Ingen slik ny modell er trent eller valgt gjennom dette notatet.

## Hva som endres

| Tilnærming | Hva modellen lærer | Hvordan den vurderes |
|---|---|---|
| Poengprediksjon | Forventede poeng for hver spiller og horisont. | Prognosefeil og kalibrering, deretter faktisk managerresultat. |
| Beslutningslæring | Hvilke bytter, kapteinsvalg og chipvalg som gir størst langsiktig verdi fra en gitt managertilstand. | Netto sesongpoeng fra lovlige handlinger under samme informasjon og ressurser. |
| Læring for å vinne | Hvilken strategi som gir størst sannsynlighet for å slå et definert konkurrentfelt. | Vinnsannsynlighet eller rangering under en modell av konkurrenter og usikre utfall. |

Prognosemodellen og manageren kan brukes sammen. En modell kan ha lav gjennomsnittlig prognosefeil og likevel velge feil kaptein eller bruke et bytte for tidlig. Managerens verdifunksjon må også verdsette bank, gratisbytter, fremtidig fleksibilitet og ubrukte chips.

Den eksisterende benchmarken er allerede en manager på beslutningssiden: prognoser mates inn i en regelstyrt planlegger. Den nye hypotesen er å lære deler av beslutningspolicyen eller fremtidsverdien i stedet for å bruke bare forhåndsbestemte heuristikker. Den erstatter ikke automatisk prognosemodellen eller regelmotoren.

## Matematisk oppsett

En tilstand består av tropp, kjøpspriser, bank, gratisbytter, chips, runde og informasjon som faktisk er tilgjengelig før fristen. Fotballtilstanden er bare delvis observert; fremtidig form, skader og rotasjon er usikre.

En handling er et lovlig sett med bytter, startellever, benk, kaptein og eventuell chip. Belønningen kan først være rundens poeng minus overgangskostnader. Policyen velger handlinger for å maksimere forventet samlet verdi over resten av sesongen:

`maksimer forventet sum av netto rundepoeng gitt policyen`.

For et eksplisitt vinnermål endres kriteriet til:

`maksimer sannsynligheten for at egen sluttscore overstiger konkurrentfeltets beste sluttscore`.

Disse målene kan foretrekke forskjellige handlinger. Hvis en manager ligger langt bak, kan høyere risiko øke sjansen for å ta igjen lederen selv om forventede poeng er litt lavere. En leder kan foretrekke å redusere variasjon relativt til konkurrenten. Effekten avhenger av det konkrete feltet, ikke bare egen poengfordeling.

## Første avgrensede hypotese

Behold datagrunnlag, prognoser, lovlighetsmotor og kontrollpolicy. Test en lært fremtidsverdi for beholdte gratisbytter, bank og chips, eller en avgrenset beslutningsrangering blant lovlige forslag fra dagens planlegger. La den eksisterende motoren håndheve reglene.

Denne første sammenligningen svarer på om **lærte beslutninger** tilfører verdi med de samme prognosene. Prognoseforbedringer og endret risikomål skal testes separat før de eventuelt kombineres. Start med forventede netto sesongpoeng; ikke bruk en udefinert «vinne»-belønning.

Før forsøket registreres må treningsmiljø, policyklasse, tillatte handlinger, belønningsmål, ressursgrenser, kontroll og stoppregel fryses. Den eksisterende kampanjens tak på åtte konfigurasjoner skal ikke utvides gjennom denne ideen. Et nytt forsøk trenger en separat dokumentert kampanjeramme.

## Hva simulatoren må gi oss

Den eksisterende regelmotoren gir lovlige tilstandsoverganger og poengberegning. [Model Lab](../model_lab/README.md) gir en kontrollert inngang for prognoser, input og resultater. I denne versjonen er de innebygde managerpolicyene adaptive og faste; en trenbar managerpolicy er et videre adapterarbeid.

For læring gjennom simulering trenger vi i tillegg et kvalifisert usikkerhetsmiljø med plausible spillerutfall, spilletid og samvariasjon. Mange simuleringer av de samme historiske sesongene er ikke mange uavhengige fotballsesonger. En agent kan ellers lære å utnytte simulatorens svakheter eller historisk fasit.

For et vinnermål må vi også definere feltet: miniliga, øvre persentil eller overall-seier. Konkurrentenes lag, eierskap, handlinger og risiko blir en del av miljøet. Konkurrentmodellen må evalueres separat; et høyt simuleringsresultat gir ikke i seg selv en dokumentert sannsynlighet for faktisk overall-seier.

## Forskningsgrunnlag og vurdering

Decision-focused learning trener en prediktiv modell etter kvaliteten på beslutningene den fører til. Et NeurIPS-arbeid undersøker dette for sekvensielle beslutninger og sammenligner det med trening på et mellomliggende prediksjonstap. Resultatene gjelder studiens egne oppgaver, og gir en metodisk begrunnelse for å teste ideen i FPL. [Learning MDPs from Features](https://proceedings.nips.cc/paper_files/paper/2021/hash/49e863b146f3b5470ee222ee84669b1c-Abstract.html).

En annen mulig senere retning er offline læring fra sekvenser av tilstander, handlinger og belønninger. Decision Transformer betinger handlinger på blant annet ønsket fremtidig avkastning og tidligere hendelser. Arbeidet tester Atari, Gym og Key-to-Door; det dokumenterer ikke en bedre FPL-manager. [Decision Transformer](https://proceedings.neurips.cc/paper_files/paper/2021/hash/7f489f642a0ddb10272b5c31057f0663-Abstract.html).

Prosjektets første prioritet bør være en liten, kontrollert lært beslutningskomponent med tydelig referanse. Mer kompleks arkitektur er først berettiget hvis den mindre prøven viser en konkret svakhet som den kan løse.
