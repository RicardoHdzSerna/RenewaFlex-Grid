"""
ip26_network_scenarios.py
=========================

Scenario version of ip26_network_build.py. Choose the parameter scenario below
(SCENARIO) or on the command line:

    python ip26_network_scenarios.py                    # uses SCENARIO below
    python ip26_network_scenarios.py q3                 # one scenario
    python ip26_network_scenarios.py all                # every scenario + comparison workbook
    python ip26_network_scenarios.py median other.yaml  # other config file

Scenarios (defined in config_scenarios.yaml, section 'scenarios'):
    median          r', x', b', rating = median of full_network.csv per kV and line/cable
    mean            same, average
    q1              same, first quartile (25th percentile)
    q3              same, third quartile (75th percentile)
    template        values of the Parameters tab of IP26_line_separate_sheet.xlsx
                    (x' and ratings; r' and b' are not in that file -> median)
    median_oldline  median, but lijnverzwaring rows use r', x', b' recalculated from
                    the old line in full_network.csv (old R/length, X/length, B/length)

Original description:

Turns the TenneT IP2026 line projects (IP26_line.xlsx) into network edges in the
format of full_network.csv and writes them to an Excel workbook with one tab per
werkzaamheden type (like IP26_line_separate_sheet.xlsx):

    1, Parameters, (blank), klantaansluiting, lijnverzwaring, nieuwe verbinding,
    stationsuitbreiding, Verkabelen, vervangen station, Stations, Station_match, Notes

Column order of every data tab:
    edge_id type from_node_id from_station_id from_station_name from_voltage_kv
    to_node_id to_station_id to_station_name to_voltage_kv resistance_ohm reactance_ohm
    resistance_pu reactance_pu susceptance_pu_half susceptance_pu_total edge_type
    length_m max_current_a sn_mva source
    OBJECTID bovengronds_ondergrond bestaand_nieuw provincie n_nummer n_projectnaam
    n_projectfase_ip n_werkzaamheden_ip n_miek trace N_ibn_jaar_ip2026
    [lijnverzwaring only: old line values from full_network.csv]
    kv Shape__Length n_circuits via_station_ids match_confidence match_note

Inputs (DATA folder, see input_folder in the config):
    IP26_line.xlsx                 TenneT IP2026 line export
    full_network.csv               existing network (station IDs/names, old line values)
    stations_tennet_arcgis.csv     TenneT station layer: STATIONID, name, RD coordinates
    ip26_line_endpoints.csv        path ends of every IP26 line (RD coordinates)
    IP26_point.xlsx                TenneT IP2026 point export (project points, x_coord/y_coord in RD New)

Usage:
    pip install pandas openpyxl pyyaml
    python ip26_network_build.py                    # uses config_network.yaml next to this file
    python ip26_network_build.py other_config.yaml
"""

import math
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# --------------------------------------------------------------------------- columns
SPEC_COLS = [
    "edge_id", "type", "from_node_id", "from_station_id", "from_station_name", "from_voltage_kv",
    "to_node_id", "to_station_id", "to_station_name", "to_voltage_kv",
    "resistance_ohm", "reactance_ohm", "resistance_pu", "reactance_pu",
    "susceptance_pu_half", "susceptance_pu_total", "edge_type", "length_m",
    "max_current_a", "sn_mva", "source",
]
INFO_COLS = [
    "OBJECTID", "bovengronds_ondergrond", "bestaand_nieuw", "provincie", "n_nummer",
    "n_projectnaam", "n_projectfase_ip", "n_werkzaamheden_ip", "n_miek", "trace",
    "N_ibn_jaar_ip2026",
]
# lijnverzwaring only: (group title, column name, key in the old-values dict)
OLD_COLS = [
    (None, "Voltage_level(kV)", "kv"),
    ("Old line values for Maximum Current Imax (A)", "max_current_a (A)", "max_current_a"),
    ("Old line values for Maximum Current Imax (A)", "sn_mva (MVA)", "sn_mva"),
    ("Old line values for Maximum Current Imax (A)", "Matched circuits", "circuits"),
    ("Old line vales for Dynamic line rating (DLR)", "DLRmin(A)", "dlr_min"),
    ("Old line vales for Dynamic line rating (DLR)", "DLRmax(A)", "dlr_max"),
    ("Old line values for Electrical Parameters", "Resistance_R(Ω)", "r_ohm"),
    ("Old line values for Electrical Parameters", "Reactance_X(Ω)", "x_ohm"),
    ("Old line values for Electrical Parameters", "Susceptance_B(μS)", "b_us"),
    ("Old line values for Electrical Parameters", "Length_(km)", "length_km"),
    ("Old line values for Electrical Parameters", "Comment", "comment"),
]
EXTRA_COLS = ["kv", "Shape__Length", "n_circuits", "n_circuits_basis", "include_in_network", "duplicate_of_OBJECTID",
              "via_station_ids", "from_name_source", "to_name_source", "match_confidence", "match_note"]
# parameters used per row (the electrical formulas of the row reference these cells)
PARAM_COLS = ["parameter_scenario", "r_ohm_per_km_used", "x_ohm_per_km_used", "b_uS_per_km_used",
              "rating_a_used", "parameter_basis"]
# columns of the original template IP26_line_separate_sheet (always the last four columns)
TPL_COLS = ["X model (\u2126)\n= L\u00b7x\u2032\u00b7\u221a3/N", "X standard (\u2126)\n= L\u00b7x\u2032/N",
            "Peak capacity (MVA)\n= N\u00b7cap", "Secure capacity (MW)\n= MVA\u00b7PF\u00b7RF"]

INPUT_COLS = ["OBJECTID", "bovengronds_ondergrond", "kv", "bestaand_nieuw", "provincie", "n_nummer",
              "n_projectnaam", "n_projectfase_ip", "n_werkzaamheden_ip", "n_miek", "trace",
              "N_ibn_jaar_ip2026", "Shape__Length"]

# =============================================================================
# CHOOSE THE SCENARIO HERE: median | mean | q1 | q3 | template | median_oldline | all
SCENARIO = "all"
CONFIG_FILE = "config_scenarios.yaml"
# =============================================================================

NAVY = PatternFill("solid", fgColor="1F3864")
GREY = PatternFill("solid", fgColor="E6E6E6")
INPUT_FILL = PatternFill("solid", fgColor="FFF2CC")
CALC_FILL = PatternFill("solid", fgColor="E2EFDA")
OLD_FILL = PatternFill("solid", fgColor="DDEBF7")
LOW_FILL = PatternFill("solid", fgColor="FCE4D6")
WHITE_BOLD = Font(bold=True, color="FFFFFF")
BOLD = Font(bold=True)

PARAM_SBASE_ROW = 5
PARAM_TYPES_HEADER_ROW = 9


# --------------------------------------------------------------------------- helpers
def load_config(path):
    path = Path(path).resolve()
    with open(path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    base = path.parent
    p = cfg["paths"]
    for key in ("input_folder", "output_folder"):
        folder = Path(p[key])
        p[key] = folder if folder.is_absolute() else (base / folder)
    return cfg


def kv_number(v):
    """'380kV' -> 380, 150 -> 150, None -> None"""
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return None
    m = re.search(r"\d+", str(v))
    return int(m.group()) if m else None


def station_kv(sid):
    m = re.search(r"(\d+)$", str(sid))
    return int(m.group(1)) if m else None


def station_code(sid):
    """'RLL380' -> 'RLL' (used in edge_id, like full_network.csv)"""
    return re.sub(r"\d+$", "", str(sid))


def clean(v):
    if v is None:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating,)):
        return float(v)
    return v


