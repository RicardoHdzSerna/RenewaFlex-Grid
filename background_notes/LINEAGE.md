# Lineage of the grid workbook `inputs/derived/jao_core_v29`

The chain starts from a workbook, not from JAO's raw file, because the workbook carries months of documented corrections. The
raw file is in `inputs/raw/` for reference; every step from it to v29 is a numbered script in the archive
(`archive/dcopf/scripts/`) and is logged with dates and decisions in `archive/dcopf/notes/provenance.md`. In short:

| step | archived script | what it did | documented in |
|---|---|---|---|
| v1 | `10_build_enr_workbook.py` | JAO Core Static Grid Model (9th release, March 2026) → sheets Nodes, Lines, Tielines, Transformers, DCLines; ratings √3·k·Ī with k = 400 (380 kV) / 225 (220 kV) and Ī = mean of the listed seasonal currents; phase-shifter series reactances excluded (self-loop rule) | archive notes 01, 05, 06 |
| tie-lines | `66_fix_tieline_workbook.py`, `70_tieline_reactance_mixed.py` | tie-line rows listed by two operators matched and corrected (e.g. the Poland–Slovakia border) | archive replay2025 notes 05 |
| representatives, stations | `67_set_rep_buses_workbook.py`, `68_merge_stations_workbook.py` | the representative bus per zone (12 buses) set in the IsRepresentative column; station spellings merged | archive notes 08, 12 |
| v23 … v27 | `89_fix_workbook_phase_a.py` | four data fixes found in the line-by-line check against JAO's flow-based data | archive notes 14 (§ Phase A), replay2025 notes 14 |
| v28, v29 | `96_build_nl_patch_from_gridaware.py` + `97_apply_workbook_patch.py`; `99_build_nl_patch2.py` + `100_apply_workbook_patches.py` | the Dutch 380 kV elements missing from the JAO file (Randstad ring Beverwijk–Vijfhuizen–Bleiswijk, Bergum–Vierverlaten 220 kV, Maasbracht–Boxmeer–Dodewaard circuit, Borssele–Rilland circuit P), from GridAware's full network and TenneT's data; patches in `inputs/patches/jao2026_nl*` | docs/14 |
| v29-2035-amir, v29-2035-tennet | `111`, `112`, `113` | the Dutch 2035 grid from TenneT's IP2026 under two selection rules (patches in `inputs/patches/ip2026_nl_2035_*`) | docs/17, 18, 19 |
| v29-nl380 | `117` (here `12_nodal_workbook.py`) | every Dutch 380 kV bus flagged representative (nodal variant, step 3) | docs/21 |

Side branches that were tested and NOT adopted (archive): phase-shifter series reactance added (v30-pst, archive note 15),
seasonal ratings (v31, archive note 16). The base for everything is v29 (user decision 2026-10-16).
