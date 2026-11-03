#!/usr/bin/env python3
# core_grid_dcopf (2026-10-23): copy of 10n_test_2025_nodal.py with ONE addition: --injections <parquet> (8760 x nodes, MW, written by
# scripts/19_nl_node_injections_2025.py) gives the nodes of a multi-node zone HOURLY injections instead of a static key share x the
# zone's net position. They must add up to the zone's Core net position every hour (asserted, as before). Output prefix
# fixedposnodalinj_<network>_<injections folder>. Everything else unchanged; the original header follows.
# core_grid_dcopf (2026-10-16): copy of archive/replay2025/scripts/61_fixed_position_test_nodal.py; 3 path/name edit(s), see docs/MAP.md; the original header follows.
"""
61_fixed_position_test_nodal.py — step 3 (2026-10-16): copy of 53_fixed_position_test_dc.py for networks in which ONE bidding zone
is represented by many nodes (the Netherlands at 380 kV, dcopf/scripts/118). Changes against 53, nothing else:

  * the zone of a node is read from the network folder's nodes.csv (column zone; "DE" means DE_LU) and added to ZONE_OF_NODE;
    the twelve TYNDP codes of 53 remain valid;
  * a zone with several nodes takes its injections from a KEY file (--key <csv> with columns node, share; the shares of a zone
    sum to 1): node injection = share x the zone's Core net position, every hour. replay2025/scripts/62 writes a PLACEHOLDER
    even-spread key; the user's demand/supply keys replace it. The German-split positions file of 47/53 is not supported here;
  * the hourly flows of EVERY branch are written (branch_flows_hourly.parquet), so the flows inside the nodal zone can be
    compared between keys later; output directory prefix fixedposnodal_<network>_<key folder | single>.
  Borders are still compared at bidding-zone level (model flow BE-NL = sum of the branches between the Belgian node and all
  Dutch nodes), ALEGrO as in 53. Validation data are only compared against. Original docstring of 53 follows.

53_fixed_position_test_dc.py — copy of 51_fixed_position_test_19.py with ONE correction: the ALEGrO direct-current link.

Found on 2026-10-06 while explaining the Dutch borders. 27, 47 and 51 route each zone's full Core net position through the
AC network and THEN add the ALEGrO exchange (JAO ALDE) to the Belgium-Germany border. But the measured Belgian and German
positions already contain the ALEGrO exchange, and that part does not travel over AC lines. So ALEGrO was counted twice:
the model's border flows out of Belgium and out of Germany did not add up to their positions (mean absolute difference
755 MW = mean |ALDE|; zero for every other zone).
Correction, nothing else changed: the AC network is given the positions MINUS what ALEGrO carries
(Belgium: NP - ALDE; Germany: NP + ALDE; ALDE > 0 = Belgium to Germany), and ALEGrO is added on the Belgium-Germany border
as before. Asserted every hour: for every zone the model's border flows add up to its position.
Effect on the corrected networks: about -0.01 GW on the mean error, -1 point of hours inside the limits; Belgium-Germany
changes most (mean error halves, correlation falls from 0.87 to 0.78).
Output directory prefix fixedposdc_. Original docstring of 51 follows.

51_fixed_position_test_19.py — copy of 47_fixed_position_test_split.py with ONE addition: the Poland–Slovakia border.

Why (2026-10-06): the measured flows contain 19 Core borders; 27 and 47 compare 18, because the networks built so far had no
PL–SK branch (the Krosno–Lemesany tie-lines ended in a dead-end bus, see dcopf/scripts/66_fix_tieline_workbook.py). The
positions of PL and SK have always included the measured PL–SK flow, so a network without that branch had to carry it
through Czechia. Changes against 47, nothing else:
  * PAIRS has a 19th pair ("PL", "SK"); the 18 pairs of 27/47 are kept first, in the same order (PAIRS18);
  * a border without a branch in the network is reported with model flow 0 (r undefined) instead of being left out;
  * the summary gives mean r and mean MAE over the 18 borders of 27/47 (comparable with every earlier number) AND the
    MAE over all 19; output directory prefix fixedpos19_.
Run on a network without a PL–SK branch, the 18-border numbers equal 47's (checked: see notes/05).

--- header of 47 follows ---
47_fixed_position_test_split.py — the fixed-position test (27_fixed_position_test.py) for networks in which a bidding zone
is represented by more than one node (Germany as DE0N + DE0S). Copy of 27 with these changes, nothing else:

  * node code = the asset name up to "_E_Demand" (27 takes the first four characters and knows twelve codes);
  * a zone with two nodes takes its two injections from a positions file (46_de_split_positions.py). Their sum must equal
    the zone's Core net position in every hour — asserted, abort above 1e-6 MW;
  * a border is compared at bidding-zone level: the model flow DE-PL is the sum of the branches between PL and BOTH German
    nodes, so every table lines up with the single-node baseline (same 18 borders, same measured series);
  * a branch whose capacity is the "unlimited" marker (>= 1e5 MW) is reported but not counted in the feasibility share;
  * with --baseline-net, branches that also exist in the baseline (same two zones, neither of them split) are additionally
    checked against the BASELINE limit: that isolates the effect of the routing from the effect of the refitted limits;
  * a manifest with input hashes and the configuration is written before anything is computed.

    ~/.tulipa_pipeline_venv/bin/python -W ignore scripts/47_fixed_position_test_split.py <network folder>
        [--positions runs/desplit_positions_<ver>/positions.parquet --variant primary] [--baseline-net <folder>] [--tag t]

Positions: each zone's physical Core net position from the measured ENTSO-E flows, as 27 'physical'. BE-DE is compared as
AC branch(es) + ALEGrO (JAO ALDE net position), as 27. Run on a single-node network without --positions it reproduces 27
(checked: see notes/04). Validation data are only compared against; the split of the German position comes from 46.
Writes runs/fixedposdc_<network>_<variant>[_tag]/{manifest.json, borders.csv, branches.csv, summary.md, border_flows_hourly.parquet}.
"""
from __future__ import annotations
import datetime, hashlib, json, sys
from pathlib import Path
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
HIST_ROOT = ROOT / "inputs" / "validation_2025"
H = pd.date_range("2025-01-01", "2026-01-01", freq="1h", tz="UTC", inclusive="left")
ZONE_OF_NODE = {"AT00": "AT", "BE00": "BE", "CZ00": "CZ", "DE00": "DE_LU", "DE0N": "DE_LU", "DE0S": "DE_LU", "FR00": "FR", "HR00": "HR", "HU00": "HU",
                "NL00": "NL", "PL00": "PL", "RO00": "RO", "SI00": "SI", "SK00": "SK"}
