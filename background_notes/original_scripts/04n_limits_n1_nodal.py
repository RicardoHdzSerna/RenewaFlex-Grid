#!/usr/bin/env python3
# core_grid_dcopf (2026-10-16): copy of archive/dcopf/scripts/120_limits_nodal_n1.py; 3 path/name edit(s), see docs/MAP.md; the original header follows.
"""
120_limits_nodal_n1.py — step 3 (2026-10-16): scripts/83 (N-1 transfer limits with a monitored set and an injection key,
LP envelope on the sparse network) for the NODAL network of scripts/118: one zone at bus resolution (the Netherlands at
380 kV), every other zone one node. Same engine (scripts/77), same method and checks; the "zones" of 83 are the nodes.

    ~/.tulipa_pipeline_venv/bin/python scripts/120_limits_nodal_n1.py runs/<enr-run> <tag> <name>
        --monitored=380kv | eic:<csv with a column eic> | every      which lines may set a limit
        [--key=380kv | one]     where a ZONE node's exchange enters its grid (default 380kv: spread evenly over the zone's
                                380 kV buses, as 83); a nodal bus's exchange always enters at that bus
        [--security=n1all | n1border | n0]                              (default n1all)

Transactions: every pair of the network's nodes (946 for 33 Dutch buses + 11 zones). Transfer limit of a transaction on the
FULL grid (N-1 as 83: every branch record out in turn, the outaged circuit's rating removed from its pair, grid-splitting
outages skipped; only monitored lines may set the limit, every line carries flow and can be an outage), then the LP envelope
C_l = max_t T_t |PTDF_t,l| over the sparse network's branches (reactances and PTDFs reproduced here from the full grid,
checked against the 118 network first, as 83 reproduces 58).

Reads   runs/<enr-run>/outputs + inputs/jao_core.xlsx; inputs/derived/diag_fixedpos_<tag>-sparse-LP (the 118 network;
        its N-0 limits and reactances are reproduced first); runs/*-sparse-fit-nodal-<tag>-sparse-LP/branches.csv
Writes  runs/<today>-limits-nodal-<tag>-<name>/ {manifest.json (first), pairs.csv, branches.csv, monitored_lines.csv,
        branches_for_73.csv, checks.json, report.md}
        inputs/derived/diag_fixedpos_<tag>-sparse-LP-<name>/ (same files as the 118 folder, limits replaced)
Both abort if they exist. No validation data is read.
"""
import collections, datetime, importlib.util, json, sys
from pathlib import Path

import numpy as np, pandas as pd, openpyxl

DCOPF = Path(__file__).resolve().parents[1]
_sp = importlib.util.spec_from_file_location("n1m", DCOPF / "scripts" / "lib_n1_engine.py"); E = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(E)
args = [a for a in sys.argv[1:] if not a.startswith("--")]; opt = lambda k, d: next((a.split("=", 1)[1] for a in sys.argv if a.startswith(f"--{k}=")), d)
if len(args) != 3 or not opt("monitored", None):
    sys.exit(__doc__)
run = Path(args[0]).resolve(); TAG, NAME = args[1], args[2]; MONITORED, KEY, SECURITY = opt("monitored", None), opt("key", "380kv"), opt("security", "n1all")
if KEY not in ("380kv", "one") or SECURITY not in ("n1all", "n1border", "n0") or not (MONITORED in ("380kv", "every") or MONITORED.startswith("eic:")):
    sys.exit(__doc__)
BASE_NET = DCOPF / "inputs" / "derived" / f"diag_fixedpos_{TAG}-sparse-LP"
OUT = DCOPF / "runs" / f"{datetime.date.today().isoformat()}-limits-nodal-{TAG}-{NAME}"; NET = DCOPF / "inputs" / "derived" / f"diag_fixedpos_{TAG}-sparse-LP-{NAME}"
for p in (OUT, NET):
    if p.exists():
        sys.exit(f"ABORT: {p} exists — never overwritten")
fits = sorted((DCOPF / "runs").glob(f"*-sparse-fit-nodal-{TAG}-sparse-LP/branches.csv")); assert len(fits) == 1, f"ABORT: expected one nodal sparse-fit run for {TAG}, found {fits}"
hashes = {}
def rd(p):
    hashes[str(Path(p).resolve().relative_to(DCOPF.parent))] = E.sha(p); return p

