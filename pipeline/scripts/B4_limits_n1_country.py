#!/usr/bin/env python3
"""
B4_limits_n1_country.py — N-1 limits for every branch of a country-level network.

STEP  B4 in run_all.sh (HANDOVER.md section 3.4)

WHAT IT DOES
  As B4_limits_n1_nodal.py, for a network with one node per zone: for every pair of zones the full-grid N-1 transfer limit
  (each zone's exchange spread evenly over its 380 kV buses; only monitored lines may set the limit; every line and transformer
  can fail), then the LP envelope for the branches.

READS   runs/<reduction run>/outputs + workbook; inputs/derived/diag_fixedpos_<tag>-sparse-LP (from B2_network_country.py);
        runs/*-sparse-fit-<tag>-sparse-LP/branches.csv
WRITES  runs/<today>-limits-<tag>-<name>/ and inputs/derived/diag_fixedpos_<tag>-sparse-LP-<name>/. Both abort if they exist.

USAGE   python scripts/B4_limits_n1_country.py runs/<reduction run> <tag> <name> --monitored=eic:<monitored_eics.csv>

HISTORY Same code as core_grid_dcopf/scripts/04_limits_n1.py (archived 83_limits_spread_monitored_n1.py); only this header was
        rewritten (the scripts as run, with their history notes, are in background_notes/original_scripts/).
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
OUT = DCOPF / "runs" / f"{datetime.date.today().isoformat()}-limits-{TAG}-{NAME}"; NET = DCOPF / "inputs" / "derived" / f"diag_fixedpos_{TAG}-sparse-LP-{NAME}"
for p in (OUT, NET):
    if p.exists():
        sys.exit(f"ABORT: {p} exists — never overwritten")
fits = sorted((DCOPF / "runs").glob(f"*-sparse-fit-{TAG}-sparse-LP/branches.csv")); assert len(fits) == 1, f"ABORT: expected one sparse-fit run for {TAG}, found {fits}"
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
CONFIG = {"script": "scripts/B4_limits_n1_country.py", "script_sha256": E.sha(Path(__file__)), "engine": "scripts/lib_n1_engine.py", "enr_run": str(run), "tag": TAG, "name": NAME,
          "key": {"380kv": "exchange spread evenly over the zone's 380 kV buses (assumption)", "one": "all of the exchange at the representative bus"}[KEY],
          "monitored": {"380kv": "lines with both ends at 380 kV", "every": "every line and transformer"}.get(MONITORED, f"lines with a circuit whose EIC is in {MONITORED[4:]}"),
          "security": {"n1all": "every branch record out in turn, its rating removed from its pair; grid-splitting outages skipped", "n1border": "lines crossing a zone border out in turn, ratings unchanged (TNO)", "n0": "no outage"}[SECURITY],
          "branch_limits": "LP envelope C_l = max_t TTC_t |PTDF_t,l| on the physical-border network (reactances and PTDFs of the present network)", "validation_data_read": "none"}
(OUT / "manifest.json").write_text(json.dumps({"started": datetime.datetime.now().isoformat(timespec="seconds"), "CONFIG": CONFIG, "inputs_sha256": hashes}, indent=1))

nr = list(wbk["Nodes"].iter_rows(values_only=True)); nh = list(nr[0]); col = lambda r, k: r[nh.index(k)]
zone_of = {col(r, "Bus"): col(r, "Zone") for r in nr[1:] if r[0]}; flag = {col(r, "Zone"): col(r, "Bus") for r in nr[1:] if r[0] and col(r, "IsRepresentative") == 1}
adj = set()
for sh in ("Lines", "Tielines", "Transformers"):
    rs = list(wbk[sh].iter_rows(values_only=True)); h = rs[0]
    for r in rs[1:]:
        if r and r[0]:
            za, zb = zone_of.get(r[h.index("From_node")]), zone_of.get(r[h.index("To_node")])
            if za and zb and za != zb:
                adj.add(tuple(sorted((za, zb))))
PAIRS = sorted(adj); zones = sorted(set(zone_of.values())); zi = {z: j for j, z in enumerate(zones)}; nz = len(zones)
name = dict(zip(bm.new_id, bm.old_name)); ids = sorted(bm.new_id); n = len(ids); pos = {i: j for j, i in enumerate(ids)}; idx_of = {name[i]: pos[i] for i in ids}
bname = [name[i] for i in ids]; bzone = np.array([zone_of[x] for x in bname]); kv = np.array([int(x.rsplit("_", 1)[1]) for x in bname])
F = ld.New_ID_From.map(pos).to_numpy(); T = ld.New_ID_To.map(pos).to_numpy(); K = [idx_of[flag[z]] for z in zones]; ti, tj = E.transactions(nz)
ia = np.array([zi[a] for a, _ in PAIRS]); ib = np.array([zi[b] for _, b in PAIRS]); BORD = [f"{a}-{b}" for a, b in PAIRS]
G = E.prepare(n, F, T, (1.0 / ld.X_pu).to_numpy(float), ld.Capacity_MW.to_numpy(float))
Binv, GA, GB, GBB, GCAP = G["Binv"], G["GA"], G["GB"], G["GBB"], G["GCAP"]
DA = Binv[GA, :] - Binv[GB, :]
X, PT, _ = E.kron_sparse(G, K, ia, ib, nz); A = np.abs(PT[:, ti] - PT[:, tj])


def key(kind):
    W = np.zeros((n, nz))
    for z in zones:
        if kind == "one":
            W[idx_of[flag[z]], zi[z]] = 1.0
        else:
            m = (bzone == z) & (kv == 380); assert m.any(), f"ABORT: zone {z} has no 380 kV bus"
            W[m, zi[z]] = 1.0 / m.sum()
    return W


def limits(W, mon, outages=None, tno=True):
    """-> limit per pair of zones, the line that sets it, the outage (branch record, -1 = none) under which it is set, counts."""
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
# the present limits must come out first
T_now, _, _, _ = limits(key("one"), every); C_now = (T_now[None, :] * A).max(axis=1)
fl = pd.read_csv(f_net["flow.csv"]); fm = pd.read_csv(f_net["flow-milestone.csv"]); nd = pd.read_csv(f_net["nodes.csv"]); az = dict(zip(nd.asset, nd.zone))
order = [PAIRS.index(tuple(sorted((az[a], az[b])))) for a, b in zip(fl.from_asset, fl.to_asset)]
chk = {"present_limits_reproduced_max_rel_diff": float(np.abs(fl.capacity.to_numpy() / C_now[order] - 1).max()), "reactances_reproduced_max_rel_diff": float(np.abs(fm.reactance.to_numpy() / X[order] - 1).max())}
if max(chk.values()) > 1e-6:
    sys.exit(f"ABORT: the present network is not reproduced: {chk}")
W = key(KEY)
T0, l0, _, _ = limits(W, mon)
outs = {"n0": None, "n1border": np.flatnonzero(bzone[F] != bzone[T]), "n1all": np.arange(len(ld))}[SECURITY]
T1, l1, crit, cnt = limits(W, mon, outs, tno=(SECURITY != "n1all"))
if not (np.isfinite(T0).all() and np.isfinite(T1).all()):
    sys.exit("ABORT: a pair of zones has no monitored line that carries its exchange")
C0 = (T0[None, :] * A).max(axis=1); C1 = (T1[None, :] * A).max(axis=1); setby = (T1[None, :] * A).argmax(axis=1)
lname = lambda l: f"{bname[GA[l]]} – {bname[GB[l]]}"
oname = lambda h: "none" if h < 0 else f"{ld.From_node[h]} – {ld.To_node[h]} [{ld.EIC_Code[h]}]"
P = pd.DataFrame({"zone_a": [zones[i] for i in ti], "zone_b": [zones[j] for j in tj], "neighbours": [tuple(sorted((zones[i], zones[j]))) in adj for i, j in zip(ti, tj)], "limit_present_method_n0_mw": T_now,
                  "limit_this_method_n0_mw": T0, "line_setting_it_n0": [lname(l) for l in l0], "limit_this_method_mw": T1, "ratio_to_present": T1 / T_now, "line_setting_it": [lname(l) for l in l1], "under_outage_of": [oname(h) for h in crit]})
P.to_csv(OUT / "pairs.csv", index=False)
Bd = pd.DataFrame({"zone_a": [a for a, _ in PAIRS], "zone_b": [b for _, b in PAIRS], "x_pu": X, "limit_present_mw": C_now, "limit_this_method_n0_mw": C0, "limit_this_method_mw": C1, "ratio_to_present": C1 / C_now,
                   "set_by_exchange": [f"{zones[ti[t]]}->{zones[tj[t]]}" for t in setby]})
Bd.to_csv(OUT / "branches.csv", index=False)
pd.DataFrame({"from": [bname[a] for a in GA[mon]], "to": [bname[b] for b in GB[mon]], "kv_from": kv[GA[mon]], "kv_to": kv[GB[mon]], "zone_from": bzone[GA[mon]], "zone_to": bzone[GB[mon]],
              "circuits": G["GK"][mon], "rating_sum_mw": GCAP[mon]}).to_csv(OUT / "monitored_lines.csv", index=False)
zp = {tuple(sorted((a, b))): c for a, b, c in zip(Bd.zone_a, Bd.zone_b, Bd.limit_this_method_mw)}
f73 = fit.copy(); ph = f73.physical == True
new = [zp[tuple(sorted((a, b)))] for a, b in zip(f73.zone_a[ph], f73.zone_b[ph])]; assert ph.sum() == len(PAIRS)
f73.loc[ph, "cap_LP_sparse_MW"] = new; f73.loc[ph, "cap_final_MW"] = new; f73.loc[ph, "cap_LP_sparse_noint_MW"] = new; f73.loc[ph, "cap_set_by_txn"] = f"83:{NAME}"
f73.to_csv(OUT / "branches_for_73.csv", index=False)
NET.mkdir(parents=False); f2 = fl.copy(); f2["capacity"] = [f"{v:.10g}" for v in C1[order]]
f2.to_csv(NET / "flow.csv", index=False); fm.to_csv(NET / "flow-milestone.csv", index=False); nd.to_csv(NET / "nodes.csv", index=False)
(NET / "README.md").write_text(f"# {NET.name}\n\nThe network of `{BASE_NET.name}` (same branches, same reactances) with branch limits from scripts/83_limits_spread_monitored_n1.py:\n"
                               + "".join(f"- {k}: {CONFIG[k]}\n" for k in ("key", "monitored", "security")) + f"Details in `runs/{OUT.name}/`. NOT a Tulipa input (branches and nodes only).\n")
with open(NET / "sha256.txt", "w") as fh:
    for p in sorted(NET.iterdir()):
        if p.name != "sha256.txt":
            fh.write(f"{E.sha(p)}  {p.name}\n")
nmon = int(mon.sum()); mk = collections.Counter("380 kV line" if a == 380 and b == 380 else ("transformer" if bname[x].rsplit("_", 1)[0] == bname[y].rsplit("_", 1)[0] else "220 kV or other line") for a, b, x, y in zip(kv[GA[mon]], kv[GB[mon]], GA[mon], GB[mon]))
checks = {**chk, "aggregated_lines": int(len(GA)), "lines_that_may_set_a_limit": nmon, "of_which": dict(mk), "of_which_cross_a_border": int((bzone[GA[mon]] != bzone[GB[mon]]).sum()),
          "buses_380_per_zone": {z: int(((bzone == z) & (kv == 380)).sum()) for z in zones}, "outages": cnt, "eic_in_list": (len(eic_list) if eic_list is not None else None),
          "branch_records_with_eic_in_list": (int(ld.EIC_Code.isin(eic_list).sum()) if eic_list is not None else None)}
(OUT / "checks.json").write_text(json.dumps(checks, indent=1))
L = [f"# Branch limits — {NAME} ({run.name})", "", f"- exchange enters at: {CONFIG['key']}", f"- lines that may set a limit: {CONFIG['monitored']} — {nmon} of {len(GA)} lines ({', '.join(f'{v} {k}' for k, v in mk.items())}; {checks['of_which_cross_a_border']} cross a border)",
     f"- security: {CONFIG['security']} — " + ("; ".join(f"{v} {k}" for k, v in cnt.items()) or "no outage"),
     f"- check: the present limits and reactances are reproduced first ({chk['present_limits_reproduced_max_rel_diff']:.1e}, {chk['reactances_reproduced_max_rel_diff']:.1e})", "",
     f"Limit between two zones against the present one (66 pairs): median {np.median(T1 / T_now):.2f}, lowest {np.min(T1 / T_now):.2f}, highest {np.max(T1 / T_now):.2f}. "
     f"Without outages this method gives {np.median(T0 / T_now):.2f} (median).", "",
     "| branch | reactance p.u. | present limit MW | this method, no outage | this method | ratio to present | set by the exchange |", "|---|---|---|---|---|---|---|"]
for r in Bd.itertuples():
    L.append(f"| {r.zone_a}–{r.zone_b} | {r.x_pu:.5f} | {r.limit_present_mw:,.0f} | {r.limit_this_method_n0_mw:,.0f} | {r.limit_this_method_mw:,.0f} | {r.ratio_to_present:.2f} | {r.set_by_exchange} |")
L += ["", "## Neighbouring zones: limit, the line that sets it, and under which outage", "", "| pair | present MW | this method MW | line that sets it | with this line out |", "|---|---|---|---|---|"]
for r in P[P.neighbours].itertuples():
    L.append(f"| {r.zone_a}–{r.zone_b} | {r.limit_present_method_n0_mw:,.0f} | {r.limit_this_method_mw:,.0f} | {r.line_setting_it} | {r.under_outage_of} |")
L += ["", f"Network folder: `inputs/derived/{NET.name}`. For the Tulipa builder (73): `runs/{OUT.name}/branches_for_73.csv`."]
(OUT / "report.md").write_text("\n".join(L) + "\n")
mj = json.loads((OUT / "manifest.json").read_text()); mj["finished"] = datetime.datetime.now().isoformat(timespec="seconds")
mj["outputs_sha256"] = {p.name: E.sha(p) for p in sorted(OUT.iterdir()) if p.name != "manifest.json"}; mj["network_folder"] = {p.name: E.sha(p) for p in sorted(NET.iterdir()) if p.name != "sha256.txt"}
(OUT / "manifest.json").write_text(json.dumps(mj, indent=1))
print("\n".join(L)); print("\nwritten:", OUT, "and", NET)
