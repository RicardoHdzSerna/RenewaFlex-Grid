# 2026-10-16 — The Niederlangen tee stub and the monitored set

User: "check the niederlangen stub first, then start step 3". Result in one line: the stub distorts the N-1 limits computed
WITHOUT phase shifters (five Dutch pair limits, three branch limits, 6.6 points of the 2025 test), and leaves option 3 — the
limit set Tulipa uses — unchanged to within 1.2 % on 4 of 66 pairs, with the 2025 test and the MaxBEX comparison identical.

## 1. The stub

`NIEDERLANGEN_380 – Y-NIEDERLANGEN_380`, EIC 11T0-0000-0991-I: the 0.33 km tee connection of Niederlangen onto the
Meeden–Diele / Dörpen West corridor, carried in the JAO static grid model with a FIXED current of 650 A, i.e. 450 MW
(√3 · 400 kV · 0.65 kA). In the N-1 limit sets of script 83 (monitored = every line with both ends at 380 kV) it sets the
pair limits of AT–NL, CZ–NL, DE–NL, FR–NL and HU–NL, each under the outage of Meppen–Dörpen West (11T0-0000-2116-Q): a
0.33 km stub rated at a fifth of its legs caps five Dutch pairs. In JAO's final-computation files (script 87, three business
days) the stub never appears as a monitored element (0 CNE rows) while its legs are monitored at 2,506–2,955 A; JAO does use
it as an outage element (444 contingency rows). So the stub is in the grid and in the outage list, but no TSO lets it limit
a transfer.

## 2. Test: monitored set = 380 kV lines of at least 1 km

`runs/2026-10-16-monitored-380kv-ge1km/`: rule "both ends at 380 kV and Length_km >= 1" keeps 1,368 EICs (1,370 rows)
and excludes 60 rows (`excluded_stubs.csv`: tee stubs "Y-…", station jumpers, offshore landing circuits such as
Borssele–Zeeuwse Kust 0.11–0.35 km; 55 Lines, 5 Tielines). The excluded rows stay in the grid and in the outage list.
Chain, all on v29: 83 `--monitored=eic:…` → `runs/2026-10-16-limits-v29-n1-380kv-ge1km`; 115 (copy of 93 with a
`--monitored=` option; 93 asserts the "380kv" rule of the 83 run) → `runs/2026-10-16-limits-v29-n1-380kv-ge1km-pst-frm10`;
replay2025/53 on the three networks `diag_fixedpos_v29-sparse-LP-n1-380kv-ge1km[-pst-frm10|-frm10]`; 94 →
`runs/2026-10-16-ttc-vs-maxbex-v29-ge1km`. Log `notes/ttc_pst_frm10_v29_ge1km_2026-10-16.log`.

### N-1 limits without phase shifters (83)

| pair | all 380 kV lines monitored | 380 kV lines >= 1 km | set by (>= 1 km) |
|---|---|---|---|
| AT–NL | 4,309 | 6,855 | Diele–Meeden, outage of the other Meeden–Diele circuit |
| CZ–NL | 4,344 | 5,195 | Hradec Východ–Röhrsdorf, outage of the parallel circuit |
| DE–NL | 4,477 | 6,672 | Diele–Meeden, as AT–NL |
| FR–NL | 4,742 | 6,907 | Geertruidenberg–Krimpen, outage of the parallel circuit |
| HU–NL | 4,354 | 4,557 | Nosovice–Varin, outage of P. Biskupice–Stupava |
| BE–NL | 3,720 | 3,720 | Maasbracht–Van Eyck (unchanged) |
| other 60 pairs | unchanged | unchanged | |

N-1 branch limits (LP envelope, MW): BE–DE 1,814 → 2,007; BE–NL 2,658 → 3,740; DE–NL 2,826 → 4,327; the other 16 unchanged.
2025 fixed-position test, hours with every branch inside its limit: 88.8 % → 95.4 %.

