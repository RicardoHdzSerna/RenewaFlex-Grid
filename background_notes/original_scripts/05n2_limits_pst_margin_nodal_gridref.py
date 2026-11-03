#!/usr/bin/env python3
# core_grid_dcopf (2026-10-21): 05n2_limits_pst_margin_nodal_gridref.py — COPY of scripts/05n_limits_pst_margin_nodal.py (not edited).
# Changed ONLY the capability check (MW moved per degree per phase-shifter corridor): 05n compares with scripts/74's values, which
# belong to today's grid (ratio 1.007 on v29). On a grid with new parallel paths (2035 + Tilburg loop-in: Rilland-Tilburg is no
# longer a dead end) the true value changes, and 05n aborts (Zandvliet-Rilland 1.186). Here 74's value is scaled by the full-grid
# Thevenin factor of the corridor, [1/(X_corridor + X_th)] on this run's workbook over the same on jao_core_v29 (DC, reactances in
# p.u. on the nominal kV; the corridor's own circuits removed for X_th). Same 15 % tolerance against the scaled value; both the
# original and the scaled reference are written to capability_check.csv. Check on 2026-10-21: the factor reproduces 05n's
# ratios within 1 % (Zandvliet-Rilland 1.175 vs 1.186, Van Eyck-Maasbracht 1.084 vs 1.093). The header of 05n follows.
# core_grid_dcopf (2026-10-16): copy of archive/dcopf/scripts/121_ttc_nodal_pst_margin.py; 5 path/name edit(s), see docs/MAP.md; the original header follows.
"""
121_ttc_nodal_pst_margin.py — step 3 (2026-10-16): scripts/115 (= 93: N-1 transfer limits with the phase shifters SET per
exchange within their RAO range, every rating reduced by the reliability margin, LP envelope; "option 3") for the NODAL
network of scripts/118 and a scripts/120 run. Same engine (77), same phase-shifter model and checks as 115 (with every angle
at zero the limits of 120 times 1 - margin are reproduced for every transaction; MW moved per degree per corridor against
scripts/74); the "zones" of 115 are the nodes of the network. Docstring of 93/92 (method) in scripts/115.

    ~/.tulipa_pipeline_venv/bin/python scripts/121_ttc_nodal_pst_margin.py runs/<enr-run> <tag> <name> runs/<120 run of the same tag>
        --neutral-name=<name> [--margin=0.10] [--monitored=380kv | eic:<csv with a column eic>]   (the 120 run must use the same monitored set)

Writes runs/<today>-limits-nodal-<tag>-<name>/ {manifest.json (first), pairs.csv, branches.csv, corridors.csv, capability_check.csv,
branches_for_73.csv, report.md} and inputs/derived/diag_fixedpos_<tag>-sparse-LP-<name>/ (with phase shifters set per exchange),
inputs/derived/diag_fixedpos_<tag>-sparse-LP-<neutral-name>/ (without), both with the margin. All abort if they exist. No validation data are read.
"""
import collections, datetime, importlib.util, json, math, sys
from pathlib import Path

import numpy as np, pandas as pd, openpyxl
from scipy.optimize import linprog

DCOPF = Path(__file__).resolve().parents[1]
_sp = importlib.util.spec_from_file_location("n1m", DCOPF / "scripts" / "lib_n1_engine.py"); E = importlib.util.module_from_spec(_sp); _sp.loader.exec_module(E)
PSTRUN = DCOPF / "inputs" / "pst_inventory"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(args) != 4:
    sys.exit(__doc__)
run = Path(args[0]).resolve(); TAG, NAME = args[1], args[2]; r120 = Path(args[3]).resolve()
opt = lambda k, d: next((a.split("=", 1)[1] for a in sys.argv if a.startswith(f"--{k}=")), d)
MARGIN = float(opt("margin", "0.10")); NNAME = opt("neutral-name", None); MONITORED = opt("monitored", "380kv")
if not (MONITORED == "380kv" or MONITORED.startswith("eic:")):
    sys.exit("ABORT: --monitored must be 380kv or eic:<csv with a column eic>")
EIC_LIST = set(pd.read_csv(Path(MONITORED[4:]).resolve()).eic) if MONITORED.startswith("eic:") else None
MON_TEXT = "lines with both ends at 380 kV" if EIC_LIST is None else f"lines with a circuit whose EIC is in {MONITORED[4:]}"
if not NNAME:
    sys.exit(__doc__)
