# 2026-10-16 — Step 3: the Netherlands at 380 kV nodal resolution — scoping and first build

User (2026-10-16): "Step three actually is and will be to test the Netherlands, but at the high voltage network … reduce the
networks all across Europe … not reduce the network in the Netherlands, but just keep the high voltage representation";
"For the nodes, let's keep only the 380 kV ones … we will also get a key of the data of the distribution keys of demand and
supply"; "check the niederlangen stub first, then start step 3" (stub: notes/20).

## 1. Design

- **Nodes.** The 33 Dutch 380 kV buses of v29 are nodes of their own (34 with Tilburg in the 2035 grids); every other Core
  zone keeps its one representative bus (unchanged from the 12-node network): 44 nodes. The 12 Dutch 220 kV buses are
  eliminated by the Kron reduction (user: 380 kV only). The five Dutch spur buses (Hollandse Kust Zuid and Zeeuwse Kust
  landing stations, Eemshaven converter station / Synergieweg / compensation station) are kept as nodes as instructed; they
  matter only if the keys put injection there (offshore wind landing points).
- **Mechanism.** ENR in `manual_excel` mode with IsRepresentative = 1 for every Dutch 380 kV bus: scripts/117 writes
  `inputs/derived/jao_core_v29-nl380` (byte copy of v29, 32 cells changed, read back and checked); scripts/116 is a copy of 11
  that can read `HIGH_RES_ZONES` from the environment (not used in this build). Package facts (source read): manual mode
  accepts any number of representatives per zone; the full-grid TTC is computed for all 1.54 M bus pairs anyway (5 s);
  `high_res_zones` keeps ALL buses of a zone (220 kV included) and only changes the package's own capacity fit (intra-zone
  lines fixed to physical capacity), which our chain does not use (58 / 83 recompute the limits) — so it is not used.
- **Sparse network** (scripts/118, the 58 method at node level): a branch for every node pair joined by at least one AC row
  of the workbook: 37 Dutch 380 kV line pairs, 6 tie pairs (Maasbracht / Doetinchem / Hengelo / Meeden – DE, Maasbracht /
  Rilland – BE), 17 zone pairs (BE–NL and DE–NL of the 12-node network are now node–zone pairs): 60 branches. Kron
  fill-ins are dropped as before (9 Dutch pairs joined only through foreign grids, e.g. Maasbracht–Rilland via Belgium; 49
  non-adjacent bus–zone pairs; 38 zone pairs). Reactance = the Kron value (default) or, as a variant, the physical parallel
  reactance for the Dutch pairs (`--nl-x=physical`).
- **Limits in this first build**: the LP envelope of the full-grid N-0 transfer limits over all 946 node-pair transactions
  (58 method) — a baseline only. The option-3 limits (N-1, phase shifters, 10 % margin) need the 83 / 93 procedure at node
  level: next step.
- **Keys.** replay2025/scripts/61 (copy of 53) splits the Dutch net position over the Dutch nodes by a key file (node,
  share); scripts/62 writes a PLACEHOLDER even key (1/33 each) so that the chain can be exercised. The user's demand and
  supply keys replace it; nothing about Dutch internal flows may be read from the placeholder.
- **Node codes**: `NL-<bus name without _380, spaces as hyphens>` (e.g. NL-KRIMPEN-AAN-DEN-IJSSEL); zones AT00 … SK00 as
  before; asset names `<code>_E_Demand_2035` (the Tulipa naming is designed with the keys).

## 2. What the reduction shows

Run `runs/2026-10-16-stage2-v29-nl380-LP-virtual` (COMPLETED, 33 s, 0 flagged console lines): one AC island of 1,756
buses, 44 representatives kept, 946 transactions. The package lists 156 equivalent branches (it prunes Kron admittances
below 1e-10): fill-in appears only among the five Dutch border buses, the Ens / Meeden / Eemshaven 220 kV couplings and
the foreign representatives. Dense PTDF check against the package: max difference 1e-12 (opposite global sign convention,
as 58 found).

- **Kron reactance = physical reactance (ratio 1.0000) for 35 of the 37 Dutch pairs**: a Dutch 380 kV bus connected only to
  other retained buses gets no fill-in. The two exceptions are real parallel paths through eliminated buses:
  Eemshaven–Meeden 0.929 (the Groningen 220 kV path Meeden 220 – Weiwerd – Eemshaven 220 in parallel) and
  Doetinchem–Hengelo 0.954 (the German loop Niederrhein … Gronau). The Friesland 220 kV loop hangs on Ens alone and is
  eliminated without trace. Per-unit base confirmed from the data: Z_base = 380² / 100 Ω.
- **Ties** (Kron, p.u.): Maasbracht–DE 0.0084, Doetinchem–DE 0.0121, Meeden–DE 0.0340, Hengelo–DE 0.0438, Maasbracht–BE 0.0106,
  Rilland–BE 0.0190 — the tie-line plus the foreign path to the zone's representative bus.
- **Physical-X variant**: 2025 routing identical to three decimals (r 0.909, MAE 0.401 GW, 86.3 % inside). The choice does
  not matter; Kron is kept (method consistency). Folders `…-sparse-LP-physx` kept for the record.

