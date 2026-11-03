# Node sets for the nodal Netherlands

`nl_ielgas_sander_32.csv` (2026-10-19): the 32 Dutch electricity nodes of SR2025 SR2025-to-Tulipa / I-ELGAS network (sheet
`Inputs I-ELGAS DE` of `Electricity Trading Capacities I-ELGAS.xlsx`, every `E-xxx` endpoint), mapped to the JAO bus of the same
station (name reading, checked against JAO lines: 34 of his 37 internal links are JAO lines; `../../../nl_merge/D0_nodes_vs_JAO_check.md`).
Stations with 380 and 220 kV (Eemshaven, Ens, Meeden, Vierverlaten) use the 380 kV bus. Five nodes are 220 kV-only JAO buses
(Bergum, Louwsmeer, Oudehaske, Zeyerveen, Weiwerd). Not in his set: Breukelen, Hessenweg (not a node in his grid), the landing
spurs. User 2026-10-19: the reference (network) nodes must be the nodes the demand/supply keys exist for.

`nl_ielgas_sander_31_today.csv` (2026-10-23): SR2025 node set for TODAY's grid (v29-vvltr2, 2025 validation): the 32 nodes minus
E-TIL (TILBURG_380 exists only in the 2035 grids, with the loop-in from 2027). In the 2025 injections Tilburg's keys go to
Geertruidenberg (nearest 380 kV station on the Geertruidenberg–Eindhoven line the loop-in cuts). Assumption, labelled.
