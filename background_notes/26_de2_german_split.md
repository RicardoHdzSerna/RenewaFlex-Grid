# 26 — Germany split north/south (ACER DE2) (2026-10-25)

User: "build the German north/south split". Choices (2026-10-25): ACER DE2 zones; 2035 HVDC corridors from NEP + TYNDP, listed for
approval before use; grid + split keys (the dispatch session builds the Tulipa inputs). Not adopted; nothing existing changed.

## 1. Split

- **Source:** ACER Decision 11/2022, Annex VI, "Nodes to BZ - DE2 - German TSOs" (ModifiedSpectralP1). J1 = north, J2 = south.
- **Bus assignment:** the node names are model codes, so buses were matched by TSO (`scripts/29_de2_split_workbook.py`):
  - 50Hertz → north; Amprion (Emsland stations included) and TransnetBW → south;
  - TenneT → north from Voerden (51.81° N) upwards, south from Elsen (51.77° N) downwards (Hesse and Bavaria);
  - Niederlangen → south (ACER code NLAN; assumed to be Niederlangen);
  - every other German bus → the zone of most of its German neighbours.
  - Result: 109 German buses north and 215 south, the same in today's and the 2035 grid.
- **Representative buses** (nodes DE0N / DE0S):
  - north: WOLMIRSTEDT_380, the most central north 380 kV bus that is not a border station (electrical distance);
  - south: ROMMERSKIRCHEN_380, as before.
- **Ties to the Netherlands:** Meeden → north; Maasbracht, Doetinchem and Hengelo → south.

## 2. Split keys (`inputs/derived/de2_split_keys`, `scripts/31`)

- **Source:** ENTSO-E Bidding Zone Review 2025 output data (`inputs/external/entsoe_bzr_2025`).
- **Rule:** north share = north / (north + south) capacity of the same technology and vintage. Load uses the mean of three climate years.

| Item | North share | Item | North share |
|---|---|---|---|
| Load | 0.304 | Gas CCGT new | 0.294 |
| Wind onshore | 0.670 | Gas, all types | 0.300 |
| Wind offshore | 1.000 | Lignite new | 0.507 |
| Solar | 0.370 | Run-of-river | 0.057 |
| Battery | 0.308 | Pumped storage | 0.326 |

Every Tulipa DE00 asset is in `keys_tulipa_DE00.csv`, with its basis. Proxies are marked ASSUMED: rooftop PV, oil, electrolysers, hydrogen CCGT/OCGT and the heat-sector assets. These are 2025 target-year shares applied to 2035.

## 3. Full-grid check of the 2035 split network (`runs/fullgridcheck_2035rt4k-de2-*`, `scripts/23d`)

Model maximum (MW) and model / full grid:

| Exchange | Full grid | Base | Main (BE ×0.832, DE ×0.852) | Lower (BE ×0.832, DE ×0.664) |
|---|---|---|---|---|
| NL → BE | 5,300 | 6,370 (1.20) | 5,300 (1.00) | 5,300 (1.00) |
| NL → DE | 10,397 | 12,207 (1.17) | 10,397 (1.00) | 8,108 (0.78) |
| NL → BE + DE | 12,096 | 16,846 (1.39) | 14,242 (1.18) | 12,096 (1.00) |
| DE → BE transit | 5,984 | 6,056 (1.01) | 5,040 (0.84) | 5,040 (0.84) |
| DE north → south transit | 15,119 | 15,119 (1.00) | 12,877 (0.85) | 10,042 (0.66) |

- **Why the base allows more than before the split:** the Meeden–north tie gets 3,489 MW, against 1,794 MW to the one-node Germany.
- **Side effect of the corrections:** cutting the Dutch ties also cuts Germany's own north–south transfer, because part of it runs through the Netherlands.

## 4. 2025 test on today's grid (SR2025 units + German split injections, `scripts/30`, `10n3`)

| | One German node | DE2 split |
|---|---|---|
| Mean hourly r (19 borders) / MAE | 0.909 / 0.392 GW | 0.902 / 0.435 GW |
| BE–NL bias / MAE | +0.68 / 0.73 GW | +0.54 / 0.62 GW |
| AT–CZ MAE | 0.36 | 0.79 |
| AT–DE MAE | 0.50 | 0.93 |
| CZ–DE MAE | 0.40 | 0.57 |
| CZ–PL MAE | 0.37 | 0.55 |
| Hours with a non-Dutch branch over its limit | 8.4 % | 30.5 % (SK–CZ 19 %, CZ–north 14 %, north–south 10 %) |

- **North surplus:** the north node exports about 10.8 GW on average.
- **What the split fixes:** part of the Belgium–Netherlands bias; it falls by 0.14 GW. The full-grid "wind in the north" proxy (docs/23) removed it entirely.
- **What it breaks:** much of the north surplus now goes south through Poland and Czechia instead of through Germany. AT–CZ, AT–DE, CZ–DE and CZ–PL get much worse, as in the archived DE2 test of 6 October.
- **Candidate cause, not checked:** the north representative (Wolmirstedt, east) and the one-bus Czech and Polish nodes.

## 5. German HVDC corridors expected by 2035 (research of 2026-10-25; for approval, not yet used)

