#!/usr/bin/env python3
"""
22_nl_transfer_capacity_compare.py — how much can the Netherlands export to / import from its Core neighbours in the country network
(one Dutch node) and in the nodal network (Dutch nodes)? (2026-10-23, user: "How does going from one zone to nodes change ... the
total transfer capacity between the Netherlands and its neighbors?")

On each network folder as Tulipa would see it (flow.csv limits = option 3, flow-milestone.csv reactances, DC power flow), a linear
programme maximises a bilateral transfer t: the Dutch side injects t (export) or takes t (import), the receiving side is BE00, DE00,
or BE00 + DE00 with a free split; every other zone 0; every limited branch within |flow| <= limit. ALEGrO is not involved.
The Dutch side in the nodal network is placed in three ways:
  free      any distribution over the Dutch nodes (each node one sign: >= 0 for export, <= 0 for import) — the best case;
  even      1/31 per node;
  keyed     export: SR2025 generation keys weighted by Dutch 2025 generation per technology (components_twh.csv of a 19/19b run,
            positive generation columns); import: SR2025 demand key (E_Demand). Fixed shape.
Also listed: sum of the limits of the border branches, and the N-1 transaction limits (pairs.csv of the 05/05n runs).
No validation data are read.

    ~/.tulipa_pipeline_venv/bin/python scripts/22_nl_transfer_capacity_compare.py <country network> <nodal network> <country 05 run> <nodal 05n run> <19 run> <label>

Writes runs/transfercap_<label>/{manifest.json (first), transfers.csv, summary.md}; aborts if the folder exists.
"""
from __future__ import annotations
import datetime, importlib.util, json, sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.optimize import linprog

ROOT = Path(__file__).resolve().parents[1]
_s = importlib.util.spec_from_file_location("t10n2", ROOT / "scripts" / "10n2_test_2025_nodal_injections.py"); T = importlib.util.module_from_spec(_s); _s.loader.exec_module(T)
SH = Path("/Users/ricardohernandezserna/TNO/RenewaFLEX/nl_merge/nl_inputs/2035/shares.csv")
GEN_COLS = ["Biomass", "Fossil Gas", "Fossil Hard coal", "Hydro Run-of-river and pondage", "Nuclear", "Other", "Solar", "Waste", "Wind Offshore", "Wind Onshore"]


def network(d: Path):
    b = T.read_network(d); nodes, PT = T.ptdf(b)
    cap = b.capacity.to_numpy(float); lim = cap < T.UNLIMITED_FROM_MW
    return b, nodes, PT[lim], cap[lim], [f"{r.a}-{r.c}" for r, l in zip(b.itertuples(), lim) if l]


def max_transfer(nodes, PT, cap, names, nl_shape, sinks, export=True):
    """nl_shape: None = free (one variable per Dutch node, sign-constrained) or dict node->share; sinks: receiving nodes (free split)."""
    nl = [n for n in nodes if T.ZONE_OF_NODE[n] == "NL"]; ix = {n: i for i, n in enumerate(nodes)}
    src = nl if nl_shape is None else ["shape"]
    nv = len(src) + len(sinks)                                       # variables: Dutch side amounts, sink amounts (all >= 0)
    sgn = 1.0 if export else -1.0
    Inj = np.zeros((len(nodes), nv))
    for k, n in enumerate(src):
        if nl_shape is None:
            Inj[ix[n], k] = sgn
        else:
            for m, s in nl_shape.items():
                Inj[ix[m], k] = sgn * s
    for k, n in enumerate(sinks):
        Inj[ix[n], len(src) + k] = -sgn
    Fm = PT @ Inj                                                     # branch flow per unit of each variable
    A = np.vstack([Fm, -Fm]); bvec = np.r_[cap, cap]
    Aeq = np.r_[np.ones(len(src)), -np.ones(len(sinks))][None, :]
    c = -np.r_[np.ones(len(src)), np.zeros(len(sinks))]
    r = linprog(c, A_ub=A, b_ub=bvec, A_eq=Aeq, b_eq=[0.0], bounds=[(0, None)] * nv, method="highs")
    if r.status != 0:
        sys.exit(f"ABORT: LP {r.message}")
    f = Fm @ r.x; util = np.abs(f) / cap; bind = [names[i] for i in np.argsort(-util)[:3] if util[i] > 1 - 1e-6]
    split = {n: float(r.x[len(src) + k]) for k, n in enumerate(sinks)}
    return -r.fun, bind, split


