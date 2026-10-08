# Arbeidsrekkefølge for å fullføre harmoniseringen

Oppdatert 8. oktober 2026. Start fra [CURRENT.json](CURRENT.json), ikke fra
eldre avviks-, minutt- eller restlister. Dette er en arbeidsplan; ingen av
pilotene eller scoringsberegningene nedenfor er startet som del av publiseringen.

## Status og målegrunnlag

28 934 åpne feltkrav i 24 716 unike spillerkamper. 52 564 spillerkamper og
479 hele kamper har nødvendige inputfelt, av totalt 77 280 og 2 660.
Tilgjengelighet er ikke kvalifisert scoring. 569 151 tilgjengelige/markerte
eksterne kravrader har kvalitetsforbehold, samlet i 73 ikke-tomme felt-/sesonggrupper.
Dette er ikke 569 151 manuelle oppgaver. Den eldre kontrollmatrisen med
109 grupper bevares som historikk; 73 teller bare nåværende grupper med flagg.
Unionen av åpne krav og kvalitetsflagg er 77 214 unike spillerkamper.

[Per-felt-rest](followup_2026_10_08/bulk_followup/results/field_summary.csv),
[assistavhengigheter](priority/assist_groups.csv) og
[kvalitetsgrupper](priority/quality_groups.csv) er maskinlesbare.
Etter `python followup_2026_10_08/bootstrap.py` gjenskaper
`python priority/build.py` prioriteringsgrunnlaget fra øyeblikksbildet.

## Prioritert gjennomføring

| Prioritet | Felles problem og potensial | Avgrenset neste handling | Kriterium for skalering / ferdig |
|---|---|---|---|
| 1 | 21 manglende arkivkamper: 3 106 åpne krav i 593 spillerkamper, fordelt på ti felt | Samle tidligere kildeforsøk per kamp; velg 2–3 representative kamper og prøv bare en dokumentert ny eller tidligere ubenyttet kildevei. Undersøk flere tellere fra samme svar. Ta de tre ekstra kampene med manglende målhendelser i samme kampoversikt. | Verifisert kamp-/lag-/spillerkobling, eksplisitte observasjoner og kildebelegg. Hent resten av den støttede feltgruppen i én gjenopptakbar batch. Ikke gjenta den kjente mislykkede times_tackled-ruten. Potensialet er et tak, ikke lovet kildedekning. |
| 2 | Mållinjeklareringer: 3 540 krav; tidligere deling 2 598 bak fem manglende eksplisitte sesongtotaler, 587 arkiv-/identitetsgap, 355 positive ufordelte rester | Avklar først de fem lag-/sesongtilfellene som én kildepilot. Gjenbruk alle innhentede primærsvar og dokumenterte forsøk. Krev ny kildebegrunnelse før en tom rangering prøves igjen. | Bare eksplisitte kompatible totaler eller kvalifisert komplett hendelsesinventar kan brukes. Eksakt ikke-negativ sumavstemming kan gi null; fravær fra rangering eller positiv rest kan ikke. Arkivdelen overlapper prioritet 1. |
| 3 | Assists med positivt kildebelegg: 391 mål uten entydig pasningssertifikat og 1 028 mål med mellomliggende hendelser | Pilotér de vanligste hendelsesmønstrene samlet. Skill slettede/administrative rader, dueller og faktiske berøringer; verifiser mottaker, årsakskjede og gjeldende regelvilkår. Bevar alle rå rader og tvetydig rekkefølge. | Frys ny tolkning og kontrollplan før fasit. Tidsordnet kontroll; kjente utfall merkes regresjon, ikke holdout. Bruk konservative kandidatsett når disse kan bevises; tildel assist bare når hele den aktuelle ruten er kvalifisert. |
| 4 | Resterende store assistgrupper: særlig 827 mål med source-not-assisted-markør og 383 uten positivt sertifikat | Kjør små, representative piloter for hver årsaksgruppe, ikke én generell «ingen markør = ingen assist»-regel. Undersøk retur, forsvarskontakt, intensjon/mottakssted og eventuell hands-/dødballårsak med offisielt belegg. | Skaler bare undergrupper med dokumentert, testbar årsaksregel. Omtolkning av historisk Opta/FPL-markør alene er utilstrekkelig. Hold usikre kandidater og hele kampverdier adskilt. |
| 5 | Resterende taklinger og øvrige tellere | Behandle de 908 uparede mislykkede driblingene/balltapene som én skjemapilot, deretter de 221 kampinventarene. Gjenbruk arkivsporet for de 559 manglende identitetene. Ta SOT, CBI, foul/won/net tackles og keeperlokasjon per felles kilde-/sesongproblem. | Faktiske forsvarshendelser og komplett inventar kreves; ingen drible-/balltapsproxy. Skill eksplisitte konflikter fra fravær. De to smother-tilfellene og enkeltunntakene beholdes til egne gater er oppfylt. |
| 6 | Kvalifisert scoring, deretter fullstendig datasett | Lukk felles regel-/kvalitetsgater mens kildepilotene pågår. Når en gruppe hele kamper er kvalifisert, beregn avledede regelendringer og ranger bonus for samtlige deltakere i hver kamp. | Sesongriktige koeffisienter, avrunding/klipping, revisjoner og deltakerinventar må være verifisert først. Frigi bare komplette kvalifiserte kamper; låste labels/modeller/benchmark beholdes. Først etter samlet kvalifisering vurderes modelltrening. |

