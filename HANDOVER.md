# The Dutch 2035 grid model: handover

Written 3 November 2026 for the colleague who takes over the grid. It explains, in order, everything that was done to build the
electricity grid used in the RenewaFLEX 2035 runs: where each piece of data comes from, what we changed and why, what we assumed,
and what is still open. Everything this document mentions is in this folder, except a few earlier scripts that are lost
(said where it matters) and the RenewaFLEX folders where the networks are used.

**GridAware** is the data set of the full Dutch grid at all voltage levels; **SR2025** is the scenario data set whose 32 Dutch
nodes carry the demand and supply of the RenewaFLEX runs. **Tulipa** is the energy-system model the networks are made for; **RenewaFLEX** is the project; **nl_merge** is the part of it
that builds the Dutch Tulipa inputs. Other terms are explained in section 8.

If you only read one section, read **1. The short version**. If you want to change the grid (for example add the 2040 lines), go
to **5. How to add new lines (2035 changes, 2040)**.

---

## 0. What is in this folder

| folder / file | what it is |
|---|---|
| `HANDOVER.md` (this file; also as `.docx`) | the explanation |
| `CHECK_REQUEST.md` | short note for checking how the IP26 project matching code was used for the 150/110 kV grid (section 9) |
| `pipeline/` | everything needed to rebuild the grid: the code (`pipeline/scripts/`), the input data (`pipeline/inputs/`) and one command that runs it all (`pipeline/run_all.sh`) |
| `pipeline/inputs/derived/jao_core_v29/` | the starting point: the 2026 grid workbook (JAO data with our fixes and the missing Dutch lines already in it) |
| `pipeline/inputs/patches/` | the two patches already inside v29 and the 2035 decision table; `run_all.sh` writes the other patches here. The patch files in use, each with a `CHANGELOG.md` that says what and why, are in `reference_outputs/original_patches/` |
| `pipeline/hv_ip26/`, `pipeline/run_all_hv.sh` | the IP26 project matching code with a 2035 horizon, and the run that adds the 150/110 kV grid (section 9, first version) |
| `reference_outputs/` | the five finished 2035 networks exactly as the RenewaFLEX runs use them, the original patches, and the German split files, to compare a rebuild against; `networks/hv_nodal_main` and `hv_150_110/` hold the first version with the 150/110 kV grid (section 9); `NETWORK_NAMES.csv` gives the full name of each network |
| `sources/` | the original documents and data files from outside (JAO, GridAware, TenneT, ACER, SR2025, the IP26 project matching code with its saved outputs) |
| `background_notes/` | the working notes written during the project (more detail, more jargon), maps of the grid, the old handover of 19 Oct, and the scripts exactly as run (`original_scripts/`) |

---

## 1. The short version

We need a model of the high-voltage grid (380 kV and 220 kV) of the Netherlands and its neighbours in 2035, small enough for the
energy-system model (Tulipa), but with the Dutch grid detailed enough to see where it gets congested.

We built it in three stages:

**Stage A: make a complete grid file for 2035** (the "workbook": an Excel file with every node, line and transformer).

1. Start from **JAO's Core Static Grid Model (March 2026)**: the official grid file of the 12 Core countries, 1,756 nodes.
2. Add the **Dutch lines that JAO's file is missing** (Randstad ring, a Friesland 220 kV line, a second Maasbracht–Dodewaard
   circuit, one Borssele–Rilland circuit). Values from the GridAware network and JAO's own operational files.
3. Add one **transformer at Vierverlaten** that no file has, with assumed values, so that the northern 220 kV ring is connected.
4. **Add the 2035 projects** from TenneT's Investment Plan 2026 (IP2026): a new Rilland–Tilburg line, the new Tilburg station,
   higher ratings on several lines, a cable section on Borssele–Rilland. **This is where the 2035 lines come in.**
