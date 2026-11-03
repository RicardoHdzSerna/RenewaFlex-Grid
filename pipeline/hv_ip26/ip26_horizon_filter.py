"""
ip26_horizon_filter.py
======================

Data pipeline on top of ip26_network_scenarios.py.

For every parameter scenario (median, mean, q1, q3, template, median_oldline):
  1. read output/IP26_line_network_edges_<scenario>.xlsx
  2. remove all projects in phase "Studie" (n_projectfase_ip)
  3. write one workbook per horizon year with only the lines in service by then
     (N_ibn_jaar_ip2026 <= 2030, and <= 2040):
        output/horizons/IP26_line_network_edges_<scenario>_2030.xlsx
        output/horizons/IP26_line_network_edges_<scenario>_2040.xlsx

Only the columns edge_id ... source are kept (keep_columns_until in the config); duplicate
features (include_in_network = no) are removed. The electrical formulas stay live: references
to removed columns (n_circuits, the per-km parameters used) are replaced by their content, so the
formulas only point to kept columns and the Parameters tab. A tab "Horizon_filter"
lists every row with its year, phase and whether it was kept (and why not).

Network action columns (after 'source'): every kept edge is checked against Juan's network
(full_network.csv). Reinforcements of connections that already exist there must NOT be added as
extra edges (that would double the corridor) but applied as changes to the existing branches:
    network_action = modify existing branch      route exists: change rating / parameters of the
                                                 listed full_network branches (per-circuit values given)
                     new edge (extra circuits)   route exists but the project adds circuits: add this edge
                     new edge (new connection)   no route in full_network (new station / new route)
                     already in full_network     the added circuits already exist: no change
    applies_to_listed_branches = yes / no - duplicate of OBJECTID ... / no - reference only ...
        so that every full_network branch is changed once: rows of the same project listing the same branches
        (one project drawn as several features, e.g. 290/303) -> only the longest row applies; new-edge rows that
        list a loop-in branch or the existing circuits (e.g. 375 lists BSL-RLL380, changed by 378) are references.
    branches_also_listed_by = the other rows that name the same branches.
The Parameters and Notes tabs are cleaned of everything that only describes dropped columns (template block).
See network_check in config_horizons.yaml.

Usage:
    pip install pandas openpyxl pyyaml
    python ip26_network_scenarios.py all      # first: make the scenario workbooks
    python ip26_horizon_filter.py             # then: 2030 and 2040 workbooks per scenario
    python ip26_horizon_filter.py other.yaml
"""

import copy
import re
import sys
from pathlib import Path

import pandas as pd
import yaml
from openpyxl import load_workbook
from openpyxl.formula.translate import Translator
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

NAVY = PatternFill("solid", fgColor="1F3864")
WHITE_BOLD = Font(bold=True, color="FFFFFF")
NON_DATA_TABS = {"Parameters", "Stations", "IP26_new_stations", "Station_match", "Notes", "Horizon_filter"}


def load_config(path):
    path = Path(path).resolve()
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for key in ("input_folder", "output_folder"):
        folder = Path(cfg["paths"][key])
        cfg["paths"][key] = folder if folder.is_absolute() else path.parent / folder
    return cfg


