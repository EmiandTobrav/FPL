# Utvidelse til 2019/20–2023/24: FBref-arkiv

Fullført 6. oktober 2026. Gratis kilde funnet, hentet, kontrollert og brukt til **foreløpige, delvis dekkende** etiketter. Ikke eksakt ny-regel-fasit og ikke en ny modellsimulering. Kostnad 0 NOK.

## Kilder og reproduserbarhet

[JaseZiv/worldfootballR_data](https://github.com/JaseZiv/worldfootballR_data/releases/tag/fb_advanced_match_stats) publiserer Premier League-spillerdata per kamp. Vi hentet `ENG_M_1st_defense_player_advanced_match_stats.csv` (45 693 432 bytes, asset-ID 294012224) og `ENG_M_1st_misc_player_advanced_match_stats.csv` (44 553 850 bytes, asset-ID 294203825). Deres publiserte SHA-256 stemmer med de nedlastede filene; se `source_sha256.json`. Arkivet vedlikeholdes ikke lenger.

Spillerkobling bruker [ChrisMusson/FPL-ID-Map](https://github.com/ChrisMusson/FPL-ID-Map): stabil FPL/Opta-code til FBref-ID. Et fryst `raw/Master.csv` er inkludert. Vi gjenbruker prosjektets sesongvise FPL-playerfiler for code til element-ID; ingen fuzzy navnematching. Kampkobling bruker sesong, hjemmelag og bortelag med eksplisitte navnealiaser. Gyldige nøkkelrelasjoner testes. Kildenes registreringsdefinisjoner og dekning kan variere over tid.

Fra repositoryets rot, etter vanlig `scripts/prepare_data.py`:

```
python research/current/rescoring_2025/historical_fbref/download.py
python research/current/rescoring_2025/historical_fbref/build.py
```

De store opprinnelige CSV-ene gjenopprettes fra publiserte release-assets og hashkontrolleres. Historiske etiketter, ID-kart, kode, dekning og validering er lagret direkte i dette repositoryet. Masterfilen er kun identitetsmapping; ingen fremtidig prestasjonsvariabel brukes til prediksjon.

## Dekning i nye historiske etiketter

Prosentene gjelder aktive utespiller-/kamprader med beregnbare defcon-poeng, ikke antall kamper eller alle registrerte spillerrader.

| Sesong | Defensive kamper | Kamper med gjenvinningsfil | Brukbare aktive utespillerrader | Mangler | Dekning |
|---|---:|---:|---:|---:|---:|
| 2019/20 | 380 | 380 | 9812 | 2 | 99,98 % |
| 2020/21 | 380 | 380 | 9628 | 0 | 100,00 % |
| 2021/22 | 379 | 305 | 8477 | 1245 | 87,19 % |
| 2022/23 | 380 | 373 | 10420 | 155 | 98,53 % |
| 2023/24 | 380 | 380 | 10551 | 57 | 99,46 % |

Filernes kampdekning garanterer ikke fuld spiller-/feltdekning. Forsvarere behøver ikke gjenvinninger, så de kan stadig ha beregnbare poeng i kamper der misc-filen mangler. Ukoblede spillere og nødvendige manglende statistikker forblir eksplisitt manglende, aldri null. 2019/20 har i tillegg 32 FPL-spiller/kampnøkler med motstridende minutter/poeng i duplikater; disse er sperret fra alternative etiketter. De fleste berører ikke aktive utespillerrader i tabellen, men hindrer likevel en påstand om komplett sesongfasit.

Kjente, rekonstruerte tilleggspoeng er henholdsvis 3492, 3002, 2748, 2698 og 2680. Ved mangler er dette summer av kjente verdier, ikke komplette nye sesongtotaler eller managergevinster.

## Ny kildedefinisjon kontrollert

FBref skiller mellom blokkering av skudd og pasninger. CBIT her bruker **Tkl_Tackles + Sh_Blocks + Int + Clr**; MID/FWD får i tillegg `Recov`. Ikke legg `Blocks_Blocks` til som om alle pasningsblokkeringer gir FPL-poeng.

Arkivet inneholder 40 kamper fra starten av 2025/26, som gir 1129 sammenlignbare aktive utespillerrader mot offisielle FPL-tellinger:

| Variant | Poengavvik | Enighet |
|---|---:|---:|
| Bare skuddblokkeringer | 10 (alle falske positive) | 99,11 % |
| Alle blokkeringer | 44 (alle falske positive) | 96,10 % |

Dette er en avgrenset kontroll av en annen datakilde, ikke samme hele-sesong-validering på 99,67 % som FPL-Core-Insights. Tidligere sesonger kan ha andre leverandørdefinisjoner. De nye etikettene heter derfor `fbref_provisional`. Ingen tellekorreksjon er lært på 2025/26. Kilde-/feltvalget er vurdert på disse kontrollkampene; de er ikke en urørt modellholdout.

## Bruk videre

`results/{season}_labels.csv` inneholder historisk score, rekonstruert defcon, alternativ total og kvalitet per FPL-spiller/kamp. Historiske assists, bonus og alle andre komponenter beholdes. Manglende defcon gir manglende alternativ total. Keeper og null offisielle minutter gir null defcon; konfliktnøkler forblir sperret. Kvalitetsflagg og komponentvis maskering må brukes i trening.

Det er nå mulig å utvide treningsgrunnlaget med observasjonene som faktisk har etiketter. Vi bør ikke starte komplette sammenlignbare sesongbacktester før resterende hull er håndtert under en felles, eksplisitt evalueringsprotokoll. Å fjerne vanskelig koblede spillere fra spillerutvalget eller behandle deres mangler som null kan påvirke lagvalg og gi skjev evaluering. Særlig 2021/22 trenger utfylling fra en uavhengig kilde.

Den godkjente 2024/25-rekonstruksjonen beholdes som før, og 2025/26 beholder offisielle defensive poeng. Benchmarken er urørt. Ingen betaling eller abonnement er opprettet; eventuell senere datatilgang må holde brukerens totale ramme på 500 NOK.
