#!/usr/bin/env python3
"""
A7_set_dutch_nodes.py — copy of a workbook in which the listed Dutch buses are the nodes to keep in the reduction.

STEP  A7 in run_all.sh (HANDOVER.md section 2.8)

WHAT IT DOES
  Sets IsRepresentative = 1 for every bus in the node list (column `bus`) and 0 for every other Dutch bus. The reduction (B1)
  keeps the representative buses as nodes and eliminates the rest. Foreign zones keep their one representative bus.
  Nothing else changes: the files are copied byte for byte, jao_core.xlsx is rewritten with only these cells changed, read back
  and checked. A Dutch bus that is already representative in the source must be in the list (else ABORT).

WHY
  The network nodes must be the nodes for which demand and supply keys exist: SR2025 32 I-ELGAS substations
  (inputs/nodesets/nl_ielgas_sander_32.csv: 27 at 380 kV and 5 at 220 kV only).

READS   inputs/derived/jao_core_<source>/, the node list
WRITES  inputs/derived/jao_core_<new>/  (copy + changed IsRepresentative cells, sha256.txt, manifest.json). Aborts if it exists.

USAGE   python scripts/A7_set_dutch_nodes.py <source version> <new version> <node list csv>
        e.g. python scripts/A7_set_dutch_nodes.py v29-vvltr2-2035-tennet-tlb3-rt4k v29-vvltr2-2035-tennet-tlb3-rt4k-nlsander inputs/nodesets/nl_ielgas_sander_32.csv

HISTORY Same code as core_grid_dcopf/scripts/18_nodal_workbook_nodeset.py (19 Oct 2026; from archived 117 via 12); only this
        header was rewritten.
"""
import datetime, hashlib, json, shutil, sys
from pathlib import Path

import numpy as np, openpyxl, pandas as pd

DCOPF = Path(__file__).resolve().parents[1]
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(args) != 3:
    sys.exit(__doc__)
SRC_V, NEW_V, NODESET_CSV = args
NODESET = set(pd.read_csv(NODESET_CSV).bus.astype(str))
SRC, OUT = DCOPF / "inputs" / "derived" / f"jao_core_{SRC_V}", DCOPF / "inputs" / "derived" / f"jao_core_{NEW_V}"
ZONE, KV = "NL", 380.0
if not (SRC / "jao_core.xlsx").exists():
    sys.exit(f"ABORT: source workbook not found: {SRC}")
if OUT.exists():
    sys.exit(f"ABORT: {OUT} exists — never overwritten")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def same(a, b):
    try:
        return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(b)))
    except (TypeError, ValueError):
        return str(a) == str(b)


src_hashes = {p.name: sha(p) for p in sorted(SRC.iterdir()) if p.is_file()}
OUT.mkdir(parents=False)
for p in sorted(SRC.iterdir()):
    if p.is_file():
        shutil.copyfile(p, OUT / p.name)                      # byte copies; sha256.txt and manifest.json are rewritten below
before = pd.read_excel(SRC / "jao_core.xlsx", sheet_name=None)
xl = openpyxl.load_workbook(OUT / "jao_core.xlsx"); ws = xl["Nodes"]
hdr = {c.value: c.column for c in ws[1]}
for k in ("Bus", "IsRepresentative", "baseKV", "Zone"):
    if k not in hdr:
        sys.exit(f"ABORT: Nodes sheet has no column {k}")
changed, reps = [], []
for r in range(2, ws.max_row + 1):
    bus = ws.cell(r, hdr["Bus"]).value
    if bus is None:
        continue
    z, kv, rep = ws.cell(r, hdr["Zone"]).value, ws.cell(r, hdr["baseKV"]).value, ws.cell(r, hdr["IsRepresentative"]).value
    is_rep = rep is not None and str(rep).strip() not in ("", "0", "0.0", "False", "false")
    if z == ZONE and is_rep and bus not in NODESET:
        sys.exit(f"ABORT: {bus} is representative in the source but not in the node set")
    if z == ZONE and bus in NODESET and not is_rep:
        changed.append({"sheet": "Nodes", "row": r, "Bus": bus, "column": "IsRepresentative", "old": rep, "new": 1})
        ws.cell(r, hdr["IsRepresentative"]).value = 1; is_rep = True
    if is_rep:
        reps.append({"Bus": bus, "Zone": z, "baseKV": float(kv)})
