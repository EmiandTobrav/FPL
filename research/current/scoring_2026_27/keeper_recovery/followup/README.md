# Oppfølging: 18 av 57 avklart

7. oktober 2026. Alle 57 keeper-/kampobservasjoner er hentet på nytt fra Premier
Leagues spillerstatistikk. Spillerens Opta-kode, én aktiv opptreden og kampkobling
kontrolleres. 57/57 innhentinger lyktes. Råresponsene ligger i
`primary_raw.jsonl.gz`, med URL og SHA-256 i `primary_sources.json`.
`identity_evidence.json.gz` bevarer relevante spiller- og kampkatalograder.

## Godkjente løsninger

- Seks eksplisitte primærtall: Martínez 1 og Sánchez 2 mot Aston Villa
  1. desember 2024; Leno 1 og Forster 3 i Tottenham–Fulham samme dag;
  Darlow 1 mot Bournemouth og Dúbravka 3 mot Manchester City 22. april 2026.
  Dúbravkas primærtall 3 bekrefter skuddrekonstruksjonen og overstyrer arkivets
  separate keeperfelt 2. Den opprinnelige konflikten bevares.
- Fem nuller følger av eksplisitt null redninger i både låst FPL og FotMob:
  Schmeichel mot Sheffield United 6. desember 2020; Kepa mot Aston Villa,
  Pickford mot Tottenham, Ederson mot Liverpool og Navas mot Wolves i april 2023.
  Fravær av et primærfelt brukes ikke som nullbevis.
- Tre komplette redningsinventarer: De Gea 0 mot Manchester City 7. desember
  2019, McCarthy 1 mot Aston Villa 22. februar 2020 og Ward 2 mot Chelsea
  27. august 2022. Hver registrerte redning har én entydig skuddpartner i samme
  periode. Antall redninger stemmer med både ny primærstatistikk og FotMob.
  McCarthys tidligere sperre brukte en sum av utelatte storsjansefelt som null;
  denne summen er ikke et eksplisitt motbevis. De Geas øvrige skuddantall har
  fortsatt et avvik, men alle fire redningene er identifisert uten storsjansemerke.
- Fire tellinger fra komplett skuddliste og skytternes blokkerte skudd:
  Olsen 0, Pickford 0 og Onana 1 den 1. desember 2024, samt Sels 0 mot Fulham
  15. mars 2026. Alle skytternes skudd- og måltall må stemme. Et ukjent
  blokkeringsmerke løses bare når skytterens samtlige relevante skudd entydig
  er blokkerte eller ingen er blokkerte. Olsen får lagets telling minus
  Martínez' eksplisitte telling. Dette krever ikke gjetting av keeperbyttets klokke.

**Ward:** Historisk FPL har én redning, mens både oppdatert Premier League og
FotMob har to. De to merkede storsjanseskuddene har hver sin keeperredning.
Den nye tellingen er derfor godkjent som retrospektiv hendelsesstatistikk;
FPL-avviket er markert i `decisions.csv`. Historiske FPL-poeng endres ikke her.

**Sels:** Den manglende flaggraden gjelder Basseys ikke-storsjanse. Alle seks
Fulham-skudd stemmer nå med skytternes tellinger; de to andre type-15-skuddene
har eksplisitte blokkeringsmerker. Det eldre råhendelsesarkivet har en slettet
Bassey-hendelse og er ikke en komplett fasit for det nyere skudduttrekket.

`decisions.csv` har alle 18 vedtak og maskinlesbare bevis. For nye godkjenninger
bevares `original_reason` og `resolution_method` i hovedfilen.

## Fortsatt uløst: 39 observasjoner i 23 kamper

37 observasjoner gjelder de samme 21 kampene som mangler i hendelsesarkivet.
Fem andre keepere i disse kampene er nå avklart gjennom null-redningsgrensen.

To kildekonflikter gjenstår:

- Ramsdale, Bournemouth–Aston Villa 1. februar 2020: fire offisielle redninger,
  men bare tre komplette skudd/redningspar. Aston Villa har 18 skudd i
  spillerstatistikken, mens hendelseslisten har 17. Den manglende avslutningen
  kan ikke antas å være en ordinær sjanse.
- Sánchez, Chelsea–Tottenham 19. mai 2026: arkivets keeperfelt sier én
  storsjanseredning, skuddlisten sier null, og den nye primærresponsen utelater
  feltet. Utelatelsen er ikke et eksplisitt null og løser derfor ikke konflikten.

De 39 godkjente feltene forblir tomme. Ingen imputering eller xG-grense brukes.
For å fullføre trengs en supplerende eksport for de 21 kampene og kildeavklaring
for de to konfliktene. En offentlig eksport med eksplisitte storsjanse- og
blokkeringsmerker er ikke funnet for restlisten.

## Kontrollerte alternative kilder

FotMobs gamle endepunkt ga 404; det oppdaterte `/api/data/matchDetails` ga
403 ved nettverkstunnelen. Ingen tilgangssperre ble omgått. Premier Leagues
SDP-kommentarendepunkter v1/v2 ga 404 for kontrollkampen fra 2024/25.
GitHub-arkivene CleveHan/Soccer, jmlee8939/whoscored_crawling,
BVBtm86/WhoScored-Events-Data og Ali-Hasan-Khan/Scrape-Whoscored-Event-Data ble
kontrollert; ingen komplett relevant hendelseseksport for restlisten ble funnet.
jakeyk11/football-data-analytics opplyser at WhoScored-dataene ikke følger repoet.
Ingen bestilling, abonnement eller henvendelse til andre er sendt. Kostnad 0 kr.

## Gjenkjøring

Kjør `recover.py`, deretter `reconcile_followup.py`. Oppfølgingen bruker bare
versjonerte filer og pandas. `test_followup.py` tilfører ti tester; totalt tjue
transformasjonstester består. Den tidligere kontrollen av 52 eksplisitte
2026/27-tellinger er uendret; dette er ikke en ny uavhengig leverandørkontroll.
