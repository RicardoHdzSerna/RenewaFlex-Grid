# 2026-10-16 — Which IP2026 projects count for a future grid: what the IP26 project matching did, what TenneT itself does

User: "there are some rules that we need to follow in order to say: this project can happen, this is still too early
stage ... I think he did it, so I want to understand what he did first." Sources: the IP26 project matching's `README.md` and `PROVENANCE.md`
(`dcopf/IP2026 and the IP26 project matching work/Code/`), his horizon workbooks, TenneT's IP2026 text (chapters 3, 4, 5, 7), the IP26 line layer.

## 1. The raw material: TenneT's project list

The ArcGIS layer `IP26_line` has 167 line features (one project can be several features). Attributes that carry maturity:

| attribute | values (features) | meaning |
|---|---|---|
| `n_projectfase_ip` | Studie 76, Voorbereiding 50, Realisatie 37, blank 4 | TenneT's project phase at the time of the plan |
| `N_ibn_jaar_ip2026` | a year or a range, e.g. "2031-2034" | planned commissioning (in-service) window |
| `n_miek` | n.v.t. 81, pMIEK 59, nMIEK 23 | national / provincial energy-infrastructure priority programme label |
| `n_werkzaamheden_ip` | new connection 76, reinforcement 61, cabling 12, station extension 10, … | what the project does |

TenneT's phases (IP2026 §5, figure 5.8): G0 initiation → **study phase** (alternatives) → Gate 1 (selection of alternatives)
→ **basic design** → Gate 2 (Final Investment Decision) → **realisation phase** (permits, detail design, construction,
commissioning) → G4/G5 close-out. The layer's three labels read as: *Studie* = before Gate 1; *Voorbereiding* = between
Gate 1 and the investment decision; *Realisatie* = after the investment decision (my reading of the two vocabularies; the
layer uses "Voorbereiding", the text "basisontwerpfase").

## 2. TenneT's own rule, in the plan itself

IP2026 §5.3 (net model): the grid used for the calculations is the expected situation on 1 July 2026, and for the target
years it is extended only with projects that were **in the realisation phase in December 2024**. Projects in the study and
basic-design phases are deliberately left out, "so that the risk score of a project can still be updated until the Final
Investment Decision (Gate 2) and need and usefulness stay monitored." Consequence stated in chapter 3: the 2040 grid TenneT
tests is "almost identical to the 2035 grid", because only realisation-phase projects enter.

Chapter 4 gives the reason in numbers: about 200 projects slipped against IP2024; the most and the largest delays occur in
the study and basic-design phases; realisation-phase projects slip far less and by less. (90 % of the ~70 projects finished
2023–2025 were on time.)

Two technical statements worth keeping: §7.4 — "within the horizon of this plan all domestic 380 kV and 220 kV connections
are upgraded to 4,000 A (4 kA)"; the "Beter Benutten Bestaande 380 kV" programme raised several 380 kV connections to
2 × 2,635 MVA (4 kA) per connection and is finished.

## 3. What the IP26 project matching did (his step 3, `ip26_horizon_filter.py`, `config_horizons.yaml`)

Per parameter scenario and per horizon year (2030 and 2040; no 2035):

1. **Remove phase Studie** (76 features). This is his only maturity rule: Voorbereiding and Realisatie are both kept.
2. **Keep a line when its commissioning year ≤ horizon**; for a range such as "2029-2030" the **last** year counts
   (`year_basis: end`, `inclusive: true`), i.e. the project is in only when fully in service by the horizon year. The
   first-year alternative is a config switch; his PROVENANCE lists it as the open decision "E18" (10 rows start by 2030 but
   end after it; flagged only).
3. Remove rows without a year (4) and duplicate drawings of the same project (13 in 2040: same geometry drawn 2–4 times;
   the first feature is used, N circuits split over k different features).
4. Result: 2030 → 30 edges (27 projects); 2040 → 70 edges. Removal reasons in his 2040 log: Studie 76, duplicates 13,
   "in service 2038-2041, after 2040" 4, no year 4; kept 70.

Then, independently of maturity, he classifies every kept edge against the GridAware network (`network_action`): *modify
existing branch* (reinforcement or cabling of a connection GridAware has: change that branch's rating and parameters, do not add
an edge; 20 of 30 in 2030), *new edge (new connection)* (a station or route not in the GridAware network; 10 in 2030), *new edge
(extra circuits)* (3rd/4th circuit; 2040 only), *already in full_network*.

