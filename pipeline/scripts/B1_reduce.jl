# B1_reduce.jl — reduce the full grid workbook to its representative buses (Kron reduction) with the ElectricityNetworkReduction package.
#
# STEP  B1 in run_all.sh (HANDOVER.md section 3.1)
#
# WHAT IT DOES
#   Reads inputs/derived/jao_core_<DERIVED_VERSION>/jao_core.xlsx and runs the Julia package ElectricityNetworkReduction (ENR,
#   https://github.com/TulipaEnergy/ElectricityNetworkReduction.jl; version pinned in Manifest.toml). ENR:
#     - builds the DC network of the full grid (about 1,760 buses), checks it is one connected island;
#     - keeps the buses with IsRepresentative = 1 (one per foreign zone; SR2025 32 Dutch buses in a nodal workbook) and
#       eliminates every other bus (Kron reduction), so that flows between the kept buses are exactly those of the full grid;
#     - writes the equivalent reactances between kept buses, the PTDFs, and the full-grid transfer limit (TTC) of every pair.
#   B2 turns this into the reduced network; B4/B5 compute the N-1 limits from the full grid itself.
#
# SETTINGS (environment variables, as run_all.sh sets them)
#   DERIVED_VERSION=<workbook version>   which workbook to read
#   REP_NODE_MODE=manual_excel           use the IsRepresentative column of the workbook
#   MIQP_CAP_S=1800                      time cap for ENR's MIQP option (not used with LP)
#
# USAGE   julia --threads=4,0 scripts/B1_reduce.jl <run name> LP virtual
#         run name e.g. 2026-11-03-stage2-v29-vvltr2-2035-tennet-tlb3-rt4k-nlsander-LP-virtual
#         "LP" = ENR's capacity-fitting method; "virtual" allows virtual lines (as in every run in use).
#         --threads=4,0 is needed: --threads=auto crashes ENR's TTC loop on Julia >= 1.12.
# WRITES  runs/<run name>/ (inputs copy, outputs/, manifest.md). Never overwrites.
#
# HISTORY Same code as core_grid_dcopf/scripts/01_reduce.jl (archived 11 -> 116_stage1_jao_diagnostics_hires.jl); only this
#         header was added. The guard at the top checks a read-only Tulipa baseline folder that is not in this package; with
#         the folder absent the check passes. The original header follows.
#
# core_grid_dcopf (2026-10-16): copy of archive/dcopf/scripts/116_stage1_jao_diagnostics_hires.jl; 2 path/name edit(s), see docs/MAP.md; the original header follows.
# 116_stage1_jao_diagnostics_hires.jl — COPY of 11_stage1_jao_diagnostics.jl (not edited) with ONE change: CONFIG.high_res_zones is read from
# the environment variable HIGH_RES_ZONES (comma-separated zone labels; empty = as 11). Step 3 of 2026-10-16: the Netherlands at full
# bus resolution, every other zone one representative bus. Original header of 11 follows.
# 11_stage1_jao_diagnostics.jl — Stage 1 (CLAUDE.md §8): run ENR on the JAO Core workbook built by
# scripts/10_build_enr_workbook.py. DIAGNOSTICS ONLY: the outputs to read are Island_Diagnostics
# and Line_Details; TTC/capacity outputs are produced but not interpreted at this stage.
#
# Run:   julia --threads=4,0 dcopf/scripts/11_stage1_jao_diagnostics.jl [run-name] [QP|LP|MIQP] [virtual]
#        3rd arg "virtual" sets allow_virtual_lines=true (default false, as the package test suite).
#        (--threads=4,0 = 4 default threads, 0 interactive: see notes/03_enr_threadid_bug.md;
#         --threads=auto or --threads=4 crash the package's TTC loop on Julia >= 1.12)
# Writes dcopf/runs/<run-name>/ (default: <today>-stage0-case118). Never overwrites.

using Pkg
const DCOPF = normpath(joinpath(@__DIR__, ".."))
Pkg.activate(DCOPF; io = devnull)
using ElectricityNetworkReduction
const ENR = ElectricityNetworkReduction   # qualify every call: not all names are exported
using Dates, SHA, TOML

const BASELINE  = joinpath(DCOPF, "inputs", "tulipa_baseline", "2035_v2")   # core_grid_dcopf: the read-only Tulipa baseline copy inside this folder
# Installed ENR commit — from ~/.julia/clones (Manifest stores only the tree hash). Recorded
# in notes/provenance.md; update here if the environment is ever re-resolved.
const ENR_COMMIT = "de3d2583cad87a7341fb52272f8c14bbbd966d2e"

sha256hex(path) = open(path) do io; bytes2hex(sha256(io)); end

# ---------------------------------------------------------------- 0. guardrails
# Baseline freeze must still hold (it silently did not, once — see provenance.md).
# Sys.iswritable uses access(2): a real permission check with no write attempt.
for p in (BASELINE,)
    Sys.iswritable(p) && error("ABORT: baseline is writable at $p — re-apply the freeze and investigate.")