## 3. Envelope limits of this build (N-0, every full-grid line monitored — baseline only)

| branch group | result |
|---|---|
| Dutch lines (37) | envelope ≈ rating: cap / rating 1.00–1.08 for 30 pairs; Eindhoven–Maasbracht 1.19, Hengelo–Zwolle 1.17, Doetinchem–Hengelo 1.14, Geertruidenberg–Rilland 1.37 (sparse PTDF below the full-grid one); Meeden–Zwolle 0.63 |
| ties | Maasbracht–BE 2,952 MW (1.00 of rating), Rilland–BE 3,060 (0.58), Doetinchem–DE 4,438 (0.89), Maasbracht–DE 4,198 (1.16), Hengelo–DE 1,448 (0.40), Meeden–DE 1,384 (0.42) |
| zone pairs (17) | as the 12-node fit, within the sparsification error |
| TTC fit error, 946 transactions | dense: median 0.0 %, 618 exact; sparse: median +1.6 %, 816 within ±20 % (12-node network: 61 of 66); Dutch pairs +0.6 %, bus–zone +3.3 %, zone–zone +2.2 % |

Hengelo–DE and Meeden–DE at 40 % of their ratings are the package's N-0 transfer limits through Gronau–Hengelo and
Meeden–Diele, capped by other elements of the full grid (every line monitored, the Niederlangen stub among them, note 20).
They will change with the node-level N-1 limits and the ">= 1 km" monitored rule.

## 4. The 2025 fixed-position test with the even placeholder key

`replay2025/runs/fixedposnodal_diag_fixedpos_v29-nl380-sparse-LP_key_nl-even-v29-nl380` against the 12-node baseline
`fixedposdc_diag_fixedpos_v29-sparse-LP_single` (same measured positions, same limits method).

| | 12-node (all of NL at Rilland) | nodal NL, even key |
|---|---|---|
| mean hourly r, 18 borders | 0.895 | 0.909 |
| mean MAE, 19 borders (GW) | 0.387 | 0.401 |
| hours with every branch inside its N-0 limit | 83.5 % | 86.3 % |
| BE–NL: mean error GW / r | +0.32 / 0.72 | +0.75 / 0.86 |
| DE–NL: mean error GW / r | −0.32 / 0.96 | −0.75 / 0.97 |
| BE–DE: mean error GW / r / MAE | +0.16 / 0.78 / 0.65 | −0.11 / 0.94 / 0.22 |
| BE–FR and DE–FR: MAE GW | 0.57 | 0.70 |

Reading: where the Dutch position enters the grid decides the BE–NL / DE–NL split and, through the loop, BE–DE and the
French borders. With the even key too much of the Dutch import comes from Belgium (+0.75 GW on average) and too little from
Germany; the hourly shapes are better (r up on both borders) and BE–DE improves a lot (MAE 0.65 → 0.22 GW). Inside the
Netherlands an even spread of about 1.8 GW of average import over 33 buses produces almost no flow (95th-percentile
utilisation below 0.12 on every Dutch line): the real pattern — generation at Eemshaven, Maasvlakte, Borssele, load in the
Randstad — is what the user's keys must bring. **No conclusion about the Dutch grid can be drawn from this run**; it shows
that the chain works and that the keys are decisive.

## 5. Node-level limits (scripts 119, 120, 121) — same day

- **Monitored set.** The ">= 1 km" list of note 20 drops the Dutch landing circuits under 1 km (Borssele – Zeeuwse Kust, four
  circuits of 0.11–0.35 km; Eemshaven Oudeschip – Synergieweg / – Compensatie filterstation). In the nodal network these rows ARE
  branches between nodes and their rating is the only limit of a transfer to the spur bus; without them that limit is infinite
  (120 aborted; folder kept `…_ABORTED-spur-pairs-unmonitored`). scripts/119 → `runs/2026-10-16-monitored-nodal-v29-nl380`:
  the >= 1 km list plus every excluded row whose two ends are representative buses (8 rows; 1,376 EICs). The stubs inside the
  other grids stay excluded.
- **120** (83 at node level: 946 transactions, a Dutch node's exchange at its bus, a zone's spread over its 380 kV buses, every
  record out in turn, 14 s): `runs/2026-10-16-limits-nodal-v29-nl380-n1-380kv` (all 380 kV lines) and `…-n1-380kv-ge1km-nodal`.
  Check: 118's N-0 limits and reactances reproduced first (2e-10, 4e-12).
- **121** (115 at node level: phase shifters set per exchange within the RAO range, 10 % margin, 59 s):
  `runs/2026-10-16-limits-nodal-v29-nl380-n1-380kv-ge1km-nodal-pst-frm10` (+ the neutral `…-frm10`). Checks: with every angle
  at zero the 120 limits times 0.9 are reproduced (6e-12); MW per degree per corridor against scripts/74 within tolerance.

