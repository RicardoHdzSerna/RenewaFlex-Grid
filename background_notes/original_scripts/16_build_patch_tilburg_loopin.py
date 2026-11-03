#!/usr/bin/env python3
"""
16_build_patch_tilburg_loopin.py — a workbook patch that loops the Geertruidenberg–Eindhoven 380 kV line into the new
Tilburg 380 kV station (2026-10-19). User: "ok cool then lets add it" (after the sources below).

Why: the 2035 grids (patches ip2026_nl_2035_*) add TILBURG_380 only as the end of Rilland–Tilburg (IP2026 A-1002678), a radial
spur. TenneT's station Tilburg (Spinder) is looped into the existing 380 kV line:
  TenneT, "Aanmeldingsnotitie m.e.r. hoogspanningsstation Tilburg" (project 002.678.21, 2 Feb 2022; ruimtelijkeplannen.nl,
  plan NL.IMRO.0000.EZKip20Til380-1000, bijlage tb13; copy in this patch folder):
  p. 11 "De inlussing van de bestaande 380kV-verbinding in dit 380kV station aan de west- en oostzijde" (new masts 1205, 59AN,
  60N, 61N); p. 12 "2 van de bestaande 3 circuits worden ingelust ... 1 circuit behouden blijft"; p. 14 once Zuid-West 380 kV
  Oost is ready "kan ook het derde circuit op het hoogspanningsstation worden aangesloten". The existing line is
  Geertruidenberg–Eindhoven (only 380 kV line at the site; RVO/TenneT ZW380 Oost documents; I-ELGAS "Eindhoven-(Tilburg)-
  Geertruidenberg"). Commissioning of the station: 2027 (TenneT project page).

What: for each looped circuit, REMOVE the Geertruidenberg-Eindhoven380 <c> row and ADD Geertruidenberg-Tilburg380 <c> and
Tilburg-Eindhoven380 <c>. Length and X split in proportion to the straight-line distances between the bus coordinates of the
base workbook (great circle); current and capacity unchanged (same conductor); R = B = 0 (workbook rule). The few hundred metres
of new loop-in spans are neglected. EIC codes PATCH-NL35-TLB-nnnn (assumed identities: after the loop-in each piece is its own
circuit for the outage list and the monitored set). --circuits=3 (2035 with Rilland–Tilburg in service: all three looped) or
--circuits=2 (2027–2030 state: W and Z looped, G direct).

    ~/.tulipa_pipeline_venv/bin/python scripts/16_build_patch_tilburg_loopin.py <base version with TILBURG_380> --circuits=<2|3>
    e.g. ... 16_build_patch_tilburg_loopin.py v29-2035-tennet --circuits=3
Writes inputs/patches/ip2026_nl_2035_tilburg_loopin_<n>c/: nodes_add.csv, transformers_add.csv (empty), lines_add.csv,
lines_remove.csv, patch_metadata.csv, CHANGELOG.md, checks.json, manifest.json (+ the source PDF if given with --source=).
Applied by scripts/17_apply_patches_modify_remove.py. Aborts if the folder exists.
"""
import datetime, hashlib, json, math, shutil, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
args = [a for a in sys.argv[1:] if not a.startswith("--")]
opt = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
n_c = int(opt.get("circuits", "0"))
if len(args) != 1 or n_c not in (2, 3):
    sys.exit(__doc__)
BASE_V = args[0]; WB = ROOT / "inputs" / "derived" / f"jao_core_{BASE_V}" / "jao_core.xlsx"
OUT = ROOT / "inputs" / "patches" / f"ip2026_nl_2035_tilburg_loopin_{n_c}c"
if OUT.exists():
    sys.exit(f"ABORT: {OUT} exists — never overwritten")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
W = pd.read_excel(WB, sheet_name=None); L, N = W["Lines"], W["Nodes"]
GER, TIL, EHV = "GEERTRUIDENBERG_380", "TILBURG_380", "EINDHOVEN_380"
for b in (GER, TIL, EHV):
    if b not in set(N.Bus):
        sys.exit(f"ABORT: bus {b} not in the base workbook")
ge = L[(L.From_node == GER) & (L.To_node == EHV)].sort_values("Line_name")
if len(ge) != 3 or set(ge.Line_name.str[-1]) != {"G", "W", "Z"}:
    sys.exit(f"ABORT: expected circuits G, W, Z of Geertruidenberg-Eindhoven380, found {list(ge.Line_name)}")
til = L[(L.From_node == TIL) | (L.To_node == TIL)]
if set(til.Line_name) != {"Rilland-Tilburg380 W", "Rilland-Tilburg380 Z"}:
    sys.exit(f"ABORT: TILBURG_380 should have exactly the two Rilland rows, has {list(til.Line_name)}")
xy = {r.Bus: (r.Latitude, r.Longitude) for r in N.itertuples()}


def gc_km(a, b):
    (la1, lo1), (la2, lo2) = map(lambda p: (math.radians(p[0]), math.radians(p[1])), (xy[a], xy[b]))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(h))


d1, d2, d0 = gc_km(GER, TIL), gc_km(TIL, EHV), gc_km(GER, EHV)
f = d1 / (d1 + d2)
loop = ["W", "Z", "G"][:n_c] if n_c == 3 else ["W", "Z"]
remove, add, meta = [], [], []
k = 0
SRC = ("TenneT 2022 Aanmeldingsnotitie m.e.r. hoogspanningsstation Tilburg (002.678.21) p.11-14; TenneT project page "
       "station Tilburg (commissioning 2027); IP2026 A-1002678 Rilland-Tilburg 2031-2034")
