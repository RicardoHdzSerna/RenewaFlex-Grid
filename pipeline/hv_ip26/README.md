> **Copy for the grid handover (3 Nov 2026).** The code is unchanged. One change in the configuration: `2035` added to `horizons`
> in `config_horizons.yaml` and `config_final_network.yaml`. The output folders are not included: `../run_all_hv.sh` makes them.
> How this code is used in the grid model: `../../HANDOVER.md` section 9.

# IP26 network edges – from TenneT IP2026 line projects to the final 2030 / 2040 networks

This package converts the line projects of TenneT's *Investeringsplan Net op land 2026* (IP2026, ArcGIS layer
`IP26_line`) into network edges in the format of the GridAware network file `full_network.csv` (edge list with from/to
station, R, X, B in Ω and per unit, rating and MVA), builds parameter scenarios and 2030 / 2040 horizons, and
finally derives the 2030 / 2040 networks as the GridAware network plus the IP26 changes.

## How to run (in this order)

All scripts read the data from the `DATA/` folder inside this folder (`NewLines_IP26/DATA/`) and take their settings from the YAML
config next to them. Run from the project folder:

1. *(optional)* **`python ip26_network_build.py`** – one base workbook with the IP26 edges (median values).
   → `output/IP26_line_network_edges.xlsx`. Not needed by the later steps.
2. **`python ip26_network_scenarios.py all`** – the IP26 edges for the six parameter scenarios (median, mean,
   q1, q3, template, median_oldline).
   → `output/IP26_line_network_edges_<scenario>.xlsx` (6 workbooks, live formulas) and
   `output/IP26_scenario_comparison.xlsx`.
3. **`python ip26_horizon_filter.py`** – removes Studie projects, keeps the lines in service by 2030 / 2040, keeps
   the columns up to `source`, and checks every edge against `DATA/full_network.csv` (`network_action`,
   `applies_to_listed_branches`, per-circuit values), applying the review decisions of `config_decisions.yaml`.
   → `output/horizons/IP26_line_network_edges_<scenario>_<2030|2040>.xlsx` (12 workbooks).
4. *(report)* **`python ip26_vs_full_network.py`** – which IP26 projects are already in GridAware's 2030 network
   (in / partly / not in). → `output/IP26_projects_vs_full_network.xlsx`. Not needed by steps 5–6.
5. **`python ip26_final_network.py`** – the final networks: `DATA/full_network.csv` + the IP26 changes of the
   step-3 horizon workbooks and `config_decisions.yaml` (lines split at new stations, upgrades combined in series
   on the existing branches, `manual:` copies never changed, new connections added), every change marked and logged.
   → `output_final/<scenario>/full_network_final_<scenario>_<2030|2040>.xlsx` (tabs `network`, `change_log`)
   and `output_final/IP26_final_network_summary.xlsx` (counts, checks, rules).
6. **`python ip26_excel_to_csv.py`** (last) – converts every workbook in `output_final/` to CSV.
   → `output_final_csv/<scenario>/full_network_final_<scenario>_<horizon>/network.csv` and `change_log.csv`
   (+ `output_final_csv/IP26_final_network_summary/Summary.csv`, `Rules.csv`).

The final network for a model run is `output_final_csv/<scenario>/full_network_final_<scenario>_<horizon>/network.csv`
(e.g. `median`, `2030`): GridAware's 21 columns first, in the same order, then the traceability columns.
The step numbers above are used throughout this README.

```
DATA/IP26_line.xlsx ─┐
DATA/full_network.csv┤
DATA/stations…, ends ├─► 1. ip26_network_build.py ──► output/IP26_line_network_edges.xlsx (optional, median)
DATA/IP26_point.xlsx ┘
                     └─► 2. ip26_network_scenarios.py ──► output/IP26_line_network_edges_<scenario>.xlsx (6×)
                                                │          output/IP26_scenario_comparison.xlsx
                                                ├─► 3. ip26_horizon_filter.py ──► output/horizons/…_<scenario>_<2030|2040>.xlsx (12×)
                                                │                                       │
                                                └─► 4. ip26_vs_full_network.py          │
                                                       output/IP26_projects_vs_full_network.xlsx
                                                                                        ▼
DATA/full_network.csv ─────────────────────────────► 5. ip26_final_network.py ──► output_final/<scenario>/full_network_final_<scenario>_<horizon>.xlsx
                                                                                   output_final/IP26_final_network_summary.xlsx
                                                                                        ▼
                                                     6. ip26_excel_to_csv.py ──► output_final_csv/<scenario>/<workbook>/<tab>.csv
```

