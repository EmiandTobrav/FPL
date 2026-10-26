SAMLET BERIKET FPL-MASTER, VERSJON 5
25. oktober 2026

player_matches.csv.xz har alle 190 124 PL-rader fra åtte sesonger,
2019/20–2026/27. Inneværende sesong går fortsatt gjennom GW7.
MASTER_ACTIVE.json peker på denne samlede filen.

Alle tidligere felt er bevart uendret, inklusive vær/sol med usikkerhet
rundt solnedgang, utlånsmarkeringer, kampbelastning, landskamper, kalender,
skadestatus, lagkameratfravær og dødballroller.

101 nye felt er lagt til:
- 69 pr_-felt: starter, innhopp og nullminutter over siste 3/5/10 registrerte
  historikkegnede kamper, varighet ved start og innhopp, 60-minuttersandeler,
  sekvenser, rolleendringer og separat forrige-sesong-oppsummering.
- 32 ds_-felt: beskrivende angreps- og innslippsstyrke for lag/motstander,
  justert for tidligere motstand og hjemme-/borteforhold, med tellinger og
  tydelig merket nøytral prior ved sesongstart.

Begge lag bruker bare tilgjengelig historikk strengt før av_forecast_at.
Tilgjengeligheten viderefører avspark+24t-proxyen; faktisk historisk
mottakstid og statistikkversjon er ikke fullt dokumentert.
pr_strict_historical_qualified og ds_strict_historical_qualified er False.
To tidligere faktiske frister i 2021/22 GW18 og 2024/25 GW15 videreføres.

Starter bruker kvalifisert native_starts, aldri en 60-minuttersregel.
Null minutter skiller ikke ubrukt benk fra fravær. Utlåns-/utenfor-PL-nullene
brukes ikke som spillerhistorikk. Korte vinduer og tomme betingede
gjennomsnitt er merket. Sesonger blandes ikke i de rullerende vinduene.

Styrke er målbasert og ikke en kalibrert prognose. Innslippsindeks over 1
betyr svakere forsvar. Alle klubber starter nøytralt hver sesong.
XG brukes ikke i de nye indeksene før definisjon og fullstendige lagtotaler
er kvalifisert. Eksisterende xG-felt og kvalitetsmarkeringer beholdes.

Nøkkel: season/fixture/code. Ingen cup-/landskamper eller nye spillerrader
er lagt til. 2 730 fysiske PL-kamper; 159 881 historikkegnede observasjoner
og 30 243 markerte strukturelle nuller, uendret fra forrige versjon.

loader.py iter_records(view='observations') gir alle felt.
view='history' utelater strukturelle nuller og retrospektivt vær som standard.
before og include_weather fungerer som tidligere.
Metode, feltliste og kontroller: datasets/fpl_role_strength_v1/README.txt.
coverage.csv og verification.json følger masterarkivet.
Ingen modeller er trent eller endret; treningspekeren ACTIVE.json er bevart.
