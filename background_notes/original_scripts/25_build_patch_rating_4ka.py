#!/usr/bin/env python3
"""
25_build_patch_rating_4ka.py — rating patch for two Dutch 380 kV corridors upgraded to 4 kA (2026-10-23).

Requested by the 2035 dispatch session (nl_merge, plan approved by the user; reasoning in nl_merge/G8_ip2026_ratings_and_bottlenecks_check.md
section 4). Four circuits, current 3,300 -> 4,000 A, capacity sqrt(3) x 400 kV x I = 2,771.281 MW (the workbook's convention: 3,300 A
is 2,286.307 MW), X/R/B unchanged:
    Krimpen aan den IJssel-Geertruidenberg380 W / Z   (49T0000000000274 / 49T0000000000282)
    Maasbracht-Eindhoven380 W / Z                     (49T0000000000290 / 49T000000000030F)
Source: TenneT Investeringsplan 2026 Net op land (IP2026/), p.109 Table 8.5 "Gerealiseerde investeringen RPP project Beter Benutten
Bestaande 380 kV": A-1002589 Geertruidenberg - Krimpen and A-1002586 Eindhoven - Maasbracht "Opwaarderen naar 2 x 2.635 MVA", Gereed;
text on the same page: "verhoogd tot 2 x 2.635 MVA (4 kA) per verbinding". Table 4.1 (p.23 / p.25): A-1002589 verzwaren 2023,
A-1002586 verzwaren 1e 2e circuit 2025. End-station work before 2035: A-1000199 Geertruidenberg 380 kV vervangen primair (Realisatie,
2026; p.71), A-1002495 Maasbracht 380 kV vervangen station (Realisatie, 2030-2031; p.69). The other three corridors of Table 8.5
(Ens-Zwolle, Lelystad-Ens, Diemen-Lelystad) are already 4,000 A / 2,771.281 MW in the workbook.

    ~/.tulipa_pipeline_venv/bin/python scripts/25_build_patch_rating_4ka.py <base workbook version> <patch name>
    e.g. ... v29-vvltr2-2035-tennet-tlb3 ip2026_nl_2035_rating_4ka

Writes inputs/patches/<patch name>/ in the format of scripts/17 (lines_modify.csv, empty *_add.csv with the workbook's columns,
patch_metadata.csv, CHANGELOG.md, manifest.json with base_version and output hashes); aborts if it exists. Reads no validation data.
"""
import datetime, hashlib, json, math, sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ROWS = [("Krimpen aan den IJssel-Geertruidenberg380 W", "49T0000000000274", "A-1002589"), ("Krimpen aan den IJssel-Geertruidenberg380 Z", "49T0000000000282", "A-1002589"),
        ("Maasbracht-Eindhoven380 W", "49T0000000000290", "A-1002586"), ("Maasbracht-Eindhoven380 Z", "49T000000000030F", "A-1002586")]