BASE_NET = DCOPF / "inputs" / "derived" / f"diag_fixedpos_{TAG}-sparse-LP"
OUT = DCOPF / "runs" / f"{datetime.date.today().isoformat()}-limits-nodal-{TAG}-{NAME}"; NET = DCOPF / "inputs" / "derived" / f"diag_fixedpos_{TAG}-sparse-LP-{NAME}"
NETN = DCOPF / "inputs" / "derived" / f"diag_fixedpos_{TAG}-sparse-LP-{NNAME}"
for p in (OUT, NET, NETN):
    if p.exists():
        sys.exit(f"ABORT: {p} exists — never overwritten")
m120 = json.loads((r120 / "manifest.json").read_text())["CONFIG"]
assert m120["script"].startswith("scripts/04n_") and "380 kV" in m120["key"] and m120["security"].startswith("every branch record out"), "the 120 run must use the 380 kV key and every record out"
assert m120["monitored"] == MON_TEXT or (EIC_LIST is not None and m120["monitored"].startswith("lines with a circuit whose EIC is in") and Path(m120["monitored"].rsplit(" in ", 1)[1]).name == Path(MONITORED[4:]).name
                                         and Path(m120["monitored"].rsplit(" in ", 1)[1]).parent.name == Path(MONITORED[4:]).parent.name), f"the 120 run's monitored set ({m120['monitored']}) differs from --monitored"
hashes = {}
def rd(p):
    hashes[str(Path(p).resolve().relative_to(DCOPF.parent))] = E.sha(p); return p

man = (run / "manifest.md").read_text()
cfg = {l.split("=")[0].strip(): l.split("=", 1)[1].strip().strip('"') for l in man.splitlines() if " = " in l and not l.startswith("|")}
O = run / "outputs"; ld = pd.read_csv(rd(O / f"Line_Details_{cfg['suffix']}.csv")); bm = pd.read_csv(rd(O / f"Bus_ID_Map_{cfg['suffix']}.csv"))
wbk = openpyxl.load_workbook(rd(run / "inputs" / cfg["input_filename"]), read_only=True, data_only=True)
pl = pd.read_csv(rd(PSTRUN / "pst_placement.csv")); cap_t = pd.read_csv(rd(PSTRUN / "pst_capability.csv")); P120 = pd.read_csv(rd(r120 / "pairs.csv"))
f_net = {k: rd(BASE_NET / k) for k in ("flow.csv", "flow-milestone.csv", "nodes.csv")}
fits = sorted((DCOPF / "runs").glob(f"*-sparse-fit-nodal-{TAG}-sparse-LP/branches.csv")); assert len(fits) == 1, f"ABORT: expected one nodal sparse-fit run for {TAG}, found {fits}"
fit = pd.read_csv(rd(fits[0]))
OUT.mkdir(parents=False)
CONFIG = {"script": "scripts/05n2_limits_pst_margin_nodal_gridref.py", "capability_reference": "scripts/74 x Thevenin factor (this workbook / jao_core_v29)", "monitored": MON_TEXT, "reliability_margin": MARGIN, "neutral_network_folder": str(NETN), "script_sha256": E.sha(Path(__file__)), "engine": "scripts/lib_n1_engine.py", "enr_run": str(run), "tag": TAG, "name": NAME, "neutral_run_120": str(r120),
          "method": "120 (nodal bus at its bus, zone spread over its 380 kV buses; only monitored lines limit; every record out, rating removed) + phase-shifter angles set per exchange (preventive), within the RAO tap range; ratings x (1 - margin)",
          "transactions": "every pair of nodes of the network", "pst_source": str(PSTRUN), "pst_reactance": "not added", "validation_data_read": "none"}
(OUT / "manifest.json").write_text(json.dumps({"started": datetime.datetime.now().isoformat(timespec="seconds"), "CONFIG": CONFIG, "inputs_sha256": hashes}, indent=1))