Requirements: Python 3.9+, `pip install pandas openpyxl pyyaml`. No internet access is needed. Each script
accepts another config file as argument; all paths in the configs are relative to the config file
(`DATA/...`). To read the data from another folder (e.g. the repository's `DATA/`), change `input_folder` (steps 1, 2, 4),
`network_file` (step 3) and `base_network`, `stations_file`, `endpoints_file`, `points_file` (step 5).
Excel lock files (`~$…xlsx`, created while a workbook is open in Excel) are not part of the package, are
ignored by the scripts and are listed in `.gitignore`; delete any that remain in the repository.

---

## 0. Review status

Confirmed (checked in the generated files, all six scenarios):

- **Upgrades modify existing branches, they are not added as new edges.** Every lijnverzwaring, Verkabelen or
  replacement of a connection that exists in `full_network.csv` has `network_action = modify existing branch`;
  step 5 changes the listed branches (record_status `derived`) and adds no branch. In 2030 this covers 12 of
  the 13 lijnverzwaring rows and all 5 Verkabelen rows. An upgrade only becomes a new edge when the
  connection is not in the GridAware network (298 Almelo pocket: Hengelo Weideweg 110 is not a node there) or when it
  adds circuits (`new edge (extra circuits)`, 2040 only). See §4.6 and §4.8.
- **The horizon rule uses the last year of the range.** "2029-2030" counts as 2030 (`year_basis: end`,
  `inclusive: true` in `config_horizons.yaml`): a line is in the 2030 network when it is fully in service by 2030.
- **The √3 and template columns are removed** from the horizon workbooks and everything after them:
  "X model (Ω) = L·x′·√3/N", "X standard (Ω) = L·x′/N", "Peak capacity (MVA) = N·cap" and
  "Secure capacity (MW) = MVA·PF·RF" are dropped with all other columns after `source`, and their parameters
  (cap, PF, RF) and notes are removed from the Parameters and Notes tabs. The model value is `reactance_ohm`
  = L·x′/N (no √3). Only the scenario workbooks of step 2 still contain these columns, for reference.
- **Partial upgrades are combined in series** (§4.8): R, X, B = old per-km × unchanged length + new per-km ×
  upgraded length; rating = min(old, new); the upgraded length and its source are recorded, the result is
  marked `derived`. Length weighting is applied to **every** partial upgrade (no 70 % rule): 2030 15 IP26 rows
  (40 branches), 2040 27 rows (66 branches).

**Review of 16-10-2026 – how each point is resolved** (see §4.8 and `config_decisions.yaml`):

| # | Point | Resolution in the code |
|---|---|---|
| 1 | Don't change `manual:RLL380-ZVL380-G/-W` (copies) | `manual:` copies of a real circuit (11 in the GridAware file) are never listed or changed; they stay `base` and are marked in `manual_copy_of`. Other `manual:` lines (e.g. `manual:RBZ150-NMR150-W/Z`) are real circuits and are upgraded normally. Check: 0 copies changed. |
| 2 | Row 378 needs cable parameters (X must go down) | Verkabelen rows that IP26 marks as overhead use the scenario's cable r′, x′, b′ and rating (`verkabelen_uses_cable_parameters`). BSL-RLL380 G/O/P/Z (median): X 10.18 → 7.40 Ω, rating min(2,826, 1,481) = 1,481 A. |
| 3 | Row 302: one route | `route_choice`: via Nieuwe Meer (VHZ-NMR150 W/Z, manual:RBZ150-NMR150-W/Z); the direct VHZ-RBZ150 circuits are not changed. Direct route = one-line switch. |
| 4 | Leave out rows 375–377 (NDLS) | `exclude_rows: 375, 376, 377`: not added, Borssele–Rilland not split (split on hold, `enabled: false`); logged as "excluded for now". No NDLS bus in the final networks. |
| 5 | Length weighting for every partial upgrade, no 70 % threshold | `full_coverage_threshold: 1.0`: upgraded length = min(IP26 length, branch length) spread over the route. Note: rows whose IP26 trace is only slightly shorter than GridAware's branch are now partial and keep the old rating (min rule), e.g. 290/303 Rilland–Zandvliet (6.18 / 5.18 of 6.6 km) stay at 2,000 A. |
| 6 | Dead-end new stations AMH380, HGLW110, LGSP150, LRHS150 | Tab `New_stations` of the summary lists every new bus, its connections, IP26 project, congestion type and MIEK. The IP26 data holds **no** loads or generators: LGSP150 / LRHS150 are Liander (DSO) substations → load connections; HGLW110 (pocket Almelo) is a demand-congestion project (Afname); AMH380 (Amaliahaven 380 kV station, nMIEK) has no stated customer. MW values must come from GridAware / TenneT / the DSO. |
| 7 | Read from the repository's `DATA/`; sources of the extra files | The data stays in `NewLines_IP26/DATA/` (as agreed); every path is one config key, so pointing to the repository's `DATA/` is a config change only. URLs, download date and licence of the station layer and the line endpoints: `DATA_SOURCES.md`. (The 4 files in `contrib/` on the branch are to be removed in git; they are not part of this package.) |
| 8 | Change log: values of new edges and MVA | `change_log` has `final_length_m`, `final_resistance_ohm`, `final_reactance_ohm`, `final_susceptance_pu_total`, `final_max_current_a`, `final_sn_mva` for new edges, and `base_sn_mva` / `final_sn_mva` (plus base/final length) for changed branches. |
| 9 | Hold off PowerFactory import scripts | No PowerFactory scripts in this package. |

Earlier decisions that stay in place: 290 → circuit G and 303 → circuit W of Rilland–Zandvliet 380 (one row per
circuit, `circuit_assignment`); new-station rows that only reference a branch another row upgrades (e.g.
304/379, 306/398, 311/345 in 2040) do not change that branch (`applies_to_listed_branches`). Configs point to the
`NewLines_IP26/DATA/`; the template block is removed from the horizon Parameters tabs; CSVs are made for the final
outputs only.

**Open: the 20 unclear 2030 changes.** The 2030 horizon has 30 IP26 edges (27 projects): 10 new edges (new
stations or new connections; 375–377 excluded for now, so 7 are added) and 20 rows marked *modify existing
branch* (290 and 303 are the two circuits of one project). The modify rows are the unclear ones: the connection is in the GridAware network, but whether his branch
already carries the IP26 upgrade cannot be confirmed from the data. Step 5 applies them; to be checked with
GridAware / TenneT:

| OBJECTID | Project | Connection | Type | Year | Why unclear |
|---|---|---|---|---|---|
| 290 / 303 | A-1000664 | Rilland–Zandvliet 380 (circuit G / circuit W) | lijnverzwaring | 2025 | rating 2,000 A in full_network < 4,000 A target |
| 293 | A-1002793 | Woensdrecht–Bergen op Zoom 150 | lijnverzwaring | 2028 | 150 kV target rating not published (full_network 800 A) |
| 294 | A-1002854 | Geertruidenberg–Waalwijk 150 | lijnverzwaring | 2025 | 150 kV target rating not published (full_network 900 A) |
| 296 | A-1002813 | Boxmeer–Venray 150 | lijnverzwaring | 2029-2030 | 150 kV target rating not published (full_network 900 A) |
| 300 | A-1002032 | Best–Tilburg Noord 150 | lijnverzwaring | 2026 | target not published; new station Oirschot (OIR150) not in full_network |
| 301 | A-1002658 | Lutterade–Born–Maasbracht 150 | lijnverzwaring | 2028 | target not published; low-confidence match, direct GRTH-LUTT150 W/Z also exists |
| 302 | A-1003169 | Vijfhuizen–Nieuwe Meer–Rozenburg Zuid 150 | lijnverzwaring | 2026 | 150 kV target rating not published (full_network 800 A) |
| 316 | A-1002987 | Harculo 110 pocket (HCL–NVD) | lijnverzwaring | 2026 | 110 kV target rating not published (full_network 700 A) |
| 325 | A-1003333 | Diemen–Bijlmer Noord 150 | lijnverzwaring | 2027 | 150 kV target rating not published (full_network 800 A) |
| 343 | A-1003403 | Kattenberg–Dodewaard 150 | lijnverzwaring | 2029-2030 | 150 kV target rating not published (full_network 800 A) |
| 412 | A-1003053 | Oostelijk Friesland (BGM–OWD 110) | lijnverzwaring | 2029-2030 | 110 kV target rating not published (full_network 700 A) |
| 297 | A-1002952 | Driebergen–Veenendaal–Dodewaard 150 | Verkabelen | 2026 | still an overhead line in full_network |
| 329 | A-1003141 | Utrecht Lage Weide–Nieuwegein 150 | Verkabelen | 2029-2030 | still an overhead line in full_network |
| 333 | A-1003431 | Apeldoorn–Woudhuis 150 | Verkabelen | 2027 | still overhead; new station APZO150 not in full_network |
| 378 | A-1002896 | Borssele–Rilland 380 | Verkabelen | 2028 | still an overhead line in full_network |
| 443 | A-1003187 | Almelo Mosterdpot–Tusveld 110 | Verkabelen | 2029-2030 | still an overhead line in full_network |
| 324 | A-1002892 | Oostzaan 150 (HW–NDK) | nieuwe verbinding | 2028 | route exists directly, not yet looped in through OZN150 |
| 373 | A-1000343 | Merwedeweg 150 (ERP–TWG) | nieuwe verbinding | 2027 | new station MRWW150 not in full_network (loop-in) |
| 444 | A-1002654 | Velsen–Beverwijk–Oterleek 150 | stationsuitbreiding | 2026 | route and rating already in full_network ("in") – confirm only |

Source: `network_action`, `applies_to_listed_branches`, `action_note` in
`output/horizons/IP26_line_network_edges_<scenario>_2030.xlsx` and the `Lines` tab of
`output/IP26_projects_vs_full_network.xlsx`.

---

## 1. Folder layout

```
NewLines_IP26/
├── ip26_network_build.py        step 1: base builder (one parameter set, median) – optional
├── config_network.yaml          config of step 1 (also holds all station assignments)
├── ip26_network_scenarios.py    step 2: builder with parameter scenarios (SCENARIO switch)
├── config_scenarios.yaml        config of step 2 (= config_network.yaml + scenario sections)
├── ip26_horizon_filter.py       step 3: Studie removal, 2030 / 2040 horizons, network actions
├── config_horizons.yaml         config of step 3
├── ip26_vs_full_network.py      step 4: IP26 projects already in the GridAware network? (report)
├── config_vs_full_network.yaml  config of step 4
├── ip26_final_network.py        step 5: final 2030 / 2040 networks = the GridAware network + IP26 changes
├── config_final_network.yaml    config of step 5
├── config_decisions.yaml        review decisions on single rows (steps 3 and 5)
├── ip26_excel_to_csv.py         step 6: final workbooks -> CSV (also the formula evaluator used by step 5)
├── config_excel_to_csv.yaml     config of step 6
├── README.md                    this file
├── .gitignore                   Excel lock files, __pycache__
├── DATA/                        input data (never changed)
│   ├── IP26_line.xlsx                 TenneT IP2026 line export (167 rows)
│   ├── IP26_point.xlsx                TenneT IP2026 point export (366 project points, RD x/y)
│   ├── full_network.csv               GridAware's 2030 network: stations, lines, cables, transformers
│   ├── stations_tennet_arcgis.csv     TenneT station layer: 371 STATIONID, name, RD x/y (see DATA_SOURCES.md)
│   ├── ip26_line_endpoints.csv        first/last vertex of every path of every IP26 line, RD x/y (see DATA_SOURCES.md)
│   └── IP26_line_separate_sheet.xlsx  earlier workbook; its Parameters tab feeds the 'template' scenario
├── DATA_SOURCES.md              URL, download date and licence of the files in DATA/
├── output/                      intermediate results (steps 1–4)
│   ├── IP26_line_network_edges.xlsx                 step 1
│   ├── IP26_line_network_edges_<scenario>.xlsx      step 2 (median, mean, q1, q3, template, median_oldline)
│   ├── IP26_scenario_comparison.xlsx                step 2
│   ├── horizons/IP26_line_network_edges_<scenario>_<2030|2040>.xlsx   step 3
│   └── IP26_projects_vs_full_network.xlsx           step 4
├── output_final/                final results (step 5)
│   ├── <scenario>/full_network_final_<scenario>_<2030|2040>.xlsx      tabs network, change_log
│   └── IP26_final_network_summary.xlsx                                tabs Summary, New_stations, Rules
└── output_final_csv/            final results as CSV (step 6)
    ├── <scenario>/full_network_final_<scenario>_<2030|2040>/network.csv, change_log.csv
    └── IP26_final_network_summary/Summary.csv, New_stations.csv, Rules.csv
```

One scenario only in step 2: set `SCENARIO = "q3"` at the top of `ip26_network_scenarios.py`, or run
`python ip26_network_scenarios.py q3`.

---

## 2. Quick start

```bash
pip install pandas openpyxl pyyaml
python ip26_network_scenarios.py all   # step 2
python ip26_horizon_filter.py          # step 3
python ip26_vs_full_network.py         # step 4 (report)
python ip26_final_network.py           # step 5: final networks
python ip26_excel_to_csv.py            # step 6: final networks as CSV
```

What each step produces: see *How to run* at the top.

---

## 3. Input data (`DATA/`) and where it came from

| File | Source | Used for |
|---|---|---|
| `IP26_line.xlsx` | TenneT IP2026 ArcGIS layer `TenneT_investeringsplan_2026_projecten/FeatureServer/1` (export) | the 167 line projects: voltage, over/underground, phase, year, `Shape__Length` |
| `IP26_point.xlsx` | same service, layer 0 (export, 366 points) | coordinates and names of new stations; project number link (`nummer` = `n_nummer`) |
| `full_network.csv` | GridAware's 2030 network model (393 nodes; 767 lines/cables, 38 transformers) | station IDs and names, old line values, per-km parameter statistics, circuit counts |
| `stations_tennet_arcgis.csv` | TenneT ArcGIS `TenneT_Assets_Hoogspanning/FeatureServer/5` (station polygons; STATIONID, OBJECTOMSCHRIJVING, centroid in RD New / EPSG:28992) | station names and locations not in `full_network.csv`; snapping |
| `ip26_line_endpoints.csv` | geometry of layer `IP26_line` (paths generalised, first and last vertex of each path, RD New) | which stations a line connects |
| `IP26_line_separate_sheet.xlsx` | earlier project workbook | `template` scenario (x′ 0.265 Ω/km, ratings 4,000/1,500/1,000 A, cap, PF, RF) |

Verification sources (used while building the config, not read by the code):
TenneT conductor layers `TenneT_Assets_Hoogspanning/FeatureServer/2` (overhead) and `/3` (cable),
field `NETSCHAKELID` (circuit ID, same naming as `full_network.csv`), queried around the line ends;
TenneT grid maps June 2026 (tennet.eu – only the main 380/220 kV and cross-border stations are labelled).

---

## 4. Method

### 4.1 Station matching (from / to stations of every line)

1. **Geometry.** Every path end of an IP26 line is compared with all stations of the same voltage
   (ArcGIS station layer, stations of `full_network.csv`, new-station points of `IP26_point.xlsx`).
   Path ends used once are the line terminals.
2. **Project name.** The candidates are checked against `n_projectnaam` (e.g. "Borssele-Rilland 380 kV").
3. **TenneT circuit IDs.** For partial sections, loop-ins and doubtful ends, the TenneT conductor layers
   were queried around the line end; the circuits found (e.g. `GT-WW150 W`) are quoted in the note.
4. **Project points.** `IP26_point.xlsx` gives the location of new stations and, via the project number,
   the point belonging to each line.
5. The result is fixed per OBJECTID in `assignments` of the config (from, to, via, confidence, note).
   Lines without an entry are matched automatically (nearest station of the same kV within 1.5 km).

**Name rule** (column `from_name_source` / `to_name_source`):
1. old line file `full_network.csv` (exact name, e.g. "Station Rilland 380", "Zandvliet (BE)");
2. TenneT ArcGIS map (OBJECTOMSCHRIJVING);
3. new station: name from the IP2026 point file; customer substation: name from the project name
   (e.g. "Liander Havenstad 150"); otherwise assumed (config).

New stations get an ID in the same style (`TLB380`, `ZBE150`, `HST380` …), listed in `extra_stations`.

**Confidence** (`match_confidence`): *high* = both stations certain; *medium* = loop-in into an existing
line (far station = one end of that line) or name and geometry differ; *low* = indicative trace,
ambiguous corridor or assumed station.

Result: 213 stations used (152 named from `full_network.csv`, 1 from the ArcGIS map, 41 from the IP2026
point file, 14 customer substations, 5 assumed); 141 high, 16 medium, 6 low, 4 empty rows (458–461).
**Approximate stations (to be confirmed).** GNMS110 (Groningen Meerstad 110, line 374) and MDM380
(Middenmeer 380, line 345) are not in any source and are placed at the free end of their IP26 line, with
the name taken from the project. Their locations are approximate (possibly several km off) and accepted for
now; they should be confirmed from the IP2026 project descriptions **A-1003051** (Vierverlaten–Groningen
Meerstad) and **A-1003017** (Noord-Holland Noord 380 kV).
Other uncertain stations: Groningen Meerstad 110 and Middenmeer 380 (name and location assumed),
DONN 110 near Wijster (name assumed); Born 150, Zandvliet, Van Eyck, Liander Osdorp, Liander Weesp
Noord (approximate location only). Low-confidence lines: 301, 339, 345, 419, 420, 450.

### 4.2 Number of circuits per edge (`n_circuits`)

One edge represents N parallel circuits (as `parallel` in pandapower): R/N, X/N, B·N, I·N.
Rules in order (column `n_circuits_basis` shows the rule used):
1. override per OBJECTID (config `circuits.override`);
2. project name: "3e circuit" = 1, "3e en 4e circuit" = 2, "N circuits" = N;
3. existing route (lijnverzwaring, Verkabelen, bestaande verbinding): number of circuits of that route in
   `full_network.csv` (circuit letters W, Z, G …; 'Nvt' edges not counted);
4. default 2 for new connections (TenneT builds double circuit; IP2026 Table 8.3).

IP26 draws some projects several times with identical geometry (e.g. Diemen–Lelystad 3×,
Vierverlaten–Hessenweg–Ens 4×). The first feature is used; copies are kept with
`include_in_network = no` and `duplicate_of_OBJECTID`. A project drawn as k *different* features between
the same stations gets N/k circuits per feature (e.g. Rilland–Zandvliet 290/303: 1 each).
Result: 141 rows with 2 circuits, 22 with 1, 2 with 3, 2 with 4; 22 duplicate features.

### 4.3 Electrical values

| Column | Formula | Reference (equation) |
|---|---|---|
| `edge_type` | bovengronds → line, ondergronds → cable | input `bovengronds_ondergrond` |
| `length_m` | `Shape__Length` (indicative IP26 trace) | input |
| `resistance_ohm` | R = r′ · L/1000 / N | series impedance Z = (r′ + jx′)·length/parallel (pandapower line model) |
| `reactance_ohm` | X = x′ · L/1000 / N | idem |
| `resistance_pu` | R / Z_base, Z_base = kV² / S_base | Z_N = V_N²/S_N, z = Z/Z_N (per-unit system) |
| `reactance_pu` | X / Z_base | idem |
| `susceptance_pu_total` | b′·10⁻⁶ · L/1000 · N · Z_base | Y = (g + j2πfC′)·length·parallel, y = Y·Z_N (g = 0) |
| `susceptance_pu_half` | total / 2 | nominal-π model, Y/2 at each end |
| `max_current_a` | rating · N | pandapower `max_i_ka · parallel` |
| `sn_mva` | √3 · kV · I / 1000 | three-phase apparent power S = √3·V·I |

S_base = 100 MVA (as in `full_network.csv`; checked on all 767 lines/cables). r′, x′, b′ and rating come
from the Parameters tab (per kV and line/cable, depending on the scenario). Rows of type lijnverzwaring
use the rating after reinforcement: 380/220 kV 4,000 A (IP2026 §7.4), 150 kV 1,500 A and 110 kV 1,000 A
(assumptions). References: pandapower documentation (Line element); Grainger & Stevenson, *Power System
Analysis* (ch. 2, 4–6); Glover, Overbye & Sarma, *Power System Analysis and Design* (ch. 2–3); Kundur,
*Power System Stability and Control* (ch. 6); CIGRE TB 601; IEC 60287.

**Template columns** (last four columns, from the original `IP26_line_separate_sheet`):
`X model (Ω) = L·x′·√3/N`, `X standard (Ω) = L·x′/N` (= `reactance_ohm`, same x′),
`Peak capacity (MVA) = N·cap` (cap = 1000 MVA for 380 kV; other voltages: `sn_mva`),
`Secure capacity (MW) = MVA·PF·RF` (PF 0.95, RF 1). L = Shape__Length/1000 km.

### 4.4 Old line values (lijnverzwaring tab)

For each lijnverzwaring row the existing line is looked up in `full_network.csv`: the direct edge between
from and to station, otherwise the chain through the via stations, otherwise `old_chain` from the config.
Shown per circuit: max current, MVA, number of circuits, R, X, B (µS), length, edge IDs. DLR is not in
`full_network.csv` (empty). Duplicate circuits in the old file (e.g. `branch:RLL-ZVL380 W` and
`branch:manual:RLL380-ZVL380-W`) are counted once. Found for 42 of 49 lijnverzwaring lines; the other
7 go to new stations. These values are used in the calculation only in scenario `median_oldline`.

### 4.5 Parameter scenarios (step 2)

| Scenario | r′, x′, b′ | Rating |
|---|---|---|
| `median` | median of `full_network.csv` per kV and line/cable | median; 380/220 kV lines 4,000 A |
| `mean` | average | average; 380/220 kV lines 4,000 A |
| `q1` | first quartile (25th percentile) | Q1; 380/220 kV lines 4,000 A |
| `q3` | third quartile (75th percentile) | Q3; 380/220 kV lines 4,000 A |
| `template` | x′ from `IP26_line_separate_sheet.xlsx` (0.265 Ω/km); r′, b′ = median | 4,000 / 1,500 / 1,000 A from the template |
| `median_oldline` | median; lijnverzwaring rows: old line R/length, X/length, B/length × IP26 length | as median |

Statistics are computed from `full_network.csv` at run time (r′ = R/length, x′ = X/length,
b′ = B_total/length per edge). At 150/110 kV most edges carry standard values, so median, mean and the
quartiles are almost equal; the spread is at 380/220 kV. Total X of all edges: median 306 Ω, mean 306,
q1 298, q3 307, template 356, median_oldline 323.

### 4.6 Horizons 2030 / 2040 (step 3)

Per scenario workbook:
1. projects in phase `Studie` removed (76 rows), rows without year removed (458–461);
2. line kept when its commissioning year ≤ horizon; for a range ("2029-2030") the last year is used
   (`year_basis: end`, configurable to `start`);
3. duplicate features (`include_in_network = no`) removed;
4. data tabs reduced to the columns `edge_id` … `source`; the Parameters and Notes tabs are cleaned of the
   parameters and notes of the dropped columns (template block cap / PF / RF, old line values);
5. every kept edge is checked against the GridAware network (`full_network.csv`) and gets network-action
   columns after `source` (see below).

Result (same for all scenarios): 2030 → 30 edges, 2040 → 70 edges.

**Network action (no doubled corridors).** Reinforcements of connections that already exist in GridAware's
network must not be added as extra edges; they are changes to the existing branches. Per edge:

| `network_action` | Rule | What to do in GridAware's model |
|---|---|---|
| modify existing branch | route between the stations exists in `full_network.csv` (direct, through the via stations, or `old_chain`) and the project adds no circuits (lijnverzwaring, Verkabelen, replacement, …) | do **not** add the edge; give the listed `full_network_edge_ids` the per-circuit rating and parameters (`per_circuit_*`); partial sections and loop-ins of new stations are explained in `action_note` |
| new edge (extra circuits) | route exists, project adds circuits ("3e circuit", "3e en 4e circuit") and `full_network.csv` has fewer | add the edge (it holds only the added circuits); keep the existing branches |
| new edge (new connection) | a station is not in `full_network.csv` or there is no route | add the edge; for loop-ins the existing branch to split is named in `action_note` |
| already in full_network | the added circuits already exist | no change |

In short:
- **Modify existing branch** – the connection already exists in the GridAware network (`full_network.csv`), directly
  or through intermediate stations. The IP26 project only changes it (new conductors / lijnverzwaring,
  undergrounding / Verkabelen, replacement). Do **not** add the IP26 edge, because that would put a second
  copy of the corridor next to the existing one. Instead, update the branches listed in `full_network_edge_ids`
  with the new per-circuit values (rating, R, X, B). Example: RLL–ZVL380 → update `branch:RLL-ZVL380 G/W`.
- **New edge (new connection)** – the connection does not exist in the GridAware network yet: one of its stations is
  missing there (a new station such as Amaliahaven or Hengelo Weideweg), or there is no branch between the
  two stations. **Add** the IP26 edge as a new branch. When a new station is inserted into an existing line
  (loop-in), `action_note` names the existing branch to split at that station.
- **New edge (extra circuits)** – the route exists, but the project adds circuits the GridAware network does not have
  yet (e.g. a 3rd and 4th circuit). Add the edge for those extra circuits only and keep the existing branches.

Extra columns: `applies_to_listed_branches`, `branches_also_listed_by`, `full_network_edge_ids`, `full_network_circuits`, `full_network_max_current_a`,
`full_network_length_km`, `n_circuits`, `per_circuit_resistance_ohm`, `per_circuit_reactance_ohm`,
`per_circuit_susceptance_pu_total`, `per_circuit_max_current_a` (live formulas = edge value × or ÷ N),
`action_note`.
Result: 2030 → 20 modify existing branch, 10 new connections (375–377 marked "excluded for now"); the 13
lijnverzwaring rows of 2030 are 12 × modify (e.g. 290 → `branch:RLL-ZVL380 G`, 303 → `branch:RLL-ZVL380 W`) and
1 new edge (Almelo pocket: Hengelo Weideweg 110 is not a node of `full_network.csv`). 2040 → 36 modify,
3 extra circuits, 31 new connections (375–377 excluded for now). Formulas stay live: references to
removed columns are replaced by their content, so they only point to kept columns and the Parameters tab.

Checks against the GridAware file (all 12 horizon files, identical network actions in every scenario):
- every listed `full_network_edge_ids` exists in `full_network.csv`; no "new connection" row has a direct
  edge between its stations; every direct edge of a modify/extra-circuit row is listed;
- `full_network.csv` holds 11 circuits a second time as a `manual:` copy (same stations, same circuit letter,
  identical values, e.g. `branch:RLL-ZVL380 G` and `branch:manual:RLL380-ZVL380-G`). Copies are not listed and
  never changed (review item f); `action_note` names them. `manual:` branches without a real counterpart
  (e.g. `manual:RBZ150-NMR150-W`) are real circuits. A circuit that appears twice without `manual:`
  (Druten–Tiel row 428, `branch:TL-ZBM150 W` = `DRT-ZBM-TL150 W:seg2`) is listed and changed in both rows;
- **Duplicate references** – some branches are named by two rows. Column `applies_to_listed_branches` marks
  which row applies the change, so each change is applied once (step 5 only applies rows with `yes`);
  `branches_also_listed_by` names the other rows:

  | Rows | Situation | Marking |
  |---|---|---|
  | 290 / 303 Rilland–Zandvliet 380 | one project (A-1000664), two circuits, one row per circuit | `circuit_assignment`: 290 lists and changes `RLL-ZVL380 G`, 303 `RLL-ZVL380 W`; both `yes` |
  | 375 / 378 Borssele–Rilland 380 | 375 = new station NDLS380 cut into the line; 378 = cabling of 19.8 km | 375 (and 376/377) `no - excluded for now` (`exclude_rows`, review point 4); 378 `yes`, applied to the unsplit BSL-RLL380. With the split enabled, 375 becomes `split existing branch` and step 5 splits first, then places the cable |
  | 302 Vijfhuizen–Rozenburg Zuid 150 | listed branches of two alternative routes | `route_choice`: only VHZ–NMR150 W/Z and manual:RBZ150-NMR150-W/Z are listed (the direct VHZ–RBZ150 P and manual:RBZ150-VHZ150-W/Z are not changed) |
  | 2040: 304/379, 306/398, 311/345 | upgrade of a route + new station looped into it | upgrade `yes`; new-station row `reference only` |
  | 2040: 348 / 349 Maasbracht–Eindhoven | 3rd and 4th circuit, one feature each, both list the existing circuits W/Z | both `reference only` for W/Z; each is added as its own new edge |

  A general rule remains for other rows of one project listing the same branches: the longest row applies, the
  others are marked `no - duplicate of …` (does not occur in the current data). Rows of *different* projects that
  change the same branch are both `yes` and combined in series in step 5.

### 4.7 IP26 projects already in GridAware's 2030 network (step 4)

GridAware asked which IP26 projects are already in his 2030 network (`full_network.csv`). For every IP26 line
(duplicate features skipped) the route between its from and to station is looked up in `full_network.csv`
(lines and cables): directly, through the via stations, or through `old_chain` from the config.

| Status | Rule |
|---|---|
| **not in** | a from/to station is not in `full_network.csv` (new station), or there is no edge between the stations |
| **partly** | the route exists but not everything the project delivers: fewer circuits than "3e circuit" (3) / "3e en 4e circuit" (4); lijnverzwaring with a rating below 4,000 A at 380/220 kV (IP2026 §7.4); lijnverzwaring at 150/110 kV, where the upgrade cannot be verified (no published target rating); Verkabelen where the route is still an overhead line; a new intermediate station that is not in `full_network.csv`; or only part of a multi-station route |
| **in** | the route exists with the circuits, rating or cable type the project delivers |

A project (`n_nummer`) is *in* when all its lines are in, *not in* when none is, otherwise *partly*.
Column `expected_by_network_year` (commissioning end year ≤ 2030) and `check` flag projects due by 2030
that are not (fully) in the network, and projects in the network that come later.

Result (136 projects): 12 in, 62 partly, 62 not in. Of the 28 projects due by 2030, 1 is in, 18 partly,
9 not in (mostly new stations such as Amaliahaven, Zeeburgereiland, Nieuwdorp Liechtensteinweg).
Main reasons for *partly*: 150/110 kV upgrade not verifiable (22 lines), 380/220 kV rating below 4 kA (13),
circuits missing (10), route still overhead for cabling projects (10), new intermediate station (6).

**GridAware's topology map.** GridAware's GridAware topology map (HTML, `DATA/GridAware_topology_map/` in the
repository) gives RD coordinates for his 392 nodes. Once its node list is exported to a CSV
(`node_id, x_rd, y_rd`) and set as `juan_nodes_file`, step 4 adds GridAware's coordinates and the distance to
the station location used here to tab `Stations`. (The HTML itself is not in this package yet.)

### 4.8 Final 2030 / 2040 networks (step 5)

The 2030 and 2040 networks are a **derived layer**: GridAware's base network (`DATA/full_network.csv`, never
changed on disk) plus the IP26 changes of the horizon workbook of the scenario, applied by code. Every
changed or added record is marked (`record_status`) and traceable (`ip26_*` columns, `change_log` tab).

