#!/usr/bin/env python3
# 02n2_sparse_network_nodal_hv.py — COPY of 02n_sparse_network_nodal.py (2026-10-19) with ONE addition to the adjacency rule: node pairs
# joined THROUGH eliminated buses of the nodal zone (the Dutch 220 kV network) also get a branch — every pair of nodes attached to one
# connected piece of eliminated nodal-zone buses (e.g. Vierverlaten 380 – Ens 380 through the 220 kV ring once a Vierverlaten 380/220 kV
# transformer exists). Pairs joined only through FOREIGN grids are still dropped. On v29-nl380 the rule adds nothing new (the Groningen
# 220 kV piece joins Eemshaven and Meeden, which a 380 kV line joins already). Header of 02n follows.
# core_grid_dcopf (2026-10-16): copy of archive/dcopf/scripts/118_sparse_fit_nodal.py; 1 path/name edit(s), see docs/MAP.md; the original header follows.
"""
118_sparse_fit_nodal.py — step 3 (2026-10-16): the "sparse" (physical-adjacency) network with LP-envelope limits for a
reduction in which ONE zone is kept at bus resolution (the Netherlands at 380 kV: scripts/117 + 116) and every other zone
is its one representative bus. Generalisation of scripts/58_sparse_fit_split.py from zone-level to node-level adjacency;
the fit itself is unchanged.

    ~/.tulipa_pipeline_venv/bin/python scripts/118_sparse_fit_nodal.py runs/<enr-run> <tag> [--nodal-zone=NL] [--nl-x=kron|physical]

Nodes: every representative bus of the ENR run. A zone with one representative is a zone node (code AT00, BE00, ...); the
nodal zone's buses are nodes of their own (code NL-<bus name without the voltage suffix, spaces as hyphens>).
Physical adjacency (node pairs that get a branch), from the workbook's AC rows (Lines, Tielines, Transformers), each end
mapped to its node (a nodal-zone bus that is a representative -> itself; a nodal-zone bus that is NOT a representative
-> eliminated, no node; a foreign bus -> its zone node):
  * two nodal buses joined by at least one AC row (the Dutch 380 kV line pairs);
  * a nodal bus and a zone joined by at least one AC row (the tie-lines Maasbracht/Doetinchem/Hengelo/Meeden–DE, Maasbracht/Rilland–BE);
  * two zones joined by at least one AC row (BE–NL and DE–NL of 58 are now node–zone pairs).
Node pairs joined only through eliminated buses (the Dutch 220 kV network, the foreign grids) get no branch, like 58's
non-physical zone pairs. The package lists an equivalent branch only where the Kron admittance exceeds 1e-10, so the listed
equivalent is not the complete graph; the dense check uses the listed branches, treats absent package PTDFs as zero and, as 58,
accepts either global sign convention (the package's PTDF sign is the opposite of ours; which one matched is reported).
Reactance: the Kron value of the ENR run (--nl-x=kron, default). --nl-x=physical replaces it, for nodal-bus pairs only, by
the parallel reactance of the physical circuits (variant: how much do the parallel paths through eliminated buses matter).
Limits: LP envelope C_l = max over ALL representative-pair transactions t of (TTC_original_t - DC_t) * |PTDF_t,l| on the
sparse network: the 58 method (N-0, every line of the full grid monitored, exchange at the two buses). The N-1 / monitored /
spread refinements of 83 and 93 follow in a separate script.

Reads  runs/<enr-run>/outputs/{Equivalent_Capacities,TTC_Comparison,PTDF_Reduced_Network}_<suf>.csv, runs/<enr-run>/inputs/jao_core.xlsx
Writes runs/<today>-sparse-fit-nodal-<tag>/ {manifest.md (first), adjacency.csv, branches.csv, ttc_errors.csv,
       ptdf_check_dense_vs_package.csv, ptdf_sparse_vs_dense.csv, report.md}
       inputs/derived/diag_fixedpos_<tag>/ {flow.csv, flow-milestone.csv, nodes.csv, README.md, sha256.txt} (format of 58; read by replay2025/61)
Both abort if they exist. No validation data is read.
"""
import collections, datetime, hashlib, re, sys
from pathlib import Path

