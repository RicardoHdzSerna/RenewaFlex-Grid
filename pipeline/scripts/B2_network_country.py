#!/usr/bin/env python3
"""
B2_network_country.py — the reduced network with one node per country (the Netherlands one node too).

STEP  B2 in run_all.sh (HANDOVER.md section 4.4: the two country-level networks)

WHAT IT DOES
  As B2_network_nodal.py, but every zone is one node: the branches are the zone pairs with at least one line, tie-line or
  transformer between them (19 branches; 22 with Germany split), with their Kron reactances and the N-0 envelope limits.
  --unlimited=<ZA>:<ZB> gives one branch an unlimited capacity (not used for the networks in use).

READS   runs/<reduction run>/outputs/ and its inputs/jao_core.xlsx
WRITES  runs/<today>-sparse-fit-<tag>/ and inputs/derived/diag_fixedpos_<tag>/ (flow.csv, flow-milestone.csv, nodes.csv, ...).
        Both abort if they exist.

USAGE   python scripts/B2_network_country.py runs/<reduction run> <tag> [--unlimited=DE_N:DE_S]

HISTORY Same code as core_grid_dcopf/scripts/02_sparse_network.py (archived 58_sparse_fit_split.py); only this header was
        rewritten (the scripts as run, with their history notes, are in background_notes/original_scripts/).
"""
import datetime, hashlib, sys
from pathlib import Path

import numpy as np, pandas as pd, openpyxl

DCOPF = Path(__file__).resolve().parents[1]
ARGS = [a for a in sys.argv[1:] if not a.startswith("--")]
run = Path(ARGS[0]).resolve(); TAG = ARGS[1]
UNLIMITED = next((tuple(sorted(a.split("=", 1)[1].split(":"))) for a in sys.argv if a.startswith("--unlimited=")), None)
UNLIMITED_MW = 1.0e6            # "effectively unlimited": far above any conceivable flow; the test asserts it never binds
TOL_PTDF, WITHIN, YEAR, P_BASE = 1e-6, 20.0, 2035, 100.0
NODE = {"AT": "AT00", "BE": "BE00", "CZ": "CZ00", "DE": "DE00", "DE_N": "DE0N", "DE_S": "DE0S", "FR": "FR00", "HR": "HR00", "HU": "HU00",
        "NL": "NL00", "PL": "PL00", "RO": "RO00", "SI": "SI00", "SK": "SK00"}
OUT = DCOPF / "runs" / f"{datetime.date.today().isoformat()}-sparse-fit-{TAG}"
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
O = run / "outputs"
f_eq, f_ttc, f_pr, f_wb = rd(O / f"Equivalent_Capacities_{suf}.csv"), rd(O / f"TTC_Comparison_{suf}.csv"), rd(O / f"PTDF_Reduced_Network_{suf}.csv"), rd(run / "inputs" / cfg["input_filename"])
OUT.mkdir(parents=False)
CONFIG = {"script": "scripts/B2_network_country.py", "script_sha256": sha(Path(__file__)), "enr_run": str(run), "tag": TAG, "unlimited_pair": UNLIMITED, "unlimited_mw": UNLIMITED_MW,
          "adjacency_rule": "AC Lines/Tielines/Transformers rows of the workbook crossing a zone border; DC links reported, not counted",
          "fit": "LP envelope C_l = max_t (TTC_orig_t - DC_t) * abs(PTDF_t,l) on the sparse network, all zone pairs as transactions",
          "ptdf_check_tolerance": TOL_PTDF, "power_base_mva": P_BASE, "node_codes": NODE, "validation_data_read": "none"}
(OUT / "manifest.md").write_text("\n".join([f"# Manifest — {OUT.name}", "", f"- started {datetime.datetime.now().isoformat(timespec='seconds')} (this file is written before anything is computed; outputs are appended at the end)",
                                            f"- package (source run): {pkg}", f"- ENR CONFIG of the source run: rep_node_mode={cfg.get('rep_node_mode')}, rep_node_k_per_zone={cfg.get('rep_node_k_per_zone')}, "
                                            f"allow_virtual_lines={cfg.get('allow_virtual_lines')}, optimisation_type={cfg.get('optimisation_type')}", "", "## CONFIG", ""]
                                           + [f"- {k}: {v}" for k, v in CONFIG.items()] + ["", "## Input SHA-256", ""] + [f"- `{k}` {v}" for k, v in inputs_hashed.items()]) + "\n")

