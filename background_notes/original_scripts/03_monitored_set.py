#!/usr/bin/env python3
"""
03_monitored_set.py — the monitored set: which lines of the full grid may set a transfer limit in 04 / 05. Rule adopted on
2026-10-16 (docs/20_niederlangen_stub_monitored_set.md): 380 kV lines (both ends at 380 kV) of at least 1 km. Tee stubs,
station jumpers and landing circuits under 1 km stay in the grid and in the outage list but may not limit a transfer (JAO
never monitors them; the 0.33 km Niederlangen stub with a fixed 450 MW used to cap five Dutch pair limits). Transformers
and 220 kV lines are not monitored (user decision of 2026-10-13: "380 kV lines only").

    ~/.tulipa_pipeline_venv/bin/python scripts/03_monitored_set.py <workbook version>      e.g. v29

Reads  inputs/derived/jao_core_<version>/jao_core.xlsx (sheets Lines, Tielines)
Writes runs/<today>-monitored-380kv-ge1km-<version>/ {monitored_eics.csv (column eic), excluded_stubs.csv, README.md, manifest.json}
Aborts if the folder exists. For the nodal network, 03n adds the sub-kilometre rows between representative buses.
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