import numpy as np, pandas as pd, openpyxl

DCOPF = Path(__file__).resolve().parents[1]
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = lambda k, d: next((a.split("=", 1)[1] for a in sys.argv if a.startswith(f"--{k}=")), d)
if len(ARGS) != 2:
    sys.exit(__doc__)
run = Path(ARGS[0]).resolve(); TAG = ARGS[1]; NODAL = opt("nodal-zone", "NL"); NLX = opt("nl-x", "kron")
if NLX not in ("kron", "physical"):
    sys.exit(__doc__)
TOL_PTDF, WITHIN, YEAR, P_BASE = 1e-6, 20.0, 2035, 100.0
NODE = {"AT": "AT00", "BE": "BE00", "CZ": "CZ00", "DE": "DE00", "FR": "FR00", "HR": "HR00", "HU": "HU00", "NL": "NL00", "PL": "PL00", "RO": "RO00", "SI": "SI00", "SK": "SK00"}
OUT = DCOPF / "runs" / f"{datetime.date.today().isoformat()}-sparse-fit-nodal-{TAG}"
NET = DCOPF / "inputs" / "derived" / f"diag_fixedpos_{TAG}"
for p in (OUT, NET):
    if p.exists():
        sys.exit(f"ABORT: {p} exists — never overwritten; pass another tag")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


inputs_hashed = {}
def rd(p):
    inputs_hashed[str(p.relative_to(DCOPF))] = sha(p); return p


man = (run / "manifest.md").read_text()
cfg = {l.split("=")[0].strip(): l.split("=", 1)[1].strip().strip('"') for l in man.splitlines() if " = " in l and not l.startswith("|")}
suf = cfg["suffix"]; pkg = next((l for l in man.splitlines() if "ElectricityNetworkReduction" in l), "?").strip("| ")
status = next((l for l in man.splitlines() if l.startswith("| Status")), "?")
if "COMPLETED" not in status:
    sys.exit(f"ABORT: ENR run not completed: {status}")
if cfg.get("rep_node_mode") != "manual_excel":
    sys.exit(f"ABORT: rep_node_mode is {cfg.get('rep_node_mode')}; the nodal fit needs the workbook's IsRepresentative selection")
O = run / "outputs"
f_eq, f_ttc, f_pr, f_wb = rd(O / f"Equivalent_Capacities_{suf}.csv"), rd(O / f"TTC_Comparison_{suf}.csv"), rd(O / f"PTDF_Reduced_Network_{suf}.csv"), rd(run / "inputs" / cfg["input_filename"])
OUT.mkdir(parents=False)
CONFIG = {"script": "scripts/02n2_sparse_network_nodal_hv.py", "script_sha256": sha(Path(__file__)), "enr_run": str(run), "tag": TAG, "nodal_zone": NODAL, "nodal_reactance": NLX,
          "adjacency_rule": "AC Lines/Tielines/Transformers rows of the workbook whose two ends map to two different nodes (nodal-zone representative bus -> itself; "
                            "nodal-zone non-representative bus -> none; foreign bus -> its zone); DC links reported, not counted",
          "fit": "LP envelope C_l = max_t (TTC_orig_t - DC_t) * abs(PTDF_t,l) on the sparse network, all representative-pair transactions (58 method, N-0)",
          "package_pruning": "equivalent branches listed by the package only above 1e-10 pu admittance; absent package PTDF entries are taken as 0",
          "ptdf_check_tolerance": TOL_PTDF, "power_base_mva": P_BASE, "zone_node_codes": {z: c for z, c in NODE.items() if z != NODAL}, "validation_data_read": "none"}
