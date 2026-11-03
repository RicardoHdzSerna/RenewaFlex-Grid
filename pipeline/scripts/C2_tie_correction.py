#!/usr/bin/env python3
"""
C2_tie_correction.py — scale the Dutch border ties so that the reduced network allows no more than the full grid.

STEP  C2 in run_all.sh (HANDOVER.md section 4.1)

WHAT IT DOES
  Takes the full-grid maxima of a C1 run (cases "free": NL -> BE, NL -> DE, NL -> BE + DE) and finds, by bisection:
    f_BE  one factor for both Belgian ties (BE00 - NL-*) so that the reduced network's NL -> BE maximum equals the full grid's;
    f_DE  one factor for all German ties (NL-* - DE*), mode
            beonly f_DE = 1: German ties unchanged (the "main" network with one German node, *-tiefixbe)
            main   so that NL -> DE equals the full grid (f_DE = 1 if it is already within; the Germany-split network),
            lower  so that NL -> BE + DE together equals the full grid (stricter).
  Every other branch, and every reactance, is unchanged. It is a labelled correction, not a new limit method.
  Results in use: one German node: beonly f_BE 0.826, f_DE 1; lower f_BE 0.826, f_DE 0.797. Germany split: main f_BE 0.832,
  f_DE 0.852. (main on the one-German-node network would give f_DE 0.997: there the reduced network allows NL -> DE 10,356 MW
  against 10,322 MW in the full grid; that 0.3 % was left as it is in the network in use.)

READS   the nodal network folder (flow.csv, flow-milestone.csv, nodes.csv), the C1 run (cases.csv, manifest.json)
WRITES  inputs/derived/<network>-<suffix>/  flow.csv, flow-milestone.csv, nodes.csv, README.md, sha256.txt, manifest.json.
        Aborts if it exists.

USAGE   python scripts/C2_tie_correction.py <nodal network folder> <C1 run> <suffix> <beonly|main|lower>
        e.g. ... C2_tie_correction.py inputs/derived/diag_fixedpos_...-pst-frm10 runs/fullgridcheck_2035rt4k-base tiefixbe main

HISTORY Same code as core_grid_dcopf/scripts/24c_tie_correction_variant_de2.py (25 Oct 2026; 24 -> 24b -> 24c). The one-German-
        node networks in use were made with 24b (Belgian ties only) and 24 (= lower). Changes for the handover: mode beonly added
        (= 24b; checked: same network); helpers from lib_network.py (unchanged code) instead of 22_... and 10n3_...; this header.
       
"""
from __future__ import annotations
import datetime, importlib.util, json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("lib_network", ROOT / "scripts" / "lib_network.py"); M = importlib.util.module_from_spec(_s); _s.loader.exec_module(M)
T = M                                                                 # network(), max_transfer() and the zone tables all live in lib_network.py