xl.save(OUT / "jao_core.xlsx")
# ---- read-back: every sheet identical to the source except Nodes.IsRepresentative on exactly the changed rows
back = pd.read_excel(OUT / "jao_core.xlsx", sheet_name=None)
if set(back) != set(before):
    sys.exit(f"ABORT: sheet set changed: {set(back) ^ set(before)}")
n_cells = 0
for s in before:
    a, b = before[s], back[s]
    if a.shape != b.shape or list(a.columns) != list(b.columns):
        sys.exit(f"ABORT: sheet {s} changed shape or columns")
    for col in a.columns:
        x, y = a[col].astype(str).to_numpy(), b[col].astype(str).to_numpy()
        bad = [int(i) for i in np.flatnonzero(x != y) if not same(x[i], y[i])]
        if s == "Nodes" and col == "IsRepresentative":
            if set(a.Bus.iloc[bad]) != {c["Bus"] for c in changed}:
                sys.exit(f"ABORT: read-back: changed buses differ from the plan: {set(a.Bus.iloc[bad]) ^ {c['Bus'] for c in changed}}")
            n_cells = len(bad)
        elif bad:
            sys.exit(f"ABORT: read-back: unexpected change in {s}.{col}, rows {bad[:5]}")
nodes = back["Nodes"]
n_nl380 = len(NODESET)
if set(nodes.Bus[(nodes.Zone == ZONE) & (nodes.IsRepresentative == 1)]) != NODESET:
    sys.exit("ABORT: Dutch representatives differ from the node set")
n_foreign_reps = int(((nodes.Zone != ZONE) & (nodes.IsRepresentative == 1)).sum())
n_reps = int((nodes.IsRepresentative == 1).sum())
if n_reps != n_nl380 + n_foreign_reps or n_reps != len(reps):
    sys.exit(f"ABORT: representative count {n_reps} != {n_nl380} Dutch 380 kV + {n_foreign_reps} foreign ({len(reps)} listed)")

with open(OUT / "sha256.txt", "w") as fh:
    for p in sorted(OUT.iterdir()):
        if p.name not in ("sha256.txt", "manifest.json"):
            fh.write(f"{sha(p)}  {p.name}\n")
man = {"status": "finished", "written": datetime.datetime.now().isoformat(timespec="seconds"), "script": Path(__file__).name, "script_sha256": sha(Path(__file__)),
       "purpose": "nodal Netherlands on a node set — the listed Dutch buses are representative; everything else is a byte copy of the source",
       "node_set_csv": str(NODESET_CSV), "node_set_sha256": sha(Path(NODESET_CSV)),
       "source_version": SRC_V, "source_sha256": src_hashes, "rule": f"Nodes.IsRepresentative = 1 for every bus with Zone == {ZONE} listed in the node set",
       "changed_cells": n_cells, "changes": changed, "representatives": reps, "n_representatives": n_reps, "n_dutch_380kV": n_nl380, "n_foreign_representatives": n_foreign_reps,
       "files_copied_byte_for_byte": [p for p in src_hashes if p not in ("sha256.txt", "manifest.json")], "source_manifest_kept_as": "manifest_source.json"}
shutil.copyfile(SRC / "manifest.json", OUT / "manifest_source.json") if (SRC / "manifest.json").exists() else None
(OUT / "manifest.json").write_text(json.dumps(man, indent=1))
print(f"{OUT.name}: {n_cells} cells changed; representatives {n_reps} = {n_nl380} Dutch (node set) + {n_foreign_reps} foreign")
print("Dutch representatives:", ", ".join(r["Bus"] for r in reps if r["Zone"] == ZONE))