(OUT / "manifest.md").write_text("\n".join([f"# Manifest — {OUT.name}", "", f"- started {datetime.datetime.now().isoformat(timespec='seconds')} (this file is written before anything is computed; outputs are appended at the end)",
                                            f"- package (source run): {pkg}", f"- ENR CONFIG of the source run: rep_node_mode={cfg.get('rep_node_mode')}, high_res_zones={cfg.get('high_res_zones')}, "
                                            f"allow_virtual_lines={cfg.get('allow_virtual_lines')}, optimisation_type={cfg.get('optimisation_type')}", "", "## CONFIG", ""]
                                           + [f"- {k}: {v}" for k, v in CONFIG.items()] + ["", "## Input SHA-256", ""] + [f"- `{k}` {v}" for k, v in inputs_hashed.items()]) + "\n")

eq = pd.read_csv(f_eq); ttc = pd.read_csv(f_ttc); pr = pd.read_csv(f_pr)
cf, ct = "from_node", "to_node"
assert {cf, ct} <= set(eq.columns) and eq[cf].map(lambda v: isinstance(v, str)).all()
ac = eq[eq.is_dc == False].reset_index(drop=True); dc = eq[eq.is_dc == True].reset_index(drop=True)
if (ac.X_pu <= 0).any():
    sys.exit(f"ABORT: AC branch(es) with non-positive reactance: {ac[ac.X_pu <= 0][[cf, ct, 'X_pu']].to_dict('records')}")
nodes = sorted(set(ac[cf]) | set(ac[ct])); n = len(nodes); idx = {x: i for i, x in enumerate(nodes)}
# ---- workbook: zones, voltages, representatives, physical rows ----
wb = openpyxl.load_workbook(f_wb, read_only=True, data_only=True)
nr = list(wb["Nodes"].iter_rows(values_only=True)); nh = nr[0]
zone_of = {r[nh.index("Bus")]: r[nh.index("Zone")] for r in nr[1:] if r[0]}
kv_of = {r[nh.index("Bus")]: float(r[nh.index("baseKV")]) for r in nr[1:] if r[0]}
flagged = sorted(r[nh.index("Bus")] for r in nr[1:] if r[0] and r[nh.index("IsRepresentative")] == 1)
if flagged != nodes:
    sys.exit(f"ABORT: the package did not keep the flagged representative buses (silent fallback?): {len(flagged)} flagged vs {len(nodes)} kept")
reps_by_zone = collections.Counter(zone_of[b] for b in nodes)
multi = sorted(z for z, c in reps_by_zone.items() if c > 1)
if multi != [NODAL]:
    sys.exit(f"ABORT: zones with several representatives {multi}; this script handles exactly one nodal zone ({NODAL})")
if set(zone_of.values()) - set(NODE):
    sys.exit(f"ABORT: zone(s) without a node code: {set(zone_of.values()) - set(NODE)}")
slug = lambda b: f"{NODAL}-" + re.sub(r"_\d+$", "", b).replace(" ", "-")
code_of_bus = {b: (slug(b) if zone_of[b] == NODAL else NODE[zone_of[b]]) for b in nodes}
assert len(set(code_of_bus.values())) == n, "ABORT: node codes not unique"
is_nodal = lambda code: code.startswith(f"{NODAL}-")
zone_of_code = {c: zone_of[b] for b, c in code_of_bus.items()}


def nkey(bus):
    z = zone_of.get(bus)
    if z is None:
        return None
    if z == NODAL:
        return code_of_bus.get(bus)                      # None for an eliminated (non-representative) bus of the nodal zone
    return NODE[z]


adj, adj_src, phys, dropped = set(), {}, {}, collections.Counter()
for sh in ("Lines", "Tielines", "Transformers"):
    rows = list(wb[sh].iter_rows(values_only=True)); h = rows[0]
    for r in rows[1:]:
        if not r or not r[0]:
            continue
        fa, tb = r[h.index("From_node")], r[h.index("To_node")]
        ka, kb = nkey(fa), nkey(tb)
        if ka is None or kb is None:
            dropped[f"{sh}: one end eliminated"] += 1; continue
        if ka == kb:
            continue
        key = tuple(sorted((ka, kb))); adj.add(key); adj_src.setdefault(key, collections.Counter())[sh] += 1
        p = phys.setdefault(key, {"n_circuits": 0, "sum_inv_X_ohm": 0.0, "rating_MW": 0.0, "voltages": set()})
        X = r[h.index("X")]; cap = r[h.index("Capacity_MW")]
        p["n_circuits"] += 1; p["rating_MW"] += float(cap or 0.0); p["voltages"].add(float(r[h.index("Voltage_level")]))
        if X and float(X) > 0:
            p["sum_inv_X_ohm"] += 1.0 / float(X)
