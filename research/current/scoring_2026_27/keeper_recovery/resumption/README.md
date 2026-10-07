# Gjenopptak 7. oktober 2026: 38 keeperobservasjoner gjenstår

**5 343 av 5 381 er avklart (99,29 %).** Både 2024/25 og 2025/26 er nå
dekket. Historiske poeng, BPS, bonus, modell og benchmark er ikke endret.
Full harmonisering er fortsatt sperret.

## Nytt bevis: Sánchez 19. mai 2026

Premier Leagues offisielle kampstatistikk for Chelsea–Tottenham, kamp 125155,
oppgir eksplisitt `big_chance_saves=1` og `saves=2` for Chelsea.
Sánchez er lagets eneste aktive keeper i den fryste deltakerpopulasjonen,
spilte 90 minutter, og både hans offisielle spillerstatistikk, historiske
FPL-telling og FotMob oppgir to redninger. Lagets ene storsjanseredning kan
derfor tilordnes ham entydig. Det tidligere eksplisitte keeperfeltet i
hendelsesarkivet sier også én.

Den eldre skuddrekonstruksjonen sier null. Den bevares i
`candidate_big_chance_saves`; `original_reason=explicit_count_conflict` bevares.
Dette er en dokumentert kildeavklaring med offisiell kampstatistikk, ikke en
antakelse om at et utelatt spillerfelt betyr null. `decisions.csv` bevarer
bevisene. Metoden avviser keeperbytter, manglende teller, redningsavvik og
uenighet mellom det eksplisitte lagfeltet og det eksplisitte arkivfeltet.

## Nytt kildegrunnlag og usikkerhetsgrenser

Alle 23 kamper fra den opprinnelige restlisten er hentet fra
`https://footballapi.pulselive.com/football/stats/match/{id}`.
`sources.json` inneholder URL og SHA-256; `raw/` bevarer svarene.
Ved gjenkjøring kontrolleres hash, kamp-ID, sesong, dato og begge lag mot
den tidligere identitetskontrollerte køen og keeperpopulasjonen.

For de 38 gjenstående keeperobservasjonene er et konservativt intervall lagret
i `unresolved_bounds.csv`. Nedre grense er null; øvre grense er keeperens
verifiserte antall redninger, begrenset av motstanderens eksplisitte antall
store sjanser brent når dette finnes. Utelatt teller gir ingen ny begrensning.
Dette strammer inn intervallet for **16 observasjoner**. Det velges ingen
verdi innenfor intervallet, og alle 38 godkjente felt forblir tomme.
Dette er grenser betinget på at de offisielle tellingene er korrekte;
det er ikke statistiske konfidensintervaller eller verifisert bonus.

**37 observasjoner i 21 kamper** trenger fortsatt hendelser med
storsjansemerker. **Ramsdale mot Aston Villa 1. februar 2020** mangler fortsatt
én skuddpartner. Hans utelatte primære storsjansefelt gir ikke nullbevis.

## Kontroll av arkivhullet

Den opprinnelige fixture- og hendelseseksporten ble lastet ned på nytt.
Begge samsvarer med SHA-256 i `../source_manifest.json`:
fixtures `9dcdffe83ae68395b299c99bb867e644140a43af14d28ae1a90861cf343d208f`,
events `a69184e1c0d35ed39e1146b748f0ff3b649750bb1d52624286406e0cacd4b6f2`.
Hendelsesfilen har henholdsvis 376, 373 og 370 kamper for 2019/20,
2020/21 og 2022/23. Ingen ekstra ukoblede kamper finnes i de versjonerte
hendelses- eller skudduttrekkene for disse sesongene. Dette støtter at hullet
ligger i arkivet; en enkel datokoblingsrettelse løser det ikke.

Det nye søkeresultatet `moosterwegel/whoscored-opta-events-scraper` ble også
kontrollert. Dets README sier eksplisitt at kampdata ikke følger repoet.
Det er derfor ingen supplerende hendelseseksport. Ingen tilgangssperrer ble
omgått, ingen henvendelser sendt og ingen betalte kilder brukt.

## Gjenkjøring og neste steg

Kjør `recover.py`, `reconcile_followup.py`, deretter
`reconcile_match_totals.py`. Det siste steget kan kjøres flere ganger uten
å endre resultatet. Kjør deretter `python -m unittest discover -s
research/current/scoring_2026_27/keeper_recovery -p 'test_*.py'`.
25 tester består, inkludert fem nye tester av lagtilordning og intervaller.

De resterende intervallene kan brukes i en senere følsomhetsanalyse av
bonus, men først må øvrige BPS-komponenter og assistforutsetninger være
tilstrekkelig avklart for alle spillerne i hver kamp. Original historisk BPS
er ikke en gyldig erstatning for en slik 2026/27-grunnberegning.