HALF_OF_NODE = {"DE0N": "DE_N", "DE0S": "DE_S"}                 # column suffix in the positions file
PAIRS = [("AT", "CZ"), ("AT", "DE_LU"), ("AT", "HU"), ("AT", "SI"), ("BE", "DE_LU"), ("BE", "FR"), ("BE", "NL"), ("CZ", "DE_LU"), ("CZ", "PL"), ("CZ", "SK"),
         ("DE_LU", "FR"), ("DE_LU", "NL"), ("DE_LU", "PL"), ("HR", "HU"), ("HR", "SI"), ("HU", "RO"), ("HU", "SI"), ("HU", "SK"), ("PL", "SK")]     # the 18 borders of 27, same orientation, + PL-SK
PAIRS18 = [f"{a}-{c}" for a, c in PAIRS[:18]]
CORE = ["AT", "BE", "CZ", "DE_LU", "FR", "HR", "HU", "NL", "PL", "RO", "SI", "SK"]
UNLIMITED_FROM_MW = 1.0e5
TOL_MW = 1e-6
ZONE_LABEL = {"DE": "DE_LU"}                                    # workbook zone -> the zone label of the measured data


def load_zone_map(d: Path):
    """61: nodes.csv of the network folder (dcopf/scripts/118) gives every node its zone; added to ZONE_OF_NODE."""
    f = d / "nodes.csv"
    if f.exists():
        nd = pd.read_csv(f)
        for r in nd.itertuples():
            z = ZONE_LABEL.get(str(r.zone), str(r.zone))
            if ZONE_OF_NODE.get(r.node, z) != z:
                sys.exit(f"ABORT: node {r.node} is {ZONE_OF_NODE[r.node]} in 53 but {z} in {f}")
            ZONE_OF_NODE[r.node] = z


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def load_measured():
    hist = HIST_ROOT
    f_phys, f_jao = hist / "crossborder_flows_physical_hourly_mw.parquet", hist / "jao_net_position_hourly_mw.parquet"
    phys = pd.read_parquet(f_phys).set_axis(H); jao = pd.read_parquet(f_jao).set_axis(H)
    meas = lambda a, c: (phys.get(f"{a}>{c}", pd.Series(0.0, index=H)).fillna(0) - phys.get(f"{c}>{a}", pd.Series(0.0, index=H)).fillna(0))
    NP = pd.DataFrame({z: sum(meas(z, y) for y in CORE if y != z) for z in CORE})
    alde = jao.get("ALDE", pd.Series(0.0, index=H))
    M = pd.DataFrame({f"{a}-{c}": meas(a, c) for a, c in PAIRS})
    return {"hist": hist, "files": [f_phys, f_jao], "NP": NP, "alde": alde, "M": M}