| Horizon row | What step 5 does | `record_status` |
|---|---|---|
| modify existing branch, `applies_to_listed_branches = yes` | changes the parameters of every listed branch (real circuits only, never a `manual:` copy); **no new branch** | `derived` |
| split existing branch | replaces each listed circuit by two branches at the new station (only when a split in `config_decisions.yaml` is enabled; 375 is on hold) | `derived (split)` |
| row in `exclude_rows` (375, 376, 377) | nothing; logged as "excluded for now" | – |
| modify existing branch, `no - duplicate of …` | nothing (the change is made by the row named there); logged | – |
| `manual:` copy of a real circuit | never changed; `manual_copy_of` names the real circuit | `base` |
| new edge (new connection) / new edge (extra circuits) | adds the IP26 edge (`add_new_edges: true`); listed reference branches are not changed | `new (IP26)` |
| already in full_network | no change; logged | – |
| every other branch of `full_network.csv` | copied unchanged (bit-identical values) | `base` |

**Series combination (per branch, per circuit).** Every changed branch is a chain of sections in series
(column `sections`, JSON: length, r′, x′, b′, rating, source). GridAware's branch is one section with his per-km values
(value / length L); an upgrade replaces the upgraded length of that old section by a section with the new per-km
values (IP26 per-circuit value / IP26 length, or the scenario's cable parameters for a Verkabelen row that IP26
marks as overhead, `verkabelen_uses_cable_parameters`); a split adds the loop-in section. With one upgrade:

    R  = r′_old · (L − L_up) + r′_new · L_up
    X  = x′_old · (L − L_up) + x′_new · L_up
    B  = b′_old · (L − L_up) + b′_new · L_up          (susceptance_pu_total, b′ in pu/km; half = B / 2)
    rating = min(I_old, I_new)                        (partial upgrade; fully upgraded branch: I_new)
    R_pu = R / Zbase, X_pu = X / Zbase, Zbase = kV² / 100 MVA;  sn_mva = GridAware's sn_mva · rating / I_old
    length_m stays GridAware's L

