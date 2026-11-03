"""
ip26_vs_full_network.py
=======================

Which IP26 projects are already in Juan's 2030 network (full_network.csv)?

Reads
    DATA/full_network.csv                         Juan's network (edge list)
    DATA/IP26_line.xlsx                           TenneT IP2026 line projects
    output/IP26_line_network_edges_median.xlsx     stations per IP26 line (from ip26_network_scenarios.py)
    optional: Juan's node coordinates (GridAware topology map) as CSV

and writes output/IP26_projects_vs_full_network.xlsx with
    Projects   one row per IP26 project (n_nummer): in full_network / partly / not in full_network
    Lines      one row per IP26 line feature with all checks
    Stations   every station used by IP26: in full_network.csv or not (and Juan's coordinates if given)
    Rules      the classification rules

Classification of one IP26 line (duplicate features are skipped):
    not in    the route between its from and to station (direct, or through the via stations)
              does not exist in full_network.csv (e.g. new station, new route)
    partly    the route exists, but not everything the project delivers:
                - fewer circuits than the project gives ("3e circuit", "3e en 4e circuit"),
                - lijnverzwaring: rating in full_network.csv below the upgrade target,
                - Verkabelen: the route is still an overhead line in full_network.csv,
                - only some sections of a multi-station route exist
    in        the route exists with the circuits, rating or cable the project delivers
A project is "in" when all its lines are in, "not in" when none is, otherwise "partly".

Usage:
    pip install pandas openpyxl pyyaml
    python ip26_vs_full_network.py                    # uses config_vs_full_network.yaml
    python ip26_vs_full_network.py other.yaml
"""

import re
import sys
from pathlib import Path

import pandas as pd
import yaml
from openpyxl import load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

NAVY = PatternFill("solid", fgColor="1F3864")
WHITE_BOLD = Font(bold=True, color="FFFFFF")
FILL = {"in": PatternFill("solid", fgColor="C6EFCE"), "partly": PatternFill("solid", fgColor="FFEB9C"),
        "not in": PatternFill("solid", fgColor="FFC7CE")}


# --------------------------------------------------------------------------- helpers
def load_config(path):
    path = Path(path).resolve()
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    for key in ("input_folder", "output_folder"):
        folder = Path(cfg["paths"][key])
        cfg["paths"][key] = folder if folder.is_absolute() else path.parent / folder
    return cfg


def kv_number(v):
    m = re.search(r"\d+", str(v)) if v is not None and not (isinstance(v, float) and pd.isna(v)) else None
    return int(m.group()) if m else None


def end_year(v):
    years = [int(y) for y in re.findall(r"\d{4}", str(v))] if isinstance(v, (str, int)) else []
    return max(years) if years else None


def circuit_tag(edge_id):
    s = re.sub(r":seg\d+$", "", str(edge_id))
    return re.split(r"[ \-]", s)[-1]


def build_index(fn, cfg):
    e = fn[fn["type"].isin(cfg.get("edge_types") or ["line", "cable"])]
    idx = {}
    for r in e.itertuples(index=False):
        idx.setdefault(frozenset((r.from_station_id, r.to_station_id)), []).append(r)
    return idx


def section(idx, a, b, ignore):
    """Edges between two stations, one per circuit letter (non-'manual' edge preferred)."""
    edges = sorted(idx.get(frozenset((a, b)), []), key=lambda e: ("manual" in e.edge_id, e.edge_id))
    out = {}
    for e in edges:
        t = circuit_tag(e.edge_id)
        if t not in ignore:
            out.setdefault(t, e)
    return out


def route(idx, frm, to, via, ignore):
    """Looks up the route in full_network.csv: direct edge and/or chain through the via stations.
    Returns dict with status of the route and the circuits found."""
    res = {"direct": {}, "chain": None, "chain_found": 0, "chain_total": 0}
    res["direct"] = section(idx, frm, to, ignore)
    if via:
        stations = [frm, *via, to]
        secs = [section(idx, a, b, ignore) for a, b in zip(stations[:-1], stations[1:])]
        res["chain"] = secs
        res["chain_found"] = sum(1 for s in secs if s)
        res["chain_total"] = len(secs)
    return res