# ---- 02n2: pairs joined through eliminated buses of the nodal zone
elim = {b for b, z in zone_of.items() if z == NODAL and nkey(b) is None}
par_e = {b: b for b in elim}
def fnd(x):
    while par_e[x] != x:
        par_e[x] = par_e[par_e[x]]; x = par_e[x]
    return x
touch_e = []
for sh in ("Lines", "Tielines", "Transformers"):
    rows = list(wb[sh].iter_rows(values_only=True)); h = rows[0]
    for r in rows[1:]:
        if not r or not r[0]:
            continue
        fa, tb = r[h.index("From_node")], r[h.index("To_node")]
        if fa in elim and tb in elim:
            par_e[fnd(fa)] = fnd(tb)
        elif fa in elim and nkey(tb):
            touch_e.append((fa, nkey(tb)))
        elif tb in elim and nkey(fa):
            touch_e.append((tb, nkey(fa)))
attach = collections.defaultdict(set)
for e, k in touch_e:
    attach[fnd(e)].add(k)
via = {tuple(sorted((a, b))) for ks in attach.values() for a in ks for b in ks if a != b}
via_new = sorted(via - adj)
for key in via:
    adj.add(key); adj_src.setdefault(key, collections.Counter())["via eliminated nodal-zone buses"] += 1
VIA_TEXT = (f"pieces of eliminated {NODAL} buses: {len(attach)}, attached to " + "; ".join(sorted("{" + ", ".join(sorted(ks)) + "}" for ks in attach.values()))
            + f"; pairs joined through them: {len(via)}, of which new (no direct row): {', '.join(f'{a}–{b}' for a, b in via_new) or 'none'}")
print(VIA_TEXT)
adj_dc = set()
if "DCLines" in wb.sheetnames:
    rows = list(wb["DCLines"].iter_rows(values_only=True)); h = rows[0]
    for r in rows[1:]:
        if r and r[0]:
            ka, kb = nkey(r[h.index("From_node")]), nkey(r[h.index("To_node")])
            if ka and kb and ka != kb:
                adj_dc.add(tuple(sorted((ka, kb))))
klass = lambda a, b: "nodal-nodal" if is_nodal(a) and is_nodal(b) else ("nodal-zone" if is_nodal(a) or is_nodal(b) else "zone-zone")
for key, p in phys.items():                                                       # physical reactance of the circuits in parallel, in p.u. on the row voltage
    p["X_phys_pu"] = (1.0 / p["sum_inv_X_ohm"]) / (max(p["voltages"]) ** 2 / P_BASE) if p["sum_inv_X_ohm"] > 0 else np.nan
pd.DataFrame([{"node_a": a, "node_b": b, "class": klass(a, b), "ac_rows": sum(adj_src[(a, b)].values()), **adj_src[(a, b)], "n_circuits": phys.get((a, b), {"n_circuits": 0, "rating_MW": np.nan, "X_phys_pu": np.nan})["n_circuits"],
               "rating_sum_MW": phys.get((a, b), {"n_circuits": 0, "rating_MW": np.nan, "X_phys_pu": np.nan})["rating_MW"], "X_phys_pu": phys.get((a, b), {"n_circuits": 0, "rating_MW": np.nan, "X_phys_pu": np.nan})["X_phys_pu"], "dc_link": (a, b) in adj_dc} for a, b in sorted(adj)]
             + [{"node_a": a, "node_b": b, "class": klass(a, b), "ac_rows": 0, "dc_link": True} for a, b in sorted(adj_dc - adj)]).to_csv(OUT / "adjacency.csv", index=False)
