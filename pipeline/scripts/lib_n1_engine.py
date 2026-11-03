#!/usr/bin/env python3
"""
lib_n1_engine.py — the full-grid calculations shared by B4, B5 and C1. Not run on its own.

  Builds the DC power-flow matrices of the full workbook grid (susceptance matrix, PTDFs: MW on each line per MW injected at each
  bus), the N-1 outage updates (exact rank-one updates: what each line carries when one other element is out), the monitored
  line set and the transfer limit of an exchange (the largest exchange with every monitored line within its rating, intact and
  under every outage).

HISTORY Same code as core_grid_dcopf/scripts/lib_n1_engine.py (archived 77_n1_ttc_tno_method.py); only this header was added
        (the script as run is in background_notes/original_scripts/).
"""
import datetime, hashlib, json, sys
from pathlib import Path

import numpy as np, pandas as pd

DCOPF = Path(__file__).resolve().parents[1]
BRIDGE_EPS = 1e-7
MODES = {"tno": "ratings matrix unchanged during an outage (as in the MATLAB file)",
         "strict": "rating of the outaged circuit removed from its pair (not in the MATLAB file)"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# ------------------------------------------------------------------ engine (also imported by 78)
def prepare(n, F, T, bb, cap):
    """Full grid: branch records (F, T, susceptance, rating) -> aggregated lines and the inverse susceptance matrix (bus 0 = slack)."""
    assert (F != T).all() and (bb > 0).all()
    a, b = np.minimum(F, T), np.maximum(F, T)
    g = pd.DataFrame({"a": a, "b": b, "bb": bb, "cap": cap, "k": 1}).groupby(["a", "b"], as_index=False).sum()
    pidx = {(x, y): i for i, (x, y) in enumerate(zip(g.a, g.b))}
    B = np.zeros((n, n)); np.add.at(B, (F, F), bb); np.add.at(B, (T, T), bb); np.add.at(B, (F, T), -bb); np.add.at(B, (T, F), -bb)
    keep = np.arange(1, n); Binv = np.zeros((n, n)); Binv[np.ix_(keep, keep)] = np.linalg.inv(B[np.ix_(keep, keep)])
    return {"n": n, "F": F, "T": T, "bb": bb, "cap": cap, "B": B, "Binv": Binv, "GA": g.a.to_numpy(), "GB": g.b.to_numpy(), "GBB": g.bb.to_numpy(),
            "GCAP": g.cap.to_numpy(), "GK": g.k.to_numpy(), "pair": np.array([pidx[(x, y)] for x, y in zip(a, b)]),
            "nb": np.bincount(np.r_[g.a.to_numpy(), g.b.to_numpy()], minlength=n)}          # distinct neighbours per bus


def transactions(nk):
    tx = [(i, j) for i in range(nk) for j in range(i + 1, nk)]
    return np.array([i for i, _ in tx]), np.array([j for _, j in tx])


def _limit(W, ti, tj):
    L = np.abs(W[:, ti] - W[:, tj]); return 1.0 / L.max(axis=0), L.argmax(axis=0)


def n0(G, K, ti, tj):
    """Transfer limit between kept buses K[ti] and K[tj] on the intact grid; D0 = angle difference over each line per MW injected at each kept bus."""
    D0 = G["Binv"][np.ix_(G["GA"], K)] - G["Binv"][np.ix_(G["GB"], K)]
    ttc, lim = _limit(G["GBB"][:, None] * D0 / G["GCAP"][:, None], ti, tj)
    return ttc, lim, D0


def n1(G, K, ti, tj, outages, D0):
    """Each branch record in `outages` taken out in turn (rank-one update of the inverse). -> {mode: (limits, limiting line)}, status list."""
    Binv, GA, GB, K = G["Binv"], G["GA"], G["GB"], np.asarray(K)
    res = {m: (np.full((len(outages), len(ti)), np.nan), np.full((len(outages), len(ti)), -1)) for m in MODES}; status = []
    for o, h in enumerate(outages):
        s, r, b, p = G["F"][h], G["T"][h], G["bb"][h], G["pair"][h]
        if G["nb"][s] <= 1 or G["nb"][r] <= 1:
            status.append("skipped: an end bus has one neighbour (MATLAB rule)"); continue
        u = Binv[:, s] - Binv[:, r]; den = 1.0 - b * (u[s] - u[r])
        if den < BRIDGE_EPS:
            status.append("skipped: taking it out splits the grid (rule added here)"); continue
        D = D0 + (b / den) * np.outer(u[GA] - u[GB], u[K])
        gbb = G["GBB"].copy(); gbb[p] -= b
        if gbb[p] < 1e-9 * b:
            gbb[p] = 0.0
        for m in MODES:
            cap = G["GCAP"].copy()
            if m == "strict":
                cap[p] -= G["cap"][h]
            W = gbb[:, None] * D / np.where(cap > 1e-9, cap, np.inf)[:, None]
            res[m][0][o], res[m][1][o] = _limit(W, ti, tj)
        status.append("taken out")
    return res, status


def brute(G, K, ti, tj, h, mode):
    """The same outage by rebuilding and inverting the whole matrix (check of the rank-one update)."""
    n, s, r, b, p = G["n"], G["F"][h], G["T"][h], G["bb"][h], G["pair"][h]
    B = G["B"].copy(); B[s, s] -= b; B[r, r] -= b; B[s, r] += b; B[r, s] += b
    keep = np.arange(1, n); Bi = np.zeros((n, n)); Bi[np.ix_(keep, keep)] = np.linalg.inv(B[np.ix_(keep, keep)])
    gbb = G["GBB"].copy(); gbb[p] = max(gbb[p] - b, 0.0); cap = G["GCAP"].copy()
    if mode == "strict":
        cap[p] -= G["cap"][h]
    D = Bi[np.ix_(G["GA"], K)] - Bi[np.ix_(G["GB"], K)]
    return _limit(gbb[:, None] * D / np.where(cap > 1e-9, cap, np.inf)[:, None], ti, tj)[0]


def kron_sparse(G, K, ia, ib, nk):
    """Kron reduction to the kept buses, then the network of the listed pairs only. -> reactance per pair, PTDF (pairs x kept buses)."""
    Zr = G["Binv"][np.ix_(K, K)]; Zk = Zr[1:, 1:] - Zr[1:, [0]] - Zr[[0], 1:] + Zr[0, 0]; Bk = np.linalg.inv(Zk)
    L = np.zeros((nk, nk)); L[1:, 1:] = Bk; L[0, 1:] = -Bk.sum(axis=0); L[1:, 0] = -Bk.sum(axis=1); L[0, 0] = Bk.sum()
    bsp = -L[ia, ib]; A = np.zeros((len(ia), nk)); A[np.arange(len(ia)), ia] = 1; A[np.arange(len(ia)), ib] = -1
    Bs = A.T @ (bsp[:, None] * A); kp = np.arange(1, nk); Xm = np.zeros((nk, nk)); Xm[np.ix_(kp, kp)] = np.linalg.inv(Bs[np.ix_(kp, kp)])
    return 1.0 / bsp, (bsp[:, None] * A) @ Xm, L


# ------------------------------------------------------------------ our network
def main():
    import openpyxl
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    run = Path(args[0]).resolve(); TAG = args[1]
    BASE_NET = DCOPF / "inputs" / "derived" / f"diag_fixedpos_{TAG}-sparse-LP"
    OUT = DCOPF / "runs" / f"{datetime.date.today().isoformat()}-n1-ttc-{TAG}"
    NETS = {m: DCOPF / "inputs" / "derived" / f"diag_fixedpos_{TAG}-sparse-LP-n1{m}" for m in MODES}
    for p in [OUT, *NETS.values()]:
        if p.exists():
            sys.exit(f"ABORT: {p} exists — never overwritten")
    hashes = {}
    def rd(p):
        hashes[str(Path(p).resolve().relative_to(DCOPF.parent))] = sha(p); return p
    man = (run / "manifest.md").read_text()
    cfg = {l.split("=")[0].strip(): l.split("=", 1)[1].strip().strip('"') for l in man.splitlines() if " = " in l and not l.startswith("|")}
    suf = cfg["suffix"]; O = run / "outputs"
    ld = pd.read_csv(rd(O / f"Line_Details_{suf}.csv")); bm = pd.read_csv(rd(O / f"Bus_ID_Map_{suf}.csv")); tp = pd.read_csv(rd(O / f"TTC_Original_Network_{suf}.csv"))
    wb = openpyxl.load_workbook(rd(run / "inputs" / cfg["input_filename"]), read_only=True, data_only=True)
    nr = list(wb["Nodes"].iter_rows(values_only=True)); nh = list(nr[0]); col = lambda r, k: r[nh.index(k)]
    zone_of = {col(r, "Bus"): col(r, "Zone") for r in nr[1:] if r[0]}
    flag = {col(r, "Zone"): col(r, "Bus") for r in nr[1:] if r[0] and col(r, "IsRepresentative") == 1}
    adj = set()
    for sh in ("Lines", "Tielines", "Transformers"):
        rows = list(wb[sh].iter_rows(values_only=True)); h = rows[0]
        for r in rows[1:]:
            if r and r[0]:
                za, zb = zone_of.get(r[h.index("From_node")]), zone_of.get(r[h.index("To_node")])
                if za and zb and za != zb:
                    adj.add(tuple(sorted((za, zb))))
    PAIRS = sorted(adj); zones = sorted(set(zone_of.values())); zi = {z: j for j, z in enumerate(zones)}; nz = len(zones)
    name = dict(zip(bm.new_id, bm.old_name)); ids = sorted(bm.new_id); n = len(ids); pos = {i: j for j, i in enumerate(ids)}; idx_of = {name[i]: pos[i] for i in ids}
    bname = [name[i] for i in ids]; bzone = np.array([zone_of[x] for x in bname])
    F = ld.New_ID_From.map(pos).to_numpy(); T = ld.New_ID_To.map(pos).to_numpy()
    f_net = {k: rd(BASE_NET / k) for k in ("flow.csv", "flow-milestone.csv", "nodes.csv")}
    OUT.mkdir(parents=False)
    CONFIG = {"script": "scripts/77_n1_ttc_tno_method.py", "script_sha256": sha(Path(__file__)), "enr_run": str(run), "tag": TAG, "n0_network": str(BASE_NET),
              "matlab_source": "KronNewCapV2_avg.m, TotalTransferCapacity, lines 296-326 (N-1) and 284-285 (N-0)", "modes": MODES,
              "outage_set": "every Line_Details record whose two end buses lie in different zones (one record = one circuit)",
              "skip_rule_matlab": "an end bus with one neighbour or none: outage not applied, limit unchanged",
              "skip_rule_added": f"an outage that splits the grid (1 - b * effective reactance < {BRIDGE_EPS}) is not applied",
              "n1_value": "minimum over the outages (the MATLAB comment; its code line 333 takes max, which returns the N-0 value)",
              "branch_limits": "LP envelope C_l = max_t TTC_t |PTDF_t,l| on the physical-border network, as scripts 58 and 72",
              "representative_buses": flag, "validation_data_read": "none"}
    (OUT / "manifest.json").write_text(json.dumps({"started": datetime.datetime.now().isoformat(timespec="seconds"), "CONFIG": CONFIG, "inputs_sha256": hashes}, indent=1))

    G = prepare(n, F, T, (1.0 / ld.X_pu).to_numpy(), ld.Capacity_MW.to_numpy())
    K = [idx_of[flag[z]] for z in zones]; ti, tj = transactions(nz)
    T0, lim0, D0 = n0(G, K, ti, tj)
    pk = {tuple(sorted((a, b))): v for a, b, v in zip(tp.transaction_from, tp.transaction_to, tp.TTC_AC_MW)}
    chk_ttc = max(abs(T0[t] / pk[tuple(sorted((ids[K[ti[t]]], ids[K[tj[t]]])))] - 1) for t in range(len(ti)))
    ia = np.array([zi[a] for a, _ in PAIRS]); ib = np.array([zi[b] for _, b in PAIRS])
    X, PT, _ = kron_sparse(G, K, ia, ib, nz); A = np.abs(PT[:, ti] - PT[:, tj])
    C0 = (T0[None, :] * A).max(axis=1)
    fl = pd.read_csv(f_net["flow.csv"]); fm = pd.read_csv(f_net["flow-milestone.csv"]); nd = pd.read_csv(f_net["nodes.csv"]); az = dict(zip(nd.asset, nd.zone))
    key = [tuple(sorted((az[a], az[b]))) for a, b in zip(fl.from_asset, fl.to_asset)]
    assert sorted(key) == PAIRS and list(fm.from_asset) == list(fl.from_asset) and list(fm.to_asset) == list(fl.to_asset), "ABORT: the N-0 folder has other branches"
    order = [PAIRS.index(k) for k in key]
    chk_cap = float(np.abs(fl.capacity.to_numpy() / C0[order] - 1).max()); chk_x = float(np.abs(fm.reactance.to_numpy() / X[order] - 1).max())
    if max(chk_ttc, chk_cap, chk_x) > 1e-6:
        sys.exit(f"ABORT: N-0 not reproduced (TTC {chk_ttc:.2e}, limits {chk_cap:.2e}, reactances {chk_x:.2e})")

    cross = np.flatnonzero(bzone[F] != bzone[T])
    res, status = n1(G, K, ti, tj, cross, D0)
    done = np.array([s == "taken out" for s in status])
    pick = list(np.flatnonzero(done)[:3]) + [int(np.nanargmin(np.nanmin(res[m][0] / T0[None, :], axis=1))) for m in MODES]
    chk_sm = max(float(np.abs(brute(G, K, ti, tj, cross[o], m) / res[m][0][o] - 1).max()) for o in dict.fromkeys(pick) for m in MODES)
    if chk_sm > 1e-6:
        sys.exit(f"ABORT: rank-one update differs from a full inversion ({chk_sm:.2e})")

    def lname(l):
        return f"{bname[G['GA'][l]]} – {bname[G['GB'][l]]}"
    def oname(o):
        r = ld.iloc[cross[o]]; return f"{r.From_node} – {r.To_node} [{r.EIC_Code}]"
    out = {}
    for m in MODES:
        V, Lm = res[m]; Vf = np.where(np.isnan(V), np.inf, V); worst = Vf.argmin(axis=0); v = Vf.min(axis=0)
        ttc = np.minimum(T0, v); bind = v < T0
        out[m] = {"ttc": ttc, "worst": np.where(bind, worst, -1), "lim": np.where(bind, Lm[worst, np.arange(len(ti))], lim0), "C": (ttc[None, :] * A).max(axis=1), "set_by": (ttc[None, :] * A).argmax(axis=1)}
    physical = {tuple(sorted((zones[i], zones[j]))) in adj for i, j in zip(ti, tj)}
    P = pd.DataFrame({"zone_a": [zones[i] for i in ti], "zone_b": [zones[j] for j in tj], "bus_a": [bname[K[i]] for i in ti], "bus_b": [bname[K[j]] for j in tj],
                      "physical_border": [tuple(sorted((zones[i], zones[j]))) in adj for i, j in zip(ti, tj)], "ttc_n0_mw": T0, "limiting_line_n0": [lname(l) for l in lim0]})
    for m in MODES:
        P[f"ttc_n1_{m}_mw"] = out[m]["ttc"]; P[f"ratio_{m}"] = out[m]["ttc"] / T0
        P[f"critical_outage_{m}"] = [oname(o) if o >= 0 else "none (no outage lowers it)" for o in out[m]["worst"]]
        P[f"limiting_line_{m}"] = [lname(l) for l in out[m]["lim"]]
    P.to_csv(OUT / "pairs.csv", index=False)
    Od = ld.iloc[cross][["EIC_Code", "From_node", "To_node", "Voltage_level", "X_pu", "Capacity_MW"]].reset_index(drop=True)
    Od.insert(3, "zone_from", bzone[F[cross]]); Od.insert(4, "zone_to", bzone[T[cross]]); Od["circuits_between_the_two_buses"] = G["GK"][G["pair"][cross]]; Od["status"] = status
    for m in MODES:
        with np.errstate(all="ignore"):
            Od[f"lowest_ratio_{m}"] = np.nanmin(res[m][0] / T0[None, :], axis=1)
        Od[f"pairs_where_critical_{m}"] = [int((out[m]["worst"] == o).sum()) for o in range(len(cross))]
    Od.to_csv(OUT / "outages.csv", index=False)
    Bd = pd.DataFrame({"zone_a": [a for a, _ in PAIRS], "zone_b": [b for _, b in PAIRS], "x_pu": X, "limit_n0_mw": C0, "n0_set_by": [f"{zones[ti[t]]}->{zones[tj[t]]}" for t in (T0[None, :] * A).argmax(axis=1)]})
    for m in MODES:
        Bd[f"limit_n1_{m}_mw"] = out[m]["C"]; Bd[f"ratio_{m}"] = out[m]["C"] / C0; Bd[f"n1_{m}_set_by"] = [f"{zones[ti[t]]}->{zones[tj[t]]}" for t in out[m]["set_by"]]
    Bd.to_csv(OUT / "branches.csv", index=False)
    for m in MODES:
        NETS[m].mkdir(parents=False); f2 = fl.copy(); f2["capacity"] = [f"{v:.10g}" for v in out[m]["C"][order]]
        f2.to_csv(NETS[m] / "flow.csv", index=False); fm.to_csv(NETS[m] / "flow-milestone.csv", index=False); nd.to_csv(NETS[m] / "nodes.csv", index=False)
        (NETS[m] / "README.md").write_text(f"# {NETS[m].name}\n\nThe network of `{BASE_NET.name}` (same branches, same reactances) with branch limits from N-1 transfer limits, mode `{m}`: {MODES[m]}.\n"
                                           f"Built by scripts/77_n1_ttc_tno_method.py; details in `runs/{OUT.name}/`. NOT a Tulipa input (branches and nodes only).\n")
        with open(NETS[m] / "sha256.txt", "w") as fh:
            for p in sorted(NETS[m].iterdir()):
                if p.name != "sha256.txt":
                    fh.write(f"{sha(p)}  {p.name}\n")
    st = pd.Series(status).value_counts().to_dict()
    checks = {"n0_ttc_vs_package_max_rel_diff": chk_ttc, "n0_limits_vs_folder_max_rel_diff": chk_cap, "reactances_vs_folder_max_rel_diff": chk_x,
              "rank_one_update_vs_full_inversion_max_rel_diff": chk_sm, "outages_checked_by_full_inversion": [oname(o) for o in dict.fromkeys(pick)],
              "buses": n, "branch_records": int(len(ld)), "aggregated_lines": int(len(G["GA"])), "cross_zone_records": int(len(cross)), "outage_status": st}
    (OUT / "checks.json").write_text(json.dumps(checks, indent=1))
    q = lambda x: f"{np.median(x):.2f} (lowest {np.min(x):.2f}, highest {np.max(x):.2f})"
    L = [f"# N-1 transfer limits with the method of the TNO MATLAB file — {run.name}", "",
         f"Grid: {n} buses, {len(ld)} branch records = {len(G['GA'])} lines after joining parallel branches. Representative buses: " + "; ".join(f"{z} {flag[z]}" for z in zones) + ".", "",
         f"Outages: {len(cross)} branch records cross a zone border. " + "; ".join(f"{v} {k}" for k, v in st.items()) + ".", "",
         "Checks: N-0 limits against the package " + f"{chk_ttc:.1e}, N-0 branch limits and reactances against `{BASE_NET.name}` {chk_cap:.1e} and {chk_x:.1e}, "
         f"rank-one outage update against a full inversion {chk_sm:.1e} (largest relative differences).", "",
         "## Transfer limit between two zones, N-1 over N-0 (66 pairs)", "", "| mode | median ratio | pairs lowered by more than 1 % | pairs with no change |", "|---|---|---|---|"]
    for m in MODES:
        r = out[m]["ttc"] / T0; L.append(f"| {m} | {q(r)} | {int((r < 0.99).sum())} | {int((r > 1 - 1e-9).sum())} |")
    L += ["", "## Branch limits of the physical-border network (MW)", "", "| branch | reactance p.u. | N-0 | N-1 tno | ratio | N-1 strict | ratio |", "|---|---|---|---|---|---|---|"]
    for r in Bd.itertuples():
        L.append(f"| {r.zone_a}–{r.zone_b} | {r.x_pu:.5f} | {r.limit_n0_mw:,.0f} | {r.limit_n1_tno_mw:,.0f} | {r.ratio_tno:.2f} | {r.limit_n1_strict_mw:,.0f} | {r.ratio_strict:.2f} |")
    L += ["", "## Pairs of neighbouring zones (MW)", "", "| pair | N-0 | N-1 tno | critical outage (tno) | N-1 strict | critical outage (strict) |", "|---|---|---|---|---|---|"]
    for r in P[P.physical_border].itertuples():
        L.append(f"| {r.zone_a}–{r.zone_b} | {r.ttc_n0_mw:,.0f} | {r.ttc_n1_tno_mw:,.0f} | {r.critical_outage_tno} | {r.ttc_n1_strict_mw:,.0f} | {r.critical_outage_strict} |")
    L += ["", "Network folders with these limits: " + ", ".join(f"`inputs/derived/{p.name}`" for p in NETS.values()) + "."]
    (OUT / "report.md").write_text("\n".join(L) + "\n")
    mj = json.loads((OUT / "manifest.json").read_text()); mj["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
    mj["outputs_sha256"] = {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.name != "manifest.json"}
    mj["network_folders"] = {p.name: {q_.name: sha(q_) for q_ in sorted(p.iterdir()) if q_.name != "sha256.txt"} for p in NETS.values()}
    (OUT / "manifest.json").write_text(json.dumps(mj, indent=1))
    print("\n".join(L)); print("\nwritten:", OUT)


if __name__ == "__main__":
    main()