eq = pd.read_csv(f_eq); ttc = pd.read_csv(f_ttc); pr = pd.read_csv(f_pr)
cf, ct = "from_node", "to_node"
assert {cf, ct} <= set(eq.columns) and eq[cf].map(lambda v: isinstance(v, str)).all()
ac = eq[eq.is_dc == False].reset_index(drop=True); dc = eq[eq.is_dc == True].reset_index(drop=True)
if (ac.X_pu <= 0).any():
    sys.exit(f"ABORT: AC branch(es) with non-positive reactance: {ac[ac.X_pu <= 0][[cf, ct, 'X_pu']].to_dict('records')}")
nodes = sorted(set(ac[cf]) | set(ac[ct])); n = len(nodes); idx = {x: i for i, x in enumerate(nodes)}
assert len(ac) == n * (n - 1) // 2, f"ABORT: {len(ac)} AC branches but {n} nodes -> not the complete Kron equivalent"
# ---- zones and physical adjacency from the workbook ----
wb = openpyxl.load_workbook(f_wb, read_only=True, data_only=True)
nr = list(wb["Nodes"].iter_rows(values_only=True)); nh = nr[0]
zone_of = {r[nh.index("Bus")]: r[nh.index("Zone")] for r in nr[1:] if r[0]}
flagged = sorted(r[nh.index("Bus")] for r in nr[1:] if r[0] and r[nh.index("IsRepresentative")] == 1)
zone = {x: zone_of[x] for x in nodes}; assert len(set(zone.values())) == n, "ABORT: two representative buses in one zone"
if cfg.get("rep_node_mode") == "manual_excel" and flagged != nodes:
    sys.exit(f"ABORT: the package did not keep the flagged representative buses (silent fallback?): flagged {flagged} vs kept {nodes}")
if set(zone.values()) - set(NODE):
    sys.exit(f"ABORT: zone(s) without a node code: {set(zone.values()) - set(NODE)}")
zrep = {z: x for x, z in zone.items()}
adj_ac, adj_src = set(), {}
for sh in ("Lines", "Tielines", "Transformers"):
    rows = list(wb[sh].iter_rows(values_only=True)); h = rows[0]
    for r in rows[1:]:
        if not r or not r[0]:
            continue
        za, zb = zone_of.get(r[h.index("From_node")]), zone_of.get(r[h.index("To_node")])
        if za and zb and za != zb:
            key = tuple(sorted((za, zb))); adj_ac.add(key); adj_src.setdefault(key, {}).setdefault(sh, 0); adj_src[key][sh] += 1
adj_dc = set()
if "DCLines" in wb.sheetnames:
    rows = list(wb["DCLines"].iter_rows(values_only=True)); h = rows[0]
    for r in rows[1:]:
        if not r or not r[0]:
            continue
        za, zb = zone_of.get(r[h.index("From_node")]), zone_of.get(r[h.index("To_node")])
        if za and zb and za != zb:
            adj_dc.add(tuple(sorted((za, zb))))
adj = set(adj_ac); dc_only = adj_dc - adj_ac
pd.DataFrame([{"zone_a": a, "zone_b": b, "ac_branches": sum(adj_src[(a, b)].values()), **adj_src[(a, b)], "dc_link": (a, b) in adj_dc} for a, b in sorted(adj)]
             + [{"zone_a": a, "zone_b": b, "ac_branches": 0, "dc_link": True} for a, b in sorted(dc_only)]).to_csv(OUT / "adjacency.csv", index=False)
if UNLIMITED and UNLIMITED not in adj:
    sys.exit(f"ABORT: --unlimited pair {UNLIMITED} is not a physical pair of this network")
ac["zone_a"] = ac[cf].map(zone); ac["zone_b"] = ac[ct].map(zone)
ac["pair"] = [tuple(sorted((a, b))) for a, b in zip(ac.zone_a, ac.zone_b)]
ac["physical"] = ac.pair.isin(adj); ac["physical_dc_only"] = ac.pair.isin(dc_only)
keep = list(range(1, n))                         # slack = first node; transaction PTDFs do not depend on it


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


dense = ac; sparse = ac[ac.physical].reset_index(drop=True)
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
chk = []
for t, (a, b) in enumerate(txns):
    for l, r in dense.iterrows():
        v = pk.get((a, b, r[cf], r[ct]))
        if v is None:
            v = -pk.get((a, b, r[ct], r[cf]), np.nan)
        chk.append({"txn": f"{a}->{b}", "branch": f"{r[cf]}-{r[ct]}", "ours": Pd[t, l], "package": v, "diff": Pd[t, l] - v})
chk = pd.DataFrame(chk); chk.to_csv(OUT / "ptdf_check_dense_vs_package.csv", index=False)
n_missing = int(chk.package.isna().sum()); maxdiff = min(float(chk["diff"].abs().max()), float((chk.ours + chk.package).abs().max()))
if n_missing or maxdiff > TOL_PTDF:
    sys.exit(f"ABORT: dense PTDF check against the package failed: {n_missing} missing entries, max |diff| {maxdiff:.3e}")