def edge_type_of(cfg, bo):
    s = str(bo or "").lower()
    for key, val in cfg["system"]["edge_type_map"].items():
        if s.startswith(key):
            return val
    return cfg["system"]["default_edge_type"]


# --------------------------------------------------------------------------- stations
SRC_OLD = "old line file (full_network.csv)"
SRC_MAP = "TenneT ArcGIS map (station layer)"
SRC_POINT = "IP2026 point file (new station)"
SRC_CUST = "project name (customer/DSO substation)"
SRC_CFG = "config (assumed)"


class StationRegistry:
    """IDs, names, voltages, coordinates and origin of every station."""

    def __init__(self, cfg, fn, arc, points=None):
        self.data = {}
        # 1) ArcGIS station layer
        for r in arc.itertuples():
            nm = clean(r.station_name)
            self.data[r.station_id] = dict(id=r.station_id, name=nm or r.station_id,
                                           kv=station_kv(r.station_id), x=r.x_rd, y=r.y_rd,
                                           origin="TenneT ArcGIS station layer", note="",
                                           name_source=SRC_MAP if nm else None)
        # 2) full_network.csv: its names take priority (compatibility with the old file)
        fn_names = {}
        for side in ("from", "to"):
            for sid, name, kv in fn[[f"{side}_station_id", f"{side}_station_name", f"{side}_voltage_kv"]].itertuples(index=False):
                fn_names.setdefault(str(sid), (name, kv))
        self.in_fn = set(fn_names)
        for sid, (name, kv) in fn_names.items():
            if sid in self.data:
                if isinstance(name, str) and name and name != sid:
                    self.data[sid]["name"] = name
                    self.data[sid]["name_source"] = SRC_OLD
                self.data[sid]["origin"] = "full_network.csv + TenneT ArcGIS"
            else:
                real = isinstance(name, str) and name and name != sid
                self.data[sid] = dict(id=sid, name=name if real else sid,
                                      kv=clean(kv) or station_kv(sid), x=None, y=None,
                                      origin="full_network.csv", note="",
                                      name_source=SRC_OLD if real else None)
        # 3) extra stations from the config (new stations, customers, coordinates for fn-only)
        for e in cfg.get("extra_stations") or []:
            sid = e["id"]
            d = self.data.get(sid, dict(id=sid, origin=None))
            x, y, pinfo = e.get("x"), e.get("y"), None
            if e.get("point") is not None and points is not None:
                hit = points[points.OBJECTID == int(e["point"])]
                if hit.empty:
                    raise KeyError(f"extra station {sid}: point {e['point']} not in the point file")
                h = hit.iloc[0]
                x, y = float(h.x_coord), float(h.y_coord)     # coordinates from IP26_point.xlsx
                pinfo = f"{int(h.OBJECTID)}: {h.projectnaam} ({h.werkzaamheden})"
            # Name priority: 1) old line file full_network.csv, 2) TenneT ArcGIS map,
            # 3) config (new station from the IP2026 point file, customer, assumed).
            if d.get("name_source") is None:
                d["name"] = e["name"]
                d["name_source"] = {"ip2026_point": SRC_POINT, "customer": SRC_CUST}.get(
                    e.get("origin"), SRC_CFG)
                if sid in self.in_fn:
                    d["name_source"] += " (old line file has only the ID)"
            d.update(kv=e.get("kv") or station_kv(sid), x=x, y=y, note=e.get("note", ""), point=pinfo)
            origin = {"full_network": "full_network.csv", "ip2026_point": "IP2026 point layer (new station)",
                      "customer": "customer/DSO substation (project name)",
                      "assumed": "assumed (see note)"}.get(e.get("origin"), e.get("origin"))
            if sid in self.in_fn:
                origin = "full_network.csv" + (" + TenneT ArcGIS" if "ArcGIS" in str(d.get("origin")) else "")
            d["origin"] = origin
            self.data[sid] = d

    def get(self, sid):
        if sid is None:
            return None
        if sid not in self.data:
            raise KeyError(f"station '{sid}' is not in full_network.csv, the ArcGIS station list or extra_stations")
        return self.data[sid]

    def with_coords(self, kv=None):
        rows = [d for d in self.data.values() if d["x"] is not None and (kv is None or d["kv"] == kv)]
        return rows


def path_ends(endpoints, oid):
    e = endpoints[endpoints.OBJECTID == oid]
    pts = []
    for r in e.itertuples():
        pts.append((r.x_start, r.y_start))
        pts.append((r.x_end, r.y_end))
    return pts


def terminals(pts, tol=300.0):
    """Cluster the path ends; ends used once (dangling) are the line terminals."""
    clusters = []
    for x, y in pts:
        for c in clusters:
            if math.hypot(c["x"] - x, c["y"] - y) < tol:
                c["n"] += 1
                break
        else:
            clusters.append({"x": x, "y": y, "n": 1})
    t = [c for c in clusters if c["n"] == 1]
    return t or clusters


def nearest(stations, x, y):
    best, bd = None, None
    for s in stations:
        d = math.hypot(s["x"] - x, s["y"] - y)
        if bd is None or d < bd:
            best, bd = s, d
    return best, bd


def dist_to_line(st, pts):
    if st is None or st["x"] is None or not pts:
        return None
    return min(math.hypot(st["x"] - x, st["y"] - y) for x, y in pts)


def project_points(points, row, ends):
    """IP26 points with the same project number (n_nummer = nummer) and their distance to the line."""
    out = {"project_point": None, "project_point_werkzaamheden": None, "project_point_dist_to_line_end_m": None}
    if points is None or pd.isna(row.get("n_nummer")):
        return out
    hit = points[points.nummer == row["n_nummer"]]
    if hit.empty:
        return out
    txt, wz, dist = [], [], []
    for h in hit.itertuples():
        txt.append(f"{h.OBJECTID}: {h.projectnaam}")
        wz.append(str(h.werkzaamheden))
        if ends:
            dist.append(str(round(min(math.hypot(h.x_coord - x, h.y_coord - y) for x, y in ends))))
    out.update(project_point="; ".join(txt), project_point_werkzaamheden="; ".join(wz),
               project_point_dist_to_line_end_m="; ".join(dist) or None)
    return out


# --------------------------------------------------------------------------- old values
def build_edge_index(fn):
    idx = {}
    lines = fn[fn["type"].isin(["line", "cable"])]
    for r in lines.itertuples(index=False):
        key = frozenset((r.from_station_id, r.to_station_id))
        idx.setdefault(key, []).append(r)
    return idx


def circuit_tag(edge_id):
    """'branch:RLL-ZVL380 W' / 'branch:manual:RLL380-ZVL380-W' / '...150 W:seg2' -> 'W'"""
    s = re.sub(r":seg\d+$", "", str(edge_id))
    return re.split(r"[ \-]", s)[-1]