# --------------------------------------------------------------------------- classification
def classify(row, cfg, idx, fn_nodes, assignment=None):
    ignore = set(cfg.get("ignore_circuit_ids") or [])
    frm, to = row.get("from_station_id"), row.get("to_station_id")
    via = [v.strip() for v in str(row.get("via_station_ids") or "").split(",") if v.strip() and v.strip() != "nan"]
    kv = kv_number(row.get("kv"))
    wz = str(row.get("n_werkzaamheden_ip") or "").strip()
    name = str(row.get("n_projectnaam") or "")
    out = {"from_in_full_network": None, "to_in_full_network": None, "route_in_full_network": None,
           "full_network_edges": None, "full_network_circuits": None, "full_network_type": None,
           "full_network_max_current_a": None, "required": None, "upgrade_check": None, "status": None, "reason": None}
    if not frm or not to or pd.isna(frm) or pd.isna(to):
        out.update(status="not in", reason="no stations (no project data)")
        return out
    out["from_in_full_network"] = "yes" if frm in fn_nodes else "no"
    out["to_in_full_network"] = "yes" if to in fn_nodes else "no"
    missing = [x for x in (frm, to) if x not in fn_nodes]
    if missing:
        out.update(route_in_full_network="no", status="not in",
                   reason="station(s) not in full_network.csv: " + ", ".join(missing))
        return out
    via_in = [v for v in via if v in fn_nodes]
    via_missing = [v for v in via if v not in fn_nodes]
    r = route(idx, frm, to, via_in, ignore)
    direct = r["direct"]
    chain_ok = r["chain"] is not None and r["chain_found"] == r["chain_total"] and r["chain_total"] > 0
    chain_part = r["chain"] is not None and 0 < r["chain_found"] < r["chain_total"]
    old_chain = (assignment or {}).get("old_chain")
    oc = None
    if not direct and not chain_ok and old_chain:
        secs = [section(idx, a, b, ignore) for a, b in zip(old_chain[:-1], old_chain[1:])]
        if all(secs):
            oc = secs
    pre = []     # reasons that limit the status to 'partly'
    if via_missing:
        pre.append("new intermediate station(s) not in full_network.csv: " + ", ".join(via_missing))
    if direct or chain_ok or oc:
        if chain_ok:
            chain_tags = min((set(s) for s in r["chain"]), key=len)
            chain_edges = [e for s in r["chain"] for e in s.values()]
        else:
            chain_tags, chain_edges = set(), []
        if oc:
            chain_tags = min((set(s) for s in oc), key=len)
            chain_edges = [e for s in oc for e in s.values()]
        tags = set(direct) | chain_tags
        edges = list(direct.values()) + chain_edges
        how = ("direct" if direct else "") + (" + " if direct and (chain_ok or oc) else "") + \
              ("via " + ", ".join(via_in) if chain_ok else "") + ("via " + "-".join(old_chain) if oc else "")
        out["route_in_full_network"] = f"yes ({how})"
        if direct and via_in and not chain_ok:
            pre.append(f"route exists directly, but not through {', '.join(via_in)} "
                       f"({r['chain_found']} of {r['chain_total']} sections)")
    elif chain_part:
        edges = [e for s in r["chain"] for e in s.values()]
        tags = set()
        out["route_in_full_network"] = f"partly ({r['chain_found']} of {r['chain_total']} sections)"
        pre.append(f"only {r['chain_found']} of {r['chain_total']} sections of the route "
                   f"({frm} - {', '.join(via_in)} - {to}) exist in full_network.csv")
    else:
        out.update(route_in_full_network="no", status="not in",
                   reason="no edge between these stations in full_network.csv")
        return out
    out["full_network_edges"] = "; ".join(e.edge_id for e in edges)
    out["full_network_circuits"] = len(tags) if tags else None
    types = sorted({e.type for e in edges})
    out["full_network_type"] = "/".join(types)
    out["full_network_max_current_a"] = min(float(e.max_current_a) for e in edges) if edges else None
    # what the project delivers
    reasons = []
    for rule in cfg.get("circuit_rules") or []:
        m = re.search(rule["pattern"], name, flags=re.I)
        if m:
            need = int(m.group(1)) if rule["required"] == "group" else int(rule["required"])
            out["required"] = f">= {need} circuits"
            if len(tags) < need:
                reasons.append(f"{len(tags)} circuit(s) in full_network, project gives {need}")
            break
    if wz in (cfg.get("upgrade_types") or []) and kv in (cfg.get("upgrade_target_rating_a") or {}):
        target = cfg["upgrade_target_rating_a"][kv]
        assumed = kv in (cfg.get("upgrade_target_is_assumption") or [])
        out["required"] = (out["required"] + "; " if out["required"] else "") + \
            f">= {target} A{' (assumed target)' if assumed else ''}"
        cur = out["full_network_max_current_a"]
        if assumed and not cfg.get("verify_assumed_targets", False):
            out["upgrade_check"] = "not verifiable"
            reasons.append(f"upgrade not verifiable: no published target rating at {kv} kV "
                           f"(full_network has {cur:.0f} A)")
        elif cur is not None and cur < target:
            out["upgrade_check"] = "not in full_network"
            reasons.append(f"rating {cur:.0f} A in full_network < upgrade target {target} A")
        else:
            out["upgrade_check"] = "in full_network"
    if wz in (cfg.get("cabling_types") or []):
        out["required"] = (out["required"] + "; " if out["required"] else "") + "cable"
        if "cable" not in types:
            reasons.append("route is an overhead line in full_network, project cables it")
    reasons = pre + reasons
    if reasons:
        lead = "route partly exists" if str(out["route_in_full_network"]).startswith("partly") else "route exists"
        out.update(status="partly", reason=lead + "; " + "; ".join(reasons))
    else:
        out.update(status="in", reason="route exists" + (" with the required " + out["required"] if out["required"] else ""))
    return out


