# Avsluttet frisparkprøve – kontrollomfanget er utilstrekkelig

Den tidligere påbegynte prøven er nå ferdigstilt med ett bevart resultat.
**Ingen dataverdi, målavgjørelse, poengversjon eller feltkrav er endret.**
Sporet er ikke kvalifisert og skal ikke kjøres på nytt med uendrede innganger.
Dette er avslutning av et eldre regelspor, ikke nye assistregler i datagapfasen.

Det fryste hendelsesuttrekket gir 30 foreløpige målforslag: 16 der målscoreren
selv vinner frisparket og 14 med en annen ordinær foul-vinner. Bare ni har
hele, regelkompatible ettmålslag som native FPL-kontroll, med 130 spillerkamper.
Fem kontrollmål tilhører selvtatt-gruppen og fire den andre gruppen.
Hele assistvektoren stemmer på alle ni, uten beskyttede konflikter eller
konflikt mot tidligere kandidatavslag. Dette oppfyller likevel ikke den
opprinnelige globale gaten på **20 kontrollmål**, og ordinær-gruppen er under
kravet om **fem per gruppe**. Ingen kontroll utelates og ingen terskel senkes.
Ingen gruppe, heller ikke selvtatt-gruppen, er derfor kvalifisert.

[Den opprinnelige protokollen](protocol.json), regelkode, kildepekere,
utfallsblind kontrollseleksjon og prediksjonsfrys er bevart. Resultatet er
regresjon på tidligere sett kildebevis, ikke uavhengig holdout. Hånden,
indirekte spark, korte pasninger, ufullstendige inventarer og tvetydige
årsaksforløp gir ingen kvalifikasjon. Mål med andre assistårsaker behandles
ikke av denne prøven. Rå FPL og godkjente målavgjørelser forblir uendret.

Et senere nytt, komplett og kompatibelt mål-/foulinventar må tilføre flere
på forhånd valgte kontrollmål før sporet kan gjenåpnes. Det eksisterende
kontrollutvalget beholdes. Datagapinnhenting fortsetter; nye regelberegninger
følger brukerens faseorden etter nødvendig kildearbeid og samlet kvalitet.

Fra denne mappen:

```bash
python reproduce.py
```

**Ni filer gjenskapes byteidentisk offline**, inkludert kontrollplan,
prediksjoner, kildefrys og de uendrede kontrollresultatene. Ingen ny
nettinnhenting kreves. [Kontrollresultat](results/validation.json),
[avslutningsstatus](results/findings.json) og [replaybevis](replay_report.json)
dokumenterer de konkrete manglende gatene og null anvendte utfyllinger.