def old_values(edge_index, chain, kv):
    """Series sum over the chain; per circuit (first circuit of every section).
    full_network.csv sometimes holds the same circuit twice (e.g. 'branch:RLL-ZVL380 W' and
    'branch:manual:RLL380-ZVL380-W'); circuits are counted once per circuit letter and the
    non-'manual' edge is preferred."""
    sections = []
    for a, b in zip(chain[:-1], chain[1:]):
        edges = edge_index.get(frozenset((a, b)))
        if not edges:
            return None
        edges = sorted(edges, key=lambda e: ("manual" in e.edge_id, e.edge_id))
        uniq = {}
        for e in edges:
            uniq.setdefault(circuit_tag(e.edge_id), e)
        sections.append(list(uniq.values()))
    zbase = kv ** 2 / 100.0
    r = sum(float(s[0].resistance_ohm) for s in sections)
    x = sum(float(s[0].reactance_ohm) for s in sections)
    b_us = sum(float(s[0].susceptance_pu_total) / float(s[0].from_voltage_kv) ** 2 * 100.0 * 1e6
               for s in sections if not pd.isna(s[0].susceptance_pu_total))
    length = sum(float(s[0].length_m) for s in sections if not pd.isna(s[0].length_m)) / 1000.0
    imax = min(float(s[0].max_current_a) for s in sections)
    circuits = min(len(s) for s in sections)
    ids = "; ".join(e.edge_id for s in sections for e in s)
    return dict(kv=kv, max_current_a=imax, sn_mva=math.sqrt(3) * kv * imax / 1000.0, circuits=circuits,
                dlr_min=None, dlr_max=None, r_ohm=round(r, 6), x_ohm=round(x, 6), b_us=round(b_us, 4),
                length_km=round(length, 4),
                comment=f"full_network.csv: {ids}" + ("" if len(sections) == 1 else
                                                       f" (series of {len(sections)} sections, values per circuit)"))


def find_old(edge_index, a, cfg_row, kv):
    frm, to = a.get("from"), a.get("to")
    if not frm or not to:
        return None
    # 1) direct edge, 2) chain through via stations, 3) chain given in the config
    tries = [[frm, to]]
    via = a.get("via") or []
    if via:
        tries.append([frm, *via, to])
    if cfg_row.get("old_chain"):
        if cfg_row.get("old_chain_first"):
            tries.insert(0, list(cfg_row["old_chain"]))
        else:
            tries.append(list(cfg_row["old_chain"]))
    for chain in tries:
        res = old_values(edge_index, chain, kv)
        if res:
            return res
    return dict(kv=kv, comment="No edge between these stations in full_network.csv (new station or new route).")


# --------------------------------------------------------------------------- per-row calculation
def line_type_rows(cfg):
    """(kv, edge_type) -> (Parameters row, dict)"""
    out = {}
    for i, t in enumerate(cfg["line_types"]):
        out[(int(t["kv"]), t["edge_type"])] = (PARAM_TYPES_HEADER_ROW + 1 + i, t)
    return out


def reinforced_rows(cfg):
    start = PARAM_TYPES_HEADER_ROW + 1 + len(cfg["line_types"]) + 3
    out = {}
    for i, (kv, v) in enumerate((cfg.get("reinforced_max_current_a") or {}).items()):
        out[int(kv)] = (start + i, v)
    return out, start - 1


def compute(cfg, row, a, reg, ends, lt_rows, rf_rows, circ, old=None):
    oid = int(row["OBJECTID"])
    kv = kv_number(row["kv"])
    etype = edge_type_of(cfg, row["bovengronds_ondergrond"])
    n = int(circ["n"])
    length = clean(row["Shape__Length"])
    frm, to = reg.get(a.get("from")), reg.get(a.get("to"))
    rec = {c: None for c in SPEC_COLS}
    for c in INFO_COLS:
        rec[c] = clean(row.get(c))
    rec.update(kv=clean(row["kv"]), Shape__Length=length, n_circuits=n, n_circuits_basis=circ["basis"],
               include_in_network=circ["include"], duplicate_of_OBJECTID=circ["dup_of"],
               via_station_ids=", ".join(a.get("via") or []) or None,
               match_confidence=a.get("conf"), match_note=a.get("note"))
    has_data = bool(a.get("from") or a.get("to") or length)
    rec["type"] = etype if has_data else None
    rec["edge_type"] = etype if has_data else None
    if frm:
        rec["from_name_source"] = frm.get("name_source")
        rec.update(from_node_id=f"node:{frm['id']}", from_station_id=frm["id"],
                   from_station_name=frm["name"], from_voltage_kv=frm["kv"])
    if to:
        rec["to_name_source"] = to.get("name_source")
        rec.update(to_node_id=f"node:{to['id']}", to_station_id=to["id"],
                   to_station_name=to["name"], to_voltage_kv=to["kv"])
    m = cfg["matching"]
    if frm and to:
        ekv = frm["kv"] if frm["kv"] == to["kv"] else f"{frm['kv']}-{to['kv']}"
        rec["edge_id"] = f"{m['edge_id_prefix']}{station_code(frm['id'])}-{station_code(to['id'])}{ekv} " \
                         + m["edge_id_suffix"].format(oid=oid)
    # electrical values
    calc = {}
    key = (kv, etype)
    sc = cfg["_scenario"]
    rec["parameter_scenario"] = sc["name"]
    if kv and length and key in lt_rows and frm and to:
        prow, t = lt_rows[key]
        lijn = str(row.get("n_werkzaamheden_ip") or "").strip().lower() == "lijnverzwaring"
        rated = t["max_current_a"]
        rating_cell = f"Parameters!$G${prow}"
        if lijn and kv in rf_rows and rf_rows[kv][1] and rf_rows[kv][1].get("value") is not None:
            rated = rf_rows[kv][1]["value"]
            rating_cell = f"Parameters!$C${rf_rows[kv][0]}"
        # per-km parameters of this row: line type of the scenario, or the old line
        par = dict(r=t["r_ohm_per_km"], x=t["x_ohm_per_km"], b=t["b_uS_per_km"],
                   cells=dict(r=f"Parameters!$D${prow}", x=f"Parameters!$E${prow}", b=f"Parameters!$F${prow}"),
                   basis=f"{sc['label']}: {kv} kV {etype} (Parameters row {prow})")
        mode = sc.get("lijnverzwaring_from_old_line")
        if lijn and mode and old and old.get("length_km"):
            ok = old["length_km"] > 0 and old.get("r_ohm") is not None
            if ok and mode == "per_km":
                par = dict(r=old["r_ohm"] / old["length_km"], x=old["x_ohm"] / old["length_km"],
                           b=old["b_us"] / old["length_km"], cells=None,
                           basis=f"old line (full_network.csv), per km = old R, X, B / old length "
                                 f"{old['length_km']:.3f} km, applied to the IP26 length; {old['comment']}")
            elif ok and mode == "total":
                km_ip = length / 1000.0
                par = dict(r=old["r_ohm"] / km_ip, x=old["x_ohm"] / km_ip, b=old["b_us"] / km_ip, cells=None,
                           basis=f"old line (full_network.csv) totals kept (per km scaled to the IP26 length so "
                                 f"that R, X, B equal the old circuit); {old['comment']}")
        elif lijn and mode:
            par["basis"] += "; no old line found in full_network.csv, scenario values used"
        rec.update(r_ohm_per_km_used=par["r"], x_ohm_per_km_used=par["x"], b_uS_per_km_used=par["b"],
                   rating_a_used=rated, parameter_basis=par["basis"])
        rec["_par_cells"] = par["cells"]
        sbase = cfg["system"]["s_base_mva"]
        zbase = kv ** 2 / sbase
        km = length / 1000.0
        r = par["r"] * km / n
        x = par["x"] * km / n
        b_tot_pu = par["b"] * 1e-6 * km * n * zbase
        imax = rated * n
        calc = dict(resistance_ohm=r, reactance_ohm=x, resistance_pu=r / zbase, reactance_pu=x / zbase,
                    susceptance_pu_total=b_tot_pu, susceptance_pu_half=b_tot_pu / 2,
                    length_m=length, max_current_a=imax, sn_mva=math.sqrt(3) * kv * imax / 1000.0)
        rec.update(calc)
        tp = cfg["template_parameters"]
        x_tpl = par["x"] * km                   # x′ used for this row (same as reactance_ohm)
        peak = n * tp["capacity_per_circuit_mva"]["value"] if kv in tp["capacity_applies_to_kv"] else calc["sn_mva"]
        rec[TPL_COLS[0]] = x_tpl * math.sqrt(3) / n
        rec[TPL_COLS[1]] = x_tpl / n
        rec[TPL_COLS[2]] = peak
        rec[TPL_COLS[3]] = peak * tp["power_factor"]["value"] * tp["reserve_factor"]["value"]
        rec["_tpl_cap"] = kv in tp["capacity_applies_to_kv"]
        rec["_prow"] = prow
        rec["_rating_cell"] = rating_cell
        src_rating = "reinforced rating" if lijn and rating_cell.startswith("Parameters!$C") else "rating"
        rec["source"] = (f"IP2026 (TenneT ArcGIS IP26_line {oid}); scenario {sc['name']}; R/X/B: "
                         f"{'old line' if par['cells'] is None else f'Parameters {kv} kV {etype}'}, "
                         f"{src_rating}; stations: {a.get('conf')}")
    else:
        rec["length_m"] = length
        why = "no stations" if not (frm and to) else ("no length" if not length else f"no line type {key}")
        rec["source"] = f"IP2026 (TenneT ArcGIS IP26_line {oid}); not calculated ({why})"
    # match log
    rec["_log"] = dict(from_dist=dist_to_line(frm, ends), to_dist=dist_to_line(to, ends))
    return rec


