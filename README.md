# Dutch 2035 grid model: handover package

Start with **`HANDOVER.md`** (also as `HANDOVER.docx`). `CHECK_REQUEST.md` is the note for checking the 150/110 kV step. It explains what was built, why, from which sources, what is assumed
and what is still open. The figure `figures/chain_overview.png` shows the whole chain on one page.

| folder | what it is |
|---|---|
| `pipeline/` | code + input data; `bash pipeline/run_all.sh` rebuilds the five 2035 networks from the 2026 workbook (about 15 min) |
| `pipeline/scripts/` | one script per step, named by step (A1 … C2); each starts with a plain explanation of what it does |
| `pipeline/inputs/` | the starting workbook (`derived/jao_core_v29`), the patches with their sources, SR2025 node list, phase-shifter data, ACER's German split |
| `reference_outputs/` | the five networks the RenewaFLEX runs use, and the original 2035 patches, to compare a rebuild against |
| `pipeline/hv_ip26/`, `pipeline/run_all_hv.sh` | first version with the 150/110 kV grid added, using the IP26 project matching code (HANDOVER.md section 9); result in `reference_outputs/networks/hv_nodal_main` and `reference_outputs/hv_150_110/` |
| `sources/` | the original documents and data from outside (JAO, GridAware, TenneT IP2026 and Tilburg, ACER, SR2025, the IP26 project matching) |
| `background_notes/` | the working notes of the grid project, maps, and the scripts exactly as they were run (`original_scripts/`) |

Made 3 November 2026 from the folders `core_grid_dcopf/` and `grid_inputs_2035_all-variants/` of the RenewaFLEX project.
JAO's data may be used for analysis; check JAO's terms before passing it outside the project.
