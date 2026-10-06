# 2024/25: historiske poeng med rekonstruert defcon

Fullført 6. oktober 2026 etter brukerens godkjenning av gratisdatakvaliteten. Datasett-ID `historical_plus_defcon_2025_v1`. Kostnad 0 NOK.

## Ferdig datasett

- 27 283 vanlige spiller-/kamprader, 380 kamper, 11 566 rader med spilletid.
- Ingen manglende defcon-grunnlag blant aktive utespillere.
- 322 Assistant Manager-rader er utelatt; de er ikke vanlige spillere.
- 1 253 defcon-utslag gir 2 506 ekstra poeng fordelt over hele spillerpopulasjonen. Dette er ikke en managers sesonggevinst.
- Forsvarere: 1 316 tilleggspoeng; midtbane: 1 174; angrep: 16; keepere: 0.

| Spiller | Historiske poeng | Rekonstruert defcon | Historisk + defcon |
|---|---:|---:|---:|
| James Tarkowski | 105 | 44 | 149 |
| Moisés Caicedo | 98 | 42 | 140 |
| Jan Bednarek | 60 | 40 | 100 |
| Dean Huijsen | 104 | 38 | 142 |
| Murillo | 130 | 38 | 168 |

Dette er **ikke full 2025/26-omregning**. Assists, bonus og alle øvrige poengkomponenter beholder historisk verdi. Historisk posisjon brukes. De rekonstruerte defensive poengene har kvalitetsflagg, ikke status som offisiell fasit. Grunnlaget er [FPL-Core-Insights](https://github.com/olbauday/FPL-Core-Insights) og våre fryste FPL-filer, kontrollert mot [2025/26](../core_2025_validation/README.md).

## Filer og bruk

Kjør `python research/current/rescoring_2025/defcon_2024/build.py` fra en checkout med klargjorte prosjektdata. Utdata ligger i `results/`:

- `GW01.csv`–`GW38.csv`: én rad per FPL-spiller/kamp, med opprinnelige poeng, defcon, alternativ total, kvalitet og telling. Dobbeltrunder beholder separate kamper.
- `players.csv`: spillersummer og følsomhet for én hendelse mer/mindre per kamp.
- `positions.csv`: posisjonssummer.
- `manifest.json`, `input_sha256.json`: definisjon, avgrensninger og sporbarhet.
- `source_only.csv`: kildeobservasjon uten tilsvarende FPL-rad; ikke lagt inn som en kunstig opptreden.

Kampkoblingen bruker ordnet hjemme-/bortelag og sesong; spillerkoblingen bruker FPL-ID. Aktive mangler ville stoppet byggingen. Null spilletid gir null defensive poeng fra offisiell opptreden, ikke fra antatt null i manglende statistikk. Keepere er ikke kvalifisert. Alle summer avstemmes; tester dekker terskler, manglende tellinger og separate kamper i dobbeltrunder.

`defcon_minus1` og `defcon_plus1` er eksplisitte stresscenarioer for én færre/flere tellende defensive hendelser per spiller/kamp. De er ikke konfidensintervaller eller estimerte feilrater. Ingen korreksjon er lært fra 2025/26 og brukt bakover. Valg av kilde er likevel vurdert mot 2025/26, så dette etablerer ingen ny urørt testperiode.

## Neste modellforsøk

Den eksisterende benchmarken og alle historiske resultater er urørt. Neste forsøk bør bruke en separat måldefinisjon og kjøre benchmark-algoritmen og utfordreren på samme nye oppgjørsgrunnlag. Skill mellom å legge defcon til oppgjøret og å retrene modellen mot det nye målet; ellers blandes scoringeffekt og modellgevinst. Eventuelle defensive prediktorer må lagges før fristen. Bare å legge siste sesongs rekonstruerte sluttpoeng inn som før-kamp-feature ville gi lekkasje.

Den undersøkte gratisdatakilden har sesongmapper fra 2024/25 og fremover. Arbeidet her gjør derfor 2024/25 tilgjengelig som ytterligere defcon-treningsgrunnlag; det hevder ikke at tidligere sesonger allerede er rekonstruert. For eldre år må nye kilder kontrolleres før tilsvarende utvidelse. Maksimalt 500 NOK totalt er registrert for eventuell senere datatilgang; ingen abonnement eller kjøp er gjort.