# --------------------------------------------------------------------------- circuits
def fn_circuit_tags(edge_index, a, cfg_row, ignore=()):
    """Circuit letters of the existing route in full_network.csv (direct edge plus the chain
    through the via stations); old_chain_first: only the configured old_chain."""
    def tags_of(chain):
        secs = []
        for x, y in zip(chain[:-1], chain[1:]):
            edges = edge_index.get(frozenset((x, y)))
            if not edges:
                return None
            tags = {circuit_tag(e.edge_id) for e in edges} - set(ignore)
            if not tags:
                return None
            secs.append(tags)
        return min(secs, key=len) if secs else None       # circuits running the whole chain
    frm, to = a.get("from"), a.get("to")
    if not frm or not to:
        return None, None
    if cfg_row.get("old_chain_first") and cfg_row.get("old_chain"):
        t = tags_of(list(cfg_row["old_chain"]))
        return (t, "old_chain") if t else (None, None)
    found, how = set(), []
    t = tags_of([frm, to])
    if t:
        found |= t
        how.append("direct")
    if a.get("via"):
        t = tags_of([frm, *a["via"], to])
        if t:
            found |= t
            how.append("via")
    if not found and cfg_row.get("old_chain"):
        t = tags_of(list(cfg_row["old_chain"]))
        if t:
            found |= t
            how.append("old_chain")
    return (found, "+".join(how)) if found else (None, None)


def determine_circuits(cfg, df, assign_of, edge_index):
    """n_circuits per row. Rules, in order (config 'circuits'):
    1) override per OBJECTID; 2) project name ('3e circuit' = 1, '3e en 4e circuit' = 2, 'N circuits');
    3) existing route (lijnverzwaring, Verkabelen or 'bestaande verbinding'): number of circuits of that
       route in full_network.csv; 4) default per kV.
    Then per project and station pair: features with identical geometry are duplicates (kept, flagged
    include_in_network = no); if a project has k different features between the same stations, the
    project circuits are divided over them (N / k)."""
    cc = cfg.get("circuits") or {}
    out = {}
    for _, row in df.iterrows():
        oid = int(row["OBJECTID"])
        a = assign_of[oid]
        kv = kv_number(row["kv"])
        name = str(row.get("n_projectnaam") or "")
        wz = str(row.get("n_werkzaamheden_ip") or "").strip()
        bn = str(row.get("bestaand_nieuw") or "").strip()
        n, basis = None, None
        if oid in (cc.get("override") or {}):
            n, basis = cc["override"][oid], "config override"
        if n is None:
            for rule in cc.get("name_rules") or []:
                m = re.search(rule["pattern"], name, flags=re.I)
                if m:
                    n = int(m.group(1)) if rule.get("circuits") == "group" else int(rule["circuits"])
                    basis = f"project name: '{m.group(0)}'"
                    break
        if n is None and (wz in (cc.get("existing_route_types") or []) or bn == "bestaande verbinding"):
            tags, how = fn_circuit_tags(edge_index, a, (cfg.get("assignments") or {}).get(oid, {}),
                                        cc.get("ignore_circuit_ids") or [])
            if tags:
                n = len(tags)
                basis = f"existing route in full_network.csv ({how}): circuits {', '.join(sorted(tags))}"
        if n is None:
            n = int((cc.get("default_by_kv") or {}).get(kv, cfg.get("default_circuits", 1)))
            basis = f"default for {kv} kV (config circuits.default_by_kv)"
        out[oid] = {"n": n, "basis": basis, "include": "yes", "dup_of": None}
    # duplicates and splitting over features of the same project between the same stations
    groups = {}
    for _, row in df.iterrows():
        oid = int(row["OBJECTID"])
        a = assign_of[oid]
        if pd.isna(row.get("n_nummer")) or not a.get("from"):
            continue
        groups.setdefault((row["n_nummer"], a.get("from"), a.get("to")), []).append(
            (oid, round(float(row["Shape__Length"] or 0))))
    for key, feats in groups.items():
        if len(feats) < 2:
            continue
        first_of = {}
        for oid, ln in sorted(feats):
            if ln in first_of:
                out[oid].update(include="no", dup_of=first_of[ln],
                                basis=out[oid]["basis"] + f"; identical geometry to {first_of[ln]} (duplicate feature)")
            else:
                first_of[ln] = oid
        k = len(first_of)
        if k > 1:
            for oid in first_of.values():
                n_tot = out[oid]["n"]
                if n_tot % k == 0 and (oid not in ((cc.get("override") or {}))):
                    out[oid].update(n=n_tot // k,
                                    basis=out[oid]["basis"] + f"; {n_tot} circuits drawn as {k} separate features: {n_tot // k} each")
            for oid, ln in feats:
                if out[oid]["include"] == "no":
                    out[oid]["n"] = out[first_of[ln]]["n"]
    return out