Dersom første kildepilot ikke gir relevant dekning, dokumenter konkret blokkering
og gå videre til neste store gruppe; ikke bruk hele arbeidsøkten på ett utilgjengelig
endepunkt. Manuell vurdering reserveres for unntak etter batchkontroll.

## Assistgrupper: betingede tak, ikke prognoser

Tallene beregnes fra dagens spiller–mål-avhengigheter etter alle kandidatavgrensninger.
«Kan lukkes» betyr **hvis alle gjenværende målbidrag i hele gruppen avklares**.
Berørte felt overlapper mellom grupper og skal ikke summeres.

| Gruppe | Mål | Berørte assistkrav | Kan lukkes ved full gruppeavklaring | Nye komplette spillerkamper | Nye komplette hele kamper |
|---|---:|---:|---:|---:|---:|
| Source-not-assisted-markør | 827 | 7 488 | 5 866 | 5 684 | 211 |
| Positivt målbelegg, ingen entydig pasning | 391 | 4 352 | 3 010 | 2 778 | 64 |
| Pasning med mellomliggende hendelser | 1 028 | 4 158 | 2 993 | 2 836 | 221 |
| Ingen positiv mål-/assistmarkør | 383 | 2 879 | 2 461 | 2 005 | 48 |
| Straffe | 185 | 2 449 | 1 782 | 1 635 | 33 |
| Selvmål | 228 | 890 | 715 | 703 | 43 |
| Direkte frispark | 23 | 308 | 199 | 194 | 4 |

583 assistkrav ligger i inventar-/identitetsgap og inngår ikke i målgruppene.
Det største teoretiske potensialet har ikke nødvendigvis lavest beviskostnad;
derfor kommer positivt kildebelegg før fraværsmarkører i den praktiske rekkefølgen.

## Regler som ikke kan omgås for å redusere tallene

- Historiske FPL-felt, minutter og eksplisitte nuller er fasit når regelkompatible.
  Eksterne kilder utfyller nye/manglende variabler og dokumenterte regelendringer.
- Rå FPL, godkjente keeperverdier, offisielle mål-/selvmålsrettelser og frosne
  kontrollsett bevares. Kjent fasit er aldri ny uavhengig validering.
- Ingen null fra fravær; ingen xG-imputering av storsjanseredninger. De 38
  gjenværende keeperobservasjonene er ikke 38 automatiske nuller.
- Behold uendrede historiske BPS-komponenter. Kvalifiser bare endrede ledd,
  gammel netto-taklingsklipping og kilderevisjoner før de trekkes fra/legges til.
- Bonus rangeres for hele kampen, med komplette deltakere og kvalifisert BPS.
  Les [globale regelgater](../fpl_authority/rule_dependencies.json); de er ikke
  ekstra feltkrav som kan summeres til restlisten.
- Tidligere avviste snarveier står fast: skuddbalanse for mållinjeklareringer,
  clearance+block-subsett med moteksempler, normaliserte arkivnuller uten belegg,
  ignorert fixture-filter i times_tackled-rangeringen og manglende gk_smother-total.

Hver batch rapporterer åpne feltkrav, unike berørte spillerkamper, komplette
spillerkamper og hele kamper, samt kildekvalitet og kvalifisert scoring separat.
Prioriteringsfiler oppdateres etter hver batch; gamle potensialtall brukes ikke
som neste arbeidskø.