end
println("baseline freeze verified read-only: ", BASELINE)

run_name = isempty(ARGS) ? Dates.format(today(), "yyyy-mm-dd") * "-stage1-jao-core" : ARGS[1]
const OPT = length(ARGS) >= 2 ? ARGS[2] : "QP"   # capacity-fitting method; LP/MIQP exercise HiGHS, QP exercises Ipopt
OPT in ("QP", "LP", "MIQP") || error("ABORT: unknown optimisation type $OPT")
const VIRTUAL = length(ARGS) >= 3 && ARGS[3] == "virtual"
RUN_DIR  = joinpath(DCOPF, "runs", run_name)
isdir(RUN_DIR) && error("ABORT: run directory exists, never overwrite: $RUN_DIR — pass a new name.")
mkpath(joinpath(RUN_DIR, "inputs")); mkpath(joinpath(RUN_DIR, "outputs"))

# ---------------------------------------------------------------- 1. inputs (untouched copy)
enr_pkg  = pkgdir(ENR)
const DERIVED_VERSION = get(ENV, "DERIVED_VERSION", "v1")   # which builder output to run
const DERIVED = joinpath(DCOPF, "inputs", "derived", "jao_core_" * DERIVED_VERSION)
src_xlsx = joinpath(DERIVED, "jao_core.xlsx")
isfile(src_xlsx) || error("derived workbook not found: $src_xlsx — run scripts/10_build_enr_workbook.py first")
input_dir = joinpath(RUN_DIR, "inputs")
for f in ("jao_core.xlsx", "build_report.md", "row_decisions.csv", "substation_map.csv", "sha256.txt")
    cp(joinpath(DERIVED, f), joinpath(input_dir, f))
end
input_sha = sha256hex(joinpath(input_dir, "jao_core.xlsx"))
println("input: jao_core.xlsx sha256=", input_sha, "  (from ", src_xlsx, ")")

# ---------------------------------------------------------------- 2. CONFIG — every field, explicitly (CLAUDE.md §7)
ENR.reset_config!()
CONFIG = ENR.CONFIG
CONFIG.input_filename      = "jao_core.xlsx"
CONFIG.case_study          = "jao_core_" * DERIVED_VERSION
CONFIG.bus_names_as_int    = false      # bus ids are strings NAME_kV
CONFIG.in_pu               = false      # JAO ohms/µS; Voltage_level = NOMINAL kV per level (see notes/provenance.md decision 3)
CONFIG.allow_virtual_lines = VIRTUAL    # false = package default (watch for the silent revert-to-true); true = all zone pairs
CONFIG.base                = 100.0      # MVA
CONFIG.optimisation_type   = OPT        # "QP" as in the test suite; "LP"/"MIQP" for the HiGHS check
CONFIG.lambda              = 1e-6
CONFIG.ptdf_epsilon        = 1e-6
CONFIG.suffix              = OPT
CONFIG.miqp_binding_candidates_per_txn = 8
CONFIG.miqp_time_limit_sec = parse(Float64, get(ENV, "MIQP_CAP_S", "1800"))   # user: 600 s cap for Stage 2 (2026-09-13)
CONFIG.miqp_mip_rel_gap    = 1e-4
CONFIG.rep_node_mode       = get(ENV, "REP_NODE_MODE", "auto")   # "manual_excel" uses the workbook's IsRepresentative column (builder --rep=...)
CONFIG.rep_node_k_per_zone = 1
CONFIG.rep_node_degree_threshold = 1e-8
CONFIG.high_res_zones      = isempty(get(ENV, "HIGH_RES_ZONES", "")) ? String[] : String.(split(get(ENV, "HIGH_RES_ZONES", ""), ","))   # 116: zones kept at full bus resolution (env HIGH_RES_ZONES=NL)
CONFIG.enable_plots        = true       # Stage 0 explicitly checks the plotting stack
CONFIG.has_dc_lines        = true       # ALEGrO in DCLines sheet
CONFIG.dc_lines_sheet      = "DCLines"
CONFIG.has_transformers    = true
CONFIG.transformers_sheet  = "Transformers"
CONFIG.transformers_in_pu  = false      # JAO transformer X in ohms referred to primary; Voltage_level = nominal primary kV
CONFIG.has_converters      = false
CONFIG.converters_sheet    = "Converters"
CONFIG.parallel_processing = true       # source default is false; needs --threads=auto
# Guard: any Config field not set above would silently keep its default.
let set_here = Set(Symbol.(["input_filename","case_study","bus_names_as_int","in_pu","allow_virtual_lines","base",
        "optimisation_type","lambda","ptdf_epsilon","suffix","miqp_binding_candidates_per_txn","miqp_time_limit_sec",
        "miqp_mip_rel_gap","rep_node_mode","rep_node_k_per_zone","rep_node_degree_threshold","high_res_zones",
        "enable_plots","has_dc_lines","dc_lines_sheet","has_transformers","transformers_sheet","transformers_in_pu",
        "has_converters","converters_sheet","parallel_processing"]))
    missing = setdiff(Set(fieldnames(typeof(CONFIG))), set_here)
    isempty(missing) || error("ABORT: Config fields not set explicitly: $(collect(missing)) — package version moved?")