def main():
    args = sys.argv[1:]
    if len(args) != 6:
        sys.exit(__doc__)
    cnet, nnet, c05, n05, r19, label = [Path(a).resolve() for a in args[:5]] + [args[5]]
    out = ROOT / "runs" / f"transfercap_{label}"
    if out.exists():
        sys.exit(f"ABORT: {out} exists — never overwritten")
    files = {f"{k}/{f}": p / f for k, p in (("country", cnet), ("nodal", nnet)) for f in ("flow.csv", "flow-milestone.csv", "nodes.csv")}
    files.update({"country pairs": c05 / "pairs.csv", "nodal pairs": n05 / "pairs.csv", "components_twh": r19 / "components_twh.csv", "shares.csv": SH})
    out.mkdir(parents=True)
    CONFIG = {"script": Path(__file__).name, "script_sha256": T.sha(Path(__file__)), "country_network": str(cnet), "nodal_network": str(nnet), "country_05": str(c05), "nodal_05n": str(n05), "run_19": str(r19)}
    (out / "manifest.json").write_text(json.dumps({"status": "started", "started": datetime.datetime.now().isoformat(timespec="seconds"), "config": CONFIG, "inputs_sha256": {k: T.sha(p) for k, p in files.items()}}, indent=1))

    ct = pd.read_csv(files["components_twh"]).set_index("node"); gen = ct[[c for c in GEN_COLS if c in ct.columns]].clip(lower=0).sum(axis=1); gkey = (gen / gen.sum()).to_dict()
    sh = pd.read_csv(SH); dk = sh[sh.tech == "E_Demand"].assign(node=lambda x: x.node.replace({"NL-TILBURG": "NL-GEERTRUIDENBERG"})).groupby("node").share.sum()
    rows = []
    for model, d in (("country", cnet), ("nodal", nnet)):
        T.ZONE_OF_NODE.update({})                                       # read_network adds the nodal codes
        b, nodes, PT, cap, names = network(d)
        nl = [n for n in nodes if T.ZONE_OF_NODE[n] == "NL"]
        shapes = {"one node": {nl[0]: 1.0}} if len(nl) == 1 else {"free": None, "even": {n: 1 / len(nl) for n in nl}, "keyed": "keyed"}
        dkey = (dk.reindex(nl).fillna(0) / dk.reindex(nl).fillna(0).sum()).to_dict() if len(nl) > 1 else None
        border = {z: float(sum(c for r, c in zip(b.itertuples(), b.capacity) if {r.za, r.zc} == {"NL", z})) for z in ("BE", "DE_LU")}
        for dirn in ("export", "import"):
            for to in (("BE00",), ("DE00",), ("BE00", "DE00")):
                for sname, shp in shapes.items():
                    if shp == "keyed":
                        shp = gkey if dirn == "export" else dkey
                    t, bind, split = max_transfer(nodes, PT, cap, names, shp, list(to), dirn == "export")
                    rows.append({"model": model, "direction": dirn, "neighbour": "+".join(z[:2] for z in to), "dutch_side": sname, "max_mw": t,
                                 "split": "; ".join(f"{k[:2]} {v:,.0f}" for k, v in split.items()) if len(to) > 1 else "", "binding": "; ".join(bind)})
        rows.append({"model": model, "direction": "border branch limits", "neighbour": "BE", "dutch_side": "sum", "max_mw": border["BE"]})
        rows.append({"model": model, "direction": "border branch limits", "neighbour": "DE", "dutch_side": "sum", "max_mw": border["DE_LU"]})
    R = pd.DataFrame(rows); R.to_csv(out / "transfers.csv", index=False, float_format="%.1f")
    cp = pd.read_csv(files["country pairs"]); np_ = pd.read_csv(files["nodal pairs"])
    ttc_c = {z: float(cp[((cp.zone_a == z) & (cp.zone_b == "NL")) | ((cp.zone_a == "NL") & (cp.zone_b == z))].ttc_pst_mw.iloc[0]) for z in ("BE", "DE")}
    nb = {z: np_[(np_.node_a.str.startswith("NL-") & (np_.node_b == f"{z}00")) | (np_.node_b.str.startswith("NL-") & (np_.node_a == f"{z}00"))].ttc_pst_mw for z in ("BE", "DE")}
    piv = R[R.direction.isin(["export", "import"])].pivot_table(index=["direction", "neighbour"], columns=["model", "dutch_side"], values="max_mw")
    md = [f"# Dutch transfer capacity, country vs nodal network — {label}", "", f"Country `{cnet.name}`; nodal `{nnet.name}`; option-3 limits as in flow.csv.", "",
          "Maximum bilateral transfer (MW; other zones 0):", "", "```", piv.round(0).to_string(), "```", "",
          "Binding branches and split:", "", "```", R[R.direction.isin(["export", "import"])][["model", "direction", "neighbour", "dutch_side", "max_mw", "split", "binding"]].round(0).to_string(index=False), "```", "",
          "Sum of border branch limits (MW): " + ", ".join(f"{r.model} NL–{r.neighbour} {r.max_mw:,.0f}" for r in R[R.direction == "border branch limits"].itertuples()), "",
          f"N-1 transaction limits with phase shifters (05/05n pairs.csv): country NL–BE {ttc_c['BE']:,.0f}, NL–DE {ttc_c['DE']:,.0f} MW; nodal, Dutch node -> BE00: "
          f"{nb['BE'].min():,.0f}–{nb['BE'].max():,.0f} (median {nb['BE'].median():,.0f}), -> DE00: {nb['DE'].min():,.0f}–{nb['DE'].max():,.0f} (median {nb['DE'].median():,.0f}) MW."]
    (out / "summary.md").write_text("\n".join(md) + "\n")
    (out / "manifest.json").write_text(json.dumps({"status": "finished", "finished": datetime.datetime.now().isoformat(timespec="seconds"), "config": CONFIG, "inputs_sha256": {k: T.sha(p) for k, p in files.items()},
                                                   "outputs_sha256": {q.name: T.sha(q) for q in sorted(out.iterdir()) if q.name != "manifest.json"}}, indent=1))
    print("\n".join(md)); print(f"wrote {out}")


if __name__ == "__main__":
    main()
