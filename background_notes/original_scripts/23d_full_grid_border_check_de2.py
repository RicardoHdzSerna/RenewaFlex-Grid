#!/usr/bin/env python3
# core_grid_dcopf (2026-10-25): 23d_full_grid_border_check_de2.py — COPY of 23c with ONE change: imports 10n3 (knows the zones DE_N/DE_S)
# instead of 10n2 (23c aborted on a DE2 network: runs/_ABORTED-silent_fullgridcheck_2035rt4k-de2-base). Header of 23c follows.
"""
23c_full_grid_border_check_de2.py — copy of 23b_full_grid_border_check_transit.py (2026-10-25) for networks in which Germany is split
(DE2, scripts/29: nodes DE0N, DE0S). Changes, nothing else: "Germany" as a receiving or sending side = all German nodes of the network,
each its own variable (free split), labelled DE; NL -> DE0N and NL -> DE0S are added as separate cases; the single-pair check uses
NL-MAASBRACHT -> DE0S, NL-MEEDEN -> DE0N, NL-RILLAND -> BE00; transits DE -> BE, DE -> FR (Germany free) and DE0N -> DE0S.
Works unchanged for a network with one German node DE00. Header of 23b follows.
23b_full_grid_border_check_transit.py — copy of 23_full_grid_border_check.py (2026-10-23) with ONE addition: third-country transits
through the Netherlands, DE00 -> BE00 and DE00 -> FR00 (foreign zones spread over their 380 kV buses, Dutch nodes 0), solved on the
full grid and on the reduced network, so a tie correction (scripts/24, 24b) can be checked for blocking real transit. The <nodal network>
may be a corrected variant: the full-grid side (rules of the 05n run) does not depend on it. Output prefix fullgridcheck_ as 23.
--- header of 23 follows ---
23_full_grid_border_check.py — is the Dutch border room of the NODAL network physically secure on the full grid? (2026-10-23)

User: "yes run the full-grid check", after the other session's finding (G3_copper_step_check_NT_2035.md): every tie branch of
the nodal network gets its own option-3 limit from the single exchange that loads it most (envelope C_l = max_t TTC_t |PTDF_t,l|,
05n/05n2 line "C1 = ..."), and nothing limits the sum of the ties. Scripts/22 showed the consequence: with the Dutch side free to
sit anywhere, the nodal network lets 14.9 GW cross NL <-> BE+DE against 9.2 GW in the country network.

The question: does the FULL grid, under the same security rules as option 3, allow those transfers? For each case a linear
programme maximises a transfer on the FULL grid of the network's reduction run, with exactly the option-3 rules of 05n:
  every branch record out in turn (bridges skipped), only the monitored set may limit (EIC list of the 05n/05n2 run), ratings x (1 - 10 %),
  phase-shifter angles free within their RAO range (preventive, one setting per case), corridor circuits out take their PST with them,
  constraint generation until no monitored line is overloaded in the intact grid or under any outage.
The same case is also solved on the REDUCED nodal network (flow.csv limits, PTDF, as Tulipa sees it), so the two can be compared.
Cases (variables >= 0, sum of the Dutch side = sum of the receiving side, maximise the sum):
  free      each Dutch node its own amount (the best-case placement, what a dispatch can approach);
  even      Dutch side 1/n per node (fixed shape);
  keyed     Dutch side by a generation key (--gen-key components_twh.csv of a 19/19b run; fixed shape; only on the grid it belongs to);
  zone      the Netherlands as ONE zone: exchange spread evenly over the Dutch 380 kV buses (the convention of 04/05 for the country
            network; full grid only);
  reduced-optimum  the Dutch and receiving amounts of the REDUCED network's 'free' optimum taken as a fixed shape and scaled on the
            full grid: the factor says how much of what the reduced network allows is secure (< 1 = the reduced network over-allows).
Receiving side: BE00, DE00, or BE00 + DE00 with a free split; a foreign zone is spread evenly over its 380 kV buses (as 04n/05n).
Check: for single node pairs the 05n/05n2 pairs.csv ttc_pst_mw is reproduced (abort above 1e-4 relative).
No validation data are read. Read-only: no network is changed.

    ~/.tulipa_pipeline_venv/bin/python -W ignore scripts/23_full_grid_border_check.py <nodal network> <05n run> <label> [--gen-key <components_twh.csv>]

Writes runs/fullgridcheck_<label>/{manifest.json (first), cases.csv, case_injections.csv, summary.md}; aborts if the folder exists.
"""
from __future__ import annotations
import collections, datetime, importlib.util, json, math, sys
from pathlib import Path
import numpy as np, pandas as pd, openpyxl
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
_e = importlib.util.spec_from_file_location("n1m", ROOT / "scripts" / "lib_n1_engine.py"); E = importlib.util.module_from_spec(_e); _e.loader.exec_module(E)
_s = importlib.util.spec_from_file_location("t10n2", ROOT / "scripts" / "10n3_test_2025_nodal_injections_de2.py"); T = importlib.util.module_from_spec(_s); _s.loader.exec_module(T)
PSTRUN = ROOT / "inputs" / "pst_inventory"
GEN_COLS = ["Biomass", "Fossil Gas", "Fossil Hard coal", "Hydro Run-of-river and pondage", "Nuclear", "Other", "Solar", "Waste", "Wind Offshore", "Wind Onshore"]