def project_status(statuses):
    s = set(statuses)
    if s == {"in"}:
        return "in"
    if s == {"not in"}:
        return "not in"
    return "partly"


# --------------------------------------------------------------------------- output
def write_df(wb_writer, name, df, widths, status_col=None):
    df.to_excel(wb_writer, sheet_name=name, index=False)
    ws = wb_writer.sheets[name]
    for j, c in enumerate(df.columns, start=1):
        cell = ws.cell(1, j)
        cell.font, cell.fill = WHITE_BOLD, NAVY
        cell.alignment = Alignment(wrap_text=True, vertical="top")
        ws.column_dimensions[get_column_letter(j)].width = widths.get(c, 14)
    if status_col and status_col in df.columns:
        j = list(df.columns).index(status_col) + 1
        for i, v in enumerate(df[status_col], start=2):
            if v in FILL:
                ws.cell(i, j).fill = FILL[v]
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}"


def main(config_path=None):
    config_path = config_path or Path(__file__).with_name("config_vs_full_network.yaml")
    cfg = load_config(config_path)
    p = cfg["paths"]
    fn = pd.read_csv(p["input_folder"] / p["network_file"], float_precision="round_trip")
    idx = build_index(fn, cfg)
    fn_nodes = set(fn["from_station_id"]) | set(fn["to_station_id"])
    edges_wb = p["output_folder"] / p["edges_workbook"]
    if not edges_wb.exists():
        raise FileNotFoundError(f"{edges_wb} not found - run ip26_network_scenarios.py first")
    lines = pd.read_excel(edges_wb, sheet_name="1")
    stations = pd.read_excel(edges_wb, sheet_name="Stations")
    ip26 = pd.read_excel(p["input_folder"] / p["ip26_file"])
    year_cut = cfg.get("network_year", 2030)
    assigns = {}
    if p.get("network_config"):
        with open(Path(config_path).resolve().parent / p["network_config"], encoding="utf-8") as f:
            assigns = yaml.safe_load(f).get("assignments") or {}

    rows = []
    for _, r in lines.iterrows():
        rec = {c: r.get(c) for c in ["OBJECTID", "n_nummer", "n_projectnaam", "n_werkzaamheden_ip", "n_projectfase_ip",
                                     "N_ibn_jaar_ip2026", "kv", "bestaand_nieuw", "edge_type", "edge_id",
                                     "from_station_id", "from_station_name", "to_station_id", "to_station_name",
                                     "via_station_ids", "n_circuits", "include_in_network", "duplicate_of_OBJECTID",
                                     "match_confidence"]}
        if r.get("include_in_network") == "no":
            rec.update(status="duplicate", reason=f"duplicate feature of {int(r['duplicate_of_OBJECTID'])} (not counted)")
        else:
            rec.update(classify(r, cfg, idx, fn_nodes, assigns.get(int(r['OBJECTID']), {})))
        y = end_year(r.get("N_ibn_jaar_ip2026"))
        rec["expected_by_network_year"] = None if y is None else ("yes" if y <= year_cut else "no")
        rows.append(rec)
    L = pd.DataFrame(rows)
    order = ["OBJECTID", "n_nummer", "n_projectnaam", "n_werkzaamheden_ip", "n_projectfase_ip", "N_ibn_jaar_ip2026",
             "expected_by_network_year", "kv", "edge_type", "status", "reason", "from_station_id", "from_station_name",
             "from_in_full_network", "to_station_id", "to_station_name", "to_in_full_network", "via_station_ids",
             "route_in_full_network", "full_network_edges", "full_network_circuits", "full_network_type",
             "full_network_max_current_a", "required", "upgrade_check", "n_circuits", "bestaand_nieuw", "include_in_network",
             "duplicate_of_OBJECTID", "match_confidence", "edge_id"]
    L = L[order]

    # projects
    prj = []
    for num, g in L[L.n_nummer.notna()].groupby("n_nummer", sort=False):
        g2 = g[g.status != "duplicate"]
        st = project_status(g2.status) if len(g2) else "not in"
        y = end_year(g.N_ibn_jaar_ip2026.iloc[0])
        exp = None if y is None else (y <= year_cut)
        if st == "in" and exp is False:
            note = f"in full_network although commissioning after {year_cut}"
        elif st != "in" and exp:
            note = f"expected by {year_cut} but {'only partly' if st == 'partly' else 'not'} in full_network"
        else:
            note = None
        prj.append({"n_nummer": num, "n_projectnaam": g.n_projectnaam.iloc[0],
                    "n_werkzaamheden_ip": g.n_werkzaamheden_ip.iloc[0], "n_projectfase_ip": g.n_projectfase_ip.iloc[0],
                    "N_ibn_jaar_ip2026": g.N_ibn_jaar_ip2026.iloc[0], "kv": g.kv.iloc[0],
                    "expected_by_network_year": None if exp is None else ("yes" if exp else "no"),
                    "status": st, "lines": ", ".join(str(int(o)) for o in g.OBJECTID),
                    "lines_in": int((g2.status == "in").sum()), "lines_partly": int((g2.status == "partly").sum()),
                    "lines_not_in": int((g2.status == "not in").sum()),
                    "reason": " | ".join(f"{int(o)}: {s} - {rs}" for o, s, rs in zip(g2.OBJECTID, g2.status, g2.reason)),
                    "check": note, "match_confidence": ", ".join(sorted(set(g2.match_confidence.dropna())))})
    P = pd.DataFrame(prj)

    # stations
    S = stations[["station_id", "station_name", "voltage_kv", "x_rd", "y_rd", "name_source", "origin",
                  "in_full_network", "used_by_OBJECTID", "note"]].copy()
    jn = p.get("juan_nodes_file")
    if jn:
        J = pd.read_csv(p["input_folder"] / jn, float_precision="round_trip")
        key = "node_id" if "node_id" in J.columns else "station_id"
        J["station_id"] = J[key].astype(str).str.replace("node:", "", regex=False)
        J = J.rename(columns={"x_rd": "juan_x_rd", "y_rd": "juan_y_rd"})[["station_id", "juan_x_rd", "juan_y_rd"]]
        S = S.merge(J, on="station_id", how="left")
        S["dist_to_juan_node_m"] = ((S.x_rd - S.juan_x_rd) ** 2 + (S.y_rd - S.juan_y_rd) ** 2) ** 0.5

    rules = pd.DataFrame({"rule": [
        "Data: Juan's 2030 network = full_network.csv (lines and cables). Stations per IP26 line from " + p["edges_workbook"] + ".",
        "not in: no edge between the from and to station (direct or through the via stations), e.g. a new station or a new route.",
        "partly: the route exists but not everything the project delivers: fewer circuits than '3e circuit' (3) / '3e en 4e circuit' (4); "
        "lijnverzwaring with a rating below the upgrade target (380/220 kV 4,000 A per IP2026 §7.4) or, at 150/110 kV, an upgrade that cannot be verified because no target rating is published (full_network.csv carries the standard 900 / 700 A); "
        "Verkabelen where the route is still an overhead line; or only some sections of a multi-station route exist.",
        "in: the route exists with the circuits, rating or cable type the project delivers. For 'nieuwe verbinding' and other types without "
        "a circuit rule, the existence of the route counts as in.",
        "Project (n_nummer): in = all its lines in; not in = none; otherwise partly. Duplicate features (include_in_network = no) are not counted.",
        f"expected_by_network_year: commissioning year (end year of N_ibn_jaar_ip2026) <= {year_cut}. Column 'check' flags projects expected "
        f"by {year_cut} that are not (fully) in full_network, and projects in full_network that come later.",
        "Station matching follows the station assignment of ip26_network_build / ip26_network_scenarios (geometry, project name, TenneT "
        "circuit IDs, IP2026 points). GNMS110 (Groningen Meerstad 110) and MDM380 (Middenmeer 380) are assumed, approximate locations "
        "(confirm from IP2026 projects A-1003051 and A-1003017).",
    ]})

    out = p["output_folder"] / p["output_file"]
    with pd.ExcelWriter(out, engine="openpyxl") as xw:
        write_df(xw, "Projects", P, {"n_projectnaam": 55, "reason": 100, "check": 45, "lines": 18}, "status")
        write_df(xw, "Lines", L, {"n_projectnaam": 55, "reason": 70, "from_station_name": 30, "to_station_name": 30,
                                  "full_network_edges": 60, "route_in_full_network": 24, "required": 28}, "status")
        write_df(xw, "Stations", S, {"station_name": 36, "origin": 30, "name_source": 30, "note": 80, "used_by_OBJECTID": 30})
        rules.to_excel(xw, sheet_name="Rules", index=False)
        xw.sheets["Rules"].column_dimensions["A"].width = 160
        for c in xw.sheets["Rules"]["A"]:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    print(f"Written: {out}")
    print("Projects:", P.status.value_counts().to_dict())
    print("Lines (excluding duplicates):", L[L.status != "duplicate"].status.value_counts().to_dict())
    return P, L


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