man = (run / "manifest.md").read_text()
cfg = {l.split("=")[0].strip(): l.split("=", 1)[1].strip().strip('"') for l in man.splitlines() if " = " in l and not l.startswith("|")}
suf = cfg["suffix"]; O = run / "outputs"
ld = pd.read_csv(rd(O / f"Line_Details_{suf}.csv")); bm = pd.read_csv(rd(O / f"Bus_ID_Map_{suf}.csv"))
wbk = openpyxl.load_workbook(rd(run / "inputs" / cfg["input_filename"]), read_only=True, data_only=True)
f_net = {k: rd(BASE_NET / k) for k in ("flow.csv", "flow-milestone.csv", "nodes.csv")}; fit = pd.read_csv(rd(fits[0]))
eic_list = set(pd.read_csv(rd(Path(MONITORED[4:]).resolve())).eic) if MONITORED.startswith("eic:") else None
OUT.mkdir(parents=False)
CONFIG = {"script": "scripts/04n_limits_n1_nodal.py", "script_sha256": E.sha(Path(__file__)), "engine": "scripts/lib_n1_engine.py", "enr_run": str(run), "tag": TAG, "name": NAME, "base_network": str(BASE_NET),
          "key": {"380kv": "zone node: exchange spread evenly over the zone's 380 kV buses (assumption); nodal bus: at the bus", "one": "every node: all of the exchange at its representative bus"}[KEY],
          "monitored": {"380kv": "lines with both ends at 380 kV", "every": "every line and transformer"}.get(MONITORED, f"lines with a circuit whose EIC is in {MONITORED[4:]}"),
          "security": {"n1all": "every branch record out in turn, its rating removed from its pair; grid-splitting outages skipped", "n1border": "lines crossing a zone border out in turn, ratings unchanged (TNO)", "n0": "no outage"}[SECURITY],
          "transactions": "every pair of nodes of the network", "branch_limits": "LP envelope C_l = max_t T_t |PTDF_t,l| on the sparse nodal network (reactances and PTDFs of the 118 network)", "validation_data_read": "none"}
(OUT / "manifest.json").write_text(json.dumps({"started": datetime.datetime.now().isoformat(timespec="seconds"), "CONFIG": CONFIG, "inputs_sha256": hashes}, indent=1))

nr = list(wbk["Nodes"].iter_rows(values_only=True)); nh = list(nr[0]); col = lambda r, k: r[nh.index(k)]
zone_of = {col(r, "Bus"): col(r, "Zone") for r in nr[1:] if r[0]}
nd = pd.read_csv(f_net["nodes.csv"]); fl = pd.read_csv(f_net["flow.csv"]); fm = pd.read_csv(f_net["flow-milestone.csv"])
nodes = nd.node.tolist(); nk = len(nodes); ni = {c: j for j, c in enumerate(nodes)}
node_zone = dict(zip(nd.node, nd.zone)); node_bus = dict(zip(nd.node, nd.representative_bus)); node_nodal = dict(zip(nd.node, nd.nodal.astype(bool))); a2n = dict(zip(nd.asset, nd.node))
klass = lambda a, b: "nodal-nodal" if node_nodal[a] and node_nodal[b] else ("nodal-zone" if node_nodal[a] or node_nodal[b] else "zone-zone")
PAIRS = [(a2n[a], a2n[b]) for a, b in zip(fl.from_asset, fl.to_asset)]; PSET = {tuple(sorted(p)) for p in PAIRS}
assert len(fm) == len(fl) and (fm.from_asset.map(a2n) == [a for a, _ in PAIRS]).all() and (fm.to_asset.map(a2n) == [b for _, b in PAIRS]).all(), "ABORT: flow.csv and flow-milestone.csv rows differ"
name = dict(zip(bm.new_id, bm.old_name)); ids = sorted(bm.new_id); n = len(ids); pos = {i: j for j, i in enumerate(ids)}; idx_of = {name[i]: pos[i] for i in ids}
bname = [name[i] for i in ids]; bzone = np.array([zone_of[x] for x in bname]); kv = np.array([int(x.rsplit("_", 1)[1]) for x in bname])
F = ld.New_ID_From.map(pos).to_numpy(); T = ld.New_ID_To.map(pos).to_numpy(); K = [idx_of[node_bus[c]] for c in nodes]; ti, tj = E.transactions(nk)
ia = np.array([ni[a] for a, _ in PAIRS]); ib = np.array([ni[b] for _, b in PAIRS])
G = E.prepare(n, F, T, (1.0 / ld.X_pu).to_numpy(float), ld.Capacity_MW.to_numpy(float))
Binv, GA, GB, GBB, GCAP = G["Binv"], G["GA"], G["GB"], G["GBB"], G["GCAP"]
DA = Binv[GA, :] - Binv[GB, :]
X, PT, _ = E.kron_sparse(G, K, ia, ib, nk); A = np.abs(PT[:, ti] - PT[:, tj])