# --------------------------------------------------------------------------- scenarios
def network_statistics(fn, stat):
    """r' (ohm/km), x' (ohm/km), b' (uS/km) and max_current_a per (kV, line/cable) of full_network.csv."""
    e = fn[fn["type"].isin(["line", "cable"]) & (fn["length_m"] > 0)].copy()
    km = e["length_m"] / 1000.0
    zbase = e["from_voltage_kv"] ** 2 / 100.0
    e["r"] = e["resistance_ohm"] / km
    e["x"] = e["reactance_ohm"] / km
    e["b"] = e["susceptance_pu_total"] / zbase / km * 1e6
    g = e.groupby(["from_voltage_kv", "type"])[["r", "x", "b", "max_current_a"]]
    funcs = {"median": g.median, "mean": g.mean,
             "q1": lambda: g.quantile(0.25), "q3": lambda: g.quantile(0.75)}
    if stat not in funcs:
        raise ValueError(f"unknown statistic '{stat}' (median, mean, q1, q3)")
    res = funcs[stat]()
    counts = e.groupby(["from_voltage_kv", "type"]).size()
    return res, counts


def read_template(cfg, inp):
    t = cfg["template_workbook"]
    from openpyxl import load_workbook
    ws = load_workbook(inp / t["file"], data_only=True)[t["sheet"]]
    return {k: ws[c].value for k, c in t["cells"].items()}


def apply_scenario(cfg, scenario, fn, inp):
    """Builds cfg['line_types'] (and, for 'template', the ratings and template parameters) for the scenario."""
    if scenario not in cfg["scenarios"]:
        raise ValueError(f"scenario '{scenario}' is not in the config ({', '.join(cfg['scenarios'])})")
    sc = dict(cfg["scenarios"][scenario], name=scenario)
    stat = sc.get("statistic", "median")
    vals, counts = network_statistics(fn, stat)
    label = {"median": "median", "mean": "average", "q1": "first quartile (Q1)", "q3": "third quartile (Q3)"}[stat]
    over = cfg.get("rating_overrides") or {}
    types = []
    for kv, et in [(380, "line"), (380, "cable"), (220, "line"), (220, "cable"),
                   (150, "line"), (150, "cable"), (110, "line"), (110, "cable")]:
        v = vals.loc[(kv, et)]
        rating = float(v["max_current_a"])
        rsrc = f"{label} of full_network.csv"
        key = f"{kv}_{et}"
        if sc.get("use_rating_overrides", True) and key in over:
            rating, rsrc = over[key]["value"], over[key]["source"]
        types.append({"kv": kv, "edge_type": et, "r_ohm_per_km": round(float(v["r"]), 6),
                      "x_ohm_per_km": round(float(v["x"]), 6), "b_uS_per_km": round(float(v["b"]), 4),
                      "max_current_a": round(rating, 2),
                      "source": f"r', x', b': {label} of {int(counts.loc[(kv, et)])} {kv} kV {et}s in full_network.csv. "
                                f"Rating: {rsrc}."})
    sc["label"] = f"{label} of full_network.csv"
    if sc.get("source") == "template":
        tv = read_template(cfg, inp)
        fn_label = sc["label"]
        sc["label"] = "IP26_line_separate_sheet.xlsx Parameters"
        m = cfg["template_workbook"]["mapping"]
        for t in types:
            k = f"{t['kv']}_{t['edge_type']}"
            xcell, icell = m["x"][k], m["rating"][k]
            t["x_ohm_per_km"] = tv[xcell]
            t["max_current_a"] = tv[icell]
            t["source"] = (f"x' = {tv[xcell]} ({cfg['template_workbook']['cells'][xcell]} of the template), "
                           f"rating = {tv[icell]} A ({cfg['template_workbook']['cells'][icell]}); r' and b' are not "
                           f"in the template: {fn_label} ({int(counts.loc[(t['kv'], t['edge_type'])])} edges).")
        for kv in list(cfg.get("reinforced_max_current_a") or {}):
            icell = m["rating"][f"{kv}_line"]
            cfg["reinforced_max_current_a"][kv] = {"value": tv[icell], "source": f"Template {cfg['template_workbook']['cells'][icell]}."}
        tp = cfg["template_parameters"]
        for k, cell in (("capacity_per_circuit_mva", "cap"), ("power_factor", "pf"), ("reserve_factor", "rf")):
            tp[k]["value"] = tv[cell]
    cfg["line_types"] = types
    cfg["_scenario"] = sc
    return sc


def write_comparison(cfg, results):
    """One workbook comparing the scenarios: per OBJECTID R, X, B, rating and MVA."""
    p = cfg["paths"]
    rows = []
    for name, recs in results.items():
        for r in recs:
            rows.append({"scenario": name, "OBJECTID": r["OBJECTID"], "edge_id": r.get("edge_id"),
                         "n_werkzaamheden_ip": r.get("n_werkzaamheden_ip"), "include_in_network": r.get("include_in_network"),
                         "resistance_ohm": r.get("resistance_ohm"), "reactance_ohm": r.get("reactance_ohm"),
                         "susceptance_pu_total": r.get("susceptance_pu_total"), "max_current_a": r.get("max_current_a"),
                         "sn_mva": r.get("sn_mva")})
    d = pd.DataFrame(rows)
    out = p["output_folder"] / cfg["paths"].get("comparison_file", "IP26_scenario_comparison.xlsx")
    with pd.ExcelWriter(out) as xw:
        for col in ("reactance_ohm", "resistance_ohm", "susceptance_pu_total", "max_current_a", "sn_mva"):
            piv = d.pivot_table(index=["OBJECTID", "edge_id", "n_werkzaamheden_ip", "include_in_network"],
                                columns="scenario", values=col, aggfunc="first")[list(results)]
            piv.reset_index().to_excel(xw, sheet_name=col[:31], index=False)
        tot = d[d.include_in_network == "yes"].groupby("scenario")[["resistance_ohm", "reactance_ohm", "sn_mva"]].sum()
        tot.loc[list(results)].reset_index().to_excel(xw, sheet_name="totals", index=False)
    print(f"Written: {out}")


