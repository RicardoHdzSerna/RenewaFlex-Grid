#!/usr/bin/env python3
# core_grid_dcopf (2026-10-21): 03n2_monitored_set_nodal_nl220.py — COPY of scripts/03n_monitored_set_nodal.py (not edited). Changed:
# (1) every DUTCH 220 kV line of at least 1 km (both ends Zone NL at 220 kV; sheets Lines and Tielines) is added to the monitored
# set — the nodal network on SR2025 node set keeps five 220 kV nodes (Bergum, Louwsmeer, Oudehaske, Zeyerveen, Weiwerd) whose
# exchanges run over 220 kV lines only, so with 380 kV lines alone 04n finds no monitored line for them. Foreign 220 kV lines and
# all transformers stay unmonitored (decision of 2026-10-13 otherwise unchanged). User 2026-10-21: "add the Dutch 220 kV lines of
# at least 1 km to the monitored set (foreign 220 kV stays unmonitored), as a new script".
# (2) no abort when no sub-kilometre row joins two representative buses (the landing spurs are not nodes in that node set).
# The header of 03n follows.
# core_grid_dcopf (2026-10-16): copy of archive/dcopf/scripts/119_monitored_set_nodal.py; no edits; the original header follows.
"""
119_monitored_set_nodal.py — step 3 (2026-10-16): the monitored set for the NODAL network = the ">= 1 km" set of
runs/2026-10-16-monitored-380kv-ge1km (380 kV lines of at least 1 km; tee stubs, jumpers and landing circuits under 1 km
excluded, note 20) PLUS every excluded row whose two ends are both representative buses of the nodal workbook. Reason: in
the nodal network those short rows (the Borssele – Zeeuwse Kust landing circuits, Eemshaven Oudeschip – Synergieweg and
– Compensatie filterstation) ARE branches between nodes, and their rating is the only limit of a transfer to the spur bus;
without them the transfer limit of such a node pair is infinite (scripts/120 aborted on 2026-10-16 with the plain >= 1 km
list). The stubs inside the other grids (Y-Niederlangen and the like) stay excluded.

    ~/.tulipa_pipeline_venv/bin/python scripts/119_monitored_set_nodal.py <ge1km folder> inputs/derived/jao_core_<nodal version> <out folder name>

Writes runs/<out folder name>/ {monitored_eics.csv (column eic), added_rows.csv, README.md, manifest.json}; aborts if it exists.
"""
import datetime, hashlib, json, sys
from pathlib import Path

import pandas as pd

DCOPF = Path(__file__).resolve().parents[1]
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(args) != 3:
    sys.exit(__doc__)
SRC, WBD, OUT = Path(args[0]).resolve(), Path(args[1]).resolve(), DCOPF / "runs" / args[2]
if OUT.exists():
    sys.exit(f"ABORT: {OUT} exists — never overwritten")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


f_mon, f_exc, f_wb = SRC / "monitored_eics.csv", SRC / "excluded_stubs.csv", WBD / "jao_core.xlsx"
mon = pd.read_csv(f_mon); exc = pd.read_csv(f_exc); nodes = pd.read_excel(f_wb, sheet_name="Nodes")
reps = set(nodes[nodes.IsRepresentative == 1].Bus)
add = exc[exc.From_node.isin(reps) & exc.To_node.isin(reps) & exc.EIC_Code.notna()].copy()
kv = dict(zip(nodes.Bus, nodes.baseKV.astype(float))); zn = dict(zip(nodes.Bus, nodes.Zone))
ln = pd.concat([pd.read_excel(f_wb, sheet_name=s) for s in ("Lines", "Tielines")], ignore_index=True)
nl220 = ln[ln.From_node.map(zn).eq("NL") & ln.To_node.map(zn).eq("NL") & ln.From_node.map(kv).eq(220.0) & ln.To_node.map(kv).eq(220.0)
           & (ln.Length_km.astype(float) >= 1.0) & ln.EIC_Code.notna()].copy()
if nl220.empty:
    sys.exit("ABORT: no Dutch 220 kV line of at least 1 km found")
new = sorted(set(mon.eic.astype(str)) | set(add.EIC_Code.astype(str)) | set(nl220.EIC_Code.astype(str)))
OUT.mkdir(parents=False)
pd.DataFrame({"eic": new}).to_csv(OUT / "monitored_eics.csv", index=False)
add.to_csv(OUT / "added_rows.csv", index=False)
nl220.to_csv(OUT / "added_nl220_lines.csv", index=False)
(OUT / "README.md").write_text(f"# Monitored set for the nodal network ({WBD.name})\n\nRule: the >= 1 km set of `{SRC.name}` ({len(mon)} EICs) plus every excluded row whose two ends are both representative buses "
                               f"of `{WBD.name}` ({len(add)} rows, `added_rows.csv`): in the nodal network these rows are branches between nodes and their rating is the only limit of a transfer to the spur bus.\n"
                               f"Plus every Dutch 220 kV line of at least 1 km ({len(nl220)} rows, `added_nl220_lines.csv`; user 2026-10-21). "
                               f"Stubs inside the other grids stay excluded ({len(exc) - len(add)} rows). monitored_eics.csv: {len(new)} EICs.\n\nAdded: " + "; ".join(f"{r.Line_name} ({r.Length_km:.2f} km, {r.Capacity_MW:.0f} MW)" for r in add.itertuples()) + "\n")
(OUT / "manifest.json").write_text(json.dumps({"status": "finished", "written": datetime.datetime.now().isoformat(timespec="seconds"), "script": Path(__file__).name, "script_sha256": sha(Path(__file__)),
                                               "inputs_sha256": {str(f_mon): sha(f_mon), str(f_exc): sha(f_exc), str(f_wb): sha(f_wb)}, "representatives": len(reps), "eics_ge1km": int(len(mon)), "rows_added": int(len(add)), "nl220_lines_added": int(len(nl220)),
                                               "eics_total": len(new), "outputs_sha256": {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.name != "manifest.json"}}, indent=1))
print(f"{OUT.name}: {len(new)} EICs = {len(mon)} (>= 1 km) + {len(add)} rows between representative buses + {len(nl220)} Dutch 220 kV lines:")
print(nl220[["Line_name", "From_node", "To_node", "Length_km", "Capacity_MW"]].to_string(index=False))
print(add[["Line_name", "From_node", "To_node", "Length_km", "Capacity_MW"]].to_string(index=False))
