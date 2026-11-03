# 2026-10-16 — Dutch part of JAO 2026 completed with elements from the GridAware network (patch v27 → v28)

Report for the user's brief of 2026-10-16 ("complete the Dutch part of JAO 2026 with elements from the GridAware network", Part 1
only, 2026 base). Section 2a items added; section 2b items investigated and reported, not added. The 2035 / IP2026 change
list was not started.

## 1. Where things are

| step | what | where |
|---|---|---|
| JAO file | Core Static Grid Model 2026 (raw, never modified) | `dcopf/inputs/raw/202603_Core Static Grid Model_External.xlsx` |
| builder | raw → workbook `jao_core.xlsx` (sheets Lines, Tielines, Nodes, Generators, Transformers, DCLines) | `scripts/10_build_enr_workbook.py`; fixes 66–89 make new versions |
| base | JAO 2026 workbook with the 14 Oct fixes | `inputs/derived/jao_core_v27/` |
| the GridAware network | copied unchanged from `IP2026 and the IP26 project matching work/Code/full_network.csv`, registered with hash | `inputs/external/gridaware_full_network_2026-10-16/` (SOURCES.md) |
| IP2026 | plan, annexes 4–6, IP26 project points (evidence only) | `inputs/external/tennet_ip2026_2026-10-16/` (SOURCES.md) |
| patch builder | reads the files, checks every rule, writes the patch | `scripts/96_build_nl_patch_from_gridaware.py` (copy of 95, see §8) |
| patch | nodes_add, lines_add, transformers_add (empty), CHANGELOG, metadata, evidence, node diff, 2b proposals, checks | `dcopf/patches/jao2026_nl/` |
| apply step | v27 + patch → v28; additions only, idempotent | `scripts/97_apply_workbook_patch.py` → `inputs/derived/jao_core_v28/` |
| reduction | the package reads `jao_core.xlsx` and writes `Line_Details_LP.csv` (regenerated, not edited) | `scripts/11_stage1_jao_diagnostics.jl` → `runs/2026-10-16-stage2-v28-LP-virtual/` |
| reduced network, limits | sparse fit, N-1 380 kV, option 3 | `scripts/58`, `83`, `93` → `inputs/derived/diag_fixedpos_v28-sparse-LP*` |
| before/after | full-grid 2025 DC power flow, corridors, snapshots, border routing, 53 and 90 side by side | `scripts/98_nl_patch_before_after.py` → `runs/2026-10-16-nl-patch-before-after-v27-v28/` |
| tests | 10 checks of section 5 of the brief | `dcopf/tests/test_nl_patch_jao2026.py` |

The pipeline reads the workbook, not the CSV export of 15 October (`exports/network_v27_full_2026-10-15/`); that export is
untouched. Nothing in the `IP2026 and the IP26 project matching work` folder is read by any pipeline script (test 10).

## 2. JAO capacity convention found (brief §3.2)

k = Capacity_MW / (√3 · Currrent_(A) / 1000), every row of jao_core_v27:

| sheet | 380 kV level | 220 kV level |
|---|---|---|
| Lines | 400.000 (1,320 rows, 399.9995–400.0009) | 225.000 (1,278 rows, 224.996–225.001) |
| Tielines | 400.000 (101 rows) | 225.000 (47 rows) |
| Transformers | 400.000 (405 rows) | 225.000 (40 rows) |

