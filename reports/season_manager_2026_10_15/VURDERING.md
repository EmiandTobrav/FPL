# Hva den første brede managerprøven lærte oss

Denne kandidatversjonen forkastes som oppgradering. Den lærte rangeringen tapte mot samme forslagssystem uten læring i begge evalueringsår: −553 og −42 netto poeng. Det er dermed ikke bare forskjeller mellom den gamle og den nye planleggeren som forklarer utfallet. Se [hovedresultatet](RESULTATER.md).

## Det konkrete feilbildet

I 2023/24 beholdt den lærte manageren troppen uten bytter i 31 av de 37 rundene etter åpningen. Kontrollen uten læring gjorde dette i tre runder. Den lærte manageren lot første halvårs Wildcard, Free Hit og Bench Boost utløpe ubrukt. Den brukte først andre halvårs Bench Boost i GW34 og Wildcard i GW35. Dette er observerte handlinger, ikke en hypotetisk forklaring.

Den lærte rangeringen valgte gjentatte ganger handlinger med klart lavere verdi etter den felles kortsiktige vurderingen. Den oppnådde ikke en langsiktig gevinst som oppveide dette. Feilbildet er forenlig med dårlig kalibrert verdi av å vente og beholde ressurser. Sammenligningen alene identifiserer ikke hvilken feature eller koeffisient som forårsaket hver feil.

I 2024/25 fikk den lærte manageren 2433 poeng, over både benchmarkens 2344 og chip-policyens 2385. Kontrollen med samme forslag uten læring fikk likevel 2475. Gevinsten mot den eldre benchmarken dokumenterer derfor ikke at den lærte rangeringen tilfører verdi. Hele systemet og læringens tillegg må fortsatt vurderes separat.

[Beslutningsdiagnostikken](decision_diagnostics.json) viser bytteaktivitet, ubrukte chips og avvik fra kortsiktig rangering. Diagnostikken er laget etter kjøringen og brukes til å beskrive utfallet, ikke til å endre policyen eller påstå en årsakssammenheng.

## Hvorfor en enkel sesongverdi er vanskelig å lære

Før 2023/24 har modellen 114 treningsrader fra én faktisk fotballsesong; før 2024/25 har den 266 rader fra to sesonger. Flere rader og alternative managerforløp gjenbruker de samme fotballutfallene. De er ikke uavhengige eksempler på hvordan verden kan utvikle seg.

Målet fra en tidlig runde inneholder poeng for nesten en hel sesong. Mye skyldes senere fotballutfall og handlinger, og kan ikke tilskrives den ene nåværende handlingen. En enkel modell med 40 aggregerte features kan derfor lære sammenhenger som gir dårlige handlingsvalg selv om den trenes på riktig poengmål og før-frist-data. Denne prøven dokumenterer at problemet oppstår her; den viser ikke at managerlæring generelt er feil retning.

## Et bedre avgrenset neste spørsmål

En ny hypotese bør undersøke om vi kan lære **tilleggsverdien av å avvike fra en sterk referanse**, fremfor å la et lite datagrunnlag anslå hele sesongens handlingsverdi med stor frihet. Det krever bedre sammenlignbare fortsettelser fra samme tilstand, mer dekning av alternative handlinger og en på forhånd bestemt kontroll av usikre verdianslag. Plassavhengige benkefeatures er også en konkret, separat kapasitetsutvidelse; se [begrensningene](BEGRENSNINGER.md).

Dette er forslag til en ny registrert prøve. Ingen av disse endringene er testet eller valgt på bakgrunn av disse evalueringsårene i dette forsøket. Dagens benchmark og alle positive og negative resultater er bevart.