# --------------------------------------------------------------------------- workbook
def write_parameters(wb, cfg):
    ws = wb.create_sheet("Parameters")
    ws["B1"] = f"Parameters for the IP26 network edges - scenario: {cfg['_scenario']['name']}"
    ws["B1"].font = Font(bold=True, size=14)
    ws["B2"] = ("All electrical formulas in the data tabs reference these cells (output_mode: formulas). "
                "Change a value here and everything recalculates.")
    ws["B2"].font = Font(italic=True, size=10)
    for j, h in enumerate(["Parameter", "Value", "Unit", "Source / comment"]):
        c = ws.cell(4, 2 + j, h)
        c.font, c.fill = WHITE_BOLD, NAVY
    ws.cell(PARAM_SBASE_ROW, 2, "Base power Sbase")
    c = ws.cell(PARAM_SBASE_ROW, 3, cfg["system"]["s_base_mva"])
    c.font, c.fill = Font(color="0000FF"), INPUT_FILL
    ws.cell(PARAM_SBASE_ROW, 4, "MVA")
    ws.cell(PARAM_SBASE_ROW, 5, "Per-unit base of full_network.csv (Zbase = kV² / Sbase).")

    ws.cell(PARAM_TYPES_HEADER_ROW - 1, 2, "Electrical parameters per circuit, by voltage level and edge type - "
            + cfg["_scenario"]["label"]).font = Font(bold=True, size=12)
    ws.cell(PARAM_TYPES_HEADER_ROW - 1, 8, cfg["_scenario"]["description"]).font = Font(italic=True)
    heads = ["Voltage (kV)", "edge_type", "r′ (Ω/km)", "x′ (Ω/km)", "b′ (µS/km)", "max_current_a (A)", "Source / comment"]
    for j, h in enumerate(heads):
        c = ws.cell(PARAM_TYPES_HEADER_ROW, 2 + j, h)
        c.font, c.fill = WHITE_BOLD, NAVY
    for i, t in enumerate(cfg["line_types"]):
        r = PARAM_TYPES_HEADER_ROW + 1 + i
        vals = [t["kv"], t["edge_type"], t["r_ohm_per_km"], t["x_ohm_per_km"], t["b_uS_per_km"], t["max_current_a"], t.get("source", "")]
        for j, v in enumerate(vals):
            c = ws.cell(r, 2 + j, v)
            if 2 <= j <= 5:
                c.font, c.fill = Font(color="0000FF"), INPUT_FILL
    rf, hdr = reinforced_rows(cfg)
    ws.cell(hdr - 1, 2, "Rating after reinforcement (rows of type lijnverzwaring)").font = Font(bold=True, size=12)
    for j, h in enumerate(["Voltage (kV)", "max_current_a (A)", "Unit", "Source / comment"]):
        c = ws.cell(hdr, 2 + j, h)
        c.font, c.fill = WHITE_BOLD, NAVY
    for kv, (r, v) in rf.items():
        ws.cell(r, 2, kv)
        c = ws.cell(r, 3, v.get("value") if v else None)
        c.font, c.fill = Font(color="0000FF"), INPUT_FILL
        ws.cell(r, 4, "A")
        ws.cell(r, 5, (v or {}).get("source", ""))
    for col, w in {"A": 3, "B": 38, "C": 14, "D": 12, "E": 12, "F": 12, "G": 17, "H": 110}.items():
        ws.column_dimensions[col].width = w
    ws.cell(hdr + len(rf) + 2, 2, "Formulas (per row, n = n_circuits):").font = BOLD
    lines = ["resistance_ohm = r′ × length_m/1000 / n", "reactance_ohm = x′ × length_m/1000 / n",
             "resistance_pu = resistance_ohm / (kV² / Sbase)", "reactance_pu = reactance_ohm / (kV² / Sbase)",
             "susceptance_pu_total = b′×10⁻⁶ × length_m/1000 × n × kV² / Sbase", "susceptance_pu_half = susceptance_pu_total / 2",
             "max_current_a = rating × n", "sn_mva = √3 × kV × max_current_a / 1000"]
    for i, t in enumerate(lines):
        ws.cell(hdr + len(rf) + 3 + i, 2, t)
    # parameters of the original template (last four columns of every data tab)
    tr = template_rows(cfg)
    tp = cfg["template_parameters"]
    ws.cell(tr["header"] - 1, 2, "Parameters of the original template IP26_line_separate_sheet "
            "(columns X model, X standard, Peak capacity, Secure capacity)").font = Font(bold=True, size=12)
    for j, h in enumerate(["Parameter", "Value", "Unit", "Source / comment"]):
        c = ws.cell(tr["header"], 2 + j, h)
        c.font, c.fill = WHITE_BOLD, NAVY
    for key, rowno in (("capacity_per_circuit_mva", tr["cap"]),
                       ("power_factor", tr["pf"]), ("reserve_factor", tr["rf"])):
        v = tp[key]
        ws.cell(rowno, 2, v["label"])
        c = ws.cell(rowno, 3, v["value"])
        c.font, c.fill = Font(color="0000FF"), INPUT_FILL
        ws.cell(rowno, 4, v["unit"])
        ws.cell(rowno, 5, v["source"])
    ws.cell(tr["rf"] + 2, 2, "L = Shape__Length / 1000 (km), N = n_circuits, x′ = column E of the table "
            "'Electrical parameters per circuit' for the row's voltage and edge type (so X standard = reactance_ohm "
            "and X model = √3 × reactance_ohm). Peak capacity = N × cap for "
            f"{', '.join(map(str, tp['capacity_applies_to_kv']))} kV; for other voltages Peak capacity = sn_mva "
            "(the template has no capacity value for them).")


def template_rows(cfg):
    _, hdr = reinforced_rows(cfg)
    n_rf = len(cfg.get("reinforced_max_current_a") or {})
    start = hdr + n_rf + 3 + 8 + 3          # after the formula list
    return {"header": start, "cap": start + 1, "pf": start + 2, "rf": start + 3}


def columns_for(lijn):
    cols = SPEC_COLS + INFO_COLS
    if lijn:
        cols = cols + [f"old:{k}" for _, _, k in OLD_COLS]
    return cols + EXTRA_COLS + PARAM_COLS + TPL_COLS