# ---- branch table of the listed equivalent ----
ac["node_a"] = ac[cf].map(code_of_bus); ac["node_b"] = ac[ct].map(code_of_bus)
ac["key"] = [tuple(sorted((a, b))) for a, b in zip(ac.node_a, ac.node_b)]
ac["class"] = [klass(*k) for k in ac.key]
ac["physical"] = ac.key.isin(adj); ac["physical_dc_only"] = ac.key.isin(adj_dc - adj)
ac["X_kron_pu"] = ac.X_pu
ac["X_phys_pu"] = ac.key.map(lambda k: phys[k]["X_phys_pu"] if k in phys else np.nan)
ac["n_circuits"] = ac.key.map(lambda k: phys[k]["n_circuits"] if k in phys else 0)
ac["rating_sum_MW"] = ac.key.map(lambda k: phys[k]["rating_MW"] if k in phys else np.nan)
missing_phys = sorted(adj - set(ac.key))
if missing_phys:
    sys.exit(f"ABORT: physical node pair(s) without a listed equivalent branch: {missing_phys}")
if NLX == "physical":
    m = ac.physical & (ac["class"] == "nodal-nodal") & ac.X_phys_pu.notna()
    ac.loc[m, "X_pu"] = ac.loc[m, "X_phys_pu"]
keep = list(range(1, n))                          # slack = first node; transaction PTDFs do not depend on it


def build(br):
    B = np.zeros((n, n))
    for _, r in br.iterrows():
        i, j = idx[r[cf]], idx[r[ct]]; b = 1.0 / r.X_pu; B[i, i] += b; B[j, j] += b; B[i, j] -= b; B[j, i] -= b
    Binv = np.zeros((n, n)); Binv[np.ix_(keep, keep)] = np.linalg.inv(B[np.ix_(keep, keep)])
    return Binv


def n_components(br):
    parent = list(range(n))
    def f(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]; x = parent[x]
        return x
    for _, r in br.iterrows():
        parent[f(idx[r[cf]])] = f(idx[r[ct]])
    return len({f(x) for x in range(n)})


dense = ac.copy(); dense["X_pu"] = dense.X_kron_pu          # the dense check is always against the package's own reactances
sparse = ac[ac.physical].reset_index(drop=True)
if n_components(sparse) > 1:
    sys.exit("ABORT: the physical-only network is not connected")
Bdi, Bsi = build(dense), build(sparse)
txns = list(zip(ttc.From_node, ttc.To_node)); assert len(txns) == n * (n - 1) // 2, "ABORT: TTC_Comparison is not the full pair set"


def ptdf_matrix(br, Binv):
    F = np.array([idx[x] for x in br[cf]]); T = np.array([idx[x] for x in br[ct]]); bb = 1.0 / br.X_pu.values
    P = np.zeros((len(txns), len(br)))
    for t, (a, b) in enumerate(txns):
        inj = np.zeros(n); inj[idx[a]] += 1; inj[idx[b]] -= 1; th = Binv @ inj
        P[t] = bb * (th[F] - th[T])
    return P


Pd, Ps = ptdf_matrix(dense, Bdi), ptdf_matrix(sparse, Bsi)
pk = {(r.txn_from_name, r.txn_to_name, r.line_from_name, r.line_to_name): r.PTDF_value for r in pr.itertuples()}
chk, n_absent = [], 0
for t, (a, b) in enumerate(txns):
    for l, r in dense.iterrows():
        v = pk.get((a, b, r[cf], r[ct]))
        if v is None:
            rv = pk.get((a, b, r[ct], r[cf]))
            if rv is None:
                v = 0.0; n_absent += 1
            else:
                v = -rv
        chk.append({"txn": f"{a}->{b}", "branch": f"{r[cf]}-{r[ct]}", "ours": Pd[t, l], "package": v, "diff": Pd[t, l] - v})