5. **Loop the Geertruidenberg–Eindhoven line into Tilburg** (TenneT's plan for station Tilburg).
6. **Raise two more corridors to 4,000 A** (Krimpen–Geertruidenberg, Maasbracht–Eindhoven; TenneT says this is done).
7. Optionally **split Germany into north and south** (ACER's split), for one network variant.
8. Mark the **32 SR2025 Dutch substations** as the nodes we keep.

**Stage B: reduce the network and calculate TTCs.** (Script names in `pipeline/scripts/` start with the stage letter: A1–A7, B1–B5, C1–C2.)

9. **Reduce** the 1,756-node grid to 43 nodes (the 32 SR2025 Dutch substations plus one node per other country) with the same
   electrical behaviour between those nodes (Kron reduction).
10. Decide **which lines may limit** flows (380 kV lines of at least 1 km, plus Dutch 220 kV lines of at least 1 km).
11. Compute the **TTCs** (total transfer capacities) and from them a **limit (MW) for every branch** of the reduced network such that the real grid stays within its ratings even if any
    one element fails (N-1), with phase shifters set as the operators would, and 10 % of each rating kept as a reliability margin.

**Stage C: one correction.**

12. The limits are computed one exchange at a time, so the Dutch border ties together allow more than the real grid can carry.
    We **scale the border ties down** until the reduced network allows no more than the real grid (Belgian ties × 0.826).

The result is a folder with three small files (`nodes.csv`, `flow.csv`, `flow-milestone.csv`) that the Tulipa model builder
reads. There are five variants (section 4.4); the RenewaFLEX runs mostly use the one with the corrected Belgian ties.

A first version that also includes the Dutch 150/110 kV grid, built with the IP26 project matching code, is described in
section 9. It is not used in any run yet and needs checking.

![The whole chain on one page. Yellow: where the 2035 lines and ratings enter.](figures/chain_overview.png)

Everything from step 3 onward can be rebuilt with one command (`pipeline/run_all.sh`, about 15 minutes), and the rebuild was
checked to give the same numbers as the networks in use (section 6). Steps 1 and 2 were done earlier with scripts that are
no longer available; their result (the v29 workbook) is the starting file, and every change they made is listed in it
(section 2.1).

---

## 2. Stage A, step by step: the grid file for 2035

The grid file is an Excel workbook, `jao_core.xlsx`, with six sheets: `Nodes` (buses), `Lines`, `Tielines` (lines across a
border), `Transformers`, `DCLines`, `Generators`. Each line row has its two end buses, the series reactance `X` (ohm), the current
rating (A), the length and the capacity in MW. Capacity is always computed the same way, as JAO does:
**MW = √3 × 400 kV × current (kA)** for 380 kV, and √3 × 225 kV × current for 220 kV. So 4,000 A = 2,771.281 MW.

Every change to the workbook is a **patch**: a folder in `pipeline/inputs/patches/` with the rows to add, change or remove, and a
`CHANGELOG.md` that gives the source of every value (the patches in use are also in `reference_outputs/original_patches/`). A patch is never typed into the workbook by hand. The script
`A5_apply_patches.py` applies patches and writes a new workbook version in a new folder; it never overwrites, and it checks that
every row it changes still has the values the patch expects.

Workbook versions are named by what is in them:

| version | = | what was added |
|---|---|---|
| `v29` | JAO 2026 + our data fixes + missing Dutch lines | the starting point (2.1, 2.2) |
| `v29-vvltr2` | v29 + Vierverlaten transformer (2 units) | 2.3 |
| `v29-vvltr2-2035-tennet-tlb3` | + IP2026 2035 projects (TenneT rule) + Tilburg loop-in (3 circuits) | 2.4, 2.5 |
| `v29-vvltr2-2035-tennet-tlb3-rt4k` | + 4 kA on two corridors | 2.6 |
| `…-rt4k-de2` | + Germany split north/south | 2.7 |
| `…-nlsander` | + the 32 SR2025 Dutch nodes marked as the nodes to keep | 2.8 |

### 2.1 Start: JAO's Core Static Grid Model (March 2026) → workbook v27

- **Source:** JAO, Core Static Grid Model, 9th release, March 2026 (`sources/01_jao_core_static_grid_model_2026/`: the Excel
  file, JAO's handbook and the web page with the station coordinates). Downloaded 5 June 2026 from JAO's publication tool.
- **What it is:** the grid model the Core TSOs publish for flow-based market coupling: every 380 and 220 kV line, tie-line and
  transformer of AT, BE, CZ, DE, FR, HR, HU, NL, PL, RO, SI, SK, with reactances and current ratings.
- **What we did to it** (the result is listed row by row in `pipeline/inputs/derived/jao_core_v29/`: `build_report.md`,
  `row_decisions.csv`, `corrections.csv`):
  - turned it into the six-sheet workbook; rating = mean of the seasonal currents JAO lists; R and B set to 0 (a DC power flow
    needs only X);
  - tie-lines that both neighbouring operators list were matched and kept once;
  - phase-shifter rows that connect a bus to itself were left out;
  - station spellings merged; 15 small pieces of grid with no connection to the rest left out (listed in `build_report.md`);
  - one bus per country chosen as its "representative" (for the Netherlands: Rilland);
  - four data errors fixed after comparing with JAO's daily flow-based data (versions v23–v27).

### 2.2 Dutch lines missing from JAO's file → v28, v29

JAO's static file misses some Dutch lines that exist today. We found them by comparing with the **GridAware network**
(`sources/02_gridaware/full_network.csv`, the full Dutch grid including 150 and 110 kV) and confirmed each one in **JAO's
own 2026 flow-based files**, where TenneT uses them as monitored lines or outages. Full report:
`background_notes/14_nl_patch_from_gridaware.md`.

Patch `jao2026_nl` (→ v28), 2 new nodes and 8 circuits:

| line | circuits | current (A) | values from | why it matters |
|---|---|---|---|---|
| Beverwijk – Vijfhuizen 380 kV | 2 | 3,000 | GridAware (X, length); rating confirmed in JAO's flow-based file | closes the Randstad ring west of Amsterdam |
| Bleiswijk – Vijfhuizen 380 kV | 2 | 3,000 | same | same |
| Beverwijk – Oostzaan 380 kV | 2 | 3,300 | GridAware | same; Oostzaan was a dead end without it |
| Bergum – Vierverlaten 220 kV | 2 | 2,500 | GridAware | closes the Friesland 220 kV ring |

New nodes: Beverwijk 380 and Vijfhuizen 380 (coordinates from TenneT's station layer).

Patch `jao2026_nl_2` (→ v29):

| element | values from | note |
|---|---|---|
| node Boxmeer 380 | IP2026 project point | |
| Maasbracht – Boxmeer 380 kV, Boxmeer – Dodewaard 380 kV (the second Maasbracht–Dodewaard circuit) | X and length: GridAware; current 2,498 A: JAO 2026 flow-based file | decision 16 Oct 2026: JAO's current, not GridAware's 2,000 A |
| Borssele – Rilland 380 kV circuit P | JAO's own file | this one was not missing from JAO: our first builder dropped it by mistake as a duplicate |

**Effect, checked:** the lines through Amsterdam now carry flows close to what JAO shows: TenneT lines within ±25 % of JAO's
flows went from 74 % to 83 % after patch 1 (78 % after patch 2, see the notes). An independent review checked patch 1 row by row
and accepted it (`background_notes/14_…md`, §10).

### 2.3 Assumed transformer at Vierverlaten → v29-vvltr2

- **Problem:** the northern 220 kV ring (Ens – Oudehaske – Louwsmeer – Bergum – Vierverlaten – Zeyerveen – Hessenweg – Ens) touches the
  380 kV grid only at Ens in every file we have. In reality there are 380/220 kV transformers at Vierverlaten: TenneT's IP2026
  lists "Vierverlaten 380/220 kV-transformatoren" as a bottleneck (number 1578), but no file gives their values.
- **What we did:** added 2 transformer units at Vierverlaten with **assumed** values: the median reactance of the 8 Dutch
  380/220 kV units in JAO's file (31.529 ohm), 1,140 A each. Codes `ASSUMED-NL-TR-0001/0002`. Script
  `A1_build_patch_vierverlaten_transformer.py`, patch `nl_vierverlaten_tr_assumed_2u`.
- **Effect:** a new branch Vierverlaten–Ens in the reduced network; the ring carries about 30 % of a Vierverlaten→Ens transfer.
- **Checked and rejected:** a transformer between Zwolle 380 and Hessenweg 220 (in the GridAware file, formula values only). The previous owner
  confirmed there is none (19 Oct 2026).
- **Note:** one working note (`background_notes/provenance.md`, 19 Oct) calls this transformer "not adopted". That entry
  was written before the decision to build all later networks on v29-vvltr2. It **is** in every network in use.

### 2.4 The 2035 projects from TenneT's IP2026 → this is where the 2035 lines come in

- **Source:** TenneT, *Investeringsplan 2026 Net op land* and its annexes 4–6 (`sources/03_tennet_ip2026/`), plus TenneT's map
  layer of the planned lines (`IP26_line.xlsx`, `IP26_point.xlsx`, 167 line features with phase and commissioning years).
- **Which projects count for 2035.** IP2026 projects have a phase: *Studie* (study), *Voorbereiding* (preparation, past the first
  gate) and *Realisatie* (realisation, investment decided). Two rules were compared (`background_notes/18_…md`):
  - **TenneT's own rule** (IP2026 §5.3): only projects already in realisation. TenneT uses this rule for its own 2035 and 2040
    grids. **This is the rule of every network in use.**
  - **Our rule:** realisation and preparation, study left out. More optimistic.
  - In both: a project counts if the *last* year of its commissioning window is 2035 or earlier; 220 kV and up only.
- **The decision table** `pipeline/inputs/patches/ip2026_nl_2035_decisions/decision_table.csv` lists, for every project in the
  window, what it does to the grid and with which values (one row per element). `projects.csv` next to it lists all 28 Dutch
  220/380 kV projects with their phase and years, including those after 2035.
- **Values used** (from the decision table's `value_rule` column):
  - a reinforced line gets 4,000 A (IP2026 §7.4: all domestic 380 and 220 kV connections go to 4 kA);
  - a new 380 kV overhead line: X = length × 0.273 ohm/km (median of the Dutch 380 kV lines in JAO's file), 4,000 A, 2 circuits;
  - a cable section: X of the cabled share × 0.134 ohm/km (median of the GridAware 380 kV cables); rating unchanged (not published);
  - a new station with no line of its own is recorded but not built (it changes no flow).
- **Script:** `A2_build_patch_from_decisions.py` reads the table and writes the patch; `A5_apply_patches.py` applies it.

What the 2035 patch changes (patch `ip2026_nl_2035_tennet`, 7 projects):

| project | IP2026 | phase, in service | change in the workbook |
|---|---|---|---|
| Rilland – Tilburg 380 kV (Zuid-West 380 kV Oost) | A-1002678 | realisation, 2031–2034 | **new line**, 2 circuits, 78.1 km, X 21.294 ohm, 4,000 A; **new node** Tilburg 380 |
| Krimpen – Diemen – Beverwijk 380 kV reinforcement | A-1003430 | realisation, 2030–2031 | 7 circuits (Krimpen–Diemen, Krimpen–Breukelen, Breukelen–Diemen, Oostzaan–Diemen ×2, Beverwijk–Oostzaan ×2) to 4,000 A |
| Rilland – Zandvliet 380 kV new conductors | A-1000664 | realisation, 2025 | 2 tie-lines to Belgium 3,790 → 4,000 A |
| Borssele – Rilland 380 kV cabling | A-1002896 | realisation, 2028 | circuits G and Z: X 9.63 → 7.28 ohm (19.8 of 38 km cabled) |
| Amaliahaven, Nieuwdorp Liechtensteinweg, Halsteren 380 kV stations | A-1003091, A-1003600, A-1003120 | realisation | recorded, not built (no flow effect) |

Under our rule (patch `ip2026_nl_2035_project`, built, not used) six more projects are added: Dodewaard–Doetinchem,
Maasbracht–Boxmeer–Dodewaard and Geertruidenberg–Rilland to 4,000 A, a third Eemshaven Oudeschip–Eemshaven circuit, and two stations.
At country level both rules gave the same result (`background_notes/19_…md`).

### 2.5 Tilburg looped into Geertruidenberg–Eindhoven

- **Source:** TenneT, *Aanmeldingsnotitie m.e.r. hoogspanningsstation Tilburg* (2 February 2022), `sources/04_tennet_tilburg_2022/`:
  the new Tilburg 380 kV station is connected into the existing Geertruidenberg–Eindhoven line; 2 of 3 circuits from 2027, the
  third once Rilland–Tilburg is ready. So all 3 by 2035.
- **What we did:** each of the 3 circuits Geertruidenberg–Eindhoven is replaced by Geertruidenberg–Tilburg + Tilburg–Eindhoven.
  Length and X split by straight-line distance (one third / two thirds); rating unchanged. Script `A3_build_patch_tilburg_loopin.py`,
  patch `ip2026_nl_2035_tilburg_loopin_3c`.
- Without this, Tilburg would be the end of a dead-end line (2.4) and Rilland–Tilburg would carry no through-flow.

### 2.6 4,000 A on Krimpen–Geertruidenberg and Maasbracht–Eindhoven

- **Source:** IP2026 p.109, Table 8.5 ("Beter Benutten Bestaande 380 kV"): both corridors upgraded to 2 × 2,635 MVA (4 kA),
  status "gereed" (done). JAO's 2026 file still lists 3,300 A.
- **What we did:** 4 circuits 3,300 → 4,000 A. Script `A4_build_patch_rating_4ka.py`, patch `ip2026_nl_2035_rating_4ka`.

### 2.7 Germany split north/south (one variant only)

- **Source:** ACER Decision 11/2022, Annex VI, the German TSOs' two-zone split (`sources/05_acer_germany_split/`).
- **What we did:** every German bus gets zone north or south (50Hertz north; Amprion and TransnetBW south; TenneT Germany by
  latitude, north of Voerden; Niederlangen south). Germany then has two nodes, DE0N and DE0S. Script `A6_split_germany.py`.
- The split shares of German demand and generation and the 2035 north–south HVDC links that the Tulipa builder needs are in
  `reference_outputs/germany_split/` (made in the grid project from ENTSO-E's Bidding Zone Review 2025 data; not rebuilt here).

### 2.8 The 32 SR2025 Dutch nodes

- **Source:** the SR2025 node list (`sources/06_sr2025_nodes/nl_ielgas_sander_32.csv`; the file name is kept as the networks in use refer to it): 32 Dutch substations (27 at 380 kV,
  5 at 220 kV only) for which the demand and supply keys exist.
- **What we did:** these 32 buses are marked as nodes to keep (`IsRepresentative = 1`); every other Dutch bus is eliminated in the
  reduction. Script `A7_set_dutch_nodes.py`.

---

## 3. Stage B: from the full grid to a reduced network with limits

### 3.1 Reduction (`B1_reduce.jl`)

The full workbook (1,756 buses in the 2026 workbook v29, one more with Tilburg) is reduced to the nodes we keep: the 32 SR2025 Dutch nodes and one representative bus per other
country (43 nodes; 44 with Germany split). The method is **Kron reduction**: the eliminated buses are removed from the network
equations so that, between the kept nodes, power flows exactly as in the full grid. It is done by the Julia package
*ElectricityNetworkReduction* (TulipaEnergy on GitHub). Output: the equivalent reactance between kept nodes, and the full-grid
sensitivities (PTDFs: how many MW flow over each line per MW exchanged) used for the limits.

### 3.2 Which node pairs get a branch (`B2_network_nodal.py`, `B2_network_country.py`)

Kron reduction connects almost every pair of nodes. We keep a branch only where there is a physical connection: two Dutch nodes
joined by a line (directly or through eliminated Dutch 220 kV buses), a Dutch node and a neighbouring country joined by a tie-line,
and two countries that share a border. Result: 64 branches (66 with Germany split).

### 3.3 Which lines may set a limit (`B3_monitored_lines.py`, `B3_monitored_lines_nodal.py`)

A branch limit comes from the lines in the real grid that would overload first. We let **380 kV lines of at least 1 km**
(everywhere) and **Dutch 220 kV lines of at least 1 km** do that. Why: TenneT, Amprion, Elia, 50Hertz, RTE and PSE only had 380 kV
elements binding in 2025, and very short stubs (such as the 0.33 km Niederlangen tee) set unrealistic limits
(`background_notes/20_…md`).

### 3.4 TTCs: N-1, phase shifters, 10 % margin (`B4_…`, `B5_…`)

For every pair of nodes, the scripts compute the **TTC** (total transfer capacity): the largest exchange the **full** grid can carry with every monitored line within
its rating, also when any one line or transformer is out (N-1). Each node's exchange is spread over the 380 kV buses behind it.
Then:
- **phase shifters** (Belgian, Dutch and German) are set for each exchange within the range the operators use;
- every rating is reduced by **10 %** (JAO's reliability margin).
This is called "option 3" in the notes. Each branch of the reduced network gets the largest flow it carries in any of these
exchanges. Checked on 2025: the limits are on average 1.09 times what JAO offered the market (MaxBEX, the largest exchange between two countries in JAO's market coupling), and 92 % of the hours of
2025 fall inside them (`background_notes/27_limitations_and_freeze.md`).

---

## 4. Stage C and the result

### 4.1 Border-tie correction (`C1_full_grid_border_check.py`, `C2_tie_correction.py`)

Because each branch gets the largest flow of any single exchange, several exchanges together can exceed what the real grid can
carry. Check (C1): in the reduced network the Netherlands could export 6,416 MW to Belgium; the full grid allows 5,300 MW
(the bottleneck is Doel–Zandvliet in Belgium). Correction (C2): one factor on both Belgian ties so that the reduced network allows
exactly 5,300 MW: **× 0.826** ("main" in the tables below; `C2_tie_correction.py` mode `beonly`; German ties unchanged, which leaves NL → Germany 0.3 % above the full grid). A stricter variant also scales the German ties (× 0.797) so that NL → Belgium + Germany together
is right ("lower"). With Germany split, the main variant (mode `main`) scales Belgian ties × 0.832 and German ties × 0.852.

### 4.2 The output files

Each network is a folder with:

| file | content |
|---|---|
| `nodes.csv` | node name (`NL-BERGUM`, `BE00`, …), the Tulipa asset it belongs to, zone, representative bus, voltage, Dutch or not |
| `flow.csv` | one row per branch: from, to, `capacity` = the limit in MW (same in both directions) |
| `flow-milestone.csv` | one row per branch: `reactance` in per unit on 100 MVA, for Tulipa's DC power flow |
| `README.md`, `manifest.json`, `sha256.txt` | how it was made, input hashes |

### 4.3 How the Tulipa runs use it

The NL merge (`nl_merge`, the SR2025 data in Tulipa) reads one network folder with `--core-dcopf` and maps the SR2025 nodes to the
network nodes with `nl_ielgas_sander_32.csv`. "Copper plate" runs (no grid limits inside the Netherlands) use the same folder with the Dutch limits lifted.

### 4.4 The five networks

In this package each network has a **short name**. The grid scripts give them long technical names (the ones the RenewaFLEX runs
and manifests use); `reference_outputs/NETWORK_NAMES.csv` lists both. After a rebuild, `run_all.sh` copies the finished networks
to `pipeline/outputs/<short name>/`.

| short name | Netherlands | Germany | border ties | nodes / branches | used for |
|---|---|---|---|---|---|
| `nodal_main` | 32 nodes | 1 node | main (BE × 0.826) | 43 / 64 | **main nodal runs** |
| `nodal_lower` | 32 nodes | 1 node | lower (BE × 0.826, DE × 0.797) | 43 / 64 | sensitivity |
| `nodal_de2_main` | 32 nodes | north, south | main (BE × 0.832, DE × 0.852) | 44 / 66 | runs with Germany split |
| `country` | 1 node | 1 node | none | 12 / 19 | country-level runs |
| `country_de2` | 1 node | north, south | none | 13 / 22 | country level, Germany split |

How the long names are built (for example `nodal_main` = `diag_fixedpos_v29-vvltr2-2035-tennet-tlb3-rt4k-nlsander-hv-sparse-LP-n1-380kv-nl220-ge1km-nodal-pst-frm10-tiefixbe`):
the workbook version (`v29-vvltr2-2035-tennet-tlb3-rt4k`: section 2; `tlb3` Tilburg looped in, `rt4k` the 4 kA patch), `nlsander`
the 32 SR2025 nodes, `n1-380kv-nl220-ge1km` N-1 TTCs from 380 kV and Dutch 220 kV lines of at least 1 km, `pst-frm10` phase
shifters and 10 % margin, `tiefix…` the tie correction.

---

## 5. How to add new lines (2035 changes, 2040)

New lines enter in **Stage A only**: you make a patch, apply it to a workbook, then rerun Stages B and C. Nothing in Stages B and
C needs to change.

**To build a 2040 grid with TenneT's projects:**

1. Copy `pipeline/inputs/patches/ip2026_nl_2035_decisions/` to a new folder, e.g. `ip2026_nl_2040_decisions/`.
2. In its `decision_table.csv`, **delete the 27 rows of 2035** (they are already in the 2035 workbook; applying them again
   stops with ABORT because the old values no longer match). Then add one row per element of every project whose commissioning
   window ends in 2036–2040. `projects.csv` already lists the candidates (rows with `ibn_end` 2036–2040), and the full list with phases and
   years is TenneT's layer `sources/03_tennet_ip2026/IP26_line.xlsx`. For each row fill: `action` (add node / add line / modify /
   skip), the line name and buses as they are in the workbook, old and new current, MW and X, length, `value_rule` (where the
   values come from) `rule_tennet` / `rule_project` (yes/no), `status`, and the evidence columns `project`, `project_name`, `phase_layer`, `ibn_ip2026`,
   `ip26_page` (the header of `A2_build_patch_from_decisions.py` lists every column it reads). Use the value rules of 2.4, or better values if TenneT publishes them.
3. Build and apply the patch on top of the 2035 workbook (so 2040 = 2035 + the new projects):

   ```bash
   cd pipeline
   python scripts/A2_build_patch_from_decisions.py inputs/patches/ip2026_nl_2040_decisions tennet v29-vvltr2-2035-tennet-tlb3-rt4k ip2026_nl_2040_tennet --eic-prefix=PATCH-NL40
   python scripts/A5_apply_patches.py v29-vvltr2-2035-tennet-tlb3-rt4k v29-vvltr2-2035-tennet-tlb3-rt4k-2040 inputs/patches/ip2026_nl_2040_tennet
   ```
4. Mark the SR2025 nodes (`A7_set_dutch_nodes.py`) and run Stages B and C on the new version: in a copy of `run_all.sh`, set
   `V=v29-vvltr2-2035-tennet-tlb3-rt4k-2040` (it is used by both the `chain` part and the Stage C lines) and skip the A steps. If a new station must become a node of its own, add it to the node list first.

**What to watch out for:**
- TenneT's own 2040 grid uses only realisation-phase projects and is "almost identical to the 2035 grid" (IP2026 chapter 3). With
  that rule a 2040 grid will add little; with our rule it adds many preparation-phase projects (the IP26 matching code in
  `sources/07_ip26_project_matching/` kept 70 line sections for 2040). The choice of rule is the main decision.
- A new station without its own demand or generation changes no flow. It only matters if a line passes through it (loop-in, as
  Tilburg) or if the SR2025 keys put demand or supply there.
- Projects that change a line that exists in the workbook must name it exactly as in the workbook (sheet, `Line_name`, `EIC_Code`);
  `A5_apply_patches.py` stops if the old values do not match. Use `pipeline/inputs/derived/jao_core_<version>/jao_core.xlsx` to look them up.
- Foreign grids stay as in 2026. German, Belgian and other 2035/2040 projects are not in the model (section 7).

---

## 6. How to rebuild, and how we checked it

```bash
cd pipeline
bash run_all.sh                         # about 15-25 minutes; writes inputs/derived/, inputs/patches/, runs/, logs/
python scripts/verify_against_reference.py   # compares the five rebuilt networks with reference_outputs/
bash run_all_hv.sh                      # optional, section 9: the network with the 150/110 kV grid (about 5-10 minutes)
```

Requirements (`pipeline/environment/`): Python 3.9 with numpy, pandas, scipy, openpyxl, pyarrow (versions in
`requirements.txt`); Julia 1.12 with the packages in `Project.toml` / `Manifest.toml` (instantiate once with
`julia --project=. -e 'using Pkg; Pkg.instantiate()'`). `run_all.sh` uses `python3` and `julia --threads=4,0`; set `PY=` or `JL=` to use others (for example
`PY=~/.tulipa_pipeline_venv/bin/python bash run_all.sh` on the RenewaFLEX laptop).

Every script refuses to overwrite an existing output folder, writes a `manifest.json` with the hashes of what it read, and prints
its instructions when called without arguments.

**Checks done for this handover (3 November 2026):**

1. **Workbooks and patches.** Rebuilt from v29 with the scripts of this folder, the 2035 patches (Vierverlaten, IP2026 under both
   rules, Tilburg, 4 kA) are byte-identical to the original patch files (`reference_outputs/original_patches/`), and every
   workbook version (v29-vvltr2 up to the two `-nlsander` workbooks) is identical, sheet by sheet, to the one in the grid project.
2. **Networks.** `run_all.sh` followed by `verify_against_reference.py`: all five networks have the same nodes, the same branches,
   and limits and reactances with zero difference from the networks the RenewaFLEX runs use.
3. **Scripts as run.** The same check with the original, unrenamed scripts (`background_notes/original_scripts/`) also gave
   zero difference.

One thing the check showed: the tie correction of the main one-Germany network scales only the Belgian ties. In that network the
Netherlands can still export 10,356 MW to Germany against 10,322 MW in the full grid (0.3 % more). The Germany-split network does
correct the German ties. This is left as it is in the networks in use (mode `beonly` of `C2_tie_correction.py`).

---

## 7. What is assumed, what is open

### Assumptions in the networks in use

| # | assumption | where | how big |
|---|---|---|---|
| 1 | Vierverlaten 380/220 kV transformers: 2 units with median Dutch values | 2.3 | changes northern limits by 5–23 % |
| 2 | Ratings of the GridAware lines Beverwijk–Oostzaan (3,300 A) and Bergum–Vierverlaten (2,500 A) cannot be checked against JAO | 2.2 | open |
| 3 | 2035 = realisation-phase projects only (TenneT's rule) | 2.4 | at country level no difference with our rule |
| 4 | New-line and cable reactances per km are medians, not project data | 2.4 | Rilland–Tilburg only |
| 5 | Tilburg loop-in: length split by straight-line distance | 2.5 | small |
| 6 | Foreign grids as in 2026; Germany without its 2035 north–south HVDC lines in the one-node networks | all | the least certain part of 2035 flows |
| 7 | Each country's exchange spread evenly over its 380 kV buses when computing limits | 3.4 | individual lines can be off; limits right on average |
| 8 | One rating per line (mean of JAO's seasons); DC power flow, no losses or voltage limits | 2.1 | seasonal patterns flattened |
| 9 | Tie correction is one uniform factor every hour | 4.1 | conservative in some hours |

Full list with numbers: `background_notes/27_limitations_and_freeze.md`.

### Open items

- **Lost scripts.** The scripts from JAO's raw file to v29 and the original 2035 patch builder were in an archive folder that is no
  longer on this computer (`~/TNO/TestTulipa_TYNDP2026 - MAIN/archive/`). If someone has a copy, add it to `sources/`. The 2035 patch
  builder has been rewritten (`A2_…`) and gives identical files.
- **2040 grid:** not built (section 5).
- **Maasbracht–Dodewaard** carries 1.3–1.4 times the share of exchanges JAO gives it; not resolved.
- **Vierverlaten transformer values:** ask TenneT (data request open since October).
- **150 and 110 kV:** not in the networks in use; a first version is in section 9.
- **Other countries' 2035 projects** (German north–south corridors, Belgian and French reinforcements): not included.
- **Offshore landing stations** (Wijk aan Zee, Hollandse Kust, Borssele platforms): only as far as JAO has them; offshore wind is
  connected to its landing node in the NL merge, not in this grid.

---

### Next step: the 150/110 kV grid

A first version that adds the Dutch 150/110 kV grid is built and described in section 9. It is not used in any run yet and
needs checking.

## 8. Words used

| word | meaning |
|---|---|
| JAO | Joint Allocation Office; publishes the Core grid model and the daily flow-based market data |
| Core | the 12-country region of flow-based market coupling (AT, BE, CZ, DE, FR, HR, HU, NL, PL, RO, SI, SK) |
| workbook | our Excel version of the grid (`jao_core.xlsx`) |
| patch | a folder of rows to add / change / remove in the workbook, with sources |
| EIC | the identifier of a grid element in JAO's files; our own rows have codes like `PATCH-NL-0001` or `ASSUMED-…` |
| circuit | one three-phase line; a "double-circuit" line has two (named by colour: W wit, Z zwart, G grijs, …) |
| X | series reactance (ohm); decides how power splits between parallel paths |
| rating / capacity | the most current (A) or power (MW) a line may carry; MW = √3 × 400 kV × kA at 380 kV |
| Kron reduction | removing buses from the network equations while keeping the electrical behaviour between the rest |
| PTDF | how much of a 1 MW exchange flows over a line |
| N-1 | the grid must stay within ratings when any one element fails |
| phase shifter (PST) | a transformer that steers flow on a line; set per exchange here |
| FRM / margin | the 10 % of each rating kept free for uncertainty |
| option 3 | our limit rule: N-1 + phase shifters + 10 % margin |
| MaxBEX | the largest exchange JAO's market coupling offered between two zones; used to check our limits |
| IP2026 | TenneT's Investment Plan 2026 for the onshore grid |
| Realisatie / Voorbereiding / Studie | TenneT's project phases: realisation (investment decided), preparation, study |
| GridAware | the network data set of the full Dutch grid (all voltage levels) |
| SR2025 nodes | the 32 Dutch substations for which the SR2025 demand and supply keys exist |
| TTC | total transfer capacity: the largest exchange between two nodes that the full grid carries N-1 secure; branch limits are derived from the TTCs |
| DE2 | Germany split into two zones (north, south) as in ACER's bidding-zone review |

---

## 9. First version: the 150/110 kV grid added (to be checked)

Built 3 November 2026. **Not used in any run yet.** The networks of section 4.4 do not contain it.

### 9.1 What it is and where it comes from

The 380/220 kV grid stays exactly as in sections 2–4 (JAO 2026 + our patches). Below it we add the Dutch 150 and 110 kV grid of
2035, taken from the **IP26 project matching code** (`pipeline/hv_ip26/`, a copy of the code in `sources/07_ip26_project_matching/`).
That code takes the GridAware network (`full_network.csv`, all Dutch voltage levels) and applies TenneT's IP2026 projects for a
target year. We use it as it is, with one change: **2035 added to the horizons** in `config_horizons.yaml` and
`config_final_network.yaml` (it had 2030 and 2040). Its other settings are unchanged: study-phase projects left out (our rule),
last year of the commissioning window counts, parameter scenario `median`, and its reviewed decisions in `config_decisions.yaml`.
Rerun unchanged, the code gives byte-identical 2030 and 2040 networks to the ones saved with it.

GridAware's 380/220 kV part is built on an older JAO release (for example 2,000 A on Rilland–Zandvliet, where JAO 2026 has
3,790 A), so from the code's 2035 network we take **only** the 150/110 kV lines and the transformers down to 150/110 kV.
Its 380/220 kV lines and its 380/220 kV IP2026 changes are left out; those come from our own 2035 decision table (section 2.4).

### 9.2 Steps (`pipeline/run_all_hv.sh`, about 5 minutes after `run_all.sh`)

| step | script | what it does |
|---|---|---|
| H1 | `hv_ip26/ip26_network_scenarios.py all`, `ip26_horizon_filter.py`, `ip26_final_network.py`, `ip26_excel_to_csv.py` | the code's steps 2, 3, 5, 6: GridAware + IP2026 projects for 2030, 2035, 2040 |
| A8 | `scripts/A8_build_patch_hv_150_110.py` (new) | the 150/110 kV part of the 2035 network as a patch: buses, lines, transformers |
| A5 | `scripts/A5_apply_patches.py` | 2035 workbook + this patch → `v29-vvltr2-2035-tennet-tlb3-rt4k-hv` |
| A7, B1–B5, C1–C2 | as in `run_all.sh` | SR2025 nodes, reduction, TTCs, border-tie correction (Belgian ties) |

What A8 does:
- **buses:** every 150/110 kV bus connected to the 380/220 kV grid through a transformer (329: named `HV-<station>_<kV>`, e.g.
  `HV-DIEMEN_150`), not kept as nodes, so the reduction eliminates them;
- **lines:** every 150/110 kV line and cable between them (632). X and current as in the code's network; R = B = 0;
  MW = √3 × nominal kV × current (an assumption: JAO's convention has no rule for 150/110 kV);
- **transformers:** 30 (20 at 380/150, 1 at 380/110, 9 at 220/110). The 380/220 kV side is matched to our workbook bus of the same
  station (all 30 matched). X from the transformer's per-unit value; rating = its MVA;
- **left out** (`dropped.csv`): the 380/220 kV elements (165) and one piece of 150/110 kV grid with no transformer to 380/220 kV (2 lines).

The 150/110 kV lines **carry flow and can fail in the N-1 check, but do not set a TTC**: the rule of section 3.3 (380 kV and Dutch
220 kV lines of at least 1 km) is unchanged. One self-check had to be loosened: B4 recomputes the reduced network from the full
grid and now agrees to 3 × 10⁻⁶ instead of 10⁻⁶ (rounding with 330 more buses); `run_all_hv.sh` sets `REPRO_TOL=1e-5` for it.

### 9.3 Result

Network `reference_outputs/networks/hv_nodal_main` (before the tie correction: `hv_nodal_no_tie_fix`); branch-by-branch comparison
with the main network in `reference_outputs/hv_150_110/compare_with_and_without_hv.csv`.

| | without 150/110 kV (in use) | with 150/110 kV (first version) |
|---|---|---|
| nodes | 43 | 43 |
| branches | 64 | 212 (148 new) |
| Dutch internal branches present in both: TTC-based limit, with / without | | 0.89 to 1.15 (Meeden–Zwolle −11 %, Oudehaske–Zeyerveen +15 %) |
| their reactances, with / without | | 0.91 to 1.07 (the 150/110 kV grid runs in parallel) |
| Belgian tie factor | 0.826 | 0.833 |

The 148 new branches join SR2025 nodes that are connected only through the 150/110 kV grid (for example Hengelo–Meeden through
110 kV, Diemen–Vijfhuizen through 150 kV). Their limits are small (median 8 MW, largest 1,021 MW) because no 150/110 kV line may
set a TTC and these branches carry only a small share of any exchange. **In a Tulipa run such small limits can bind when several
exchanges add up: check this before using the network.**

### 9.4 What needs checking

1. **Missing transformers.** Six stations have a 380/220 kV bus and a 150/110 kV bus in the data but no transformer between them:
   Rilland 380/150, Ens 380/110 and 220/110, Meeden 380/110, Doetinchem 380/150 (GridAware links Doetinchem 380 to Langerak 150),
   Delesto 220/110 (`reference_outputs/hv_150_110/hv_150_110_2035/check_transformers.csv`). The new Tilburg 380 kV station has no transformer to 150 kV either.
   In reality most of these exist; without them the 150/110 kV grid is linked to the 380/220 kV grid at fewer points.
2. **GridAware's base year.** The code calls `full_network.csv` a 2030 network; some IP2026 projects are already in it and others
   not (its own report: of 28 projects due by 2030, 1 in, 18 partly, 9 not). Its 20 "modify existing branch" rows of 2030 are
   marked unclear in its README.
3. **150/110 kV ratings after reinforcement** are assumptions of the code (1,500 A at 150 kV, 1,000 A at 110 kV); TenneT does not
   publish them. The MW rule for 150/110 kV lines (√3 × nominal kV × A) is ours.
4. **Should 150/110 kV lines set TTCs?** Not in this version. Monitoring them would make many limits lower; TenneT monitors only
   380 kV in the flow-based market.
5. **The small limits of the 148 new branches** (9.3).
6. **Coordinates** of 30 buses (wind parks, DSO substations) are approximate (nearest connected bus); they are used for maps only.

### 9.5 When GridAware or TenneT's data change: how to rerun

1. Put the new files in `pipeline/hv_ip26/DATA/` with the same names: `full_network.csv` (GridAware), `IP26_line.xlsx`,
   `IP26_point.xlsx`, `stations_tennet_arcgis.csv`, `ip26_line_endpoints.csv` (TenneT; `hv_ip26/DATA_SOURCES.md` says how each was
   downloaded). Keep the old ones in a dated subfolder.
2. Check that `full_network.csv` still has the same columns (the code reads them by name; the first 21 columns are listed in
   `hv_ip26/README.md`) and that station codes still end in their voltage (`DIM150`).
3. Delete `pipeline/hv_ip26/output/`, `output_final/`, `output_final_csv/`, the patch `pipeline/inputs/patches/hv_150_110_2035/` and
   the workbook folders `pipeline/inputs/derived/jao_core_*-hv*`; then `bash run_all_hv.sh`. Python needs pandas, openpyxl and pyyaml.
4. Read `hv_150_110_2035/CHANGELOG.md`, `dropped.csv` and `check_transformers.csv`: new stations that are not in our workbook show up
   there. A 380/220 kV station that is new in GridAware must first exist in our workbook (section 5) or its transformer is dropped.
5. For another year, add it to `horizons` in both configs and change `2035` in `run_all_hv.sh` (variable `NET35`).
6. If a new GridAware release is also based on JAO 2026 at 380/220 kV, the split of 9.1 still holds; if the 380/220 kV station
   codes change, update `pipeline/inputs/patches/jao2026_nl/node_diff.csv` (GridAware station code → workbook bus), which A8 uses
   to match the transformers.

## Appendix A. Old script names → new names

The scripts in `pipeline/scripts/` are the scripts that built the networks in use, renamed by step and with a plain header. Their
code is the same, except where noted.

| new name | step | was (in `core_grid_dcopf/scripts/`) | code changes for the handover |
|---|---|---|---|
| `A1_build_patch_vierverlaten_transformer.py` | A1 | `14_build_patch_vierverlaten_tr.py` | none |
| `A2_build_patch_from_decisions.py` | A2 | new; replaces the lost `112_build_ip2026_2035_patches.py` | new script; gives byte-identical patch files for both 2035 rules |
| `A3_build_patch_tilburg_loopin.py` | A3 | `16_build_patch_tilburg_loopin.py` | none |
| `A4_build_patch_rating_4ka.py` | A4 | `25_build_patch_rating_4ka.py` | none |
| `A5_apply_patches.py` | A1–A4 | `17_apply_patches_modify_remove.py` (also replaces `13_apply_patches.py`) | none |
| `A6_split_germany.py` | A5 | `29_de2_split_workbook.py` | none |
| `A7_set_dutch_nodes.py` | A6 | `18_nodal_workbook_nodeset.py` | none |
| `B1_reduce.jl` | B1 | `01_reduce.jl` | none |
| `B2_network_nodal.py` | B2 | `02n3_sparse_network_nodal_hv_de2.py` (also replaces `02n2_…`) | script name written in the manifest |
| `B2_network_country.py` | B4 | `02_sparse_network.py` | script name written in the manifest |
| `B3_monitored_lines.py` | B2 | `03_monitored_set.py` | none |
| `B3_monitored_lines_nodal.py` | B2 | `03n2_monitored_set_nodal_nl220.py` | none |
| `B4_limits_n1_nodal.py` | B3 | `04n_limits_n1_nodal.py` | script name written in the manifest |
| `B4_limits_n1_country.py` | B4 | `04_limits_n1.py` | script name written in the manifest |
| `B5_limits_pst_margin_nodal.py` | B3 | `05n2_limits_pst_margin_nodal_gridref.py` | script name in the manifest, and the check of the B4 run's script name |
| `B5_limits_pst_margin_country.py` | B4 | `05b_limits_pst_margin_gridref.py` | script name written in the manifest |
| `C1_full_grid_border_check.py` | C1, C2 | `23d_full_grid_border_check_de2.py` (also replaces `23b_…`) | helper functions read from `lib_network.py` |
| `C2_tie_correction.py` | C1, C2 | `24c_tie_correction_variant_de2.py` (also replaces `24_…`, `24b_…`) | helper functions read from `lib_network.py`; mode `beonly` added (= `24b`, Belgian ties only) |
| `lib_n1_engine.py` | — | `lib_n1_engine.py` | none |
| `lib_network.py` | — | functions copied from `10n3_test_2025_nodal_injections_de2.py` and `22_nl_transfer_capacity_compare.py` | gathered in one file, code unchanged |
| `verify_against_reference.py` | check | new | |

Every script got a new header in plain words (what, why, reads, writes, usage, history); the earlier technical notes are kept
as comments below it. The scripts exactly as they were run are in `background_notes/original_scripts/`, with the driver that was
used to check them (`run_all_as_verified.sh`): run with those scripts, the package gave the same five networks too.


## Appendix B. Source files

| folder in `sources/` | what | from | date |
|---|---|---|---|
| `01_jao_core_static_grid_model_2026/` | JAO Core Static Grid Model (Excel), handbook, publication page | JAO publication tool | release March 2026, downloaded 5 Jun 2026 |
| `02_gridaware/full_network.csv` | full Dutch grid, all voltages | GridAware; same file the patches were built from (SHA-256 `6e0092…49c5`) | received Oct 2026 |
| `03_tennet_ip2026/` | Investeringsplan 2026 Net op land, annexes 4–6; IP26 line and point layers, station list | TenneT | 2026 |
| `04_tennet_tilburg_2022/` | Aanmeldingsnotitie m.e.r. hoogspanningsstation Tilburg | TenneT, via ruimtelijkeplannen.nl | 2 Feb 2022 |
| `05_acer_germany_split/` | ACER Decision 11/2022, annexes V and VI | ACER | 2022 |
| `06_sr2025_nodes/` | the 32 SR2025 nodes and their buses | SR2025 | Oct 2026 |
| `07_ip26_project_matching/` | code that matches the IP26 projects to the GridAware network, with 2030 and 2040 horizons | project team | Oct 2026 |

JAO's data may be used for analysis; check JAO's terms before passing it outside the project.