def write_data_sheet(wb, name, recs, cfg, lijn=False):
    ws = wb.create_sheet(name)
    cols = columns_for(lijn)
    L = {c: get_column_letter(i + 1) for i, c in enumerate(cols)}
    hdr_rows = 2 if lijn else 1
    # headers
    for i, c in enumerate(cols):
        cell = ws.cell(1, i + 1)
        if c.startswith("old:"):
            grp, sub, _ = next(o for o in OLD_COLS if f"old:{o[2]}" == c)
            ws.cell(2, i + 1, sub).font = BOLD
            ws.cell(2, i + 1).fill = OLD_FILL
            ws.cell(2, i + 1).alignment = Alignment(wrap_text=True, vertical="top")
            if grp:
                cell.value = grp
            else:
                cell.value = sub
            cell.fill = OLD_FILL
        else:
            target = ws.cell(2, i + 1) if lijn else cell   # lijnverzwaring: names in row 2, groups in row 1
            target.value = c
            target.fill = GREY
            target.font = BOLD
            target.alignment = Alignment(wrap_text=True, vertical="top")
            cell.fill = GREY
        cell.font = BOLD
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    if lijn:  # merge group titles
        groups = {}
        for i, c in enumerate(cols):
            if c.startswith("old:"):
                grp = next(o for o in OLD_COLS if f"old:{o[2]}" == c)[0]
                if grp:
                    groups.setdefault(grp, []).append(i + 1)
        for grp, idx in groups.items():
            ws.merge_cells(start_row=1, start_column=min(idx), end_row=1, end_column=max(idx))
    mode = cfg.get("output_mode", "formulas")
    sb = f"Parameters!$C${PARAM_SBASE_ROW}"
    for k, rec in enumerate(recs):
        r = hdr_rows + 1 + k
        for c in cols:
            if c.startswith("old:"):
                v = (rec.get("_old") or {}).get(c[4:])
            else:
                v = rec.get(c)
            ws.cell(r, cols.index(c) + 1, clean(v))
        if mode == "formulas" and rec.get("_prow"):
            p = rec["_prow"]
            R, F, N = f"{L['length_m']}{r}", f"{L['from_voltage_kv']}{r}", f"{L['n_circuits']}{r}"
            K, Lx, P, S = (f"{L['resistance_ohm']}{r}", f"{L['reactance_ohm']}{r}",
                           f"{L['susceptance_pu_total']}{r}", f"{L['max_current_a']}{r}")
            RP, XP, BP, IP = (f"{L['r_ohm_per_km_used']}{r}", f"{L['x_ohm_per_km_used']}{r}",
                              f"{L['b_uS_per_km_used']}{r}", f"{L['rating_a_used']}{r}")
            pc = rec.get("_par_cells")
            if pc:   # live link to the Parameters tab; old-line rows keep their values
                ws.cell(r, cols.index("r_ohm_per_km_used") + 1, "=" + pc["r"])
                ws.cell(r, cols.index("x_ohm_per_km_used") + 1, "=" + pc["x"])
                ws.cell(r, cols.index("b_uS_per_km_used") + 1, "=" + pc["b"])
            ws.cell(r, cols.index("rating_a_used") + 1, "=" + rec["_rating_cell"])
            f = {
                "resistance_ohm": f"={RP}*{R}/1000/{N}",
                "reactance_ohm": f"={XP}*{R}/1000/{N}",
                "resistance_pu": f"={K}/({F}^2/{sb})",
                "reactance_pu": f"={Lx}/({F}^2/{sb})",
                "susceptance_pu_total": f"={BP}*1E-6*{R}/1000*{N}*{F}^2/{sb}",
                "susceptance_pu_half": f"={P}/2",
                "max_current_a": f"={IP}*{N}",
                "sn_mva": f"=SQRT(3)*{F}*{S}/1000",
            }
            tr = template_rows(cfg)
            T = f"{L['sn_mva']}{r}"
            Q = f"{L[TPL_COLS[2]]}{r}"
            f[TPL_COLS[0]] = f"=({R}/1000)*{XP}*SQRT(3)/{N}"
            f[TPL_COLS[1]] = f"=({R}/1000)*{XP}/{N}"
            f[TPL_COLS[2]] = (f"={N}*Parameters!$C${tr['cap']}" if rec.get("_tpl_cap") else f"={T}")
            f[TPL_COLS[3]] = f"={Q}*Parameters!$C${tr['pf']}*Parameters!$C${tr['rf']}"
            for c, formula in f.items():
                ws.cell(r, cols.index(c) + 1, formula)
        for c in ("resistance_ohm", "reactance_ohm", "resistance_pu", "reactance_pu",
                  "susceptance_pu_half", "susceptance_pu_total", "max_current_a", "sn_mva", *TPL_COLS):
            ws.cell(r, cols.index(c) + 1).fill = CALC_FILL
        if rec.get("include_in_network") == "no":
            for c in ("edge_id", "include_in_network", "duplicate_of_OBJECTID"):
                ws.cell(r, cols.index(c) + 1).fill = LOW_FILL
        if rec.get("match_confidence") in ("low", "none"):
            for c in ("from_station_id", "to_station_id", "match_confidence"):
                ws.cell(r, cols.index(c) + 1).fill = LOW_FILL
    widths = {"edge_id": 30, "type": 7, "from_node_id": 14, "from_station_id": 11, "from_station_name": 32,
              "from_voltage_kv": 8, "to_node_id": 14, "to_station_id": 11, "to_station_name": 32, "to_voltage_kv": 8,
              "edge_type": 8, "length_m": 11, "source": 40, "OBJECTID": 9, "n_projectnaam": 50,
              "match_note": 80, "via_station_ids": 22, "n_circuits_basis": 45,
              **{c: 16 for c in TPL_COLS}, "parameter_basis": 60}
    for c in cols:
        ws.column_dimensions[L[c]].width = widths.get(c, 13)
    for c in ("resistance_ohm", "reactance_ohm", "length_m", "Shape__Length", "max_current_a", "sn_mva", *TPL_COLS):
        for r in range(hdr_rows + 1, hdr_rows + 1 + len(recs)):
            ws.cell(r, cols.index(c) + 1).number_format = "0.000"
    for c in ("resistance_pu", "reactance_pu", "susceptance_pu_half", "susceptance_pu_total"):
        for r in range(hdr_rows + 1, hdr_rows + 1 + len(recs)):
            ws.cell(r, cols.index(c) + 1).number_format = "0.000000"
    ws.freeze_panes = ws.cell(hdr_rows + 1, 2)
    ws.auto_filter.ref = f"A{hdr_rows}:{L[cols[-1]]}{hdr_rows + len(recs)}"
    return ws


def write_table(wb, name, df, widths=None):
    ws = wb.create_sheet(name)
    for j, c in enumerate(df.columns):
        cell = ws.cell(1, j + 1, c)
        cell.font, cell.fill = WHITE_BOLD, NAVY
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    for i, row in enumerate(df.itertuples(index=False)):
        for j, v in enumerate(row):
            ws.cell(i + 2, j + 1, clean(v))
    for j, c in enumerate(df.columns):
        ws.column_dimensions[get_column_letter(j + 1)].width = (widths or {}).get(c, 14)
    ws.freeze_panes = "B2"
    ws.auto_filter.ref = f"A1:{get_column_letter(len(df.columns))}{len(df) + 1}"
    return ws


def write_notes(wb, cfg, summary):
    ws = wb.create_sheet("Notes")
    ws.column_dimensions["A"].width = 160
    ws["A1"] = "Notes"
    ws["A1"].font = Font(bold=True, size=12)
    r = 3
    for t in (cfg.get("notes") or []) + summary:
        c = ws.cell(r, 1, t)
        c.alignment = Alignment(wrap_text=True, vertical="top")
        r += 1


