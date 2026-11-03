#!/usr/bin/env python3
# core_grid_dcopf (2026-10-19): 17_apply_patches_modify_remove.py — COPY of scripts/13_apply_patches.py (not edited) with three
# additions, everything else as 13 (and as the archived 100):
#   1. a patch may carry lines_modify.csv (format of the ip2026_nl_2035_* patches, applied there by the archived 113: sheet, Line_name,
#      EIC_Code, current/capacity/X old and new) and lines_remove.csv (full rows of the Lines sheet). Per patch the order is
#      removals, modifications, additions. A modified or removed row must match the workbook exactly (old values / every column),
#      otherwise abort.
#   2. rebase: a patch built for another workbook version may be applied when every row it removes or modifies is identical in
#      its base workbook and in the intermediate workbook (additions are checked for collisions as in 13). Recorded in the manifest.
#      Needed to put the 2035 patches (built for v29) on the base v29-vvltr2 (HANDOVER §6.3).
#   3. --out-dir=<dir> writes the new version there instead of inputs/derived (reproduction tests only).
#   Read-back: every sheet of the written workbook equals the planned in-memory workbook.
# The header of 13 follows.
# core_grid_dcopf (2026-10-19): copy of archive/dcopf/scripts/100_apply_workbook_patches.py; no edits (paths are relative to this folder:
# inputs/derived/jao_core_<v>, patches under inputs/patches/); the original header follows.
"""
100_apply_workbook_patches.py — COPY of 97_apply_workbook_patch.py (not edited), generalised to a SEQUENCE of patches and
with the station map appended as text. Review finding F-04 (reviews/jao2026_nl_patch, 2026-10-16): 97 read
substation_map.csv with pandas and wrote it back, which re-serialised 1,592 untouched lines (ints -> floats). Here the
source file's bytes are kept and new rows are appended with the file's own line ending; the other copied files are not
re-serialised either. Everything else as 97: additions only, never an existing row changed, idempotent, read back and
compared, manifest first.

    ~/.tulipa_pipeline_venv/bin/python -W ignore scripts/100_apply_workbook_patches.py <source version> <new version> patches/<p1> [patches/<p2> ...]
    e.g. ... 100_apply_workbook_patches.py v27 v29 patches/jao2026_nl patches/jao2026_nl_2

Patches are applied in the given order. Each patch records the version it was built for (manifest config.base_version):
the first must equal the source version; a later one must equal a version whose workbook is identical, sheet by sheet,
to the intermediate result at that point (e.g. jao2026_nl_2 was built for v28 = v27 + jao2026_nl; applying both to v27
reproduces v28 before the second patch, and that is checked). A patch row already present with identical values is
skipped; one that collides with a different existing row aborts. If nothing is left to add, nothing is written.
Writes inputs/derived/jao_core_<new>/ {manifest.json (first), jao_core.xlsx, build_report.md (appended), row_decisions.csv
(byte copy), substation_map.csv (byte copy + appended rows), corrections.csv, patch_applied.csv, sha256.txt}.
"""
import csv, datetime, hashlib, io, json, shutil, sys
from pathlib import Path

import openpyxl
import pandas as pd

DCOPF = Path(__file__).resolve().parents[1]
SHEETS = {"Nodes": "nodes_add.csv", "Lines": "lines_add.csv", "Transformers": "transformers_add.csv"}
FILES = ("jao_core.xlsx", "build_report.md", "row_decisions.csv", "substation_map.csv")


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def same(a, b):
    if str(a).strip() == str(b).strip():          # also two empty cells ('nan' == 'nan'), which float comparison would call different
        return True
    try:
        return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(b)))
    except (TypeError, ValueError):
        return False


def load_patch(pdir: Path):
    mj = json.loads((pdir / "manifest.json").read_text())
    if mj.get("status") != "finished":
        sys.exit(f"ABORT: patch {pdir} did not finish")
    for name, h in mj["outputs_sha256"].items():
        if sha(pdir / name) != h:
            sys.exit(f"ABORT: patch file {name} changed since the patch was built")
    ops = {k: (pd.read_csv(pdir / f"lines_{k}.csv", keep_default_na=False) if (pdir / f"lines_{k}.csv").exists() else None) for k in ("modify", "remove")}
    return mj, {s: pd.read_csv(pdir / f, keep_default_na=False) for s, f in SHEETS.items()}, pd.read_csv(pdir / "patch_metadata.csv", keep_default_na=False), ops