chk = pd.DataFrame(chk); chk.to_csv(OUT / "ptdf_check_dense_vs_package.csv", index=False)
md_same, md_flip = float(chk["diff"].abs().max()), float((chk.ours + chk.package).abs().max())
SIGN = "same" if md_same <= md_flip else "opposite"; maxdiff = min(md_same, md_flip)   # as 58: the package's PTDF sign convention may be the opposite of ours (it is); either global convention is accepted
if maxdiff > TOL_PTDF:
    sys.exit(f"ABORT: dense PTDF check against the package failed: max |diff| {maxdiff:.3e} with the {SIGN} sign convention ({n_absent} entries absent in the package file, taken as 0)")
# ---- sparse vs dense PTDFs on the physical branches (what the sparsification changes) ----
dpos = {k: i for i, k in enumerate(dense.key)}
svd = pd.DataFrame({"node_a": sparse.node_a, "node_b": sparse.node_b, "class": sparse["class"],
                    "ptdf_max_abs_diff": [np.abs(Ps[:, l] - Pd[:, dpos[k]]).max() for l, k in enumerate(sparse.key)],
                    "ptdf_rms_diff": [np.sqrt(np.mean((Ps[:, l] - Pd[:, dpos[k]]) ** 2)) for l, k in enumerate(sparse.key)],
                    "ptdf_rms_dense": [np.sqrt(np.mean(Pd[:, dpos[k]] ** 2)) for k in sparse.key]})
svd.to_csv(OUT / "ptdf_sparse_vs_dense.csv", index=False)
# ---- LP envelope ----
dcmap = {tuple(sorted((code_of_bus[r[cf]], code_of_bus[r[ct]]))): r.capacity_MW for _, r in dc.iterrows()}
ttc["node_a"] = [code_of_bus[a] for a, _ in txns]; ttc["node_b"] = [code_of_bus[b] for _, b in txns]
ttc["pair"] = [tuple(sorted((a, b))) for a, b in zip(ttc.node_a, ttc.node_b)]
ttc["class"] = [klass(*p) for p in ttc.pair]
ttc["dc_MW"] = ttc.pair.map(dcmap).fillna(0.0)
target = (ttc.TTC_Original_MW - ttc.dc_MW).clip(lower=0).values


def fit(P):
    M = target[:, None] * np.abs(P)
    return M.max(axis=0), M.argmax(axis=0)


def implied(P, C):
    A = np.abs(P); out = np.full(len(txns), np.inf)
    for t in range(len(txns)):
        m = A[t] > 1e-9
        if m.any():
            out[t] = (C[m] / A[t, m]).min()
    return out + ttc.dc_MW.values


Cd, _ = fit(Pd); Cs, arg = fit(Ps)
set_by = [f"{ttc.node_a[t]}->{ttc.node_b[t]}" for t in arg]
Td, Ts = implied(Pd, Cd), implied(Ps, Cs)
ttc["ttc_implied_dense"] = Td; ttc["ttc_implied_sparse"] = Ts
ttc["err_dense_pct"] = 100 * (Td - ttc.TTC_Original_MW) / ttc.TTC_Original_MW; ttc["err_sparse_pct"] = 100 * (Ts - ttc.TTC_Original_MW) / ttc.TTC_Original_MW
ttc[["class", "node_a", "node_b", "From_node", "To_node", "TTC_Original_MW", "dc_MW", "ttc_implied_dense", "ttc_implied_sparse", "err_dense_pct", "err_sparse_pct"]].to_csv(OUT / "ttc_errors.csv", index=False)
sparse = sparse.copy()
sparse["cap_LP_sparse_MW"] = Cs; sparse["cap_set_by_txn"] = set_by; sparse["cap_final_MW"] = Cs
sparse = sparse.merge(svd[["node_a", "node_b", "ptdf_max_abs_diff", "ptdf_rms_diff"]], on=["node_a", "node_b"], how="left")
br = dense.copy(); br["cap_LP_dense_MW"] = Cd
br = br.merge(sparse[[cf, ct, "cap_LP_sparse_MW", "cap_set_by_txn", "cap_final_MW", "ptdf_max_abs_diff", "ptdf_rms_diff"]], on=[cf, ct], how="left")
br["X_used_pu"] = ac.X_pu
br[[cf, ct, "node_a", "node_b", "class", "physical", "physical_dc_only", "X_used_pu", "X_kron_pu", "X_phys_pu", "n_circuits", "rating_sum_MW", "capacity_MW", "cap_LP_dense_MW", "cap_LP_sparse_MW",
    "cap_set_by_txn", "cap_final_MW", "ptdf_max_abs_diff", "ptdf_rms_diff"]].rename(columns={"capacity_MW": f"cap_package_{suf}_MW"}).to_csv(OUT / "branches.csv", index=False)