def read_network(d: Path) -> pd.DataFrame:
    load_zone_map(d)
    fl, fm = pd.read_csv(d / "flow.csv"), pd.read_csv(d / "flow-milestone.csv")
    b = fm[fm.dc_opf == True].merge(fl[["from_asset", "to_asset", "capacity"]], on=["from_asset", "to_asset"]).reset_index(drop=True)
    b["a"] = b.from_asset.str.split("_E_Demand").str[0]; b["c"] = b.to_asset.str.split("_E_Demand").str[0]
    unknown = (set(b.a) | set(b.c)) - set(ZONE_OF_NODE)
    if unknown:
        sys.exit(f"ABORT: node code(s) without a zone: {unknown}")
    b["za"] = b.a.map(ZONE_OF_NODE); b["zc"] = b.c.map(ZONE_OF_NODE)
    return b


def ptdf(b: pd.DataFrame):
    nodes = sorted(set(b.a) | set(b.c)); ix = {n: i for i, n in enumerate(nodes)}
    A = np.zeros((len(b), len(nodes)))
    for k, r in enumerate(b.itertuples()):
        A[k, ix[r.a]], A[k, ix[r.c]] = 1, -1
    Bd = np.diag(1 / b.reactance.to_numpy()); Bbus = A.T @ Bd @ A
    ref = ix[next(n for n in nodes if ZONE_OF_NODE[n] == "DE_LU")]; keep = [i for i in range(len(nodes)) if i != ref]     # reference node: irrelevant for balanced injections
    X = np.zeros((len(nodes), len(nodes))); X[np.ix_(keep, keep)] = np.linalg.inv(Bbus[np.ix_(keep, keep)])
    return nodes, Bd @ A @ X


