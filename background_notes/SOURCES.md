# Data in `inputs/` — where it comes from and what may be shared

| folder | content | source | sharing |
|---|---|---|---|
| `inputs/raw/` | JAO Core Static Grid Model, 9th release (March 2026): the published workbook, its web page, the handbook | JAO publication tool, downloaded 2026-06-05 | JAO publication data: check JAO's terms before redistributing; it is the primary input of the whole chain |
| `inputs/derived/jao_core_v29/` | the grid workbook the chain reads (nodes, lines, tie-lines, transformers, DC lines; ratings √3·k·Ī). Built from `inputs/raw/` by the archived scripts (see LINEAGE.md) | derived here | same terms as the raw file |
| `inputs/derived/jao_core_v29-2035-amir/`, `…-tennet/` | the Dutch 2035 grids (TenneT IP2026 projects applied to v29 under two selection rules; docs/18, docs/19) | derived here | same |
| `inputs/patches/` | the Dutch patches (GridAware / TenneT data) and the IP2026 2035 decision table and patches, as applied to the workbook | derived here from GridAware's full network and TenneT's IP2026 | derived data; sources named in each patch's CHANGELOG |
| `inputs/pst_inventory/` | phase-shifter corridors, ranges and capability, derived from the JAO workbook (archived script 74; report.md explains) | derived here | same terms as the raw file |
| `inputs/monitored/` | the monitored line sets (EIC lists): 380 kV lines of at least 1 km, and the nodal addition | derived here (03_monitored_set.py, 03n) | derived |
| `inputs/tulipa_baseline/2035_v2/` | the TYNDP-2026 2035 Tulipa input folder (baseline v2, Poland fixed) the Tulipa builder copies from; read-only | the TYNDP-26-to-Tulipa pipeline (frozen baseline) | internal project data |
| `inputs/validation_2025/` | measured 2025 hourly cross-border physical flows (ENTSO-E Transparency Platform) and JAO Core net positions (JAO publication tool); the manifest of the fetch is next to them | archived script 60, fetched 2026-09-25 | ENTSO-E: public with attribution; JAO: analysis only, check the terms before redistributing. Validation data: compared against, never an input |

No credentials are stored anywhere in this folder. The ENTSO-E API token the archived fetch script used lives only in the
environment variable `ENTSOE_API_KEY`.