def locate(df, sheet, name, eic):
    idx = df.index[(df.Line_name.astype(str) == str(name)) & (df.EIC_Code.astype(str) == str(eic))]
    if len(idx) != 1:
        sys.exit(f"ABORT: {sheet} row {name} ({eic}) found {len(idx)} times")
    return idx[0]


def apply_ops(wb, ops):
    """Removals then modifications on the in-memory workbook; returns the list of touched rows (sheet, name, eic, old row)."""
    touched = []
    rem = ops.get("remove")
    if rem is not None and len(rem):
        for r in rem.to_dict("records"):
            i = locate(wb["Lines"], "Lines", r["Line_name"], r["EIC_Code"])
            row = wb["Lines"].loc[i].to_dict()
            if not all(same(r[c], row[c]) for c in r):
                sys.exit(f"ABORT: remove: {r['Line_name']} differs from the workbook row")
            touched.append(("Lines", r["Line_name"], r["EIC_Code"], row, "remove"))
            wb["Lines"] = wb["Lines"].drop(index=i).reset_index(drop=True)
    mod = ops.get("modify")
    if mod is not None and len(mod):
        for r in mod.to_dict("records"):
            s = r["sheet"]; i = locate(wb[s], s, r["Line_name"], r["EIC_Code"]); row = wb[s].loc[i].to_dict()
            if not (same(row["Currrent_(A)"], r["current_old_A"]) and same(row["Capacity_MW"], r["capacity_old_MW"]) and same(row["X"], r["X_old_ohm"])):
                sys.exit(f"ABORT: modify: old values of {r['Line_name']} do not match the workbook")
            touched.append((s, r["Line_name"], r["EIC_Code"], row, "modify"))
            wb[s].loc[i, ["Currrent_(A)", "Capacity_MW", "X"]] = [float(r["current_new_A"]), float(r["capacity_new_MW"]), float(r["X_new_ohm"])]
    return touched


def plan(wb: dict, patch: dict):
    """Rows to add per sheet and rows skipped (already present), against the sheets `wb`. Aborts on any collision."""
    for s, df in patch.items():
        if list(df.columns) != list(wb[s].columns):
            sys.exit(f"ABORT: {SHEETS[s]} columns {list(df.columns)} differ from the workbook's {list(wb[s].columns)}")
    add, skip = {s: [] for s in SHEETS}, []
    buses = dict(zip(wb["Nodes"].Bus, wb["Nodes"].to_dict("records")))
    for r in patch["Nodes"].to_dict("records"):
        if r["Bus"] in buses:
            if all(same(r[c], buses[r["Bus"]][c]) for c in r):
                skip.append(("Nodes", r["Bus"], "already present, identical")); continue
            sys.exit(f"ABORT: bus {r['Bus']} exists with different values")
        if not str(r["Bus"]).endswith(f"_{int(r['baseKV'])}"):
            sys.exit(f"ABORT: bus {r['Bus']} does not end in _{int(r['baseKV'])}")
        add["Nodes"].append(r)
    known = set(buses) | {r["Bus"] for r in add["Nodes"]}
    existing = pd.concat([wb[s].assign(sheet=s) for s in ("Lines", "Tielines", "Transformers")], ignore_index=True)
    by_eic = {str(e): r for e, r in zip(existing.EIC_Code, existing.to_dict("records"))}
    by_pair = {(frozenset((f, t)), str(n).rsplit(" ", 1)[-1]): r for f, t, n, r in zip(existing.From_node, existing.To_node, existing.Line_name, existing.to_dict("records"))}
    cols = list(wb["Lines"].columns)
    for s in ("Lines", "Transformers"):
        for r in patch[s].to_dict("records"):
            key = (frozenset((r["From_node"], r["To_node"])), str(r["Line_name"]).rsplit(" ", 1)[-1])
            hit = by_eic.get(str(r["EIC_Code"])) or by_pair.get(key)
            if hit is not None:
                if all(same(r[c], hit[c]) for c in cols):
                    skip.append((s, r["Line_name"], "already present, identical")); continue
                sys.exit(f"ABORT: {r['Line_name']} collides with existing row {hit['Line_name']} ({hit['EIC_Code']}) with different values")
            if r["From_node"] == r["To_node"] or not {r["From_node"], r["To_node"]} <= known:
                sys.exit(f"ABORT: {r['Line_name']}: self-loop or unknown bus")
            if not (float(r["X"]) > 0 and float(r["Capacity_MW"]) > 0 and float(r["Currrent_(A)"]) > 0):
                sys.exit(f"ABORT: {r['Line_name']}: X, current or rating not positive")
            add[s].append(r)
    for r in add["Nodes"]:
        if not any(r["Bus"] in (b["From_node"], b["To_node"]) for s in ("Lines", "Transformers") for b in add[s]):
            sys.exit(f"ABORT: new bus {r['Bus']} gets no branch")
    return add, skip


