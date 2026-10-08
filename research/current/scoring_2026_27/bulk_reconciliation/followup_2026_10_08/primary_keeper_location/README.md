# Direkte primære keeperlokasjoner – 8. oktober 2026

Denne batchen lukker **14 feltkrav og 14 hele inputkamper**. Gjeldende rest blir
**14 893 krav**, 13 731 berørte spillerkamper, 63 549 inputkomplette
spillerkamper og 766 inputkomplette kamper. Dette er inputkvalifisering;
poeng og trening har egne gater.

## Kilde og komplett inventar

393 råsvar dekker sesongtotal og samtlige 381 FPL-opptredener for de tolv
keeperne bak de siste 16 lokasjonskravene. 39 tidligere svar gjenbrukes;
354 offentlige Premier League-svar er innhentet med begrenset rate.
`plan.csv`, `protocol.json` og den opprinnelige ledgerpekeren ble lagret før
kontroll av de øvrige keeperne. Kellehers allerede innhentede 37 kamper var
den eksplorative piloten; dette er ingen urørt eller uavhengig leverandørtest.

Primærens `saved_ibox` og `saved_obox` behandles hver for seg. En utelatt
matchverdi er bevist null bare når alle eksplisitte ikke-negative matchverdier
uttømmer den eksplisitte sesongtotalen, og hele native opptredensinventaret
er med. Både primær spiller-ID, Opta-ID, kampkode, minutter og opptredener
kontrolleres. Direkte lokasjonstellinger kan ikke overstige native FPL-redninger.
Ingen lokasjon er beregnet som totale redninger minus inside-redninger.

## Populasjonskontroll og beskyttede avvik

Alle **746 kjente inside-/outside-verdier stemmer**: 381 inside og 365 outside.
Kontrollene gjenbruker godkjente og tilgjengelige eksterne lokasjonsverdier
med delt Opta-opphav; de er ikke 746 uavhengige native FPL-kontroller.
Minstekrav per keeper er ti kjente verdier i hvert lokasjonsfelt, fem positive
outside-verdier og ingen lokasjonsavvik. Ett avvik sperrer hele keepergruppen.

Elleve keepere kvalifiseres. **Sánchez sperres** fordi primæren har fem minutter
i kamp 47 mot FPLs fire, og 3 041 sesongminutter mot FPLs 3 040. Kravene i
kamp 33 og 323 forblir åpne. Ingen kontrollgate er senket etter sammenligningen.

De 14 nye outside-verdiene er alle nuller bevist ved separat, eksakt
sesonguttømming. Native FPLs totale redninger beholdes uendret. Primærens
redningstotaler har egen audit i `results/native_save_audit.csv`; forskjeller
brukes aldri til lokasjonsberegning. Tidligere skuddinventarer, keeperdata,
konflikter, scoringsversjoner og mislykkede CBI-gater bevares.

## Reproduksjon

Fra repositoryroten:

```sh
python research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/primary_keeper_location/reproduce.py
python -m unittest discover -s research/current/scoring_2026_27/bulk_reconciliation/followup_2026_10_08/primary_keeper_location -p test_locations.py
```

Syv tester består. Tolv resultatfiler er gjenskapt byteidentisk i separat
kopi uten nettverk. Råfiler, kilde-URL-er og fil-/rå-SHA er lagret i
`inputs/source_manifest.csv`; manifestet låser alle innganger og utganger.
Kjør `reproduce.py`, ikke en ny innhenting eller planlegging, for å gjenskape
batchen. Det kanoniske treningsdatasettet har fortsatt åpne gater.