# ---------------------------------------------------------------- grid (as 120)
nr = list(wbk["Nodes"].iter_rows(values_only=True)); nh = list(nr[0]); col = lambda r, k: r[nh.index(k)]
zone_of = {col(r, "Bus"): col(r, "Zone") for r in nr[1:] if r[0]}
nd = pd.read_csv(f_net["nodes.csv"]); fl = pd.read_csv(f_net["flow.csv"]); fm = pd.read_csv(f_net["flow-milestone.csv"])
nodes = nd.node.tolist(); nn = len(nodes); ni = {c: j for j, c in enumerate(nodes)}
node_zone = dict(zip(nd.node, nd.zone)); node_bus = dict(zip(nd.node, nd.representative_bus)); node_nodal = dict(zip(nd.node, nd.nodal.astype(bool))); a2n = dict(zip(nd.asset, nd.node))
klass = lambda a, b: "nodal-nodal" if node_nodal[a] and node_nodal[b] else ("nodal-zone" if node_nodal[a] or node_nodal[b] else "zone-zone")
PAIRS = [(a2n[a], a2n[b]) for a, b in zip(fl.from_asset, fl.to_asset)]; PSET = {tuple(sorted(p)) for p in PAIRS}
name = dict(zip(bm.new_id, bm.old_name)); ids = sorted(bm.new_id); n = len(ids); pos = {i: j for j, i in enumerate(ids)}; idx_of = {name[i]: pos[i] for i in ids}
bname = [name[i] for i in ids]; bzone = np.array([zone_of[x] for x in bname]); kv = np.array([int(x.rsplit("_", 1)[1]) for x in bname])
F = ld.New_ID_From.map(pos).to_numpy(); T = ld.New_ID_To.map(pos).to_numpy(); K = [idx_of[node_bus[c]] for c in nodes]; ti, tj = E.transactions(nn)
ia = np.array([ni[a] for a, _ in PAIRS]); ib = np.array([ni[b] for _, b in PAIRS])
G = E.prepare(n, F, T, (1.0 / ld.X_pu).to_numpy(float), ld.Capacity_MW.to_numpy(float))
Binv, GA, GB, GBB, GCAP, bb, cap = G["Binv"], G["GA"], G["GB"], G["GBB"], G["GCAP"] * (1.0 - MARGIN), G["bb"], G["cap"] * (1.0 - MARGIN)   # reliability margin
SB = float(cfg.get("base", "100.0"))                                  # MW per per-unit (ENR CONFIG.base)
X, PT, _ = E.kron_sparse(G, K, ia, ib, nn); A = np.abs(PT[:, ti] - PT[:, tj])
if float(np.abs(fm.reactance.to_numpy() / X - 1).max()) > 1e-6:
    sys.exit("ABORT: the reactances of the 118 network are not reproduced")
if EIC_LIST is None:
    mon = (kv[GA] == 380) & (kv[GB] == 380)
else:
    hit = ld.EIC_Code.isin(EIC_LIST).to_numpy(); mon = np.zeros(len(GA), bool); mon[G["pair"][hit]] = True
MI = np.flatnonzero(mon)
W = np.zeros((n, nn))
for c in nodes:
    if node_nodal[c]:
        W[idx_of[node_bus[c]], ni[c]] = 1.0
    else:
        z = node_zone[c]; m = (bzone == z) & (kv == 380); W[m, ni[c]] = 1.0 / m.sum()
pair_of = {(a, b): p for p, (a, b) in enumerate(zip(GA, GB))}
# ---------------------------------------------------------------- phase-shifter corridors (as 115)
cp = pl.merge(cap_t[["corridor", "angle_per_circuit_deg"]], on="corridor", how="inner"); assert len(cp) == len(pl), "placement and capability tables do not match"
cor = collections.OrderedDict()
for r in cp.itertuples():
    key = tuple(sorted((r.bus_a, r.bus_b)))
    c = cor.setdefault(key, {"name": [], "a": r.bus_a, "b": r.bus_b, "deg": 0.0}); c["name"].append(r.corridor); c["deg"] += float(r.angle_per_circuit_deg)
nk = len(cor); Wp = np.zeros((n, nk)); Bk = np.zeros(nk); sk = np.zeros(nk); pk = np.zeros(nk, int); phimax = np.zeros(nk); recs_k = []
for k, (key, c) in enumerate(cor.items()):
    a, b = idx_of[c["a"]], idx_of[c["b"]]; p = pair_of[(min(a, b), max(a, b))]
    rr = np.flatnonzero(G["pair"] == p); recs_k.append(set(rr)); Bk[k] = GBB[p]; pk[k] = p; sk[k] = 1.0 if a == GA[p] else -1.0
    Wp[a, k] -= 1.0; Wp[b, k] += 1.0                                  # per unit of B*phi: withdrawal at a, injection at b
    phimax[k] = math.radians(c["deg"])
