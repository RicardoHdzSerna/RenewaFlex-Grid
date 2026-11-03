#!/usr/bin/env python3
"""
B3_monitored_lines_nodal.py — the monitored lines for a nodal network: B3's list plus Dutch 220 kV lines and short node-to-node rows.

STEP  B3 in run_all.sh (HANDOVER.md section 3.3)

WHAT IT DOES
  Starts from the list of B3_monitored_lines.py and adds:
    * every Dutch 220 kV line of at least 1 km (both ends in the Netherlands at 220 kV; sheets Lines and Tielines);
    * every row under 1 km whose two ends are both nodes of the nodal workbook (e.g. landing circuits), because in the nodal
      network such a row IS a branch and its rating is the only limit of a transfer to that node.
  Foreign 220 kV lines and all transformers stay unmonitored.

WHY
  SR2025 node set keeps five 220 kV-only nodes (Bergum, Louwsmeer, Oudehaske, Zeyerveen, Weiwerd). Their exchanges run over
  220 kV lines only, so with 380 kV lines alone they would have no limit. Decision 21 Oct 2026.

READS   the folder written by B3_monitored_lines.py, inputs/derived/jao_core_<nodal version>/jao_core.xlsx
WRITES  runs/<out folder name>/  monitored_eics.csv, added_rows.csv, added_nl220_lines.csv, README.md, manifest.json.
        Aborts if it exists.

USAGE   python scripts/B3_monitored_lines_nodal.py <B3 folder> inputs/derived/jao_core_<nodal version> <out folder name>

HISTORY Same code as core_grid_dcopf/scripts/03n2_monitored_set_nodal_nl220.py (21 Oct 2026; from archived 119 via 03n); only
        this header was rewritten (the scripts as run, with their history notes, are in background_notes/original_scripts/).
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
