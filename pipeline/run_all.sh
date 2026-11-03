#!/bin/bash
# run_all.sh — rebuild the five 2035 grid networks from the 2026 workbook v29, inside this folder.
#
#   bash run_all.sh                 about 15 minutes; then:  python scripts/verify_against_reference.py
#
# Needs Python 3.9 with environment/requirements.txt and Julia 1.12 with Project.toml / Manifest.toml (see ../HANDOVER.md §6).
# Set PY=... or JL=... to use another Python or Julia. Steps A and C skip their work if the output exists; B reruns unless its run
# folders exist, which are named by date: to resume on another day, set D=<date of the first run>. Labels = script names (A1 ... C2)
# with the HANDOVER.md section in brackets.
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python3}
JL=${JL:-"julia --threads=4,0"}
D=${D:-$(date +%F)}                 # run folders are named by date, as in the grid project
mkdir -p runs logs
say() { echo; echo "=== $* ($(date +%T))"; }

# ============================================================ A. the grid workbook: from the 2026 grid to the 2035 grid
say "A1 (2.3) assumed Vierverlaten 380/220 kV transformer, 2 units, on v29"
[ -d inputs/patches/nl_vierverlaten_tr_assumed_2u ] || $PY scripts/A1_build_patch_vierverlaten_transformer.py v29 --units=2
[ -d inputs/derived/jao_core_v29-vvltr2 ] || $PY -W ignore scripts/A5_apply_patches.py v29 v29-vvltr2 inputs/patches/nl_vierverlaten_tr_assumed_2u

say "A2 (2.4) THE 2035 LINES: IP2026 projects (TenneT rule) from the decision table"
[ -d inputs/patches/ip2026_nl_2035_tennet ] || $PY scripts/A2_build_patch_from_decisions.py inputs/patches/ip2026_nl_2035_decisions tennet v29 ip2026_nl_2035_tennet
[ -d inputs/patches/ip2026_nl_2035_project ] || $PY scripts/A2_build_patch_from_decisions.py inputs/patches/ip2026_nl_2035_decisions project v29 ip2026_nl_2035_project   # our rule (realisation + preparation), built for reference, not used below
#    v29 + 2035 projects: only needed as the base the Tilburg patch is built on
[ -d inputs/derived/jao_core_v29-2035-tennet ] || $PY -W ignore scripts/A5_apply_patches.py v29 v29-2035-tennet inputs/patches/ip2026_nl_2035_tennet

say "A3 (2.5) Tilburg looped into Geertruidenberg-Eindhoven, all 3 circuits"
[ -d inputs/patches/ip2026_nl_2035_tilburg_loopin_3c ] || $PY scripts/A3_build_patch_tilburg_loopin.py v29-2035-tennet --circuits=3
[ -d inputs/derived/jao_core_v29-vvltr2-2035-tennet-tlb3 ] || $PY -W ignore scripts/A5_apply_patches.py v29-vvltr2 v29-vvltr2-2035-tennet-tlb3 \
    inputs/patches/ip2026_nl_2035_tennet inputs/patches/ip2026_nl_2035_tilburg_loopin_3c

say "A4 (2.6) 4,000 A on Krimpen-Geertruidenberg and Maasbracht-Eindhoven"
[ -d inputs/patches/ip2026_nl_2035_rating_4ka ] || $PY scripts/A4_build_patch_rating_4ka.py v29-vvltr2-2035-tennet-tlb3 ip2026_nl_2035_rating_4ka
V=v29-vvltr2-2035-tennet-tlb3-rt4k           # the 2035 workbook
[ -d inputs/derived/jao_core_$V ] || $PY -W ignore scripts/A5_apply_patches.py v29-vvltr2-2035-tennet-tlb3 $V inputs/patches/ip2026_nl_2035_rating_4ka

say "A6 (2.7) Germany split north/south (variant)"
[ -d inputs/derived/jao_core_$V-de2 ] || $PY -W ignore scripts/A6_split_germany.py $V $V-de2

say "A7 (2.8) SR2025 32 Dutch nodes"
for W in $V $V-de2; do
  [ -d inputs/derived/jao_core_$W-nlsander ] || $PY -W ignore scripts/A7_set_dutch_nodes.py $W $W-nlsander inputs/nodesets/nl_ielgas_sander_32.csv
done