rec_cor = {h: k for k, rr in enumerate(recs_k) for h in rr}
pd.DataFrame([{"corridor": " / ".join(c["name"]), "bus_a": c["a"], "bus_b": c["b"], "circuits": len(recs_k[k]), "range_deg": c["deg"], "susceptance_pu": Bk[k]} for k, c in enumerate(cor.values())]).to_csv(OUT / "corridors.csv", index=False)
# ---------------------------------------------------------------- outage data (exact rank-one update, all outages at once; as 115)
DA = Binv[GA, :] - Binv[GB, :]
U = Binv[:, F] - Binv[:, T]; den = 1.0 - bb * (U[F, np.arange(len(ld))] - U[T, np.arange(len(ld))])
okc = np.flatnonzero(den >= E.BRIDGE_EPS); nsplit = len(ld) - len(okc)
U = U[:, okc]; coef = bb[okc] / den[okc]; po = G["pair"][okc]; DAo = DA[:, F[okc]] - DA[:, T[okc]]
D0z = DA @ W; D0p = DA @ (Wp * Bk[None, :] * SB); UWz = U.T @ W; UWp = U.T @ (Wp * Bk[None, :] * SB)
nO = len(okc); cor_out = {c: rec_cor[okc[c]] for c in range(nO) if okc[c] in rec_cor}


def rows(i, j, cases):
    """LP rows (+f <= cap and -f <= cap) for case list [(c or -1, line m)], variables [P, phi_1..phi_nk]. As 115."""
    Ar, br = [], []
    for c, m in cases:
        g, cp_ = GBB[m], GCAP[m]; dz = D0z[m]; dp = D0p[m].copy(); fac = np.ones(nk); direct = np.zeros(nk)
        if c >= 0:
            dz = dz + DAo[m, c] * coef[c] * UWz[c]; dp = dp + DAo[m, c] * coef[c] * UWp[c]
            if po[c] == m:
                g = g - bb[okc[c]]; cp_ = cp_ - cap[okc[c]]
            if c in cor_out:
                kk = cor_out[c]; fac[kk] = (Bk[kk] - bb[okc[c]]) / Bk[kk]
        if cp_ <= 1e-9 or g <= 1e-12 * GBB[m]:
            continue
        for k in range(nk):
            if pk[k] == m:
                direct[k] = SB * sk[k] * Bk[k] * fac[k]             # in-service corridor susceptance x phi, MW
        row = np.concatenate([[g * (dz[i] - dz[j])], g * dp * fac + direct])
        Ar += [row, -row]; br += [cp_, cp_]
    return Ar, br


def flows_all(i, j, x):
    """Flows on every line in the intact grid and under every outage for x = [P, phi]. As 115 (nn nodes)."""
    P, phi = x[0], x[1:]
    wz = np.zeros(nn); wz[i], wz[j] = P, -P
    d0 = D0z @ wz + D0p @ phi; dirc = np.zeros(len(GA)); np.add.at(dirc, pk, SB * sk * Bk * phi)
    f0 = GBB * d0 + dirc
    cc = coef * (UWz @ wz + UWp @ phi); dO = d0[:, None] + DAo * cc[None, :]
    FO = GBB[:, None] * dO + dirc[:, None]; capO = np.repeat(GCAP[:, None], nO, axis=1)
    cols = np.arange(nO); FO[po, cols] = (GBB[po] - bb[okc]) * dO[po, cols] + dirc[po]; capO[po, cols] = GCAP[po] - cap[okc]
    for c, kk in cor_out.items():                                      # a corridor circuit out: its phase shifter goes with it
        fac = (Bk[kk] - bb[okc[c]]) / Bk[kk]; phi2 = phi.copy(); phi2[kk] *= fac
        d0c = D0z @ wz + D0p @ phi2; ccc = coef[c] * (UWz[c] @ wz + UWp[c] @ phi2); dd = d0c + DAo[:, c] * ccc
        dirc2 = np.zeros(len(GA)); np.add.at(dirc2, pk, SB * sk * Bk * phi2); g = GBB.copy(); g[po[c]] -= bb[okc[c]]
        if po[c] == pk[kk]:
            dirc2[pk[kk]] = SB * sk[kk] * Bk[kk] * phi2[kk]
        FO[:, c] = g * dd + dirc2
    return f0, FO, capO