The sections are in series, so their impedances add (and their charging adds): this equals a length-weighted
average of the per-km values times L. The rating is not weighted: the weakest section limits the branch.
A fully upgraded branch gets the IP26 type (e.g. a cabled line becomes `cable`, `type_on_full_coverage: ip26`);
a partially upgraded branch keeps GridAware's type and lists its sections in `section_types`
(e.g. `line 12.421 km (unchanged) + cable 5.179 km (IP26 294)`).

**Upgraded length L_up and its source.** The IP26 length (`length_m` of the IP26 edge = IP2026 line geometry)
is compared with the listed route in `full_network.csv`: a direct branch between the IP26 stations is its
own route; the branches of a multi-station route (e.g. LUTT–BORN–MBT) form one route whose length is the sum
of the sections. `L_up = L · min(1, L_IP26 / L_route)` – spread in proportion to the branch lengths, because the
location of the upgraded part is not in the data. Every partial upgrade is length-weighted
(`full_coverage_threshold: 1.0`, review point 5); with a value below 1 (e.g. 0.7), a ratio at or above it would
count as a full upgrade. When `L_IP26 / L_route ≥ full_coverage_threshold` the
whole branch counts as upgraded (the difference is then only IP26 geometry vs GridAware's length). The IP26 row, the
lengths, the ratio and the rule used are written per branch in `upgraded_length_source`.

**Result (identical counts in all six scenarios):**

| Horizon | IP26 rows applied (modify) | derived branches | of which partial | new IP26 edges | base (unchanged) | total edges | buses (new) |
|---|---|---|---|---|---|---|---|
| 2030 | 20 | 53 | 40 (from 15 IP26 rows) | 7 | 752 | 812 | 398 (5) |
| 2040 | 36 | 90 | 66 (from 27 IP26 rows) | 31 | 715 | 836 | 417 (24) |

Borssele–Rilland 380 (378, per circuit G, O, P, Z, median): 17.373 km old line + 19.827 km cable →
X = 0.27375·17.373 + 0.1335·19.827 = 7.40 Ω (was 10.18 Ω), rating min(2,826, 1,481) = 1,481 A.
With the split enabled (on hold) the cable lies on NDLS–RLL380 only (§4.9).

**Columns of the `network` tab / `network.csv`:** GridAware's 21 columns in the same order, then
`record_status`, `ip26_objectids`, `ip26_n_nummer`, `ip26_project`, `ip26_werkzaamheden`, `ip26_in_service`,
`network_action`, `coverage` (full / partial / new edge), `branch_length_m`, `upgraded_length_m`,
`split_from`, `manual_copy_of`, `unchanged_length_m`, `upgraded_share`, `upgraded_length_source`, `section_types`,
`sections` (JSON), `base_type`, `base_length_m`,
`base_resistance_ohm`, `base_reactance_ohm`, `base_susceptance_pu_total`, `base_max_current_a`, `base_sn_mva`
(GridAware's values before the change), `new_resistance_ohm_per_km`, `new_reactance_ohm_per_km`,
`new_susceptance_pu_per_km`, `new_max_current_a` (IP26 per circuit), `change_note`.
The `change_log` tab has one row per IP26 row × branch: modified (base and final length, R, X, B, rating and
MVA), added as new edge (its length, R, X, B, rating and MVA), or not applied (excluded for now / manual copy /
duplicate / reference only / already in full_network) with the reason. The summary tab `New_stations` lists every
new bus with its connections, IP26 project, congestion type (Afname = demand, Productie = generation) and MIEK,
and flags buses with only one connection; loads and generators are not in the IP26 data.

**Checks (tab `Summary`, every scenario and horizon):** untouched rows identical to `full_network.csv` (0 differences,
values bit-identical, also in the CSV); no base edge missing except the split originals; 0 `manual:` copies
changed (11 marked); the changed branches are exactly the branches of the applying rows; R, X, B, R_pu, B/2,
rating and length of every derived branch equal to the sum / minimum over its sections, and the old-line sections
carry GridAware's per-km values; for the split line: old line + upgraded length = original length; islands listed. In
addition all 858 derived branch rows (6 scenarios × 2 horizons) were recomputed from the GridAware file and the
per-km values and ratings of the scenario workbooks: max relative difference 3e-16.
Spot check by hand: GT–WW150 W, 5.18 of 17.6 km upgraded, rating 900 A = min(900, 1,500).

---

### 4.9 Review decisions (`config_decisions.yaml`)

Row-specific decisions are kept in one file, read by step 3 (which branches a row lists / applies to) and
step 5 (how the change is applied). Change a decision there and rerun steps 3, 5 and 6.

| Key | Review item | Current decision |
|---|---|---|
| `circuit_assignment` | c) 290 / 303 | 290 → circuit G, 303 → circuit W |
| `route_choice` | e) 302 | route VHZ150–NMR150–RBZ150 (project name); alternative `[VHZ150, RBZ150]` – to confirm |
| `manual_copies` | f) | `never_change` |
| `exclude_rows` | review point 4 | 375, 376, 377 (NDLS) left out for now |
| `splits` | d) 375 | on hold (`enabled: false`). When enabled: BSL380–RLL380 G/O/P/Z cut at NDLS380; tap position `auto` = IP26 line end of 375 projected on the line (1.672 km from Borssele); loop-in length = length of 375 (1.168 km) |
| `section_location` | d) 378 | used with the split only: `auto` = from the IP26 geometry of 378 (km 17.4–37.2 from Borssele → all on NDLS–RLL380) |
| `verkabelen_uses_cable_parameters` | d) "cable has different R, X, B and rating" | true: Verkabelen rows that IP26 marks as overhead (378, 346) use the scenario's cable parameters |

