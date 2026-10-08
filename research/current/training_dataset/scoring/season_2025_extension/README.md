# Utvidet kvalifisert poengversjon for 2025/26

Denne additive versjonen bruker den uendrede, kvalifiserte omregningsmotoren
fra `season_2025` og de 14 nye direkte primære lokasjonsverdiene. Den
kvalifiserer **12 nye hele kamper**, samlet **374 kamper og 11 315 spillerkamper**.
Én tidligere kvalifisert kamp (365) sperres av et nytt BCS-avvik; nettoøkningen
er elleve hele kamper. Alle øvrige tidligere labels er kontrollert identiske;
den publiserte første versjonen og godkjente keeperverdier bevares.
442 spillerkamper får endret bonus/poeng mot historisk FPL; komponentregnskapet
har ingen residualer. Native grunnpoeng og allerede tildelt defcon bevares.

381 ferske storsjanseredningstellinger er også kontrollert. To kildeavvik
gjelder Kelleher337 og Sánchez365; begge hele kamper sperres uten å erstatte
godkjente verdier. Resultatet ligger i latest_primary_big_chance_controls.csv.

De 746 lokasjonskontrollene og hele produsentens fryste innganger/utganger
kontrolleres før omregning. Alle tidligere native felt-, helkamp-, bonus-,
inside-, storsjanserednings- og taklingsgater er uendrede. `input_lock.json`
låser også den nye kildebatchen. Den opprinnelige v1 er uendret og separat
reproduserbar; ingen godkjente keeperartefakter er overskrevet.

Seks kamper er sperret:

| Kamp | Årsak |
|---|---|
| 33 og 323 | Sánchez sine outside-krav er åpne under eksakt minuttgate |
| 215 | Barnes, code 44699, har et null-minutt-kort utenfor gammel ledger; originalpoeng −1 bevares |
| 337 | Kellehers ferske storsjanseredningsrevisjon 0→1 er fortsatt beskyttet |
| 356 | Dokus times-tackled-kildekonflikt er fortsatt åpen |
| 365 | Sánchez: godkjent BCS=1, ny komplett primærsesong peker mot 0; originalverdien bevares |

Ingen inaktive observasjoner gis oppdiktede poengetiketter. Før-frist-features
og trening er ikke kvalifisert. En hel kamp må være kvalifisert før bonus eller
noen av dens nye poengetiketter publiseres.

Fra repositoryroten:

```sh
python research/current/training_dataset/scoring/season_2025_extension/reproduce.py
```

Tretten resultatfiler er gjenskapt byteidentisk offline i en separat kopi.
`results/fixture_status.csv` viser alle 380 kamper, og manifestet dokumenterer
kode, innganger, utganger og poengversjonen.