| result (>= 1 km nodal rule) | value |
|---|---|
| N-1 transfer limit against the N-0 one of 118, median | all 0.63; Dutch pairs 0.55; Dutch node–zone 0.74; zone–zone 0.91 |
| phase-shifter gain (with / without), median | all 1.01 (471 of 946 transactions gain more than 1 %); Dutch pairs 1.08, up to 1.37 (Hengelo–Zwolle 2,653 → 3,637 MW) |
| ties, transfer limit without → with phase shifters | Maasbracht–BE 2,224 → 4,020; Rilland–BE 2,980 → 4,101; Doetinchem–DE 6,058 → 6,728; Hengelo–DE 5,493 → 6,408; Maasbracht–DE 4,171 → 5,242; Meeden–DE 2,569 → 4,562 |
| Dutch line branch limits / rating | N-1: median 0.62 (0.39–1.00; four pairs exactly 0.50 = a double circuit without parallel path); option 3: median 0.61 (0.35–0.90): margin and phase-shifter gain roughly cancel |
| zone–zone transaction limits against the 12-node run, same rule | identical (ratio 1.0000 for all 55, N-1 and with phase shifters): the nodal chain reproduces the zonal computation where it must |
| zone–zone branch limits | differ where the branch's Kron reactance changed: BE–DE X 0.0191 → 0.0874 p.u. (its coupling through the Dutch grid now runs over the Dutch nodes), limit 2,949 → 651 MW; the other zone branches' reactances move by a median 0.4 % |
| Dutch node ↔ zone transfer limits, option 3 | median 3.5–3.8 GW per foreign zone (towards DE: 561 MW at the Eemshaven compensation station up to 6,743 at Geertruidenberg); the zonal DE–NL limit of 8,551 MW is a different quantity (exchange spread over 33 buses) |

2025 fixed-position test (even placeholder key; routing identical for every limit set: r 0.909, MAE 0.401 GW), hours with every
branch inside its limit:

| limit set | 12-node network | nodal network |
|---|---|---|
| N-0 envelope (58 / 118) | 83.5 % | 86.3 % |
| N-1, all 380 kV lines monitored | 88.8 % | 90.4 % |
| N-1, >= 1 km rule (nodal: + spur rows) | 95.4 % | 95.0 % |
| option 3 (N-1 + phase shifters + 10 % margin, >= 1 km rule) | 91.7 % | 91.6 % |
| N-1 + 10 % margin without phase shifters (>= 1 km) | 83.7 % | 82.4 % |

The most loaded branches of the nodal option 3 are the same foreign borders as in the 12-node test (SK–CZ p95 1.02 and 6.4 % of
hours over, then FR–BE, RO–HU, SI–AT); the Dutch branches peak at 0.48 of their limit (Geertruidenberg–Krimpen) with the even key.

**Status.** The nodal chain is complete up to the option-3 network `inputs/derived/diag_fixedpos_v29-nl380-sparse-LP-n1-380kv-ge1km-nodal-pst-frm10`
(44 nodes, 60 branches; `branches_for_73.csv` in the 121 folder for a Tulipa builder). Missing: the user's keys and the Tulipa folder.

## 6. Next

1. **Keys** — proposed format, one CSV: `node` (the 33 codes or bus names), `share_demand`, `share_generation` (optionally
   per technology: offshore wind, onshore wind, solar, gas, nuclear, other), `source`. For the 2025 test the hourly node
   injection is share_generation × G_NL(t) − share_demand × D_NL(t), which needs hourly Dutch generation and load (ENTSO-E;
   load not fetched yet — a data request). A single net key (node, share) works with what is already there (scripts/61).
2. **Tulipa folder** (73 generalised): 33 Dutch demand assets with keyed demand and generation on the 2035 base, the 60
   branches with the option-3 limits — only after the keys.
3. **Decisions for the user**: the ">= 1 km" monitored rule (note 20; used here with the spur-row addition); whether the five
   spur buses stay nodes (they do no harm; they matter only if the keys put injection there).
4. The same scripts apply to the 2035 grids (117 on `v29-2035-amir` / `-tennet`) when wanted.

## Scripts and folders

dcopf scripts 116, 117, 118, 119, 120, 121; replay2025 scripts 61, 62. Limit runs `runs/2026-10-16-limits-nodal-v29-nl380-*`, networks `inputs/derived/diag_fixedpos_v29-nl380-sparse-LP-n1-*`, 2025 tests `replay2025/runs/fixedposnodal_*_key_nl-even-v29-nl380`; log `notes/ttc_nodal_pst_frm10_v29-nl380_2026-10-16.log`. `inputs/derived/jao_core_v29-nl380`;
`runs/2026-10-16-stage2-v29-nl380-LP-virtual`; `runs/2026-10-16-sparse-fit-nodal-v29-nl380-sparse-LP[-physx]`;
`inputs/derived/diag_fixedpos_v29-nl380-sparse-LP[-physx]`; `replay2025/runs/key_nl-even-v29-nl380`;
`replay2025/runs/fixedposnodal_diag_fixedpos_v29-nl380-sparse-LP[-physx]_key_nl-even-v29-nl380`. Aborted first attempts
kept: `…_ABORTED-ptdf-sign-convention` (2 run folders), `…_ABORTED-report-keyerror` (2 run + 2 network folders).