def key(kind):
    W = np.zeros((n, nk))
    for c in nodes:
        if kind == "one" or node_nodal[c]:
            W[idx_of[node_bus[c]], ni[c]] = 1.0
        else:
            z = node_zone[c]; m = (bzone == z) & (kv == 380); assert m.any(), f"ABORT: zone {z} has no 380 kV bus"
            W[m, ni[c]] = 1.0 / m.sum()
    return W


def limits(W, mon, outages=None, tno=True):
    """-> limit per pair of nodes, the line that sets it, the outage (branch record, -1 = none) under which it is set, counts. As 83."""
    D0 = DA @ W; best, bl = E._limit(mon[:, None] * GBB[:, None] * D0 / GCAP[:, None], ti, tj); crit = np.full(len(ti), -1); cnt = collections.Counter()
    for h in (outages if outages is not None else []):
        s, r, b, p = F[h], T[h], G["bb"][h], G["pair"][h]
        if tno and (G["nb"][s] <= 1 or G["nb"][r] <= 1):
            cnt["skipped: an end bus has one neighbour"] += 1; continue
        u = Binv[:, s] - Binv[:, r]; den = 1.0 - b * (u[s] - u[r])
        if den < E.BRIDGE_EPS:
            cnt["skipped: taking it out splits the grid"] += 1; continue
        D = D0 + (b / den) * np.outer(DA[:, s] - DA[:, r], u @ W)
        gbb = GBB.copy(); gbb[p] -= b
        if gbb[p] < 1e-9 * b:
            gbb[p] = 0.0
        cap = GCAP.copy()
        if not tno:
            cap[p] -= G["cap"][h]
        t, l = E._limit(mon[:, None] * gbb[:, None] * D / np.where(cap > 1e-9, cap, np.inf)[:, None], ti, tj)
        m = t < best; best[m] = t[m]; bl[m] = l[m]; crit[m] = h; cnt["taken out"] += 1
    return best, bl, crit, dict(cnt)


every = np.ones(len(GA), bool)
if MONITORED == "380kv":
    mon = (kv[GA] == 380) & (kv[GB] == 380)
elif MONITORED == "every":
    mon = every
else:
    hit = ld.EIC_Code.isin(eic_list).to_numpy(); mon = np.zeros(len(GA), bool); mon[G["pair"][hit]] = True
# the 118 network (N-0 limits, every line monitored, exchange at the representative buses) must come out first
T_now, _, _, _ = limits(key("one"), every); C_now = (T_now[None, :] * A).max(axis=1)
chk = {"present_limits_reproduced_max_rel_diff": float(np.abs(fl.capacity.to_numpy() / C_now - 1).max()), "reactances_reproduced_max_rel_diff": float(np.abs(fm.reactance.to_numpy() / X - 1).max())}
if max(chk.values()) > 1e-6:
    sys.exit(f"ABORT: the 118 network is not reproduced: {chk}")
W = key(KEY)
T0, l0, _, _ = limits(W, mon)
outs = {"n0": None, "n1border": np.flatnonzero(bzone[F] != bzone[T]), "n1all": np.arange(len(ld))}[SECURITY]
T1, l1, crit, cnt = limits(W, mon, outs, tno=(SECURITY != "n1all"))
badm = ~(np.isfinite(T0) & np.isfinite(T1) & (T1 < 1e9))              # inf, or astronomically large from numerical noise: no monitored line carries the exchange
if badm.any():
    bad = [(nodes[ti[t]], nodes[tj[t]]) for t in np.flatnonzero(badm)][:10]
    sys.exit(f"ABORT: {int(badm.sum())} node pair(s) have no monitored line that carries their exchange (intact grid or under outage), e.g. {bad}")
