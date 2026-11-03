# Handover — Core grid model for Tulipa (state on 2026-10-19)

This file is the starting point for a new session or a new person. It says what this folder is, how to run it,
which decisions are in force, where the results are, and what is still open. All paths are relative to this
folder (`core_grid_dcopf/`), so the folder can be moved as a whole. Details live in `README.md` and `docs/`.

---

## 1. What this is

A reduced representation of the Core electricity grid (JAO's Core Static Grid Model, 12 bidding zones,
1,756 buses at 380/220 kV) for the energy-system model **Tulipa**:

- **Country level:** one node per Core zone, 19 physical border branches with Kron-reduced reactances, branch
  limits from N-1 transfer limits with phase shifters set per exchange and a 10 % reliability margin
  ("option 3"). Used in a 2035 Tulipa input folder where these 19 DC-OPF branches replace the Core NTCs.
- **Nodal Netherlands (step 3):** the 33 Dutch 380 kV substations as separate nodes (44 nodes, 61 branches),
  every other zone one node, same limit method at node level. Built and tested; waits for the demand and
  supply distribution keys before it can be used in Tulipa.
- **Validation:** measured 2025 net positions routed through the network and compared with measured border
  flows (ENTSO-E) and with the limits; JAO line-by-line flow shares; JAO 2025 MaxBEX.

User's aim (2026-10-14): "a very good representation of the grid that works with 2025 data" usable for
2030/2035. "We are testing only how the grid model works; dispatch is another animal."

---

## 2. Read first