assert (sparse.cap_final_MW > 0).all() and np.isfinite(sparse.cap_final_MW).all() and (sparse.X_pu > 0).all()

# ---- minimal network folder (what the fixed-position test reads) ----
NET.mkdir(parents=False)
asset = lambda code: f"{code}_E_Demand_{YEAR}"
pd.DataFrame({"capacity": sparse.cap_final_MW.map(lambda v: f"{v:.10g}"), "carrier": "electricity", "discount_rate": "", "economic_lifetime": "", "from_asset": sparse.node_a.map(asset),
              "investment_integer": "", "is_transport": "true", "technical_lifetime": "", "to_asset": sparse.node_b.map(asset)}).to_csv(NET / "flow.csv", index=False)
pd.DataFrame({"commodity_price": 0.0, "dc_opf": "true", "from_asset": sparse.node_a.map(asset), "investable": "false", "milestone_year": YEAR, "operational_cost": 0.0,
              "reactance": sparse.X_pu.map(lambda v: f"{v:.12g}"), "to_asset": sparse.node_b.map(asset)}).to_csv(NET / "flow-milestone.csv", index=False)
pd.DataFrame([{"node": code_of_bus[b], "asset": asset(code_of_bus[b]), "zone": zone_of[b], "representative_bus": b, "baseKV": kv_of[b], "nodal": is_nodal(code_of_bus[b])} for b in nodes]).to_csv(NET / "nodes.csv", index=False)
(NET / "README.md").write_text(f"# {NET.name}\n\nMinimal network folder for replay2025's fixed-position test (scripts/61): ONLY the dc_opf branches (flow.csv, flow-milestone.csv) and nodes.csv. "
                               f"NOT a Tulipa input (no assets, no profiles).\n\nNodal zone {NODAL}: {reps_by_zone[NODAL]} buses as nodes (codes {NODAL}-<bus>); every other zone one node. "
                               f"Reactances: {'Kron equivalent of the ENR run' if NLX == 'kron' else 'Kron equivalent, except the nodal-zone line pairs which carry the physical parallel reactance'}; "
                               f"limits: LP envelope of the full-grid N-0 transfer limits (58 method).\n\nBuilt by scripts/118_sparse_fit_nodal.py from `{run.name}`; fit details in `runs/{OUT.name}/`.\n")
with open(NET / "sha256.txt", "w") as fh:
    for p in sorted(NET.iterdir()):
        if p.name != "sha256.txt":
            fh.write(f"{sha(p)}  {p.name}\n")


def stats(e):
    e = np.asarray(e); return f"{np.median(e):+.1f} | {np.percentile(e, 10):+.1f} | {np.percentile(e, 90):+.1f} | {e.min():+.1f} | {e.max():+.1f} | {int((np.abs(e) <= WITHIN).sum())}/{len(e)} | {int((np.abs(e) < 1e-6).sum())}"


