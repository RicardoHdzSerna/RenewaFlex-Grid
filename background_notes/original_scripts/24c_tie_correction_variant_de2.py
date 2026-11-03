#!/usr/bin/env python3
"""
24c_tie_correction_variant_de2.py — copy of 24_tie_correction_variant.py (2026-10-25) for networks with Germany split (DE2: DE0N, DE0S;
also works with one node DE00). Changes, nothing else: "Germany" = all German nodes of the network (free split, as 23c/23d); the
targets come from a 23c/23d run (cases "free", to BE / DE / BE+DE); a mode argument:
  main   f_BE so free NL->BE = full grid; then f_DE (all German ties) so free NL->DE = full grid (f_DE = 1 if already within);
  lower  f_BE as main; then f_DE so free NL->BE+DE = full grid (24's rule).
The 2025-test module 10n3 (knows DE_N/DE_S) replaces 10n2 inside scripts/22. Header of 24 follows.
24_tie_correction_variant.py — a nodal network VARIANT with corrected Dutch tie limits (2026-10-23, user: "yes build the variant and
run both checks").

Why: scripts/23 showed that the nodal network lets more cross the Dutch borders than the full grid can carry N-1 securely under the
option-3 rules: NL -> BE about 20 % too much (full-grid binding element behind the border: Doel–Zandvliet), NL -> BE+DE together
about 24 % too much; NL -> DE alone is right. Cause: every tie branch gets its own limit from the single exchange that loads it most
(envelope of 05n/05n2); no exchange checks the ties together.

What this script does (labelled correction, NOT a new limit method):
  step 1  one factor f_BE for BOTH Belgian ties (BE00–NL-*), found by bisection so that the reduced network's maximum free NL -> BE
          transfer equals the full-grid secure maximum of the same case (cases.csv of a scripts/23 run, case "free", to "BE");
  step 2  with f_BE applied: if the reduced maximum free NL -> BE+DE still exceeds the full-grid value, one factor f_DE for ALL German
          ties (NL-*–DE00), found the same way on the BE+DE case; otherwise f_DE = 1.
Every other branch is unchanged (reactances unchanged, so routing — and the 2025 border statistics — are unchanged).
The maximum transfers use the same LP as scripts/22 (other zones 0, Dutch side free per node, limited branches only).

    ~/.tulipa_pipeline_venv/bin/python scripts/24_tie_correction_variant.py <nodal network> <scripts/23 run> <suffix>

Writes inputs/derived/<network name>-<suffix>/ {flow.csv, flow-milestone.csv, nodes.csv, README.md, sha256.txt, manifest.json};
aborts if it exists. Reads no validation data.
"""
from __future__ import annotations
import datetime, importlib.util, json, sys
from pathlib import Path
import numpy as np, pandas as pd

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("t22", ROOT / "scripts" / "22_nl_transfer_capacity_compare.py"); M = importlib.util.module_from_spec(_s); _s.loader.exec_module(M)
_s3 = importlib.util.spec_from_file_location("t10n3", ROOT / "scripts" / "10n3_test_2025_nodal_injections_de2.py"); T = importlib.util.module_from_spec(_s3); _s3.loader.exec_module(T)
M.T = T                                                               # 24c: scripts/22 uses 10n3 (zones DE_N/DE_S)


def main():
    if len(sys.argv) != 5 or sys.argv[4] not in ("main", "lower"):
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
    if MODE == "main":
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
