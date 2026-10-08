# Avgrenset arkivkontroll før FPL-frist

Dette er kildebelegg for neste featurefase, ikke en kvalifisert treningsvisning.
[Randdalf/fplcache](https://github.com/Randdalf/fplcache) lagrer bootstrap-snapshots
fire ganger daglig. Kildeinventaret viser år 2021–2026; dekning for alle runder
og de tidligste sesongene er ennå ikke kartlagt.

Ett faktisk snapshot fra `cache/2025/8/15/1252.json.xz` er hentet ved uforanderlig
commit `4aaec38e6b5f5ade8b63162a3678ce67148adb67`. Samme kildeversjons
`cache.py` og workflow er bevart. API-ens filhistorikk har én commit, med
forfatter-/committertid **2025-08-15 12:52:48 UTC**. Payloaden oppgir faktisk
GW1-frist **2025-08-15 17:30 UTC** og 685 unike spillere/Opta-koder. Før sesongstart inneholder prestasjonsfeltene videreført statistikk fra
2024/25: 395 spillere har minutter og 394 har poeng. Blant 511 sammenlignbare
spillere stemmer 504 minutt-/poengsummer, 510 måltall og 509 assisttall med
den bevarte 2024/25-inventaren. Retur-/overgangsnuller og enkelte kildeversjoner
avviker. Dette er ikke inneværende sesongs akkumulerte kampstatistikk.
Filnavnets tid er konsistent med
UTC-committen; denne kontrollen alene er ikke selvstendig attestasjon av
opprinnelig publisering eller collectorens klokke/tidssone.

Ingen modellfeatures eller treningsrader er aktivert på dette beviset. Neste
arbeid er å kvalifisere innhentingstid/publisering, velge rette snapshots før
hver frist, avstemme det faktiske spilleruniverset og ikke-deltakelseslabels,
og kontrollere feltenes definisjoner, preseason-videreføring/nullstilling og
kilderevisjoner gjennom alle sesongene. Historiske data
fra etter en frist brukes ikke som erstatning for det aktuelle snapshotet.

Fra repositoryroten:

```sh
python research/current/bootstrap_availability_pilot/fplcache/verify.py
```

`probe.json` låser kilde-URL-er og SHA-256. `verification.json` dokumenterer
bare de avgrensede kontrollene som faktisk er gjennomført.
