#!/bin/bash
# run_all_hv.sh — FIRST VERSION: the 2035 network with the Dutch 150/110 kV grid added (HANDOVER.md section 9).
#
#   bash run_all.sh        first (builds the 2035 workbook v29-vvltr2-2035-tennet-tlb3-rt4k)
#   bash run_all_hv.sh     then this (about 20 minutes)
#
# Steps: H1 run the IP26 project matching code (hv_ip26/) with the 2035 horizon; A8 + A5 add its 150/110 kV grid to the 2035
# workbook; A7 the 32 SR2025 nodes; B1-B5 and C1-C2 as in run_all.sh (one German node, main tie correction).
# The IP26 code needs pyyaml (pip install pyyaml) besides pandas and openpyxl.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python3}
JL=${JL:-"julia --threads=4,0"}
D=${D:-$(date +%F)}
mkdir -p runs logs
say() { echo; echo "=== $* ($(date +%T))"; }

say "H1 IP26 project matching code, horizons 2030, 2035, 2040 (study phase left out, last year of the window counts)"
NET35=hv_ip26/output_final_csv/median/full_network_final_median_2035/network.csv
if [ ! -f $NET35 ]; then
  (cd hv_ip26 && $PY -W ignore ip26_network_scenarios.py all && $PY -W ignore ip26_horizon_filter.py \
     && $PY -W ignore ip26_final_network.py && $PY -W ignore ip26_excel_to_csv.py) > logs/H1_ip26.log 2>&1
fi

V0=v29-vvltr2-2035-tennet-tlb3-rt4k
V=$V0-hv
say "A8 the 150/110 kV grid of 2035 as a patch, applied to $V0"
[ -d inputs/patches/hv_150_110_2035 ] || $PY scripts/A8_build_patch_hv_150_110.py $NET35 $V0 hv_150_110_2035
[ -d inputs/derived/jao_core_$V ] || $PY -W ignore scripts/A5_apply_patches.py $V0 $V inputs/patches/hv_150_110_2035
say "A7 the 32 SR2025 nodes"
[ -d inputs/derived/jao_core_$V-nlsander ] || $PY -W ignore scripts/A7_set_dutch_nodes.py $V $V-nlsander inputs/nodesets/nl_ielgas_sander_32.csv

NV=$V-nlsander; T=$NV-hv
RED_N="runs/${D}-stage2-${NV}-LP-virtual"; RED_C="runs/${D}-stage2-${V}-LP-virtual"
say "B1 Kron reduction"
[ -d "$RED_N" ] || DERIVED_VERSION="$NV" REP_NODE_MODE=manual_excel MIQP_CAP_S=1800 $JL scripts/B1_reduce.jl "${D}-stage2-${NV}-LP-virtual" LP virtual > logs/B1_${NV}.log 2>&1
grep -q COMPLETED "$RED_N/manifest.md"
[ -d "$RED_C" ] || DERIVED_VERSION="$V" REP_NODE_MODE=manual_excel MIQP_CAP_S=1800 $JL scripts/B1_reduce.jl "${D}-stage2-${V}-LP-virtual" LP virtual > logs/B1_${V}.log 2>&1
grep -q COMPLETED "$RED_C/manifest.md"
say "B2, B3 reduced network, monitored lines (unchanged rule: 380 kV and Dutch 220 kV lines of at least 1 km; 150/110 kV carry flow and can fail, but do not set a limit)"
[ -d inputs/derived/diag_fixedpos_${T}-sparse-LP ] || $PY -W ignore scripts/B2_network_nodal.py "$RED_N" "${T}-sparse-LP" > logs/B2_${T}.log
[ -d "runs/${D}-monitored-380kv-ge1km-${V}" ] || $PY -W ignore scripts/B3_monitored_lines.py "$V" > logs/B3_${V}.log
MON="runs/${D}-monitored-380kv-ge1km-${V}"; MONN="runs/${D}-monitored-nodal-nl220-${NV}"
[ -d "$MONN" ] || $PY -W ignore scripts/B3_monitored_lines_nodal.py "$MON" "inputs/derived/jao_core_${NV}" "${D}-monitored-nodal-nl220-${NV}" > logs/B3n_${NV}.log
MONOPT="--monitored=eic:$MONN/monitored_eics.csv"; NAME=n1-380kv-nl220-ge1km-nodal
say "B4, B5 TTCs: N-1, then phase shifters + 10 % margin"
# the self-check that recomputes the reduced network from the full grid agrees to 3e-6 here (1e-6 is the default tolerance)
export REPRO_TOL=1e-5
[ -d "runs/${D}-limits-nodal-${T}-${NAME}" ] || $PY -W ignore scripts/B4_limits_n1_nodal.py "$RED_N" "$T" "$NAME" "$MONOPT" > logs/B4_${T}.log 2>&1
[ -d "runs/${D}-limits-nodal-${T}-${NAME}-pst-frm10" ] || $PY -W ignore scripts/B5_limits_pst_margin_nodal.py "$RED_N" "$T" "${NAME}-pst-frm10" "runs/${D}-limits-nodal-${T}-${NAME}" \
    "--neutral-name=${NAME}-frm10" --margin=0.10 "$MONOPT" > logs/B5_${T}.log 2>&1
say "C1, C2 border-tie correction (Belgian ties, as the main network)"
N1=inputs/derived/diag_fixedpos_${T}-sparse-LP-${NAME}-pst-frm10
[ -d runs/fullgridcheck_2035rt4k-hv-base ] || $PY -W ignore scripts/C1_full_grid_border_check.py $N1 runs/${D}-limits-nodal-${T}-${NAME}-pst-frm10 2035rt4k-hv-base > logs/C1_hv.log 2>&1
[ -d $N1-tiefixbe ] || $PY -W ignore scripts/C2_tie_correction.py $N1 runs/fullgridcheck_2035rt4k-hv-base tiefixbe beonly > logs/C2_hv.log 2>&1
say "outputs: the final networks copied under short names to outputs/ (full names: ../reference_outputs/NETWORK_NAMES.csv)"
mkdir -p outputs
tail -n +2 ../reference_outputs/NETWORK_NAMES.csv | while IFS=, read -r short full rest; do
  [ -d "inputs/derived/$full" ] && [ ! -d "outputs/$short" ] && cp -R "inputs/derived/$full" "outputs/$short" && echo "  outputs/$short"
done
say "done: $N1-tiefixbe"