def injections(nodes, NP: pd.DataFrame, key: dict | None, inj: pd.DataFrame | None = None) -> np.ndarray:
    """61: a zone with one node gets its Core net position; a zone with several nodes splits it by the key's shares."""
    cols = []
    by_zone = {}
    for n in nodes:
        by_zone.setdefault(ZONE_OF_NODE[n], []).append(n)
    for z, ns in by_zone.items():
        if len(ns) > 1 and inj is not None:                         # 10n2: hourly injections for every node of the zone
            missing = [n for n in ns if n not in inj.columns]
            if missing:
                sys.exit(f"ABORT: injections have no column for node(s) {missing}")
        elif len(ns) > 1:
            if key is None:
                sys.exit(f"ABORT: zone {z} has {len(ns)} nodes; pass --key")
            missing = [n for n in ns if n not in key]
            if missing:
                sys.exit(f"ABORT: key has no share for node(s) {missing}")
            tot = float(sum(key[n] for n in ns))
            if not abs(tot - 1.0) <= 1e-9:
                sys.exit(f"ABORT: the shares of zone {z} sum to {tot:.12f}, not 1")
    for n in nodes:
        z = ZONE_OF_NODE[n]
        cols.append(NP[z].to_numpy() if len(by_zone[z]) == 1 else (inj[n].to_numpy() if inj is not None else float(key[n]) * NP[z].to_numpy()))
    P = np.column_stack(cols)
    for z, ns in by_zone.items():                                   # the nodes of a zone must add up to the zone's Core net position, every hour
        if len(ns) > 1:
            err = float(np.abs(P[:, [nodes.index(n) for n in ns]].sum(axis=1) - NP[z].to_numpy()).max())
            if not err <= TOL_MW:
                sys.exit(f"ABORT: the nodes of {z} do not sum to its net position (max difference {err:.3e} MW)")
    if not np.abs(P.sum(axis=1)).max() <= 1e-3:
        sys.exit(f"ABORT: injections do not sum to zero (max {np.abs(P.sum(axis=1)).max():.3e} MW)")
    return P


def border_flows(F: np.ndarray, b: pd.DataFrame, alde: pd.Series) -> pd.DataFrame:
    out = {}
    for za, zc in PAIRS:
        comp = pd.Series(0.0, index=H); n = 0
        for k, r in enumerate(b.itertuples()):
            if (r.za, r.zc) == (za, zc):
                comp = comp + F[:, k]; n += 1
            elif (r.za, r.zc) == (zc, za):
                comp = comp - F[:, k]; n += 1
        # 51: a border without a branch is kept with model flow 0 (47 left it out)
        if {za, zc} == {"BE", "DE_LU"}:
            comp = comp + alde
        out[f"{za}-{zc}"] = comp
    return pd.DataFrame(out)


def border_table(B: pd.DataFrame, M: pd.DataFrame, mask=None) -> pd.DataFrame:
    rows = []
    for col in B.columns:
        c, m = (B[col], M[col]) if mask is None else (B[col][mask], M[col][mask])
        rows.append({"border": col, "hourly_r": c.corr(m), "model_mean_gw": c.mean() / 1e3, "measured_mean_gw": m.mean() / 1e3, "mean_error_gw": (c.mean() - m.mean()) / 1e3, "mae_gw": (c - m).abs().mean() / 1e3})
    return pd.DataFrame(rows)


def evaluate(d: Path, meas: dict, key: dict | None = None, inj: pd.DataFrame | None = None):
    b = read_network(d); nodes, PT = ptdf(b)
    P = injections(nodes, meas["NP"], key, inj).astype(float)
    # 53: ALEGrO carries `alde` from Belgium to Germany outside the AC network; the AC network gets the rest.
    a = meas["alde"].to_numpy(); be = [i for i, n in enumerate(nodes) if ZONE_OF_NODE[n] == "BE"]; de = [i for i, n in enumerate(nodes) if ZONE_OF_NODE[n] == "DE_LU"]
    if len(be) != 1:
        sys.exit("ABORT: expected one Belgian node")
    P[:, be[0]] -= a
    P[:, de[-1 if len(de) > 1 else 0]] += a                      # the German node the link lands at: Oberzier lies in the southern half (DE0S sorts last)
    F = P @ PT.T
    B = border_flows(F, b, meas["alde"])
    for z in CORE:                                              # every zone: border flows (ALEGrO included) must add up to its position
        s = sum((B[c] if c.split("-")[0] == z else -B[c]) for c in B.columns if z in (c.split("-")[0], c.split("-", 1)[1]))
        err = float((s - meas["NP"][z]).abs().max())
        if err > 1e-3:
            sys.exit(f"ABORT: border flows of {z} do not add up to its position (max {err:.3f} MW)")
    return b, nodes, F, B