def main():
    argv = sys.argv[1:]; args = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--gen-key")]
    if len(args) != 3:
        sys.exit(__doc__)
    net, r05, label = Path(args[0]).resolve(), Path(args[1]).resolve(), args[2]
    gk = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--gen-key=")), None)
    if "--gen-key" in sys.argv:
        gk = sys.argv[sys.argv.index("--gen-key") + 1]
    out = ROOT / "runs" / f"fullgridcheck_{label}"
    if out.exists():
        sys.exit(f"ABORT: {out} exists — never overwritten")
    m05 = json.loads((r05 / "manifest.json").read_text())["CONFIG"]
    run = Path(m05["enr_run"]); MARGIN = float(m05["reliability_margin"]); mon_txt = m05["monitored"]
    eicf = ROOT / mon_txt.rsplit(" in ", 1)[1] if " in " in mon_txt else None
    if eicf is None or not eicf.exists():
        sys.exit(f"ABORT: monitored set of the 05n run not found ({mon_txt})")
    man = (run / "manifest.md").read_text()
    cfg = {l.split("=")[0].strip(): l.split("=", 1)[1].strip().strip('"') for l in man.splitlines() if " = " in l and not l.startswith("|")}
    O = run / "outputs"
    files = {"Line_Details": O / f"Line_Details_{cfg['suffix']}.csv", "Bus_ID_Map": O / f"Bus_ID_Map_{cfg['suffix']}.csv", "workbook": run / "inputs" / cfg["input_filename"],
             "monitored_eics": eicf, "pst_placement": PSTRUN / "pst_placement.csv", "pst_capability": PSTRUN / "pst_capability.csv",
             "05n pairs": r05 / "pairs.csv", "flow.csv": net / "flow.csv", "flow-milestone.csv": net / "flow-milestone.csv", "nodes.csv": net / "nodes.csv"}
    if gk:
        files["gen_key"] = Path(gk).resolve()
    CONFIG = {"script": Path(__file__).name, "script_sha256": E.sha(Path(__file__)), "network": str(net), "run_05n": str(r05), "enr_run": str(run), "monitored": mon_txt, "margin": MARGIN,
              "rules": "as 05n: every record out (bridges skipped), monitored set limits, ratings x (1-margin), PST angles within RAO range per case, constraint generation",
              "foreign_zone_placement": "even over its 380 kV buses (04n/05n)", "zone_case_nl_placement": "even over the Dutch 380 kV buses (04/05)"}
    out.mkdir(parents=True)
    (out / "manifest.json").write_text(json.dumps({"status": "started", "started": datetime.datetime.now().isoformat(timespec="seconds"), "config": CONFIG,
                                                   "inputs_sha256": {k: E.sha(p) for k, p in files.items()}}, indent=1))

    # ---------------------------------------------------------------- full grid (as 05n)
    ld = pd.read_csv(files["Line_Details"]); bm = pd.read_csv(files["Bus_ID_Map"])
    wb = openpyxl.load_workbook(files["workbook"], read_only=True, data_only=True); nr = list(wb["Nodes"].iter_rows(values_only=True)); nh = list(nr[0])
    zone_of = {r[nh.index("Bus")]: r[nh.index("Zone")] for r in nr[1:] if r[0]}
    nd = pd.read_csv(files["nodes.csv"]); nodes = nd.node.tolist(); node_zone = dict(zip(nd.node, nd.zone)); node_bus = dict(zip(nd.node, nd.representative_bus))
    node_nodal = dict(zip(nd.node, nd.nodal.astype(bool)))
    name = dict(zip(bm.new_id, bm.old_name)); ids = sorted(bm.new_id); n = len(ids); pos = {i: j for j, i in enumerate(ids)}; idx_of = {name[i]: pos[i] for i in ids}
    bname = [name[i] for i in ids]; bzone = np.array([zone_of[x] for x in bname]); kv = np.array([int(x.rsplit("_", 1)[1]) for x in bname])
    F = ld.New_ID_From.map(pos).to_numpy(); Tt = ld.New_ID_To.map(pos).to_numpy()
    G = E.prepare(n, F, Tt, (1.0 / ld.X_pu).to_numpy(float), ld.Capacity_MW.to_numpy(float))
    Binv, GA, GB, GBB = G["Binv"], G["GA"], G["GB"], G["GBB"]; GCAP = G["GCAP"] * (1.0 - MARGIN); bb = G["bb"]; cap = G["cap"] * (1.0 - MARGIN)
    SB = float(cfg.get("base", "100.0"))
    EIC = set(pd.read_csv(files["monitored_eics"]).eic); hit = ld.EIC_Code.isin(EIC).to_numpy(); mon = np.zeros(len(GA), bool); mon[G["pair"][hit]] = True; MI = np.flatnonzero(mon)

    def col_node(c):                                                   # bus vector of one network node, per MW (as 05n W)
        w = np.zeros(n)
        if node_nodal[c]:
            w[idx_of[node_bus[c]]] = 1.0
        else:
            m = (bzone == node_zone[c]) & (kv == 380); w[m] = 1.0 / m.sum()
        return w
    nl_nodes = [c for c in nodes if node_zone[c] == "NL"]
    Wnl_zone = ((bzone == "NL") & (kv == 380)).astype(float); Wnl_zone /= Wnl_zone.sum()

    # phase shifters (as 05n)
    pl = pd.read_csv(files["pst_placement"]); cap_t = pd.read_csv(files["pst_capability"]); cp = pl.merge(cap_t[["corridor", "angle_per_circuit_deg"]], on="corridor"); assert len(cp) == len(pl)
    cor = collections.OrderedDict()
    for r in cp.itertuples():
        c = cor.setdefault(tuple(sorted((r.bus_a, r.bus_b))), {"name": [], "a": r.bus_a, "b": r.bus_b, "deg": 0.0}); c["name"].append(r.corridor); c["deg"] += float(r.angle_per_circuit_deg)
    pair_of = {(a, b): p for p, (a, b) in enumerate(zip(GA, GB))}
    nk = len(cor); Wp = np.zeros((n, nk)); Bk = np.zeros(nk); sk = np.zeros(nk); pk = np.zeros(nk, int); phimax = np.zeros(nk); recs_k = []
    for k, c in enumerate(cor.values()):
        a, b = idx_of[c["a"]], idx_of[c["b"]]; p = pair_of[(min(a, b), max(a, b))]
        recs_k.append(set(np.flatnonzero(G["pair"] == p))); Bk[k] = GBB[p]; pk[k] = p; sk[k] = 1.0 if a == GA[p] else -1.0
        Wp[a, k] -= 1.0; Wp[b, k] += 1.0; phimax[k] = math.radians(c["deg"])
    rec_cor = {h: k for k, rr in enumerate(recs_k) for h in rr}
    DA = Binv[GA, :] - Binv[GB, :]
    U = Binv[:, F] - Binv[:, Tt]; den = 1.0 - bb * (U[F, np.arange(len(ld))] - U[Tt, np.arange(len(ld))])
    okc = np.flatnonzero(den >= E.BRIDGE_EPS); U = U[:, okc]; coef = bb[okc] / den[okc]; po = G["pair"][okc]; DAo = DA[:, F[okc]] - DA[:, Tt[okc]]
    D0p = DA @ (Wp * Bk[None, :] * SB); UWp = U.T @ (Wp * Bk[None, :] * SB); nO = len(okc); cor_out = {c: rec_cor[okc[c]] for c in range(nO) if okc[c] in rec_cor}

    def solve(Wc, src_mask, use_pst=True):
        """Wc: bus x components (signed: + injection, - withdrawal per unit amount); src_mask: which components are on the Dutch side.
        Maximise the Dutch side subject to N-1 on the monitored set, as 05n rows()/flows_all() with a general set of components."""
        ncomp = Wc.shape[1]; D0z = DA @ Wc; UWz = U.T @ Wc

        def rows(cases):
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
                        direct[k] = SB * sk[k] * Bk[k] * fac[k]
                row = np.concatenate([g * dz, g * dp * fac + direct]); Ar += [row, -row]; br += [cp_, cp_]
            return Ar, br

        def flows(x):
            amt, phi = x[:ncomp], x[ncomp:]
            d0 = D0z @ amt + D0p @ phi; dirc = np.zeros(len(GA)); np.add.at(dirc, pk, SB * sk * Bk * phi); f0 = GBB * d0 + dirc
            cc = coef * (UWz @ amt + UWp @ phi); dO = d0[:, None] + DAo * cc[None, :]
            FO = GBB[:, None] * dO + dirc[:, None]; capO = np.repeat(GCAP[:, None], nO, axis=1)
            cols = np.arange(nO); FO[po, cols] = (GBB[po] - bb[okc]) * dO[po, cols] + dirc[po]; capO[po, cols] = GCAP[po] - cap[okc]
            for c, kk in cor_out.items():
                fac = (Bk[kk] - bb[okc[c]]) / Bk[kk]; phi2 = phi.copy(); phi2[kk] *= fac
                d0c = D0z @ amt + D0p @ phi2; ccc = coef[c] * (UWz[c] @ amt + UWp[c] @ phi2); dd = d0c + DAo[:, c] * ccc
                dirc2 = np.zeros(len(GA)); np.add.at(dirc2, pk, SB * sk * Bk * phi2); g = GBB.copy(); g[po[c]] -= bb[okc[c]]
                if po[c] == pk[kk]:
                    dirc2[pk[kk]] = SB * sk[kk] * Bk[kk] * phi2[kk]
                FO[:, c] = g * dd + dirc2
            return f0, FO, capO

        cases = {(-1, m) for m in MI}; Ar, br = rows(sorted(cases))
        bounds = [(0, 1e6)] * ncomp + [(-v, v) if use_pst else (0, 0) for v in phimax]
        cvec = np.r_[-src_mask.astype(float), np.zeros(nk)]; Aeq = np.r_[np.where(src_mask, 1.0, -1.0), np.zeros(nk)][None, :]
        for it in range(60):
            res = linprog(cvec, A_ub=np.array(Ar), b_ub=np.array(br), A_eq=Aeq, b_eq=[0.0], bounds=bounds, method="highs")
            if res.status != 0:
                raise RuntimeError(f"LP status {res.status}: {res.message}")
            f0, FO, capO = flows(res.x)
            v0 = np.abs(f0[MI]) - GCAP[MI]; vO = np.abs(FO[MI, :]) - capO[MI, :]
            bad = [(-1, MI[q]) for q in np.flatnonzero(v0 > 1e-6 * GCAP[MI])]
            for c in np.argsort(-vO.max(axis=0))[:25]:
                if vO[:, c].max() > 1e-6 * np.median(GCAP):
                    bad += [(int(c), MI[q]) for q in np.flatnonzero(vO[:, c] > 0)]
            new = [x for x in bad if x not in cases]
            if not new:
                util0 = np.abs(f0[MI]) / GCAP[MI]; utilO = np.where(capO[MI, :] > 1e-9, np.abs(FO[MI, :]) / np.maximum(capO[MI, :], 1e-9), 0)
                q = int(np.argmax(np.maximum(util0, utilO.max(axis=1)))); bind = f"{bname[GA[MI[q]]]}–{bname[GB[MI[q]]]}"
                return res.x, it + 1, bind
            cases |= set(new); a2, b2 = rows(new); Ar += a2; br += b2
        raise RuntimeError("constraint generation did not converge")

    # ---------------------------------------------------------------- reduced network (flow.csv limits, as Tulipa)
    b = T.read_network(net); rnodes, PT = T.ptdf(b); capr = b.capacity.to_numpy(float); lim = capr < T.UNLIMITED_FROM_MW; PT, capr = PT[lim], capr[lim]
    rix = {c: i for i, c in enumerate(rnodes)}

    def solve_reduced(comps, src_mask):
        """comps: list of {node: weight} (signed, per unit amount)."""
        Inj = np.zeros((len(rnodes), len(comps)))
        for k, cdict in enumerate(comps):
            for c, w in cdict.items():
                Inj[rix[c], k] = w
        Fm = PT @ Inj
        r = linprog(-src_mask.astype(float), A_ub=np.vstack([Fm, -Fm]), b_ub=np.r_[capr, capr], A_eq=np.where(src_mask, 1.0, -1.0)[None, :], b_eq=[0.0],
                    bounds=[(0, None)] * len(comps), method="highs")
        if r.status != 0:
            raise RuntimeError(r.message)
        return r.x

    # ---------------------------------------------------------------- check: single node pairs reproduce 05n
    P05 = pd.read_csv(files["05n pairs"]); chk = []
    DEN = [c for c in nodes if str(node_zone[c]).startswith("DE")]                       # 23c: the German nodes
    lab = lambda c: {"DE0N": "DEN", "DE0S": "DES"}.get(c, c[:2])
    gsel = lambda c: next((x for x in DEN if x in c), DEN[0])
    for a, z in (("NL-MAASBRACHT", gsel(("DE0S", "DE00"))), ("NL-MEEDEN", gsel(("DE0N", "DE00"))), ("NL-RILLAND", "BE00")):
        Wc = np.column_stack([col_node(a), -col_node(z)]); x, it, _ = solve(Wc, np.array([True, False]))
        ref = P05[((P05.node_a == a) & (P05.node_b == z)) | ((P05.node_a == z) & (P05.node_b == a))].ttc_pst_mw.iloc[0]
        chk.append({"pair": f"{a}->{z}", "here_mw": x[0], "05n_mw": ref, "rel_diff": x[0] / ref - 1})
    CK = pd.DataFrame(chk); print(CK.to_string(), flush=True)
    if CK.rel_diff.abs().max() > 1e-4:
        sys.exit("ABORT: single-pair transfers do not reproduce the 05n pairs.csv")

    # ---------------------------------------------------------------- cases
    shapes = {"even": {c: 1.0 / len(nl_nodes) for c in nl_nodes}}
    if gk:
        ct = pd.read_csv(files["gen_key"]).set_index("node"); gen = ct[[c for c in GEN_COLS if c in ct.columns]].clip(lower=0).sum(axis=1)
        if set(gen.index) != set(nl_nodes):
            sys.exit("ABORT: the generation key's nodes differ from the network's Dutch nodes")
        shapes["keyed"] = (gen / gen.sum()).to_dict()
    rows_out, inj_out = [], []
    sinksets = [("BE00",), tuple(DEN), ("BE00",) + tuple(DEN)] + ([(c,) for c in DEN] if len(DEN) > 1 else [])
    for sinks in sinksets:
        to = "BE+DE" if len(sinks) == 1 + len(DEN) and len(sinks) > 1 else ("DE" if tuple(sinks) == tuple(DEN) else "+".join(lab(c) for c in sinks))
        # free
        Wc = np.column_stack([col_node(c) for c in nl_nodes] + [-col_node(s) for s in sinks]); sm = np.r_[np.ones(len(nl_nodes), bool), np.zeros(len(sinks), bool)]
        xf, it, bind = solve(Wc, sm)
        xr = solve_reduced([{c: 1.0} for c in nl_nodes] + [{s: -1.0} for s in sinks], sm)
        rows_out.append({"to": to, "case": "free", "reduced_mw": xr[sm].sum(), "full_grid_mw": xf[:len(sm)][sm].sum(), "full_grid_binding": bind, "iterations": it,
                         "split_full": "; ".join(f"{lab(s)} {v:,.0f}" for s, v in zip(sinks, xf[len(nl_nodes):len(sm)])), "split_reduced": "; ".join(f"{lab(s)} {v:,.0f}" for s, v in zip(sinks, xr[len(nl_nodes):]))})
        for c, vf, vr in zip(nl_nodes, xf[:len(nl_nodes)], xr[:len(nl_nodes)]):
            inj_out.append({"to": to, "case": "free", "node": c, "full_grid_mw": vf, "reduced_mw": vr})
        # reduced optimum as a fixed shape on the full grid
        tot = xr[sm].sum(); wvec = sum(xr[k] / tot * Wc[:, k] * (1 if sm[k] else 1) for k in range(len(sm)))
        xo, it, bind = solve(np.column_stack([np.clip(wvec, 0, None), np.clip(wvec, None, 0)]), np.array([True, False]))
        rows_out.append({"to": to, "case": "reduced-optimum (shape fixed)", "reduced_mw": tot, "full_grid_mw": xo[0], "full_grid_binding": bind, "iterations": it})
        # fixed Dutch shapes
        for sname, shp in shapes.items():
            wnl = sum(w * col_node(c) for c, w in shp.items())
            Wc = np.column_stack([wnl] + [-col_node(s) for s in sinks]); sm = np.r_[True, np.zeros(len(sinks), bool)]
            xs, it, bind = solve(Wc, sm); xr = solve_reduced([shp] + [{s: -1.0} for s in sinks], sm)
            rows_out.append({"to": to, "case": sname, "reduced_mw": xr[0], "full_grid_mw": xs[0], "full_grid_binding": bind, "iterations": it,
                             "split_full": "; ".join(f"{lab(s)} {v:,.0f}" for s, v in zip(sinks, xs[1:])), "split_reduced": "; ".join(f"{lab(s)} {v:,.0f}" for s, v in zip(sinks, xr[1:]))})
        # the Netherlands as one zone (full grid only)
        Wc = np.column_stack([Wnl_zone] + [-col_node(s) for s in sinks]); sm = np.r_[True, np.zeros(len(sinks), bool)]
        xz, it, bind = solve(Wc, sm)
        rows_out.append({"to": to, "case": "zone (NL spread over 380 kV)", "reduced_mw": np.nan, "full_grid_mw": xz[0], "full_grid_binding": bind, "iterations": it,
                         "split_full": "; ".join(f"{lab(s)} {v:,.0f}" for s, v in zip(sinks, xz[1:]))})
        print(pd.DataFrame(rows_out).tail(4).to_string(), flush=True)
    trans = [(tuple(DEN), ("BE00",), "DE->BE"), (tuple(DEN), ("FR00",), "DE->FR")] + ([(("DE0N",), ("DE0S",), "DEN->DES")] if {"DE0N", "DE0S"} <= set(DEN) else [])
    for srcs, dsts, tl in trans:                                       # 23c: transit, Germany free over its nodes, no Dutch injection
        Wc = np.column_stack([col_node(c) for c in srcs] + [-col_node(c) for c in dsts]); sm = np.r_[np.ones(len(srcs), bool), np.zeros(len(dsts), bool)]
        xt, it, bind = solve(Wc, sm); xr = solve_reduced([{c: 1.0} for c in srcs] + [{c: -1.0} for c in dsts], sm)
        rows_out.append({"to": f"{tl} (transit)", "case": "zone to zone", "reduced_mw": xr[sm].sum(), "full_grid_mw": xt[:len(sm)][sm].sum(), "full_grid_binding": bind, "iterations": it})
    R = pd.DataFrame(rows_out); R["full_over_reduced"] = R.full_grid_mw / R.reduced_mw
    R.to_csv(out / "cases.csv", index=False, float_format="%.1f"); pd.DataFrame(inj_out).to_csv(out / "case_injections.csv", index=False, float_format="%.1f")
    ties = {f"{r.a}-{r.c}": r.capacity for r in b.itertuples() if {r.za, r.zc} & {"NL"} and r.za != r.zc}
    md = [f"# Full-grid check of the Dutch border room — {label}", "", f"Reduced network `{net.name}` (option-3 limits); full grid of `{run.name}` ({n} buses, {len(ld)} records, "
          f"{len(MI)} monitored lines, {nO} outages); rules of `{r05.name}` (margin {MARGIN:.0%}, phase shifters within range).", "",
          "Check, single pairs vs 05n pairs.csv:", "", "```", CK.round(4).to_string(index=False), "```", "",
          "Tie limits in the reduced network (MW): " + ", ".join(f"{k} {v:,.0f}" for k, v in ties.items()), "",
          "Maximum transfer, MW (reduced = what Tulipa can do on the nodal network; full grid = what is N-1 secure under option-3 rules):", "",
          "```", R[["to", "case", "reduced_mw", "full_grid_mw", "full_over_reduced", "split_reduced", "split_full", "full_grid_binding"]].round(2).to_string(index=False), "```"]
    (out / "summary.md").write_text("\n".join(md) + "\n")
    (out / "manifest.json").write_text(json.dumps({"status": "finished", "finished": datetime.datetime.now().isoformat(timespec="seconds"), "config": CONFIG,
                                                   "inputs_sha256": {k: E.sha(p) for k, p in files.items()}, "check": CK.to_dict("records"),
                                                   "outputs_sha256": {q.name: E.sha(q) for q in sorted(out.iterdir()) if q.name != "manifest.json"}}, indent=1))
    print("\n".join(md)); print(f"wrote {out}")


if __name__ == "__main__":
    main()
