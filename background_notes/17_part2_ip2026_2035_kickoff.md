# 2026-10-16 — Part 2 kickoff: the Dutch 2035 grid from TenneT's IP2026 (220 kV and up)

User (2026-10-16): "keep v29, rebuild the Tulipa folder and start part 2". Part 2 = the 2035 change list from TenneT's
Investeringsplan 2026, applied to the JAO 2026 grid (base v29), 220 kV and above only (decision 8). This note is the
scoping: what the sources give, which projects are in, how they would enter the grid, and what has to be decided first.
Nothing has been added to any workbook.

## 1. Sources at hand (all in `dcopf/IP2026 and the IP26 project matching work/`, registered copies in `inputs/external/tennet_ip2026_2026-10-16/`)

| source | what it gives | what it lacks |
|---|---|---|
| `IP26_line.xlsx` (TenneT ArcGIS line layer, 167 features) | project number and name, phase (Studie 76, Voorbereiding 50, Realisatie 37), work type (new connection 76, reinforcement 61, cabling 12, station extension 10, customer connection 3, station replacement 1), existing/new, overhead/underground, commissioning range `N_ibn_jaar_ip2026`, trace length; kV: 380 (41 features), 220 (8), 150 (96), 110 (22) | no electrical parameters, no ratings, no end stations as attributes (only the trace) |
| `IP26_point.xlsx` (366 project points) | station projects with RD coordinates and years | — |
| IP2026 PDF and annexes 4–6 | bottleneck ↔ project links, years, descriptions | numbers |
| the IP26 project matching's pipeline (`Code/`, `NewLines/output/`; contrib, not run here) | per project: end stations matched to GridAware's station ids, circuits, per-km R/X/B from Grid-Aware statistics by voltage and type, a "reinforced rating" assumption for upgrades; horizons 2030 and 2040 (rule: last year of the commissioning range ≤ horizon; Studie removed); `network_action` = modify existing branch / new edge (extra circuits) / new connection, with the GridAware branch ids affected | the xlsx here hold the values as formulas (the branch's CSV outputs are not in the folder; the Parameters tab allows recomputation); known issues (his PROVENANCE): double counting unless filtered on `network_action`, partial-branch upgrades not length-weighted, loop-in stations undefined, assumed stations, unregistered inputs; no 2035 horizon |
| GridAware's `full_network.csv`, JAO v29 | identities of the existing branches an upgrade touches | — |

## 2. The 2035 list at 220 kV and up

Rule used here (the IP26 project matching's E18 rule, extended to 2035): last year of the commissioning range ≤ 2035. 49 features at 220/380 kV
in the layer; 22 features (14 projects) qualify, 2 of them in phase Studie. All 380 kV; the eight 220 kV features are
2036 or later. Grouped by what they would do to our grid:

**A. Reinforcement or cabling of lines that exist in v29 (change the rating, for cabling also X)**

| project | km | phase | IBN | in our grid |
|---|---|---|---|---|
| A-1000664 Rilland–Zandvliet 380 kV vervangen geleiders | 11 | Realisatie | 2025 | tie-lines RILLAND–ZANDVLIET GREY/29, WHITE/30: JAO 2026 already lists 3,790 A, i.e. the new conductors — probably nothing to do; to confirm |
| A-1002896 Borssele–Rilland 380 kV verkabelen | 20 | Realisatie | 2028 | Borssele–Rilland G/O/P/Z: part of the route becomes cable (lower X per km, rating to be given) |
| A-1003078 Dodewaard–Doetinchem 380 kV verzwaren | 45 | Voorbereiding | 2030–31 | Dodewaard–Doetinchem W/Z (2,500 / 3,100 A seasonal today) |
| A-1003430 Krimpen–Diemen–Beverwijk 380 kV verzwaren | 89 | Realisatie | 2030–31 | Krimpen–Diemen Z, Krimpen–Breukelen, Breukelen–Diemen, Diemen–Oostzaan G/Z, Beverwijk–Oostzaan W/Z (patch rows) |
| A-1000363 Beverwijk–Vijfhuizen–Bleiswijk 380 kV verzwaren | 58 | **Studie** | 2030–31 | Beverwijk–Vijfhuizen W/Z, Bleiswijk–Vijfhuizen O/P (patch rows) |
| A-1003079 Maasbracht–Boxmeer–Dodewaard 380 kV verzwaren | 100 | Voorbereiding | 2031–34 | Maasbracht–Dodewaard W, Maasbracht–Boxmeer Z, Boxmeer–Dodewaard Z |
| A-1003434 Geertruidenberg–Rilland 380 kV verzwaren | 60 | Voorbereiding | 2032–35 | Geertruidenberg–Rilland W/Z |

**B. New 380 kV connections**

| project | km | phase | IBN | what it is for our grid |
|---|---|---|---|---|
| A-1002678 Rilland–Tilburg 380 kV (ZW380 Oost) | 78 | Realisatie | 2031–34 | new line Rilland – new station Tilburg 380 (380/150 kV). With one Dutch node and no 150 kV, Tilburg 380 is a radial end: it carries no through-flow unless something else connects at 380 kV |
| A-1003432 Eemshaven Oudeschip–Eemshaven 380 kV 3e circuit | 1.4 | Voorbereiding | 2031–34 | a third circuit next to the two existing (0.38 Ω, 4,000 A each): corridor X ÷ 1.5, capacity × 1.5 |

**C. New 380 kV stations (loop-ins or spurs)**

| project | phase | IBN | reading |
|---|---|---|---|
| A-1003091 Amaliahaven 380 kV station | Realisatie | 2027 | Maasvlakte area; a spur station (the IP26 project matching: MVL–AMH 2.1 km). No through-path |
| A-1003600 Nieuwdorp Liechtensteinweg 380 kV station | Realisatie | 2029–30 | next to Borssele (the IP26 project matching: NDLS–BSL 1.2 km); spur |
| A-1003120 Halsteren 380 kV station | Realisatie | 2030–31 | 3.5 km underground to Rilland (the IP26 project matching: HST–RLL cable); spur for 150 kV supply |
| A-1003069 Einighausen 380 kV station | Voorbereiding | 2031–34 | Limburg, 21 km (the IP26 project matching: EIN–MBT line to Maasbracht); spur for 150 kV supply |
| A-1003408 A9-Zuid 380/150 kV station | Voorbereiding | 2032–35 | loop-in on Beverwijk–Vijfhuizen (the IP26 project matching: A9Z–VHZ 1.5 km) |

In a model with one Dutch node and no 150 kV, a spur or loop-in station without its own injection changes no flow: a
loop-in only splits a line into two series segments (same total X), a spur hangs dead. They matter for N-1 granularity
and for any later 150 kV coupling, not for the 2035 country-level flows. Proposal: leave group C out of the 2035 grid
and document it, except where a station creates a new parallel path (none of the five does).

**D. Out of scope by decision 8**: the 118 features at 150/110 kV (new 150 kV connections, cablings, 380/150 kV transformer
extensions, customer connections). Note that most of IP2026's 2035 investment is there.

## 3. What IP2026 does not cover, and must be decided

1. **The rest of Core in 2035.** The Tulipa 2035 runs use the JAO 2026 grid for all twelve countries. Part 2 as scoped
   updates the Netherlands only; Germany (SuedLink and the other HVDC corridors, 380 kV reinforcements), Belgium
   (Ventilus, Boucle du Hainaut), France, Poland, Czechia, Austria all change by 2035 too. Sources would be the TYNDP 2026
   project sheets (the baseline we run is TYNDP 2035; its NTCs already assume those projects) and the TSOs' development
   plans. Decision: Dutch-only 2035 grid (inconsistent with the TYNDP NTCs elsewhere), or a Core-wide 2035 patch
   (a much larger job, project by project).
2. **Ratings after a reinforcement.** IP2026 gives none. Options: JAO's highest Dutch 380 kV class, 4,000 A (what the newer
   Dutch lines carry today); the IP26 project matching's "reinforced rating" assumption; or ask TenneT. Same question for cabled sections.
3. **Reactance of new lines and cables.** Rule proposal: overhead 380 kV = median x′ of JAO's Dutch 380 kV rows (0.273 Ω/km);
   cable = JAO's own Dutch cable sections (Wateringen–Bleiswijk 0.168 Ω/km) or the IP26 project matching's per-km value; lengths from the
   IP26 traces.
4. **Studie-phase projects** (here only A-1000363, the Randstad north-ring reinforcement): in or out for 2035? the IP26 project matching
   excluded them.
5. **Validation.** A 2035 grid cannot be checked against measured flows. Proposed checks: option-3 limits of the 2035 grid
   against the TYNDP 2035 NTCs of the baseline (plausibility), before/after of the 2025 positions as a sensitivity, and
   the same N-1 / margin / phase-shifter machinery unchanged.

## 4. Proposed method (same mechanism as Part 1)

- One curated decision table, one row per project: action (re-rate / add row / add node / skip), target JAO rows (by
  EIC or placeholder), new current, X rule, length, evidence (IP26 feature ids, annex pages), status.
- A builder script turns it into a patch `patches/ip2026_nl_2035` (nodes_add, lines_add, and — new for Part 2 — a
  `lines_modify.csv` for re-ratings, since Part 1's apply step is additions-only; the apply script needs a copy with a
  modify step, with old/new values recorded in corrections.csv).
- Apply on v29 → `jao_core_v29-2035` (name to agree); reduction; option-3 limits; Tulipa folder
  `tulipa_dcopf_2035_base2b-v29-2035-sparse19-N1-380kV-PST-FRM10`; the two test days.
- Everything else as in Part 1: nothing in `IP2026 and the IP26 project matching work/` read by the pipeline (registered copies only),
  manifests, tests.

## 5. Decisions needed before building

1. Dutch-only 2035 grid, or Core-wide?
2. Reinforcement rating: 4,000 A unless IP2026 states otherwise, or ask TenneT first?
3. Studie projects in or out?
4. Group C stations: skip (no flow effect with one Dutch node), or add for N-1 granularity?
5. Horizon rule: last year of the commissioning range ≤ 2035 (as proposed), or first year?