Constant within each level (spread = rounding of the 3-decimal MW). It is the builder's `--jao-fmax` choice of 13 Sept
(MW at JAO's operating voltage 400/225 kV, per-unit base nominal 380/220 kV). R = 0 and B = 0 in every row (checked).
It is also JAO's own convention, confirmed by the independent review (F-06) on JAO's 2026 flow-based data: Fmax / (√3 · Imax)
= 400.00 ± 0.07 over 15,612 monitored-element records at 380 kV (TenneT NL: 399.99 ± 0.05 over 3,120).
`Voltage_level` of the Dutch rows: 380 and 220 (nominal); the reduction converts X(Ω) with that value and 100 MVA.

## 3. Rows added (jao_core_v28)

| EIC (placeholder) | Line_name | From – To | X Ω | km | A | MW | GridAware edge_id | JAO 2026 element (EIC in JAO's flow-based files) |
|---|---|---|---|---|---|---|---|---|
| PATCH-NL-0001 | Beverwijk-Vijfhuizen380 W | BEVERWIJK_380 – VIJFHUIZEN_380 | 2.860119 | 12.2 | 3,000 | 2,078.461 | branch:BVW-VHZ380 W | Beverwijk - Vijfhuizen 380 Wit (49T000000000049V) |
| PATCH-NL-0002 | Beverwijk-Vijfhuizen380 Z | BEVERWIJK_380 – VIJFHUIZEN_380 | 2.860119 | 12.2 | 3,000 | 2,078.461 | branch:BVW-VHZ380 Z | … Zwart (49T000000000048X) |
| PATCH-NL-0003 | Bleiswijk-Vijfhuizen380 O | BLEISWIJK_380 – VIJFHUIZEN_380 | 9.920326 | 45.97 | 3,000 | 2,078.461 | branch:BWK-VHZ380 O | Bleiswijk - Vijfhuizen 380 Oranje (49T000000000047Z) |
| PATCH-NL-0004 | Bleiswijk-Vijfhuizen380 P | BLEISWIJK_380 – VIJFHUIZEN_380 | 9.920326 | 45.97 | 3,000 | 2,078.461 | branch:BWK-VHZ380 P | … Paars (49T0000000000460; JAO imax 3,000 A, same as GridAware) |
| PATCH-NL-0005 | Beverwijk-Oostzaan380 W | BEVERWIJK_380 – OOSTZAAN_380 | 4.352655 | 15.9 | 3,300 | 2,286.307 | branch:BVW-OZN380 W | Beverwijk - Oostzaan 380 Wit (49T0000000000517) |
| PATCH-NL-0006 | Beverwijk-Oostzaan380 Z | BEVERWIJK_380 – OOSTZAAN_380 | 4.353 | 17.0 | 3,300 | 2,286.307 | branch:BVW-OZN380 Z | … Zwart (49T0000000000509) |
| PATCH-NL-0007 | Bergum-Vierverlaten220 W | BERGUM_220 – VIERVERLATEN_220 | 8.5441 | 32.4798 | 2,500 | 974.279 | branch:BGM-VVL220 W | Bergum - Vierverlaten 220 wit (49T000000000068R) |
| PATCH-NL-0008 | Bergum-Vierverlaten220 Z | BERGUM_220 – VIERVERLATEN_220 | 8.5393 | 32.4798 | 2,500 | 974.279 | branch:BGM-VVL220 Z | … zwart (49T0000000000169) |

Nodes: `BEVERWIJK_380` (52.47, 4.68) and `VIJFHUIZEN_380` (52.37, 4.70), NL, 380 kV, defaults of the Dutch 380 kV nodes
(IsRepresentative 0, Type 1, Vm 1, Va 0, Vmax 1.1, Vmin 0.9). Representative bus of NL unchanged (Rilland).

- **Values** read from the file; equal to the brief's table to its rounding (checked; the build aborts otherwise). Only
  current, reactance and length are taken; GridAware's R and B are kept in `patch_metadata.csv`. How far GridAware's reactances can
  be trusted (review F-01, 71 Dutch 220/380 kV circuits present in both files): within 2 % of JAO's for 46, within 10 % for
  59; the class the patch belongs to (Oostzaan–Diemen, Louwsmeer–Bergum, Vierverlaten–Zeyerveen) agrees within 0.5 %; the
  Randstad-south 4,000 A circuits (Maasvlakte–Simonshaven, Crayestein–Simonshaven, Crayestein–Krimpen, Krimpen–Bleiswijk)
  are +15 % with half the rating, and GridAware's Krimpen–Breukelen tee is placed differently from JAO's: care in later patches.
- **Existence**: all eight circuits appear in JAO's own 2026 flow-based files (outages on 14 Jan, 15 Jul, 10 Sep 2026;
  Bleiswijk–Vijfhuizen Paars is also monitored), so TenneT's 2026 grid model has them even though JAO's static file does not.
  IP2026 annex 4 names them as bottlenecks of reinforcement projects of existing connections:
  - A-1000363 "Beverwijk-Vijfhuizen-Bleiswijk 380 kV verzwaren verbinding" (2030–31; bottlenecks 1611/1612, 2070);
  - A-1003430 "Krimpen-Diemen-Beverwijk 380 kV verzwaren verbinding" (bottleneck 1573 Beverwijk-Oostzaan);
  - A-1000366 "Vierverlaten-Oudehaske-Ens 220 kV verzwaren west ring" (bottleneck 1608 Bergum-Vierverlaten).
- **Duplicates**: no workbook row between the same buses or naming both stations; no row in the JAO file naming both
  stations (they are absent from it, not dropped by our builder); no other record in the GridAware file joins the same stations
  (no `manual:` copy, no segment chain). Placeholder EICs unique and new.
- **Plausibility**, x′ = X/length: Beverwijk–Oostzaan 0.274 / 0.256 Ω/km and Bergum–Vierverlaten 0.263 Ω/km, as the Dutch
  JAO medians (380 kV 0.273, 220 kV 0.263). Bleiswijk–Vijfhuizen 0.216 Ω/km (brief: route with cable sections). Beverwijk–
  Vijfhuizen 0.234 Ω/km is also below the overhead range. My reading, not a fact: GridAware's susceptance per km is 0.019 p.u./km
  on Beverwijk–Vijfhuizen and 0.044 on Bleiswijk–Vijfhuizen, against 0.006 on the overhead Beverwijk–Oostzaan, which points
  to cable sections on both routes. Not changed. The brief's expected range 0.27–0.30 Ω/km is itself wrong (review F-02):
  JAO's own Dutch 380 kV rows over 5 km (50 lines) run 0.17–0.64 Ω/km, median 0.273, Wateringen–Bleiswijk 0.168.
- **Capacity** = √3 · 400 · I / 1000 (380 kV), √3 · 225 · I / 1000 (220 kV), k from §2.
- **Line_Details_LP.csv regenerated** by the reduction (34 s): 3,221 rows = v27's 3,213 + the 8 new ones, no existing row
  changed (full-record comparison). New rows have X_pu = X / (kV² / 100) on the same base as the existing Dutch rows
  (e.g. Oostzaan–Diemen 4.21 Ω → 0.002916 p.u.). One island of 1,755 buses (NL 44).
- **Coordinates**: `DATA/GridAware_topology_map` is not here, so the RD values of the brief were used (EPSG:28992). pyproj is
  not installed (installing it needs a download), so the published RD → WGS84 approximation was used. Checks:
  - the round trip RD → WGS84 → RD is within 1.4 mm;
  - the brief's points lie 11.5 m and 20.4 m (Beverwijk) and 35.7 m (Vijfhuizen) from IP2026 project points at those
    stations;
  - 23 of 32 IP26 points at Dutch JAO stations convert to within 0.005° of the JAO coordinates (JAO's rounding). The other
    9 belong to 5 stations (Geertruidenberg, Eindhoven, Maasvlakte, Borssele, Meeden) and are off by 0.016–0.024° for every
    point of the same station, which suggests JAO's own coordinates for those stations are approximate.

## 4. Checks of brief §5 (all pass; `tests/test_nl_patch_jao2026.py`, 10 tests, 1.0 s)

- Dutch nodes 42 → 44; 8 new Lines rows; other sheets unchanged; existing rows identical to v27.
- No duplicate (station pair, circuit) in the Dutch part; patch EICs unique.
- Connectivity:
  - Oostzaan was a dead end off Diemen and is now joined to Beverwijk; Beverwijk joins Vijfhuizen and Oostzaan;
    Vijfhuizen joins Beverwijk and Bleiswijk.
  - With Diemen–Oostzaan out, Oostzaan still reaches Krimpen.
  - Bergum and Louwsmeer reach Ens 220 kV with either the Oudehaske or the Vierverlaten side out (west ring closed).
- Capacity = √3 · k · I; x′ in range (Bleiswijk–Vijfhuizen 0.216 noted).
- Line_Details regenerated with the same per-unit base.
- Applying the patch again adds nothing (v28 + patch: 10 rows "already present", nothing written); rerunning v27 → v28
  aborts (never overwritten).
- No pipeline script reads the the IP26 project matching folder. There were no tests in `dcopf/` before; this file is the first.

## 5. Before and after (2025)

`runs/2026-10-16-nl-patch-before-after-v27-v28/report.md` has all tables. Full grid, every hour of 2025: measured net
positions spread over each zone's 380 kV buses (same buses before and after; the new buses get no injection). Internal
Dutch flows are therefore the exchange-driven part only, not real loadings, which depend on Dutch generation and load
locations the model does not have.

| corridor (sum of circuits) | mean abs. MW before → after | p95 abs. MW | MW per 1,000 MW NL→BE | MW per 1,000 MW BE→DE |
|---|---|---|---|---|
| Krimpen – Diemen (1 circuit) | 113 → 69 | 250 → 157 | 65 → 48 | −82 → −54 |
| Krimpen – Breukelen Kortrijk | 103 → 64 | 236 → 155 | 77 → 59 | −83 → −54 |
| Breukelen Kortrijk – Diemen | 142 → 97 | 303 → 208 | −44 → −26 | 83 → 54 |
| Diemen – Oostzaan | 70 → 158 | 166 → 352 | −33 → 8 | 0 → −67 |
| Beverwijk – Oostzaan (new) | — → 105 | — → 225 | — → −42 | — → 67 |
| Beverwijk – Vijfhuizen (new) | — → 105 | — → 225 | — → 42 | — → −67 |
| Bleiswijk – Vijfhuizen (new) | — → 105 | — → 225 | — → −42 | — → 67 |
| Bleiswijk – Krimpen | 265 → 225 | 629 → 518 | 127 → 164 | 0 → −60 |
| Ens – Oudehaske, Oudehaske – Louwsmeer, Louwsmeer – Bergum, Bergum – Vierverlaten (new) | 0 → 0 | 0 → 0 | 0 | 0 |

- **Amsterdam ring**: Krimpen–Diemen, Krimpen–Breukelen and Breukelen–Diemen lose a third to 40 % of their exchange flow
  to the new western path Diemen–Oostzaan–Beverwijk–Vijfhuizen–Bleiswijk. Before, Diemen–Oostzaan carried only Oostzaan's own share of the Dutch
  injection, because Oostzaan was a dead end.
- **Snapshots** (largest Dutch export, 2025-03-14 14:00 UTC, +7,667 MW):
  - Krimpen–Diemen −123 → −44 MW;
  - Diemen–Oostzaan −256 → −440 MW;
  - each new corridor 185 MW.

  Largest import (2025-01-25 07:00 UTC, −4,995 MW): new corridors 45 MW.
- **Northern 220 kV ring**: it is now closed, but in JAO's data it touches the 380 kV grid only at Ens (Ens 380/220
  transformers), so no exchange flow can pass through it, before or after. It would carry flow with a second coupling, e.g.
  the Vierverlaten 380/220 kV transformers (§6 item 5) or Dutch generation and load in the north. The patch matters there
  for N-1, not for the exchange flows.

JAO line-by-line check (scripts/90 on 2026 JAO data; our share of an exchange on JAO's monitored elements against JAO's;
same 4,089 comparisons):

| | within ±25 % of JAO before → after | off by 2× or more | median ours / JAO |
|---|---|---|---|
| TenneT NL elements (829 element-outage pairs, 47 elements) | **74 % → 83 %** | 5.8 % → 2.3 % | 0.99 → 1.03 |
| all operators | 45 % → 47 % | 15 % → 14 % | 1.06 → 1.09 |

Biggest changes:

| JAO-monitored line | median ours / JAO, before → after | within ±25 %, before → after |
|---|---|---|
| Diemen–Krimpen Zwart | 1.80 → 1.07 | 0 → 100 % |
| Oostzaan–Diemen Zwart | 0.33 → 0.92 | 0 → 100 % |
| Oostzaan–Diemen Grijs | 0.33 → 0.89 | 0 → 100 % |
| Krimpen–Breukelen Kortrijk Wit | 1.53 → 1.01 | 0 → 100 % |
| Lelystad–Ens (both circuits) | 1.08 → 1.19 | 91 → 64 % (worse) |

So the Amsterdam distortion the brief describes was real and the patch removes it. Diele–Meeden and Maasbracht–Oberzier
move from 10–15 % to 65–100 % within ±25 %, but their medians barely change (1.26 → 1.24/1.25): that is a threshold effect,
not an improvement. RTE's elements go from 31 % to 26 % within ±25 % (61 comparisons).

2025 validation of the reduced network (what Tulipa uses; `replay2025/scripts/53`):

| | v27 | v28 |
|---|---|---|
| routing r / mean abs. error, 19 borders | 0.896 / 0.387 GW | 0.896 / 0.387 GW |
| BE–NL, DE–NL mean abs. error | 0.589, 0.589 GW | 0.587, 0.587 GW |
| hours inside every limit: present (no N-1) | 83.7 % | 83.7 % |
| hours inside: N-1 380 kV | 87.4 % | 88.2 % (NL–DE limit 2,665 → 2,736 MW; hours over 9.2 → 8.4 %) |
| hours inside: option 3 (N-1 + phase shifters + 10 % margin) | 91.7 % | 91.7 % |

- **Expected**: the Netherlands is one node in the reduced network, so the Randstad ring hardly changes the zone-to-zone
  equivalent. The patch's effect is inside the country.
- **Option 3 limit changes**:
  - all branch limits within ±15 MW, except BE–NL 3,781 → 3,617 MW (−4 %);
  - that limit is set by the FR→NL exchange, whose limit with phase shifters fell from 6,911 to 6,640 MW;
  - which line binds there is not recorded by script 93: not identified.
- **Full-grid border routing**: r 0.919, mean error 0.325 → 0.326 GW. Side note: better than the reduced network's
  0.387 GW with these injections.

## 6. Section 2b — findings and proposals (nothing added; `patches/jao2026_nl/proposals_2b.csv`)

1. **Second Maasbracht–Dodewaard 380 circuit.** It exists in 2026, and already via Boxmeer.
   - **JAO's 2026 flow-based files** monitor these elements, and use them as outages, on all three days:
     - "Maasbracht - Boxmeer 380 Zwart" (49T000000000007A);
     - "Boxmeer - Dodewaard 380 Zwart" (49T000000000006C);
     - "Boxmeer-Boxmeer 380 Zwart" (49T000000000149R), with imax 2,498 / 2,875 A;
     - one outage takes all three out together.
   - **IP2026 annex 4** lists bottlenecks "Maasbracht-Boxmeer 380 kV" (2034), "Maasbracht-Boxmeer-Dodewaard 380 kV" (1572),
     "Station Boxmeer 380 kV" (1736) and "Boxmeer 380/150 kV-transformatoren" (1438).
   - **IP2026 projects**: A-1003079 "verzwaren" (reinforce, 2031–34) and A-1003068 "Boxmeer 380 kV realiseren station"
     (2030–31), which I read as a full station replacing today's connection.
   - **Against**: absent from JAO's static file.
   - **Proposal**: one row `Maasbracht-Dodewaard380 Z`, MAASBRACHT_380 – DODEWAARD_380, X 31.1291 Ω (15.2709 + 15.8582),
     112.44 km, 2,000 A (GridAware's lower segment), 1,385.6 MW. Electrically the same as two segments while Boxmeer has no
     injection in the model.
   - **Question**: GridAware's 2,000 A, or JAO 2026's 2,498 A?
2. **Zwolle 380 / Hessenweg 220 transformer.** Not recommended without a source.
   - **No evidence**: no such transformer in JAO's static file; no element named Hessenweg anywhere in JAO's 2026 files;
     IP2026 lists 380/220 kV transformer bottlenecks only at Eemshaven, Ens, Meeden and Vierverlaten.
   - **GridAware's values are formula values**: X 12.3771 Ω = 0.15 · 380² / 1,750 MVA; no current.
   - **If added**: Voltage_level 380 (X stays on the 380 kV base GridAware used); current 2,659 A from 1,750 MVA at 380 kV;
     1,842.1 MW with k = 400.
3. **Wijk aan Zee 380 / Hollandse Kust Noord–West.**
   - **In JAO's file**: 6 rows Hollandse Kust Noord Landstation – Wijk aan Zee 380. The builder kept 3 (EIC duplicates;
     the X values of the two copies differ, flagged) and then excluded them as an isolated fragment, because nothing joins
     Wijk aan Zee to the grid in JAO (data request no. 1 of 13 Sept).
   - **Needed to add it**:
     - nodes WIJK AAN ZEE_380 and HOLLANDSE KUST NOORD LANDSTATION_380;
     - those JAO rows;
     - GridAware's 4 Beverwijk – Wijk aan Zee cables (1.0266 Ω, 5.8 km, 1,474 A each). Beverwijk now exists, so they would
       join it.
   - **GridAware's WAZ380:HNL220 transformer and the HKW nodes** are formula values or offshore details.
   - **Offshore wind in the model now**:
     - In Tulipa (2035 folder) Dutch offshore wind is a set of producers, all on the single NL node:
       NL00_Wind_Offshore 18,824 MW, plus hubs NL0U 700 MW and NL0J, NL0K, NL0W, NLLL 2,000 MW each. The landing point
       plays no role.
     - In the 2025 test only net positions are used.
     - In the limit calculation an exchange is spread over the zone's 380 kV buses, including the Hollandse Kust Zuid and
       Zeeuwse Kust landing stations.
   - **Recommendation**: later, only needed if offshore wind is placed at its landing point.
4. **Full node diff** (`patches/jao2026_nl/node_diff.csv`).
   - **the GridAware file** has 76 stations at 220/380 kV:
     - 48 are in the workbook (41 Dutch, 7 German/Belgian border stations); Robbenplaat counts there because the builder
       merged it into Eemshaven 220;
     - 2 added by this patch;
     - 1 in JAO's file but excluded (Wijk aan Zee);
     - 25 absent from JAO.
   - **The workbook** has 2 Dutch buses GridAware does not: VIERVERLATEN_380 and ZEEUWSE KUST LANDSTATION_380.

   | GridAware stations absent from JAO | connects to | recommendation |
   |---|---|---|
   | Boxmeer 380 | Maasbracht, Dodewaard | item 1 |
   | Wijk aan Zee 380 (excluded), Hollandse Kust Noord 220, HKW Alpha/Beta/North 220 | Beverwijk; offshore | item 3 |
   | Hoek van Holland 380 | Maasvlakte, Westerlee | later: on a through path; JAO has Maasvlakte–Westerlee as a direct double circuit, GridAware one path via Hoek van Holland, so the topology differs: check |
   | Doekegat 380, Diemer Vijfhoek 380, Enecogen 380, Maasstroom centrale 380, Oostpolder 220 | one station each | not needed: radial; they carry only their own injection, which the zonal model does not place there |
   | BritNed, COBRA, NorNed ends; Waddenweg converter station 380 | one station each | not needed: HVDC terminals (DC links are transport flows in Tulipa) |
   | Gemini (Eemshaven-Gemini 380/220, Windpark Gemini 1/2), Hollandse Kust Zuid 220 and Alpha/Beta, Borssele Alpha/Beta 220, ZKL220 | landing stations, offshore | later: only with offshore wind at its landing point |

5. **Eemshaven Oudeschip – Vierverlaten 380 (flag).** VIERVERLATEN_380 has only its two circuits to Eemshaven Oudeschip, so
   it is a dead end and carries no flow in our model.
   - **Evidence that it is not a dead end in reality**:
     - JAO's 2026 files monitor both circuits, and their zonal PTDFs for Belgium and Germany are small but not zero
       (+0.005 and −0.002). A line without an onward connection would not carry flow from other zones' exchanges.
     - IP2026 bottleneck 1578 is "Vierverlaten 380/220 kV-transformatoren".
   - **Data**: neither JAO's static file nor the GridAware file has these transformers.
   - **Consequence**: this is also why the closed northern 220 kV ring carries no exchange flow (§5).
6. **Borssele–Rilland circuit O (flag, nothing changed).** It is JAO's own row, not a manual edit.
   - **What JAO lists**: circuits G, O, P, Z. O and P both carry the EIC "Unknown" and 4,000 A, with different X
     (10.03 / 10.02 Ω) and B (181.38 / 182.97 µS), so they are two circuits.
   - **What our builder did**: it dropped P as an "EIC duplicate" of O. That rule is meant for tie-lines listed by both
     operators; "Unknown" is not an EIC. P is the only row dropped this way.
   - **Consequence**: our grid has 3 Borssele–Rilland circuits instead of 4. Restoring P is a builder change: your call.

## 7. Open questions

1. Item 1: add the second Maasbracht–Dodewaard circuit, and with which current: GridAware's 2,000 A or JAO 2026's 2,498 A?
2. Item 2: leave the Zwolle/Hessenweg transformer out until GridAware gives a source?
3. Item 5: look for data on the Vierverlaten 380/220 kV transformers (TenneT)? Without them the northern ring stays
   flowless for exchanges.
4. Item 6: restore Borssele–Rilland P (builder rule: "Unknown" is not an EIC)?
5. EICs: the patch rows carry PATCH-NL placeholders, as asked. JAO's own EICs for the same circuits are known (table §3).
   Use them instead? The JAO line-by-line check could then also compare outages of these lines.
6. Carry v28 forward to the Tulipa folder (option-3 limits on v28; BE–NL −164 MW)?
7. Git: `dcopf/` has no repository (decision 1 of 13 Sept), so no commits were made. Hashes are in every manifest.
   Start one for the scripts?

## 8. Deviations from the brief, and housekeeping

- **The brief's references to the other repository are not here**: `DATA/`, `contrib/amir_newlines_ip26`,
  `tests/test_contrib_isolation.py`, the staging loader with its E2a duplicate handling, `IP26_new_lines_summary_v4.pdf`.
  What I did instead:
  - registered the GridAware file as an input;
  - checked duplicates explicitly (the 8 edges are plain `branch:` records, and no `manual:` copy or segment joins the
    same stations);
  - wrote my own isolation test.
- **Coordinates**: brief's RD values, published approximation instead of pyproj (§3).
- **First build superseded**: the first build (script 95) is kept as `patches/jao2026_nl_SUPERSEDED-evidence-order`, with
  the script as run. Its patch rows are identical; its CHANGELOG cited the first IP2026 record in file order, the
  Borssele–Rilland project for Beverwijk–Vijfhuizen. Script 96 (a copy) ranks each corridor's own project first.
- **Scope of the check**: the brief asked for "at least one 2025 snapshot"; all 8,760 hours were run, plus two snapshots.

## 9. Next steps (proposal)

1. **Decide the 2b items** (§7), then build them as a second patch on v28 → v29: `scripts/96` style plus `97`.
2. **Tulipa**: if v28 is carried forward, rebuild the folder with script 73 and the v28 option-3 `branches_for_73.csv`,
   then the two test days. Optionally find which line sets FR→NL with phase shifters (BE–NL −164 MW).
3. **JAO's EICs** for the patch rows (question 5), then rerun the JAO line-by-line check.
4. **Internal Dutch flows**: they can only be judged with Dutch generation and load placed at nodes. That needs data the
   model does not have (GridAware's 150/110 kV network plus unit locations). Separate task, if wanted.
5. **The 2035 / IP2026 change list** (Part 2), when you say so.

## 10. Independent review, decisions, second patch → v29 (same day)

**Review.** An independent session reviewed the patch against the user's review brief: `reviews/jao2026_nl_patch/REVIEW.md`
(13 rerunnable scripts, own recomputation of every row, own power flow, rerun of the reduction). Verdict **accept**, no
blocker or major issue, seven minor findings. Nothing outside its folder was written (96 input/output hashes identical
before and after). F-01, F-02 and F-06 are folded into §2–3 above. F-03: the 3,300 A (Beverwijk–Oostzaan) and 2,500 A
(Bergum–Vierverlaten) ratings cannot be checked against JAO (no imax published for them); open. F-04: scripts/97 read
`substation_map.csv` with pandas and wrote it back, re-serialising 1,592 untouched lines ("3,6" → "3.0,6.0"; no semantic
change) in v28; fixed below. F-05: the brief expected the northern 220 kV ring to carry flow; it cannot (§5), the brief's
expectation was wrong. F-07: cosmetic (GridAware's 6-decimal precision; Bleiswijk → Vijfhuizen orientation, JAO's own).

**User decisions (2026-10-16, on §7):** 1 add the second Maasbracht–Dodewaard circuit with JAO's current; 2 Zwolle/Hessenweg
transformer: leave out; 3 Vierverlaten 380/220 kV transformers: no (logged as data request); 4 restore Borssele–Rilland P;
5 EICs: placeholders in the workbook, translation in the comparison scripts; 6 Tulipa folder: not yet; 7 fix the review
findings; 8 only 220 kV and above for now.

**Patch 2** `patches/jao2026_nl_2` (`scripts/99_build_nl_patch2.py v28 jao2026_nl_2`):

| patch id | row | values | source |
|---|---|---|---|
| BOXMEER_380 | node, NL 380 kV, 51.62 N 5.89 E | defaults of the Dutch 380 kV nodes | IP2026 project point "Boxmeer 380 kV realiseren station", RD → WGS84 |
| PATCH-NL-0009 | Maasbracht-Boxmeer380 Z | X 15.270864 Ω, 54.54 km, 2,498 A, 1,730.7 MW | X, length: GridAware `branch:MBT-BMR-DOD380 Z:seg1`; current: JAO 2026 element 49T000000000007A |
| PATCH-NL-0010 | Boxmeer-Dodewaard380 Z | X 15.858223 Ω, 57.90 km, 2,498 A, 1,730.7 MW | GridAware `…:seg2`; JAO element 49T000000000006C |
| PATCH-NL-0011 | Borssele-Rilland380 P | X 10.02 Ω, 39.5 km, 4,000 A, 2,771.3 MW | JAO's raw file row (EIC "Unknown"), builder's mean-of-ratings rule |

- The circuit is modelled as JAO does, two segments through Boxmeer: electrically the same as one direct row while Boxmeer
  has no injection, and one-to-one with JAO's elements for the translation. x′ 0.280 and 0.274 Ω/km (W circuit 0.274).
- Current: JAO publishes 2,498 A in July 2026 and 2,875 A in January; the user chose 2,498. Alternatives recorded in the
  patch manifest: builder's mean rule 2,686.5 A; GridAware 2,000 / 2,875 A. Deviation from the brief's "values from GridAware": the
  rating comes from JAO (the brief itself forbids replacing a JAO rating by GridAware's).
- `eic_alias.csv`: JAO 49T000000000007A → PATCH-NL-0009, 49T000000000006C → PATCH-NL-0010; "Boxmeer-Boxmeer 380 Zwart"
  (49T000000000149R, an element inside the station) ignored in an outage set only when a segment is in the same set.
- Borssele–Rilland P: JAO's own row, dropped by the builder on 13 Sept as an "EIC duplicate" of O because both carry
  "Unknown" (the only row dropped that way). Placeholder EIC because "Unknown" is not an identifier. Radial corridor: no
  effect on any flow; corridor capacity 7,258 → 10,029 MW.

**v29** = v27 + `jao2026_nl` + `jao2026_nl_2` by `scripts/100_apply_workbook_patches.py` (copy of 97: a sequence of
patches, each checked against the version it was built for — the intermediate after patch 1 must equal v28 — and the
copied files kept byte for byte, new station-map rows appended as text with the file's CRLF; F-04 fixed). Re-applying
both patches to v29 adds nothing. v28 stays as the reviewed intermediate; its station map has the cosmetic re-serialisation.
Reduction `runs/2026-10-16-stage2-v29-LP-virtual` (3,224 branches, 1,756 buses, NL 45; existing bus ids unchanged,
BOXMEER_380 appended); fit `runs/2026-10-16-sparse-fit-v29-sparse-LP`; limits `runs/2026-10-16-limits-v29-n1-380kv`,
`…-n1-380kv-pst-frm10`; 2025 tests `replay2025/runs/fixedposdc_diag_fixedpos_v29-sparse-LP*`; JAO check with translation
`runs/2026-10-16-share-check-vs-jao-v29` (`scripts/101_share_check_vs_jao_alias.py`: 10 JAO codes → placeholders, 1
ignored); before/after `runs/2026-10-16-nl-patch-before-after-v28-v29`. Tests: 20 pass (`tests/test_nl_patch2_jao2026.py`).

| | v28 | v29 |
|---|---|---|
| 2025 routing, reduced network: r / mean abs. error, 19 borders | 0.896 / 0.387 GW | 0.896 / 0.387 GW |
| hours inside every limit: present / N-1 380 kV / option 3 | 83.7 / 88.2 / 91.7 % | 83.5 / 88.8 / 91.7 % |
| option-3 branch limits that moved by more than 10 MW | | BE–NL 3,617 → 3,732; DE–NL 5,296 → 5,398; BE–DE 2,960 → 2,941; DE–FR 3,882 → 3,893 |
| full grid: border fit r / MAE | 0.919 / 0.325 GW | 0.919 / 0.326 GW |
| JAO check: combinations involving patched lines | 0 | 69 |
| JAO check: TenneT NL within ±25 % | 83 % (47 elements) | 78 % (50 elements) |
| Maasbracht–Dodewaard W, our share / JAO's | 1.97 | 1.42; Boxmeer segments 1.36 and 1.27 |
| Bleiswijk–Vijfhuizen Paars (JAO-monitored), our share / JAO's | not compared | 0.61–0.97 |
| Borssele–Rilland G and Z, our share / JAO's | 0.61 | 0.39 |

Reading:
- The second circuit brings Maasbracht–Dodewaard W from twice JAO's share to 1.4 times, but the corridor as a whole still
  carries 1.3–1.4 times what JAO gives it: our grid routes more of the Belgian and German exchanges through Maasbracht–
  Dodewaard than JAO's. The TenneT NL figure falls from 83 to 78 % only because the 57 newly compared Boxmeer combinations
  sit at 1.25–1.4; no earlier comparison got worse. Not resolved by this patch; candidates (not investigated): JAO's
  generation keys around Maasbracht/Eindhoven, the 150 kV grid (outside scope, decision 8), GridAware's Randstad-south values (F-01).
- Borssele–Rilland G/Z fall from 0.61 to 0.39 of JAO's share because four circuits now share Borssele's even-spread
  injection; JAO's keys put real generation at Borssele. A key effect, not a topology one.
- Full grid: the Boxmeer circuit carries 90 MW on average (p95 204 MW); Dodewaard–Doetinchem +49 MW, Maasbracht–Dodewaard W
  −39 MW; nothing else beyond 12 MW.
- Reduced network: the N-1 380 kV set gains 0.6 points; option 3 is unchanged at 91.7 %; its BE–NL and DE–NL branch limits
  rise back by about 100 MW.

Open after this: F-03 ratings; the Vierverlaten 380/220 kV transformers (data request 10); the Maasbracht–Dodewaard
corridor at 1.3–1.4× JAO; the Tulipa folder on v29 (user: not yet).

```
cd dcopf; PY=~/.tulipa_pipeline_venv/bin/python
$PY -W ignore scripts/99_build_nl_patch2.py v28 jao2026_nl_2
$PY -W ignore scripts/100_apply_workbook_patches.py v27 v29 patches/jao2026_nl patches/jao2026_nl_2
DERIVED_VERSION=v29 REP_NODE_MODE=manual_excel MIQP_CAP_S=1800 ~/.juliaup/bin/julia --threads=4,0 scripts/11_stage1_jao_diagnostics.jl 2026-10-16-stage2-v29-LP-virtual LP virtual
$PY -W ignore scripts/58_sparse_fit_split.py runs/2026-10-16-stage2-v29-LP-virtual v29-sparse-LP
$PY -W ignore scripts/83_limits_spread_monitored_n1.py runs/2026-10-16-stage2-v29-LP-virtual v29 n1-380kv --monitored=380kv
$PY -W ignore scripts/93_ttc_with_pst_margin.py runs/2026-10-16-stage2-v29-LP-virtual v29 n1-380kv-pst-frm10 runs/2026-10-16-limits-v29-n1-380kv --neutral-name=n1-380kv-frm10 --margin=0.10
$PY -W ignore scripts/101_share_check_vs_jao_alias.py runs/2026-10-16-stage2-v29-LP-virtual v29 v29
cd ../replay2025; for n in "" -n1-380kv -n1-380kv-pst-frm10; do $PY -W ignore scripts/53_fixed_position_test_dc.py ../dcopf/inputs/derived/diag_fixedpos_v29-sparse-LP$n; done
cd ../dcopf; $PY -W ignore scripts/98_nl_patch_before_after.py v28-v29 runs/2026-10-16-stage2-v28-LP-virtual runs/2026-10-16-stage2-v29-LP-virtual ../replay2025/runs/fixedposdc_diag_fixedpos_v28-sparse-LP_single ../replay2025/runs/fixedposdc_diag_fixedpos_v29-sparse-LP_single runs/2026-10-16-share-check-vs-jao-v28 runs/2026-10-16-share-check-vs-jao-v29
cd ..; $PY -m unittest discover -s dcopf/tests -v
```

## Reproduce (v28, the reviewed version)

```
cd dcopf; PY=~/.tulipa_pipeline_venv/bin/python
$PY -W ignore scripts/96_build_nl_patch_from_gridaware.py v27 jao2026_nl
$PY -W ignore scripts/97_apply_workbook_patch.py v27 patches/jao2026_nl v28
DERIVED_VERSION=v28 REP_NODE_MODE=manual_excel MIQP_CAP_S=1800 ~/.juliaup/bin/julia --threads=4,0 scripts/11_stage1_jao_diagnostics.jl 2026-10-16-stage2-v28-LP-virtual LP virtual
$PY -W ignore scripts/58_sparse_fit_split.py runs/2026-10-16-stage2-v28-LP-virtual v28-sparse-LP
$PY -W ignore scripts/83_limits_spread_monitored_n1.py runs/2026-10-16-stage2-v28-LP-virtual v28 n1-380kv --monitored=380kv
$PY -W ignore scripts/93_ttc_with_pst_margin.py runs/2026-10-16-stage2-v28-LP-virtual v28 n1-380kv-pst-frm10 runs/2026-10-16-limits-v28-n1-380kv --neutral-name=n1-380kv-frm10 --margin=0.10
$PY -W ignore scripts/90_share_check_vs_jao_tagged.py runs/2026-10-16-stage2-v28-LP-virtual v28
cd ../replay2025; for n in "" -n1-380kv -n1-380kv-pst-frm10; do $PY -W ignore scripts/53_fixed_position_test_dc.py ../dcopf/inputs/derived/diag_fixedpos_v28-sparse-LP$n; done
cd ../dcopf; $PY -W ignore scripts/98_nl_patch_before_after.py v27-v28 runs/2026-10-14-stage2-v27-LP-virtual runs/2026-10-16-stage2-v28-LP-virtual ../replay2025/runs/fixedposdc_diag_fixedpos_v27-sparse-LP_single ../replay2025/runs/fixedposdc_diag_fixedpos_v28-sparse-LP_single runs/2026-10-14-share-check-vs-jao-v27 runs/2026-10-16-share-check-vs-jao-v28
cd ..; $PY -m unittest discover -s dcopf/tests -v
```
Logs: `notes/stage2_v28_2026-10-16.log`, `notes/share_check_v28_2026-10-16.log`, `notes/limits_v28_n1-380kv_2026-10-16.log`,
`notes/ttc_pst_frm10_v28_2026-10-16.log`. JAO data: analysis only, not for redistribution.
