# Build report — jao_core_v1 (Stage 1 workbook)

Source: `202603_Core Static Grid Model_External.xlsx` sha256 fcf99279135433f3bf6f9dd587418de1bd289039c82cc0cf2ce54f2d48613d4e

Coordinates: `2026-03-16_Core_SGM_publication.html` sha256 c41b18cfbb1f0d1d0b82717a33c0870ec184d7d978bc333760e0b418c85b75e6

S_base = 100.0 MVA; kV base = nominal per level (110/220/380/750); capacity = sqrt3·kV·mean(ratings)/1000; UNRATED = 9999.0 MW

**MW rating voltage: JAO operating voltage (380→400 kV, 220→225 kV)** — Capacity_MW = √3·U_op·Ī/1000; p.u. base stays nominal (user decision 2026-09-13, notes/10).


**DC power-flow inputs: R = 0 and B = 0 written for every line, tie-line and transformer** (user decision 2026-09-13; JAO's R and B are still in row_decisions/raw; reason: ENR builds its PTDF from -imag(Ybus), which would carry line charging into the DC matrix — notes/09).

## Counts

- raw rows: Lines 2632, Tielines 333, Transformers 526
- written: Lines 2596, Tielines 148, Transformers 466, DCLines 1, Nodes 1763
- buses with coordinates: 1592 / 1763
- zones: {'PL': 147, 'BE': 84, 'FR': 612, 'RO': 109, 'HU': 43, 'CZ': 42, 'DE': 552, 'NL': 42, 'SI': 20, 'HR': 19, 'AT': 57, 'SK': 36}
- kV levels: {220: 974, 380: 778, 110: 10, 750: 1}
- AC components (union-find preview): 1; sizes: [1763]
- buses pruned (only referenced by de-duplicated rows): 3
- zone consistency: 0 buses zoned against their intra-TSO lines (checked); tie-line-only buses (zone from comment): 55
- alias evidence rows from shared EICs: 7 (alias_evidence_from_eic_v11b.csv)
- zone merge applied (reduction only): {'LU': 'DE'}
- homonym station names split by coordinates: 1 → ST. PETER: ['AT', 'DE']
- isolated fragments excluded (no path to main island): 15 fragments, 32 buses — listed below

## Isolated fragments excluded (bus lists)

- [3] DONZENAC_220, FEROUGE_220, TALAMET_220
- [3] BRODE_220, DUVIGNEAU_220, PIQUAGE A DUVIGNEAU_220
- [2] GUETERSLOH_220, HESSELN_220
- [2] SALZACH_220, SALZBURG_220
- [2] FONT (LA)_220, RIORGES_220
- [2] ANOULD_220, ETIVAL_220
- [2] BARJAC_220, CROISIERE_220
- [2] AVALLON_220, JOUX-LA-VILLE_220
- [2] MUREAUX (LES)_220, NOUROTTES_220
- [2] CAEN_220, RANVILLE_220
- [2] SACLAY (PLATEAU)_220, VILLERAS_220
- [2] MONTCROISETTE_220, VENDIN_220
- [2] CRETAINE_220, TOLBIAC_220
- [2] BOULE (LA)_220, PUTEAUX_220
- [2] HOLLANDSE KUST NOORD LANDSTATION_380, WIJK AAN ZEE_380
- representative buses (rule central_degree380, overrides {'NL': 'KRIMPEN AAN DEN IJSSEL_380'}): AT=DUERNROHR_380; BE=GRAMME_380; CZ=HRADEC VYCHOD_380; DE=ROMMERSKIRCHEN_380; FR=CHESNOY (LE)_380; HR=MELINA_380; HU=MARTONVASAR_380; NL=KRIMPEN AAN DEN IJSSEL_380; PL=ROGOWIEC_380; RO=BUCURESTI SUD_380; SI=BERICEVO_380; SK=KRIZOVANY_380

## Actions per sheet

- Lines / COUPLER: 3
- Lines / EIC_DUP_DROPPED: 8
- Lines / EXCLUDE: 3
- Lines / EXCLUDE_ISOLATED: 20
- Lines / KEEP: 2603
- Lines / KEEP_UNRATED: 21
- Lines / MERGE_ENDPOINTS: 2
- Tielines / COUPLER: 12
- Tielines / DROP_EXTERNAL: 54
- Tielines / EIC_DUP_DROPPED: 99
- Tielines / EIC_DUP_DROPPED_SPELLING: 7
- Tielines / EXCLUDE: 11
- Tielines / KEEP: 254
- Tielines / TO_DCLINES: 2
- Transformers / EXCLUDE: 60
- Transformers / KEEP: 466

## Every non-KEEP row

- [Lines] MERGE_ENDPOINTS: 'Eemshaven-Robbenplaat220 W' (TENNET NL) — R=X=0 (length 0.04 km): singular in DC-PF; ROBBENPLAAT_220 merged into EEMSHAVEN_220
- [Lines] MERGE_ENDPOINTS: 'Eemshaven-Robbenplaat220 Z' (TENNET NL) — R=X=0 (length 0.04 km): singular in DC-PF; ROBBENPLAAT_220 merged into EEMSHAVEN_220
- [Lines] COUPLER: 'Y-Herbertingen (-Hoheneck - Metzingen) HERBTG W' (AMPRION GMBH) — both ends are the same bus (HERBERTINGEN_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Lines] EXCLUDE: 'Y-Schwanheim (-Bischofsheim -Kriftel) TREBUR S' (AMPRION GMBH) — blank Voltage_level
- [Lines] EXCLUDE: 'Reporyje - Milin' (CEPS) — blank reactance X — no value can be assigned
- [Lines] EXCLUDE: 'Milin - Kocin' (CEPS) — blank reactance X — no value can be assigned
- [Lines] COUPLER: 'Mehrum - Mehrum/N T421' (TENNETGMBH) — both ends are the same bus (MEHRUM_220): TSO-to-TSO busbar coupler inside one station, collapsed
- [Lines] COUPLER: 'Mehrum - Mehrum/N T422' (TENNETGMBH) — both ends are the same bus (MEHRUM_220): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] COUPLER: 'Brunsbüttel - Brunsbüttel 949' (50HERTZ) — both ends are the same bus (BRUNSBUETTEL_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] COUPLER: 'Krümmel - Krümmel 993' (50HERTZ) — both ends are the same bus (KRUEMMEL_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] COUPLER: 'Krümmel - Krümmel 994' (50HERTZ) — both ends are the same bus (KRUEMMEL_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] COUPLER: 'Herbertingen - Herbertingen UEB 41HE' (AMPRION GMBH) — both ends are the same bus (HERBERTINGEN_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] COUPLER: 'Herbertingen - Herbertingen UEB 42HE' (AMPRION GMBH) — both ends are the same bus (HERBERTINGEN_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] TO_DCLINES: 'Oberzier - Lixhe ALEGRO' (AMPRION GMBH) — HVDC row: X=0.05 ohm would be a near-short as AC; capacity from AC formula — FLAG: confirm DC rating
- [Tielines] DROP_EXTERNAL: 'Laufenburg - Tiengen ANDLSB' (AMPRION GMBH) — far end outside Core (CH-DE); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Lienz - Auronzo 261' (APG) — far end outside Core (AT-IT); hybrid design keeps NTC there
- [Tielines] EXCLUDE: 'Meiningen - Ruethi 407' (APG) — both endpoints unknown (not in any intra-TSO line); comment='Tieline between AT-CH.'
- [Tielines] EXCLUDE: 'Meiningen - Ruethi 408' (APG) — both endpoints unknown (not in any intra-TSO line); comment='Tieline between AT-CH.'
- [Tielines] DROP_EXTERNAL: 'Nauders - Pradella 429' (APG) — far end outside Core (AT-CH); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Nauders - Pradella 430' (APG) — far end outside Core (AT-CH); hybrid design keeps NTC there
- [Tielines] COUPLER: 'Schifflange PST-Schifflange' (Creos) — both ends are the same bus (SCHIFFLANGE_220): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] DROP_EXTERNAL: 'Divaca - Redipuglia' (ELES) — far end outside Core (SI-IT); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Divaca - Padriciano' (ELES) — far end outside Core (SI-IT); hybrid design keeps NTC there
- [Tielines] EXCLUDE: 'Y – SANEM (– AUBANGE – SCHIFFLANGE) 220.512' (ELIA) — both endpoints unknown (not in any intra-TSO line); comment='BE (SOTEL) Part Tie-line to LU'
- [Tielines] DROP_EXTERNAL: 'GEZELLE – NEMO CONVERTOR STATION 380.114' (ELIA) — far end outside Core (BE-UK); hybrid design keeps NTC there
- [Tielines] TO_DCLINES: 'ALEGRO HVDC' (ELIA) — HVDC row: X=0.05 ohm would be a near-short as AC; capacity from AC formula — FLAG: confirm DC rating
- [Tielines] DROP_EXTERNAL: 'Mostar - Konjsko' (HOPS) — far end outside Core (BA-HR); hybrid design keeps NTC there
- [Tielines] EXCLUDE: 'Prijedor - Sisak' (HOPS) — both endpoints unknown (not in any intra-TSO line); comment='Tie-line to BA (NOSBiH) '
- [Tielines] DROP_EXTERNAL: 'Ugljevik - Ernestinovo' (HOPS) — far end outside Core (BA-HR); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Ernestinovo-S. Mitrovica' (HOPS) — far end outside Core (HR-RS); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Mostar - Zakucac' (HOPS) — far end outside Core (BA-HR); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Prijedor - Meduric' (HOPS) — far end outside Core (BA-HR); hybrid design keeps NTC there
- [Tielines] EXCLUDE: 'Gradacac - Dakovo' (HOPS) — both endpoints unknown (not in any intra-TSO line); comment='Tie-line to BA (NOSBiH) '
- [Tielines] EXCLUDE: 'Tuzla - Dakovo' (HOPS) — both endpoints unknown (not in any intra-TSO line); comment='Tie-line to BA (NOSBiH) '
- [Tielines] EXCLUDE: 'Trebinje - Plat 1' (HOPS) — both endpoints unknown (not in any intra-TSO line); comment='Tie-line to BA (NOSBiH) '
- [Tielines] DROP_EXTERNAL: 'Tiszalok - Mukachevo' (MAVIR) — far end outside Core (HU-UA); hybrid design keeps NTC there
- [Tielines] COUPLER: 'Heviz - Zerjavinec' (MAVIR) — both ends are the same bus (ZERJAVINEC_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] COUPLER: 'Bekescsaba - Nadab' (MAVIR) — both ends are the same bus (NADAB_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] DROP_EXTERNAL: 'Kisvarda - Mukachevo' (MAVIR) — far end outside Core (HU-UA); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Szabolcsbaka - Mukachevo' (MAVIR) — far end outside Core (HU-UA); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Sandorfalva - Subotica' (MAVIR) — far end outside Core (HU-RS); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Szabolcsbaka - Zahidno Ukrainska' (MAVIR) — far end outside Core (HU-UA); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'RZESZOW-KHMELNYTSKYI' (PSE) — far end outside Core (PL-UA); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'ELK BIS-ALYTUS' (PSE) — far end outside Core (PL-LT); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'ELK BIS-ALYTUS' (PSE) — far end outside Core (PL-LT); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'ZAMOSC-DOBROTWOR' (PSE) — far end outside Core (PL-UA); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'SLUPSK-STARNO' (PSE) — far end outside Core (PL-SE); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'LIT 400KV N0 1 RONDISSONE - ALBERTVILLE' (RTE) — far end outside Core (IT-FR); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'LIT 400KV N0 2 RONDISSONE - ALBERTVILLE' (RTE) — far end outside Core (IT-FR); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'LIT 400 kV VICH-BAIXAS' (RTE) — far end outside Core (ES-FR); hybrid design keeps NTC there
- [Tielines] EXCLUDE: 'LIT 400 kV HERNANI-ARGIA (BAYONNE SUD)' (RTE) — both endpoints unknown (not in any intra-TSO line); comment='Tie line to ES (RTE)'
- [Tielines] DROP_EXTERNAL: 'LIT 225 kV BIESCAS-PRAGNERES' (RTE) — far end outside Core (ES-FR); hybrid design keeps NTC there
- [Tielines] EXCLUDE: 'LIT 225 kV ARKALE-ARGIA (BAYONNE SUD)' (RTE) — both endpoints unknown (not in any intra-TSO line); comment='Tie line to ES (RTE)'
- [Tielines] DROP_EXTERNAL: 'LIT 400KV N0 1 VENAUS - VILLARODIN' (RTE) — far end outside Core (IT-FR); hybrid design keeps NTC there
- [Tielines] EXCLUDE: 'LIT 225KV N0 1 CAMPOROSSO - MENTO / .CAM' (RTE) — both endpoints unknown (not in any intra-TSO line); comment='Tie line to IT (RTE)'
- [Tielines] EXCLUDE: 'V.Kapusany - Mukachevo' (SEPS) — one endpoint's country unresolvable; comment='Tie line with Ukraenergo'
- [Tielines] DROP_EXTERNAL: 'Medgidia Sud - Varna' (TEL) — far end outside Core (RO-BG); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Medgidia Sud - Dobrudja' (TEL) — far end outside Core (BG-RO); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Tantareni - Kozlodui c1' (TEL) — far end outside Core (RO-BG); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Tantareni - Kozlodui c2' (TEL) — far end outside Core (RO-BG); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Rosiori - Mukacevo c1' (TEL) — far end outside Core (RO-UA); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Isaccea - Vulcanesti' (TEL) — far end outside Core (RO-MD); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Portile de Fier - Djerdap c1' (TEL) — far end outside Core (RO-RS); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Pancevo 2 - Resita c2' (TEL) — far end outside Core (RO-RS); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Pancevo 2 - Resita c1' (TEL) — far end outside Core (RO-RS); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Asphard - Eichstetten rt/sw' (TRANSNETBW) — far end outside Core (CH-DE); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Gurtweil - Laufenburg ge' (TRANSNETBW) — far end outside Core (DE-CH); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Gurtweil - Oftringen bl' (TRANSNETBW) — far end outside Core (DE-CH); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Kuehmoos - Laufenburg br' (TRANSNETBW) — far end outside Core (DE-CH); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Kuehmoos - Laufenburg ge (Seelbach)' (TRANSNETBW) — far end outside Core (DE-CH); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Kuehmoos - Laufenburg rt' (TRANSNETBW) — far end outside Core (DE-CH); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Kuehmoos - Laufenburg ws' (TRANSNETBW) — far end outside Core (DE-CH); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Laufenburg - Trossingen rt' (TRANSNETBW) — far end outside Core (CH-DE); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Y-Kuehmoos (-Laufenburg - Lindenholz) bl' (TRANSNETBW) — far end outside Core (DE-CH); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Y-Laufenburg (-Gurtweil - Stokach) rtge' (TRANSNETBW) — far end outside Core (DE-CH); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Handewitt - Kassoe 1' (TENNETGMBH) — far end outside Core (DE-DK); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Handewitt - Kassoe 2' (TENNETGMBH) — far end outside Core (DE-DK); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Jardelund - Kassoe 1' (TENNETGMBH) — far end outside Core (DE-DK); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Jardelund - Kassoe 2' (TENNETGMBH) — far end outside Core (DK-DE); hybrid design keeps NTC there
- [Tielines] COUPLER: 'Kruemmel 50H - Kruemmel 993' (TENNETGMBH) — both ends are the same bus (KRUEMMEL_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] COUPLER: 'Kruemmel 50H - Kruemmel 994' (TENNETGMBH) — both ends are the same bus (KRUEMMEL_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] DROP_EXTERNAL: 'Nordlink Cable' (TENNETGMBH) — far end outside Core (DE-NO); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Nordlink Cable' (TENNETGMBH) — far end outside Core (DE-NO); hybrid design keeps NTC there
- [Tielines] COUPLER: 'Y-Brunsbuettel (-Brunsbuettel 50H - Hamburg/N 50H) 951' (TENNETGMBH) — both ends are the same bus (BRUNSBUETTEL_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] COUPLER: 'Y-Brunsbuettel (-Brunsbuettel 50H - Hamburg/N 50H) 952' (TENNETGMBH) — both ends are the same bus (BRUNSBUETTEL_380): TSO-to-TSO busbar coupler inside one station, collapsed
- [Tielines] DROP_EXTERNAL: 'Klixbuell/S - Endrup 1' (TENNETGMBH) — far end outside Core (DE-DK); hybrid design keeps NTC there
- [Tielines] DROP_EXTERNAL: 'Klixbuell/S - Endrup 2' (TENNETGMBH) — far end outside Core (DE-DK); hybrid design keeps NTC there
- [Lines] EIC_DUP_DROPPED: 'LIT 400KV N0 1 ECHALAS - PIVOZ-CORDIER' () — same EIC + same endpoints as 'LIT 400kV N0 2 ECHALAS-PIVOZ-CORDIER': one physical line listed by both TSOs; kept first row (X identical: 4.901)
- [Lines] EIC_DUP_DROPPED: 'LIT 400kV N0 2 PRAZ-ST-ANDRE - PIQUAGE A LA PRAZ-ST-ANDRE' () — same EIC + same endpoints as 'LIT 400kV N0 1 PRAZ-ST-ANDRE - PIQUAGE A LA PRAZ-ST-ANDRE': one physical line listed by both TSOs; kept first row — FLAG X mismatch [0.058, 0.049]
- [Lines] EIC_DUP_DROPPED: 'Y-Doernigheim (-Frankfurt/N - Grosskrotzenburg) 1' () — same EIC + same endpoints as 'Y-Doernigheim (-Frankfurt/N - Grosskrotzenburg) 1': one physical line listed by both TSOs; kept first row — FLAG X mismatch [0.1, 0.05]
- [Lines] EIC_DUP_DROPPED: 'Eichstetten C1 - Eichstetten C2 br' () — same EIC + same endpoints as 'Eichstetten C1 - Eichstetten C2 vi': one physical line listed by both TSOs; kept first row (X identical: 0.15)
- [Lines] EIC_DUP_DROPPED: 'Borssele-Rilland380 P' () — same EIC + same endpoints as 'Borssele-Rilland380 O': one physical line listed by both TSOs; kept first row (X identical: 10.03)
- [Lines] EIC_DUP_DROPPED: 'Hollandse Kust Noord Landstation-Wijk aan Zee380 W' () — same EIC + same endpoints as 'Hollandse Kust Noord Landstation-Wijk aan Zee380 B': one physical line listed by both TSOs; kept first row — FLAG X mismatch [0.07, 0.02]
- [Lines] EIC_DUP_DROPPED: 'Hollandse Kust Noord Landstation-Wijk aan Zee380 P' () — same EIC + same endpoints as 'Hollandse Kust Noord Landstation-Wijk aan Zee380 O': one physical line listed by both TSOs; kept first row — FLAG X mismatch [0.06, 0.04]
- [Lines] EIC_DUP_DROPPED: 'Hollandse Kust Noord Landstation-Wijk aan Zee380 Z' () — same EIC + same endpoints as 'Hollandse Kust Noord Landstation-Wijk aan Zee380 R': one physical line listed by both TSOs; kept first row — FLAG X mismatch [0.08, 0.03]
- [Tielines] EIC_DUP_DROPPED: 'Mecklar - Vieselbach 449-1' () — same EIC + same endpoints as 'Mecklar - Vieselbach 449-1': one physical line listed by both TSOs; kept first row (X identical: 16.325)
- [Tielines] EIC_DUP_DROPPED: 'Hradec - Rohrsdorf - V445' () — same EIC + same endpoints as 'Röhrsdorf - Hradec 445': one physical line listed by both TSOs; kept first row (X identical: 10.945)
- [Tielines] EIC_DUP_DROPPED: 'Hradec - Rohrsdorf - V446' () — same EIC + same endpoints as 'Röhrsdorf - Hradec 446': one physical line listed by both TSOs; kept first row (X identical: 10.945)
- [Tielines] EIC_DUP_DROPPED: 'Helmstedt - Wolmirstedt 491' () — same EIC + same endpoints as 'Helmstedt - Wolmirstedt 491-1': one physical line listed by both TSOs; kept first row (X identical: 6.527)
- [Tielines] EIC_DUP_DROPPED: 'Hamburg/S - Dollern 981' () — same EIC + same endpoints as 'Hamburg/Süd - Dollern 981': one physical line listed by both TSOs; kept first row (X identical: 3.548)
- [Tielines] EIC_DUP_DROPPED: 'Hamburg/S - Dollern 982' () — same EIC + same endpoints as 'Hamburg/Süd - Dollern 982': one physical line listed by both TSOs; kept first row (X identical: 3.548)
- [Tielines] EIC_DUP_DROPPED: 'Altenfeld - Redwitz 459' () — same EIC + same endpoints as 'Altenfeld - Redwitz 459': one physical line listed by both TSOs; kept first row (X identical: 7.087)
- [Tielines] EIC_DUP_DROPPED: 'Altenfeld - Redwitz 460' () — same EIC + same endpoints as 'Altenfeld - Redwitz 460': one physical line listed by both TSOs; kept first row — FLAG X mismatch [14.166686632362973, 7.0835]
- [Tielines] EIC_DUP_DROPPED: 'Redwitz - Remptendorf 413' () — same EIC + same endpoints as 'Redwitz - Remptendorf 413': one physical line listed by both TSOs; kept first row (X identical: 7.216)
- [Tielines] EIC_DUP_DROPPED: 'Redwitz - Remptendorf 414' () — same EIC + same endpoints as 'Redwitz - Remptendorf 414': one physical line listed by both TSOs; kept first row (X identical: 7.216)
- [Tielines] EIC_DUP_DROPPED: 'Mecklar - Eisenach 450-2' () — same EIC + same endpoints as 'Mecklar - Eisenach 450-2': one physical line listed by both TSOs; kept first row (X identical: 6.886)
- [Tielines] EIC_DUP_DROPPED: 'KRAJNIK-VIERRADEN c.2' () — same EIC + same endpoints as 'Vierraden - Krajnik 507': one physical line listed by both TSOs; kept first row — FLAG X mismatch [3.49, 3.888]
- [Tielines] EIC_DUP_DROPPED: 'KRAJNIK-VIERRADEN c.1' () — same EIC + same endpoints as 'Vierraden - Krajnik 508': one physical line listed by both TSOs; kept first row — FLAG X mismatch [3.49, 3.888]
- [Tielines] EIC_DUP_DROPPED: 'MIKULOWA-HAGENWERDER' () — same EIC + same endpoints as 'Hagenwerder - Mikulowa 567': one physical line listed by both TSOs; kept first row — FLAG X mismatch [2.53, 2.32]
- [Tielines] EIC_DUP_DROPPED: 'MIKULOWA-HAGENWERDER' () — same EIC + same endpoints as 'Hagenwerder - Mikulowa 568': one physical line listed by both TSOs; kept first row — FLAG X mismatch [2.606, 2.304]
- [Tielines] EIC_DUP_DROPPED: 'Guetersloh - Bechterdissen SN2' () — same EIC + same endpoints as 'Bechterdissen - Guetersloh SENNE N2': one physical line listed by both TSOs; kept first row (X identical: 3.257)
- [Tielines] EIC_DUP_DROPPED: 'Guetersloh - Bechterdissen SS1' () — same EIC + same endpoints as 'Bechterdissen - Guetersloh SENNE S1': one physical line listed by both TSOs; kept first row (X identical: 3.257)
- [Tielines] EIC_DUP_DROPPED: 'Dillenburg - Dauersberg WO2' () — same EIC + same endpoints as 'Dauersberg - Dillenburg WESTW O2': one physical line listed by both TSOs; kept first row (X identical: 9.68)
- [Tielines] EIC_DUP_DROPPED: 'Dettingen - Grosskrotzenburg US1' () — same EIC + same endpoints as 'Dettingen - Grosskrotzenburg UMAIN S1': one physical line listed by both TSOs; kept first row (X identical: 0.56)
- [Tielines] EIC_DUP_DROPPED: 'Doerpen/W - Meppen EWBL' () — same EIC + same endpoints as 'Doerpen West - Meppen EMSLD WB': one physical line listed by both TSOs; kept first row (X identical: 4.849)
- [Tielines] EIC_DUP_DROPPED: 'Urberach - Grosskrotzenburg UN2' () — same EIC + same endpoints as 'Grosskrotzenburg - Urberach UMAIN N2': one physical line listed by both TSOs; kept first row (X identical: 2.97)
- [Tielines] EIC_DUP_DROPPED: 'Meitingen - Oberbachern 419' () — same EIC + same endpoints as 'Meitingen - Oberbachern OBACHE N': one physical line listed by both TSOs; kept first row (X identical: 6.23)
- [Tielines] EIC_DUP_DROPPED: 'Meitingen - Oberbachern 420' () — same EIC + same endpoints as 'Meitingen - Oberbachern OBACHE S': one physical line listed by both TSOs; kept first row (X identical: 6.23)
- [Tielines] EIC_DUP_DROPPED_SPELLING: 'Y-Meppen (-Niederlangen - Doerpen/W) EOWS' () — same EIC as 'Meppen - Niederlangen EMSLD OW' but endpoints spelled ('Y-NIEDERLANGEN_380', 'MEPPEN_380') vs ('MEPPEN_380', 'NIEDERLANGEN_380'): same line, alias evidence; kept first row
- [Tielines] EIC_DUP_DROPPED: 'Nehden - Twistetal TO3' () — same EIC + same endpoints as 'Nehden - Twistetal TWIST O3': one physical line listed by both TSOs; kept first row (X identical: 4.438)
- [Tielines] EIC_DUP_DROPPED: 'Nehden - Twistetal TW4' () — same EIC + same endpoints as 'Nehden - Twistetal TWIST W4': one physical line listed by both TSOs; kept first row (X identical: 4.438)
- [Tielines] EIC_DUP_DROPPED: 'Y-Asslar (-Dauersberg - Limburg) WW1' () — same EIC + same endpoints as 'Y-Asslar (-Dauersberg - Limburg) WESTW W1': one physical line listed by both TSOs; kept first row (X identical: 4.571)
- [Tielines] EIC_DUP_DROPPED: 'Dellmensingen - Voehringen gn (Donau W)' () — same EIC + same endpoints as 'Dellmensingen - Voehringen DONAU W': one physical line listed by both TSOs; kept first row (X identical: 2.107)
- [Tielines] EIC_DUP_DROPPED: 'Daxlanden - Maximiliansau sw (Goldgrund Ost)' () — same EIC + same endpoints as 'Daxlanden - Maximiliansau GOLDGR O': one physical line listed by both TSOs; kept first row — FLAG X mismatch [0.618, 1.236]
- [Tielines] EIC_DUP_DROPPED: 'Hoheneck - Pulverdingen ws' () — same EIC + same endpoints as 'Hoheneck - Pulverdingen HO PU WS': one physical line listed by both TSOs; kept first row (X identical: 1.743)
- [Tielines] EIC_DUP_DROPPED: 'Kuehmoos - Tiengen gr' () — same EIC + same endpoints as 'Kuehmoos - Tiengen KUEMOS': one physical line listed by both TSOs; kept first row (X identical: 3.532)
- [Tielines] EIC_DUP_DROPPED: 'Kuehmoos - Maximiliansau ge (Rheingraben)' () — same EIC + same endpoints as 'Kuehmoos - Maximiliansau RGRABN': one physical line listed by both TSOs; kept first row — FLAG X mismatch [26.433, 52.86]
- [Tielines] EIC_DUP_DROPPED_SPELLING: 'Y-Metzingen (-Herbertingen - Hoheneck) sw HERBTG W' () — same EIC as 'Y-Metzingen (-Herbertingen - Hoheneck) HERBTG W' but endpoints spelled ('Y-HOHENECK_380', 'METZINGEN_380') vs ('HERBERTINGEN_380', 'METZINGEN_380'): same line, alias evidence; kept first row
- [Tielines] EIC_DUP_DROPPED: 'Y-Dellmensingen (-Hoheneck - Voehringen rt) DONAU O' () — same EIC + same endpoints as 'Y-Dellmensingen (-Hoheneck - Voehringen) DONAU O': one physical line listed by both TSOs; kept first row (X identical: 0.05)
- [Tielines] EIC_DUP_DROPPED: 'Y-Buers (-Herbertingen - Tiengen - Werben) BLUDNZ W' () — same EIC + same endpoints as 'Y-Buers (-Herbertingen - Tiengen - Werben) BLUDNZ W': one physical line listed by both TSOs; kept first row (X identical: 9.08)
- [Tielines] EIC_DUP_DROPPED: 'Westtirol - Leupolz 412' () — same EIC + same endpoints as 'Leupolz - Westtirol FUESSN O': one physical line listed by both TSOs; kept first row (X identical: 10.67)
- [Tielines] EIC_DUP_DROPPED: 'Westtirol - Voehringen 411' () — same EIC + same endpoints as 'Voehringen - Westtirol FUESSN W': one physical line listed by both TSOs; kept first row (X identical: 19.97)
- [Tielines] EIC_DUP_DROPPED: 'LIT 225kV N0 1 ENSDORF - ST-AVOLD' () — same EIC + same endpoints as 'Ensdorf - St. Avold AVOLD': one physical line listed by both TSOs; kept first row — FLAG X mismatch [4.067, 7.682]
- [Tielines] EIC_DUP_DROPPED: 'LIT 400kV N0 1 ENSDORF - VIGY' () — same EIC + same endpoints as 'Ensdorf - Vigy VIGY1 N': one physical line listed by both TSOs; kept first row — FLAG X mismatch [5.13, 10.275]
- [Tielines] EIC_DUP_DROPPED: 'LIT 400kV N0 2 ENSDORF - VIGY' () — same EIC + same endpoints as 'Ensdorf - Vigy VIGY2 S': one physical line listed by both TSOs; kept first row — FLAG X mismatch [5.13, 10.272]
- [Tielines] EIC_DUP_DROPPED: 'Flebour Bauler Nord' () — same EIC + same endpoints as 'Bauler - Flebour FLE BA N': one physical line listed by both TSOs; kept first row (X identical: 1.512)
- [Tielines] EIC_DUP_DROPPED: 'Flebour Bauler Süd' () — same EIC + same endpoints as 'Bauler - Flebour FLE BA S': one physical line listed by both TSOs; kept first row (X identical: 1.512)
- [Tielines] EIC_DUP_DROPPED: 'Blooren - Niederstedem Süd' () — same EIC + same endpoints as 'Blooren - Niederstedem BLONST S': one physical line listed by both TSOs; kept first row — FLAG X mismatch [5.425, 9.27]
- [Tielines] EIC_DUP_DROPPED: 'Heisdorf Quint Nord' () — same EIC + same endpoints as 'Heisdorf - Quint HEI QU N': one physical line listed by both TSOs; kept first row (X identical: 7.3)
- [Tielines] EIC_DUP_DROPPED: 'Doetinchem-Niederrhein 380 Z' () — same EIC + same endpoints as 'Doetinchem - Niederrhein DOETM SW': one physical line listed by both TSOs; kept first row (X identical: 7.205)
- [Tielines] EIC_DUP_DROPPED: 'Doetinchem-Niederrhein 380 W' () — same EIC + same endpoints as 'Doetinchem - Niederrhein DOETM WS': one physical line listed by both TSOs; kept first row (X identical: 7.31)
- [Tielines] EIC_DUP_DROPPED: 'Gronau-Hengelo 380 Z' () — same EIC + same endpoints as 'Gronau - Hengelo HENGL SW': one physical line listed by both TSOs; kept first row (X identical: 2.907)
- [Tielines] EIC_DUP_DROPPED: 'Gronau-Hengelo 380 W' () — same EIC + same endpoints as 'Gronau - Hengelo HENGL WS': one physical line listed by both TSOs; kept first row (X identical: 2.907)
- [Tielines] EIC_DUP_DROPPED: 'Maasbracht-Oberzier 380 W' () — same EIC + same endpoints as 'Maasbracht - Oberzier SELFK WS': one physical line listed by both TSOs; kept first row (X identical: 6.96)
- [Tielines] EIC_DUP_DROPPED: 'Maasbracht-Siersdorf 380 Z' () — same EIC + same endpoints as 'Maasbracht - Siersdorf SELFK SW': one physical line listed by both TSOs; kept first row (X identical: 4.935)
- [Tielines] EIC_DUP_DROPPED: 'Slavetice - Durnrohr - V437' () — same EIC + same endpoints as 'Duernrohr - Slavetice 437': one physical line listed by both TSOs; kept first row (X identical: 14.265)
- [Tielines] EIC_DUP_DROPPED: 'Slavetice - Durnrohr - V438' () — same EIC + same endpoints as 'Duernrohr - Slavetice 438': one physical line listed by both TSOs; kept first row (X identical: 14.265)
- [Tielines] EIC_DUP_DROPPED: 'Pirach - St. Peter 256' () — same EIC + same endpoints as 'St.Peter - Pirach 256': one physical line listed by both TSOs; kept first row — FLAG X mismatch [0.698, 11.752]
- [Tielines] EIC_DUP_DROPPED_SPELLING: 'Pleinting - St. Peter 258' () — same EIC as 'St.Peter - Pleinting 258' but endpoints spelled ('PLEINTING_220', 'ST. PETER (DE)_220') vs ('ST. PETER (AT)_220', 'PLEINTING_220'): same line, alias evidence; kept first row
- [Tielines] EIC_DUP_DROPPED: 'Podlog - Obersielach' () — same EIC + same endpoints as 'Obersielach - Podlog 247': one physical line listed by both TSOs; kept first row (X identical: 13.44)
- [Tielines] EIC_DUP_DROPPED: 'Maribor - Kainachtal' () — same EIC + same endpoints as 'Kainachtal - Maribor 473': one physical line listed by both TSOs; kept first row (X identical: 9.05)
- [Tielines] EIC_DUP_DROPPED: 'Maribor - Kainachtal' () — same EIC + same endpoints as 'Kainachtal - Maribor 474': one physical line listed by both TSOs; kept first row (X identical: 9.05)
- [Tielines] EIC_DUP_DROPPED: 'Buers - Meiningen gn (406A)' () — same EIC + same endpoints as 'Meiningen - Buers  406A': one physical line listed by both TSOs; kept first row (X identical: 4.49)
- [Tielines] EIC_DUP_DROPPED: 'Gyor - Neusiedl' () — same EIC + same endpoints as 'Neusiedl - Gyoer 246B': one physical line listed by both TSOs; kept first row (X identical: 17.105)
- [Tielines] EIC_DUP_DROPPED_SPELLING: 'Buers - Walgau or (405A)' () — same EIC as 'Walgauwerk - Buers  405A' but endpoints spelled ('BUERS_220', 'WALGAU_220') vs ('WALGAUWERK_220', 'BUERS_220'): same line, alias evidence; kept first row
- [Tielines] EIC_DUP_DROPPED: 'Buers - Westtirol rt (422)' () — same EIC + same endpoints as 'Westtirol - Buers  422': one physical line listed by both TSOs; kept first row (X identical: 14.25)
- [Tielines] EIC_DUP_DROPPED: 'Gyor - Wien' () — same EIC + same endpoints as 'Wien Suedost - Gyoer 245': one physical line listed by both TSOs; kept first row (X identical: 25.665)
- [Tielines] EIC_DUP_DROPPED: 'Gyor - Zurndorf' () — same EIC + same endpoints as 'Zurndorf - Gyoer 439B': one physical line listed by both TSOs; kept first row (X identical: 10.355)
- [Tielines] EIC_DUP_DROPPED: 'Szombathely - Zurndorf' () — same EIC + same endpoints as 'Zurndorf - Szombathely 440B': one physical line listed by both TSOs; kept first row — FLAG X mismatch [20.85, 19.46]
- [Tielines] EIC_DUP_DROPPED: 'Hradec - Etzenricht 441' () — same EIC + same endpoints as 'Hradec - Etzenricht': one physical line listed by both TSOs; kept first row (X identical: 21.86)
- [Tielines] EIC_DUP_DROPPED: 'Prestice - Etzenricht 442' () — same EIC + same endpoints as 'Prestice - Etzenricht': one physical line listed by both TSOs; kept first row (X identical: 14.5)
- [Tielines] EIC_DUP_DROPPED: 'Liskovec - P. Bystrica' () — same EIC + same endpoints as 'Liskovec - P. Bystrica': one physical line listed by both TSOs; kept first row — FLAG X mismatch [19.25, 20.7]
- [Tielines] EIC_DUP_DROPPED: 'Stupava - Sokolnice' () — same EIC + same endpoints as 'Sokolnice - Stupava': one physical line listed by both TSOs; kept first row — FLAG X mismatch [15.74, 19.382]
- [Tielines] EIC_DUP_DROPPED: 'Nosovice - Varin' () — same EIC + same endpoints as 'Nosovice - Varin': one physical line listed by both TSOs; kept first row — FLAG X mismatch [11.95, 11.261]
- [Tielines] EIC_DUP_DROPPED: 'WIELOPOLE-NOSOVICE' () — same EIC + same endpoints as 'Nosovice - Wielopole': one physical line listed by both TSOs; kept first row — FLAG X mismatch [20.496, 12.816]
- [Tielines] EIC_DUP_DROPPED: 'BUJAKOW-LISKOWIEC' () — same EIC + same endpoints as 'Liskovec - Bujakow': one physical line listed by both TSOs; kept first row (X identical: 16.84)
- [Tielines] EIC_DUP_DROPPED: 'KOPANINA-LISKOWIEC' () — same EIC + same endpoints as 'Liskovec - Kopanina': one physical line listed by both TSOs; kept first row — FLAG X mismatch [16.71, 17.555]
- [Tielines] EIC_DUP_DROPPED_SPELLING: 'DOBRZEN-DETMAROVICE' () — same EIC as 'Detmarovice - Dobrzen' but endpoints spelled ('DOBRZEN_380', 'DETMAROVICE_380') vs ('DETMAROVICE_380', 'XDT_DB1_380'): same line, alias evidence; kept first row
- [Tielines] EIC_DUP_DROPPED: 'Zerjavinec-Cirkovce' () — same EIC + same endpoints as 'Cirkovce - Zerjavinec': one physical line listed by both TSOs; kept first row — FLAG X mismatch [17.873, 29.05]
- [Tielines] EIC_DUP_DROPPED: 'Heviz - Cirkovce' () — same EIC + same endpoints as 'Cirkovce - Hevitz': one physical line listed by both TSOs; kept first row — FLAG X mismatch [22.964, 17.737]
- [Tielines] EIC_DUP_DROPPED: 'Zerjavinec - Podlog' () — same EIC + same endpoints as 'Podlog - Zerjavinec': one physical line listed by both TSOs; kept first row (X identical: 25.01)
- [Tielines] EIC_DUP_DROPPED: 'Melina - Divaca' () — same EIC + same endpoints as 'Divaca - Melina': one physical line listed by both TSOs; kept first row (X identical: 10.863)
- [Tielines] EIC_DUP_DROPPED: 'Pehlin - Divaca' () — same EIC + same endpoints as 'Divaca - Pehlin': one physical line listed by both TSOs; kept first row (X identical: 11.035)
- [Tielines] EIC_DUP_DROPPED: 'Tumbri - Krsko 1' () — same EIC + same endpoints as 'Krsko - Tumbri': one physical line listed by both TSOs; kept first row (X identical: 7.574)
- [Tielines] EIC_DUP_DROPPED: 'Tumbri - Krsko 2' () — same EIC + same endpoints as 'Krsko - Tumbri': one physical line listed by both TSOs; kept first row (X identical: 7.574)
- [Tielines] EIC_DUP_DROPPED: 'LIT 400kV N0 1 AVELGEM - MASTAING' () — same EIC + same endpoints as 'AVELGEM – MASTAING 380.79': one physical line listed by both TSOs; kept first row — FLAG X mismatch [11.8, 22.003]
- [Tielines] EIC_DUP_DROPPED: 'LIT 400kV N0 1 ACHENE - LONNY' () — same EIC + same endpoints as 'ACHENE – LONNY 380.19': one physical line listed by both TSOs; kept first row — FLAG X mismatch [9.54, 19.76]
- [Tielines] EIC_DUP_DROPPED: 'LIT 225kV N0 1 MONCEAU - CHOOZ' () — same EIC + same endpoints as 'CHOOZ – MONCEAU 220.48': one physical line listed by both TSOs; kept first row — FLAG X mismatch [5.73, 22.481]
- [Tielines] EIC_DUP_DROPPED: 'LIT 400kV N0 2 AVELGEM - AVELIN' () — same EIC + same endpoints as 'AVELGEM – AVELIN 380.80': one physical line listed by both TSOs; kept first row — FLAG X mismatch [6.55, 13.566]
- [Tielines] EIC_DUP_DROPPED_SPELLING: 'Y – AUBANGE (– SCHIFFLANGE – SANEM) 220.512' () — same EIC as 'Y – SCHIFFLANGE (– AUBANGE – SANEM) 220.512' but endpoints spelled ('Y - DIFFERDANGE_220', 'AUBANGE_220') vs ('Y - DIFFERDANGE_220', 'SCHIFFLANGE_220'): same line, alias evidence; kept first row
- [Tielines] EIC_DUP_DROPPED: 'LIT 225kV N0 1 AUBANGE - MOULAINE' () — same EIC + same endpoints as 'AUBANGE – MOULAINE 220.513': one physical line listed by both TSOs; kept first row — FLAG X mismatch [3.48, 6.325]
- [Tielines] EIC_DUP_DROPPED: 'Maasbracht-Van Eyck 380 W' () — same EIC + same endpoints as 'MAASBRACHT – VAN EYCK BLACK/27': one physical line listed by both TSOs; kept first row (X identical: 1.58)
- [Tielines] EIC_DUP_DROPPED: 'Maasbracht-Van Eyck 380 Z' () — same EIC + same endpoints as 'MAASBRACHT – VAN EYCK WHITE/28': one physical line listed by both TSOs; kept first row (X identical: 1.58)
- [Tielines] EIC_DUP_DROPPED: 'Rilland-Zandvliet 380 G' () — same EIC + same endpoints as 'RILLAND – ZANDVLIET GREY/29': one physical line listed by both TSOs; kept first row — FLAG X mismatch [1.07, 0.9763]
- [Tielines] EIC_DUP_DROPPED: 'Rilland-Zandvliet 380 W' () — same EIC + same endpoints as 'RILLAND – ZANDVLIET WHITE/30': one physical line listed by both TSOs; kept first row — FLAG X mismatch [1.07, 0.9763]
- [Tielines] EIC_DUP_DROPPED: 'LIT 225kV N0 1 AUBANGE - MT-SAINT-MARTIN' () — same EIC + same endpoints as 'AUBANGE – MONT-SAINT-MARTIN 220.514': one physical line listed by both TSOs; kept first row — FLAG X mismatch [0.81, 1.879]
- [Tielines] EIC_DUP_DROPPED: 'Pecs - Ernestinovo1 491A' () — same EIC + same endpoints as 'Pecs - Ernestinovo1 491A': one physical line listed by both TSOs; kept first row (X identical: 13.47)
- [Tielines] EIC_DUP_DROPPED: 'Pecs - Ernestinovo2 491B' () — same EIC + same endpoints as 'Pecs - Ernestinovo2 491B': one physical line listed by both TSOs; kept first row (X identical: 13.47)
- [Tielines] EIC_DUP_DROPPED: 'Arad - Sandorfalva' () — same EIC + same endpoints as 'Sandorfalva - Arad': one physical line listed by both TSOs; kept first row (X identical: 17.91)
- [Tielines] EIC_DUP_DROPPED: 'Levice - God' () — same EIC + same endpoints as 'Levice - God': one physical line listed by both TSOs; kept first row (X identical: 14.1)
- [Tielines] EIC_DUP_DROPPED: 'Gabcikovo - Gyor' () — same EIC + same endpoints as 'Gyor - Gabcikovo': one physical line listed by both TSOs; kept first row (X identical: 6.87)
- [Tielines] EIC_DUP_DROPPED: 'R.Sobota - Sajoivanka' () — same EIC + same endpoints as 'Sajoivanka - Rimavska Sobota': one physical line listed by both TSOs; kept first row — FLAG X mismatch [7.28, 8.072]
- [Tielines] EIC_DUP_DROPPED: 'Gabcikovo - Gonyu' () — same EIC + same endpoints as 'Gonyu - Gabcikovo': one physical line listed by both TSOs; kept first row — FLAG X mismatch [4.9, 4.621]
- [Tielines] EIC_DUP_DROPPED: 'V.Dur - Gonyu' () — same EIC + same endpoints as 'Gonyu - Velky Dur': one physical line listed by both TSOs; kept first row (X identical: 13.57)
- [Tielines] EIC_DUP_DROPPED: 'Lemesany - Krosno 2' () — same EIC + same endpoints as 'KROSNO-LEMESANY 2': one physical line listed by both TSOs; kept first row — FLAG X mismatch [35.34, 17.752]
- [Tielines] EIC_DUP_DROPPED: 'Lemesany - Krosno 1' () — same EIC + same endpoints as 'KROSNO-LEMESANY 1': one physical line listed by both TSOs; kept first row — FLAG X mismatch [35.34, 17.763]
- [Tielines] EIC_DUP_DROPPED: 'Eichstetten - Muhlbach rt (Ill)' () — same EIC + same endpoints as 'LIT 400kV N0 1 EICHSTETTEN - MUHLBACH': one physical line listed by both TSOs; kept first row — FLAG X mismatch [8.205, 4.1]
- [Tielines] EIC_DUP_DROPPED: 'Eichstetten - Vogelgrun ge (Kaiserstuhl)' () — same EIC + same endpoints as 'LIT 225kV N0 1 EICHSTETTEN - VOGELGRUN': one physical line listed by both TSOs; kept first row — FLAG X mismatch [5.952, 2.98]
- [Tielines] EIC_DUP_DROPPED_SPELLING: 'Y-Grafenrheinfeld (-Hoepfingen  - Stalldorf) 411/416' () — same EIC as 'Y-Grafenrheinfeld -(Hoepfingen-Stalldorf) ge/rt' but endpoints spelled ('GRAFENRHEINFELD_380', 'Y-HOEPFINGEN_380') vs ('Y-GRAFENRHEINFELD_380', 'GRAFENRHEINFELD_380'): same line, alias evidence; kept first row
- [Tielines] EIC_DUP_DROPPED: 'Diele-Meeden 380 Z' () — same EIC + same endpoints as 'Diele - Meeden 380 schwarz': one physical line listed by both TSOs; kept first row (X identical: 3.85)
- [Tielines] EIC_DUP_DROPPED: 'Diele-Meeden 380 W' () — same EIC + same endpoints as 'Diele - Meeden 380 weiss': one physical line listed by both TSOs; kept first row (X identical: 3.85)
- [Transformers] EXCLUDE: 'PST Röhrsdorf 441' (50HERTZ) — same nominal level both sides (410.0/410.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Röhrsdorf 442' (50HERTZ) — same nominal level both sides (410.0/410.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Vierraden 441' (50HERTZ) — same nominal level both sides (410.0/410.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Vierraden 442' (50HERTZ) — same nominal level both sides (410.0/410.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Vierraden 443' (50HERTZ) — same nominal level both sides (410.0/410.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Vierraden 444' (50HERTZ) — same nominal level both sides (410.0/410.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Hamburg/Ost 441' (50HERTZ) — same nominal level both sides (410.0/410.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Hamburg/Ost 442' (50HERTZ) — same nominal level both sides (410.0/410.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Hamburg/Ost 443' (50HERTZ) — same nominal level both sides (410.0/410.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Hamburg/Ost 444' (50HERTZ) — same nominal level both sides (410.0/410.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR Gronau TR 441 E    ' (AMPRION GMBH) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR Hanekenfaher TR 442 E ' (AMPRION GMBH) — location 'TR Hanekenfaher TR 442 E ' (parsed 'HANEKENFAHER E') matches no known substation
- [Transformers] EXCLUDE: 'TR Hanekenfaher TR 441 E ' (AMPRION GMBH) — location 'TR Hanekenfaher TR 441 E ' (parsed 'HANEKENFAHER E') matches no known substation
- [Transformers] EXCLUDE: 'TR Oberzier TR 442 E    ' (AMPRION GMBH) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Ernsthofen EHPST' (APG) — same nominal level both sides (220.0/220.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Lienz LIPST' (APG) — same nominal level both sides (220.0/220.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Tauern TAPST' (APG) — same nominal level both sides (220.0/220.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Ternitz TEPST' (APG) — same nominal level both sides (220.0/220.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR Nauders NRPST21' (APG) — same nominal level both sides (220.0/220.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR Nauders NRPST22' (APG) — same nominal level both sides (220.0/220.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR Hradec T402' (CEPS) — location 'TR Hradec T402' (parsed 'HRADEC') matches no known substation
- [Transformers] EXCLUDE: 'PST Hradec 1' (CEPS) — location 'PST Hradec 1' (parsed 'HRADEC') matches no known substation
- [Transformers] EXCLUDE: 'PST Hradec 2' (CEPS) — location 'PST Hradec 2' (parsed 'HRADEC') matches no known substation
- [Transformers] EXCLUDE: 'PST Hradec 3' (CEPS) — location 'PST Hradec 3' (parsed 'HRADEC') matches no known substation
- [Transformers] EXCLUDE: 'PST Divaca' (ELES) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR AUBANGE PST 1' (ELIA) — same nominal level both sides (243.0/243.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR VAN EYCK PST 1' (ELIA) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR VAN EYCK PST 2' (ELIA) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR ZANDVLIET PST 2' (ELIA) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR ZANDVLIET PST 3' (ELIA) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR ZANDVLIET PST 4' (ELIA) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST JOACHIMOW-TD1' (PSE) — same nominal level both sides (220.0/220.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST JOACHIMOW-TD2' (PSE) — same nominal level both sides (220.0/220.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST MIKULOWA-PF1' (PSE) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST MIKULOWA-PF2' (PSE) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST MIKULOWA-PF3' (PSE) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PSTMIKULOWA-PF4' (PSE) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST MIKULOWA-TD1' (PSE) — same nominal level both sides (220.0/220.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST MIKULOWA-TD2' (PSE) — same nominal level both sides (220.0/220.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR 400/225kV 761-(769) CERGY' (RTE) — location 'TR 400/225kV 761-(769) CERGY' (parsed '() CERGY') matches no known substation
- [Transformers] EXCLUDE: 'TR 400/225kV 761 PONTEAU' (RTE) — negative reactance X=-11.7 ohm — ask data owner, no sign flip
- [Transformers] EXCLUDE: 'TR 400/225kV 761 ST-AVOLD' (RTE) — location 'TR 400/225kV 761 ST-AVOLD' (parsed 'ST-AVOLD') matches no known substation
- [Transformers] EXCLUDE: 'TR 400/225kV 765  (769) VILLEVAUDE' (RTE) — location 'TR 400/225kV 765  (769) VILLEVAUDE' (parsed '() VILLEVAUDE') matches no known substation
- [Transformers] EXCLUDE: 'PST Meeden PST W' (TENNET NL) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Meeden PST Z' (TENNET NL) — same nominal level both sides (400.0/400.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Diele T441' (TENNETGMBH) — same nominal level both sides (380.0/380.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Diele T442' (TENNETGMBH) — same nominal level both sides (380.0/380.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Krempermarsch T441A' (TENNETGMBH) — same nominal level both sides (380.0/380.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Krempermarsch T441B' (TENNETGMBH) — same nominal level both sides (380.0/380.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Krempermarsch T442A' (TENNETGMBH) — same nominal level both sides (380.0/380.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Krempermarsch T442B' (TENNETGMBH) — same nominal level both sides (380.0/380.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Wuergau T441A' (TENNETGMBH) — same nominal level both sides (380.0/380.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Wuergau T441B' (TENNETGMBH) — same nominal level both sides (380.0/380.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Wuergau T442A' (TENNETGMBH) — same nominal level both sides (380.0/380.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'PST Wuergau T442B' (TENNETGMBH) — same nominal level both sides (380.0/380.0 kV): PST/self-loop, not representable as a branch
- [Transformers] EXCLUDE: 'TR Doerpen/W T441' (TENNETGMBH) — location 'TR Doerpen/W T441' (parsed 'DOERPEN/W') matches no known substation
- [Transformers] EXCLUDE: 'TR Doerpen/W T442' (TENNETGMBH) — location 'TR Doerpen/W T442' (parsed 'DOERPEN/W') matches no known substation
- [Transformers] EXCLUDE: 'TR Doerpen/W T443' (TENNETGMBH) — location 'TR Doerpen/W T443' (parsed 'DOERPEN/W') matches no known substation
- [Transformers] EXCLUDE: 'TR Doerpen/W T444' (TENNETGMBH) — location 'TR Doerpen/W T444' (parsed 'DOERPEN/W') matches no known substation
- [Transformers] EXCLUDE: 'TR Bucuresti Sud 400/110 4' (TEL) — blank primary/secondary kV
- [Lines] EXCLUDE_ISOLATED: 'Guetersloh - Hesseln HALLE W' () — branch of a fragment with no path to the main island (GUETERSLOH_220 - HESSELN_220)
- [Lines] EXCLUDE_ISOLATED: 'Salzburg 2 - Salzach 2 232B' () — branch of a fragment with no path to the main island (SALZBURG_220 - SALZACH_220)
- [Lines] EXCLUDE_ISOLATED: 'Salzburg 2 - Salzach 2 232C' () — branch of a fragment with no path to the main island (SALZBURG_220 - SALZACH_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 FONT (LA)-RIORGES' () — branch of a fragment with no path to the main island (FONT (LA)_220 - RIORGES_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 ANOULD-ETIVAL' () — branch of a fragment with no path to the main island (ANOULD_220 - ETIVAL_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 DONZENAC-FEROUGE' () — branch of a fragment with no path to the main island (DONZENAC_220 - FEROUGE_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 FEROUGE-TALAMET' () — branch of a fragment with no path to the main island (FEROUGE_220 - TALAMET_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 BARJAC-CROISIERE' () — branch of a fragment with no path to the main island (BARJAC_220 - CROISIERE_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 AVALLON - JOUX-LA-VILLE' () — branch of a fragment with no path to the main island (AVALLON_220 - JOUX-LA-VILLE_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 MUREAUX (LES) - NOUROTTES' () — branch of a fragment with no path to the main island (MUREAUX (LES)_220 - NOUROTTES_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 CAEN - RANVILLE' () — branch of a fragment with no path to the main island (CAEN_220 - RANVILLE_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225KV N0 1 SACLAY (PLATEAU) - VILLERAS' () — branch of a fragment with no path to the main island (SACLAY (PLATEAU)_220 - VILLERAS_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 MONTCROISETTE-VENDIN' () — branch of a fragment with no path to the main island (MONTCROISETTE_220 - VENDIN_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 CRETAINE-TOLBIAC' () — branch of a fragment with no path to the main island (CRETAINE_220 - TOLBIAC_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 BOULE (LA) - PUTEAUX' () — branch of a fragment with no path to the main island (BOULE (LA)_220 - PUTEAUX_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 BRODE - PIQUAGE A DUVIGNEAU' () — branch of a fragment with no path to the main island (BRODE_220 - PIQUAGE A DUVIGNEAU_220)
- [Lines] EXCLUDE_ISOLATED: 'LIT 225kV N0 1 DUVIGNEAU - PIQUAGE A DUVIGNEAU' () — branch of a fragment with no path to the main island (DUVIGNEAU_220 - PIQUAGE A DUVIGNEAU_220)
- [Lines] EXCLUDE_ISOLATED: 'Hollandse Kust Noord Landstation-Wijk aan Zee380 B' () — branch of a fragment with no path to the main island (HOLLANDSE KUST NOORD LANDSTATION_380 - WIJK AAN ZEE_380)
- [Lines] EXCLUDE_ISOLATED: 'Hollandse Kust Noord Landstation-Wijk aan Zee380 O' () — branch of a fragment with no path to the main island (HOLLANDSE KUST NOORD LANDSTATION_380 - WIJK AAN ZEE_380)
- [Lines] EXCLUDE_ISOLATED: 'Hollandse Kust Noord Landstation-Wijk aan Zee380 R' () — branch of a fragment with no path to the main island (HOLLANDSE KUST NOORD LANDSTATION_380 - WIJK AAN ZEE_380)

## Flags requiring a decision before Stage 2

- DCLines ALEGrO capacity 1132.8 MW is sqrt3·380·I from JAO's AC-style Imax (rows give 1635 A and 3600 A); the DC rating must be confirmed.
- 21 branches carry the 9999 MW UNRATED marker.
- Zero-X merges: ['ROBBENPLAAT_220 -> EEMSHAVEN_220']


---

# Appended by scripts/66_fix_tieline_workbook.py (2026-10-06)

Applied: connect = True; tie-line reactance rule = `first`. No validation data read; representative buses unchanged.
Buses 1763 -> 1758; changed cells 11 (`corrections.csv`); cross-zone branch rows per pair: AT-CZ 6, AT-DE 17, AT-HU 4, AT-SI 3, BE-DE 1, BE-FR 6, BE-NL 4, CZ-DE 4, CZ-PL 4, CZ-SK 4, DE-FR 5, DE-NL 8, DE-PL 4, HR-HU 3, HR-SI 6, HU-RO 2, HU-SI 1, HU-SK 5, PL-SK 2.

## Defect 1 — tie-lines that end in a bus with no other branch

| bus removed | bus kept | border | rows moved | evidence |
|---|---|---|---|---|
| KROSNO_380 | KROSNO ISKRZYNIA_380 | PL-SK | 2 | PSE internal lines 'KROSNO ISKRZYNIA' vs PSE tie-line rows 'KROSNO' (10T-PL-SK-00001W/-00002U); same map coordinates in substation_map.csv |
| PECS 1_380 | PECS_380 | HR-HU | 1 | MAVIR 'Paks - Pecs 1': circuit number written into the substation field; tie-lines 10T-HR-HU-000033/-000041 name 'Pecs' |
| PECS 2_380 | PECS_380 | HR-HU | 1 | MAVIR 'Paks - Pecs 2': circuit number written into the substation field |
| RIMAVSKA SOBOTA_380 | R. SOBOTA_380 | HU-SK | 1 | SEPS internal lines 'R. Sobota'; SEPS tie-line row of EIC 10T1001C--00054V 'R.Sobota'; alias R.SOBOTA=RIMAVSKA SOBOTA approved 2026-09-13 |
| XDT_DB1_380 | DOBRZEN_380 | CZ-PL | 1 | CEPS row of EIC 10T1001A1001A09N ends at the border-point code XDT_DB1; PSE row of the same EIC: DOBRZEN -> DETMAROVICE |

## Defect 2 — reactance of tie-lines listed by two operators

Tie-line rows in the workbook: 148; listed by two operators with both reactances: 109 (70 cross-border, 39 between operators of one country).

- cross-border: both rows are halves 36, each row is the operator's own part 22, row 1 is the whole line 1, row 2 is the whole line 8; per-km rule not applicable 3; flagged ambiguous 1.
  whole-line reactance (per-km rule) / built value: median 2.00, min 0.63, max 20.49; unchanged in 1 of 67.
- inside one country: both rows are halves 27, each row is the operator's own part 2, row 1 is the whole line 3, row 2 is the whole line 2; per-km rule not applicable 5; flagged ambiguous 6.
  whole-line reactance (per-km rule) / built value: median 2.00, min 1.00, max 3.92; unchanged in 3 of 34.

Cross-border lines, per border (count; median ratio whole-line / built):

AT-CZ 2 x2.00, AT-DE 4 x9.92, AT-HU 4 x2.00, AT-SI 3 x2.00, BE-FR 5 x2.07, BE-NL 4 x1.95, CZ-DE 4 x2.00, CZ-PL 4 x1.87, CZ-SK 3 x2.08, DE-FR 5 x1.89, DE-NL 8 x1.99, DE-PL 4 x2.02, HR-HU 3 x2.00, HR-SI 6 x2.00, HU-RO 2 x2.30, HU-SI 1 x1.77, HU-SK 5 x1.98

After the merge, neighbours of the kept buses: DOBRZEN_380: 5; KROSNO ISKRZYNIA_380: 3; PECS_380: 2; R. SOBOTA_380: 3.

## Not corrected (not resolvable from the file)

- Sokolnice–Senica (CZ–SK, EIC 10T-CZ-SK-00007M): listed by CEPS at 380 kV; SEPS lists Senica only at 220 kV (Krizovany–Senica) and no transformer. SENICA_380 stays a dead end.
- Y-Differdange tee (BE–LU, EIC 22T201907102---7): the Aubange leg is dropped by the EIC de-duplication. A phase shifter (Schifflange) sits on that path; the parallel SOTEL path Aubange–Belval–Oxylux–Schifflange is in the workbook.
- Aubange–Mont-Saint-Martin 220 kV (BE–FR): RTE's 225 kV lines behind Mont-Saint-Martin are not in the file; the bus stays a dead end.
- Tie-lines listed by one operator only keep their listed reactance (it may be that operator's part).


---

# Appended by scripts/70_tieline_reactance_mixed.py (2026-10-06)

No validation data read; buses, branches and representative buses unchanged.

## Mixed rule on jao_core_v14a

Tie-line rows 148; listed by two operators with both reactances 109 (72 cross-border). Normal range used for the result check: 380 kV 0.224-0.408, 220 kV 0.233-0.431 ohm per km.

| what was taken | lines | reading |
|---|---|---|
| sum | 99 | 64 x both rows are halves; 27 x each row is the operator's own part; 8 x no length listed by one operator: the sum |
| row 1 | 3 | 3 x row 1 is the whole line |
| row 2 | 7 | 7 x row 2 is the whole line |

Changed against the source: 106 of 109 rows; new / built: median 2.00, from 1.00 to 20.49.
Differs from the plain sum on 10 rows.

## Flagged by the general-logic checks

32 of the 109 two-operator rows (13 cross-border): the check changed the reading, the result is outside the normal range, the call was close, or there was no length to judge with.

| border | line | taken | value, ohm | per km | flags |
|---|---|---|---|---|---|
| AT-DE | Meiningen - Buers  406A | sum | 8.98 |  | no length: could not be judged |
| AT-DE | Walgauwerk - Buers  405A | sum | 4.48 |  | no length: could not be judged |
| AT-DE | Westtirol - Buers  422 | sum | 28.52 |  | no length: could not be judged |
| AT-SI | Obersielach - Podlog 247 | sum | 26.99 | 0.516 | result: 0.52 ohm per km is outside the normal range 0.23-0.43 |
| BE-FR | AUBANGE  MOULAINE 220.513 | row 2 | 6.33 | 0.416 | lengths: 7.85 + 15.204 km against 9 km straight; taken as the full length listed twice |
| BE-FR | AVELGEM  MASTAING 380.79 | row 2 | 22.00 | 0.289 | lengths: 38.45 + 76.148 km against 53 km straight; taken as the full length listed twice |
| BE-NL | RILLAND  ZANDVLIET GREY/29 | sum | 2.05 | 0.203 | result: 0.20 ohm per km is outside the normal range 0.22-0.41 |
| BE-NL | RILLAND  ZANDVLIET WHITE/30 | sum | 2.05 | 0.203 | result: 0.20 ohm per km is outside the normal range 0.22-0.41 |
| DE-NL | Gronau - Hengelo HENGL SW | sum | 5.81 | 0.212 | result: 0.21 ohm per km is outside the normal range 0.22-0.41 |
| DE-NL | Gronau - Hengelo HENGL WS | sum | 5.81 | 0.212 | result: 0.21 ohm per km is outside the normal range 0.22-0.41 |
| NL-DE | Maasbracht - Oberzier SELFK WS | sum | 14.11 | 0.376 | close call: row 2 is nearer the normal value than the sum, by less than 10 %; sum kept |
| SI-HR | Cirkovce - Zerjavinec | row 2 | 29.05 | 0.297 | lengths: 97.8 + 97.8 km against 67 km straight; taken as the full length listed twice |
| SI-HR | Podlog - Zerjavinec | sum | 50.02 | 0.509 | result: 0.51 ohm per km is outside the normal range 0.23-0.43 |
| DE-DE | Blooren - Niederstedem BLONST S | sum | 14.70 | 0.193 | result: 0.19 ohm per km is outside the normal range 0.23-0.43 |
| DE-DE | Dauersberg - Dillenburg WESTW O2 | row 2 | 9.68 | 0.238 | lengths: 38 + 40.6419 km against 22 km straight; taken as the full length listed twice |
| DE-DE | Dellmensingen - Voehringen DONAU W | sum | 4.21 |  | no length: could not be judged |
| DE-DE | Dettingen - Grosskrotzenburg UMAIN S1 | sum | 1.12 | 0.176 | result: 0.18 ohm per km is outside the normal range 0.22-0.41 |
| DE-DE | Doerpen West - Meppen EMSLD WB | sum | 9.70 | 0.294 | lengths: 17 + 32.9615 km against 18 km straight; taken as the full length listed twice |
| DE-DE | Grosskrotzenburg - Urberach UMAIN N2 | sum | 6.00 | 0.169 | result: 0.17 ohm per km is outside the normal range 0.22-0.41 |
| DE-DE | Hamburg/Sud - Dollern 981 | sum | 7.08 | 0.165 | result: 0.16 ohm per km is outside the normal range 0.22-0.41 |
| DE-DE | Hamburg/Sud - Dollern 982 | sum | 7.08 | 0.165 | result: 0.16 ohm per km is outside the normal range 0.22-0.41 |
| DE-DE | Herbertingen - Herbertingen (Amprion)  rt-Uebergabe  | sum | 0.11 |  | no length: could not be judged |
| DE-DE | Herbertingen - Herbertingen (Amprion) sw-Uebergabe 4 | sum | 0.10 |  | no length: could not be judged |
| DE-DE | Hoheneck - Pulverdingen HO PU WS | sum | 3.48 | 0.175 | result: 0.18 ohm per km is outside the normal range 0.22-0.41 |
| DE-DE | Kuehmoos - Maximiliansau RGRABN | row 2 | 52.86 | 0.253 | lengths: 105 + 208.9 km against 136 km straight; taken as the full length listed twice |
| DE-DE | Kuehmoos - Tiengen KUEMOS | sum | 7.06 |  | no length: could not be judged |
| DE-DE | Meitingen - Oberbachern OBACHE N | sum | 12.46 | 0.166 | result: 0.17 ohm per km is outside the normal range 0.22-0.41 |
| DE-DE | Meitingen - Oberbachern OBACHE S | sum | 12.46 | 0.166 | result: 0.17 ohm per km is outside the normal range 0.22-0.41 |
| DE-DE | Meppen - Niederlangen EMSLD OW | sum | 5.84 | 0.135 | result: 0.13 ohm per km is outside the normal range 0.22-0.41 |
| DE-DE | Y-Dellmensingen (-Hoheneck - Voehringen) DONAU O | sum | 0.10 |  | no length: could not be judged |
| DE-DE | Y-Grafenrheinfeld -(Hoepfingen-Stalldorf) ge/rt | sum | 12.66 | 0.251 | lengths: 50.44 + 50.139 km against 44 km straight; taken as the full length listed twice |
| DE-DE | Y-Metzingen (-Herbertingen - Hoheneck) HERBTG W | sum | 0.72 | 0.193 | result: 0.19 ohm per km is outside the normal range 0.22-0.41 |

Lengths that could not be reconciled with the map, no change made (10 rows; station coordinates are approximate, tee points especially): Bechterdissen - Guetersloh SENNE N2 (DE-DE); Bechterdissen - Guetersloh SENNE S1 (DE-DE); Daxlanden - Maximiliansau GOLDGR O (DE-DE); Dettingen - Grosskrotzenburg UMAIN S1 (DE-DE); Divaca - Melina (SI-HR); Maasbracht - Oberzier SELFK WS (NL-DE); Maasbracht - Siersdorf SELFK SW (NL-DE); Meppen - Niederlangen EMSLD OW (DE-DE); Y-Asslar (-Dauersberg - Limburg) WESTW W (DE-DE); Y-Metzingen (-Herbertingen - Hoheneck) H (DE-DE).

Listed by one operator only, cannot be corrected (38 rows, 16 cross-border). 15 of them have a reactance per km of the listed share outside the normal range (the listed length is then not the length the reactance belongs to): Audorf/S - Hamburg/N 50H weiss (DE-DE, 0.118); BELVAL-OXYLUX (BE-DE, 1.12); Ganderkesee - St. Huelfe HUNTE SW (DE-DE, 0.03); Ganderkesee - St. Huelfe HUNTE WS (DE-DE, 0.03); Grafenrheinfeld - Stalldorf rt (416) (DE-DE, 1.579); Hamburg/N - Hamburg/N 50H rot (DE-DE, 0.197); Helmstedt - Wolmirstedt 492-2 (DE-DE, 0.139); Westtirol - Silz 274E (DE-AT, 0.161); Westtirol - Silz 413 (DE-AT, 0.145); Westtirol - Silz 414 (DE-AT, 0.146); Y-Kriftel (-Frankfurt/SW - Karben) 2 (DE-DE, 0.052); Y-St. Peter (-Simbach - Altheim) 233 (AT-DE, 0.032); Y-St. Peter (-Simbach - Altheim) 234 (AT-DE, 0.032); Zaya - Sokolnice 243 (AT-CZ, 0.92); Zaya - Sokolnice 244 (AT-CZ, 0.92).


---

# Appended by scripts/68_merge_stations_workbook.py (2026-10-06)

Stations merged against jao_core_v22a (`station_merges_2026-10-06_internal.csv`):

- H.ZIVOTICE_380 -> H. ZIVOTICE_380 (CZ): CEPS rows 'H. Zivotice - Krasikov' (station 'H. Zivotice') and 'H. Zivotice - Kletne' (station 'H.Zivotice'): one station, two punctuations; the Krasikov-Kletne 380 kV corridor is cut in two
- SZOMBATHELY 1_380 -> SZOMBATHELY_380 (HU): MAVIR row 'Heviz - Szombathely 1': circuit number written into the substation field (same pattern as Paks - Pecs 1/2); 'Gyor - Szombathely' and the Zurndorf tie-line name 'Szombathely'
- SZOMBATHELY 2_380 -> SZOMBATHELY_380 (HU): MAVIR row 'Heviz - Szombathely 2': circuit number written into the substation field
- OSTROW_380 -> OSTROW WLKP_380 (PL): PSE rows 'KROMOLICE-OSTROW c.1' (station 'OSTROW WLKP') and 'KROMOLICE-OSTROW c.2' (station 'OSTROW'): two circuits of one line, both 112.5 km


---

# Appended by scripts/67_set_rep_buses_workbook.py (2026-10-06)

Representative buses changed against jao_core_v22: CZ HRADEC VYCHOD_380 -> NOSOVICE_380; NL KRIMPEN AAN DEN IJSSEL_380 -> RILLAND_380. TUNED (calibrated on 2025 flows) on the MIXED-rule base: winners of the guarded searches atcz-mixed-odd and nl-mixed-odd (selection on odd ISO weeks; the same sets win with the halves swapped), protocol replay2025/runs/2026-10-06-tuning-protocol
All representative buses: AT = DUERNROHR_380; BE = GRAMME_380; CZ = NOSOVICE_380; DE = ROMMERSKIRCHEN_380; FR = CHESNOY (LE)_380; HR = MELINA_380; HU = MARTONVASAR_380; NL = RILLAND_380; PL = ROGOWIEC_380; RO = BUCURESTI SUD_380; SI = BERICEVO_380; SK = KRIZOVANY_380.


---

# Appended by scripts/89_fix_workbook_phase_a.py (2026-10-14)

Fixes against jao_core_v23 (user, 2026-10-14: "yes fix them and rerun" (replay2025/notes/14, section 4)):

- F1 merge FRANKFURT_380 into FRANKFURT/SW_380: 1 branch end moved. JAO publication: EIC 11T0-0000-0030-G = 'Kriftel - Frankfurt/SW TAUNUS 2', substation 'Frankfurt/SW'
- F2 add Kainachtal - Dreibein Mellach 475KT and 476KT: X 4.705 ohm each (15.4 km); ratings of the listed legs. JAO publication monitors 'Kainachtal - Y_Mellach 475KT/476KT'; the JAO static file lists only the other legs. ESTIMATED: length 13.13 km straight x 1.172 (median route/straight, 31 APG 380 kV lines) = 15.38 km; X = 0.3059 ohm/km (median APG 380 kV) x length
- F3 add transformer SENICA_380 - SENICA_220: X 79.22 ohm, 249.415 MW. Sokolnice - Senica (10T-CZ-SK-00007M) is 380 kV in the JAO file (CEPS) and in JAO's publication (u = 380, CZ-SK); Senica had no other 380 kV element. ESTIMATED: X, current and rating = medians of SEPS's 3 380/220 kV transformers in the workbook
- F4 ratings of unrated lines: 21 lines. operator-and-voltage median of rated lines in the workbook


---

# Appended by scripts/100_apply_workbook_patches.py (2026-10-16)

Patches applied to jao_core_v27, in order: `jao2026_nl` (2 Nodes, 8 Lines, 0 Transformers; 0 skipped), `jao2026_nl_2` (1 Nodes, 3 Lines, 0 Transformers; 0 skipped).

- jao2026_nl / Nodes: BEVERWIJK_380
- jao2026_nl / Nodes: VIJFHUIZEN_380
- jao2026_nl / Lines: Beverwijk-Vijfhuizen380 W
- jao2026_nl / Lines: Beverwijk-Vijfhuizen380 Z
- jao2026_nl / Lines: Bleiswijk-Vijfhuizen380 O
- jao2026_nl / Lines: Bleiswijk-Vijfhuizen380 P
- jao2026_nl / Lines: Beverwijk-Oostzaan380 W
- jao2026_nl / Lines: Beverwijk-Oostzaan380 Z
- jao2026_nl / Lines: Bergum-Vierverlaten220 W
- jao2026_nl / Lines: Bergum-Vierverlaten220 Z
- jao2026_nl_2 / Nodes: BOXMEER_380
- jao2026_nl_2 / Lines: Maasbracht-Boxmeer380 Z
- jao2026_nl_2 / Lines: Boxmeer-Dodewaard380 Z
- jao2026_nl_2 / Lines: Borssele-Rilland380 P

See each patch's CHANGELOG.md for sources and conversions.