### Option 3 (N-1 + phase shifters set per exchange + 10 % margin; what Tulipa uses)

| | all 380 kV lines | >= 1 km |
|---|---|---|
| pair limits that move | — | BE–NL 5,000 → 5,015; FR–NL 6,892 → 6,974; AT–BE 5,662 → 5,677; BE–CZ 5,612 → 5,626 (4 of 66, <= 1.2 %) |
| AT–NL, DE–NL pair limits | 6,550 / 8,551 | 6,550 / 8,551 (identical to 0.1 MW) |
| branch limits that move | — | BE–DE 2,941 → 2,949; BE–NL 3,732 → 3,777 (2 of 19); DE–NL 5,398 both |
| 2025 test, hours inside | 91.7 % | 91.7 % |
| MaxBEX: median ours / JAO; below 10 % / inside / above 90 % | 1.09; 23 / 38 / 39 % | 1.09; 23 / 38 / 39 % |

Routing is unchanged by construction (reactances untouched: r = 0.895 over 18 borders, MAE 0.387 GW over 19). The N-1 set
with the 10 % margin but WITHOUT phase shifters (`…-ge1km-frm10`) gives 83.7 % — information only, no v29 counterpart run.

## 3. Reading

With the angles at zero the stub is the binding element of five Dutch pairs. Once the phase shifters are set per exchange
(Meeden–Diele, Gronau–Hengelo, Van Eyck–Maasbracht, Zandvliet–Rilland, …) the flow is steered off the Meeden–Diele corridor
and the stub never binds: the AT–NL and DE–NL option-3 limits are the same MW with or without it (the optimiser finds
different angle sets — Meeden–Diele 1.5° vs 4.8° for AT–NL — with the same limit: several optima). The sets that the stub
does distort are the no-PST N-1 numbers quoted in notes 16 and 19 and in the process PDF; option 3 and the Tulipa folder
built from it are not affected beyond 1.2 % on two branches.

## 4. Proposal (user decision)

**Decided (user, 2026-10-16: "ok adopt the 1 km rule, keep v29 as is"): points 1 and 2 as proposed.** The rule applies from step 3
on (nodal network: with the spur-row addition of scripts/119, note 21 §5); v29 option 3 and its Tulipa folder are unchanged.

1. Adopt "380 kV lines of at least 1 km" as the monitored rule from now on: JAO monitors neither the stub nor the other
   sub-kilometre rows, and a tee stub with a placeholder rating is not a transfer-capacity element. The 1 km threshold is a
   proxy (the 60 excluded rows are listed); the alternative "exactly JAO's monitored elements" (83 `--monitored=eic:` with
   script 84's list) remains available.
2. Keep the current v29 option 3 and its Tulipa folder as they are (the change is <= 1.2 % on BE–DE and BE–NL; user:
   "lets not fuck what we have"). The rule is applied in step 3, whose limit step is rebuilt anyway. If full consistency is
   preferred, rebuilding option 3 and the Tulipa folder with the >= 1 km rule is the 73 / 31 / 32 chain (minutes).
3. Replace the no-PST N-1 numbers in notes 16/19 by the >= 1 km ones only if they are used further; they are sensitivities.

## Folders

`runs/2026-10-16-monitored-380kv-ge1km`, `runs/2026-10-16-limits-v29-n1-380kv-ge1km`, `runs/2026-10-16-limits-v29-n1-380kv-ge1km-pst-frm10`,
`inputs/derived/diag_fixedpos_v29-sparse-LP-n1-380kv-ge1km{,-pst-frm10,-frm10}`, `replay2025/runs/fixedposdc_diag_fixedpos_v29-sparse-LP-n1-380kv-ge1km*_single`,
`runs/2026-10-16-ttc-vs-maxbex-v29-ge1km`. Two empty folders from a first launch whose output was swallowed are kept as
`…_ABORTED-empty-no-manifest` (53 and 94 were rerun; the reruns are the folders above). Scripts: 115 (new), 83/53/94 unchanged.
