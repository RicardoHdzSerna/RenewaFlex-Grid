# 25 — 2035 grid with the 4 kA rating patch, and the two tie variants (2026-10-23)

Requested by the 2035 dispatch session (nl_merge; plan approved by the user): rating fix in all cases; Belgian-only tie correction as
the MAIN case; a strict all-ties correction as the LOWER bound; the uncorrected nodal network dropped. Grid/limit work done here,
Tulipa side there. Nothing existing was changed; all folders are new.

## 1. Rating patch

`scripts/25_build_patch_rating_4ka.py v29-vvltr2-2035-tennet-tlb3 ip2026_nl_2035_rating_4ka` → `inputs/patches/ip2026_nl_2035_rating_4ka`.
Four circuits go from 3,300 A to 4,000 A; capacity √3 × 400 kV × I = 2,771.281 MW (the workbook's convention: 3,300 A = 2,286.307 MW).
X, R and B are unchanged.

- Krimpen aan den IJssel–Geertruidenberg380 W and Z (49T0000000000274 / 49T0000000000282, A-1002589)
- Maasbracht–Eindhoven380 W and Z (49T0000000000290 / 49T000000000030F, A-1002586)

Source checked in `IP2026/Investeringsplan 2026 Net op land.pdf`:
- p.109, Table 8.5, "Opwaarderen naar 2 x 2.635 MVA", Gereed; text "(4 kA) per verbinding".
- Table 4.1: p.23 (A-1002589, 2023) and p.25 (A-1002586, 2025).
- End stations: A-1000199 (p.71, Realisatie 2026) and A-1002495 (p.69, Realisatie 2030–2031).

The other three corridors of Table 8.5 (Ens–Zwolle, Lelystad–Ens, Diemen–Lelystad) were already at 4,000 A in the workbook.

`scripts/17_apply_patches_modify_remove.py` → workbook `jao_core_v29-vvltr2-2035-tennet-tlb3-rt4k`. Diff against the source: exactly
those 4 rows. `scripts/18_nodal_workbook_nodeset.py` with `nl_ielgas_sander_32.csv` → `jao_core_v29-vvltr2-2035-tennet-tlb3-rt4k-nlsander`.

## 2. Limits (same rules as the 2026-10-21 networks)

Driver `scripts/run_chain_rt4k_2035.sh`. Steps:
- 01 reductions → `runs/2026-10-23-stage2-v29-vvltr2-2035-tennet-tlb3-rt4k[-nlsander]-LP-virtual`
- 02n2 / 02
- 03 + 03n2 → monitored set 380 kV ≥ 1 km + Dutch 220 kV ≥ 1 km, 1,393 EICs, identical to the 2026-10-21 set
- 04n + 05n2 (nodal), 04 + 05b (country)

**Reactances identical** to the unpatched networks (flow-milestone.csv equal, nodal and country).

Option-3 limits that moved by more than 0.5 % (all others within 0.5 %):

| Branch | Before (MW) | After (MW) | Change |
|---|---|---|---|
| Geertruidenberg–Krimpen | 3,010 | 3,496 | +16 % |
| Eindhoven–Maasbracht | 3,827 | 4,213 | +10 % |
| Ens–Zwolle | 3,233 | 3,283 | +1.5 % |
| Ens–Lelystad | 3,334 | 3,371 | +1.1 % |
| Country network BE–NL | 3,800 | 3,821 | +0.5 % |

The country network's NL–DE limit is unchanged at 5,704 MW.

2025 test, SR2025 injections on the 2035 node set: Geertruidenberg–Krimpen is over its limit in 68 h instead of 236 h. Eindhoven–Maasbracht
is never over. The other Dutch internal overloads are unchanged: Bleiswijk–Wateringen 2,110 h, Eemshaven–Meeden 251 h.

## 3. Tie variants (factors recomputed against the full grid of the patched grid)

Base full-grid check: `scripts/23b_full_grid_border_check_transit.py` → `runs/fullgridcheck_2035rt4k-base-transit`. The full-grid
secure values for the free Dutch side are the same as before the patch (NL→BE 5,300, NL→DE 10,322, NL→BE+DE 12,094 MW). The binding
elements sit behind the borders (Doel–Zandvliet, Diele–Meeden), so the factors are unchanged too.

- **Main:** `scripts/24b_tie_correction_variant_be_only.py` (suffix `-tiefixbe`). Belgian ties × 0.8261: Maasbracht–BE 3,289 → 2,717,
  Rilland–BE 2,080 → 1,718 MW. German ties unchanged.
- **Lower:** `scripts/24_tie_correction_variant.py` (suffix `-tiefix`). Belgian ties × 0.8261, German ties × 0.7974: Doetinchem 3,306 → 2,636,
  Hengelo 1,089 → 868, Maasbracht 3,415 → 2,724, Meeden 1,794 → 1,431 MW.
  Chosen over option A because it uses the same yardstick (full-grid N-1, script 23) and is built and checked. Option A would be a new,
  unvalidated limit method, expected to land close to this or stricter.

## 4. Full-grid check: model maximum (MW) and model / full grid

| Exchange | Case | Full grid | Base | Main | Lower |
|---|---|---|---|---|---|
| NL→BE | free | 5,300 | 6,416 (1.21) | 5,300 (1.00) | 5,300 (1.00) |
| NL→BE | reduced optimum as fixed shape | own | (1.25) | (1.03) | (1.03) |
| NL→BE | even | 5,041 | 6,213 (1.23) | 5,132 (1.02) | 5,132 (1.02) |
| NL→DE | free | 10,322 | 10,356 (1.00) | 10,356 (1.00) | 8,258 (0.80) |
| NL→DE | reduced optimum as fixed shape | own | (1.02) | (1.02) | (0.81) |
| NL→DE | even | 8,651 | 8,770 (1.01) | 8,770 (1.01) | 6,993 (0.81) |
| NL→BE+DE | free | 12,094 | 14,974 (1.24) | 14,040 (1.16) | 12,094 (1.00) |
| NL→BE+DE | reduced optimum as fixed shape | own | (1.44) | (1.25) | (1.19) |
| NL→BE+DE | even | 9,710 | 11,722 (1.21) | 11,372 (1.17) | 9,557 (0.98) |
| DE→BE transit | zone to zone | 5,929 | 6,040 (1.02) | 4,990 (0.84) | 4,990 (0.84) |
| DE→FR transit | zone to zone | 7,002 | 7,002 (1.00) | 7,002 (1.00) | 7,002 (1.00) |

Full grid with NL as one zone (spread over the Dutch 380 kV buses): BE 5,031, DE 8,561, BE+DE 9,868 MW. BE+DE was 9,157 before the
patch: Geertruidenberg–Krimpen bound in the even/zone cases.

## 5. 2025 test (2025 flows on the 2035 grid; only "hours over limit" is meaningful here)

Injections: `scripts/19b` on the 2035 node set (Tilburg keeps its own shares) → `runs/nlinj_sander-units2025-v29-vvltr2-2035-tennet-tlb3-rt4k-nlsander`.
Border statistics are identical in all three variants (reactances unchanged): mean r 0.909, MAE 0.394 GW over 19 borders.

| Network | Hours any branch over (SR2025 / even) | Hours a tie over (SR2025 / even) |
|---|---|---|
| Base | 32.3 % / 8.3 % | 3 / 1 |
| Main | 32.3 % / 8.3 % | 8 / 3 |
| Lower | 32.4 % / 8.8 % | 175 / 44 |
| Country network (rt4k), 10_test | 8.1 % | — |

The 32 % comes from Dutch internal branches with SR2025 keys (Bleiswijk–Wateringen above all; see docs/23). It is the same in every variant.

## 6. Reading

- **Main:** right on Belgian exchanges and on Germany. It stays about 16 % too generous when the Netherlands exports to both neighbours
  at once, and 16 % too strict on DE→BE transit.
- **Lower:** right on combined exchanges. It is 20 % too strict on NL→DE alone and 16 % too strict on transit, and real 2025 flows go
  over its tie limits in 44–175 h.
- Together they bracket the border room. Neither is right everywhere: per-tie limits cannot express one shared limit (docs/24).