end
Threads.nthreads() == 1 && @warn "Julia has 1 thread: parallel_processing=true will fall back to sequential"
# ENR bug (notes/03_enr_threadid_bug.md): threadid() > nthreads() when an interactive pool exists.
if CONFIG.parallel_processing && Threads.nthreads(:interactive) > 0
    error("ABORT: $(Threads.nthreads(:interactive)) interactive thread(s) present — launch with --threads=$(Threads.nthreads()),0 (see notes/03_enr_threadid_bug.md)")
end

# ---------------------------------------------------------------- 3. run, capturing console
output_dir = joinpath(RUN_DIR, "outputs")
console    = joinpath(RUN_DIR, "console.log")
t0 = time(); ok = true; err = nothing
open(console, "w") do io
    redirect_stdout(io) do; redirect_stderr(io) do
        ENR.print_config()
        println("julia ", VERSION, "  threads=", Threads.nthreads(), "  started ", now())
        try
            ENR.main_full_analysis(input_dir, output_dir)
        catch e
            global ok = false; global err = e
            showerror(io, e, catch_backtrace()); println(io)
        end
        println("finished ", now())
    end; end
end
wall = time() - t0

# ---------------------------------------------------------------- 4. warning scan (CLAUDE.md §7)
lines = readlines(console)
flag  = r"warn|revert|fall ?back|sequential|missing|skipp|not found|MILP status: (TIME_LIMIT|INFEASIBLE|UNBOUNDED)"i
warns = [l for l in lines if occursin(flag, l)]

# ---------------------------------------------------------------- 5. manifest.md (written by the script, not by hand)
man = TOML.parsefile(joinpath(DCOPF, "Manifest.toml"))
ver(name) = begin
    d = get(man["deps"], name, nothing)
    d === nothing ? "not in Manifest" : join([string(get(e, "version", "?"), haskey(e, "git-tree-sha1") ? " tree=" * e["git-tree-sha1"] : "") for e in d], "; ")
end
outs = sort(filter(f -> isfile(joinpath(output_dir, f)), readdir(output_dir)))
open(joinpath(RUN_DIR, "manifest.md"), "w") do io
    println(io, "# Run manifest — ", run_name, "\n")
    println(io, "| | |\n|---|---|")
    println(io, "| Date | ", now(), " |")
    println(io, "| Stage | 1 — JAO Core ingestion, diagnostics only (CLAUDE.md §8), optimisation_type=", OPT, ", allow_virtual_lines=", VIRTUAL, " |")
    println(io, "| Status | ", ok ? "COMPLETED" : "FAILED: $(sprint(showerror, err))", " |")
    println(io, "| Wall-clock | ", round(wall; digits = 1), " s |")
    println(io, "| Git SHA (dcopf) | none — dcopf/ is not under git (user decision 2026-09-13; see notes/provenance.md) |")
    println(io, "| ElectricityNetworkReduction | ", ver("ElectricityNetworkReduction"), "; commit ", ENR_COMMIT, "; path ", enr_pkg, " |")
    for p in ("JuMP", "Ipopt", "Ipopt_jll", "HiGHS", "HiGHS_jll", "CairoMakie", "GraphMakie", "XLSX")
        println(io, "| ", p, " | ", ver(p), " |")
    end
    println(io, "| Julia | ", VERSION, ", threads default=", Threads.nthreads(:default), " interactive=", Threads.nthreads(:interactive), " (launch --threads=", Threads.nthreads(:default), ",", Threads.nthreads(:interactive), "), ", Sys.MACHINE, " |")
    println(io, "| Script | scripts/11_stage1_jao_diagnostics.jl |")
    println(io, "| Input | inputs/jao_core.xlsx sha256=", input_sha, " (copied from ", src_xlsx, "; builder scripts/10_build_enr_workbook.py; build_report.md + row_decisions.csv copied alongside) |")
    println(io, "\n## CONFIG (complete, as run)\n\n```")
    for f in fieldnames(typeof(CONFIG)); println(io, rpad(string(f), 34), " = ", repr(getfield(CONFIG, f))); end
    println(io, "```\n\n## Warnings / fallbacks found in console.log (", length(warns), ")\n")
    isempty(warns) ? println(io, "_none matched /", flag.pattern, "/_") : foreach(l -> println(io, "- `", strip(l), "`"), warns)
    println(io, "\n## Outputs (sha256)\n")
    for f in outs; println(io, "- `", f, "`  ", sha256hex(joinpath(output_dir, f))); end
end
println(ok ? "COMPLETED" : "FAILED", " in ", round(wall; digits = 1), " s — ", length(outs), " output files, ", length(warns), " flagged console lines")
println("run dir: ", RUN_DIR)
ok || exit(1)