# --------------------------------------------------------------------------- main
def main(config_path, scenario):
    cfg = load_config(config_path)
    p = cfg["paths"]
    inp, outp = p["input_folder"], p["output_folder"]
    df = pd.read_excel(inp / p["input_file"])
    missing = set(INPUT_COLS) - set(df.columns)
    if missing:
        raise ValueError(f"{p['input_file']} is missing columns: {sorted(missing)}")
    fn = pd.read_csv(inp / p["network_file"], float_precision="round_trip")
    arc = pd.read_csv(inp / p["stations_file"], float_precision="round_trip")
    ends_df = pd.read_csv(inp / p["endpoints_file"], float_precision="round_trip")
    points = pd.read_excel(inp / p["points_file"]) if p.get("points_file") else None
    reg = StationRegistry(cfg, fn, arc, points)
    apply_scenario(cfg, scenario, fn, inp)
    edge_index = build_edge_index(fn)
    lt_rows = line_type_rows(cfg)
    rf_rows, _ = reinforced_rows(cfg)
    assigns = cfg.get("assignments") or {}
    m = cfg["matching"]

    # pass 1: stations per row
    assign_of, aux = {}, {}
    for _, row in df.iterrows():
        oid = int(row["OBJECTID"])
        kv = kv_number(row["kv"])
        ends = path_ends(ends_df, oid)
        terms = terminals(ends)
        same_kv = reg.with_coords(kv)
        auto = []
        for t in terms:
            s, d = nearest(same_kv, t["x"], t["y"]) if same_kv else (None, None)
            auto.append((s["id"] if s else None, d))
        auto_txt = "; ".join(f"{s}@{d:.0f} m" for s, d in auto if s) or None
        if oid in assigns:
            a = dict(assigns[oid])
            method = "config assignment"
        else:  # automatic snapping
            ok = [s for s, d in auto if s and d <= m["auto_snap_max_m"]]
            a = {"from": ok[0] if ok else None, "to": ok[-1] if len(ok) > 1 else None,
                 "conf": "auto", "note": f"Automatic snap of the line ends: {auto_txt}"}
            method = "automatic snap"
        assign_of[oid] = a
        aux[oid] = (ends, auto_txt, method)
    # pass 2: circuits, then the edge values
    circuits = determine_circuits(cfg, df, assign_of, edge_index)
    recs, log = [], []
    for _, row in df.iterrows():
        oid = int(row["OBJECTID"])
        kv = kv_number(row["kv"])
        a = assign_of[oid]
        ends, auto_txt, method = aux[oid]
        old = None
        if str(row.get("n_werkzaamheden_ip") or "").strip().lower() == "lijnverzwaring" and kv:
            old = find_old(edge_index, a, assigns.get(oid, {}), kv)
        rec = compute(cfg, row, a, reg, ends, lt_rows, rf_rows, circuits[oid], old)
        rec["_old"] = old
        recs.append(rec)
        tol = m["geometry_tolerance_m"]
        fd, td = rec["_log"]["from_dist"], rec["_log"]["to_dist"]
        fs, ts = reg.get(a.get("from")), reg.get(a.get("to"))
        log.append({
            "OBJECTID": oid, "n_projectnaam": clean(row["n_projectnaam"]), "kv": clean(row["kv"]),
            "from_station_id": a.get("from"), "from_station_name": fs["name"] if fs else None,
            "from_name_source": fs.get("name_source") if fs else None,
            "from_origin": fs["origin"] if fs else None,
            "from_dist_to_line_end_m": round(fd) if fd is not None else None,
            "from_on_geometry": None if fd is None else ("yes" if fd <= tol else "no"),
            "to_station_id": a.get("to"), "to_station_name": ts["name"] if ts else None,
            "to_name_source": ts.get("name_source") if ts else None,
            "to_origin": ts["origin"] if ts else None,
            "to_dist_to_line_end_m": round(td) if td is not None else None,
            "to_on_geometry": None if td is None else ("yes" if td <= tol else "no"),
            "via_station_ids": ", ".join(a.get("via") or []) or None,
            "line_terminals_nearest_same_kv": auto_txt,
            **project_points(points, row, ends),
            "n_path_ends": len(ends), "method": method,
            "confidence": a.get("conf"), "note": a.get("note"),
        })

    # ---------- workbook
    wb = Workbook()
    wb.remove(wb.active)
    write_data_sheet(wb, "1", recs, cfg)
    write_parameters(wb, cfg)
    types = df["n_werkzaamheden_ip"].fillna("(blank)").astype(str).str.strip()
    names = sorted(types.unique(), key=lambda s: (s != "(blank)", s.lower()))
    for name in names:
        sub = [r for r, t in zip(recs, types) if t == name]
        write_data_sheet(wb, name[:31], sub, cfg, lijn=(name.lower() == "lijnverzwaring"))
    # stations used
    used = {}
    for r in recs:
        for sid in [r.get("from_station_id"), r.get("to_station_id")] + \
                   [v.strip() for v in (r.get("via_station_ids") or "").split(",") if v.strip()]:
            if sid:
                used.setdefault(sid, []).append(str(r["OBJECTID"]))
    st_rows = []
    for sid, oids in sorted(used.items()):
        d = reg.get(sid)
        st_rows.append({"station_id": sid, "node_id": f"node:{sid}", "station_name": d["name"], "voltage_kv": d["kv"],
                        "x_rd": d["x"], "y_rd": d["y"], "name_source": d.get("name_source"), "origin": d["origin"], "ip26_point": d.get("point"),
                        "in_full_network": "yes" if sid in reg.in_fn else "no",
                        "used_by_OBJECTID": ", ".join(sorted(set(oids), key=int)), "note": d.get("note")})
    st_df = pd.DataFrame(st_rows)
    write_table(wb, "Stations", st_df, {"station_name": 40, "origin": 34, "used_by_OBJECTID": 40, "note": 90, "ip26_point": 50})
    # all new-station points of IP26_point.xlsx: which ones are used as a station in this workbook
    if points is not None:
        pid_to_station = {}
        for d in reg.data.values():
            if d.get("point"):
                pid_to_station.setdefault(int(str(d["point"]).split(":")[0]), []).append(d["id"])
        rows = []
        for h in points[points.werkzaamheden.isin(cfg.get("new_station_types") or ["nieuw hoogspanningsstation"])].itertuples():
            near, dn = nearest(reg.with_coords(), h.x_coord, h.y_coord)
            ids = pid_to_station.get(int(h.OBJECTID), [])
            rows.append({"point_OBJECTID": h.OBJECTID, "nummer": h.nummer, "projectnaam": h.projectnaam,
                         "werkzaamheden": h.werkzaamheden, "spannings_niveau": h.spannings_niveau,
                         "ibn_jaar_ip2026": h.ibn_jaar_ip2026, "provincie": h.provincie,
                         "x_coord": h.x_coord, "y_coord": h.y_coord,
                         "station_id_in_this_workbook": ", ".join(ids) or None,
                         "used_by_IP26_line": "yes" if any(i in used for i in ids) else "no",
                         "nearest_station": near["id"] if near else None,
                         "nearest_station_dist_m": round(dn) if dn is not None else None})
        write_table(wb, "IP26_new_stations", pd.DataFrame(rows), {"projectnaam": 55, "station_id_in_this_workbook": 18})
    log_df = pd.DataFrame(log)
    write_table(wb, "Station_match", log_df, {"n_projectnaam": 50, "from_station_name": 32, "to_station_name": 32,
                                              "from_origin": 28, "to_origin": 28,
                                              "line_terminals_nearest_same_kv": 40, "note": 100})
    n_new = int((st_df["in_full_network"] == "no").sum())
    conf = log_df["confidence"].value_counts().to_dict()
    summary = [f"Scenario: {cfg['_scenario']['name']} - {cfg['_scenario']['description']}",
               f"Run summary: {len(recs)} rows; {len(st_df)} stations used, {n_new} of them not in full_network.csv; "
               f"confidence {conf}."]
    write_notes(wb, cfg, summary)
    wb.calculation.fullCalcOnLoad = True
    outp.mkdir(parents=True, exist_ok=True)
    out = outp / p["output_file"].replace("{scenario}", cfg["_scenario"]["name"])
    wb.save(out)

    print(f"Written: {out}")
    print(summary[0]); print(summary[1])
    far = log_df[(log_df.from_on_geometry == "no") | (log_df.to_on_geometry == "no")]
    if len(far):
        print(f"{len(far)} rows with a station more than {m['geometry_tolerance_m']} m from the line ends "
              f"(see tab Station_match): {', '.join(map(str, far.OBJECTID))}")
    return out, recs


def run(scenario=SCENARIO, config_path=None):
    config_path = config_path or Path(__file__).with_name(CONFIG_FILE)
    names = list(load_config(config_path)["scenarios"]) if scenario == "all" else [scenario]
    results = {}
    for name in names:
        out, recs = main(config_path, name)
        results[name] = recs
    if len(names) > 1:
        write_comparison(load_config(config_path), results)
    return results


if __name__ == "__main__":
    args = sys.argv[1:]
    run(args[0] if args else SCENARIO, args[1] if len(args) > 1 else None)