def solve(i, j, phimax_use, start_cases):
    cases = {(-1, m) for m in MI} | set(start_cases); Ar, br = rows(i, j, sorted(cases))
    bounds = [(0, 1e6)] + [(-v, v) for v in phimax_use]
    for it in range(40):
        res = linprog(np.r_[-1.0, np.zeros(nk)], A_ub=np.array(Ar), b_ub=np.array(br), bounds=bounds, method="highs")
        if res.status != 0:
            raise RuntimeError(f"LP status {res.status}: {res.message}")
        f0, FO, capO = flows_all(i, j, res.x)
        v0 = np.abs(f0[MI]) - GCAP[MI]; vO = np.abs(FO[MI, :]) - capO[MI, :]
        bad = [(-1, MI[q]) for q in np.flatnonzero(v0 > 1e-6 * GCAP[MI])]
        worst = np.argsort(-vO.max(axis=0))[:25]
        for c in worst:
            if vO[:, c].max() > 1e-6 * np.median(GCAP):
                bad += [(int(c), MI[q]) for q in np.flatnonzero(vO[:, c] > 0)]
        new = [x for x in bad if x not in cases]
        if not new:
            return res.x, it + 1
        cases |= set(new); a2, b2 = rows(i, j, new); Ar += a2; br += b2
    raise RuntimeError("constraint generation did not converge")


import scipy.sparse as _sp, scipy.sparse.linalg as _sla
_REFWB = DCOPF / "inputs" / "derived" / "jao_core_v29" / "jao_core.xlsx"


def _thev(path, a, b):
    w = pd.read_excel(path, sheet_name=None); br = pd.concat([w[s] for s in ("Lines", "Tielines", "Transformers")], ignore_index=True)
    br = br[(br.From_node != br.To_node) & (br.X.astype(float) > 0)]
    vl = br.Voltage_level.astype(float).where(br.Voltage_level.astype(float) > 0, 380.0); xpu = (br.X.astype(float) / (vl ** 2 / 100.0)).to_numpy()
    m = (((br.From_node == a) & (br.To_node == b)) | ((br.From_node == b) & (br.To_node == a))).to_numpy()
    if not m.any():
        return np.nan
    xc = 1.0 / np.sum(1.0 / xpu[m])
    bs = sorted(set(br.From_node) | set(br.To_node)); ix = {x: i for i, x in enumerate(bs)}
    f = br.From_node[~m].map(ix).to_numpy(); t = br.To_node[~m].map(ix).to_numpy(); y = 1.0 / xpu[~m]; nb = len(bs)
    Bm = _sp.coo_matrix((np.r_[y, y, -y, -y], (np.r_[f, t, f, t], np.r_[f, t, t, f])), shape=(nb, nb)).tocsc()
    gnd = ix[a] if ix[a] != 0 else ix[b]
    keep = [i for i in range(nb) if i != gnd]; Br = Bm[keep][:, keep]
    e = np.zeros(nb); e[ix[a]] = 1.0; e[ix[b]] = -1.0; e = e[keep]
    return 1.0 / (xc + float(e @ _sla.spsolve(Br, e)))


_THIS = run / "inputs" / cfg["input_filename"]
capchk = []
for k, c in enumerate(cor.values()):
    one = np.zeros(nk); one[k] = math.radians(1.0); f0, _, _ = flows_all(0, 0, np.r_[0.0, one])
    mw = abs(f0[pk[k]]); ref = cap_t[cap_t.corridor.isin(c["name"])].corridor_shift_mw_per_deg
    fac = _thev(_THIS, c["a"], c["b"]) / _thev(_REFWB, c["a"], c["b"])
    r74 = float(ref.iloc[0]) if len(ref) else np.nan
    capchk.append({"corridor": " / ".join(c["name"]), "mw_per_deg_here": mw, "mw_per_deg_74": r74, "thevenin_factor_vs_v29": fac, "mw_per_deg_74_scaled": r74 * fac})
