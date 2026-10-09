# Direkte Opta-forventningsstatistikk: HTTP 403, kildeforsøk avsluttet

En fryst prøve planla tre kamper: 2019/20 kamp 1, 2022/23 kamp 5 og
2026/27 kamp 1. Første forespørsel til `matchexpectedgoals` ble avvist med
**HTTP 403**. Responsbytes, URL og SHA-256 er bevart. De to andre kampene
ble ikke forsøkt etter avvisningen, og ingen annen klientnøkkel ble brukt.

Klientoppsettet kommer fra Pannadatas offentlige innhentingskode.
Endpointreferansen i planen er uoffisiell klientdokumentasjon; den beviser
ikke at denne tilgangen har rett til forventningsstatistikken. Ingen
xG-/xA-verdi er innhentet eller anvendt, og ingen krav er lukket.

Ruten har en dokumentert tilgangshindring og skal ikke prøves om igjen med
uendret tilgang. `python research/current/training_dataset/opta_expected_goals_pilot/verify.py`
kontrollerer den fryste planen og avvisningen offline, uten nye nettforespørsler.
Dette er en HTTP-avvisning fra datakilden, ikke en avvisning fra verktøyets
automatiske godkjenningskontroll.
