# Hva denne første sesongmanageren dekker

Alle fire chiptyper og komplette lovlige handlinger inngår i forslagssystemet. Modellen kan rangere ulike tropper, bytter, å spare bytter, startellevere og kapteins-/visekapteinsvalg fra de samme før-frist-prognosene. Den lærer fra poeng helt til sesongslutt.

Modellen ser aggregerte features, ikke hele råtilstanden eller alle mulige handlinger. Ulike handlinger som får samme featurevektor og kortsiktige verdi blir behandlet likt, med en fast regel for poenglikhet. Dette er en viktig kapasitetsbegrensning i den enkle Ridge-modellen.

Spesielt har benkrekkefølge faste alternative forslag, men benkens minutter, deltakelse og prognoser summeres eller gjennomsnittsberegnes. Det finnes ikke egne features for hver benkeplass. Modellen kan derfor ikke lære en selvstendig rangering av to ellers identiske handlinger som bare bytter rekkefølge på de samme benkespillerne. Den velger en komplett handling, men denne detaljen følger poenglikhetsregelen. Et senere forsøk med plassavhengige features må registreres som en faktisk modellendring; den fryste prøven endres ikke underveis.

Den samme begrensningen gjelder spillere eller lag som er forskjellige i virkeligheten, men identiske i de aggregerte inputene. Dette forsøket tester sesonglang læring av et bredere sett managerhandlinger, og gir et fungerende utgangspunkt for mer detaljert læring. Det dokumenterer ikke at alle aspekter ved FPL er lært eller optimalt løst.