CC = pd.DataFrame(capchk); CC["ratio_unscaled"] = CC.mw_per_deg_here / CC.mw_per_deg_74; CC["ratio"] = CC.mw_per_deg_here / CC.mw_per_deg_74_scaled
CC.to_csv(OUT / "capability_check.csv", index=False); print(CC.to_string(), flush=True)
if (CC.ratio.dropna() - 1).abs().max() > 0.15:
    sys.exit("ABORT: MW moved per degree differs from scripts/74 (scaled to this grid) by more than 15 %")
crit = {}
for r in P120.itertuples():
    o = r.under_outage_of
    if isinstance(o, str) and "[" in o:
        e = o.rsplit("[", 1)[1].rstrip("]")
        hs = [c for c in range(nO) if ld.EIC_Code[okc[c]] == e]
        crit[tuple(sorted((r.node_a, r.node_b)))] = hs
p120 = {(a, b): v for a, b, v in zip(P120.node_a, P120.node_b, P120.limit_this_method_mw)}
rows_out = []; t_start = datetime.datetime.now()
for t, (i, j) in enumerate(zip(ti, tj)):
    key = tuple(sorted((nodes[i], nodes[j]))); seeds = [(c, m) for c in crit.get(key, []) for m in MI]
    x0, it0 = solve(i, j, np.zeros(nk), seeds); x1, it1 = solve(i, j, phimax, seeds)
    pr = p120[(nodes[i], nodes[j])]
    rows_out.append({"node_a": nodes[i], "node_b": nodes[j], "class": klass(nodes[i], nodes[j]), "neighbours": key in PSET, "ttc_neutral_mw": x0[0], "ttc_neutral_120_mw": pr, "check_rel_diff": x0[0] / ((1.0 - MARGIN) * pr) - 1,
                     "ttc_pst_mw": x1[0], "ratio_pst_over_neutral": x1[0] / x0[0], "iterations": it0 + it1,
                     **{f"angle_deg | {' / '.join(c['name'])}": math.degrees(x1[1 + k]) for k, c in enumerate(cor.values())}})
    if t % 50 == 0 or t == len(ti) - 1:
        print(f"[{t + 1}/{len(ti)} {(datetime.datetime.now() - t_start).seconds} s] {nodes[i]}-{nodes[j]}: neutral {x0[0]:,.0f} (120: {pr:,.0f}), with phase shifters {x1[0]:,.0f}", flush=True)
PP = pd.DataFrame(rows_out); PP.to_csv(OUT / "pairs.csv", index=False)
chk = float(PP.check_rel_diff.abs().max())
if chk > 1e-4:
    sys.exit(f"ABORT: with angles at zero the limits of 120 (times 1 - margin) are not reproduced (largest relative difference {chk:.2e})")
T0 = PP.ttc_neutral_mw.to_numpy(); T1 = PP.ttc_pst_mw.to_numpy(); C0 = (T0[None, :] * A).max(axis=1); C1 = (T1[None, :] * A).max(axis=1)
rating = {tuple(sorted((a, b))): v for a, b, v in zip(fit.node_a, fit.node_b, fit.rating_sum_MW)}
Bd = pd.DataFrame({"node_a": [a for a, _ in PAIRS], "node_b": [b for _, b in PAIRS], "class": [klass(a, b) for a, b in PAIRS], "x_pu": X, "rating_sum_mw": [rating.get(tuple(sorted(p)), np.nan) for p in PAIRS],
                   "limit_neutral_mw": C0, "limit_pst_mw": C1, "ratio": C1 / C0, "set_by_exchange": [f"{nodes[ti[t]]}->{nodes[tj[t]]}" for t in (T1[None, :] * A).argmax(axis=1)]})
Bd.to_csv(OUT / "branches.csv", index=False)
for NF, CC_, what in ((NET, C1, "with phase shifters set per exchange"), (NETN, C0, "without phase shifters")):
    NF.mkdir(parents=False); f2 = fl.copy(); f2["capacity"] = [f"{v:.10g}" for v in CC_]
    f2.to_csv(NF / "flow.csv", index=False); fm.to_csv(NF / "flow-milestone.csv", index=False); nd.to_csv(NF / "nodes.csv", index=False)
    (NF / "README.md").write_text(f"# {NF.name}\n\nThe nodal network of `{BASE_NET.name}` with branch limits from node-level N-1 transfer limits {what}, ratings reduced by the {MARGIN:.0%} reliability margin, monitored: {MON_TEXT} (scripts/121_ttc_nodal_pst_margin.py, `runs/{OUT.name}`). NOT a Tulipa input.\n")
    with open(NF / "sha256.txt", "w") as fh:
        for p in sorted(NF.iterdir()):
            if p.name != "sha256.txt":
                fh.write(f"{E.sha(p)}  {p.name}\n")
