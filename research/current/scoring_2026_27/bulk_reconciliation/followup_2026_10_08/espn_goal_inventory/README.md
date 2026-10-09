# Komplette målinventarer fra allerede kvalifiserte kampresponser

**20 assistkrav lukkes: 11 257 → 11 237.** 16 nye spillerkamper er inputkomplette:
66 475 totalt, med uendrede 824 hele kamper. Ingen ny scoring eller trening.

23 kamper har nå 75 komplette mål og 46 avstemte laginventarer. De gjenbruker
samme fryste ESPN-responser, primærkodede spillerkoblinger og kvalifiserte
måltellere fra ../espn_primary_identity. Det innhentes ingen ny stor kildebatch.
Alle målscorere, selvmål, spillermålvektorer og sluttresultater stemmer med FPL.
Kildekontrollen gjenbruker de publiserte native målvektor-/identitetskontrollene;
842 straffemålfelter er tidligere sjekket i 30 kamper, ikke 842 assistkontroller.
Dette er samme kildegrunnlag og tidligere sett data, ikke uavhengig holdout.

Alle nye målavgjørelser forblir **unresolved**. Ingen ESPN-assists, kommentarfoul,
ny assistregel eller historisk generell assisttotal kopieres. Den eksisterende
aggregatorens scorer-selvutelukkelse gir 20 trygge nuller når alle relevante
lagmål er scoret av spilleren selv. Andre spillere beholder ukjente bidrag.
Selvmål krediteres motstanderlaget ut fra scorerens faktiske native klubb.

**548 tidligere inventargap har nå komplette mål, men er fortsatt åpne
assistkrav**, klassifisert som regelomregning med manglende årsaksbevis.
Denne flyttingen er ikke telt som 548 lukkede feltkrav. 15 inventarkrav står
igjen, alle i West Ham–Southampton 2022/23 kamp 290. Alle 7 543 tidligere målavgjørelser og 67 989 kjente assisttotaler bevares.
Bare 20 verdier fylles; 548 åpne krav får oppdatert status/proveniens.
774 680 øvrige ledger-rader og alle kildekolonner forblir uendret.

Manglende arkiv-ID-er får eksplisitte kanoniske FPL-nøkler: fpl_fixture,
fpl_team og fpl_player med faktisk sesong/kamp/lagkode/spillerkode. Eksisterende
ID-er bevares. ESPN-play-ID-er lagres som negative heltall i eget kilderom;
ingen oppdiktet Opta-ID brukes. Deltakere uten ESPN-kobling beholder ukjent
ESPN-ID, men må ha eksplisitt native null på mål og selvmål. Alle faktiske
kildescorere er entydig koblet. CURRENT peker til de nye deltakere/inventarer,
assisttotalene og komplett klassifisering for arbeidskøen.

Kjør `python test_inventory.py` og `python reproduce.py` fra denne mappen.
Fem tester består; 17 genererte inventar-/resultatfiler gjenskapes byteidentisk offline.
Replay gjenoppretter eksakte kildebytes fra det eksisterende versjonerte
råarkivet og gjenskaper koblinger, inventarer og summer i en isolert kopi.
Gamle mislykkede kilde-/regelstudier, native FPL-rettelsen og modeller bevares.
Samlet kvalitet og treningsklarhet gjenstår.
