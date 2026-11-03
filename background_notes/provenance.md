# Provenance log of `core_grid_dcopf` (continues `archive/dcopf/notes/provenance.md`)

- **2026-10-16 — folder created** (user: "open a new folder and somehow clean everything up and simplify as much as possible …
  self-contained … the rest archive"). Distilled from `dcopf/` and `replay2025/`, which were moved to `../archive/` afterwards
  with nothing deleted. Contents: the seventeen scripts of the chain as verbatim copies of their archived originals with path
  edits only (`MAP.md`: engine import name, phase-shifter inventory folder, validation-data folder, Tulipa baseline folder, the
  scripts' own names in manifests), plus the new `03_monitored_set.py` (the rule of note 20, checked to reproduce the list of
  2026-10-16 exactly: 1,368 EICs, 60 rows excluded) and the two drivers `run_chain.sh`, `run_chain_nodal.sh`. Data copied:
  workbooks v29, v29-2035-amir, v29-2035-tennet (v29-nl380 is rebuilt by 12); JAO raw release; phase-shifter inventory
  (`archive/dcopf/runs/2026-10-06-pst-inventory`); monitored sets of 2026-10-16; the Dutch and IP2026 patches; the Tulipa
  baseline copy `2035_v2` (made read-only); the two 2025 validation tables with their fetch manifest; `Project.toml`,
  `Manifest.toml`; the process PDF and notes 14, 17–22.
- **2026-10-16 — verification** (`VERIFICATION.md`): `run_chain.sh v29 2026-10-16 ge1km`, `run_chain.sh v29 2026-10-16 380kv`
  and `run_chain_nodal.sh v29 2026-10-16` run here; every output equals the archived run of the same name to floating-point
  precision, including the Tulipa folder (byte-identical tables) and the test-day objectives (identical to the last digit).
- **Decisions in force on 2026-10-16** (details and dates in the archived log): base workbook v29; ratings √3·k·Ī; N-1 every
  record out; exchange spread over the zone's 380 kV buses; monitored = 380 kV lines of at least 1 km (adopted 2026-10-16, with
  the sub-kilometre rows between representative buses added for the nodal network); phase shifters set per exchange, reactance
  not added; 10 % margin; the archived v29 Tulipa folder (every 380 kV line monitored) stays in use unchanged; the nodal
  Netherlands waits for the user's demand/supply keys; side branches not adopted: phase-shifter reactance (v30-pst), seasonal
  ratings (v31).
- **2026-10-19 — status report** (user: "a summary of where we are at right now, the decisions … what is missing … in a PDF").
  `scripts/report_status.py` → `docs/status_report_2026-10-19.pdf` (6 pages: summary, status per workstream, method, decisions,
  results, open items, known limits, locations). A first build with a stranded heading kept as `…_SUPERSEDED-orphan-heading.pdf`.
- **2026-10-19 — grid map** (user: "make a map ... the 380, the 220, the links between them, the rings ... What is missing?").
  `scripts/map_nl_grid.py v29` → `docs/map_nl_grid_v29.pdf` (+ `_p1.png`, `_p2.png`): page 1 the whole Dutch grid (380/220 kV,
  transformers, ties, lines added by our patches, the two 220 kV pieces); page 2 the north with the missing Vierverlaten and
  Zwolle/Hessenweg couplings (data requests 10 and 11). Workbook coordinates only (0.01°), no coastline; co-located buses drawn apart.
- **2026-10-19 — 2035 grid maps** (user: "make the same map for the 2035 grid"). `scripts/map_nl_grid_2035.py` (copy of map_nl_grid.py
  with the 2035 changes marked, rows compared by position against v29; a first draft matched rows by name + EIC and wrongly listed two
  foreign lines as changed, fixed before writing) → `docs/map_nl_grid_v29-2035-amir.pdf` (18 changed + 3 new rows, all Dutch, = the
  patch files) and `docs/map_nl_grid_v29-2035-tennet.pdf` (11 + 2).
- **2026-10-19 — source re-check of the northern 380/220 kV couplings** (user: there should be a second coupling of the 220 kV ring;
  "you haven't found this on either the JAO, GridAware's data and on the IP folder, right?"). Searched again:
  JAO static grid model (all sheets): no transformer at Vierverlaten or Zwolle/Hessenweg; JAO flow-based files (Sept 2026, Jul 2026):
  Vierverlaten only as an end of the Vierverlaten – Eemshaven Oudeschip 380 kV circuits, no transformer element;
  GridAware full_network.csv: Vierverlaten 220/110 kV and Hessenweg 220/110 kV transformers, no 380/220 at Vierverlaten, Zwolle 380 /
  Hessenweg 220 only as a "curated_transformer" with formula values; IP2026: CONFIRMS both exist without electrical data —
  bottleneck 1578 "Vierverlaten 380/220 kV-transformatoren", asset register "VVL TR426" (n-2/n-1 problem by 2035, solved by
  A-1002806 Vierverlaten – Ens 380 kV, realisation, nMIEK, 2035–2038); and A-1000065 "Hessenweg 220 kV vervangen transformator"
  (2027) linked to bottleneck 1128 "Transformatordoorvoeringen 220/380 kV". CORRECTION to archive notes/07 item 11, which said
  IP2026 shows 380/220 kV transformers only at Eemshaven, Ens, Meeden, Vierverlaten: Hessenweg is indicated too.
  A-1002806 is excluded from both 2035 grids (window ends 2038 > 2035), as in the decision table's projects.csv.