| File | What it gives |
|---|---|
| `README.md` | the chain script by script, folder layout, conventions |
| `docs/status_report_2026-10-19.pdf` | 6-page status report: decisions, results, open items |
| `docs/process_overview_2026-10-16.pdf` | picture of the whole chain, where N-1 and the margin enter |
| `docs/provenance.md` | dated log of every decision and run since the folder was created (continues the archive's log) |
| `docs/map_nl_grid_v29_v2.pdf` | map of the Dutch 380/220 kV grid as modelled (page 2: the north) |
| `docs/21_step3_nl_nodal_scoping_and_first_build.md` | the nodal Netherlands: design, first build, node-level limits |
| `docs/20_niederlangen_stub_monitored_set.md` | why only 380 kV lines of at least 1 km may set a limit |
| `docs/19_part2_2035_grids_result.md`, `docs/18_…amir_and_tennet.md` | the Dutch 2035 grids and the IP2026 selection rules |
| `docs/LINEAGE.md` | how the workbook v29 was built from JAO's file (archived scripts) |
| `docs/MAP.md` | each script here ↔ its original number in the archive |
| `docs/VERIFICATION.md` | proof that this folder reproduces the archived results exactly |
| `docs/ENVIRONMENT.md`, `docs/SOURCES.md` | software versions; data sources and sharing terms |

---

## 3. How to run

```bash
cd core_grid_dcopf
scripts/run_chain.sh v29-vvltr2            # country level (~3 min): reduction, limits, 2025 test, Tulipa folder, two test days
scripts/run_chain_nodal_hv.sh v29-vvltr2   # nodal Netherlands (~3 min): reduction, nodal limits, 2025 test with placeholder key
```

- Optional arguments: `run_chain.sh <version> [date tag = today] [ge1km | 380kv] [days]`; `run_chain_nodal_hv.sh <version> [date tag]`.
- Every step writes a new dated folder and refuses to overwrite; steps whose output exists are skipped, so a chain can be resumed.
  Running again on the same day therefore does nothing; use a new date tag to rebuild.
- **Known flaw:** the date tag only works on the day itself. The scripts name their folders with TODAY's date while the drivers look
  for them under the tag, so a past tag (e.g. `2026-10-19` run on 23 Oct) stops at the option-3 step. Run with today's date, or
  finish the remaining steps by hand as on 2026-10-23 (`docs/provenance.md`).
- Every script prints its usage when called without arguments.
- `run_chain_nodal.sh` (older, script 02n) is kept for reproduction only; use `run_chain_nodal_hv.sh` (02n2, keeps the path through the
  Dutch 220 kV ring).

**Environment** (`docs/ENVIRONMENT.md`): Python 3.9 at `~/.tulipa_pipeline_venv` (numpy, pandas, scipy, openpyxl, pyarrow;
`environment/requirements.txt`); Julia 1.12 at `~/.juliaup/bin/julia` with `Project.toml` / `Manifest.toml` here
(TulipaEnergyModel 0.22.2, HiGHS, ElectricityNetworkReduction 0.2.0 at commit de3d2583…). The drivers hard-code these two paths
(first lines of each `scripts/run_chain*.sh`); change them there if the environment lives elsewhere.

**Gotchas**
- Julia must run with `--threads=4,0` (zero interactive threads): the reduction package crashes otherwise; `01_reduce.jl` aborts if it detects one.
- `inputs/tulipa_baseline/2035_v2` must stay **read-only**: `01_reduce.jl` and `08_run_tulipa_pair.jl` abort if it is writable. After copying
  the folder, check it and if needed run `chmod -R a-w inputs/tulipa_baseline/2035_v2`.
- After moving the folder to another machine: `julia --project=. -e 'using Pkg; Pkg.instantiate()'` and recreate the venv from
  `environment/requirements.txt`.

---

## 4. Decisions in force (with dates; details in `docs/provenance.md` and the archive log)

| Date | Decision |
|---|---|
| Sep 2026 | Validation data (measured 2025 flows, JAO positions) are only compared against, never inputs. The Tulipa baseline is never modified. |
| Sep 2026 | Ratings = full thermal rating from the mean of JAO's listed currents; margins only in the limit step. |
| 13 Oct | Only 380 kV lines may set a transfer limit (no 220 kV lines, no transformers). |
| 14 Oct | "Option 3" for Tulipa: N-1 (every branch record out in turn) + phase shifters set per exchange within their range + 10 % margin. |
| 16 Oct | Dutch patch from GridAware/TenneT data (v28, v29): add missing lines, never overwrite a JAO rating, no duplicates, 220 kV and above only. |
| 16 Oct | Side branches tested and not adopted: phase-shifter series reactance (v30), seasonal ratings (v31). |
| 16 Oct | Croatia–Hungary and Poland–Slovakia limits: parked unless "really bad". Refitting the injection key: not pursued. |
| 16 Oct | Part 2 (2035 grid): Netherlands only; both our rule and TenneT's rule built; all decision-table proposals approved. |
| 16 Oct | Step 3: Netherlands nodal at 380 kV only; demand/supply keys to come from the project (handled in a separate session). |
| 16 Oct | Monitored rule: **380 kV lines of at least 1 km** (drops tee stubs such as Niederlangen, 0.33 km, fixed 450 MW, never monitored by JAO). |
| 16 Oct | Consolidate into this folder; the old working folders are archived, nothing deleted. |
| 19 Oct | Zwolle 380 kV and Hessenweg 220 kV are **not** coupled (user confirmed; TenneT's page: the new Hessenweg transformers are 220/110 kV). |
| 19 Oct | **Base workbook = `v29-vvltr2`** = v29 + two Vierverlaten 380/220 kV transformers with ASSUMED values (each a typical Dutch JAO unit, 31.5 Ω, 1,140 A). The coupling exists (TenneT IP2026 bottleneck 1578, asset "VVL TR426") but is in no grid file. |
| 19 Oct | **Reference Tulipa folder rebuilt with the 1 km rule** (on v29-vvltr2). |
| 19 Oct | Keep JAO's transformer reactances (experiment against merged stations, TNO style: transformers fit 2025 border flows and 220 kV line shares better). Nothing is claimed from that comparison (user). |

---

## 5. Reference results and where they are

**Country level (base v29-vvltr2, 1 km rule, option 3)**

| What | Where | Value |
|---|---|---|
| reduction | `runs/2026-10-19-stage2-v29-vvltr2-LP-virtual` | 12 representative buses (NL = Rilland) |
| N-1 and option-3 limits | `runs/2026-10-23-limits-v29-vvltr2-n1-380kv-ge1km[-pst-frm10]` (rebuilt 23 Oct) | |
| network (19 branches, X, limits) | `inputs/derived/diag_fixedpos_v29-vvltr2-sparse-LP-n1-380kv-ge1km-pst-frm10` | |
| 2025 test | `runs/fixedposdc_diag_fixedpos_v29-vvltr2-sparse-LP-n1-380kv-ge1km-pst-frm10_single` | r 0.895 (18 borders), MAE 0.387 GW (19), 91.7 % of hours inside |
| **Tulipa folder (reference)** | `inputs/derived/tulipa_dcopf_2035_base2b-v29-vvltr2-sparse19-n1-380kv-ge1km-pst-frm10` | + day cuts `…_day-2035-01-0{4,9}-seeded` |
| test days (NTC vs DC-OPF) | `runs/2026-10-23-stage3-pair-2035-01-0{4,9}-base2b-v29-vvltr2-…` (rebuilt 23 Oct, identical objectives) | 2035-01-04: 2.0686e9 / 2.0486e9 EUR; 2035-01-09: 1.0962e9 / 1.0969e9 |
| pair limits vs JAO 2025 MaxBEX (v29) | archive script 94 | median ratio 1.09; 23 % below JAO's p10, 38 % inside, 39 % above p90 |

**Nodal Netherlands (base v29-vvltr2)**

| What | Where |
|---|---|
| nodal workbook (44 representatives) | `inputs/derived/jao_core_v29-vvltr2-nl380` |
| reduction | `runs/2026-10-19-stage2-v29-vvltr2-nl380-LP-virtual` |
| sparse network (44 nodes, 61 branches incl. Vierverlaten–Ens via the 220 kV ring) | `runs/2026-10-19-sparse-fit-nodal-v29-vvltr2-nl380-hv-sparse-LP` |
| node-level N-1 / option-3 limits | `runs/2026-10-19-limits-nodal-v29-vvltr2-nl380-hv-n1-380kv-ge1km-nodal[-pst-frm10]` |
| **nodal network (reference)** | `inputs/derived/diag_fixedpos_v29-vvltr2-nl380-hv-sparse-LP-n1-380kv-ge1km-nodal-pst-frm10` |
| 2025 test with the even PLACEHOLDER key | `runs/fixedposnodal_…v29-vvltr2-nl380-hv…_key_nl-even-v29-vvltr2-nl380-hv` — r 0.909, MAE 0.401 GW, 91.6 % inside |
| effect of the Vierverlaten transformers | `runs/2026-10-19-compare-vierverlaten-tr/report.md` — ring carries 31 % of a Vierverlaten→Ens transfer, 17 % of Eemshaven exports to Germany |

Zone-to-zone transfer limits of the nodal network equal those of the country-level network (checked); zone *branch*
limits are not comparable one to one between the two networks. Dutch line limits are about 0.6 of their rating.

**Dutch 2035 grids (built on v29, NOT yet on v29-vvltr2):** `inputs/derived/jao_core_v29-2035-{amir,tennet}`; patches
`inputs/patches/ip2026_nl_2035_*`; decision table `inputs/patches/ip2026_nl_2035_decisions/decision_table.csv`.
At country level both rules give the same network; only the BE–NL option-3 limit moves (+4 %).

---

## 6. Open items and next steps (in order)

1. **Distribution keys** (critical path; a separate session). Per Dutch 380 kV node: demand share and generation share
   by technology (offshore wind, onshore wind, solar, gas, nuclear, other) + source. Proposed format: one CSV
   `node, share_demand, share_<technology>…, source`. Node codes = `NL-<bus name without _380, spaces as hyphens>` (see
   `nodes.csv` in the nodal network folder). The 2025 test script `scripts/10n_test_2025_nodal.py --key <csv>` takes a net
   key (`node, share`) today; separate demand/generation keys need hourly Dutch load and generation for 2025. This folder holds only the
   2025 border flows and net positions (`inputs/validation_2025/`); generation by type came from the archived 2025 fetch (see section 8),
   and **load still has to be fetched from ENTSO-E — needs the user's go-ahead**.
2. **Nodal Tulipa folder**: generalise `scripts/06_build_tulipa_inputs.py` to 33 Dutch demand nodes + 61 branches, once the keys exist.
3. **2035 grid on the new base**: apply the Vierverlaten transformer patch and the 2035 patches together (the patch step with
   modifications, archived script `113_apply_workbook_patch_modify.py`, is not yet copied here), then add the **five new 2035 380 kV
   stations** as nodes for the nodal model: Amaliahaven (2027, spur at Maasvlakte), Nieuwdorp Liechtensteinweg (2029–30, spur next to
   Borssele), Halsteren (2030–31, 3.5 km cable to Rilland), Einighausen (2031–34, 21 km to Maasbracht; our rule only),
   A9-Zuid (2032–35, loop-in on Beverwijk–Vijfhuizen; our rule only). Their connections are in the IP26 project matching's package (`NewLines_IP26 update/`).
4. **the IP26 project matching's update** (`NewLines_IP26 update/`, his IP26 package with final 2030/2040 networks in GridAware's format): read, not applied.
   Two issues raised (Teams message drafted 2026-10-19; check with the user whether it was sent and what he answered):
   (a) upgrades whose IP26 trace is slightly shorter than the line (88–99.9 %) count as "partial" and keep the OLD rating, so they have no
   capacity effect (Rilland–Zandvliet, Dodewaard–Doetinchem, Geertruidenberg–Rilland, Maasbracht–Boxmeer–Dodewaard, Maasbracht–Dodewaard);
   (b) the Borssele–Rilland cabled section takes the median cable rating of the GridAware file (1,481 A), halving the 380 kV corridor.
   Our 2035 grids already contain every 220/380 kV project up to 2035 with full 4,000 A upgrades and Borssele–Rilland's rating kept
   (X 9.63 → 7.28 Ω), so nothing needs updating for 2035. His package is the natural start for a 2040 Dutch grid once fixed
   (it includes Vierverlaten–Ens 380 kV, A-1002806, commissioning 2035–2038, outside both 2035 rules).
5. **Core-wide future grid** (only if wanted): ENTSO-E publishes 2030/2035/2040 capacities per border only
   (`../TYNDP 2026/Line-data/Line-data/ReferenceGrid_Electricity.xlsx` in the user's workspace; the Tulipa baseline uses it). Node-level
   TYNDP models are not public; an email to servicedesk@entsoe.eu was drafted on 2026-10-19 (to be sent by the user). Alternative: national
   plans (German NEP above all) mapped onto the JAO workbook as was done with IP2026.
6. **Parked**: Croatia–Hungary and Poland–Slovakia limits (actual 2025 flows exceed the option-3 limits in 40 % and 23 % of hours);
   Maasbracht–Dodewaard corridor loads 1.3–1.4× JAO's share; whether the five Dutch spur buses (landing/converter stations) stay nodes (kept).

---

## 7. Data, sharing, secrets

- `docs/SOURCES.md` lists every input and its terms. JAO publication data (the grid file, net positions) is for analysis; check
  JAO's terms before passing the folder on. ENTSO-E data: public with attribution. Tulipa baseline: project-internal.
  `NewLines_IP26 update/DATA/` holds TenneT ArcGIS exports marked "all rights reserved" (the IP26 project matching's note): keep local.
- No credentials anywhere in this folder. The archived ENTSO-E fetch script reads a token from the environment variable
  `ENTSOE_API_KEY` (kept in `~/.zshrc`); never write a token to a file, log or manifest.

## 8. The archive

The history (180 scripts, all workbook versions, run folders, JAO flow-based files, the 2025 data fetch with generation by type,
the 2025 Tulipa replay) lives in two folders, `dcopf/` and `replay2025/`, with their own log `dcopf/notes/provenance.md`.
**Location at handover (2026-10-19): unknown** — they were in `~/TNO/TestTulipa_TYNDP2026 - MAIN/archive/`, which is now empty; ask the
user where they were moved. An older copy of this folder also exists at `~/TNO/TestTulipa_TYNDP2026 - MAIN/core_grid_dcopf/`; the
current one is this folder. The chain does not need it. Two one-off scripts read from it and need that path if rerun:
`scripts/15_compare_vierverlaten_tr.py` (reproduction check) and
`experiments/2026-10-19_transformers_vs_merged/scripts/share_check.py` (JAO flow-based files). The JAO line-share check (archive
scripts 101/102) and the MaxBEX comparison (94) also live there.

## 9. Conventions (keep them)

- A script that has produced a result is never edited; a change is a copy with a new name whose header says what changed.
- Every run writes a new folder (manifest first: input hashes, configuration) and aborts if it exists; nothing is overwritten or
  deleted; superseded or aborted outputs are renamed `…_SUPERSEDED-<reason>` / `…_ABORTED-<reason>` and kept.
- Workbook versions are immutable folders in `inputs/derived/`; a new version is derived by a script or a patch (`scripts/13_apply_patches.py`).
- Invent nothing: assumed values are labelled as such (e.g. EIC codes `ASSUMED-NL-TR-…`); side branches are never adopted silently.
- Log decisions and runs, with their folders, in `docs/provenance.md`.

## 10. Glossary

| Term | Meaning |
|---|---|
| v29 | JAO Core Static Grid Model (March 2026) + documented corrections + two Dutch patches |
| v29-vvltr2 | v29 + two assumed Vierverlaten 380/220 kV transformers — the base since 2026-10-19 |
| Kron reduction | eliminates buses mathematically, keeping the electrical behaviour between the kept buses |
| sparse network | only the equivalent branches between physically connected zones (or nodes) are kept |
| N-0 / N-1 | limits with the intact grid / with every branch taken out in turn |
| option 3 | N-1 + phase shifters set per exchange + 10 % reliability margin (what Tulipa uses) |
| monitored set / 1 km rule | lines allowed to set a limit: 380 kV lines of at least 1 km |
| nodal Netherlands | the 33 Dutch 380 kV substations as nodes, other zones one node each |
| distribution keys | shares of Dutch demand and generation per node — needed to route flows inside the Netherlands |
| fixed-position test | measured 2025 hourly net positions routed through the network, compared with measured border flows |
