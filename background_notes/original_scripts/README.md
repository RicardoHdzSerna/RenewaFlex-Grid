# The scripts exactly as they were run

These are the scripts of `core_grid_dcopf/scripts/` that built the five 2035 networks in use, unchanged, plus
`run_all_as_verified.sh`, the driver used on 3 November 2026 to rerun them inside this package (with the v29 workbook and the
same inputs). That rerun gave the five networks of `reference_outputs/networks/` with zero difference in every limit and reactance.

You do not need these to work: `pipeline/scripts/` has the same code under step names (A1 … C2) with plain headers. The table in
`HANDOVER.md`, Appendix A, maps old names to new ones. To run these originals in a fresh copy of the package: copy the `.py`/`.jl` files to `pipeline/scripts/` and
`run_all_as_verified.sh` to `pipeline/`, copy `reference_outputs/original_patches/ip2026_nl_2035_tennet` to
`pipeline/inputs/patches/` (that driver applies the stored patch instead of building it), then run `bash run_all_as_verified.sh`.

Not included: the scripts from JAO's raw file to the v29 workbook, and the original 2035 patch builder (archive numbers 10,
66–100, 111–113). They were in `~/TNO/TestTulipa_TYNDP2026 - MAIN/archive/`, which is empty now.