Every system is 2 GW unless noted.

| NEP | Name | From (zone) → To (zone) | Expected | Status (BNetzA, Oct 2026) |
|---|---|---|---|---|
| DC1 | A-Nord | Emden/Ost (N) → Osterath (S) | 2027 | under construction (TYNDP24: 2,400 MW) |
| DC2 | Ultranet | Osterath (S) → Philippsburg (S) | 2026 | under construction; inside the south |
| DC3 | SuedLink | Brunsbüttel (N) → Großgartach (S) | 2028 | under construction |
| DC4 | SuedLink | Wilster/West (N) → Bergrheinfeld/West (S) | 2028 | under construction |
| DC5 | SuedOstLink | Wolmirstedt (N) → Isar (S) | 2027 | under construction |
| DC20 | SuedOstLink+ | Mühlenbeck (N) → Isar (S) | 2032 (NEP23: 2030) | partly permitted |
| DC21b | Korridor B | Wilhelmshaven (N) → Lippetal/Welver/Hamm (S) | 2032 | in permitting |
| DC25 | Korridor B | Heide/West (N) → Polsum (S) | 2033 (NEP23/TYNDP24: 2032) | in permitting |
| DC34 | Rhein-Main-Link | Großenmeer (N) → Bürstadt (S) | 2033 | in permitting |
| DC35 | Rhein-Main-Link | Großenmeer (N) → Marxheim (S) | 2035 | in permitting |
| DC31 / DC32 | NordOstLink | inside the north | 2032 / 2034 | in permitting |
| DC42 | SuedWestLink | Sahms/Nord (N) → Jettingen (S) | **2037** | planned |
| DC40 / DC41 | — | — | 2037 (NEP23 only) | missing from NEP 2025 |

By the end of 2035: 9 north → south systems (DC1, 3, 4, 5, 20, 21b, 25, 34, 35), **18 GW**. DC2 lies inside the south and DC31/DC32 inside the north, so none of those three cross the split.

Sources:
- netzausbau.de project pages (`https://www.netzausbau.de/Vorhaben/ansicht/de.html?nummer=<N>&gruppe=bbplg`);
- NEP 2037/2045 (2025) project profiles (netzentwicklungsplan.de project library, 19.05.2026) and NEP 2037/2045 (2023), 2nd draft (confirmed by BNetzA on 01.03.2024);
- ENTSO-E TYNDP 2024 project data (tyndp2024.entsoe.eu API, projects 132, 254, 235, 130, 1034, 1229);
- Amprion project pages.

Conflicts between sources: the A-Nord capacity, the DC20 and DC25 dates, stale TYNDP24 statuses, and station names that changed (Klein Rogahn → Mühlenbeck, Ovelgönne → Großenmeer).

## 6. Placement check (2026-10-25, user: "approve the HVDC list and run option 1")

HVDC list approved → `inputs/derived/de2_hvdc_2035/hvdc_de2_2035.csv` (9 systems in the 2035 model, 18,000 MW, DE0N -> DE0S).

`scripts/32_de2_placement_check_2025.py` → `runs/placecheck_de2-today`. The 2025 split-test injections (Dutch nodes, DE0N, DE0S, other zones)
are re-routed on the FULL grid of today's DE2 reduction run, with only the placement inside the zones changed. It is compared with the
one-German-node placement check (`runs/placecheck_nodal-sander-units2025`, scripts/21). All figures are full grid, 2025, GW.

| Placement | One German node: MAE 19 / BE–NL bias | DE2 split: MAE 19 / BE–NL bias |
|---|---|---|
| Every zone at one bus (what the reduced network does) | 0.386 / +0.66 | 0.460 / +0.97 |
| Germany (or each half) spread over its 380 kV stations | 0.377 / +0.62 | **0.333 / +0.23** |
| + every other zone spread | 0.310 / +0.56 | **0.275 / +0.16** |
| German wind north (assumed proxy) + rest spread | 0.337 / +0.06 | 0.321 / +0.11 |
| same + other zones spread | 0.283 / −0.01 | **0.266 / +0.04** |

The reduced DE2 network itself (10n3) scores 0.435 / +0.54.

Reading:
1. **The split is only as good as the placement of its halves.** With each half at one bus (Wolmirstedt, Rommerskirchen) the split is worse
   than one German node. Spread over their own stations, the split beats every one-node placement, and the best result without any
   assumed wind proxy is 0.275 GW (all zones spread).
2. **The weak point is the reduction, not the split.** The reduced networks route each zone as if all its power entered at one bus. The
   N-1 limits, by contrast, already assume an even spread over the zone's 380 kV buses (04/04n). Routing and limits therefore assume
   different injection patterns.
3. **The eastern borders improve only when the other zones are spread too** (AT–CZ 0.64 → 0.42 GW): Czechia and Poland at one bus each
   cause the eastern detour.
4. **Proposal, not built:** fit the reduced network's reactances to zonal PTDFs with the injection spread over each zone's 380 kV buses
   (the same assumption as the limits), instead of to one-bus Kron PTDFs.

## Open idea (user, 2026-10-25, not now)

Tune choices on 2025 (representative buses, keys) and test them out-of-sample on 2024, so a fitted choice is not judged on the data it was fitted to.