---

## 5. Output workbooks

### Steps 1 and 2: `IP26_line_network_edges[_<scenario>].xlsx`

| Tab | Content |
|---|---|
| `1` | all 167 rows |
| `Parameters` | S_base; r′, x′, b′, rating per kV and line/cable (scenario); rating after reinforcement; template parameters (cap, PF, RF); formula list |
| `(blank)`, `klantaansluiting`, `lijnverzwaring`, `nieuwe verbinding`, `stationsuitbreiding`, `Verkabelen`, `vervangen station` | one tab per `n_werkzaamheden_ip` (lijnverzwaring with two header rows and the old-line block) |
| `Stations` | every station used: ID, node, name, kV, RD x/y, name source, origin, IP26 point, in `full_network.csv`, used by OBJECTIDs |
| `IP26_new_stations` | all 86 new-station points of `IP26_point.xlsx`: station ID used, connected by an IP26 line or not, nearest station |
| `Station_match` | per row: assigned stations, distance to the line ends, nearest stations, project point, confidence, note |
| `Notes` | method, assumptions, run summary |

Column order of the data tabs:
1. `edge_id type from_node_id from_station_id from_station_name from_voltage_kv to_node_id to_station_id to_station_name to_voltage_kv resistance_ohm reactance_ohm resistance_pu reactance_pu susceptance_pu_half susceptance_pu_total edge_type length_m max_current_a sn_mva source` (format of `full_network.csv`);
2. `OBJECTID bovengronds_ondergrond bestaand_nieuw provincie n_nummer n_projectnaam n_projectfase_ip n_werkzaamheden_ip n_miek trace N_ibn_jaar_ip2026`;
3. lijnverzwaring only: old line values (Voltage, max current, MVA, matched circuits, DLRmin/max, R, X, B, length, comment);
4. `kv Shape__Length n_circuits n_circuits_basis include_in_network duplicate_of_OBJECTID via_station_ids from_name_source to_name_source match_confidence match_note`;
5. step 2 only: `parameter_scenario r_ohm_per_km_used x_ohm_per_km_used b_uS_per_km_used rating_a_used parameter_basis`;
6. the four template columns.