I_NEW = 4000.0
CAP_NEW = round(math.sqrt(3) * 400.0 * I_NEW / 1000.0, 3)                 # 2,771.281 MW
SOURCE = "TenneT IP2026 Net op land p.109 Table 8.5 (Beter Benutten Bestaande 380 kV): 'Opwaarderen naar 2 x 2.635 MVA', Gereed; p.109 text '(4 kA) per verbinding'"
APPROVAL = "user via the nl_merge 2035 dispatch session, 2026-10-23 ('rating fix in all cases'); reasoning nl_merge/G8_ip2026_ratings_and_bottlenecks_check.md s.4"


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    base, name = sys.argv[1], sys.argv[2]
    wbf = ROOT / "inputs" / "derived" / f"jao_core_{base}" / "jao_core.xlsx"; out = ROOT / "inputs" / "patches" / name
    if out.exists():
        sys.exit(f"ABORT: {out} exists — never overwritten")
    w = pd.read_excel(wbf, sheet_name=None); L = w["Lines"]
    mod, meta = [], []
    for k, (ln, eic, proj) in enumerate(ROWS, 1):
        r = L[(L.Line_name == ln) & (L.EIC_Code == eic)]
        if len(r) != 1:
            sys.exit(f"ABORT: {ln} ({eic}) found {len(r)} times in {wbf}")
        r = r.iloc[0]
        if not (float(r["Currrent_(A)"]) == 3300.0 and abs(float(r.Capacity_MW) - math.sqrt(3) * 400 * 3.3) < 1e-3):
            sys.exit(f"ABORT: {ln}: expected 3,300 A / 2,286.307 MW, found {r['Currrent_(A)']} A / {r.Capacity_MW} MW")
        mod.append({"sheet": "Lines", "Line_name": ln, "EIC_Code": eic, "current_old_A": float(r["Currrent_(A)"]), "current_new_A": I_NEW, "capacity_old_MW": float(r.Capacity_MW),
                    "capacity_new_MW": CAP_NEW, "X_old_ohm": float(r.X), "X_new_ohm": float(r.X), "decision_row": f"R4K-{k:03d}", "project": proj, "action": "modify: current and capacity"})
        meta.append({"patch_id": f"Lines:{eic}:{ln}", "sheet": "Lines", "row": ln, "decision_row": f"R4K-{k:03d}", "project": proj,
                     "source": f"4,000 A: {SOURCE}; capacity sqrt(3) x 400 x I", "conversion": "modify: current and capacity; X, R, B unchanged",
                     "evidence": "IP2026 Table 4.1 (realised): A-1002589 2023, A-1002586 2025; end stations A-1000199 Geertruidenberg (Realisatie 2026), A-1002495 Maasbracht (Realisatie 2030-2031)",
                     "approval": APPROVAL})
    out.mkdir(parents=True)
    pd.DataFrame(mod).to_csv(out / "lines_modify.csv", index=False)
    pd.DataFrame(meta).to_csv(out / "patch_metadata.csv", index=False)
    pd.DataFrame(columns=list(w["Nodes"].columns)).to_csv(out / "nodes_add.csv", index=False)
    pd.DataFrame(columns=list(w["Lines"].columns)).to_csv(out / "lines_add.csv", index=False)
    pd.DataFrame(columns=list(w["Transformers"].columns)).to_csv(out / "transformers_add.csv", index=False)
    (out / "CHANGELOG.md").write_text(f"# {name}\n\nBuilt {datetime.date.today()} by scripts/25_build_patch_rating_4ka.py for jao_core_{base}. Four 380 kV circuits 3,300 -> 4,000 A "
                                      f"({CAP_NEW} MW), X/R/B unchanged: " + "; ".join(f"{a} ({b}, {c})" for a, b, c in ROWS) + f".\nSource: {SOURCE}.\nApproval: {APPROVAL}.\n")
    cfg = {"script": Path(__file__).name, "script_sha256": sha(Path(__file__)), "base_version": base, "patch_name": name, "current_new_A": I_NEW, "capacity_new_MW": CAP_NEW,
           "source": SOURCE, "approval": APPROVAL, "validation_data_read": "none"}
    (out / "manifest.json").write_text(json.dumps({"status": "finished", "started": datetime.datetime.now().isoformat(timespec="seconds"), "finished": datetime.datetime.now().isoformat(timespec="seconds"),
                                                   "config": cfg, "inputs_sha256": {str(wbf.relative_to(ROOT)): sha(wbf)}, "counts": {"lines_modify": len(mod)},
                                                   "outputs_sha256": {p.name: sha(p) for p in sorted(out.iterdir()) if p.name != "manifest.json"}}, indent=1))
    print(pd.DataFrame(mod)[["Line_name", "current_old_A", "current_new_A", "capacity_old_MW", "capacity_new_MW", "X_old_ohm"]].to_string(index=False)); print(f"wrote {out}")


if __name__ == "__main__":
    main()
