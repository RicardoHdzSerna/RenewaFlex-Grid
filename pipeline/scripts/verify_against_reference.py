#!/usr/bin/env python3
"""
verify_against_reference.py — check that a rebuild gives the same networks as the ones the RenewaFLEX runs use.

WHAT IT DOES
  For each network in ../reference_outputs/networks/ (short names, e.g. nodal_main; ../reference_outputs/NETWORK_NAMES.csv gives
  the full name of each), it looks for the folder with the full name that run_all.sh / run_all_hv.sh wrote in inputs/derived/
  and compares:
    nodes.csv           identical rows
    flow.csv            same branches; largest difference in `capacity` (MW)
    flow-milestone.csv  same branches; largest difference in `reactance` (p.u.)
  Prints one line per network and "ALL MATCH" when every capacity is within 0.01 MW and every reactance within 1e-9 p.u.
  (the numbers are written with 6 decimals, so a rebuild on the same software gives differences of 0).
  The two hv_* networks are only checked when run_all_hv.sh has been run.

USAGE
  python scripts/verify_against_reference.py [<rebuilt networks folder>]      default: inputs/derived
"""
import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
REF = ROOT.parent / "reference_outputs" / "networks"
KEY = ["from_asset", "to_asset"]


def main():
    built_root = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "inputs" / "derived"
    full = dict(pd.read_csv(REF.parent / "NETWORK_NAMES.csv")[["short_name", "full_name"]].values)
    ok_all = True
    for ref in sorted(p for p in REF.iterdir() if p.is_dir()):
        short = ref.name; new = built_root / full[short]
        if not new.exists():
            if short.startswith("hv_"):
                print(f"skipped  {short}: not built (run run_all_hv.sh)"); continue
            print(f"MISSING  {short}"); ok_all = False; continue
        nodes_same = pd.read_csv(ref / "nodes.csv").equals(pd.read_csv(new / "nodes.csv"))
        f = pd.read_csv(ref / "flow.csv").merge(pd.read_csv(new / "flow.csv"), on=KEY, how="outer", suffixes=("_ref", "_new"), indicator=True)
        m = pd.read_csv(ref / "flow-milestone.csv").merge(pd.read_csv(new / "flow-milestone.csv"), on=KEY, how="outer", suffixes=("_ref", "_new"), indicator=True)
        same_branches = (f["_merge"] == "both").all() and (m["_merge"] == "both").all()
        dcap = (f["capacity_ref"] - f["capacity_new"]).abs().max()
        dx = (m["reactance_ref"] - m["reactance_new"]).abs().max()
        ok = nodes_same and same_branches and dcap <= 0.01 and dx <= 1e-9
        ok_all &= ok
        print(f"{'OK      ' if ok else 'DIFFERS '} {short}: {len(f)} branches, nodes {'same' if nodes_same else 'DIFFER'}, "
              f"branches {'same' if same_branches else 'DIFFER'}, max |capacity diff| {dcap:.6f} MW, max |reactance diff| {dx:.2e} p.u.")
    print("ALL MATCH" if ok_all else "NOT ALL MATCH")
    sys.exit(0 if ok_all else 1)


if __name__ == "__main__":
    main()