`edge_id` = `branch:<FROM>-<TO><kV> IP26-<OBJECTID>` (station codes without voltage, as in `full_network.csv`);
`node_id` = `node:<STATIONID>`. With `output_mode: formulas` all electrical columns are live Excel formulas
(green cells) referencing the Parameters tab; with `values` the numbers are written.

### Step 2 extra: `IP26_scenario_comparison.xlsx`
Tabs per quantity (reactance, resistance, susceptance, current, MVA): one row per OBJECTID, one column per
scenario; tab `totals` with the sums over the edges with `include_in_network = yes`.

### Step 3: `horizons/IP26_line_network_edges_<scenario>_<2030|2040>.xlsx`
Same tabs; data tabs with the 21 network columns and the kept edges, followed by the network-action columns
(`network_action`, `applies_to_listed_branches`, `branches_also_listed_by`, `full_network_edge_ids`, …,
`per_circuit_*`, `action_note`); `Parameters` without the template block; `Notes` without the notes on dropped
columns; `Station_match` filtered; new tab `Horizon_filter` with every row, phase, year, year used, kept or
reason for removal.

### Step 4: `IP26_projects_vs_full_network.xlsx`
| Tab | Content |
|---|---|
| `Projects` | one row per IP26 project: status (in / partly / not in, coloured), lines, counts, reasons, expected by 2030, check |
| `Lines` | one row per IP26 line: stations, in `full_network.csv` yes/no, route found, `full_network` edges, circuits, type, rating, what the project requires, upgrade check, status, reason |
| `Stations` | every IP26 station: in `full_network.csv` or not, name source, location (+ GridAware's coordinates when given) |
| `Rules` | the classification rules |

### Step 5: `output_final/`
| File | Content |
|---|---|
| `<scenario>/full_network_final_<scenario>_<2030\|2040>.xlsx` | tab `network` (final network, §4.8), tab `change_log` (one row per IP26 row × branch) |
| `IP26_final_network_summary.xlsx` | tab `Summary` (counts and checks per scenario and horizon), tab `Rules` |

Values only (no formulas), written at full double precision.

### Step 6: `output_final_csv/`
One CSV per tab of every workbook in `output_final/`, same subfolders:
`output_final_csv/<scenario>/full_network_final_<scenario>_<horizon>/network.csv` and `change_log.csv`,
`output_final_csv/IP26_final_network_summary/Summary.csv` and `Rules.csv` (or `<workbook>__<tab>.csv` with
`layout: flat`). Numbers are written with full precision (shortest exact representation); empty rows are dropped.

---

## 6. Code description

### 6.1 `ip26_network_build.py` (step 1)

| Part | Function(s) | What it does |
|---|---|---|
| Config | `load_config` | reads the YAML, resolves folders relative to the config |
| Helpers | `kv_number`, `station_kv`, `station_code`, `clean`, `edge_type_of` | "380kV" → 380; ID → voltage; ID → code for edge_id; NaN/NumPy clean-up; bovengronds/ondergronds → line/cable |
| Stations | `StationRegistry` | merges ArcGIS stations, `full_network.csv` stations and `extra_stations`; applies the name rule; coordinates of new stations from `IP26_point.xlsx` (`point:` key) |
| Geometry | `path_ends`, `terminals`, `nearest`, `dist_to_line`, `project_points` | line ends per OBJECTID; dangling ends = terminals; nearest station; distance station–line; project point with the same number |
| Old network | `build_edge_index`, `circuit_tag`, `old_values`, `find_old` | index of lines/cables by station pair; circuit letter of an edge ID; series values over a chain; old line lookup (direct → via → old_chain) |
| Circuits | `fn_circuit_tags`, `determine_circuits` | circuit letters of the existing route; N per row, duplicates and splitting (§4.2) |
| Calculation | `line_type_rows`, `reinforced_rows`, `compute` | Parameters row per kV/type; reinforced rating rows; one record per IP26 line with stations, edge_id, R, X, B, rating, MVA, template columns |
| Workbook | `write_parameters`, `template_rows`, `columns_for`, `write_data_sheet`, `write_table`, `write_notes` | Parameters tab; column order; data tabs with formulas and formats; tables; notes |
| Main | `main` | pass 1: stations per row (config or automatic); pass 2: circuits, values, old values; writes all tabs |

### 6.2 `ip26_network_scenarios.py` (step 2)

Copy of step 1 with scenario support. Additional / changed parts:

| Part | Function | What it does |
|---|---|---|
| Switch | `SCENARIO`, `CONFIG_FILE` (top of file) | scenario to run (`median`, `mean`, `q1`, `q3`, `template`, `median_oldline`, `all`) |
| Statistics | `network_statistics` | r′, x′, b′, max current per kV and line/cable of `full_network.csv` (median / mean / Q1 / Q3) |
| Template | `read_template` | reads the cells of the Parameters tab of `IP26_line_separate_sheet.xlsx` |
| Scenario | `apply_scenario` | builds the line-type table (and for `template` the ratings and cap/PF/RF) |
| Per row | `compute(..., old)` | chooses r′, x′, b′ for the row (scenario table, or old line for lijnverzwaring in `median_oldline`); stores them in the `*_used` columns |
| Formulas | `write_data_sheet` | electrical formulas reference the row's `*_used` cells, which link to the Parameters tab (or hold old-line values) |
| Comparison | `write_comparison` | comparison workbook when several scenarios are run |
| Entry | `main(config, scenario)`, `run` | one scenario → one workbook; `all` → all + comparison |

### 6.3 `ip26_horizon_filter.py` (step 3)

| Function | What it does |
|---|---|
| `load_config` | reads `config_horizons.yaml` |
| `commissioning_year` | "2029-2030" → 2030 (end) or 2029 (start) |
| `header_row` | finds the header row (1, or 2 on lijnverzwaring) |
| `decide` | keep / remove with reason (phase, year, horizon) |
| `inline_formula` | replaces references to removed columns by their content so formulas stay live |
| `filter_data_tab` | keeps the selected rows and the columns up to `source` in a new sheet; translates formulas to the new rows |
| `filter_match_tab` | filters `Station_match` to the kept OBJECTIDs |
| `load_network`, `fn_section`, `fn_copies`, `fn_route`, `circuit_tag` | the GridAware network: branches by station pair, per circuit; duplicate copies; multi-station routes |
| `network_action` | modify existing branch / new edge (extra circuits) / new edge (new connection) / already in full_network, with branch IDs and note |
| `apply_decisions`, `is_manual_copy` | `config_decisions.yaml`: circuit assignment, route choice, splits; `manual:` copies not listed |
| `mark_references` | `applies_to_listed_branches` / `branches_also_listed_by`: which row applies a change to a branch (duplicates of one project, reference-only rows) |
| `clean_dropped` | removes the template block from `Parameters` and the notes on dropped columns from `Notes` |
| `write_log` | tab `Horizon_filter` |
| `process`, `main` | one scenario × one horizon → one workbook (network actions computed once per horizon on all kept rows, then written to every data tab); loops over all |

### 6.4 `ip26_vs_full_network.py` (step 4)

| Function | What it does |
|---|---|
| `load_config` | reads `config_vs_full_network.yaml` |
| `build_index`, `section`, `route`, `circuit_tag` | lines/cables of `full_network.csv` by station pair; edges per circuit letter; direct and via-chain lookup |
| `classify` | status of one IP26 line (station check, route, circuits, upgrade rating, cabling, new intermediate stations) |
| `project_status` | in / partly / not in per project |
| `write_df`, `main` | reads input (`full_network.csv`, `IP26_line.xlsx`) and output (`IP26_line_network_edges_median.xlsx`, config assignments); writes the workbook |

### 6.5 `ip26_final_network.py` (step 5)

| Function | What it does |
|---|---|
| `read_tab_values` | reads tab `1` of a horizon workbook with the formulas evaluated (evaluator of `ip26_excel_to_csv.py`; the workbooks have no stored results) |
| `project_info` | OBJECTID → project number, name, type, year (scenario workbook) |
| `read_line_types` | per-km values and ratings per kV and line/cable from the horizon Parameters tab (cable parameters for Verkabelen rows) |
| `manual_copies` | `manual:` branches that repeat a real circuit (never changed) |
| `project_on_line`, `row_ends` | IP26 line ends projected on a line (tap position, section location) |
| `upgraded_lengths` | upgraded length and its source text for every listed (unsplit) branch of one IP26 row |
| `base_section`, `replace_base` | section model: GridAware's branch as one section; an upgrade replaces part of the old section |
| `build` | splits first (decisions), then the upgrades (rows with `applies_to_listed_branches = yes`), then R, X, B, rating, type, per unit, sn_mva from the sections; adds the new edges; writes the change log |
| `checks` | independent checks (untouched rows, copies unchanged, branches changed once, sections vs values, split lengths, islands) |
| `write_workbook` | `network` and `change_log` tabs, numbers stored exactly (openpyxl would round to 16 digits) |
| `main` | loops over scenarios and horizons; writes the summary workbook |

### 6.6 `ip26_excel_to_csv.py` (step 6)

Converts the workbooks of a folder (default `output_final/`) to CSV. It contains a small Excel formula
evaluator, because workbooks written by openpyxl store formulas but not their results (pandas or
`openpyxl(data_only=True)` would give empty cells); step 5 uses the same evaluator to read the horizon
workbooks.

| Function / class | What it does |
|---|---|
| `tokenize`, `Workbook.evaluate` (and `_compare` … `_primary`) | Excel formula evaluator with Excel precedence (comparison < `&` < `+ -` < `* /` < `^` < unary minus < `%`); empty cells count as 0; references within the tab, to other tabs (`Parameters!$C$5`) and ranges; functions SQRT, ABS, MIN, MAX, SUM, AVERAGE, ROUND, IF, AND, OR, PI, POWER, EXP, LN; nested formulas resolved recursively, circular references reported |
| `Workbook.value` | value of one cell (formula → evaluated result, cached per cell) |
| `libreoffice_recalc` | fallback (engine `auto`): re-saves the workbook with headless LibreOffice, which stores the results |
| `convert_workbook` | per tab: values of all cells, check against stored results, CSV writing |
| `main` | finds all `.xlsx` files (recursive, skips `~$` lock files and the CSV folder) and prints a summary per workbook |

The evaluator was validated on all 49,284 formula cells of the step 2 and step 3 workbooks: every value equal to
the LibreOffice-recalculated result (relative difference ≤ 1e-9), 0 Excel errors.

---

## 7. Configuration reference

### `config_network.yaml` / `config_scenarios.yaml`

| Key | Meaning |
|---|---|
| `paths` | `input_folder: DATA` (the DATA folder inside NewLines_IP26), `output_folder`, file names (`{scenario}` placeholder in step 2) |
| `output_mode` | `formulas` (live Excel formulas) or `values` |
| `system.s_base_mva`, `edge_type_map`, `default_edge_type` | per-unit base; bovengronds/ondergronds mapping |
| `line_types` (step 1) | r′, x′, b′, rating per kV and line/cable (medians of `full_network.csv`) |
| `scenarios`, `rating_overrides`, `template_workbook` (step 2) | scenario definitions; IP2026 4 kA ratings; template cells and their mapping to kV/type |
| `reinforced_max_current_a` | rating of lijnverzwaring rows per kV |
| `circuits` | `override`, `name_rules`, `existing_route_types`, `default_by_kv`, `ignore_circuit_ids` |
| `template_parameters` | cap, PF, RF of the template columns; `capacity_applies_to_kv` |
| `matching` | geometry tolerance (1 km), automatic snap distance (1.5 km), edge_id format |
| `points_file`, `new_station_types` | IP26 point file and the point types listed in `IP26_new_stations` |
| `extra_stations` | stations not in the ArcGIS layer: ID, name, kV, x/y (or `point:` OBJECTID), origin, note |
| `assignments` | per OBJECTID: `from`, `to`, `via`, `conf`, `note`, optional `old_chain`, `old_chain_first` |
| `notes` | text of the Notes tab |

### `config_horizons.yaml`

| Key | Meaning |
|---|---|
| `paths` | scenario workbooks in, horizon workbooks out (`{scenario}`, `{horizon}`) |
| `scenarios`, `horizons` | which scenarios and years (default 2030, 2040) |
| `year_basis`, `inclusive` | end or start year of a range; ≤ or < horizon |
| `exclude_phases` | phases removed first (`Studie`) |
| `drop_rows_without_year`, `drop_duplicate_features` | remove empty rows and duplicate features |
| `keep_columns_until` | last column kept in the data tabs (`source`) |
| `network_check` | `enabled`, `network_file` (`DATA/full_network.csv`), `decisions_config` (`config_decisions.yaml`), `assignments_config` (old_chain), `edge_types`, `ignore_circuit_ids`, `circuit_rules`: adds the network-action columns |
| `filter_match_tab` | tab filtered to the kept OBJECTIDs |

### `config_vs_full_network.yaml`

| Key | Meaning |
|---|---|
| `paths` | `input_folder: DATA`, output folder; `network_file`, `ip26_file`, `edges_workbook` (from step 2), `network_config` (assignments), `juan_nodes_file` (optional CSV), `output_file` |
| `edge_types`, `ignore_circuit_ids` | edges that form a route; circuit letters not counted (`Nvt`) |
| `circuit_rules` | projects that add circuits and the circuits required |
| `upgrade_target_rating_a`, `upgrade_target_is_assumption`, `verify_assumed_targets` | rating an upgrade must reach; 150/110 kV targets are assumptions and reported as not verifiable |
| `cabling_types`, `upgrade_types` | werkzaamheden treated as cabling / upgrade |
| `network_year` | year of the GridAware network (2030) |

### `config_final_network.yaml`

| Key | Meaning |
|---|---|
| `paths` | `base_network` (`DATA/full_network.csv`), horizon workbooks, scenario workbooks (project numbers), `output_folder` (`output_final`), `decisions_config`, `stations_file` and `endpoints_file` (geometry for the split and section location), `points_file` (IP26 points for the New_stations tab) |
| `scenarios`, `horizons` | which final networks are built |
| `modify.full_coverage_threshold` | IP26 length / route length from which the whole branch counts as upgraded (1.0 = length weighting for every partial upgrade, review point 5; 0.7 = old rule) |
| `modify.rating_partial`, `rating_full` | `min` (old, new) for partial upgrades; `new` or `min` for fully upgraded branches |
| `modify.sn_mva`, `sbase_mva` | `scale` (GridAware's sn_mva × I_new / I_old) or `formula` (√3·kV·I); Sbase for per-unit |
| `modify.type_on_full_coverage` | `ip26` (fully upgraded branch gets the IP26 type, e.g. cable) or `base` |
| `add_new_edges` | add new connections / extra circuits as `new (IP26)` edges (true) or only log them (false) |
| `record_status` | labels `base`, `derived`, `new (IP26)` |

### `config_excel_to_csv.yaml`

| Key | Meaning |
|---|---|
| `paths.input_folder`, `recursive`, `output_folder`, `exclude_folders` | workbooks to convert (`output_final` incl. the scenario subfolders), where the CSVs go (`output_final_csv`) |
| `layout` | `folder_per_workbook` (`<workbook>/<tab>.csv`) or `flat` (`<workbook>__<tab>.csv`) |
| `sheets` | `all` or a list of tab names |
| `engine` | `evaluate` (Python evaluator), `cached` (results stored by Excel/LibreOffice), `auto` (evaluate; else stored result; else LibreOffice) |
| `check_against_cached`, `tolerance` | compare evaluated values with stored results when the file has them |
| `csv.delimiter`, `encoding`, `header_newline`, `float_format`, `drop_empty_rows` | CSV format (`utf-8-sig` for opening directly in Excel) |

### Typical edits

| To change | Where |
|---|---|
| a station of a line | `assignments: <OBJECTID>: {from, to, via}` |
| a new station or its name | `extra_stations` |
| circuits of a line | `circuits.override: {<OBJECTID>: N}` |
| per-km values or ratings | Parameters tab of the output (live) or `line_types` / `scenarios` / `rating_overrides` |
| the scenario | `SCENARIO` at the top of `ip26_network_scenarios.py` |
| horizon years or year rule | `config_horizons.yaml` |
| partial-upgrade threshold, rating rule, adding new edges | `config_final_network.yaml` |
| location of the data folder | `input_folder` (steps 1, 2, 4), `network_file` (step 3), `base_network` (step 5) |

---

## 8. Verification done

- All electrical values recomputed independently from the inputs for every row and scenario: identical
  (differences ≤ 1e-9); formulas recalculated in LibreOffice without errors.
- Station IDs, names and voltages identical to `full_network.csv` where the station exists there;
  edge_ids unique; project columns identical to `IP26_line.xlsx`.
- Station matches checked against the line geometry (distance per end in `Station_match`), the project
  names, the TenneT circuit IDs around the line ends and the IP2026 point file.
- `X standard` equals `reactance_ohm` and `X model` equals √3 × `reactance_ohm` in every row.
- Horizon workbooks: every kept edge has the same values as in its scenario workbook; every listed
  `full_network_edge_ids` exists in `full_network.csv`; no "new connection" row has a direct branch.
- Final networks (step 5): see the checks in §4.8 – base rows bit-identical to `full_network.csv`, every branch
  changed once, all derived values recomputed independently (≤ 8e-16), rating rule respected.
- Precision: `full_network.csv` is read with exact float parsing (`float_precision="round_trip"`; the pandas
  default parser changes the last digits, e.g. 0.006133333333333333 → 0.0061333333333333) and the final
  workbooks store numbers exactly.

## 9. Known limitations

- `Shape__Length` is the indicative IP26 trace; for partial sections (cable sections) it is the section length.
- r′, x′, b′ are typical values per voltage and line/cable (except `median_oldline` for upgrades); conductor
  types per project are not published.
- Ratings of 150/110 kV after reinforcement (1,500 / 1,000 A) and the default of 2 circuits for new
  connections are assumptions.
- The template capacity of 1000 MVA per 380 kV circuit is lower than 4 kA (≈ 2,635 MVA); change `cap` in the
  Parameters tab if the template columns should match.
- Six lines have low-confidence station matches (§4.1); check them before using the 2040 network.
- GNMS110 and MDM380 are approximate, assumed locations; confirm from IP2026 projects A-1003051 and A-1003017.
- Nieuwdorp Liechtensteinweg (375–377) is left out for now; the split of Borssele–Rilland is on hold.
- New stations have no loads or generators in the data (tab `New_stations`); 4 new buses in 2030 and 23 in 2040
  have only one connection, and new stations at a second voltage of an existing site have no transformer.
- Step 5 splits an existing branch only where `config_decisions.yaml` enables it.
  Other loop-ins of new stations (e.g. 304/379, 306/398, 311/345, 373, 324 in 2040/2030) are added as new edges
  next to the existing branch, which is named in `action_note`. Two pairs of new stations are islands in 2040
  (no transformer data).
- Tap position and section location from the IP26 geometry are projections on the straight line between the two
  stations, scaled to GridAware's branch length.
- Partial upgrades: the position of the upgraded section on the branch is unknown; the IP26 length is spread in
  proportion to the branch lengths of the route.
- Step 4 judges "in full_network" from the network topology, circuits, rating and cable type; it cannot see
  other project content (e.g. GIS replacement, station layout). Upgrades at 150/110 kV cannot be verified.