C0 = (T0[None, :] * A).max(axis=1); C1 = (T1[None, :] * A).max(axis=1); setby = (T1[None, :] * A).argmax(axis=1)
lname = lambda l: f"{bname[GA[l]]} – {bname[GB[l]]}"
oname = lambda h: "none" if h < 0 else f"{ld.From_node[h]} – {ld.To_node[h]} [{ld.EIC_Code[h]}]"
tclass = [klass(nodes[i], nodes[j]) for i, j in zip(ti, tj)]
P = pd.DataFrame({"node_a": [nodes[i] for i in ti], "node_b": [nodes[j] for j in tj], "class": tclass, "neighbours": [tuple(sorted((nodes[i], nodes[j]))) in PSET for i, j in zip(ti, tj)],
                  "limit_present_method_n0_mw": T_now, "limit_this_method_n0_mw": T0, "line_setting_it_n0": [lname(l) for l in l0], "limit_this_method_mw": T1, "ratio_to_present": T1 / T_now,
                  "line_setting_it": [lname(l) for l in l1], "under_outage_of": [oname(h) for h in crit]})
P.to_csv(OUT / "pairs.csv", index=False)
rating = {tuple(sorted((a, b))): v for a, b, v in zip(fit.node_a, fit.node_b, fit.rating_sum_MW)}
Bd = pd.DataFrame({"node_a": [a for a, _ in PAIRS], "node_b": [b for _, b in PAIRS], "class": [klass(a, b) for a, b in PAIRS], "x_pu": X, "rating_sum_mw": [rating.get(tuple(sorted(p)), np.nan) for p in PAIRS],
                   "limit_present_mw": C_now, "limit_this_method_n0_mw": C0, "limit_this_method_mw": C1, "ratio_to_present": C1 / C_now, "set_by_exchange": [f"{nodes[ti[t]]}->{nodes[tj[t]]}" for t in setby]})
Bd.to_csv(OUT / "branches.csv", index=False)
pd.DataFrame({"from": [bname[a] for a in GA[mon]], "to": [bname[b] for b in GB[mon]], "kv_from": kv[GA[mon]], "kv_to": kv[GB[mon]], "zone_from": bzone[GA[mon]], "zone_to": bzone[GB[mon]],
              "circuits": G["GK"][mon], "rating_sum_mw": GCAP[mon]}).to_csv(OUT / "monitored_lines.csv", index=False)
zp = {tuple(sorted((a, b))): c for a, b, c in zip(Bd.node_a, Bd.node_b, Bd.limit_this_method_mw)}
f73 = fit.copy(); ph = f73.physical == True; assert int(ph.sum()) == len(PAIRS)
new = [zp[tuple(sorted((a, b)))] for a, b in zip(f73.node_a[ph], f73.node_b[ph])]
f73.loc[ph, "cap_LP_sparse_MW"] = new; f73.loc[ph, "cap_final_MW"] = new; f73.loc[ph, "cap_set_by_txn"] = f"120:{NAME}"
f73.to_csv(OUT / "branches_for_73.csv", index=False)
NET.mkdir(parents=False); f2 = fl.copy(); f2["capacity"] = [f"{v:.10g}" for v in C1]
f2.to_csv(NET / "flow.csv", index=False); fm.to_csv(NET / "flow-milestone.csv", index=False); nd.to_csv(NET / "nodes.csv", index=False)
(NET / "README.md").write_text(f"# {NET.name}\n\nThe network of `{BASE_NET.name}` (same nodes, branches and reactances) with branch limits from scripts/120_limits_nodal_n1.py:\n"
                               + "".join(f"- {k}: {CONFIG[k]}\n" for k in ("transactions", "key", "monitored", "security")) + f"Details in `runs/{OUT.name}/`. NOT a Tulipa input (branches and nodes only).\n")
with open(NET / "sha256.txt", "w") as fh:
    for p in sorted(NET.iterdir()):
        if p.name != "sha256.txt":
            fh.write(f"{E.sha(p)}  {p.name}\n")
nmon = int(mon.sum()); mk = collections.Counter("380 kV line" if a == 380 and b == 380 else ("transformer" if bname[x].rsplit("_", 1)[0] == bname[y].rsplit("_", 1)[0] else "220 kV or other line") for a, b, x, y in zip(kv[GA[mon]], kv[GB[mon]], GA[mon], GB[mon]))
checks = {**chk, "nodes": nk, "transactions": int(len(ti)), "sparse_branches": len(PAIRS), "aggregated_lines": int(len(GA)), "lines_that_may_set_a_limit": nmon, "of_which": dict(mk), "of_which_cross_a_border": int((bzone[GA[mon]] != bzone[GB[mon]]).sum()),
          "buses_380_per_zone": {z: int(((bzone == z) & (kv == 380)).sum()) for z in sorted(set(bzone))}, "outages": cnt, "eic_in_list": (len(eic_list) if eic_list is not None else None),
          "branch_records_with_eic_in_list": (int(ld.EIC_Code.isin(eic_list).sum()) if eic_list is not None else None)}