Values he attaches (not maturity, but needed later): per-km R, X, B from the statistics of the GridAware network per voltage and
line/cable (six scenarios: median, mean, Q1, Q3, template x′ 0.265 Ω/km, median with old-line values); **rating after a
reinforcement 4,000 A at 380/220 kV** (citing IP2026 §7.4), 1,500 A at 150 kV and 1,000 A at 110 kV (assumptions); two
circuits by default for new connections (IP2026 table 8.3); length = the IP26 trace. Station ends from geometry, names,
TenneT circuit ids and the IP26 point file, with a confidence per line.

His step 4 answers a different question: which IP26 projects are already in GridAware's 2030 network (12 in, 62 partly, 62
not in; of the 28 due by 2030: 1 in, 18 partly, 9 not in).

What he did **not** do: no 2035 horizon; no distinction between Voorbereiding and Realisatie; no use of the MIEK labels;
no delay allowance; the values are generic, not project data; the 20 "modify existing branch" items of 2030 are listed as
unclear (whether GridAware's branch already carries the upgrade), two of them at 380 kV (Rilland–Zandvliet 290/303, Borssele–
Rilland cabling 378).

So the IP26 project matching is **more inclusive than TenneT**: TenneT counts realisation-phase projects only; the IP26 project matching counts realisation and
preparation, and drops only the study phase.

## 4. What the two rules give for our Dutch 2035 grid (220 kV and up; end year of the range ≤ 2035)

49 features at 380/220 kV in the layer. By phase and commissioning end:

| phase | end ≤ 2030 | 2031–2035 | after 2035 | total |
|---|---|---|---|---|
| Realisatie | 5 | 6 | 3 | 14 |
| Voorbereiding | 0 | 9 | 11 | 20 |
| Studie | 0 | 2 | 13 | 15 |

- **TenneT's rule (Realisatie only, end ≤ 2035): 11 features, 7 projects** — Rilland–Zandvliet reconductoring (2025;
  JAO 2026 already lists 3,790 A), Amaliahaven station (2027), Borssele–Rilland cabling (2028), Nieuwdorp Liechtensteinweg
  station (2029–30), Halsteren station (2030–31), Krimpen–Diemen–Beverwijk reinforcement (2030–31), Rilland–Tilburg ZW380
  (2031–34).
- **our rule (Realisatie + Voorbereiding, end ≤ 2035): 20 features, 13 projects** — the seven above plus Dodewaard–
  Doetinchem reinforcement (2030–31), Einighausen station (2031–34), Maasbracht–Boxmeer–Dodewaard reinforcement (2031–34),
  Eemshaven Oudeschip–Eemshaven third circuit (2031–34), A9-Zuid station (2032–35), Geertruidenberg–Rilland reinforcement
  (2032–35).
- **Studie, end ≤ 2035: 1 project** (Beverwijk–Vijfhuizen–Bleiswijk reinforcement, 2030–31): out under both rules.
- **E18 cases for 2035** (start by 2035, end after): Vierverlaten–Ens 380 kV (Realisatie, 2035–38, nMIEK), Noord-Holland
  Noord 380 kV (Voorbereiding, 2035–38, nMIEK), Maasbracht–Eindhoven 3rd/4th circuit (Voorbereiding, 2035–38, pMIEK),
  Wijchen 380 station (Voorbereiding, 2033–36, nMIEK), and five Studie projects (Borssele–Rilland, Geertruidenberg–
  Eindhoven, Zwolle–Hengelo, Maasbracht–Van Eyck reinforcements; the two northern 220 kV rings). With the end-year rule
  all of these are out of a 2035 grid; with a first-year rule the first four would be in.

Note that most of what the two rules add to a 2035 grid are reinforcements (ratings), and that with one Dutch node the
five new stations change no flow (notes/17 §2). The two items that change topology are Rilland–Tilburg (radial spur to a
new 380/150 kV station) and the third Eemshaven circuit.

## 5. Reading, for the decision

- TenneT's rule is deliberately conservative: it exists so that the plan keeps showing the bottlenecks that unstarted
  projects would solve. For a scenario grid of 2035 that is the floor, not the expectation.
- our rule treats everything past Gate 1 as happening on schedule; IP2026's own delay statistics say preparation-phase
  projects slip often. It is the ceiling for "planned by TenneT".
- A defensible middle: base = our rule (Realisatie + Voorbereiding, end year ≤ 2035), with TenneT's rule as the
  conservative sensitivity, Studie out, E18 cases out (end-year rule), and MIEK labels recorded but not used as a rule.
  Both grids can be built from the same decision table; the difference is 6 projects, all but one reinforcements.
