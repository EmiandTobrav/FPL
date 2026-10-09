# Siste assistinventar: West Ham–Southampton 2022/23

**Ett assistkrav lukkes: 11 237 → 11 236.** Nayef Aguerds assisttotal er null
fordi han scoret lagets eneste mål. Én ny spillerkamp er inputkomplett:
66 476 totalt, med uendrede 824 hele kamper.

Den siste inventarkampen, FPL 290, ESPN 638101, har 30 entydig koblede native
spillerkoder, ett mål og sluttresultat 1–0. En ny offentlig event-respons og
allerede innhentet datotavle lagres som eksakte bytes med URL/hash.
source_projection/predict.py er byteidentisk med den tidligere kvalifiserte
ESPN-parseren. Samme primærkodede navn, gjensidige spiller-ID-er, native
spillermål/selvmål, måltype, dato, klubber og sluttscore kontrolleres.
De publiserte 30 kontrollkampene gjenbrukes; ingen ny holdout hevdes.
Fouls-mappingens tidligere feil er bevart; ingen nye foul-/straffemålfelt brukes.

Alle nye målavgjørelser er unresolved. Den eksisterende aggregatoren gir kun
målscorerens null. **De øvrige 14 assistverdiene forblir tomme og kravene åpne**
med manglende årsaksfakta. Det gjenstår nå **ingen assistinventargap** i denne
restlisten. Dette betyr ikke at alle assister er avklart: 9 270 assistkrav
står åpne, og manglende foul-/berørings-/retur-/intensjonsbevis må fortsatt hentes.

De kumulative kildetilleggene dekker 24 kamper, 48 lag og 76 mål. Alle 7 618 tidligere
målavgjørelser, 68 009 kjente assisttotaler og tidligere kanoniske ID-er bevares.
Kun én ny verdi og 14 inventarstatus/provenienser endres; 775 233 andre ledger-
rader og alle rå/kildekolonner er uendret. FPL-uttrekksrettelsen og frosne
poenglabels/modeller bevares. Ingen ny assistregel eller poengberegning.

Fem tester består. **24 genererte filer** gjenskapes byteidentisk i isolert
replay: kildeparser, inventar, kumulative mål/identiteter/lagdekning og ledger.
Fra denne mappen: `python test_inventory.py` og `python reproduce.py`.
Alle små råsvar er versjonert lokalt; replay bruker ikke nettverk eller bootstrap.
Samlet kvalitet og treningsklarhet gjenstår.
