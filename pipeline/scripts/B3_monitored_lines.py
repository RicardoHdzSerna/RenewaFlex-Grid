#!/usr/bin/env python3
"""
B3_monitored_lines.py — which lines of the full grid may set a limit: 380 kV lines of at least 1 km.

STEP  B3 in run_all.sh (HANDOVER.md section 3.3)

WHAT IT DOES
  Lists the EIC codes of every row of the Lines and Tielines sheets with both ends at 380 kV and a length of at least 1 km.
  Shorter rows (tee stubs 'Y-...', station jumpers, landing circuits) stay in the grid and can still fail in the N-1 check, but
  may not limit a transfer. Transformers and 220 kV lines are not in this list (B3_monitored_lines_nodal.py adds Dutch 220 kV).

WHY
  JAO never monitors such stubs, and the 0.33 km Niederlangen tee (fixed 450 MW) used to cap five Dutch limits
  (background_notes/20_niederlangen_stub_monitored_set.md). TenneT NL monitors only 380 kV elements.

READS   inputs/derived/jao_core_<version>/jao_core.xlsx
WRITES  runs/<today>-monitored-380kv-ge1km-<version>/  monitored_eics.csv (column eic), excluded_stubs.csv, README.md,
        manifest.json. Aborts if it exists.

USAGE   python scripts/B3_monitored_lines.py <workbook version>

HISTORY Same code as core_grid_dcopf/scripts/03_monitored_set.py (16 Oct 2026); only this header was rewritten.
"""
import datetime, hashlib, json, sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
args = [a for a in sys.argv[1:] if not a.startswith("--")]
if len(args) != 1:
    sys.exit(__doc__)
V = args[0]; WB = ROOT / "inputs" / "derived" / f"jao_core_{V}" / "jao_core.xlsx"
OUT = ROOT / "runs" / f"{datetime.date.today().isoformat()}-monitored-380kv-ge1km-{V}"
MIN_KM, KV = 1.0, 380
if not WB.exists():
    sys.exit(f"ABORT: workbook not found: {WB}")
if OUT.exists():
    sys.exit(f"ABORT: {OUT} exists — never overwritten")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


W = pd.read_excel(WB, sheet_name=["Lines", "Tielines"])
rows = pd.concat([W["Lines"].assign(sheet="Lines"), W["Tielines"].assign(sheet="Tielines")], ignore_index=True)
both380 = rows.From_node.astype(str).str.endswith(f"_{KV}") & rows.To_node.astype(str).str.endswith(f"_{KV}")
r380 = rows[both380].copy(); r380["Length_km"] = pd.to_numeric(r380.Length_km, errors="coerce")
keep = r380[r380.Length_km >= MIN_KM]; excl = r380[~(r380.Length_km >= MIN_KM)]
eics = sorted(set(keep.EIC_Code.dropna().astype(str)))
OUT.mkdir(parents=False)
pd.DataFrame({"eic": eics}).to_csv(OUT / "monitored_eics.csv", index=False)
excl[["sheet", "Line_name", "EIC_Code", "From_node", "To_node", "Currrent_(A)", "Length_km", "Capacity_MW"]].to_csv(OUT / "excluded_stubs.csv", index=False)
(OUT / "README.md").write_text(f"# Monitored set: 380 kV lines of at least 1 km ({V})\n\nRule: rows of the Lines and Tielines sheets with both ends at {KV} kV and Length_km >= {MIN_KM:g} may set an N-1 limit "
                               f"({len(keep)} rows, {len(eics)} EICs); the {len(excl)} rows under {MIN_KM:g} km (tee stubs 'Y-…', station jumpers, landing circuits) stay in the grid and in the "
                               f"outage list but are not monitored. Transformers and 220 kV lines are not monitored. Reason: docs/20_niederlangen_stub_monitored_set.md.\n")
(OUT / "manifest.json").write_text(json.dumps({"status": "finished", "written": datetime.datetime.now().isoformat(timespec="seconds"), "script": Path(__file__).name, "script_sha256": sha(Path(__file__)),
                                               "workbook": str(WB.relative_to(ROOT)), "workbook_sha256": sha(WB), "rule": f"{KV} kV both ends and Length_km >= {MIN_KM:g} km, sheets Lines + Tielines",
                                               "kept_rows": int(len(keep)), "kept_eics": len(eics), "excluded_rows": int(len(excl)),
                                               "outputs_sha256": {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.name != "manifest.json"}}, indent=1))
print(f"{OUT.name}: {len(keep)} rows kept, {len(eics)} EICs; {len(excl)} rows excluded")