# ---- LP envelope ----
dcmap = {tuple(sorted((zone[r[cf]], zone[r[ct]]))): r.capacity_MW for _, r in dc.iterrows()}
ttc["pair"] = [tuple(sorted((zone[a], zone[b]))) for a, b in txns]
ttc["dc_MW"] = ttc.pair.map(dcmap).fillna(0.0)
target = (ttc.TTC_Original_MW - ttc.dc_MW).clip(lower=0).values


def fit(P, mask=None):
    M = target[:, None] * np.abs(P)
    if mask is not None:
        M = M[mask]
    return M.max(axis=0), M.argmax(axis=0)


def implied(P, C):
    A = np.abs(P); out = np.full(len(txns), np.inf)
    for t in range(len(txns)):
        m = A[t] > 1e-9
        if m.any():
            out[t] = (C[m] / A[t, m]).min()
    return out + ttc.dc_MW.values


Cd, _ = fit(Pd); Cs, arg = fit(Ps)
set_by = [f"{zone[txns[t][0]]}->{zone[txns[t][1]]}" for t in arg]
internal_txn = np.array([p == UNLIMITED for p in ttc.pair]) if UNLIMITED else np.zeros(len(txns), bool)
Cs_noint = fit(Ps, ~internal_txn)[0] if UNLIMITED else Cs.copy()
Td, Ts = implied(Pd, Cd), implied(Ps, Cs)
ttc["ttc_implied_dense"] = Td; ttc["ttc_implied_sparse"] = Ts
ttc["err_dense_pct"] = 100 * (Td - ttc.TTC_Original_MW) / ttc.TTC_Original_MW; ttc["err_sparse_pct"] = 100 * (Ts - ttc.TTC_Original_MW) / ttc.TTC_Original_MW
ttc["zone_from"] = [zone[a] for a, _ in txns]; ttc["zone_to"] = [zone[b] for _, b in txns]
ttc[["zone_from", "zone_to", "From_node", "To_node", "TTC_Original_MW", "dc_MW", "ttc_implied_dense", "ttc_implied_sparse", "err_dense_pct", "err_sparse_pct"]].to_csv(OUT / "ttc_errors.csv", index=False)
sparse = sparse.copy()
sparse["cap_LP_sparse_MW"] = Cs; sparse["cap_set_by_txn"] = set_by; sparse["cap_LP_sparse_noint_MW"] = Cs_noint
sparse["cap_final_MW"] = [UNLIMITED_MW if (UNLIMITED and p == UNLIMITED) else c for p, c in zip(sparse.pair, Cs)]
sparse["unlimited_override"] = [bool(UNLIMITED and p == UNLIMITED) for p in sparse.pair]
br = dense.copy(); br["cap_LP_dense_MW"] = Cd
br = br.merge(sparse[[cf, ct, "cap_LP_sparse_MW", "cap_set_by_txn", "cap_LP_sparse_noint_MW", "cap_final_MW", "unlimited_override"]], on=[cf, ct], how="left")
br[[cf, ct, "zone_a", "zone_b", "physical", "physical_dc_only", "X_pu", "capacity_MW", "cap_LP_dense_MW", "cap_LP_sparse_MW", "cap_set_by_txn", "cap_LP_sparse_noint_MW", "cap_final_MW", "unlimited_override"]] \
    .rename(columns={"capacity_MW": f"cap_package_{suf}_MW"}).to_csv(OUT / "branches.csv", index=False)
assert (sparse.cap_final_MW > 0).all() and np.isfinite(sparse.cap_final_MW).all() and (sparse.X_pu > 0).all()

# ---- minimal network folder (what the fixed-position test reads) ----
NET.mkdir(parents=False)
asset = lambda z: f"{NODE[z]}_E_Demand_{YEAR}"
pd.DataFrame({"capacity": sparse.cap_final_MW.map(lambda v: f"{v:.10g}"), "carrier": "electricity", "discount_rate": "", "economic_lifetime": "", "from_asset": sparse.zone_a.map(asset),
              "investment_integer": "", "is_transport": "true", "technical_lifetime": "", "to_asset": sparse.zone_b.map(asset)}).to_csv(NET / "flow.csv", index=False)
pd.DataFrame({"commodity_price": 0.0, "dc_opf": "true", "from_asset": sparse.zone_a.map(asset), "investable": "false", "milestone_year": YEAR, "operational_cost": 0.0,
              "reactance": sparse.X_pu.map(lambda v: f"{v:.12g}"), "to_asset": sparse.zone_b.map(asset)}).to_csv(NET / "flow-milestone.csv", index=False)
