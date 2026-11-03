# 2026-10-16 — Part 2 result: the Dutch 2035 grids under the IP26 project matching's and TenneT's rule, against the base v29

User: "approve all as proposed, build both patches and run the chain". Decision table: `patches/ip2026_nl_2035_decisions`
(scripts/111; rules in notes/18). Patches: `patches/ip2026_nl_2035_amir` (Realisatie + Voorbereiding: 18 row changes,
Rilland–Tilburg W/Z + TILBURG_380, third Eemshaven Oudeschip–Eemshaven circuit) and `patches/ip2026_nl_2035_tennet`
(Realisatie only: 11 row changes, Rilland–Tilburg + TILBURG_380), built by scripts/112, applied to v29 by scripts/113 (the
apply step with a modify option) → `inputs/derived/jao_core_v29-2035-amir`, `…-tennet`. Five IP2026 stations recorded, not
built (no flow effect in a one-node Dutch model). Tests `tests/test_ip2026_2035_patches.py` (5) pass; re-applying a patch
does nothing. Chain per grid: reduction, 19-branch fit, N-1 380 kV limits, option 3, 2025 fixed-position test (sensitivity),
Tulipa folder and the two test days; comparison `runs/2026-10-16-compare-2035-grids-v29-2035/report.md` (scripts/114).

## 1. What the 2035 projects change in the model

| | base v29 | 2035, TenneT's rule | 2035, our rule |
|---|---|---|---|
| Dutch 380 kV rows re-rated to 4,000 A | — | Krimpen–Diemen–Beverwijk corridor (7 circuits), Rilland–Zandvliet (2) | the same + Dodewaard–Doetinchem (2), Maasbracht–Boxmeer–Dodewaard (3), Geertruidenberg–Rilland (2) |
| Borssele–Rilland G/Z cable section | — | X 9.63 → 7.28 Ω | same |
| new elements | — | TILBURG_380, Rilland–Tilburg W/Z (78 km, 4,000 A) | same + third Eemshaven Oudeschip–Eemshaven circuit |
| equivalent reactances of the 19 branches | | identical to v29 (4 decimals) | identical |
| N-1 branch limits that move | | BE–NL 2,658 → 2,707 MW; DE–NL 2,826 → 2,891 | identical to TenneT's |
| option-3 branch limits that move | | BE–NL 3,732 → 3,874 MW; DE–NL 5,398 → 5,392 | identical |
| N-1 pair limits of the Dutch pairs | | AT/CZ/DE/FR/HU–NL +2.2 %, BE–NL +1.9 %, others unchanged; the setting lines do not change (Niederlangen, Maasbracht–Van Eyck, …) | identical |
| 2025 test, hours inside: present / N-1 / option 3 | 83.5 / 88.8 / 91.7 % | 83.5 / 89.6 / 91.7 % | identical |
| Tulipa test days, DC-OPF objective | 2.0487492e9 / 1.0969112e9 | 2.0487606e9 / 1.0968967e9 | identical |
| pair limits vs JAO's 2025 MaxBEX (median ours / JAO) | 1.09 | 1.09 | 1.09 |

## 2. Reading

- **The two rules give the same reduced network.** The six projects that separate our rule from TenneT's are
  reinforcements of lines (Dodewaard–Doetinchem, Maasbracht–Boxmeer–Dodewaard, Geertruidenberg–Rilland) and one short
  extra circuit; none of those lines sets a pair limit or is the decisive outage, and with the Netherlands as one node a
  higher rating inside the country cannot appear in the 19 branches. In our country-level model the choice of rule does
  not matter for 2035.
- **Against today's grid the Dutch 2035 projects move two numbers**: the BE–NL branch limit (+4 % in option 3) and the
  DE–NL N-1 limit (+2 %). Everything else is unchanged to the decimal: the reactances, because reinforcements do not change
  X and the Tilburg spur and the extra 1.6 km circuit are too small; the limits, because the binding elements for the
  Dutch pairs are German lines (Niederlangen) and the Belgian ties (Maasbracht–Van Eyck), not the re-rated Dutch lines.
- **A caveat on the +2.2 %.** The pair limits AT–NL, CZ–NL, DE–NL, FR–NL and HU–NL all rise by the same factor 1.022
  = 46/45: the Dutch exchange is spread evenly over the country's 380 kV buses, and TILBURG_380 is now one more of them,
  so slightly less of a Dutch export enters near the German border and Niederlangen is loaded slightly less per MW.
  That is an effect of the injection key, not of grid strength; it would disappear with a generation-weighted key or
  with Tilburg excluded from the spread. The BE–NL changes (+1.9 % N-1, +3.8 % option 3) are partly this effect too.
- **For Tulipa** the 2035 Dutch grid changes the DC-OPF objective on the test days by 0.001 %.

## 3. Consequence for the programme

The Dutch IP2026 projects to 2035 are, for the country-level DC-OPF, a non-event: their value is inside the Netherlands,
which this model does not resolve. What would change the 2035 cross-border picture is the rest of Core (German
north–south corridors, Belgian and French reinforcements, the Polish and Czech projects), which Part 2 as scoped does not
touch, and any change at the coupling points (new interconnectors, phase shifters). Options: (a) accept the 2035 Dutch
grid as built (either rule) and move to the Core-wide question; (b) stop here and use v29 for 2035 as well, since the
difference is within noise.

## Folders

`inputs/derived/jao_core_v29-2035-{amir,tennet}`; `runs/2026-10-16-stage2-v29-2035-*-LP-virtual`; `…-sparse-fit-v29-2035-*`;
`…-limits-v29-2035-*-n1-380kv[-pst-frm10]`; `replay2025/runs/fixedposdc_diag_fixedpos_v29-2035-*-sparse-LP*_single`;
`inputs/derived/tulipa_dcopf_2035_base2b-v29-2035-{amir,tennet}-sparse19-N1-380kV-PST-FRM10` (+ the two cut days);
`runs/2026-10-16-stage3-pair-2035-01-0{4,9}-v29-2035-*-…`; `runs/2026-10-16-ttc-vs-maxbex-v29-vs-2035`; logs
`notes/stage2_v29-2035-*`, `sparse_fit_v29-2035-*`, `limits_v29-2035-*`, `ttc_pst_frm10_v29-2035-*`, `stage3_v29-2035-*`.