def commissioning_year(value, basis):
    """'2029-2030' -> 2030 (end) or 2029 (start); '2027' -> 2027; empty -> None."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    years = [int(y) for y in re.findall(r"\d{4}", str(value))]
    if not years:
        return None
    return max(years) if basis == "end" else min(years)


def header_row(ws):
    """Row that holds the column names (row 1, or row 2 on the lijnverzwaring tab)."""
    for r in (1, 2):
        if ws.cell(r, 1).value == "edge_id":
            return r
    raise ValueError(f"tab {ws.title}: no 'edge_id' header in row 1 or 2")


def decide(cfg, phase, year_raw, horizon):
    year = commissioning_year(year_raw, cfg.get("year_basis", "end"))
    if phase in (cfg.get("exclude_phases") or []):
        return False, year, f"phase {phase} removed"
    if year is None:
        return (not cfg.get("drop_rows_without_year", True)), year, "no commissioning year"
    ok = year <= horizon if cfg.get("inclusive", True) else year < horizon
    return ok, year, ("kept" if ok else f"in service {year_raw}, after {horizon}")


# --------------------------------------------------------------------------- network check
ACTION_COLS = ["network_action", "applies_to_listed_branches", "branches_also_listed_by", "full_network_edge_ids", "full_network_circuits", "full_network_max_current_a",
               "full_network_length_km", "n_circuits", "per_circuit_resistance_ohm", "per_circuit_reactance_ohm",
               "per_circuit_susceptance_pu_total", "per_circuit_max_current_a", "action_note"]


def circuit_tag(edge_id):
    s = re.sub(r":seg\d+$", "", str(edge_id))
    return re.split(r"[ \-]", s)[-1]


def load_network(cfg, config_path):
    nc = cfg.get("network_check") or {}
    if not nc.get("enabled", True):
        return None
    base = Path(config_path).resolve().parent
    fn = pd.read_csv(base / nc["network_file"], float_precision="round_trip")
    fn = fn[fn["type"].isin(nc.get("edge_types") or ["line", "cable"])]
    idx = {}
    for r in fn.itertuples(index=False):
        idx.setdefault(frozenset((r.from_station_id, r.to_station_id)), []).append(r)
    nodes = set(pd.read_csv(base / nc["network_file"], usecols=["from_station_id", "to_station_id"], float_precision="round_trip").stack())
    assigns = {}
    if nc.get("assignments_config"):
        with open(base / nc["assignments_config"], encoding="utf-8") as f:
            assigns = yaml.safe_load(f).get("assignments") or {}
    decisions = {}
    if nc.get("decisions_config"):
        with open(base / nc["decisions_config"], encoding="utf-8") as f:
            decisions = yaml.safe_load(f) or {}
    ends = {r.edge_id: (r.from_station_id, r.to_station_id) for r in fn.itertuples(index=False)}
    return {"idx": idx, "nodes": nodes, "assigns": assigns, "cfg": nc, "decisions": decisions, "ends": ends,
            "edges": {r.edge_id: r for r in fn.itertuples(index=False)}}


def is_manual_copy(net, e):
    """True for a 'manual:' branch that repeats a real circuit (same stations, same circuit letter)."""
    if "manual:" not in e.edge_id:
        return False
    return any("manual:" not in o.edge_id and circuit_tag(o.edge_id) == circuit_tag(e.edge_id)
               for o in net["idx"].get(frozenset((e.from_station_id, e.to_station_id)), []))


def fn_section(net, a, b):
    """full_network edges between two stations, one per circuit letter ('manual' duplicates dropped)."""
    ignore = set(net["cfg"].get("ignore_circuit_ids") or [])
    edges = sorted(net["idx"].get(frozenset((a, b)), []), key=lambda e: ("manual" in e.edge_id, e.edge_id))
    out = {}
    for e in edges:
        t = circuit_tag(e.edge_id)
        if t not in ignore:
            out.setdefault(t, e)
    return out


def fn_copies(net, edges):
    """Other edges in full_network for the same station pair and circuit letter as the listed edges
    (Juan's file holds some circuits twice, e.g. 'branch:RLL-ZVL380 G' and 'branch:manual:RLL380-ZVL380-G')."""
    listed = {e.edge_id for e in edges}
    out = []
    for e in edges:
        for o in net["idx"].get(frozenset((e.from_station_id, e.to_station_id)), []):
            if o.edge_id not in listed and circuit_tag(o.edge_id) == circuit_tag(e.edge_id):
                listed.add(o.edge_id)
                out.append(o)
    return out


def fn_route(net, chain, common_only=True):
    """Sections of a multi-station route; when the same circuit letters run through every section,
    only those circuits are kept (e.g. TBN-BXT has W and Z, but only W continues to BT)."""
    secs = [fn_section(net, a, b) for a, b in zip(chain[:-1], chain[1:])]
    if not secs or not all(secs):
        return None
    common = set.intersection(*[set(s) for s in secs])
    if common_only and common and len(common) == min(len(s) for s in secs):
        secs = [{t: e for t, e in s.items() if t in common} for s in secs]
    return secs


def network_action(net, v):
    """Decides how one IP26 edge relates to Juan's network. v = row values by column name."""
    oid = int(v["OBJECTID"])
    frm, to = v.get("from_station_id"), v.get("to_station_id")
    via = [x.strip() for x in str(v.get("via_station_ids") or "").split(",") if x.strip() and x.strip() != "None"]
    name = str(v.get("n_projectnaam") or "")
    res = dict.fromkeys(ACTION_COLS)
    nodes = net["nodes"]
    missing = [x for x in (frm, to) if x not in nodes]
    if missing:
        note = "station(s) not in full_network: " + ", ".join(missing) + ". Add as new edge."
        loops = []
        for vs in via:
            for end in (frm, to):
                if vs in nodes and end in nodes:
                    sec = fn_section(net, vs, end)
                    if sec:
                        loops += [e.edge_id for e in sec.values()]
        if loops:
            res["full_network_edge_ids"] = "; ".join(loops)
            note += (" Loop-in: the new station is connected into existing branch(es) " + "; ".join(loops) +
                     " - split them at the new station instead of keeping them in parallel.")
        res.update(network_action="new edge (new connection)", action_note=note)
        return res
    via_in = [x for x in via if x in nodes]
    via_new = [x for x in via if x not in nodes]
    direct = fn_section(net, frm, to)
    chain = fn_route(net, [frm, *via_in, to]) if via_in else None
    a = net["assigns"].get(oid) or {}
    oc = fn_route(net, list(a["old_chain"])) if a.get("old_chain") else None
    if a.get("old_chain_first") and oc:
        sections, used_direct, used_chain = oc, False, oc
    else:
        sections = ([direct] if direct else []) + (chain or [])
        used_direct, used_chain = bool(direct), chain
        if not sections and oc:
            sections, used_chain = oc, oc
    if not sections:
        part = []
        if via_in:
            for x, y in zip([frm, *via_in], [*via_in, to]):
                sec = fn_section(net, x, y)
                part += [e.edge_id for e in sec.values()]
        res.update(network_action="new edge (new connection)",
                   full_network_edge_ids="; ".join(part) or None,
                   action_note=("no route between these stations in full_network. Add as new edge." +
                                (" Sections already in full_network: " + "; ".join(part) if part else "")))
        return res
    # keep all circuits of the chain when the project itself has more circuits than run through it
    n_ip = int(v.get("n_circuits") or 1)
    if used_chain and min(len(sec) for sec in used_chain) < n_ip:
        full = fn_route(net, list(a["old_chain"]) if used_chain is oc else [frm, *via_in, to], common_only=False)
        if full:
            sections = ([direct] if used_direct else []) + full
            used_chain = full
    edges = [e for sec in sections for e in sec.values()]
    tags = set(direct) if used_direct else set()
    if used_chain:
        tags |= min((set(sec) for sec in used_chain), key=len)
    n_fn = len(tags)
    if used_direct:
        length_fn = min(e.length_m for e in direct.values()) / 1000
    else:
        length_fn = sum(min(e.length_m for e in sec.values()) for sec in used_chain) / 1000
    copies = fn_copies(net, edges)
    manual = [e for e in copies if is_manual_copy(net, e)]
    other = [e for e in copies if not is_manual_copy(net, e)]
    copy_note = ""
    if manual:
        copy_note += (f". full_network also holds manual copies of the same circuit(s): "
                      f"{'; '.join(e.edge_id for e in manual)} - not listed and never changed (rule: only the real "
                      f"circuit is changed; the copy is marked in step 5)")
    if other:
        copy_note += (f". full_network also holds the same circuit a second time (not a manual copy): "
                      f"{'; '.join(e.edge_id for e in other)} (same stations, same circuit letter, same values) - "
                      f"listed and changed as well")
    edges = edges + other
    alt_note = ""
    if a.get("old_chain_first") and direct:
        alt_note = (f". full_network also has a direct branch between the drawn end stations: "
                    f"{'; '.join(e.edge_id for e in direct.values())} - the old line used here follows the project "
                    f"name ({'-'.join(a['old_chain'])}); check which branch the project actually replaces")
    res.update(full_network_edge_ids="; ".join(e.edge_id for e in edges), full_network_circuits=n_fn,
               full_network_max_current_a=min(float(e.max_current_a) for e in edges),
               full_network_length_km=round(length_fn, 3) if length_fn else None)
    need = None
    for rule in net["cfg"].get("circuit_rules") or []:
        m = re.search(rule["pattern"], name, flags=re.I)
        if m:
            need = int(m.group(1)) if rule["required"] == "group" else int(rule["required"])
            break
    if need is not None:
        if n_fn >= need:
            res.update(network_action="already in full_network",
                       action_note=f"full_network already has {n_fn} circuits (project gives {need}). Do not add"
                                   + copy_note + alt_note + ".")
        else:
            res.update(network_action="new edge (extra circuits)",
                       action_note=f"full_network has {n_fn} circuit(s) on this route, project gives {need}: add this "
                                   f"edge for the extra circuit(s); keep the existing branches" + copy_note + alt_note + ".")
        return res
    length_ip = (v.get("length_m") or 0) / 1000
    partial = length_fn and length_ip and length_ip < 0.7 * length_fn
    wz = str(v.get("n_werkzaamheden_ip") or "")
    what = {"lijnverzwaring": "upgrade", "Verkabelen": "cabling"}.get(wz, wz or "project")
    note = (f"{what} of an existing connection: do NOT add this edge (it would double the corridor). Apply the "
            f"per-circuit rating and parameters to the {len(edges)} listed full_network branch(es)") + copy_note + alt_note
    if partial:
        note += (f". Partial section: IP26 length {length_ip:.1f} km vs {length_fn:.1f} km in full_network - "
                 f"apply the new parameters to that part only (e.g. length-weighted)")
    if via_new:
        note += (f". New intermediate station(s) {', '.join(via_new)} (not in full_network): split the existing "
                 f"branch(es) at the new station (loop-in)")
    if used_direct and via_in and not chain:
        note += (f". The route exists directly but not through {', '.join(via_in)}: loop {', '.join(via_in)} into "
                 f"the existing branch(es) (split them)")
    if wz == "nieuwe verbinding" and not via_new and not (used_direct and via_in and not chain):
        note += ". Note: type 'nieuwe verbinding' but the route already exists in full_network - check"
    res.update(network_action="modify existing branch", action_note=note + ".")
    return res


def apply_decisions(net, actions):
    """Applies config_decisions.yaml to the network actions (review items c, d, e):
    circuit_assignment (one row per circuit), route_choice (one route of several), splits (loop-in)."""
    dec = net.get("decisions") or {}
    ends = net["ends"]
    for oid, circuits in (dec.get("circuit_assignment") or {}).items():
        res = actions.get(int(oid))
        if not res or not res.get("full_network_edge_ids"):
            continue
        ids = [e.strip() for e in str(res["full_network_edge_ids"]).split(";") if e.strip()]
        keep = [e for e in ids if circuit_tag(e) in set(circuits)]
        res["full_network_edge_ids"] = "; ".join(keep)
        res["full_network_circuits"] = len({circuit_tag(e) for e in keep})
        res["action_note"] = (f"Decision (circuit_assignment): this row changes circuit(s) {', '.join(circuits)} only "
                              f"({'; '.join(keep)}); the other circuit(s) of the project are changed by their own row. "
                              + str(res.get("action_note") or ""))
    for oid, d in (dec.get("route_choice") or {}).items():
        res = actions.get(int(oid))
        if not res or not res.get("full_network_edge_ids"):
            continue
        route = list(d["route"])
        pairs = {frozenset(p) for p in zip(route[:-1], route[1:])}
        ids = [e.strip() for e in str(res["full_network_edge_ids"]).split(";") if e.strip()]
        keep = [e for e in ids if frozenset(ends[e]) in pairs]
        dropped = [e for e in ids if e not in keep]
        secs = {}
        for e in keep:
            secs.setdefault(frozenset(ends[e]), []).append(e)
        res["full_network_edge_ids"] = "; ".join(keep)
        res["full_network_circuits"] = min(len(v) for v in secs.values()) if secs else 0
        res["full_network_length_km"] = round(sum(min(net["edges"][e].length_m for e in v) for v in secs.values()) / 1000, 3)
        res["full_network_max_current_a"] = min(float(net["edges"][e].max_current_a) for e in keep) if keep else None
        res["action_note"] = (f"Decision (route_choice, {d.get('status', '')}): route {'-'.join(route)}; changed: "
                              f"{'; '.join(keep)}; not changed (other route): {'; '.join(dropped) or 'none'}. "
                              + str(res.get("action_note") or ""))
    excluded = {int(k) for k in (dec.get("exclude_rows") or {})}
    for oid, d in (dec.get("splits") or {}).items():
        res = actions.get(int(oid))
        if not res or not d.get("enabled", True) or int(oid) in excluded:
            continue
        a, b = d["line"]
        line_ids = sorted(e for e, st in ends.items() if frozenset(st) == frozenset((a, b))
                          and circuit_tag(e) in set(d["circuits"]) and not is_manual_copy(net, net["edges"][e]))
        res["network_action"] = "split existing branch"
        res["full_network_edge_ids"] = "; ".join(line_ids)
        res["full_network_circuits"] = len(line_ids)
        res["action_note"] = (f"Decision (splits, {d.get('status', '')}): {'-'.join(d['line'])} circuits "
                              f"{', '.join(d['circuits'])} are cut at the new station {d['station']} into "
                              f"{a}-{d['station']} and {d['station']}-{b} (step 5); this row's edge is the loop-in "
                              f"connection and becomes part of both new branches, it is not added separately.")
    return actions


def mark_references(actions, info, excluded=None):
    """Marks, for every kept IP26 row, whether its change applies to the listed full_network branches, so that
    every branch is changed only once.
      modify existing branch: rows of the same project (n_nummer) that list the same branches are duplicates
        (one project drawn as several features, e.g. 290/303 Rilland-Zandvliet): the row with the longest IP26
        length applies (tie: lowest OBJECTID), the others get "no - duplicate of ...". Rows of different
        projects that change the same branch both apply (step 5 combines them in series) and are flagged.
      new edge (new connection / extra circuits): the listed branches are a reference only (loop-in to split,
        or the existing circuits that are kept); they are not changed by this row (e.g. 375 lists BSL-RLL380,
        whose parameters are changed by 378).
      already in full_network: no change."""
    def listed(res):
        return [e.strip() for e in str(res.get("full_network_edge_ids") or "").split(";") if e.strip()]

    by_branch = {}
    for oid, res in actions.items():
        for e in listed(res):
            by_branch.setdefault(e, []).append(oid)
    modify = {oid: res for oid, res in actions.items() if res.get("network_action") == "modify existing branch"
              and int(oid) not in {int(k) for k in (excluded or {})}}
    groups = {}
    for oid, res in modify.items():
        key = (info.get(oid, {}).get("n_nummer"), frozenset(listed(res)))
        groups.setdefault(key, []).append(oid)
    applies = {}
    for (proj, _), oids in groups.items():
        oids.sort(key=lambda o: (-(info.get(o, {}).get("length_m") or 0), o))
        applies[oids[0]] = "yes"
        for o in oids[1:]:
            applies[o] = (f"no - duplicate of OBJECTID {oids[0]} (same project {proj}, same branches); "
                          f"the change is applied once, by OBJECTID {oids[0]}")
    for oid, reason in (excluded or {}).items():
        if int(oid) in actions:
            applies[int(oid)] = f"no - excluded for now (config_decisions.yaml exclude_rows: {reason})"
    for oid, res in actions.items():
        act = res.get("network_action")
        if oid not in applies:
            if act == "split existing branch":
                applies[oid] = "yes - split (loop-in of a new station, see action_note)"
            elif act == "new edge (extra circuits)":
                applies[oid] = ("no - reference only: the listed branches are the existing circuits, kept "
                                "unchanged; this row adds its own new circuit(s) as a new edge")
            elif act and act.startswith("new edge"):
                applies[oid] = ("no - reference only: loop-in, the listed branches are not changed by this row; "
                                "this row is added as a new edge") if listed(res) else "n/a - no listed branches (new edge)"
            elif act == "already in full_network":
                applies[oid] = "no - already in full_network, no change"
            else:
                applies[oid] = "n/a"
    for oid, res in actions.items():
        res["applies_to_listed_branches"] = applies[oid]
        other = sorted({o for e in listed(res) for o in by_branch.get(e, []) if o != oid})
        if other:
            res["branches_also_listed_by"] = "; ".join(
                f"{o} ({actions[o].get('network_action')}, applies: {applies[o].split(' -')[0]})" for o in other)
            changers = [o for o in other if applies[o] == "yes" and actions[o].get("network_action") ==
                        "modify existing branch" and info.get(o, {}).get("n_nummer") != info.get(oid, {}).get("n_nummer")]
            if applies[oid] == "yes" and changers:
                res["action_note"] = (res.get("action_note") or "") + (
                    f" Also changed by OBJECTID {', '.join(map(str, changers))} (other project): both changes are "
                    f"combined in series on the shared branches.")
    return actions


REF = re.compile(r"(?<![!$A-Za-z0-9_])\$?([A-Z]{1,3})\$?(\d+)(?![0-9(])")


def inline_formula(formula, row_cells, keep_cols, depth=0):
    """Replaces references to columns that will be removed by their content (value or formula),
    so that the kept formulas stay live and only reference kept columns or the Parameters tab."""
    if depth > 10:
        raise ValueError(f"formula nesting too deep: {formula}")
    body = formula[1:]

    def sub(m):
        col = m.group(1)
        if col in keep_cols:
            return m.group(0)
        v = row_cells.get(col)
        if isinstance(v, str) and v.startswith("="):
            return "(" + inline_formula(v, row_cells, keep_cols, depth + 1)[1:] + ")"
        if v is None:
            return "0"
        return repr(float(v)) if isinstance(v, (int, float)) else f'"{v}"'
    return "=" + REF.sub(sub, body)


def filter_data_tab(wb, ws, cfg, horizon, actions=None):
    """Keeps the rows that pass the filter and the columns up to 'source'; writes them to a new
    sheet (header in row 1) with the formulas translated to the new rows."""
    h = header_row(ws)
    names = [c.value for c in ws[h]]
    c_oid = names.index("OBJECTID") + 1
    c_phase = names.index("n_projectfase_ip") + 1
    c_year = names.index("N_ibn_jaar_ip2026") + 1
    c_inc = names.index("include_in_network") + 1 if "include_in_network" in names else None
    last_col = names.index(cfg.get("keep_columns_until", "source")) + 1
    keep_cols = {get_column_letter(c) for c in range(1, last_col + 1)}
    decisions, kept = [], []
    for r in range(h + 1, ws.max_row + 1):
        oid = ws.cell(r, c_oid).value
        if oid is None:
            continue
        ok, year, why = decide(cfg, ws.cell(r, c_phase).value, ws.cell(r, c_year).value, horizon)
        if ok and c_inc and cfg.get("drop_duplicate_features", True) and ws.cell(r, c_inc).value == "no":
            ok, why = False, "duplicate feature (include_in_network = no)"
        decisions.append((oid, ok, year, why))
        if ok:
            kept.append(r)
    # new sheet in the same position
    idx = wb.sheetnames.index(ws.title)
    title = ws.title
    new = wb.create_sheet(title + "_tmp", idx)
    for c in range(1, last_col + 1):
        src = ws.cell(h, c)
        dst = new.cell(1, c, src.value)
        dst._style = copy.copy(src._style)
        letter = get_column_letter(c)
        if ws.column_dimensions[letter].width:
            new.column_dimensions[letter].width = ws.column_dimensions[letter].width
    for i, r in enumerate(kept):
        dst_row = 2 + i
        row_cells = {get_column_letter(c): ws.cell(r, c).value for c in range(1, ws.max_column + 1)}
        for c in range(1, last_col + 1):
            src = ws.cell(r, c)
            v = src.value
            if isinstance(v, str) and v.startswith("="):
                v = inline_formula(v, row_cells, keep_cols)
                letter = get_column_letter(c)
                v = Translator(v, origin=f"{letter}{r}").translate_formula(f"{letter}{dst_row}")
            cell = new.cell(dst_row, c, v)
            cell._style = copy.copy(src._style)
            cell.number_format = src.number_format
    ncol = last_col
    if actions is not None:
        L = {n: get_column_letter(i + 1) for i, n in enumerate(names[:last_col])}
        hdr_src = ws.cell(h, last_col)
        for j, t in enumerate(ACTION_COLS, start=last_col + 1):
            c = new.cell(1, j, t)
            c._style = copy.copy(hdr_src._style)
            c.fill = PatternFill("solid", fgColor="FCE4D6")
            new.column_dimensions[get_column_letter(j)].width = {"network_action": 26, "full_network_edge_ids": 45,
                                                                 "applies_to_listed_branches": 40, "branches_also_listed_by": 40,
                                                                 "action_note": 90}.get(t, 14)
        fill = {"modify existing branch": "FFEB9C", "new edge (extra circuits)": "DDEBF7",
                "new edge (new connection)": "C6EFCE", "already in full_network": "D9D9D9",
                "split existing branch": "E4DFEC"}
        for i, r in enumerate(kept):
            dst_row = 2 + i
            v = {n: ws.cell(r, j + 1).value for j, n in enumerate(names)}
            res = dict(actions[v["OBJECTID"]])
            n = v.get("n_circuits") or 1
            res["n_circuits"] = n
            if v.get("resistance_ohm") is not None:     # live formulas on the kept columns
                res["per_circuit_resistance_ohm"] = f"={L['resistance_ohm']}{dst_row}*{n}"
                res["per_circuit_reactance_ohm"] = f"={L['reactance_ohm']}{dst_row}*{n}"
                res["per_circuit_susceptance_pu_total"] = f"={L['susceptance_pu_total']}{dst_row}/{n}"
                res["per_circuit_max_current_a"] = f"={L['max_current_a']}{dst_row}/{n}"
            for j, t in enumerate(ACTION_COLS, start=last_col + 1):
                c = new.cell(dst_row, j, res.get(t))
                if t == "network_action" and res.get(t) in fill:
                    c.fill = PatternFill("solid", fgColor=fill[res[t]])
                if t == "applies_to_listed_branches" and str(res.get(t)).startswith("no - duplicate"):
                    c.fill = PatternFill("solid", fgColor="F4B084")
                if t.startswith("per_circuit"):
                    c.number_format = "0.000000" if "susceptance" in t else "0.000"
        ncol = last_col + len(ACTION_COLS)
    new.freeze_panes = "B2"
    new.auto_filter.ref = f"A1:{get_column_letter(ncol)}{max(1, 1 + len(kept))}"
    wb.remove(ws)
    new.title = title
    return decisions


def filter_match_tab(ws, keep):
    names = [c.value for c in ws[1]]
    c_oid = names.index("OBJECTID") + 1
    for r in range(ws.max_row, 1, -1):          # bottom-up: plain values only, no formulas
        if ws.cell(r, c_oid).value not in keep:
            ws.delete_rows(r)
    ws.auto_filter.ref = f"A1:{get_column_letter(ws.max_column)}{max(1, ws.max_row)}"


def write_log(wb, decisions, cfg, horizon, scenario):
    ws = wb.create_sheet("Horizon_filter")
    ws["A1"] = (f"Horizon {horizon}, scenario {scenario}: projects in phase {', '.join(cfg.get('exclude_phases') or [])} "
                f"removed; kept when commissioning year ({cfg.get('year_basis', 'end')} year of N_ibn_jaar_ip2026) "
                f"{'<=' if cfg.get('inclusive', True) else '<'} {horizon}.")
    ws["A1"].font = Font(bold=True)
    heads = ["OBJECTID", "n_projectnaam", "n_werkzaamheden_ip", "n_projectfase_ip", "N_ibn_jaar_ip2026",
             "year_used", "kept", "reason", "include_in_network"]
    for j, t in enumerate(heads, start=1):
        c = ws.cell(3, j, t)
        c.font, c.fill = WHITE_BOLD, NAVY
    for i, d in enumerate(decisions, start=4):
        for j, t in enumerate(heads, start=1):
            ws.cell(i, j, d.get(t))
    for col, w in zip("ABCDEFGHI", (10, 60, 20, 16, 16, 10, 7, 32, 16)):
        ws.column_dimensions[col].width = w
    ws.freeze_panes = "A4"
    ws.auto_filter.ref = f"A3:I{3 + len(decisions)}"


def clean_dropped(wb, cfg):
    """Removes from the Parameters and Notes tabs everything that only describes columns dropped by the
    horizon filter (columns after keep_columns_until): the template block (cap, PF, RF for X model,
    X standard, Peak capacity, Secure capacity) and the notes on those columns."""
    if "Parameters" in wb.sheetnames:
        ws = wb["Parameters"]
        start = next((r for r in range(1, ws.max_row + 1)
                      if str(ws.cell(r, 2).value or "").startswith("Parameters of the original template")), None)
        if start:
            # no kept formula may point into the block
            for tab in wb.worksheets:
                for row in tab.iter_rows():
                    for c in row:
                        if isinstance(c.value, str) and c.value.startswith("="):
                            for rr in re.findall(r"Parameters!\$?[A-Z]+\$?(\d+)", c.value):
                                if int(rr) >= start:
                                    raise ValueError(f"{tab.title}!{c.coordinate} still uses Parameters row {rr}")
            ws.delete_rows(start - 1 if ws.cell(start - 1, 2).value is None else start, ws.max_row)
    if "Notes" in wb.sheetnames:
        ws = wb["Notes"]
        drop = ("Last four columns", "lijnverzwaring tab: the 'Old line values'", "Filter include_in_network")
        for r in range(ws.max_row, 0, -1):
            if any(str(ws.cell(r, 1).value or "").startswith(d) for d in drop):
                ws.delete_rows(r)
        ws.cell(ws.max_row + 2, 1, f"Horizon workbook: only the columns edge_id ... {cfg.get('keep_columns_until', 'source')} "
                                   "are kept (the template columns X model, X standard, Peak capacity, Secure capacity, "
                                   "the old line values and the project columns were dropped, and their parameters "
                                   "removed from the Parameters tab); the network action columns after source come "
                                   "from the check against full_network.csv. Duplicate features were removed.")


def process(cfg, scenario, horizon, net=None):
    p = cfg["paths"]
    src = p["input_folder"] / p["input_pattern"].format(scenario=scenario)
    if not src.exists():
        raise FileNotFoundError(f"{src} not found - run ip26_network_scenarios.py {scenario} (or all) first")
    wb = load_workbook(src)
    # row information for the log, from tab 1 (all rows)
    ws1 = wb["1"]
    h = header_row(ws1)
    names = [c.value for c in ws1[h]]
    info = {}
    for r in range(h + 1, ws1.max_row + 1):
        vals = {n: ws1.cell(r, j + 1).value for j, n in enumerate(names)}
        if vals.get("OBJECTID") is not None:
            info[vals["OBJECTID"]] = vals
    actions = None
    if net is not None:
        c_inc = names.index("include_in_network") + 1 if "include_in_network" in names else None
        actions = {}
        for oid, vals in info.items():
            ok, _, _ = decide(cfg, vals.get("n_projectfase_ip"), vals.get("N_ibn_jaar_ip2026"), horizon)
            if ok and not (c_inc and cfg.get("drop_duplicate_features", True) and vals.get("include_in_network") == "no"):
                actions[oid] = network_action(net, vals)
        apply_decisions(net, actions)
        mark_references(actions, info, (net.get("decisions") or {}).get("exclude_rows"))
    decisions_all = None
    for title in list(wb.sheetnames):
        if title in NON_DATA_TABS:
            continue
        dec = filter_data_tab(wb, wb[title], cfg, horizon, actions)
        if title == "1":
            decisions_all = dec
    keep = {oid for oid, ok, _, _ in decisions_all if ok}
    if cfg.get("filter_match_tab") in wb.sheetnames:
        filter_match_tab(wb[cfg["filter_match_tab"]], keep)
    log = []
    for oid, ok, year, why in decisions_all:
        v = info.get(oid, {})
        log.append({"OBJECTID": oid, "n_projectnaam": v.get("n_projectnaam"),
                    "n_werkzaamheden_ip": v.get("n_werkzaamheden_ip"), "n_projectfase_ip": v.get("n_projectfase_ip"),
                    "N_ibn_jaar_ip2026": v.get("N_ibn_jaar_ip2026"), "year_used": year,
                    "kept": "yes" if ok else "no", "reason": why, "include_in_network": v.get("include_in_network")})
    write_log(wb, log, cfg, horizon, scenario)
    clean_dropped(wb, cfg)
    if "Notes" in wb.sheetnames:
        ws = wb["Notes"]
        ws.cell(ws.max_row + 2, 1, f"Horizon filter ({horizon}): {len(keep)} of {len(decisions_all)} rows kept "
                                    f"(see tab Horizon_filter). Made by ip26_horizon_filter.py from {src.name}.")
    wb.calculation.fullCalcOnLoad = True
    out_dir = p["output_folder"]
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / p["output_pattern"].format(scenario=scenario, horizon=horizon)
    wb.save(out)
    msg = ""
    if net is not None:
        ws = wb["1"]
        hdr = [c.value for c in ws[1]]
        if "network_action" in hdr:
            j = hdr.index("network_action") + 1
            acts = pd.Series([ws.cell(r, j).value for r in range(2, ws.max_row + 1)]).value_counts().to_dict()
            msg = f"; {acts}"
    print(f"{out.name}: {len(keep)} edges kept{msg}")
    return out, log


def main(config_path=None):
    config_path = config_path or Path(__file__).with_name("config_horizons.yaml")
    cfg = load_config(config_path)
    net = load_network(cfg, config_path)
    summary = []
    for scenario in cfg["scenarios"]:
        for horizon in cfg["horizons"]:
            out, log = process(cfg, scenario, horizon, net)
            summary.append((scenario, horizon, sum(d["kept"] == "yes" for d in log)))
    return summary


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
