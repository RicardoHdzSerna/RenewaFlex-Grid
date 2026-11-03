#!/usr/bin/env python3
"""
A1_build_patch_vierverlaten_transformer.py — patch that adds the Vierverlaten 380/220 kV transformer(s), with ASSUMED values.

STEP  A1 in run_all.sh (HANDOVER.md section 2.3)

WHAT IT DOES
  Writes a patch with 1 or 2 transformer rows between VIERVERLATEN_380 and VIERVERLATEN_220.
  Each unit gets the values of a typical Dutch 380/220 kV unit of the base workbook (the 8 units at Eemshaven, Ens, Meeden):
    X        = their median reactance (ohm, referred to 380 kV)
    current  = their most common rating (A); Capacity_MW = sqrt(3) x 400 kV x current / 1000
    R = B = 0, Length_km = 0, Voltage_level 380; EIC codes ASSUMED-NL-TR-0001, -0002 (not JAO codes).
  The rating plays no role in the limits (transformers are never monitored); only the reactance matters.

WHY
  The Friesland-Overijssel 220 kV ring (Ens - Oudehaske - Louwsmeer - Bergum - Vierverlaten - Zeyerveen - Hessenweg - Ens) touches
  the 380 kV grid only at Ens in every grid file we have (JAO static and flow-based, GridAware), so no power can flow through it.
  TenneT's IP2026 shows that the coupling exists (bottleneck 1578 "Vierverlaten 380/220 kV-transformatoren", asset "VVL TR426")
  but gives no electrical values. Decision 19 Oct 2026: add it with typical values; 2 units, because IP2026 uses the plural.

READS   inputs/derived/jao_core_<base>/jao_core.xlsx
WRITES  inputs/patches/nl_vierverlaten_tr_assumed_<n>u/  nodes_add.csv and lines_add.csv (empty), transformers_add.csv,
        patch_metadata.csv, CHANGELOG.md, checks.json, manifest.json. Aborts if the folder exists.

USAGE   python scripts/A1_build_patch_vierverlaten_transformer.py <base version> --units=<1|2>
        e.g. python scripts/A1_build_patch_vierverlaten_transformer.py v29 --units=2
        Apply it with A5_apply_patches.py.

HISTORY Same code as core_grid_dcopf/scripts/14_build_patch_vierverlaten_tr.py, which built the patch in use (19 Oct 2026);
        only this header was rewritten for the handover.
"""
import datetime, hashlib, json, math, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
args = [a for a in sys.argv[1:] if not a.startswith("--")]
units = int(next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--units=")), "0"))
if len(args) != 1 or units not in (1, 2):
    sys.exit(__doc__)
BASE_V = args[0]; WB = ROOT / "inputs" / "derived" / f"jao_core_{BASE_V}" / "jao_core.xlsx"
OUT = ROOT / "inputs" / "patches" / f"nl_vierverlaten_tr_assumed_{units}u"
if OUT.exists():
    sys.exit(f"ABORT: {OUT} exists — never overwritten")
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
W = pd.read_excel(WB, sheet_name=None); T = W["Transformers"]; N = W["Nodes"]
ref = T[T.From_node.isin(["EEMSHAVEN_380", "ENS_380", "MEEDEN_380"]) & T.To_node.str.endswith("_220")]
if len(ref) != 8:
    sys.exit(f"ABORT: expected the 8 Dutch 380/220 kV units of the JAO file, found {len(ref)}")
for b in ("VIERVERLATEN_380", "VIERVERLATEN_220"):
    if b not in set(N.Bus):
        sys.exit(f"ABORT: bus {b} not in the base workbook")
if ((T.From_node.isin(["VIERVERLATEN_380", "VIERVERLATEN_220"])) | (T.To_node.isin(["VIERVERLATEN_380", "VIERVERLATEN_220"]))).any():
    sys.exit("ABORT: the base workbook already has a transformer at Vierverlaten")
X = float(ref.X.median()); I = float(ref["Currrent_(A)"].mode().iloc[0]); CAP = round(math.sqrt(3) * 400 * I / 1000, 3)
assert abs(CAP - float(ref[ref["Currrent_(A)"] == I].Capacity_MW.iloc[0])) < 1e-3, "rating rule differs from the reference rows"
names = ["TR Vierverlaten 380kV TR 426-assumed", "TR Vierverlaten 380kV TR second-assumed"][:units]
rows = [{"Line_name": n, "EIC_Code": f"ASSUMED-NL-TR-{k + 1:04d}", "From_node": "VIERVERLATEN_380", "To_node": "VIERVERLATEN_220", "Voltage_level": 380,
         "Currrent_(A)": I, "R": 0, "X": round(X, 3), "B": 0, "Length_km": 0, "Capacity_MW": CAP} for k, n in enumerate(names)]
OUT.mkdir(parents=True)
cols = list(T.columns)
pd.DataFrame(rows, columns=cols).to_csv(OUT / "transformers_add.csv", index=False)
pd.DataFrame(columns=list(W["Lines"].columns)).to_csv(OUT / "lines_add.csv", index=False)
pd.DataFrame(columns=list(N.columns)).to_csv(OUT / "nodes_add.csv", index=False)
src = (f"ASSUMED VALUES. Existence: TenneT IP2026 bottleneck 1578 'Vierverlaten 380/220 kV-transformatoren' (annexes 4 and 5) and asset register "
       f"'VVL TR426' (annex 6). X = median of the 8 Dutch 380/220 kV units of the JAO file ({', '.join(f'{x:.3f}' for x in sorted(ref.X))} ohm); "
       f"current = most common rating among them ({I:.0f} A, {int((ref['Currrent_(A)'] == I).sum())} of 8); units = {units} "
       + ("(IP2026 names the bottleneck in the plural)" if units == 2 else "(sensitivity)"))
pd.DataFrame([{"patch_id": r["EIC_Code"], "sheet": "Transformers", "row": r["Line_name"], "source": src, "X_ohm": r["X"], "current_A": I, "capacity_MW": CAP,
               "decision": "user, 2026-10-19: \"create the transformer for that other part of the ring ... representative of the grid\"", "date": datetime.date.today().isoformat()} for r in rows]).to_csv(OUT / "patch_metadata.csv", index=False)
checks = {"reference_units": ref[["Line_name", "X", "Currrent_(A)", "Capacity_MW"]].to_dict("records"), "X_median_ohm": X, "current_mode_A": I, "capacity_MW": CAP,
          "X_pu_per_unit_on_380kV_100MVA": X / (380 ** 2 / 100), "units": units, "X_pu_parallel": X / units / (380 ** 2 / 100)}
(OUT / "checks.json").write_text(json.dumps(checks, indent=1))
(OUT / "CHANGELOG.md").write_text(f"# {OUT.name}\n\nAdds {units} Vierverlaten 380/220 kV transformer unit(s) with ASSUMED values (typical Dutch JAO unit: X {X:.3f} ohm, "
                                  f"{I:.0f} A, {CAP} MW each). The coupling exists (IP2026 bottleneck 1578, asset VVL TR426); its values are not in any file we have. "
                                  f"Base {BASE_V}. Built by scripts/14_build_patch_vierverlaten_tr.py on {datetime.date.today().isoformat()}.\n")
outs = {p.name: sha(p) for p in sorted(OUT.iterdir())}
(OUT / "manifest.json").write_text(json.dumps({"status": "finished", "started": datetime.datetime.now().isoformat(timespec="seconds"),
    "config": {"script": Path(__file__).name, "script_sha256": sha(__file__), "base_version": BASE_V, "patch_name": OUT.name, "units": units, "values": "assumed (typical Dutch JAO 380/220 kV unit)",
               "validation_data_read": "none"}, "inputs_sha256": {str(WB.relative_to(ROOT)): sha(WB)}, "finished": datetime.datetime.now().isoformat(timespec="seconds"), "outputs_sha256": outs}, indent=1))
print(f"{OUT.name}: {units} unit(s), X {X:.3f} ohm each ({checks['X_pu_parallel']:.4f} p.u. in parallel), {I:.0f} A, {CAP} MW each")
