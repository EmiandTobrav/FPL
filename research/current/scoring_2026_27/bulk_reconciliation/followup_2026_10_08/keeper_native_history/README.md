# Keeper-CBI: native kildeversjon forklarer ikke avvikene

Avgrenset kildeforsøk 9. oktober 2026. Hypotesen og alle seks eksisterende
native vetoer ble fryst før innhenting. Fem komplette FPL-spillerhistorikker
ble hentet fra vaastav-speilet ved commit
`a8337d50698de908f92e8d1905142d968384a2ca`. Eksakte mapper ble funnet med
native spiller-ID; kode og navn ble kontrollert mot begge rosterkilder.

Alle seks CBI-verdier i historikken er identiske med det gamle FPL-uttrekket.
De eksterne avvikene beholdes: Donnarumma kamp 41 (4 mot 5) og 346 (1 mot 2),
Vicario 289 (1 mot 3), Henderson 307 (0 mot 2), Sá 310 (3 mot 4) og Darlow
317 (3 mot 2), alle i 2025/26. Kamp, spiller, dato, motstander, side,
sluttresultat, runde og minutter er kontrollert mot fryst native inventar.

**Ingen kildeversjonsrettelse, utfylling eller feltlukking.** De 341 manglende
keeper-CBI-verdiene forblir ukjente. Ruten stoppes: nyere komplett native
historikk gir ingen forklaring på vetoene. Gjenta bare ved konkret nytt
definisjons-/hendelsesbevis eller en annen kompatibel kilde.

`python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/keeper_native_history/verify.py`
gjenskaper sammenligningen offline med hashkontroll av råsvar, fryst utvalg
og native inventar. Kontrollen gjelder de seks vetoene, ikke en samlet
kvalifisering av hele keeperhistorikken. Ledger, poeng og kanoniske tabeller
endres ikke. Kildeinnhentingen og resultatkontrollen tok under ti minutter.