(OUT / "checks.json").write_text(json.dumps(checks, indent=1))
rat = lambda v: f"{np.median(v):.2f} / {np.min(v):.2f} / {np.max(v):.2f}"
L = [f"# Branch limits of the nodal network — {NAME} ({run.name})", "", f"- nodes: {nk} ({int(sum(node_nodal.values()))} nodal buses + {nk - int(sum(node_nodal.values()))} zone nodes); transactions: {len(ti)}; sparse branches: {len(PAIRS)}",
     f"- exchange enters at: {CONFIG['key']}", f"- lines that may set a limit: {CONFIG['monitored']} — {nmon} of {len(GA)} lines ({', '.join(f'{v} {k}' for k, v in mk.items())}; {checks['of_which_cross_a_border']} cross a border)",
     f"- security: {CONFIG['security']} — " + ("; ".join(f"{v} {k}" for k, v in cnt.items()) or "no outage"),
     f"- check: the 118 network's N-0 limits and reactances are reproduced first ({chk['present_limits_reproduced_max_rel_diff']:.1e}, {chk['reactances_reproduced_max_rel_diff']:.1e})", "",
     "## Transfer limit of a transaction against the N-0 one of 118 (ratio: median / lowest / highest)", "", "| transactions | n | this method without outage | this method |", "|---|---|---|---|",
     f"| all | {len(ti)} | {rat(T0 / T_now)} | {rat(T1 / T_now)} |"]
for k in ("nodal-nodal", "nodal-zone", "zone-zone"):
    m = np.array(tclass) == k
    L.append(f"| {k} | {int(m.sum())} | {rat(T0[m] / T_now[m])} | {rat(T1[m] / T_now[m])} |")
L += ["", "## Branch limits", "", "| branch | class | reactance p.u. | rating sum MW | 118 limit MW (N-0) | this method, no outage | this method | ratio to 118 | this method / rating | set by the exchange |", "|---|---|---|---|---|---|---|---|---|---|"]
for r in Bd.sort_values(["class", "node_a", "node_b"]).to_dict("records"):
    rs = r["rating_sum_mw"]
    L.append(f"| {r['node_a']}–{r['node_b']} | {r['class']} | {r['x_pu']:.5f} | " + (f"{rs:,.0f}" if np.isfinite(rs) else "—") + f" | {r['limit_present_mw']:,.0f} | {r['limit_this_method_n0_mw']:,.0f} | {r['limit_this_method_mw']:,.0f} | {r['ratio_to_present']:.2f} | "
             + (f"{r['limit_this_method_mw'] / rs:.2f}" if np.isfinite(rs) and rs > 0 else "—") + f" | {r['set_by_exchange']} |")
L += ["", "## Neighbouring nodes: transfer limit, the line that sets it, and under which outage", "", "| pair | class | 118 N-0 MW | this method MW | line that sets it | with this line out |", "|---|---|---|---|---|---|"]
for r in P[P.neighbours].sort_values(["class", "node_a", "node_b"]).to_dict("records"):
    L.append(f"| {r['node_a']}–{r['node_b']} | {r['class']} | {r['limit_present_method_n0_mw']:,.0f} | {r['limit_this_method_mw']:,.0f} | {r['line_setting_it']} | {r['under_outage_of']} |")
L += ["", f"Network folder: `inputs/derived/{NET.name}`. For a Tulipa builder: `runs/{OUT.name}/branches_for_73.csv`."]
(OUT / "report.md").write_text("\n".join(L) + "\n")
mj = json.loads((OUT / "manifest.json").read_text()); mj["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
mj["outputs_sha256"] = {p.name: E.sha(p) for p in sorted(OUT.iterdir()) if p.name != "manifest.json"}; mj["network_folder"] = {p.name: E.sha(p) for p in sorted(NET.iterdir()) if p.name != "sha256.txt"}
(OUT / "manifest.json").write_text(json.dumps(mj, indent=1))
print("\n".join(L)); print("\nwritten:", OUT, "and", NET)