def frames_equal(a: dict, b: dict):
    return set(a) == set(b) and all(a[s].shape == b[s].shape and all(same(x, y) for x, y in zip(a[s].astype(str).to_numpy().ravel(), b[s].astype(str).to_numpy().ravel())) for s in a)


def py(v):
    return v.item() if hasattr(v, "item") else v


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) < 3:
        sys.exit(__doc__)
    src_v, new_v = args[0], args[1]; pdirs = [Path(a).resolve() for a in args[2:]]
    SRC = DCOPF / "inputs" / "derived" / f"jao_core_{src_v}"; OUT = DCOPF / "inputs" / "derived" / f"jao_core_{new_v}"
    patches = [load_patch(p) for p in pdirs]
    # ---- plan every patch in sequence on in-memory frames (nothing written yet)
    wb = pd.read_excel(SRC / "jao_core.xlsx", sheet_name=None); plans = []; cur_label = src_v
    rebased = []
    for pdir, (pmj, patch, meta, ops) in zip(pdirs, patches):
        base = pmj["config"].get("base_version")
        pre = {s: d.copy() for s, d in wb.items()}
        touched = apply_ops(wb, ops)
        add, skip = plan(wb, patch)
        if base != cur_label and (any(add.values()) or touched):
            ref = DCOPF / "inputs" / "derived" / f"jao_core_{base}" / "jao_core.xlsx"
            if not ref.exists():
                sys.exit(f"ABORT: patch {pdir.name} base jao_core_{base} not found")
            refwb = pd.read_excel(ref, sheet_name=None)
            if frames_equal({s: pre[s] for s in SHEETS}, {s: refwb[s] for s in SHEETS}):
                cur_label = base
            else:                                               # rebase: every touched row identical in the patch's base and here
                for s, name, eic, row, kind in touched:
                    j = locate(refwb[s], s, name, eic)
                    if not all(same(row[c], refwb[s].loc[j, c]) for c in row):
                        sys.exit(f"ABORT: rebase of {pdir.name}: {s} row {name} differs between jao_core_{base} and the intermediate workbook")
                rebased.append({"patch": pdir.name, "built_for": base, "applied_on": cur_label, "touched_rows_checked": len(touched)})
        plans.append((pdir, pmj, meta, add, skip, touched))
        for s in SHEETS:
            if add[s]:
                wb[s] = pd.concat([wb[s], pd.DataFrame(add[s], columns=list(wb[s].columns))], ignore_index=True)
        cur_label = f"{cur_label}+{pdir.name}"
    n_add = sum(len(v) for _, _, _, add, _, _ in plans for v in add.values()) + sum(len(t) for *_, t in plans)
    if n_add == 0:
        print(f"nothing to apply: all patch rows are already in jao_core_{src_v}; nothing written"); return
    od = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--out-dir=")), None)
    if od:
        OUT = Path(od).resolve() / f"jao_core_{new_v}"
    if OUT.exists():
        sys.exit(f"ABORT: {OUT} exists — never overwritten")
    OUT.mkdir(parents=False)
    CONFIG = {"script": Path(__file__).name, "script_sha256": sha(Path(__file__)), "source_version": src_v, "new_version": new_v,
              "patches": [{"patch": str(p.relative_to(DCOPF)), "patch_script": pmj["config"].get("script"), "base_version": pmj["config"].get("base_version"),
                           "rows_to_add": {s: len(v) for s, v in add.items()}, "rows_skipped": len(skip),
                           "rows_removed": sum(1 for t in touched if t[4] == "remove"), "rows_modified": sum(1 for t in touched if t[4] == "modify")}
                          for p, pmj, _, add, skip, touched in plans], "rebased": rebased,
              "substation_map": "source bytes kept, new rows appended as text", "validation_data_read": "none", "representative_buses": "unchanged (new buses IsRepresentative = 0)"}
    inputs = {f: sha(SRC / f) for f in FILES}
    for p, pmj, *_r in plans:
        inputs.update({f"{p.name}/{k}": v for k, v in pmj["outputs_sha256"].items()})
    (OUT / "manifest.json").write_text(json.dumps({"status": "started", "started": datetime.datetime.now().isoformat(timespec="seconds"), "config": CONFIG, "inputs_sha256": inputs}, indent=1))
    for f in FILES:
        shutil.copy2(SRC / f, OUT / f)
    # ---- workbook
    xl = openpyxl.load_workbook(OUT / "jao_core.xlsx"); changes, applied, new_nodes = [], [], []
    wb_final_rows = {(s, str(n), str(e)): r for s in ("Lines", "Tielines", "Transformers") for n, e, r in zip(wb[s].Line_name, wb[s].EIC_Code, wb[s].to_dict("records"))}
    for pdir, pmj, meta, add, skip, touched in plans:
        ev = {str(r["patch_id"]): r for r in meta.to_dict("records")}
        for s, name, eic, row, kind in touched:
            ws = xl[s]; hdr = [c.value for c in ws[1]]
            hit = [i for i in range(2, ws.max_row + 1) if str(ws.cell(i, hdr.index("Line_name") + 1).value) == str(name)
                   and str(ws.cell(i, hdr.index("EIC_Code") + 1).value) == str(eic)]
            if len(hit) != 1:
                sys.exit(f"ABORT: writing: {s} row {name} found {len(hit)} times")
            m = ev.get(f"{s}:{eic}:{name}", {})
            why = "; ".join(str(x) for x in (m.get("source", ""), m.get("conversion", ""), m.get("evidence", "")) if x)
            if kind == "remove":
                ws.delete_rows(hit[0], 1)
                changes.append({"patch": pdir.name, "sheet": s, "row_name": name, "field": "(row removed)", "old": json.dumps({c: py(v) for c, v in row.items()}), "new": "", "evidence": why})
            else:
                new = wb_final_rows[(s, str(name), str(eic))]
                for c in ("Currrent_(A)", "Capacity_MW", "X"):
                    if not same(row[c], new[c]):
                        ws.cell(hit[0], hdr.index(c) + 1).value = py(new[c])
                        changes.append({"patch": pdir.name, "sheet": s, "row_name": name, "field": c, "old": py(row[c]), "new": py(new[c]), "evidence": why})
            applied.append({"patch": pdir.name, "sheet": s, "patch_id": f"{s}:{eic}:{name}", "status": "removed" if kind == "remove" else "modified"})
        for s, rows in add.items():
            ws = xl[s]; hdr = [c.value for c in ws[1]]
            last = max(i for i in range(1, ws.max_row + 1) if ws.cell(i, 1).value not in (None, ""))
            for k, r in enumerate(rows, start=1):
                for c, v in r.items():
                    ws.cell(last + k, hdr.index(c) + 1).value = py(v)
                pid = r["Bus"] if s == "Nodes" else r["EIC_Code"]; m = ev.get(str(pid), {})
                why = "; ".join(str(x) for x in (m.get("source", ""), m.get("juan_edge_id", ""), m.get("conversion", ""), m.get("ip26_evidence", ""), m.get("jao2026_fb", ""), m.get("decision", "")) if x)
                changes.append({"patch": pdir.name, "sheet": s, "row_name": r["Bus"] if s == "Nodes" else r["Line_name"], "field": "(new row)", "old": "", "new": json.dumps({c: py(v) for c, v in r.items()}), "evidence": why})
                applied.append({"patch": pdir.name, "sheet": s, "patch_id": pid, "status": "added"})
                if s == "Nodes":
                    new_nodes.append((pdir.name, r, m.get("conversion", "")))
        applied += [{"patch": pdir.name, "sheet": s, "patch_id": n, "status": why} for s, n, why in skip]
    xl.save(OUT / "jao_core.xlsx")
    # ---- station map: bytes kept, rows appended as text with the file's own line ending and quoting
    raw = (SRC / "substation_map.csv").read_bytes(); nl = b"\r\n" if b"\r\n" in raw else b"\n"
    head = raw.decode("utf-8").splitlines()[0].split(",")
    if head != ["bus", "base_name", "kv_nominal", "zone", "lat", "lng", "coord_votes", "coord_evidence"]:
        sys.exit(f"ABORT: unexpected substation_map header {head}")
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator=nl.decode())
    for pname, r, conv in new_nodes:
        w.writerow([r["Bus"], str(r["Bus"]).rsplit("_", 1)[0], int(r["baseKV"]), r["Zone"], py(r["Latitude"]), py(r["Longitude"]), 0, f"patch {pname}: {conv}"])
    with open(OUT / "substation_map.csv", "wb") as fh:
        fh.write(raw if raw.endswith(nl) else raw + nl); fh.write(buf.getvalue().encode("utf-8"))
    with open(OUT / "corrections.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["patch", "sheet", "row_name", "field", "old", "new", "evidence"]); wr.writeheader(); wr.writerows(changes)
    with open(OUT / "patch_applied.csv", "w", newline="") as fh:
        wr = csv.DictWriter(fh, fieldnames=["patch", "sheet", "patch_id", "status"]); wr.writeheader(); wr.writerows(applied)
    with open(OUT / "build_report.md", "a") as fh:
        fh.write(f"\n\n---\n\n# Appended by scripts/{Path(__file__).name} ({datetime.date.today().isoformat()})\n\nPatches applied to jao_core_{src_v}, in order: "
                 + ", ".join(f"`{p.name}` ({', '.join(f'{len(v)} {s}' for s, v in add.items())} added; {sum(1 for t in tch if t[4] == 'remove')} removed; {sum(1 for t in tch if t[4] == 'modify')} modified; {len(skip)} skipped)" for p, _, _, add, skip, tch in plans)
                 + ".\n\n" + "\n".join(f"- {c['patch']} / {c['sheet']}: {c['row_name']}" for c in changes) + "\n\nSee each patch's CHANGELOG.md for sources and conversions.\n")
    # ---- read back and compare with the plan
    back = pd.read_excel(OUT / "jao_core.xlsx", sheet_name=None)
    if set(back) != set(wb):
        sys.exit("ABORT: read-back: sheet set differs")
    for s in wb:
        if not frames_equal({s: back[s].reset_index(drop=True)}, {s: wb[s].reset_index(drop=True)}):
            sys.exit(f"ABORT: read-back: sheet {s} differs from the planned workbook")
    sm = pd.read_csv(OUT / "substation_map.csv"); sm0 = pd.read_csv(SRC / "substation_map.csv")
    if len(sm) != len(sm0) + len(new_nodes) or not (OUT / "substation_map.csv").read_bytes().startswith(raw.rstrip(nl)):
        sys.exit("ABORT: substation_map.csv not source bytes + appended rows")
    for f in ("row_decisions.csv", "build_report.md"):
        if f == "row_decisions.csv" and sha(OUT / f) != sha(SRC / f):
            sys.exit("ABORT: row_decisions.csv changed")
    with open(OUT / "sha256.txt", "w") as fh:
        for p in sorted(OUT.iterdir()):
            if p.name not in ("sha256.txt", "manifest.json"):
                fh.write(f"{sha(p)}  {p.name}\n")
    (OUT / "manifest.json").write_text(json.dumps({"status": "finished", "finished": datetime.datetime.now().isoformat(timespec="seconds"), "config": CONFIG, "inputs_sha256": inputs,
                                                   "outputs_sha256": {p.name: sha(p) for p in sorted(OUT.iterdir()) if p.name != "manifest.json"}}, indent=1))
    for p, _, _, add, skip, tch in plans:
        print(f"{p.name}: added {', '.join(f'{len(v)} {s}' for s, v in add.items())}; removed {sum(1 for t in tch if t[4] == 'remove')}; modified {sum(1 for t in tch if t[4] == 'modify')}; skipped {len(skip)}")
    if rebased:
        print("rebased:", rebased)
    print("written:", OUT)


if __name__ == "__main__":
    main()
