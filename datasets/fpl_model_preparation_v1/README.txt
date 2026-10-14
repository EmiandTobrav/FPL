Steg 1 og 2: tidsregler og historiske features

operational_proxy_v1: prognose 90 minutter før første faktiske avspark i runden; historikk tilgjengelig 24 timer etter siste avspark i observasjonen. Dette er en regelbasert tilnærming, ikke verifiserte FPL-frister eller publiseringsvintager. conservative_v1 beholder den gamle -7/+7-dagersregelen som kontroll.

Begge filer har samme spiller–runde-utvalg og uendrede H1/H3/H6-poengmål som v1. Baseline: 21 features; utvidet: historisk spredning, formtrender, starter/spilletid, tidsvektede snitt, kjente xG/xA/CBI/taklinger/recoveries, og omregnede historiske poeng. Pris, lag og posisjon hentes fra siste tidligere tilgjengelige observasjon; ingen framtidig utfylling. Motstander og framtidig kampkalender utelates fordi historiske kalender-snapshots ikke er dokumentert.

target_h1/h3/h6_available_at angir når HELE utfallet kan brukes til trening. H3/H6 må ikke trenes på før siste kamp i hele horisonten er tilgjengelig. Utsatte runder håndteres med tidsstempler. Oppdatering bruker streng < forecast_at.

split er gammel referansemetadata. Walk-forward velger tidsperioder ved kjøring. Manglende framtidige rader blir ikke nuller. Det observerte spilleruniverset er ikke en verifisert kjøpbar før-frist-tropp. Nye NaN/None beholdes; skalering, imputering, kategori-encoding og datadrevet featurevalg tilhører neste steg og må læres på treningsdelen. Ingen modell er trent.

Bruk loader.py for baseline eller extended og tidsbaserte trenings-/prediksjonsutvalg. schema.json beskriver feltene og kontrakten. Kildedatasettet er uendret.
