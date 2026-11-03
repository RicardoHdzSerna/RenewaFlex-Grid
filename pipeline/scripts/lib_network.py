#!/usr/bin/env python3
"""
lib_network.py — small helpers to read a finished network folder and compute flows on it. Not run on its own.

Used by C1_full_grid_border_check.py and C2_tie_correction.py.
  read_network(folder)   the branches of nodes.csv / flow.csv / flow-milestone.csv as one table (node codes, zones, limit, reactance)
  ptdf(branches)         DC power-flow sensitivities: MW on each branch per MW injected at each node
  network(folder)        read_network + ptdf, keeping only branches with a limit
  max_transfer(...)      the largest Dutch export (or import) the network allows to a set of receiving nodes (a linear program)
  sha(file)              SHA-256 of a file, for the manifests

These functions are copied unchanged from two scripts of the grid project: 10n3_test_2025_nodal_injections_de2.py (the 2025
test on nodal networks) and 22_nl_transfer_capacity_compare.py; only the module prefix (T.) was removed.
"""
from __future__ import annotations
import hashlib, sys
from pathlib import Path
import numpy as np
import pandas as pd
from scipy.optimize import linprog

# node code -> zone label (the German nodes, also north and south, are all "DE_LU"); nodes.csv of a network adds the Dutch nodes
ZONE_OF_NODE = {"AT00": "AT", "BE00": "BE", "CZ00": "CZ", "DE00": "DE_LU", "DE0N": "DE_LU", "DE0S": "DE_LU", "FR00": "FR", "HR00": "HR", "HU00": "HU",
                "NL00": "NL", "PL00": "PL", "RO00": "RO", "SI00": "SI", "SK00": "SK"}
# branches with a limit at or above this value count as unlimited
UNLIMITED_FROM_MW = 1.0e5
# zone in the workbook / nodes.csv -> zone label used here
ZONE_LABEL = {"DE": "DE_LU", "DE_N": "DE_LU", "DE_S": "DE_LU"}


def load_zone_map(d: Path):
    """nodes.csv of the network folder gives every node its zone; added to ZONE_OF_NODE."""
    f = d / "nodes.csv"
    if f.exists():
        nd = pd.read_csv(f)
        for r in nd.itertuples():
            z = ZONE_LABEL.get(str(r.zone), str(r.zone))
            if ZONE_OF_NODE.get(r.node, z) != z:
                sys.exit(f"ABORT: node {r.node} is {ZONE_OF_NODE[r.node]} here but {z} in {f}")
            ZONE_OF_NODE[r.node] = z


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


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


def network(d: Path):
    b = read_network(d); nodes, PT = ptdf(b)
    cap = b.capacity.to_numpy(float); lim = cap < UNLIMITED_FROM_MW
    return b, nodes, PT[lim], cap[lim], [f"{r.a}-{r.c}" for r, l in zip(b.itertuples(), lim) if l]


def max_transfer(nodes, PT, cap, names, nl_shape, sinks, export=True):
    """nl_shape: None = free (one variable per Dutch node, sign-constrained) or dict node->share; sinks: receiving nodes (free split)."""
    nl = [n for n in nodes if ZONE_OF_NODE[n] == "NL"]; ix = {n: i for i, n in enumerate(nodes)}
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
