# 27 — Grid model: freeze and limitations (2026-10-26)

User, 2026-10-26: "at a certain point, say, okay, this is fine, this is the limitations, and move forward" — agreed: the grid model is
frozen as below, the open fixes are parked, and this list goes with every result that uses it. Numbers are from the runs logged in
`docs/provenance.md`; nothing here is new.

## What is frozen

| Use | Network | Status |
|---|---|---|
| 2035 Tulipa runs (RenewaFLEX) | nodal, SR2025 32 nodes, 4 kA patch, option-3 limits: **main** = Belgian ties × 0.826 (`…-rt4k-…-pst-frm10-tiefixbe`), **lower** = Belgian × 0.826 and German ties × 0.797 (`…-tiefix`) | round 2, delivered, frozen |
| 2035 country runs | `…-rt4k-sparse-LP-n1-380kv-nl220-ge1km-pst-frm10` | frozen |
| 2025 validation | country `v29-vvltr2` option 3; nodal `v29-vvltr2-nlsander31` | frozen |

Two runs that were already going are decided once, then closed:

- **Belgian border node** (Zandvliet, or Zandvliet + Lillo; with the German north/south split and the spread fit). Adopted for a round-3
  2035 network only if it clearly earns its place: a clearly lower BE–NL error and bias in the 2025 test, AND the full-grid check shows
  no tie cut is needed (NL→BE over-allowed by 5 % or less). Otherwise dropped; round 2 stands.
  **Decided 2026-10-26: not adopted.** BE–NL bias +0.54 → +0.52 GW (no change with the fit), and the full grid still allows only
  0.82 of what the reduced network allows NL→BE (Doel–Zandvliet binding), so the tie cut stays. Round 2 stands.
- **JAO comparison on 80 hours of 2026** (download running): only to finalise the numbers in the N-1 note.

## What the model is good for

- Cross-border flows of the Core region at the level of a year: 2025 routing error about 0.39 GW per border on average (mean hourly r
  0.90), 92 % of 2025 hours inside the limits.
- Transfer limits of the right size: median 1.09 times what JAO offered the market in 2025 (MaxBEX).
- Where Dutch internal congestion sits and in which direction, as long as the levels are read as indicative (see 1 and 3 below).

## Limitations

| # | Limitation | How big | What it means for results |
|---|---|---|---|
| 1 | **One point per country** (or per Dutch station). Each country's injection enters at one bus, so some loop flows are wrong. | 2025: BE–NL bias +0.33 GW (country network) to +0.68 GW (nodal); routing error 0.39 GW per border. German north/south split + fitted reactances bring the routing error to 0.30–0.32 GW, BE–NL bias stays +0.41–0.52 GW. | The split of Dutch trade between Belgium and Germany is off by a few hundred MW on average. Internal Dutch congestion levels depend on where German power is assumed to be (e.g. Krimpen–Geertruidenberg binding hours in 2035 change by 27 % with an even German spread). Read congestion levels as indicative, directions as robust. |
| 2 | **Limits are checked one exchange at a time** (each branch gets the largest need of any single pair). Several exchanges together can exceed what the full grid carries. | 2035 nodal network: NL→BE allowed 1.21 times the secure value, NL→BE+DE 1.24 times; NL→DE alone right (1.00). | Corrected with a uniform tie cut (main: Belgian ties × 0.826; lower: + German ties × 0.797). The cut applies every hour, also when the real bottleneck (Doel–Zandvliet in Belgium) is not binding, so it is conservative in some hours and still not exact in others. |
| 3 | **Even spread instead of the operators' shift keys.** Inside a country an exchange is spread evenly over the 380 kV buses. | Line shares within 25 % of JAO's for 45 % of lines (69 % of TenneT NL lines), 80 hours of 2026; a one-bus placement gives 26 %, below 30 % for the lines of AT, CZ, HU, HR, SI, RO. A Dutch generation + load key does not do better. | Limits are sound in level (see 2025 tests) but individual lines can be off; the one-bus routing of the reduced network (1) does not match this assumption. |
| 4 | **Only 380 kV lines of at least 1 km may set a limit** (+ Dutch 220 kV lines of at least 1 km in the nodal network). Operators select by sensitivity (5 % PTDF), from 110 kV up. | Fits the Netherlands and neighbours: TenneT NL monitors only 380 kV; in 2025 TenneT NL, Amprion, Elia, 50Hertz, RTE and PSE had only 380 kV elements binding. Misses 220 kV limits that carry 30 % of 2025 Core shadow prices, almost all Austria and Bavaria–Austria. | Limits on AT–DE, AT–CZ and nearby borders are likely too generous. Measured 2025 flows exceed our limits on HR–HU in 40 % and PL–SK in 23 % of hours (parked). |
| 5 | **Phase shifters set once per exchange, preventive, within their range.** | Without the 10 % margin, limits are about 1.21 times MaxBEX; with it 1.09. | Optimistic for simultaneous exchanges (one setting serves all exchanges in reality); the margin compensates on average. |
| 6 | **DC power flow, one rating per line.** No losses, no voltage or stability limits; JAO's seasonal currents averaged (no summer/winter); for 2035 the 4 kA rating on Krimpen–Geertruidenberg and Eindhoven–Maasbracht. | Not quantified separately. | Seasonal congestion patterns are flattened. |
| 7 | **Tuned and tested on 2025 only.** Choices (monitored set, spread, margin, tie cut) were judged on 2025 data. | No out-of-sample year. | A 2024 test would show how much of the fit is 2025-specific (parked). |
| 8 | **2035 grid = TenneT IP2026 on the 2026 JAO grid.** Dutch 2035 projects selected by rule; foreign grids stay as in 2026, Germany as one node without its 2035 HVDC corridors (in the frozen networks). | e.g. 2035 Krimpen–Geertruidenberg binds northbound, the opposite of 2025 (southbound, 500 h). | Foreign-side 2035 flows, above all German north–south transit, are the least certain part. |
| 9 | **Non-Core neighbours** (GB, Nordics, CH) enter at assumed landing stations. | Moving them changes the 2025 routing error by 0.001 GW. | Negligible. |

## Parked (not to be done unless a result depends on it)

Weighted spread fits beyond 42b; more representative-bus screening; the 2024 out-of-sample test; splits of other countries; exactly
JAO's monitored list as the monitored set; the eastern non-Core data download; seasonal ratings; the 15.1 GW north–south variant of the DE2 2035 network (decide after RenewaFLEX's split runs).