pd.DataFrame([{"node": NODE[z], "asset": asset(z), "zone": z, "representative_bus": zrep[z]} for z in sorted(zrep)]).to_csv(NET / "nodes.csv", index=False)
(NET / "README.md").write_text(f"# {NET.name}\n\nMinimal network folder for replay2025's fixed-position test: ONLY the dc_opf branches (flow.csv, flow-milestone.csv) and nodes.csv. "
                               f"NOT a Tulipa input (no assets, no profiles).\n\nBuilt by scripts/58_sparse_fit_split.py from `{run.name}`; fit details in `runs/{OUT.name}/`.\n"
                               + (f"Branch {UNLIMITED[0]}–{UNLIMITED[1]}: reactance from the Kron reduction, capacity overridden to {UNLIMITED_MW:g} MW (effectively unlimited).\n" if UNLIMITED else ""))
with open(NET / "sha256.txt", "w") as fh:
    for p in sorted(NET.iterdir()):
        if p.name != "sha256.txt":
            fh.write(f"{sha(p)}  {p.name}\n")


def stats(e):
    e = np.asarray(e); return f"{np.median(e):+.1f} | {np.percentile(e, 10):+.1f} | {np.percentile(e, 90):+.1f} | {e.min():+.1f} | {e.max():+.1f} | {int((np.abs(e) <= WITHIN).sum())}/{len(e)} | {int((np.abs(e) < 1e-6).sum())}"


L = [f"# Sparse (physical-border) network with LP-envelope limits — {run.name}", "",
     f"{n} zones; representative buses: " + "; ".join(f"{z} = {zrep[z]}" for z in sorted(zrep)), "",
     f"- AC equivalent branches: {len(dense)} (complete Kron equivalent); physical: {int(dense.physical.sum())}; DC links: " + (", ".join(f"{zone[r[cf]]}–{zone[r[ct]]} {r.capacity_MW:.0f} MW" for _, r in dc.iterrows()) or "none"),
     f"- physical adjacency ({len(adj)} pairs, `adjacency.csv`): " + ", ".join(f"{a}–{b}" for a, b in sorted(adj)),
     f"- dense PTDFs vs the package's `PTDF_Reduced_Network_{suf}.csv`: {len(chk)} entries, max |diff| {maxdiff:.2e} (tolerance {TOL_PTDF})", "",
     "## Pairwise TTC error vs the full-grid TTC (%, LP envelope on each network)", "",
     "| network | branches | median | p10 | p90 | min | max | within ±20 % | exact |", "|---|---|---|---|---|---|---|---|---|",
     f"| dense | {len(dense)} | {stats(ttc.err_dense_pct)} |", f"| sparse | {len(sparse)} | {stats(ttc.err_sparse_pct)} |", "",
     "## Sparse branches", "", "| branch | X p.u. | LP capacity MW | set by transaction | capacity without the internal transaction MW | capacity written MW |", "|---|---|---|---|---|---|"]
for r in sparse.itertuples():
    L.append(f"| {r.zone_a}–{r.zone_b} | {r.X_pu:.5f} | {r.cap_LP_sparse_MW:,.0f} | {r.cap_set_by_txn} | {r.cap_LP_sparse_noint_MW:,.0f} | " + ("unlimited (override)" if r.unlimited_override else f"{r.cap_final_MW:,.0f}") + " |")
if UNLIMITED:
    ti = int(np.flatnonzero(internal_txn)[0]); n_set = int(sum(1 for s in set_by if set(s.split("->")) == set(UNLIMITED)))
    L += ["", f"Internal transaction {UNLIMITED[0]}↔{UNLIMITED[1]}: full-grid TTC {ttc.TTC_Original_MW.iloc[ti]:,.0f} MW between {txns[ti][0]} and {txns[ti][1]}; it sets the LP capacity of {n_set} of the {len(sparse)} sparse branches "
          f"(its own branch included). The override applies to the {UNLIMITED[0]}–{UNLIMITED[1]} branch only; all other capacities are the standard fit."]
L += ["", f"Network folder: `inputs/derived/{NET.name}` (flow.csv, flow-milestone.csv, nodes.csv)."]
(OUT / "report.md").write_text("\n".join(L) + "\n")
with open(OUT / "manifest.md", "a") as fh:
    fh.write("\n## Outputs (sha256)\n\n" + "\n".join(f"- `{p.name}` {sha(p)}" for p in sorted(OUT.iterdir()) if p.name != "manifest.md") + "\n"
             + f"\n## Network folder\n\n- `inputs/derived/{NET.name}/` " + "; ".join(f"{p.name} {sha(p)}" for p in sorted(NET.iterdir()) if p.name != "sha256.txt") + f"\n\nfinished {datetime.datetime.now().isoformat(timespec='seconds')}\n")
print("\n".join(L)); print("\nwritten:", OUT, "and", NET)