# ============================================================ B. reduction and limits, for one workbook: nodal and country network
chain() {
  local V=$1 NV=$1-nlsander; local T=$NV-hv
  local RED_N="runs/${D}-stage2-${NV}-LP-virtual" RED_C="runs/${D}-stage2-${V}-LP-virtual"
  say "B1 (3.1) $NV and $V: Kron reduction"
  [ -d "$RED_N" ] || DERIVED_VERSION="$NV" REP_NODE_MODE=manual_excel MIQP_CAP_S=1800 $JL scripts/B1_reduce.jl "${D}-stage2-${NV}-LP-virtual" LP virtual > logs/B1_${NV}.log 2>&1
  grep -q COMPLETED "$RED_N/manifest.md"
  [ -d "$RED_C" ] || DERIVED_VERSION="$V" REP_NODE_MODE=manual_excel MIQP_CAP_S=1800 $JL scripts/B1_reduce.jl "${D}-stage2-${V}-LP-virtual" LP virtual > logs/B1_${V}.log 2>&1
  grep -q COMPLETED "$RED_C/manifest.md"

  say "B2, B3 (3.2, 3.3) $NV: reduced network, monitored lines"
  $PY -W ignore scripts/B2_network_nodal.py "$RED_N" "${T}-sparse-LP" > logs/B2_${T}.log
  $PY -W ignore scripts/B3_monitored_lines.py "$V" > logs/B3_${V}.log
  local MON="runs/${D}-monitored-380kv-ge1km-${V}" MONN="runs/${D}-monitored-nodal-nl220-${NV}"
  $PY -W ignore scripts/B3_monitored_lines_nodal.py "$MON" "inputs/derived/jao_core_${NV}" "${D}-monitored-nodal-nl220-${NV}" > logs/B3n_${NV}.log
  local MONOPT="--monitored=eic:$MONN/monitored_eics.csv" NAME=n1-380kv-nl220-ge1km-nodal

  say "B4, B5 (3.4) $NV: N-1 limits, then phase shifters + 10 % margin"
  $PY -W ignore scripts/B4_limits_n1_nodal.py "$RED_N" "$T" "$NAME" "$MONOPT" > logs/B4_${T}.log 2>&1
  $PY -W ignore scripts/B5_limits_pst_margin_nodal.py "$RED_N" "$T" "${NAME}-pst-frm10" "runs/${D}-limits-nodal-${T}-${NAME}" \
      "--neutral-name=${NAME}-frm10" --margin=0.10 "$MONOPT" > logs/B5_${T}.log 2>&1

  say "B2, B4, B5 (4.4) $V: country network and its limits"
  $PY -W ignore scripts/B2_network_country.py "$RED_C" "${V}-sparse-LP" > logs/B2_${V}.log
  local CN=n1-380kv-nl220-ge1km
  $PY -W ignore scripts/B4_limits_n1_country.py "$RED_C" "$V" "$CN" "$MONOPT" > logs/B4_${V}.log 2>&1
  $PY -W ignore scripts/B5_limits_pst_margin_country.py "$RED_C" "$V" "${CN}-pst-frm10" "runs/${D}-limits-${V}-${CN}" \
      "--neutral-name=${CN}-frm10" --margin=0.10 "$MONOPT" > logs/B5_${V}.log 2>&1
}
chain $V
chain $V-de2

# ============================================================ C. border-tie correction of the nodal networks (4.1)
NET=n1-380kv-nl220-ge1km-nodal-pst-frm10; NAME=n1-380kv-nl220-ge1km-nodal
say "C1, C2 one German node: full-grid check, then main (Belgian ties) and lower (Belgian and German ties)"
N1=inputs/derived/diag_fixedpos_${V}-nlsander-hv-sparse-LP-$NET
[ -d runs/fullgridcheck_2035rt4k-base ] || $PY -W ignore scripts/C1_full_grid_border_check.py $N1 runs/${D}-limits-nodal-${V}-nlsander-hv-$NAME-pst-frm10 2035rt4k-base > logs/C1_base.log 2>&1
[ -d $N1-tiefixbe ] || $PY -W ignore scripts/C2_tie_correction.py $N1 runs/fullgridcheck_2035rt4k-base tiefixbe beonly > logs/C2_tiefixbe.log 2>&1
[ -d $N1-tiefix ] || $PY -W ignore scripts/C2_tie_correction.py $N1 runs/fullgridcheck_2035rt4k-base tiefix lower > logs/C2_tiefix.log 2>&1

say "C1, C2 Germany split: full-grid check, then main"
N2=inputs/derived/diag_fixedpos_${V}-de2-nlsander-hv-sparse-LP-$NET
[ -d runs/fullgridcheck_2035rt4k-de2-base ] || $PY -W ignore scripts/C1_full_grid_border_check.py $N2 runs/${D}-limits-nodal-${V}-de2-nlsander-hv-$NAME-pst-frm10 2035rt4k-de2-base > logs/C1_de2.log 2>&1
[ -d $N2-tiefixmain ] || $PY -W ignore scripts/C2_tie_correction.py $N2 runs/fullgridcheck_2035rt4k-de2-base tiefixmain main > logs/C2_tiefixmain.log 2>&1

say "outputs: the final networks copied under short names to outputs/ (full names: ../reference_outputs/NETWORK_NAMES.csv)"
mkdir -p outputs
tail -n +2 ../reference_outputs/NETWORK_NAMES.csv | while IFS=, read -r short full rest; do
  [ -d "inputs/derived/$full" ] && [ ! -d "outputs/$short" ] && cp -R "inputs/derived/$full" "outputs/$short" && echo "  outputs/$short"
done
say "done: compare with the networks in use"
$PY scripts/verify_against_reference.py
