# De to siste straffemålkravene lukket med offisiell spilleridentitet

**11 260 → 11 258 åpne krav.** To manglende verdier i Arsenal–Leeds 2022/23,
FPL-kamp 281, fylles: Gabriel Jesus (205651) ett straffemål, Granit Xhaka
(84450) null. Andre gap står igjen: ingen nye komplette spillerkamper eller
hele kamper. 66 458 spillerkamper og 824 hele kamper er inputkomplette.

Ny separat identitetsversjon gjenbruker de samme 119 fryste ESPN-responsene og
44 mål-/30 kontrollkamper. Eksakt normalisert fullt navn fra allerede
kvalifisert primærroster med offisiell spillerkode avklarer seks gamle
målvektorvetoer. Koblingen krever faktisk historisk klubb, entydige gjensidige
ID-er og konsistens gjennom sesongen; scoringsutfall brukes ikke til identitet.
Alle 74 komplette målvektorer avstemmes mot native spillermål, selvmål og score.

842 straffemålkontroller i 30 kamper, inkludert 15 positive verdier, og 2 076
referansesammenligninger på 2 059 unike feltnøkler har null avvik. Foul-mappingen
har fortsatt fem referanseavvik på tre nøkler og holdes tilbake for alle spillere.
Gamle mislykkede kontroller og original kildebatch forblir uendret. Kontroller
har mulig felles kildeopphav og tidligere sett fasit; ingen uavhengig holdout.

Bare to manglende ledgerverdier endres; alle 775 246 øvrige rader og native
kolonner bevares. Kollektiv kvalitetsstatus er fortsatt ventende; nye BPS,
bonus, poenglabels, features og modelltrening er utsatt.

Fem tester består; 16 genererte filer gjenskapes byteidentisk i isolert offline
replay. Fra denne mappen: `python test_acquisition.py` og `python reproduce.py`.
Replay gjenbruker det versjonerte råarkivet i `../espn_gap_acquisition/` og
kontrollerer alle eksterne avhengigheters hash i `dependencies.json`.
