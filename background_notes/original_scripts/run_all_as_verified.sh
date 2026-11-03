#!/bin/bash
# Rebuild the 2035 grid networks from the v29 workbook, inside this folder.
# Usage (from pipeline/, with these scripts copied to pipeline/scripts/):  bash run_all_as_verified.sh
set -euo pipefail
cd "$(dirname "$0")"
PY=${PY:-python3}
JL=${JL:-"julia --project=. --threads=4,0"}
D=$(date +%F)
mkdir -p runs logs

say() { echo; echo "=== $* ($(date +%T))"; }

# ---------------------------------------------------------------- A. grid workbook: 2026 grid -> 2035 grid
say "A1 assumed Vierverlaten 380/220 kV transformer (2 units) on v29"
[ -d inputs/patches/nl_vierverlaten_tr_assumed_2u ] || $PY scripts/14_build_patch_vierverlaten_tr.py v29 --units=2
[ -d inputs/derived/jao_core_v29-vvltr2 ] || $PY -W ignore scripts/13_apply_patches.py v29 v29-vvltr2 inputs/patches/nl_vierverlaten_tr_assumed_2u

say "A2 IP2026 2035 projects (TenneT rule) on v29, needed as the base the Tilburg patch is built on"
[ -d inputs/derived/jao_core_v29-2035-tennet ] || $PY -W ignore scripts/17_apply_patches_modify_remove.py v29 v29-2035-tennet inputs/patches/ip2026_nl_2035_tennet
[ -d inputs/patches/ip2026_nl_2035_tilburg_loopin_3c ] || $PY scripts/16_build_patch_tilburg_loopin.py v29-2035-tennet --circuits=3

say "A3 2035 projects + Tilburg loop-in on v29-vvltr2"
[ -d inputs/derived/jao_core_v29-vvltr2-2035-tennet-tlb3 ] || $PY -W ignore scripts/17_apply_patches_modify_remove.py v29-vvltr2 v29-vvltr2-2035-tennet-tlb3 inputs/patches/ip2026_nl_2035_tennet inputs/patches/ip2026_nl_2035_tilburg_loopin_3c

say "A4 4 kA ratings Krimpen-Geertruidenberg and Maasbracht-Eindhoven"
[ -d inputs/patches/ip2026_nl_2035_rating_4ka ] || $PY scripts/25_build_patch_rating_4ka.py v29-vvltr2-2035-tennet-tlb3 ip2026_nl_2035_rating_4ka
V=v29-vvltr2-2035-tennet-tlb3-rt4k
[ -d inputs/derived/jao_core_$V ] || $PY -W ignore scripts/17_apply_patches_modify_remove.py v29-vvltr2-2035-tennet-tlb3 $V inputs/patches/ip2026_nl_2035_rating_4ka

say "A5 Germany split north/south (ACER DE2)"
[ -d inputs/derived/jao_core_$V-de2 ] || $PY -W ignore scripts/29_de2_split_workbook.py $V $V-de2

say "A6 SR2025 32 Dutch nodes as network nodes"
for W in $V $V-de2; do
  [ -d inputs/derived/jao_core_$W-nlsander ] || $PY -W ignore scripts/18_nodal_workbook_nodeset.py $W $W-nlsander inputs/nodesets/nl_ielgas_sander_32.csv
done