- **2026-10-19 — transformers in the TNO MATLAB data** (user: "were they using the transformers as well?"). Checked
  `archive/dcopf/inputs/external/tno_matlab_2024_10_16`: KronNewCapV2_avg.m reads pre-built .mat files; `lines_data` (2,718 branches,
  1,486 buses) has NO transformer branches (one row named "Schifflange PST"). Buses are named by station without voltage, and at 274 of
  the 1,486 nodes 220 and 400 kV lines meet: each station's voltage levels are merged into one node, i.e. every 380/220 kV transformer
  is a zero-reactance connection. Vierverlaten, Ens, Meeden, Eemshaven are such merged nodes (so the Friesland 220 kV ring IS coupled at
  Vierverlaten in TNO's network); Hessenweg (220 only) and Zwolle (400 only) are separate nodes. Our workbook (JAO data, 1,756 buses)
  keeps separate buses per voltage with the JAO transformer reactances.
- **2026-10-19 — assumed Vierverlaten 380/220 kV transformer** (user: "create the transformer for that other part of the ring ...
  representative of the grid"; "we're not going to claim anything"). SIDE BRANCH, not adopted; v29 unchanged.
  `scripts/14_build_patch_vierverlaten_tr.py` → `inputs/patches/nl_vierverlaten_tr_assumed_{2u,1u}` (units of X 31.529 ohm = median of
  the 8 Dutch JAO 380/220 kV units, 1,140 A / 789.8 MW; EIC ASSUMED-NL-TR-000n; 2 units central because IP2026 names the bottleneck in
  the plural); `scripts/13_apply_patches.py` (verbatim copy of archived 100) → `jao_core_v29-vvltr2`, `jao_core_v29-vvltr1`.
  `scripts/02n2_sparse_network_nodal_hv.py` (02n + node pairs joined through eliminated Dutch 220 kV buses) and driver
  `run_chain_nodal_hv.sh` (tag <v>-nl380-hv); run on v29, v29-vvltr1, v29-vvltr2 (date 2026-10-19). Check: v29 through 02n2 reproduces
  the archived nodal network exactly. Result (`scripts/15_compare_vierverlaten_tr.py` → `runs/2026-10-19-compare-vierverlaten-tr`):
  new equivalent branch Vierverlaten–Ens (X 0.047 / 0.036 p.u., option-3 limit 778 / 1,007 MW for 1 / 2 units); the ring carries 26 % /
  31 % of a Vierverlaten→Ens transfer and 14–22 % of Eemshaven exports south or to Germany; Meeden–Zwolle and Eemshaven–Meeden lose a
  fifth to a quarter of their share; option-3 limits of four northern branches rise 5–23 %, all other 56 unchanged (median 0.0 %), no
  other reactance moves; 2025 test (even placeholder key) unchanged at 91.6 % inside.
- **2026-10-19 — experiment: transformers vs merged stations** (user: "give me a verdict whether it's better or not").
  `experiments/2026-10-19_transformers_vs_merged/` (README.md = verdict, RESULT.md, scripts, runs). v29-merged = v29 with every station's
  voltage levels merged (TNO convention; 283 stations, 466 transformers removed; station key = zone + name, Monceau BE/FR distinct).
  Same chain and monitored lines. Verdict: keep the transformers — 2025 border-flow MAE 0.387 vs 0.413 GW, JAO shares on 220 kV lines
  35 % vs 22 % within ±25 %; merged slightly better on 380 kV lines (55 vs 53 %) and has looser limits (+3 % median, 98.1 vs 91.7 % hours
  inside); Dutch elements equal (82 %). Not adopted; v29 unchanged.
- **2026-10-19 — Zwolle 380 / Hessenweg 220 kV: NOT coupled** (user: "no theres no trafo there"). Archived data request 11 is closed:
  the two substations share a site but have no 380/220 kV transformer between them, so the earlier reading of IP2026 project A-1000065
  (bottleneck 1128 "Transformatordoorvoeringen 220/380 kV") as evidence for one is withdrawn. The Friesland – Overijssel ring couples to
  380 kV at Ens and Vierverlaten only — the topology of the variants v29-vvltr1/2. Maps corrected: `scripts/map_nl_grid_v2.py`,
  `scripts/map_nl_grid_2035_v2.py` → `docs/map_nl_grid_v29_v2.pdf`, `…_v29-2035-amir_v2.pdf`, `…_v29-2035-tennet_v2.pdf`; the earlier PDFs
  and PNGs renamed `…_SUPERSEDED-zwolle-coupling`.
- **2026-10-19 — HANDOVER.md written** at the top of this folder (user: migrating the work to another session and moving the folder).
  Noted there: the archive (`dcopf/`, `replay2025/`) is no longer in `~/TNO/TestTulipa_TYNDP2026 - MAIN/archive/` (empty at handover).
- **2026-10-19 — Tilburg 380 kV loop-in and the 2035 grids on the base v29-vvltr2** (user: "ok cool then lets add it ... patch
  it add things, run reductions etc"; work done from the nl_merge session, plan `../nl_merge/E0_core_grid_tilburg_loopin_plan.md`).
  Source: TenneT "Aanmeldingsnotitie m.e.r. hoogspanningsstation Tilburg" (002.678.21, 2 Feb 2022; ruimtelijkeplannen.nl plan
  NL.IMRO.0000.EZKip20Til380-1000, tb13; copy in the patch folder): the existing 380 kV line is looped into station Tilburg, 2 of 3
  circuits from 2027, the third once Zuid-West 380 kV Oost (Rilland–Tilburg) is ready → all 3 for 2035.
  `scripts/16_build_patch_tilburg_loopin.py v29-2035-tennet --circuits=3` → `inputs/patches/ip2026_nl_2035_tilburg_loopin_3c`
  (remove Geertruidenberg–Eindhoven380 G/W/Z; add Geertruidenberg–Tilburg380 and Tilburg–Eindhoven380 G/W/Z, length and X split
  0.337 / 0.663 by straight-line distance of the bus coordinates (detour 0.85 %), rating unchanged, EIC PATCH-NL35-TLB-000n assumed).
  `scripts/17_apply_patches_modify_remove.py` = copy of 13 + lines_modify / lines_remove + rebase check + --out-dir. Reproduction:
  17 applied to v29 with ip2026_nl_2035_tennet and with ip2026_nl_2035_amir reproduces `jao_core_v29-2035-tennet` and
  `jao_core_v29-2035-amir` (archived 113) sheet by sheet (scratch output, not kept). Built: `jao_core_v29-vvltr2-2035-tennet-tlb3`
  and `jao_core_v29-vvltr2-2035-amir-tlb3` = v29-vvltr2 + 2035 patch (rebased: 11 / 18 touched rows identical in v29) + loop-in
  (rebased from v29-2035-tennet: 3 touched rows identical). Checks: Lines 2,609 → 2,614 / 2,615, Nodes +1, Transformers 469
  (Vierverlaten units kept), TILBURG_380 8 rows (2 Rilland, 3 + 3 loop-in), no direct Geertruidenberg–Eindhoven row, one AC island.
- **2026-10-19 — nodal network on SR2025 32 nodes (2035, TenneT rule, Tilburg loop-in)**. Node set
  `inputs/nodesets/nl_ielgas_sander_32.csv` (27 × 380 kV + 5 × 220 kV-only: Bergum, Louwsmeer, Oudehaske, Zeyerveen, Weiwerd;
  Breukelen, Hessenweg and the landing spurs eliminated). `scripts/18_nodal_workbook_nodeset.py` (copy of 12, node set from a CSV)
  → `jao_core_v29-vvltr2-2035-tennet-tlb3-nlsander` (43 representatives = 32 NL + 11 zones). `01_reduce.jl` →
  `runs/2026-10-19-stage2-v29-vvltr2-2035-tennet-tlb3-nlsander-LP-virtual` (COMPLETED, 77 s). `02n2` →
  `inputs/derived/diag_fixedpos_v29-vvltr2-2035-tennet-tlb3-nlsander-hv-sparse-LP` (43 nodes, 64 branches, 47 touching NL incl. 6
  ties; Tilburg–Rilland/Geertruidenberg/Eindhoven, no Geertruidenberg–Eindhoven branch; northern 220 kV ring branches present).
  STOPPED before 03/04n: with 220 kV nodes the 380 kV-only monitored set (decision 13 Oct) leaves ring pairs without a monitored
  line (04n aborts on such pairs). Decision asked from the user.
- **2026-10-21 — limits for the nodal network on SR2025 nodes** (user: "add the Dutch 220 kV lines of at least 1 km to the
  monitored set (foreign 220 kV stays unmonitored), as a new script, then run the N-1 and option-3 limits and the 2025 test").
  `03_monitored_set.py v29-vvltr2-2035-tennet-tlb3` → `runs/2026-10-21-monitored-380kv-ge1km-…` (1,373 EICs).
  `scripts/03n2_monitored_set_nodal_nl220.py` (copy of 03n: + every Dutch 220 kV line ≥ 1 km, 20 rows; no abort without short
  rows between nodes) → `runs/2026-10-21-monitored-nodal-nl220-v29-vvltr2-2035-tennet-tlb3-nlsander` (1,393 EICs).
  `04n` → `runs/2026-10-21-limits-nodal-v29-vvltr2-2035-tennet-tlb3-nlsander-hv-n1-380kv-nl220-ge1km-nodal` (35 s, every branch finite).
  `05n` ABORTED on its capability check (Zandvliet–Rilland 1.186 × scripts/74, Van Eyck–Maasbracht 1.093): folder renamed
  `…-pst-frm10_ABORTED-pst-capability-check-2035grid`. Cause verified independently (full-grid Thevenin, DC): the loop-in makes
  Rilland–Tilburg a parallel path; factor vs today 1.175 / 1.084 with the loop-in, 1.000 without. `scripts/05n2_limits_pst_margin_nodal_gridref.py`
  (copy of 05n; only the check: 74's MW/deg scaled by the Thevenin factor of this workbook over v29, same 15 % tolerance) →
  `runs/2026-10-21-limits-nodal-…-n1-380kv-nl220-ge1km-nodal-pst-frm10` (scaled ratios 1.001–1.008; zero-angle limits reproduce 04n to
  4.4e-16), network **`inputs/derived/diag_fixedpos_v29-vvltr2-2035-tennet-tlb3-nlsander-hv-sparse-LP-n1-380kv-nl220-ge1km-nodal-pst-frm10`**
  (43 nodes, 64 branches). 2025 test with the even placeholder key (`runs/key_nl-even-…-nlsander-hv`): r 0.909, MAE 0.401 GW
  (19 borders), 91.7 % of hours inside (reference v29-vvltr2-nl380-hv: 0.909 / 0.401 / 91.6 %). Dutch option-3 limits: 33 branches
  shared with the 380 kV reference within ±4 % except the 2035 upgrades (Diemen–Krimpen 3,645 vs 1,482 MW: Breukelen eliminated +
  4 kA; Beverwijk–Oostzaan +21 %, Diemen–Oostzaan +33 %; Eemshaven–Meeden −7 %); new: northern 220 kV branches 300–1,147 MW,
  Rilland–Tilburg 3,763, Geertruidenberg–Tilburg 4,433, Eindhoven–Tilburg 4,985 MW.
- **2026-10-21 — country-level network on the same 2035 grid** (for the nl_merge case "NL one node + Core DC-OPF", user approved
  P2). `01_reduce.jl` on `v29-vvltr2-2035-tennet-tlb3` → `runs/2026-10-21-stage2-v29-vvltr2-2035-tennet-tlb3-LP-virtual` (68 s);
  `02_sparse_network.py` → `…-sparse-LP`; `04_limits_n1.py` with the SAME monitored set as the nodal run (380 kV ≥ 1 km + Dutch
  220 kV ≥ 1 km, `runs/2026-10-21-monitored-nodal-nl220-…-nlsander`) → `runs/2026-10-21-limits-v29-vvltr2-2035-tennet-tlb3-n1-380kv-nl220-ge1km`;
  `scripts/05b_limits_pst_margin_gridref.py` (copy of 05 with the 05n2 change: 74's MW/deg scaled by the Thevenin factor; scaled
  ratios 1.001–1.008, unscaled Zandvliet–Rilland 1.186) → network
  **`inputs/derived/diag_fixedpos_v29-vvltr2-2035-tennet-tlb3-sparse-LP-n1-380kv-nl220-ge1km-pst-frm10`** (12 zones, 19 branches;
  BE–NL 3,800 MW, NL–DE 5,704 MW). 2025 test: r 0.899, MAE 0.383 GW (19 borders), 91.9 % of hours inside (reference v29-vvltr2:
  0.895 / 0.387 / 91.7 %).
- **2026-10-23 — decisions and validation document for colleagues** (user: "a document that has the decisions we have made ...
  N-1, the >1 km rule, selection of nodes, PST, new results ... and what's still open"). Claude Doc "Core grid model for Tulipa:
  validation and decisions", https://claude.ai/artifact/MEJzijnweEW3NPS5FwHT2C. Supersedes the colleague note of 6 October (N-0 limits).
  Built from this folder's docs and the project memory notes; the archive was not reachable on disk.
- **2026-10-19 — decisions (entry restored on 2026-10-23; the original entry and the runs it named were missing from this folder)**
  (user: "use the two-unit Vierverlaten variant and rebuild with the 1 km rule"). (1) Base workbook = **v29-vvltr2** (v29 + 2 assumed
  Vierverlaten 380/220 kV units) for the country level and the nodal Netherlands. (2) Reference Tulipa folder built with the 1 km
  monitored rule: `run_chain.sh v29-vvltr2 2026-10-19 ge1km` → `inputs/derived/tulipa_dcopf_2035_base2b-v29-vvltr2-sparse19-n1-380kv-ge1km-pst-frm10`.
  Original results (19 Oct): DC-OPF 2.0486306e9 / 1.0968942e9 (NTC 2.0686255e9 / 1.0962268e9); against v29 with the same rule 19
  reactances < 0.49 %, option-3 limits < 0.30 %, 2025 test identical (r 0.895, MAE 0.387 GW, 91.7 % inside).
- **2026-10-23 — colleague document updated** (Claude Doc https://claude.ai/artifact/MEJzijnweEW3NPS5FwHT2C): new section "How the
  checks are calculated"; border-by-border table of measured vs model 2025 volumes, correlation, error and hours over the limit (from
  `runs/fixedposdc_diag_fixedpos_v29-sparse-LP-n1-380kv-ge1km-pst-frm10_single`; measured flows inside every option-3 limit 45.5 % of
  hours, 84.3 % without HR–HU and PL–SK; model 161 TWh vs measured 169 TWh over 19 borders); the decisions of 19–21 October from the
  nl_merge session added (Tilburg loop-in, SR2025 32 nodes, Dutch 220 kV ≥ 1 km monitored on those nodes, scaled phase-shifter check,
  country-level network on the 2035 grid) with their 2025-test results.
- **2026-10-23 — reference v29-vvltr2 rebuilt** (user: "also rebuild"). `run_chain.sh v29-vvltr2 2026-10-19 ge1km` rebuilt
  `runs/2026-10-19-stage2-v29-vvltr2-LP-virtual`, then wrote `runs/2026-10-23-sparse-fit-v29-vvltr2-sparse-LP` and
  `runs/2026-10-23-limits-v29-vvltr2-n1-380kv-ge1km` and STOPPED at 05: the scripts date their folders with today, the driver looks under
  the tag (flaw of the drivers: a past date tag fails; noted in HANDOVER.md, drivers not edited). Finished by hand: 05 →
  `runs/2026-10-23-limits-v29-vvltr2-n1-380kv-ge1km-pst-frm10` (+ networks `diag_fixedpos_v29-vvltr2-sparse-LP-n1-380kv-ge1km[-pst]-frm10`);
  10 → r 0.895, MAE 0.387 GW, 91.7 % inside; 06 → `inputs/derived/tulipa_dcopf_2035_base2b-v29-vvltr2-sparse19-n1-380kv-ge1km-pst-frm10`
  (+ day cuts); 08/09 → `runs/2026-10-23-stage3-pair-2035-01-0{4,9}-base2b-v29-vvltr2-…`: DC-OPF 2.048630593474912e9 / 1.0968942001639974e9,
  identical to the 19 October build to the last digit.
- **2026-10-23 — 2025 test of the nodal Netherlands with SR2025 keys** (user: "ok then go for option 1"). Node set
  `inputs/nodesets/nl_ielgas_sander_31_today.csv` (SR2025 32 minus Tilburg); workbook `jao_core_v29-vvltr2-nlsander31`; chain 01 →
  02n2 → 03n2 → 04n → 05n → network `inputs/derived/diag_fixedpos_v29-vvltr2-nlsander31-hv-sparse-LP-n1-380kv-nl220-ge1km-nodal-pst-frm10`.
  New scripts: `19_nl_node_injections_2025.py` (hourly Dutch node injections from the 2025 national series × SR2025 shares; offshore by
  ASSUMED 2025 landing capacities; links at landings; residual 1.48 GW mean by the demand key; balance to the Core net position asserted),
  `19b_nl_node_injections_2025_units.py` (copy of 19: offshore and coal by the ENTSO-E 2025 unit list; first run aborted on a trailing space
  in a unit name → `runs/_ABORTED-unitname-space_…`, fixed with strip before any result), `10n2_test_2025_nodal_injections.py` (copy of
  10n + `--injections`). Results (mean r 18 / MAE 19 / hours over / BE–NL MAE): country 0.895 / 0.387 / 8.3 % / 0.59; even key 0.909 /
  0.402 / 8.4 % / 0.79; SR2025 0.909 / 0.394 / 29.2 % / 0.74; SR2025 + 2025 units 0.909 / 0.392 / 32.4 % / 0.73. Success test (BE–NL and
  DE–NL below 0.59 GW) NOT met; split error is network-driven (same for every key); Dutch internal branches Bleiswijk–Wateringen and
  Eemshaven–Meeden bind with realistic injections. Note `docs/23_nodal_2025_test_sander_keys.md`.
- **2026-10-23 — phase-shifter check of the nodal 2025 split error** (user: "check the phase shifter idea first"). New
  `scripts/20_pst_check_2025.py` → `runs/pstcheck_nodal-sander-units2025`. Full grid neutral reproduces the split (BE–NL mean error
  0.66 vs 0.68 GW sparse). Constant angles fitted to measured 2025 flows within the RAO range: all five Dutch-border corridors at their
  range limit, BE–NL MAE 0.73 → 0.41 GW (mean error 0.15); hourly angles at the limit 86–98 % of hours. Phase shifters = possible partial
  explanation only, not adopted; no 2025 tap data. Next candidate (unchecked): single-bus placement of the other zones (Germany). docs/23.
- **2026-10-23 — zone placement check** (user: "ok check the german placement idea"). New `scripts/21_zone_placement_check_2025.py`
  → `runs/placecheck_nodal-sander-units2025` (+ `-north52.0`, `-north53.0`). German wind (ENTSO-E 2025) on German 380 kV buses ≥ 52.5° N
  (ASSUMED proxy), rest even: BE–NL mean error +0.66 → +0.06 GW, MAE 0.73 → 0.39; with other zones spread too, MAE 19 0.386 → 0.283.
  Phase-shifter fit then adds nothing → the split error comes from the one-bus German placement, not from phase shifters or the
  Dutch keys. Robust to 52.0/53.0° N. docs/23.
- **2026-10-23 — placement check on the country model** (user: "run the same check on the country model"). New
  `scripts/21b_zone_placement_check_2025_country.py` (copy of 21 accepting a 10_test run; NL at RILLAND_380) →
  `runs/placecheck_country-v29-vvltr2`. Full grid V0: MAE 19 0.375, BE–NL bias +0.60 (country sparse network +0.33); German wind north:
  BE–NL bias 0.00; V4 MAE 19 0.275. The 12-node sparse network's approximation error partly cancelled the German-placement error on
  BE–NL; the nodal sparse network tracks the full grid (0.68 vs 0.66). docs/23.
- **2026-10-23 — Dutch transfer capacity, country vs nodal** (user: "How does going from one zone to nodes change ... the total
  transfer capacity between the Netherlands and its neighbors?"). New `scripts/22_nl_transfer_capacity_compare.py` →
  `runs/transfercap_v29-vvltr2-country-vs-nlsander31`. Max bilateral transfer on the option-3 networks (other zones 0). NL↔BE+DE:
  country 9,193 MW (= sum of its two border-branch limits); nodal 14,883 (free Dutch placement, best case), 10,192 (even), 8,636 export
  with SR2025 generation key / 9,528 import with the demand key; the keyed/even cases are capped by Maasbracht–DE and by the Dutch
  internal Geertruidenberg–Krimpen branch. NL↔BE 5,293 → 5,974–6,344; NL↔DE 8,561 → 8,043–10,291.
- **2026-10-23 — full-grid check of the Dutch border room** (user: "yes run the full-grid check"; cross-check of the other session's
  "sum over ties" finding, G3_copper_step_check_NT_2035.md). Envelope confirmed per branch (05/05b/05n/05n2 line "C1 = (T1[None, :] * A).max(axis=1)").
  New `scripts/23_full_grid_border_check.py`: max transfer NL -> BE / DE / BE+DE on the FULL grid under option-3 rules (every record out,
  monitored set, 10 % margin, PST within range; single pairs reproduce 05n/05n2 pairs.csv exactly) vs the reduced nodal network.
  `runs/fullgridcheck_today-v29-vvltr2-nlsander31`, `runs/fullgridcheck_2035-tennet-tlb3-nlsander`. 2035 grid (MW, reduced / full grid):
  free BE+DE 14,974 / 12,094 (0.81), BE 6,416 / 5,300 (0.83), DE 10,356 / 10,322 (1.00); even BE+DE 10,696 / 9,011 (0.84); reduced
  optimum as fixed shape 0.70. NL as one zone on the full grid: BE+DE 9,157, DE 8,561, BE 5,031 (country network 9,504 / 8,561 / 5,317).
  Full-grid binding element on the Belgian side mostly Doel–Zandvliet. Today's grid the same within 1 %. Reading: the nodal network
  over-allows by ~20 % (Belgian side and combined exchanges); the German ties alone are right; the zone-level border (1N) is lower than
  what the full grid can securely carry with favourable Dutch placement (12.1 vs 9.2 GW). Nothing changed.
- **2026-10-23 — tie-correction variants and both checks** (user: "yes build the variant and run both checks"). New scripts
  `24_tie_correction_variant.py` (Belgian ties x f_BE so free NL->BE = full grid; then German ties x f_DE so free NL->BE+DE = full grid),
  `24b_tie_correction_variant_be_only.py` (copy, German ties unchanged), `23b_full_grid_border_check_transit.py` (copy of 23 + DE->BE and
  DE->FR transit). Variants (suffix `-tiefix`, `-tiefixbe`) of `diag_fixedpos_v29-vvltr2-nlsander31-hv-…-nodal-pst-frm10` (f_BE 0.830,
  f_DE 0.802) and `diag_fixedpos_v29-vvltr2-2035-tennet-tlb3-nlsander-hv-…-nodal-pst-frm10` (f_BE 0.826, f_DE 0.797). Check 1
  (`runs/fullgridcheck_{2035,today}{base,-tiefixbe,-tiefix}-transit`), reduced / full grid, 2035: original BE 1.21–1.25, DE 1.00–1.02,
  BE+DE 1.19–1.44, DE->BE transit 1.02; BE-only: BE 1.00–1.03, DE unchanged, BE+DE 1.16–1.25, transit 0.84; BE+DE: BE 1.00–1.03,
  DE 0.80–0.81, BE+DE 1.00–1.20, transit 0.84. Check 2 (2025 test, SR2025 units / even key): border statistics unchanged (reactances
  unchanged); hours with a tie over its limit 4 / 2 (original), 5 / 6 (BE only), 173 / 47 (BE+DE). Reading: no uniform tie scaling is
  right in every case (per-branch limits cannot express a joint border limit); BE-only is the smaller compromise. Not adopted.
- **2026-10-23 — 4 kA rating patch on the 2035 grid + main/lower tie variants** (request of the nl_merge dispatch session, plan
  approved by the user there: "rating fix in all cases; Belgian-only tie correction as MAIN; strict all-ties as LOWER"). New
  `scripts/25_build_patch_rating_4ka.py` → `inputs/patches/ip2026_nl_2035_rating_4ka` (Krimpen–Geertruidenberg380 W/Z, Maasbracht–
  Eindhoven380 W/Z: 3,300 → 4,000 A, 2,771.281 MW, X/R/B unchanged; IP2026 p.109 Table 8.5); 17 → `jao_core_v29-vvltr2-2035-tennet-tlb3-rt4k`
  (diff: exactly 4 rows); 18 → `…-rt4k-nlsander`; driver `scripts/run_chain_rt4k_2035.sh` (01 ×2, 02n2, 03, 03n2, 04n, 05n2, 02, 04, 05b).
  Reactances identical to the unpatched networks; monitored set identical (1,393 EICs). Limits: Geertruidenberg–Krimpen 3,010 → 3,496,
  Eindhoven–Maasbracht 3,827 → 4,213, Ens–Zwolle +1.5 %, Ens–Lelystad +1.1 %, country BE–NL 3,800 → 3,821 MW. Networks:
  nodal `inputs/derived/diag_fixedpos_v29-vvltr2-2035-tennet-tlb3-rt4k-nlsander-hv-sparse-LP-n1-380kv-nl220-ge1km-nodal-pst-frm10` (base,
  not for use), `…-tiefixbe` (MAIN, 24b: BE ties ×0.8261), `…-tiefix` (LOWER, 24: + DE ties ×0.7974); country
  `inputs/derived/diag_fixedpos_v29-vvltr2-2035-tennet-tlb3-rt4k-sparse-LP-n1-380kv-nl220-ge1km-pst-frm10`. Checks: 23b →
  `runs/fullgridcheck_2035rt4k-{base,tiefixbe,tiefix}-transit`; 2025 test (19b injections on the 2035 node set,
  `runs/nlinj_sander-units2025-v29-vvltr2-2035-tennet-tlb3-rt4k-nlsander`; even key `runs/key_nl-even-v29-vvltr2-2035-tennet-tlb3-rt4k-nlsander-hv`).
  Results in docs/25.
- **2026-10-23 — JAO 2025 active constraints (shadow prices) downloaded and analysed** (user: "yes download the JAO 2025 shadow
  prices"; question of the dispatch session on Krimpen–Geertruidenberg). `scripts/26_download_jao_shadow_prices.py` (month requests)
  ABORTED: the API allows at most 2 days per request (HTTP 400) → folder kept as `inputs/external/_ABORTED-month-range-400_jao_shadow_prices_2025`.
  `scripts/26b_download_jao_shadow_prices_daily.py` (copy, one request per day) → `inputs/external/jao_shadow_prices_2025` (365 daily
  raw JSON, 54,941 rows, 55 MB; JAO data, analysis only, not redistributed). `scripts/27_jao_active_constraints_nl.py` →
  `runs/jaosp_2025-krimpen-maasbracht`. Krimpen–Geertruidenberg 380 Wit active in 500 h of 2025 (900 MTUs; 15-min MTUs from October),
  always under N-1 of its own Zwart circuit, direction DIRECT in 897/900 rows; shadow price median 17.8, mean 37, max 460 EUR/MW;
  Fmax 2,286 MW (3,300 A; Apr–Aug 1,958 MW / 2,826 A): JAO still rated it at 3.3 kA throughout 2025 (4 kA only in the 2026-09-10 FB
  data). Second most frequent TenneT BV element after PST Meeden 2 (950 h). Active hours: NL net position 2,957 vs 1,707 MW year mean,
  NL->BE 1,820 vs 1,129 MW. Maasbracht–Eindhoven 380 Wit/Zwart: 103 h, mostly under N-1 Diemen–Lelystad, direction OPPOSITE,
  NL net position 4,758 MW in those hours. Earlier remark "today's grid understates K–G by 17 %" withdrawn: 3.3 kA is JAO's 2025 value.
- **2026-10-24 — Krimpen–Geertruidenberg: 2025 JAO vs 2035 runs** (user: "How does this compare to the congestion we see in our 2035
  runs, similar amount of hours? And reason is similar?"). Read-only, ad-hoc reads (no new script): JAO 2025 active rows
  (`runs/jaosp_2025-krimpen-maasbracht/active_rows_lines.csv`) have direction DIRECT = Krimpen -> Geertruidenberg (substationFrom/To in
  the 2026-09-10 FB file), hubFrom NL / hubTo BE: binding SOUTHBOUND, 500 h, with high NL exports to BE. Our 2025 test on today's grid
  (10n2, 19b injections): southbound 90 % of hours, over its limit 240 h. 2035 test weeks of the dispatch session
  (`../nl_merge/test_runs/{NT,SR}-NN-rt4k-tbe_*/var_flow.csv`, main case): binding 87–125 of 168 h per week, ALL NORTHBOUND
  (Geertruidenberg -> Krimpen), with DE -> NL imports of 4.4–8.3 GW in those hours, entering mostly at Maasbracht (2.1–3.3 GW) and
  Doetinchem (1.4–3.0 GW). Hypothesis (unchecked): the one-node Germany (Rommerskirchen, docs/23) sends German imports in at the southern
  ties and over Eindhoven–Geertruidenberg–Krimpen; part of the 2035 congestion may be an artefact of that.
- **2026-10-25 — Krimpen–Geertruidenberg 2035 vs German placement** (user: "yes run the check and send it to renewaflex"). New
  `scripts/28_kg_german_placement_2035.py` → `runs/kgplace_rt4k-tbe-testweeks` (6 test weeks NT/SR, main case rt4k-tbe; fixed Tulipa
  dispatch re-routed on the full 2035 rt4k grid; NOT an optimisation). V0 (one German bus) reproduces Tulipa (r 0.99–1.00; full-grid
  K–G >= 3,496 MW in 526 h vs 604 binding h in Tulipa). V1 Germany even: 386 h (−27 %). V3 German wind north (>= 52.5° N, assumed):
  14 h (−97 %), K–G southbound in 51 % of hours, Meeden/Hengelo imports up to ~11 GW. NOT credible as a 2035 estimate: German wind
  in the weeks averages 31–112 GW (max 182 GW) vs ~15 GW in 2025, placed on today's German grid (JAO SGM) without the planned 2035
  German HVDC corridors, so V3 forces a north–south transit through NL that the real 2035 system would not carry. Reading: the 2035 K–G
  congestion is highly sensitive to how Germany is represented (−27 % already with an even spread); its level is not robust. Tie-limit
  comparisons on the full grid were dropped (physical tie lines vs equivalent branches are not comparable).
- **2026-10-25 — German north/south split (ACER DE2)** (user: "build the German north/south split"; choices: ACER DE2 zones, HVDC
  from NEP + TYNDP, grid + split keys). Sources downloaded: ACER Decision 11/2022 Annex V/VI (`inputs/external/acer_decision_11_2022`,
  node list "DE2 - German TSOs"); ENTSO-E BZR 2025 output data (`inputs/external/entsoe_bzr_2025`, README: capacity per zone, hourly load
  CY09/89/95, explicit DSR; terms: no redistribution). New scripts: `29_de2_split_workbook.py` (zone per German bus: 50Hertz north,
  Amprion/TransnetBW south, TenneT north if lat >= 51.79 except Niederlangen; others by neighbours; DE_N rep WOLMIRSTEDT_380 by
  electrical centrality, DE_S rep ROMMERSKIRCHEN_380 kept), `02n3` (zone table + DE_N/DE_S), drivers `run_chain_rt4k_de2_2035.sh`,
  `run_chain_today_de2.sh`, `31_de2_split_keys.py` (→ `inputs/derived/de2_split_keys`: Tulipa DE00 assets and ENTSO-E types -> north
  share; load 0.3037), `30_de2_injections_2025.py`, `10n3` (copy of 10n2: zones DE_N/DE_S -> DE_LU), `23c` (copy of 23b, Germany = its
  nodes; reproduces 23b exactly on one-node networks; aborted on DE2 networks because 10n2 rejects DE_N/DE_S → `runs/_ABORTED-*`),
  `23d` (= 23c importing 10n3), `24c` (tie correction with German nodes; modes main/lower). Workbooks `jao_core_v29-vvltr2[-2035-tennet-tlb3-rt4k]-de2[-nlsander(31)]`
  (109 / 215 German buses N/S, identical in both grids). Networks: 2035 nodal `diag_fixedpos_v29-vvltr2-2035-tennet-tlb3-rt4k-de2-nlsander-hv-sparse-LP-n1-380kv-nl220-ge1km-nodal-pst-frm10`
  (+ `-tiefixmain`: BE ×0.832, DE ×0.852; `-tiefixlower`: BE ×0.832, DE ×0.664), 2035 country `…-rt4k-de2-sparse-LP-n1-380kv-nl220-ge1km-pst-frm10`,
  today nodal/country `diag_fixedpos_v29-vvltr2-de2-*`. Full-grid check (`runs/fullgridcheck_2035rt4k-de2-{base-b,tiefixmain,tiefixlower}`): base
  over-allows NL->DE ×1.17 (Meeden–DE0N 3,489 MW vs 1,794 before), NL->BE+DE ×1.39; main: BE/DE alone ×1.00, combined ×1.18, DEN->DES ×0.85;
  lower: combined ×1.00, DE ×0.78, DEN->DES ×0.66. 2025 test (today, SR2025 units + DE2 injections, `runs/nlinj_de2-sander-units2025-…`):
  mean r 0.902, MAE 19 0.435 GW (one node: 0.909 / 0.392); BE–NL bias 0.68 -> 0.54 GW, MAE 0.73 -> 0.62; eastern borders worse
  (AT–CZ 0.36 -> 0.79, AT–DE 0.50 -> 0.93, CZ–DE 0.40 -> 0.57, CZ–PL 0.37 -> 0.55); hours with a non-Dutch branch over its limit 8.4 -> 30.5 %
  (SK–CZ 19 %, CZ–DE0N 14 %, DE0S–DE0N 10 %). HVDC research (agent, sources in docs/26) awaiting user approval. Not adopted.
- **2026-10-25 — HVDC list approved** (user: "approve the HVDC list and run option 1"). Table `inputs/derived/de2_hvdc_2035/hvdc_de2_2035.csv`
  (9 north->south systems in the 2035 model, 18,000 MW; DC2, DC31/32 inside one zone, DC42 2037 listed but excluded). docs/26 §5.
- **2026-10-25 — DE2 placement check** (user: "run option 1"). New `scripts/32_de2_placement_check_2025.py` → `runs/placecheck_de2-today`
  (full grid of today's DE2 run, 2025 split-test injections, placement varied). MAE 19 / BE–NL bias: one bus per zone 0.460 / +0.97;
  halves spread 0.333 / +0.23; + others spread 0.275 / +0.16; wind-north proxy + others spread 0.266 / +0.04 (one-node equivalents
  0.386 / 0.377 / 0.310 / 0.283). Reading: the split helps only with spread injections; the reduced networks route every zone at one bus
  while the N-1 limits assume an even spread. Proposal (not built): fit the reduced reactances to spread-injection zonal PTDFs. docs/26 §6.
- **2026-10-25 — representative-bus screening** (user: "did you try changing the node in the north and south germany?", then "do the same
  rep screening for Czechia and Poland"). `scripts/33_de2_rep_bus_screening.py` → `runs/repscreen_de2-today`; `scripts/35_rep_bus_screening_zones.py`
  (33 generalised) → `runs/repscreen_de2-today-cz-pl`, `runs/repscreen_de2-today-allzones`. Rule (measurement-free): the 380 kV bus whose
  border PTDFs are closest to an even spread over the zone. Current reps rank: DE_N Wolmirstedt 14, DE_S Rommerskirchen 91, CZ Nosovice 26,
  PL Rogowiec 14, AT Dürnrohr 13. Best: DE_N Wessin, DE_S Schwanheim, CZ Neznasov, PL Olsztyn, AT Kronstorf, … 2025 full-grid MAE 19:
  current 0.460; German pair only 0.328; + CZ/PL 0.316; all zones 0.276 (= all zones spread 0.275); AT–CZ 0.63 -> 0.48. Caveat: the BE pick
  "Y - ST-AMAND_380" is a tee bus the "Y-" filter missed. `scripts/34_set_representatives.py` + `run_chain_today_de2r.sh` rebuild today's DE2
  network with the German pair (running). Open idea (user): tune on 2025, test on 2024 (not now).
- **2026-10-25 — today's DE2 network rebuilt with the German pair Wessin / Schwanheim** (`34_set_representatives.py` → `jao_core_v29-vvltr2-de2r[-nlsander31]`,
  `run_chain_today_de2r.sh`; 2025 test with the same injections, 10n3). Reduced network: MAE 19 0.438 GW (Wolmirstedt/Rommerskirchen 0.435,
  one node 0.392); BE–NL bias +0.22 / MAE 0.40 (0.54 / 0.62; one node 0.68 / 0.73) — the best Dutch-border fit so far; but CZ–PL 0.88,
  DE–PL 0.87, AT–CZ 0.83, AT–DE 0.99 GW (full-grid estimate with this pair: 0.42 / 0.51 / 0.63 / 0.78); non-Dutch branch over its limit
  50 % of hours. Sparse-fit PTDF error (02n3 report) on zone–zone branches: median rms 0.054 vs rms of the dense PTDF 0.074 (de2r), 0.053 vs
  0.088 (de2), 0.054 vs 0.084 (one node): the 64-branch network cannot carry the full-grid improvement in the east. Not adopted.
- **2026-10-25 — today's DE2 network with five new representatives** (user: "yes run option 1"): `34` → `jao_core_v29-vvltr2-de2r2[-nlsander31]`
  (DE_N Wessin, DE_S Schwanheim, CZ Neznasov, PL Olsztyn, AT Kronstorf), `run_chain_today_de2r2.sh`, 2025 test (10n3, same injections).
  MAE 19 0.395 GW (one node 0.392; DE2 old stations 0.435; German pair only 0.438); BE–NL bias +0.17 / MAE 0.38; AT–CZ 0.27, AT–DE 0.42,
  BE–FR = DE–FR 0.54 (all better than one node); CZ–DE 0.83, DE–PL 0.69, CZ–PL 0.58, CZ–SK 0.36 (worse); a non-Dutch branch over its limit
  in 49 % of hours. Non-Core trade (user question): measured 2025 non-Core net exchange |mean| FR 7.2, DE 3.0, NL 0.9, BE 0.6, SI 0.6,
  AT 0.6, PL 0.5 GW; the eastern non-Core borders (PL–LT/UA, SK–UA, HU–UA/RS, RO–BG/RS/UA/MD, HR–BA/RS) are not in the measured-flow file.
  Not adopted.
- **2026-10-25 — non-Core placement check** (user: "yes run the non-Core placement test, no download yet"). New `scripts/36_noncore_placement_check_2025.py`
  → `runs/noncore_de2-today` (full grid of today's DE2 run; landings from the raw SGM tie list (JAO) or ASSUMED from public project info:
  FR–CH five French 400 kV stations, FR–GB Mandarins/Tourbe 3:1, BE–GB Gezelle, DE–DK2 Bentwisch; table landings_used.csv). MAE 19
  without / with placement: current reps 0.460 / 0.469; A reps 0.276 / 0.275; all spread 0.275 / 0.276. Per border: AT–CZ 0.48 -> 0.42,
  CZ–DE 0.43 -> 0.36, AT–DE 0.60 -> 0.56 better; BE–NL 0.34 -> 0.38, BE–FR = DE–FR 0.33 -> 0.38 worse (A reps). Known gaps: the FR–ES tie
  at Argia and FR–IT at Menton not matched (name) — their flow goes to the other landings; the DE–CH ties include the Swiss-side
  buses Beznau, which the JAO grid carries in the German zone. Reading: placing the available non-Core flows does not change the overall
  fit; it moves error between borders.
- **2026-10-25 — story report** (user: "a more extensive summary of what we have been doing and why ... a pdf with the full story ... also the
  relation with renewaflex session"). `scripts/report_story.py` → `docs/story_report_2026-10-25.pdf` (7 pages; numbers from the runs and notes
  logged above, docs/23–26, and nl_merge G2/G5/G10).
- **2026-10-26 — grid map with sources** (user: "a PDF with the grid that we have right now, sort of a map. How does it compare against
  the TenneT one? ... sources ... assumptions in terms of rating ... what came from GridAware? What came from the IP26 project matching?"; choices: today + 2035,
  TenneT comparison reused from nl_merge G6/G8/G9 and redrawn). `scripts/map_grid_sources.py` (draft, labels overlapped →
  `docs/grid_map_sources_2026-10-26_SUPERSEDED-labels*`), `_v2` (label offsets; one sentence overstated our rule →
  `…_v2_SUPERSEDED-amir-stations*`), `_v3` → **`docs/grid_map_sources_2026-10-26_v3.pdf`** (+ 3 PNG maps). Element sources derived from the
  workbooks and patch files: today 103 Dutch rows JAO, 8 GridAware (GridAware), 2 GridAware + JAO 2026 flow-based current, 1 JAO row restored by
  patch 2, 2 assumed transformers; 2035: 9 IP2026 upgrades to 4 kA, 2 new (Rilland–Tilburg), 2 cable-section X, 6 Tilburg loop-in,
  4 rating fix, 3 removed; every difference explained by a patch (script aborts otherwise). 16 of 36 Dutch 380 kV corridors below 4 kA in 2035.
- **2026-10-26 — limits story and 2025 maxima** (user: "another file expanding on this topic ... how did we manage to improve so much?"
  and "what was the maximum in 2025?"). `scripts/report_limits_story.py` (v1 wrote "60-80 %" by hand for the share of the safe exchange
  used in 2025: wrong → `docs/limits_story_2026-10-26_SUPERSEDED-share.*`), `report_limits_story_v2.py` → **`docs/limits_story_2026-10-26_v2.pdf`**.
  Steps and numbers from the colleague document (sections 4-6) and build_report.md (F1-F4). 2025 measured hourly maxima (ENTSO-E physical
  flows): NL–DE export 6,231 / import 5,420 MW; NL–BE 4,126 / 2,813; Core net position 7,667 / 4,995. Safe exchange on today's grid (full
  grid, option 3), NL as one zone / best placement: DE 8,561 / 10,320; BE 5,017 / 5,265; both 8,886 / 12,082 MW; 2025 peaks used 73-86 %.
- **2026-10-26 — note to the author of the TNO N-1 method** (user: "explain exactly what we did and why ... compared to what you did ...
  simple"). New driver `scripts/run_n1_decomposition.sh`: 04_limits_n1.py with one change at a time on today's country network (v29-vvltr2,
  ENR run 2026-10-19), each + 10_test_2025. Hours inside (2025): N-0 one bus every element 83.5 %; TNO N-1 as written (border outages,
  ratings unchanged, every element limits, one bus) 36.1 %; + every element fails, failed rating removed 14.4 %; + only 380 kV >= 1 km limits
  52.6 %; + exchange spread over 380 kV buses 95.3 %; TNO outage rule with the other changes 97.9 %; option 3 (existing) 91.7 %. NL–DE / BE–NL
  pair limits 7,323/5,799 → 4,968/5,517 → 4,544/3,599 → 4,544/3,599 → 6,629/3,724 → option 3 8,561/5,017 MW. 220 kV elements set 36 (TNO) / 44 of
  66 pair limits when every element may limit. Runs `runs/2026-10-26-limits-v29-vvltr2-decomp*`, networks `inputs/derived/diag_fixedpos_v29-vvltr2-sparse-LP-decomp*`.
  Claude Doc "How we implemented your N-1 method — and what we changed": https://claude.ai/artifact/XT93KvuPpufSt1SEJpgxmr.
- **2026-10-26 — N-1 note, steps 1 and 2: which generation shift key** (user: "start with one and two ... and the JAO comparison").
  `scripts/37b_rep_bus_rank_country.py` (37 superseded: tee filter missed "Y - ST-AMAND"; `runs/_SUPERSEDED-tee-filter_repscreen_country-v29-vvltr2`)
  → `runs/repscreen_country-v29-vvltr2`: best single-bus stand-in for the even 380 kV spread per zone, grid only; NL Rilland ranks 32/33 (best
  Diemen), DE Rommerskirchen 131/286 (best Dipperz). `scripts/38_nl_country_gsk_key.py` → `inputs/derived/gsk_nl_country2025-sander31`
  (first attempt `_ABORTED-tabulate-missing_…`): Dutch key weight = 2025 generation + |load| per node from nlinj_sander-units2025 (Country GSK of
  Core DA CCM Art. 9(4a), ACER Decision 10/2026; ASSUMED static, SR2025 2035 keys, residual and non-Core links left out).
  `scripts/04k_limits_n1_key.py` (04 + key options rep:/file:) via `scripts/run_n1_keys.sh` (setting of D/E). Hours inside 2025 (10_test_2025):
  D one bus (Rilland …) 52.6 %; G NL at Diemen 52.9 %; H + DE at Dipperz 51.6 %; I every zone at its best bus 0.4 %; E 380 kV even 95.3 %;
  J NL Country-GSK-style key + others even 96.0 %. NL–DE / BE–NL pair limits: D 4,544/3,599; G 4,686/3,253; H 1,803/3,253 (Dipperz–Mecklar);
  E 6,629/3,724; J 7,317/3,797 MW. Reading: a single injection bus overloads the lines at that bus whichever bus is chosen; the gain is the
  spread, not Rilland (the earlier remark that part of the gain was Rilland's poor placement is withdrawn).
  JAO line-share comparison with the keys: `scripts/39_share_check_keys.py` (copy of the 2026-10-19 experiment's share_check.py; JAO folder
  argument) → `runs/2026-10-26-share-check-keys-v29-vvltr2-0910`, only the 4 hours of 2026-09-10 still on disk (the 2026-01-14 and 2026-07-15
  files of the 19 Oct check are gone with the old workspace copy). Within ±25 % of JAO, all Core / TenneT NL lines: one bus 31/33 %; NL Diemen
  36/32 %; best each 33/33 %; 380 kV even 42/55 %; NL Country-GSK-style + even 38/37 %; all even 38/51 %.
- **2026-10-26 — which voltage levels bind in Core 2025** (user: "we only monitor 380 kV lines of at least 1 km ... Is this something that TSOs
  would do?"). `scripts/40_jao_binding_by_voltage_2025.py` → `runs/jaosp_2025-by-voltage` (2025 JAO active constraints on disk; voltage =
  Fmax/(sqrt3 Imax), snapped). Shadow-price CNEC rows: 380 kV 65 % of rows / 67 % of the shadow-price sum; 220 kV 15 % / 30 %; no Imax
  (external constraints) 20 % / 3 %. 220 kV binding is almost all APG (58 elements, 10 % of the sum) and TenneT DE (8 elements, 17 %:
  Altheim–Sittling, Simbach/St. Peter, Pleinting–St. Peter, i.e. the Bavaria–Austria 220 kV), plus Transelectrica; TenneT NL, Amprion,
  50Hertz, Elia (with a CNEC Imax), RTE, PSE: 380 kV only. NOTE: the summary's "hours" column counts market time units (15-minute MTUs
  from 1 Oct 2025), hence 14,254 > 8,760. JAO final computation 2026-09-10 (4 hours, on disk): 863 distinct monitored elements, 207 of
  them 220 kV (APG 83, Transelectrica 32, TenneT DE 23, PSE 23, Amprion 12, …), TenneT NL 40 elements, all 380 kV.
- **2026-10-26 — JAO final computation, 80 hours of 2026: download started** (user: "yes download the 80 hours of JAO files").
  `scripts/41_download_jao_final_computation.py` → `inputs/external/jao_fb_2026_80h` (first Tuesday and third Thursday of each month Jan–Oct
  2026, 02/08/12/18 UTC; gzip as received; log `runs/41_jao_fb_2026_80h.log`). JAO answers in ~3 min per hour of data. Comparison script
  ready: `scripts/39b_share_check_keys.py` (39 + gzip input + each key by operator).
- **2026-10-26 — round 3, step (i): spread-injection PTDF fit** (user: "yes approve the round-3 plan after the JAO comparison"; started
  while the download runs). `scripts/42_spread_ptdf_fit_nodal.py`: reactances of the reduced nodal network fitted to full-grid corridor
  PTDFs with Dutch nodes at their bus and every other zone spread over its 380 kV buses; option-3 envelope recomputed with the fitted
  PTDFs (the run's own limits reproduced first, 3e-12). On today's DE2 nodal network (`…de2-nlsander31-…-nodal-pst-frm10`):
  corridor PTDF RMS 0.053 → 0.014; 2025 test (10n3, same injections) MAE 19 0.435 → 0.318 GW, AT–CZ 0.79 → 0.35, AT–DE 0.93 → 0.50,
  CZ–PL 0.55 → 0.31, but BE–NL bias +0.54 → +0.52 (full grid all spread: +0.16). Cause: the German north–south transfer (DE0N mean
  +10.8 GW) loops 3.7 % through NL→BE on the full grid, 0.8 % in the fit. `scripts/42b_spread_ptdf_fit_nodal_weighted.py` (residuals
  weighted by RMS 2025 injection, other zones 1 GW ASSUMED; tuned on 2025 magnitudes): MAE 0.304, BE–NL bias +0.41 / MAE 0.52, AT–CZ 0.36.
  Hours with a branch over its limit unchanged (~50 %; the known non-Dutch issue of the DE2 networks). Runs `runs/2026-10-26-spreadfit[w]-de2-nlsander31`,
  networks `…-nodal-pst-frm10-spreadfit[w]`, tests `runs/fixedposnodalinj_…-spreadfit[w]_nlinj_de2-sander-units2025-…`.
- **2026-10-26 — N-1 note updated and exported to Word** (user: "Did you need to update the how we implemented the n-1 method?", then
  "give it in word format"). Claude Doc https://claude.ai/artifact/XT93KvuPpufSt1SEJpgxmr rev 12: new subsection "Where a country's exchange
  enters (change 4)" (1,000 MW example, best-single-bus test, GSK rule of ACER Decision 10/2026 Art. 9(4a), JAO comparison on the 4 hours of
  2026-09-10, to be replaced by the 80-hour sample), a paragraph on the 380 kV monitored rule (scripts/40), limitations updated (spread fit).
  Word: text saved as `docs/n1_note_2026-10-26.md`, built by `scripts/report_n1_note_docx_v2.py` → `docs/n1_note_2026-10-26.docx` (+ chart
  `docs/n1_note_hours_inside.png`); first build kept as `…_SUPERSEDED-title-overlap.*` (scripts/report_n1_note_docx.py).
- **2026-10-26 — round 3, step (ii): Belgian border node, started** (user: "yes start the Belgian node step"). `scripts/43_be2_split_workbook.py`
  → workbooks `jao_core_v29-vvltr2-de2-be2a-nlsander31` (BE_N = Zandvliet) and `…-be2b-nlsander31` (BE_N = Zandvliet + Lillo), both from
  `v29-vvltr2-de2-nlsander31`, representative Zandvliet, rest of Belgium unchanged (BE00, Gramme). New copies: `02n4_sparse_network_nodal_hv_be2.py`
  (BE_N -> BE0N), `10n4_test_2025_nodal_injections_be2.py` (BE0N pure network node, ALEGrO from BE00). Driver `scripts/run_chain_today_be2.sh`
  (01, 02n4, 03n2, 04n, 05n, 42, 42b, 10n4, 23d; log `runs/chain_today_be2_2026-10-26.log`).
- **2026-10-26 — freeze and limitations** (user: "we need to, at a certain point, say, okay, this is fine, this is the limitations, and move
  forward" / "yes agree, tell renewaflex and write the limitations list"). `docs/27_limitations_and_freeze.md`: frozen networks (round 2 main/lower
  for 2035, country and nodal 2025), the decision rule for the Belgian node (clearly lower BE–NL error and bias AND no tie cut needed, NL→BE
  over-allowance <= 5 %), nine limitations with their size, parked list. RenewaFLEX told (scope cut, round 2 stands unless the Belgian node earns
  its place; BE–DE_S branch question still owed).
- **2026-10-26 — Belgian border node: NOT adopted, round 3 dropped** (decision rule of docs/27). `run_chain_today_be2.sh` finished (reductions
  ~1 min each). 2025 test (10n4, same injections): BE–NL bias / MAE de2 +0.543 / 0.615; be2a and be2b +0.518 / 0.596 (Kron); with the weighted
  spread fit de2 +0.413 / 0.524, be2a +0.419 / 0.528, be2b +0.421 / 0.529; MAE 19 0.430 (Kron), 0.305 (fit), same for a and b. BE0N–BE00
  branch limit 2,220 (a) / 2,297 (b) MW. Full-grid check 23d (today, NL→BE, Dutch side free): reduced / full grid de2 6,301 / 5,265 (x1.20),
  be2a 6,272 / 5,149 (x1.22), be2b 6,319 / 5,123 (x1.23), binding Doel–Zandvliet in all; with the fit the over-allowance grows (x1.44–1.47).
  Neither criterion met (BE–NL not clearly better; tie cut still needed). Round 2 stays the frozen 2035 network. `runs/fullgridcheck_today-{de2,be2a,be2b}[-spreadfitw]`.
- **2026-10-26 — BE–DE branch = the Belgium–Luxembourg 220 kV tie, not ALEGrO** (RenewaFLEX question). In `jao_core_v29-vvltr2-de2` the only AC
  element between BE and DE_S is the tie-line BELVAL_220 – OXYLUX_220 (EIC 22T20211201R---K, 1 km, 503 MW; Oxylux is in Luxembourg, zone DE_LU);
  ALEGrO is in the DCLines sheet (OBERZIER_380 – LIXHE_380, 1,132.8 MW) and is not part of any AC branch (02 counts AC rows only). Keep ALEGrO as a
  separate link; no double counting.
- **2026-10-26 — German-split sensitivity for RenewaFLEX (outside the freeze, their user's request)**. No new network: recommended the existing
  2035 `…-rt4k-de2-nlsander-hv-…-nodal-pst-frm10-tiefixmain` (BE ties ×0.832, DE ×0.852) and country `…-rt4k-de2-sparse-LP-n1-380kv-nl220-ge1km-pst-frm10`.
  Full-grid facts sent (`runs/fullgridcheck_2035rt4k-de2-*`): direct DE0S–DE0N limit 9,672 MW; secure north→south AC transit 15,119 MW (base
  reproduces it; main ×0.85, lower ×0.66). Caveat sent: German AC grid = JAO 2026 + the 9 HVDC systems only (no NEP 2035 AC reinforcements), so
  the split end of the range likely overstates German north–south congestion; one-node Germany is closer to the zonal market outcome.
- **2026-10-26 — parked: 15.1 GW north–south variant of the DE2 2035 network** (user: "park it for now, but do say to the other session ... this
  could be something that can be improved"). Idea: raise the DE0S–DE0N limit (9,672 MW) of `…-rt4k-de2-…-tiefixmain` until the reduced network's
  north→south AC transit equals the full grid's 15,119 MW (now 12,877, ×0.85). RenewaFLEX told to flag after their split runs how often DE0S–DE0N
  binds; decide then.
- **2026-10-26 — JAO 80-hour download finished; line-share comparison redone** (`inputs/external/jao_fb_2026_80h`, 80/80 hours, 159 MB gzip).
  `scripts/39b_share_check_keys.py` → `runs/2026-10-26-share-check-keys-v29-vvltr2-80h` (log `runs/39b_share_check_80h.log`): 7,004 of 10,713
  element-outage combinations compared. Within ±25 % of JAO, all Core / TenneT NL: one bus 26 / 32 %; NL Diemen 32 / 33 %; best each 36 / 35 %;
  380 kV even 45 / 69 %; NL Country-GSK-style + even 42 / 52 %; all even 37 / 58 %. Below 30 % (380 kV even) for APG, CEPS, MAVIR, HOPS, ELES,
  Transelectrica. N-1 note updated (Claude Doc rev 13; `docs/n1_note_2026-10-26.md`; Word rebuilt by report_n1_note_docx_v2.py, the 4-hour
  version kept as `…_SUPERSEDED-jao-4h.*`); docs/27 limitation 3 updated.
- **2026-10-26 — German-split 2035 test weeks (RenewaFLEX, nl_merge/G16_de2_test_weeks_vs_one_node.md)**, on the option-a networks: Dutch
  congestion cost three weeks NT 2.03 → 5.38, SR2 2.75 → 6.93 M EUR; K–G hours at limit winter 87 → 2; congestion moves to a north-east transit
  corridor (Meeden import winter 19 → 469 GWh); DE0N/DE0S winter price 28 / 123 EUR/MWh; AC DE0S–DE0N at its 9,672 MW limit 141 of 168 winter hours.
  15.1 GW variant meets the agreed criterion but stays parked (user, via RenewaFLEX: "No variant for now"); full-year one-node vs split range to
  follow from the CPLEX runs.
- **2026-10-26 — 15.1 GW north–south variant: not built, premise wrong** (user approved the build; checked first). Pure DE0N→DE0S transit in the
  reduced 2035 networks = min over branches of limit / |PTDF share| (no other injection, as 23d's transit case). Nodal `…-rt4k-de2-…-tiefixmain`:
  DE0S–DE0N 9,672 MW at share 0.640 → 15,119 MW (already the full-grid value); the binding element is NL-MEEDEN–DE0N (2,972 MW after the main cut
  ×0.852, share 0.231) → 12,877 MW. Country `…-rt4k-de2-sparse-LP-…-pst-frm10`: 15,119 MW (DE0S–DE0N 11,618 MW, share 0.768; NL00–DE0N binds equally)
  = full grid, no shortfall. Raising DE0S–DE0N changes nothing; reaching 15.1 GW needs the Meeden tie uncut (3,489 MW), which brings back the
  NL→DE over-allowance (×1.17). The earlier explanation ("the direct link is too tight") is withdrawn. Recommendation: build nothing.
- **2026-10-26 — background file for rewriting the N-1 note elsewhere** (user: "give me the MD with the calculations and everything ... I'm going
  to run all of this in a different session"). `docs/n1_background_for_rewrite.md` (all facts, numbers, sources, scripts). New
  `scripts/45_example_1000mw_nl_de.py` → `runs/example_1000mw_nl_de` reproduces the note's 1,000 MW example (until now from a scratch script):
  border 773 / 843 MW, via Belgium 227 / 157, Doel–Zandvliet share 0.351 / 0.121, Diele–Meeden 0.084 / 0.272, N-0 limit 7,323 / 12,031 MW.
- **2026-10-26 — JAO share comparison: tolerance-free error metrics** (user: "extend the JAO share comparison with a second metric that does not
  depend on the 25 % tolerance"). `scripts/39c_share_check_keys_errors.py` (copy of 39b + per combination e = median over material pairs of
  |ours − JAO| / |JAO|, signed shares; median and P75 of e over combinations; within 10 / 25 / 50 % by the ratio rule of 39b; pooled variant in
  metrics.csv) → `runs/2026-10-26-share-check-keys-v29-vvltr2-80h-errors` (report.md = one table; 39b's report kept as report_share_details.md;
  log `runs/39c_share_check_80h_errors.log`). Same 80 hours and 4,227 combinations (TenneT NL 938); the 25 % column reproduces the 39b run.
  All Core, median / P75 error, within 10 / 25 / 50 %: one bus 71 / 138 %, 11 / 26 / 49 %; NL Diemen 62 / 145 %, 12 / 32 / 57 %; best each 57 / 156 %,
  18 / 36 / 60 %; 380 kV even 41 / 129 %, 24 / 45 / 67 %; NL gen+load + even 44 / 130 %, 20 / 42 / 66 %; all even 45 / 124 %, 20 / 37 / 64 %.
  TenneT NL: one bus 51 / 124 %, 17 / 32 / 64 %; Diemen 51 / 139 %, 12 / 33 / 64 %; best each 47 / 140 %, 17 / 35 / 68 %; 380 kV even 16 / 41 %,
  45 / 69 / 94 %; NL gen+load 30 / 48 %, 22 / 52 / 88 %; all even 22 / 42 %, 39 / 58 / 92 %. Ranking: 380 kV even first and every spread ahead of
  every single bus on all metrics except the all-Core P75 (all even 124 % < 380 kV even 129 %; single buses 138–156 %); the order among the three
  single-bus keys is not stable across metrics. All-Core P75 above 100 % for every key: a quarter of combinations are off by more than their own
  size (often a share in the wrong direction).
- **2026-10-27 — plain-language PDF of the whole process, for the call with GridAware** (user: "give me a PDF explaining all of this process again ...",
  then "how the PTDFs are done, this tested fix ... explain it like I'm 5"). `scripts/report_process_explainer_v3.py` → `docs/process_explainer_2026-10-27_v3.pdf`
  (+ `process_explainer_flow.png`, `process_explainer_triangle.png`): where the spread is used (only the transfer-limit step, N-0 and N-1) vs one bus
  (reduced network, envelope, Tulipa, 2025 test); how a PTDF is computed (three-bus example: shares 0.67 / 0.33); steps 1–5; decomposition; tested
  spread fit and why not adopted; limitations; cheat sheet for GridAware's email. Numbers quoted from earlier runs only. v1 (`…_SUPERSEDED-no-ptdf-section`)
  and v2 (`…_SUPERSEDED-label-overlap`) kept.
- **2026-10-27 — process explainer v4** (user: "what the original approach was ... how does that n-0 and n-1 calculation work together? ... the n-0 first
  approach ... it became 0?"). `scripts/report_process_explainer_v4.py` → `docs/process_explainer_2026-10-27_v4.pdf` (9 pages): adds the method's history
  (Sept one-bus N-0 → GridAware's N-1 → 13 Oct spread + monitored rule → 14 Oct option 3 → 16 Oct 1 km rule), the "one list, keep the smallest" explanation with
  the NL→DE entries (intact 12,031; Meeden–Diele circuit out 6,629; Doel–Zandvliet out 12,022; Maasbracht–Oberzier out 8,974; Geertruidenberg–Krimpen
  out 10,070 MW; scratch recomputation with the engine of 04, min over all outages reproduces the logged 6,629), and how the spread relates to PTDFs.
  v3 kept as `…_SUPERSEDED-no-history.*`.
- **2026-10-27 — flow figures of the 1,000 MW example** (user: "a couple of graphs ... without the spread and with the spread ... powers flowing").
  `scripts/report_flow_maps_v3.py` (v1/v2 kept as `_SUPERSEDED-*`) → `docs/flow_map_one_bus_vs_spread.png` (schematic map, MW per line, one bus vs spread;
  flows from a scratch recomputation with the engine of 04, consistent with runs/example_1000mw_nl_de: NL–DE ties 84/57/171/244/216 vs 272/123/179/142/127 MW,
  Rilland–Zandvliet 556 vs 192, Doel–Zandvliet 351 vs 121, Krimpen–Geertruidenberg −192 vs +250) and `docs/flow_full_at.png` (exchange at which each line
  is full; limits 7,323 / 12,031 MW). Added to the explainer: `scripts/report_process_explainer_v5.py` → `docs/process_explainer_2026-10-27_v5.pdf`.
- **2026-10-27 — "envelope" renamed "largest need" in everything user-facing** (user: "when you use the word envelope, that really makes me very confused
  ... please do that. Change it"). Same step (C_l = max over pairs of TTC × |PTDF|); worked example for the NL–DE branch on today's grid with our N-1
  (run decompE): AT→NL 6,825 × 0.632 = 4,316 MW largest (= the run's branch limit, "set by AT->NL"); DE→NL 4,193, CZ→NL 3,285, FR→NL 3,162 MW.
  Changed: Claude Doc (rev 15), `docs/n1_note_2026-10-26.md` + Word rebuilt (old `…_SUPERSEDED-envelope-wording.*`), `docs/27_limitations_and_freeze.md`,
  `docs/n1_background_for_rewrite.md` (keeps "envelope" as the code name). Explainer `scripts/report_process_explainer_v6.py` →
  `docs/process_explainer_2026-10-27_v6.pdf`: the rename, the NL–DE table, and a table of which grid and which start/end buses the package, the MATLAB
  file and our method use for the transfer limit (all on the full grid; package and MATLAB inject at 12 representative buses only). Code and run
  names are unchanged (they still say envelope).
- **2026-10-27 — chain diagram for 150/110 kV congestion, for the reply to GridAware** (user: "there's also a diagram of how I would see this whole chain
  working"). `scripts/report_chain_150_110kv.py` → `docs/chain_150_110kv.png` (drawing only). Context found in nl_merge: G18 (TenneT regional
  congestion studies: limiting elements are 380/150 and 220/110 kV transformers and 150/110 kV lines, none at 380 kV; TenneT's fix splits 150 kV into
  islands) and the visualisation session's finding that our 380/220 kV model causes little curtailment. Asked the "Grid congestion visualisations"
  session whether it already defined the 150/110 kV approach or has its own chain diagram.
- **2026-10-27 — visualisation session's review of the 150/110 kV chain** (no method or diagram existed there). Taken on: check against TenneT's
  limiting elements per area (nl_merge G18) instead of the capacity map (free connection room, not hourly loading); run the load flow islanded
  (deelnetten) as well as meshed; a cheaper first step (G17 §6: bus net exchange vs 380/150 kV transformer capacity). Their caveats: no congestion
  management in the dispatch (overloads before action, = TenneT's "flexibility need" view); one national wind/solar profile per bus; 380 kV flows of
  the full load flow should match Tulipa's on the reduced grid (consistency check). `scripts/report_chain_150_110kv_v2.py` → `docs/chain_150_110kv.png`.
- **2026-10-30 — standalone TTC tool for colleagues, Python and Julia** (user: "share with some colleagues the code with the n-1 and N-0 approach with
  the GSK for TTC calculation ... standalone ... also in Julia"; "the selection of lines of >1 km and only 380 kV needs to be explained ... or that
  you can change what you select"). `standalone/ttc_gsk/` (+ `standalone/ttc_gsk.zip`): `python/ttc_gsk.py` (numpy only), `julia/ttc_gsk.jl`
  (standard library only), `tools/convert_from_reduction_outputs.py` (ENR outputs + workbook → buses.csv / branches.csv), `example/` (4-bus toy:
  one bus 133.3 / spread 200 / N-1 100 MW), README (method, options incl. the monitored-line choice all / rule with --min-kv --min-km / flag,
  validation, data terms). Same algorithm as scripts/04_limits_n1.py + lib_n1_engine.py, without the project plumbing; no phase shifters, no
  reduction or largest-need step. Validation on today's grid (converted from runs/2026-10-19-stage2-v29-vvltr2-LP-virtual, scratch only, not in
  the package): decomposition runs A–F reproduced for all 66 pairs to ≤ 5.6e-7 relative (output rounding), Python = Julia exactly; `--monitored
  rule --min-kv 380 --min-km 1` selects the same 1,370 records as runs/2026-10-19-monitored-380kv-ge1km-v29-vvltr2. The package contains no
  JAO-derived data.