CONV = (f"split of the original row by straight-line distance of the bus coordinates: GER-TIL {d1:.2f} km, TIL-EHV {d2:.2f} km "
        f"(direct {d0:.2f} km), fraction {f:.4f}; Length and X x fraction; current and capacity unchanged; R = B = 0")
APPROVAL = 'user 2026-10-19: "ok cool then lets add it"'
for _, r in ge.iterrows():
    c = r.Line_name[-1]
    if c not in loop:
        continue
    remove.append(r.to_dict())
    meta.append(dict(patch_id=f"Lines:{r.EIC_Code}:{r.Line_name}", sheet="Lines", row=r.Line_name, decision_row="TLB-loopin",
                     project="station Tilburg 380 kV (002.678.21)", source=SRC, conversion="remove: cut at Tilburg",
                     evidence=f"circuit {c} looped in", approval=APPROVAL))
    for frm, to, frac, nm in ((GER, TIL, f, f"Geertruidenberg-Tilburg380 {c}"), (TIL, EHV, 1 - f, f"Tilburg-Eindhoven380 {c}")):
        k += 1
        eic = f"PATCH-NL35-TLB-{k:04d}"
        add.append({"Line_name": nm, "EIC_Code": eic, "From_node": frm, "To_node": to, "Voltage_level": 380,
                    "Currrent_(A)": float(r["Currrent_(A)"]), "R": 0, "X": round(float(r.X) * frac, 4), "B": 0,
                    "Length_km": round(float(r.Length_km) * frac, 3), "Capacity_MW": float(r.Capacity_MW)})
        meta.append(dict(patch_id=eic, sheet="Lines", row=nm, decision_row="TLB-loopin", project="station Tilburg 380 kV (002.678.21)",
                         source=SRC, conversion=CONV, evidence=f"piece of {r.Line_name} ({r.EIC_Code}); EIC assumed", approval=APPROVAL))
cols = list(L.columns)
OUT.mkdir(parents=True)
CONFIG = {"script": Path(__file__).name, "script_sha256": sha(__file__), "base_version": BASE_V,
          "patch_name": OUT.name, "circuits_looped": loop, "split_fraction_GER_TIL": f, "validation_data_read": "none"}
(OUT / "manifest.json").write_text(json.dumps({"status": "started", "started": datetime.datetime.now().isoformat(timespec="seconds"),
                                               "config": CONFIG, "inputs_sha256": {f"inputs/derived/jao_core_{BASE_V}/jao_core.xlsx": sha(WB)}}, indent=1))
pd.DataFrame(columns=list(N.columns)).to_csv(OUT / "nodes_add.csv", index=False)
pd.DataFrame(columns=cols).to_csv(OUT / "transformers_add.csv", index=False)
pd.DataFrame(add, columns=cols).to_csv(OUT / "lines_add.csv", index=False)
pd.DataFrame(remove, columns=cols).to_csv(OUT / "lines_remove.csv", index=False)
pd.DataFrame(meta).to_csv(OUT / "patch_metadata.csv", index=False)
chk = {"GER_TIL_km": d1, "TIL_EHV_km": d2, "GER_EHV_direct_km": d0, "detour_pct": 100 * ((d1 + d2) / d0 - 1), "fraction": f,
       "x_conserved": {r["Line_name"]: abs(sum(a["X"] for a in add if a["Line_name"].endswith(r["Line_name"][-1])) - r["X"]) < 1e-3 for r in remove},
       "removed": [r["Line_name"] for r in remove], "added": [a["Line_name"] for a in add]}
if not all(chk["x_conserved"].values()):
    sys.exit("ABORT: X not conserved by the split")
(OUT / "checks.json").write_text(json.dumps(chk, indent=1))
lines = [f"# CHANGELOG — patch `{OUT.name}` (base jao_core_{BASE_V})", "",
         f"Built {datetime.date.today().isoformat()} by `scripts/{Path(__file__).name}`; {APPROVAL}.", "",
         f"Source: {SRC}.", "", f"Split rule: {CONV}.", "", "| action | row | EIC | km | X (ohm) | A | MW |", "|---|---|---|---|---|---|---|"]
lines += [f"| remove | {r['Line_name']} | {r['EIC_Code']} | {r['Length_km']} | {r['X']} | {r['Currrent_(A)']} | {r['Capacity_MW']} |" for r in remove]
lines += [f"| add | {a['Line_name']} | {a['EIC_Code']} | {a['Length_km']} | {a['X']} | {a['Currrent_(A)']} | {a['Capacity_MW']} |" for a in add]
(OUT / "CHANGELOG.md").write_text("\n".join(lines) + "\n")
if "source" in opt:
    shutil.copyfile(opt["source"], OUT / "source_TenneT_2022_aanmeldingsnotitie_station_Tilburg_tb13.pdf")
outs = {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.name != "manifest.json"}
(OUT / "manifest.json").write_text(json.dumps({"status": "finished", "started": json.loads((OUT / "manifest.json").read_text())["started"],
                                               "finished": datetime.datetime.now().isoformat(timespec="seconds"), "config": CONFIG,
                                               "inputs_sha256": {f"inputs/derived/jao_core_{BASE_V}/jao_core.xlsx": sha(WB)},
                                               "counts": {"lines_remove": len(remove), "lines_add": len(add)}, "outputs_sha256": outs}, indent=1))
print(f"{OUT.name}: remove {len(remove)}, add {len(add)}; fraction {f:.4f} (GER-TIL {d1:.2f} km, TIL-EHV {d2:.2f} km, detour {chk['detour_pct']:.2f} %)")
