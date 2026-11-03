#!/usr/bin/env python3
"""
A2_build_patch_from_decisions.py — turn a decision table of TenneT projects into a workbook patch.

WHAT IT DOES
  Reads a decision table (one row per element a TenneT project changes: a new node, a new line, or a new rating / reactance
  for an existing line) and writes the patch files that A5_apply_patches.py applies to a grid workbook.
  Only the rows of the chosen rule are used (column rule_<rule> = "yes") and rows marked "rejected" in column `status` are left out.

WHY
  This is how the 2035 grid is made: TenneT's Investment Plan 2026 (IP2026) lists the projects; the decision table says which
  of them count for the target year and what each one does to the grid. The table for 2035 is
  inputs/patches/ip2026_nl_2035_decisions/decision_table.csv (27 rows for 28 projects). For 2040, copy that table, add the 2040 projects and run
  this script again with a new patch name.
  (The script that originally built the 2035 patches, 112_build_ip2026_2035_patches.py, is lost; this one was written for the
  handover and reproduces the files of both 2035 patches exactly: see run_all.sh, step A2.)

THE DECISION TABLE (columns that are read)
  row_id            e.g. D2035-004 (also used as the reference in patch_metadata.csv)
  project           TenneT project code, e.g. A-1002678
  rule_<rule>       "yes" / "no": does this row count under the rule (rule_tennet = realisation phase only; rule_amir = also
                    preparation phase)
  status            proposed / approved / needs confirmation / rejected  (only "rejected" is left out)
  action            "add node", "add line", "modify: ..." (any text starting with "modify"), "skip ..." (recorded, not built)
  sheet             workbook sheet of a modified row: Lines or Tielines
  target_line_name  name of the line (or of the bus, for "add node")
  target_eic        EIC code of a modified row
  from_node, to_node                       buses of a new line
  current_now_A, current_new_A             current (A) before and after
  capacity_now_MW, capacity_new_MW         rating (MW) before and after, = sqrt(3) x 400 kV x current / 1000 at 380 kV
  X_now_ohm, X_new_ohm                     series reactance (ohm) before and after
  length_km                                length of a new line
  value_rule                               where the values come from (copied to patch_metadata.csv); for "add node" it must
                                           contain the coordinates as "... -> <lat> N <lon> E"
  ip26_page, phase_layer, ibn_ip2026, note evidence (copied to patch_metadata.csv)

USAGE
  python scripts/A2_build_patch_from_decisions.py <decision folder> <rule> <base workbook version> <patch name> [--eic-prefix=PATCH-NL35]
  e.g. python scripts/A2_build_patch_from_decisions.py inputs/patches/ip2026_nl_2035_decisions tennet v29 ip2026_nl_2035_tennet

OUTPUT
  inputs/patches/<patch name>/  nodes_add.csv, lines_add.csv, lines_modify.csv, transformers_add.csv (empty), patch_metadata.csv,
  CHANGELOG.md, manifest.json. Aborts if the folder exists. New lines get EIC codes <prefix>-0001, -0002, ... in table order.
"""
import datetime, hashlib, json, re, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LINE_COLS = ["Line_name", "EIC_Code", "From_node", "To_node", "Voltage_level", "Currrent_(A)", "R", "X", "B", "Length_km", "Capacity_MW"]
NODE_COLS = ["Bus", "IsRepresentative", "Type", "PD", "QD", "GS", "BS", "Area", "Vm", "Va", "baseKV", "Zone", "Vmax", "Vmin", "Latitude", "Longitude"]
MODIFY_COLS = ["sheet", "Line_name", "EIC_Code", "current_old_A", "current_new_A", "capacity_old_MW", "capacity_new_MW", "X_old_ohm", "X_new_ohm",
               "decision_row", "project", "action"]


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def kv_of(bus):
    """Voltage level from the bus name, e.g. TILBURG_380 -> 380."""
    return int(str(bus).rsplit("_", 1)[1])


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 4:
        sys.exit(__doc__)
    dec_dir, rule, base, name = Path(args[0]), args[1], args[2], args[3]
    prefix = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--eic-prefix=")), "PATCH-NL35")
    out = ROOT / "inputs" / "patches" / name
    if out.exists():
        sys.exit(f"ABORT: {out} exists")
    table = pd.read_csv(dec_dir / "decision_table.csv", dtype=str, keep_default_na=False)
    if f"rule_{rule}" not in table.columns:
        sys.exit(f"ABORT: the decision table has no column rule_{rule}")
    used = table[(table[f"rule_{rule}"] == "yes") & (table["status"] != "rejected")]

    nodes, lines, modify, meta, stations = [], [], [], [], []
    for r in used.to_dict("records"):
        action = r["action"]
        evidence = f"IP2026 p{r['ip26_page']}: {r['project_name']}, {r['phase_layer']}, {r['ibn_ip2026']}"
        if action == "add node":
            m = re.search(r"->\s*([\d.]+)\s*N\s*([\d.]+)\s*E", r["value_rule"])
            if not m:
                sys.exit(f"ABORT: {r['row_id']}: no coordinates '-> <lat> N <lon> E' in value_rule")
            bus = r["target_line_name"]; kv = kv_of(bus)
            nodes.append([bus, 0, 1, 0, 0, 0, 0, "NL", 1, 0, kv, "NL", 1.1, 0.9, float(m.group(1)), float(m.group(2))])
            meta.append({"patch_id": bus, "sheet": "Nodes", "row": bus, "decision_row": r["row_id"], "project": r["project"],
                         "source": r["value_rule"], "conversion": "defaults of the Dutch 380 kV nodes", "evidence": evidence})
        elif action == "add line":
            eic = f"{prefix}-{len(lines) + 1:04d}"
            lines.append([r["target_line_name"], eic, r["from_node"], r["to_node"], kv_of(r["from_node"]), float(r["current_new_A"]), 0.0,
                          float(r["X_new_ohm"]), 0.0, float(r["length_km"]), float(r["capacity_new_MW"])])
            meta.append({"patch_id": eic, "sheet": "Lines", "row": r["target_line_name"], "decision_row": r["row_id"], "project": r["project"],
                         "source": r["value_rule"], "conversion": "R = B = 0", "evidence": evidence})
        elif action.startswith("modify"):
            modify.append([r["sheet"], r["target_line_name"], r["target_eic"], float(r["current_now_A"]), float(r["current_new_A"]),
                           float(r["capacity_now_MW"]), float(r["capacity_new_MW"]), float(r["X_now_ohm"]), float(r["X_new_ohm"]),
                           r["row_id"], r["project"], action])
            meta.append({"patch_id": f"{r['sheet']}:{r['target_eic']}:{r['target_line_name']}", "sheet": r["sheet"], "row": r["target_line_name"],
                         "decision_row": r["row_id"], "project": r["project"], "source": r["value_rule"], "conversion": action, "evidence": evidence})
        elif action.startswith("skip"):
            stations.append(r["row_id"])
        else:
            sys.exit(f"ABORT: {r['row_id']}: unknown action '{action}'")

    out.mkdir(parents=True)
    pd.DataFrame(nodes, columns=NODE_COLS).to_csv(out / "nodes_add.csv", index=False)
    pd.DataFrame(lines, columns=LINE_COLS).to_csv(out / "lines_add.csv", index=False)
    pd.DataFrame(columns=LINE_COLS).to_csv(out / "transformers_add.csv", index=False)
    pd.DataFrame(modify, columns=MODIFY_COLS).to_csv(out / "lines_modify.csv", index=False)
    pd.DataFrame(meta).to_csv(out / "patch_metadata.csv", index=False)
    log = [f"# Patch `{name}` (rule {rule}, base workbook {base})", "",
           f"Built {datetime.date.today()} by `scripts/{Path(__file__).name}` from `{dec_dir}/decision_table.csv`.", "",
           "| decision row | project | sheet | element | what changes |", "|---|---|---|---|---|"]
    log += [f"| {m['decision_row']} | {m['project']} | {m['sheet']} | {m['row']} | {m['conversion']} |" for m in meta]
    log += ["", f"Added: {len(nodes)} nodes, {len(lines)} lines. Modified: {len(modify)} rows. "
                f"New stations recorded but not built (no flow effect without their own injection): {stations}"]
    (out / "CHANGELOG.md").write_text("\n".join(log) + "\n")
    files = sorted(p for p in out.iterdir())
    (out / "manifest.json").write_text(json.dumps({
        "status": "finished", "finished": datetime.datetime.now().isoformat(timespec="seconds"),
        "config": {"script": Path(__file__).name, "base_version": base, "rule": rule, "decision_folder": str(dec_dir),
                   "rows_used": [m["decision_row"] for m in meta], "rows_skipped_as_stations": stations, "eic_prefix": prefix},
        "inputs_sha256": {"decision_table.csv": sha(dec_dir / "decision_table.csv")},
        "outputs_sha256": {p.name: sha(p) for p in files}}, indent=1))
    print(f"written {out}: {len(nodes)} nodes, {len(lines)} lines, {len(modify)} modifications, {len(stations)} stations skipped")


if __name__ == "__main__":
    main()
