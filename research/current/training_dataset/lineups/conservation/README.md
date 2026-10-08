# Full startdekning fra komplette startellevere

Denne versjonen utvider V4s separate startleveranse. Alle **185 573** historiske
spillerkamprader har nå kvalifisert startrolle. De **32 672** siste verdiene er
dokumenterte nuller, avledet fra fullstendige starterinventarer. Tidligere
rådata, prediksjoner og kvalifiserte verdier er bevart.

En null kan bare avledes når elleve forskjellige, eksplisitt kvalifiserte,
stabile personkoder er identifisert på **hver** klubbside. Da finnes det ingen
ledig startplass for en annen kanonisk personkode. Ingen minutter, standardiserte
leverandørminutter eller utelatte statistikkfelt brukes som nullbevis. Inkomplett
inventar beholder manglende verdier; tolv startere eller uklare identiteter avvises.

Prediksjoner og regel ble fryst før den nye fullpopulasjonskontrollen. Kontrollen
har 113 260 originale 2022/23–2025/26-rader i 1 520 kamper, uten avvik mot
kompatible FPL-verdier og separat dokumentert primærfasit for tidlig 2022/23.
5 675 direkte primæroppstillingsroller stemmer. Ingen av de 152 901 tidligere
kvalifiserte verdiene endres. Alle fire opprinnelige sesongterskler er beholdt.
Dette er regresjon med tidligere sett fasit og delt Opta-opphav; ikke blind holdout.

- [Full spillerkamptabell](starts_qualified.csv.xz)
- [Sesongdekning](coverage.csv)
- [Eksakte startidentiteter per kamp](complete_start_inventories.csv)
- [Kvalitetskontroll](validation_summary.json)
- [Manifest](manifest.json)

Seks tester kontrollerer deduksjon, feil klubbside, doble identiteter, ufullstendige
inventarer og bevaring av eksplisitte verdier. Samlet reproduksjon skjer med
`python research/current/training_dataset/reproduce.py` fra repositoryroten.

Dette fullfører **startrollen**, ikke øvrige hendelsesstatistikker, historisk
før-frist-tilgjengelighet eller poeng/BPS/bonus/defcon. Ingen modeller er trent.