# ---------------------------------------------------------------- B. reduction and limits (per workbook: nodal and country)
chain() {   # $1 = workbook version (country), $2 = nodal sparse-network script
  local V=$1 SPN=$2 NV=$1-nlsander; local T=$NV-hv
  local ENRN="runs/${D}-stage2-${NV}-LP-virtual" ENRC="runs/${D}-stage2-${V}-LP-virtual"
  say "B1 $NV: Kron reduction"
  [ -d "$ENRN" ] || DERIVED_VERSION="$NV" REP_NODE_MODE=manual_excel MIQP_CAP_S=1800 $JL scripts/01_reduce.jl "${D}-stage2-${NV}-LP-virtual" LP virtual > logs/reduce_${NV}.log 2>&1
  grep -q COMPLETED "$ENRN/manifest.md"
  say "B1 $V: Kron reduction"
  [ -d "$ENRC" ] || DERIVED_VERSION="$V" REP_NODE_MODE=manual_excel MIQP_CAP_S=1800 $JL scripts/01_reduce.jl "${D}-stage2-${V}-LP-virtual" LP virtual > logs/reduce_${V}.log 2>&1
  grep -q COMPLETED "$ENRC/manifest.md"
  say "B2 $NV: sparse network, monitored lines"
  $PY -W ignore scripts/$SPN "$ENRN" "${T}-sparse-LP" | tail -3
  $PY -W ignore scripts/03_monitored_set.py "$V" | tail -2
  local MON="runs/${D}-monitored-380kv-ge1km-${V}" MONN="runs/${D}-monitored-nodal-nl220-${NV}"
  $PY -W ignore scripts/03n2_monitored_set_nodal_nl220.py "$MON" "inputs/derived/jao_core_${NV}" "${D}-monitored-nodal-nl220-${NV}" | tail -2
  local MONOPT="--monitored=eic:$MONN/monitored_eics.csv" NAME=n1-380kv-nl220-ge1km-nodal
  say "B3 $NV: N-1 limits, then phase shifters + 10 % margin"
  $PY -W ignore scripts/04n_limits_n1_nodal.py "$ENRN" "$T" "$NAME" "$MONOPT" > logs/04n_${T}.log 2>&1
  $PY -W ignore scripts/05n2_limits_pst_margin_nodal_gridref.py "$ENRN" "$T" "${NAME}-pst-frm10" "runs/${D}-limits-nodal-${T}-${NAME}" "--neutral-name=${NAME}-frm10" --margin=0.10 "$MONOPT" > logs/05n2_${T}.log 2>&1
  say "B4 $V: country network and limits"
  $PY -W ignore scripts/02_sparse_network.py "$ENRC" "${V}-sparse-LP" > /dev/null
  local CN=n1-380kv-nl220-ge1km
  $PY -W ignore scripts/04_limits_n1.py "$ENRC" "$V" "$CN" "$MONOPT" > logs/04_${V}.log 2>&1
  $PY -W ignore scripts/05b_limits_pst_margin_gridref.py "$ENRC" "$V" "${CN}-pst-frm10" "runs/${D}-limits-${V}-${CN}" "--neutral-name=${CN}-frm10" --margin=0.10 "$MONOPT" > logs/05b_${V}.log 2>&1
}
chain $V      02n2_sparse_network_nodal_hv.py
chain $V-de2  02n3_sparse_network_nodal_hv_de2.py

# ---------------------------------------------------------------- C. border-tie correction (nodal networks)
NET=n1-380kv-nl220-ge1km-nodal-pst-frm10; NAME=n1-380kv-nl220-ge1km-nodal
say "C1 one Germany: full-grid check, then main (Belgian ties) and lower (Belgian + German ties)"
N1=inputs/derived/diag_fixedpos_${V}-nlsander-hv-sparse-LP-$NET
$PY -W ignore scripts/23b_full_grid_border_check_transit.py $N1 runs/${D}-limits-nodal-${V}-nlsander-hv-$NAME-pst-frm10 2035rt4k-base-transit > logs/23b.log 2>&1
$PY -W ignore scripts/24b_tie_correction_variant_be_only.py $N1 runs/fullgridcheck_2035rt4k-base-transit tiefixbe > logs/24b.log 2>&1
$PY -W ignore scripts/24_tie_correction_variant.py $N1 runs/fullgridcheck_2035rt4k-base-transit tiefix > logs/24.log 2>&1
say "C2 Germany split: full-grid check, then main"
N2=inputs/derived/diag_fixedpos_${V}-de2-nlsander-hv-sparse-LP-$NET
$PY -W ignore scripts/23d_full_grid_border_check_de2.py $N2 runs/${D}-limits-nodal-${V}-de2-nlsander-hv-$NAME-pst-frm10 2035rt4k-de2-base-b > logs/23d.log 2>&1
$PY -W ignore scripts/24c_tie_correction_variant_de2.py $N2 runs/fullgridcheck_2035rt4k-de2-base-b tiefixmain main > logs/24c.log 2>&1

say "done"