def main():
    args = sys.argv[1:]
    d = Path(args[0]).resolve()
    opt = lambda k, default=None: args[args.index(k) + 1] if k in args else default
    keyf = Path(opt("--key")).resolve() if opt("--key") else None
    injf = Path(opt("--injections")).resolve() if opt("--injections") else None
    if not injf:
        sys.exit("ABORT: 10n2 needs --injections <parquet>; use 10n for a static key")
    basef = Path(opt("--baseline-net")).resolve() if opt("--baseline-net") else None; tag = opt("--tag", "")
    out = ROOT / "runs" / f"fixedposnodalinj_{d.name}_{injf.parent.name}{('_' + tag) if tag else ''}"
    if out.exists():
        sys.exit(f"ABORT: {out} exists — never overwritten")
    meas = load_measured()
    keydf = pd.read_csv(keyf) if keyf else None
    key = dict(zip(keydf.node, keydf.share.astype(float))) if keyf else None
    key_kind = str(keydf.kind.iloc[0]) if (keyf and "kind" in keydf.columns) else None
    inputs = {"flow.csv": d / "flow.csv", "flow-milestone.csv": d / "flow-milestone.csv", "physical_flows": meas["files"][0], "jao_net_positions(ALDE only)": meas["files"][1]}
    if keyf: inputs["key"] = keyf
    inputs["injections"] = injf
    inj = pd.read_parquet(injf); inj.index = pd.DatetimeIndex(inj.index)
    if not inj.index.equals(H):
        sys.exit("ABORT: the injections are not the 8760 hours of 2025 (UTC)")
    if basef: inputs["baseline flow.csv"] = basef / "flow.csv"; inputs["baseline flow-milestone.csv"] = basef / "flow-milestone.csv"
    out.mkdir(parents=True)
    CONFIG = {"alegro": "taken out of the AC injections (BE - ALDE, DE + ALDE), added on the BE-DE border; zone balance asserted", "script": Path(__file__).name, "script_sha256": sha(Path(__file__)), "network": str(d), "key": str(keyf) if keyf else None, "key_kind": key_kind, "injections": str(injf), "nodes_csv": str(d / "nodes.csv") if (d / "nodes.csv").exists() else None,
              "baseline_network": str(basef) if basef else None, "hist_run": meas["hist"].name, "position_mode": "physical (Core net positions from measured flows, as 27)",
              "borders": [f"{a}-{c}" for a, c in PAIRS], "unlimited_from_mw": UNLIMITED_FROM_MW, "tolerance_mw": TOL_MW}
    (out / "manifest.json").write_text(json.dumps({"status": "started", "started": datetime.datetime.now().isoformat(timespec="seconds"), "config": CONFIG, "inputs_sha256": {k: sha(p) for k, p in inputs.items()}}, indent=1))
    b, nodes, F, B = evaluate(d, meas, key, inj)
    t = border_table(B, meas["M"]); t.to_csv(out / "borders.csv", index=False, float_format="%.4f")
    t18 = t[t.border.isin(PAIRS18)]; assert len(t18) == 18
    B.round(2).to_parquet(out / "border_flows_hourly.parquet")
    pd.DataFrame(F, index=H, columns=[f"{r.a}-{r.c}" for r in b.itertuples()]).round(2).to_parquet(out / "branch_flows_hourly.parquet")   # 61: every branch, hourly
    cap = b.capacity.to_numpy(); unl = cap >= UNLIMITED_FROM_MW
    util = np.abs(F) / cap
    key = [f"{r.a}-{r.c}" for r in b.itertuples()]
    u = pd.DataFrame({"branch": key, "zones": [f"{r.za}-{r.zc}" for r in b.itertuples()], "reactance_pu": b.reactance.to_numpy(), "limit_mw": np.where(unl, np.nan, cap), "unlimited": unl,
                      "mean_flow_gw": F.mean(axis=0) / 1e3, "mean_abs_flow_gw": np.abs(F).mean(axis=0) / 1e3, "p50": np.quantile(util, .5, axis=0), "p95": np.quantile(util, .95, axis=0),
                      "p99": np.quantile(util, .99, axis=0), "share_h_over_limit": (util > 1).mean(axis=0)})
    u.loc[unl, ["p50", "p95", "p99", "share_h_over_limit"]] = np.nan
    any_over = float((util[:, ~unl] > 1).any(axis=1).mean())
    if unl.any() and not (np.abs(F[:, unl]) < cap[unl]).all():
        sys.exit("ABORT: an 'unlimited' branch reached its marker capacity")
    extra = []
    if basef is not None:                                           # same branch, baseline limit: the routing effect alone
        bb = read_network(basef); blim = {frozenset((r.a, r.c)): r.capacity for r in bb.itertuples()}
        u["baseline_limit_mw"] = [blim.get(frozenset((r.a, r.c)), np.nan) for r in b.itertuples()]
        u["share_h_over_baseline_limit"] = [float((np.abs(F[:, k]) > u.baseline_limit_mw.iloc[k]).mean()) if np.isfinite(u.baseline_limit_mw.iloc[k]) else np.nan for k in range(len(b))]
        common = np.isfinite(u.baseline_limit_mw.to_numpy())
        extra.append(f"Branches that also exist in the baseline ({int(common.sum())}), against the BASELINE limits: hours with at least one of them over {float((np.abs(F[:, common]) > u.baseline_limit_mw.to_numpy()[common]).any(axis=1).mean()) * 100:.1f} %.")
    u.to_csv(out / "branches.csv", index=False, float_format="%.5f")
    de = meas["NP"]["DE_LU"].to_numpy()
    cde = {c: float(np.corrcoef((B[c] - meas["M"][c]).to_numpy(), de)[0, 1]) for c in ("AT-CZ", "CZ-DE_LU") if c in B.columns}
    md = [f"# Fixed-position test — {d.name}, hourly injections `{injf.parent.name}`", "",
          f"Routing, the 18 borders of 27/47: mean hourly r {t18.hourly_r.mean():.3f}, mean MAE {t18.mae_gw.mean():.3f} GW. All 19 borders (with PL-SK): mean MAE {t.mae_gw.mean():.3f} GW"
          + (f", mean hourly r {t.hourly_r.mean():.3f}." if t.hourly_r.notna().all() else " (PL-SK has no branch in this network: model flow 0, r undefined)."),
          f"Limits: hours with at least one branch over its fitted limit {any_over * 100:.1f} %" + (f" ({int(unl.sum())} unlimited branch not counted)." if unl.any() else "."), *extra,
          f"Correlation of the routing error with Germany's net position: " + ", ".join(f"{c} {v:+.2f}" for c, v in cde.items()) + ".", "",
          "```", t.round(3).to_string(index=False), "```", "", "```", u.round(3).to_string(index=False), "```"]
    (out / "summary.md").write_text("\n".join(md) + "\n")
    (out / "manifest.json").write_text(json.dumps({"status": "finished", "finished": datetime.datetime.now().isoformat(timespec="seconds"), "config": CONFIG, "inputs_sha256": {k: sha(p) for k, p in inputs.items()},
                                                   "result": {"mean_hourly_r_18": float(t18.hourly_r.mean()), "mean_mae_gw_18": float(t18.mae_gw.mean()), "mean_mae_gw_19": float(t.mae_gw.mean()), "share_hours_any_branch_over_limit": any_over},
                                                   "outputs_sha256": {q.name: sha(q) for q in sorted(out.iterdir()) if q.name != "manifest.json"}}, indent=1))
    print("\n".join(md)); print(f"wrote {out}")


if __name__ == "__main__":
    main()