def main():
    if len(sys.argv) != 5 or sys.argv[4] not in ("beonly", "main", "lower"):
        sys.exit(__doc__)
    net, r23, suffix, MODE = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), sys.argv[3], sys.argv[4]
    out = net.parent / f"{net.name}-{suffix}"
    if out.exists():
        sys.exit(f"ABORT: {out} exists — never overwritten")
    m23 = json.loads((r23 / "manifest.json").read_text())
    if Path(m23["config"]["network"]).resolve() != net:
        sys.exit("ABORT: the scripts/23 run was made on another network")
    C = pd.read_csv(r23 / "cases.csv")
    target = {to: float(C[(C.to == to) & (C.case == "free")].full_grid_mw.iloc[0]) for to in ("BE", "DE", "BE+DE")}
    b, nodes, PT, cap0, names = M.network(net)
    zn = lambda x: T.ZONE_OF_NODE[x]
    lim_rows = [(r.a, r.c) for r in b.itertuples() if r.capacity < T.UNLIMITED_FROM_MW]          # same order as PT / cap0 / names
    be_tie = np.array([{zn(a), zn(c)} == {"NL", "BE"} for a, c in lim_rows]); de_tie = np.array([{zn(a), zn(c)} == {"NL", "DE_LU"} for a, c in lim_rows])
    assert be_tie.sum() == 2 and de_tie.sum() == 4, (be_tie.sum(), de_tie.sum())
    DEN = sorted(n for n in nodes if T.ZONE_OF_NODE[n] == "DE_LU")                       # 24c: the German nodes

    def mx(fbe, fde, sinks):
        cap = cap0 * np.where(be_tie, fbe, 1.0) * np.where(de_tie, fde, 1.0)
        return M.max_transfer(nodes, PT, cap, names, None, sinks, True)[0]

    def bisect(fun, tgt):
        lo, hi = 0.3, 1.0
        if fun(hi) <= tgt:
            return 1.0
        for _ in range(60):
            mid = (lo + hi) / 2
            lo, hi = (mid, hi) if fun(mid) <= tgt else (lo, mid)
        return lo

    f_be = bisect(lambda f: mx(f, 1.0, ["BE00"]), target["BE"])
    if MODE == "beonly":                                              # handover: the rule of 24b, German ties unchanged
        f_de = 1.0
    elif MODE == "main":
        f_de = bisect(lambda f: mx(f_be, f, DEN), target["DE"])
    else:
        f_de = bisect(lambda f: mx(f_be, f, ["BE00"] + DEN), target["BE+DE"])
    res = {"NL->BE": (mx(1, 1, ["BE00"]), mx(f_be, f_de, ["BE00"]), target["BE"]), "NL->DE": (mx(1, 1, DEN), mx(f_be, f_de, DEN), target["DE"]),
           "NL->BE+DE": (mx(1, 1, ["BE00"] + DEN), mx(f_be, f_de, ["BE00"] + DEN), target["BE+DE"])}
    out.mkdir(parents=True)
    fl = pd.read_csv(net / "flow.csv"); a2n = lambda s: s.split("_E_Demand")[0]
    fac = []
    for r in fl.itertuples():
        za, zc = zn(a2n(r.from_asset)), zn(a2n(r.to_asset))
        fac.append(f_be if {za, zc} == {"NL", "BE"} else (f_de if {za, zc} == {"NL", "DE_LU"} else 1.0))
    fl2 = fl.copy(); fl2["capacity"] = [f"{float(c) * f:.10g}" if f != 1.0 else c for c, f in zip(fl.capacity, fac)]
    fl2.to_csv(out / "flow.csv", index=False)
    for f in ("flow-milestone.csv", "nodes.csv"):
        (out / f).write_bytes((net / f).read_bytes())
    ties = pd.DataFrame({"branch": [f"{a2n(a)}-{a2n(c)}" for a, c in zip(fl.from_asset, fl.to_asset)], "before": fl.capacity.astype(float), "factor": fac})
    ties["after"] = ties.before * ties.factor; ties = ties[ties.factor != 1.0]
    tab = "\n".join(f"| {r.branch} | {r.before:,.0f} | {r.factor:.3f} | {r.after:,.0f} |" for r in ties.itertuples())
    (out / "README.md").write_text(f"# {out.name}\n\nVARIANT of `{net.name}` (scripts/24_tie_correction_variant.py, 2026-10-23): Dutch tie limits scaled so that the "
                                   f"maximum free Dutch exchange does not exceed the full-grid N-1 secure value of `runs/{r23.name}` (scripts/23). mode {MODE}: Belgian ties x {f_be:.4f}, "
                                   f"German ties x {f_de:.4f}; every other branch, all reactances unchanged. A labelled correction, not adopted.\n\n| tie | before (MW) | factor | after (MW) |\n|---|---|---|---|\n{tab}\n\n"
                                   + "| exchange (free Dutch side) | before | after | full grid |\n|---|---|---|---|\n" + "\n".join(f"| {k} | {v[0]:,.0f} | {v[1]:,.0f} | {v[2]:,.0f} |" for k, v in res.items()) + "\n")
    (out / "manifest.json").write_text(json.dumps({"finished": datetime.datetime.now().isoformat(timespec="seconds"), "script": Path(__file__).name, "script_sha256": T.sha(Path(__file__)),
                                                   "base_network": str(net), "run_23": str(r23), "f_be": f_be, "f_de": f_de, "targets_mw": target,
                                                   "transfers_mw_before_after_fullgrid": res, "inputs_sha256": {"flow.csv": T.sha(net / "flow.csv"), "cases.csv": T.sha(r23 / "cases.csv")}}, indent=1))
    with open(out / "sha256.txt", "w") as fh:
        for p in sorted(out.iterdir()):
            if p.name != "sha256.txt":
                fh.write(f"{T.sha(p)}  {p.name}\n")
    print((out / "README.md").read_text()); print(f"wrote {out}")


if __name__ == "__main__":
    main()