cc = collections.Counter(ac["class"]); cs = collections.Counter(sparse["class"])
L = [f"# Nodal sparse network with LP-envelope limits — {run.name} (nodal zone {NODAL}, reactance {NLX})", "",
     f"{n} nodes: {reps_by_zone[NODAL]} buses of {NODAL} + {n - reps_by_zone[NODAL]} zone nodes (" + ", ".join(f"{NODE[z]} = {b}" for b in nodes if zone_of[b] != NODAL for z in [zone_of[b]]) + ")", "",
     f"- listed equivalent branches: {len(ac)} of {n * (n - 1) // 2} pairs (package prunes below 1e-10 pu admittance): " + ", ".join(f"{k} {v}" for k, v in sorted(cc.items())),
     f"- physical adjacency ({len(adj)} pairs, `adjacency.csv`): " + ", ".join(f"{k} {v}" for k, v in sorted(cs.items())) + f"; workbook rows with one end eliminated (no adjacency): {dict(dropped)}",
     f"- 02n2 rule: {VIA_TEXT}",
     f"- DC links: " + (", ".join(f"{code_of_bus[r[cf]]}–{code_of_bus[r[ct]]} {r.capacity_MW:.0f} MW" for _, r in dc.iterrows()) or "none"),
     f"- dense PTDFs vs the package's `PTDF_Reduced_Network_{suf}.csv`: {len(chk)} entries, max |diff| {maxdiff:.2e} with the {SIGN} global sign convention (tolerance {TOL_PTDF}; {n_absent} entries absent in the package file, taken as 0)", "",
     "## Pairwise TTC error vs the full-grid TTC (%, LP envelope on each network)", "",
     "| network / transactions | n | median | p10 | p90 | min | max | within ±20 % | exact |", "|---|---|---|---|---|---|---|---|---|",
     f"| dense, all | {len(ttc)} | {stats(ttc.err_dense_pct)} |", f"| sparse, all | {len(ttc)} | {stats(ttc.err_sparse_pct)} |"]
for k in ("nodal-nodal", "nodal-zone", "zone-zone"):
    m = ttc["class"] == k
    L.append(f"| sparse, {k} | {int(m.sum())} | {stats(ttc.err_sparse_pct[m])} |")
L += ["", "## Sparsification: PTDF of the physical branches, sparse vs dense (over all transactions)", "",
      "| class | branches | max |diff| | median rms diff | median rms of the dense PTDF |", "|---|---|---|---|---|"]
for k in ("nodal-nodal", "nodal-zone", "zone-zone"):
    s = svd[svd["class"] == k]
    L.append(f"| {k} | {len(s)} | {s.ptdf_max_abs_diff.max():.3f} | {s.ptdf_rms_diff.median():.4f} | {s.ptdf_rms_dense.median():.4f} |")
L += ["", "## Sparse branches", "", "| branch | class | X used p.u. | X Kron p.u. | X physical p.u. | circuits | rating sum MW | LP capacity MW | cap / rating | set by transaction | PTDF max diff |", "|---|---|---|---|---|---|---|---|---|---|---|"]
for r in sparse.sort_values(["class", "node_a", "node_b"]).to_dict("records"):            # dict rows: itertuples renames a column called "class"
    rat = r["rating_sum_MW"]
    L.append(f"| {r['node_a']}–{r['node_b']} | {r['class']} | {r['X_pu']:.5f} | {r['X_kron_pu']:.5f} | " + (f"{r['X_phys_pu']:.5f}" if np.isfinite(r['X_phys_pu']) else "—") + f" | {r['n_circuits']} | "
             + (f"{rat:,.0f}" if np.isfinite(rat) else "—") + f" | {r['cap_LP_sparse_MW']:,.0f} | " + (f"{r['cap_LP_sparse_MW'] / rat:.2f}" if np.isfinite(rat) and rat > 0 else "—")
             + f" | {r['cap_set_by_txn']} | {r['ptdf_max_abs_diff']:.3f} |")
L += ["", f"Network folder: `inputs/derived/{NET.name}` (flow.csv, flow-milestone.csv, nodes.csv)."]
(OUT / "report.md").write_text("\n".join(L) + "\n")
with open(OUT / "manifest.md", "a") as fh:
    fh.write("\n## Outputs (sha256)\n\n" + "\n".join(f"- `{p.name}` {sha(p)}" for p in sorted(OUT.iterdir()) if p.name != "manifest.md") + "\n"
             + f"\n## Network folder\n\n- `inputs/derived/{NET.name}/` " + "; ".join(f"{p.name} {sha(p)}" for p in sorted(NET.iterdir()) if p.name != "sha256.txt") + f"\n\nfinished {datetime.datetime.now().isoformat(timespec='seconds')}\n")
print("\n".join(L)); print("\nwritten:", OUT, "and", NET)