f73 = fit.copy(); ph = f73.physical == True; zp = {tuple(sorted((a, b))): c for a, b, c in zip(Bd.node_a, Bd.node_b, Bd.limit_pst_mw)}
new = [zp[tuple(sorted((a, b)))] for a, b in zip(f73.node_a[ph], f73.node_b[ph])]
f73.loc[ph, "cap_LP_sparse_MW"] = new; f73.loc[ph, "cap_final_MW"] = new; f73.loc[ph, "cap_set_by_txn"] = f"121:{NAME}"; f73.to_csv(OUT / "branches_for_73.csv", index=False)
rat = lambda v: f"{np.median(v):.2f} / {np.min(v):.2f} / {np.max(v):.2f}"
L = [f"# Node-level N-1 transfer limits with phase shifters set per exchange and a {MARGIN:.0%} reliability margin — {run.name}", "",
     f"{nk} phase-shifter corridors: " + "; ".join(f"{' / '.join(c['name'])} ±{c['deg']:.1f}°" for c in cor.values()) + ".",
     f"Nodes {nn}, transactions {len(ti)}, monitored: {MON_TEXT} ({len(MI)} lines). Outages: {nO} taken out, {nsplit} skipped (they split the grid). With every angle at zero the limits of `{r120.name}` are reproduced (largest relative difference {chk:.1e}).", "",
     "| transactions | n | with phase shifters over without: median / lowest / highest | gaining more than 1 % |", "|---|---|---|---|"]
for k, m in (("all", np.ones(len(ti), bool)),) + tuple((k, (PP["class"] == k).to_numpy()) for k in ("nodal-nodal", "nodal-zone", "zone-zone")):
    L.append(f"| {k} | {int(m.sum())} | {rat(T1[m] / T0[m])} | {int(((T1[m] / T0[m]) > 1.01).sum())} |")
L += ["", "## Branch limits (MW)", "", "| branch | class | rating sum | without phase shifters | with phase shifters | ratio | with / rating | set by the exchange |", "|---|---|---|---|---|---|---|---|"]
for r in Bd.sort_values(["class", "node_a", "node_b"]).to_dict("records"):
    rs = r["rating_sum_mw"]
    L.append(f"| {r['node_a']}–{r['node_b']} | {r['class']} | " + (f"{rs:,.0f}" if np.isfinite(rs) else "—") + f" | {r['limit_neutral_mw']:,.0f} | {r['limit_pst_mw']:,.0f} | {r['ratio']:.2f} | " + (f"{r['limit_pst_mw'] / rs:.2f}" if np.isfinite(rs) and rs > 0 else "—") + f" | {r['set_by_exchange']} |")
L += ["", "## Neighbouring nodes: transfer limit without and with phase shifters (MW)", "", "| pair | class | without | with | ratio |", "|---|---|---|---|---|"]
for r in PP[PP.neighbours].sort_values(["class", "node_a", "node_b"]).to_dict("records"):
    L.append(f"| {r['node_a']}–{r['node_b']} | {r['class']} | {r['ttc_neutral_mw']:,.0f} | {r['ttc_pst_mw']:,.0f} | {r['ratio_pst_over_neutral']:.2f} |")
L += ["", f"Network folders: `inputs/derived/{NET.name}` (with phase shifters), `inputs/derived/{NETN.name}` (without). For a Tulipa builder: `runs/{OUT.name}/branches_for_73.csv` (with phase shifters)."]
(OUT / "report.md").write_text("\n".join(L) + "\n")
mj = json.loads((OUT / "manifest.json").read_text()); mj["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
mj["outputs_sha256"] = {p.name: E.sha(p) for p in sorted(OUT.iterdir()) if p.name != "manifest.json"}; mj["network_folders"] = {NF.name: {p.name: E.sha(p) for p in sorted(NF.iterdir()) if p.name != "sha256.txt"} for NF in (NET, NETN)}
(OUT / "manifest.json").write_text(json.dumps(mj, indent=1))
print("\n".join(L))
