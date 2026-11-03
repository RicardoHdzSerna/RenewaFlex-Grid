"""
ip26_final_network.py
=====================
Step 5: builds the final 2030 / 2040 networks as a derived layer

    final network = Juan's base network (DATA/full_network.csv) + the IP26 changes

The changes come from the horizon workbooks of step 3 (output/horizons/IP26_line_network_edges_<scenario>_<horizon>.xlsx,
columns network_action and applies_to_listed_branches) and from the review decisions in config_decisions.yaml;
they are applied by code and every change is recorded and traceable. full_network.csv itself is never changed.

Every changed branch is modelled as a chain of sections in series (length, r', x', b', rating per section):
    base branch            one section with Juan's per-km values (value / length)
    split (loop-in)        the branch is cut at the new station: two branches, each = its part of the old line
                           + the loop-in connection (IP26 row values); the row's own edge is not added
    upgrade (modify)       the upgraded length of the old section(s) is replaced by a section with the new values
    final branch           R = sum r'_i L_i,  X = sum x'_i L_i,  B = sum b'_i L_i  (series);  rating = min_i rating_i
So for a partial upgrade: R, X, B = old per-km x unchanged length + new per-km x upgraded length, rating = min(old, new);
a fully upgraded branch gets the new rating (rating_full) and the IP26 type (type_on_full_coverage).

    modify existing branch, applies = yes  -> listed branches changed (record_status "derived")
    split existing branch                  -> branch replaced by two branches at the new station ("derived (split)")
    new edge (new connection / extra circuits) -> IP26 edge added ("new (IP26)"), configurable
    already in full_network / not applied  -> no change, logged
    manual: copies of a real circuit       -> never changed (manual_copy_of column), review item f

Output (output_final/<scenario>/full_network_final_<scenario>_<horizon>.xlsx), values only, two tabs:
    network      Juan's 21 columns in the same order + traceability columns
    change_log   one row per IP26 row x branch (modified / split / added / not applied, with the reason)
and output_final/IP26_final_network_summary.xlsx (counts and checks per scenario and horizon, rules).
Step 6 (ip26_excel_to_csv.py) converts these workbooks to CSV in output_final_csv/.

Usage:
    python ip26_final_network.py                     # uses config_final_network.yaml
    python ip26_final_network.py my_config.yaml
"""
import json
import math
import re
import sys
from pathlib import Path

import pandas as pd
import yaml

from ip26_excel_to_csv import Workbook  # formula evaluator: the horizon workbooks hold formulas, no stored results

CONFIG_FILE = "config_final_network.yaml"

BASE_COLS = ["edge_id", "type", "from_node_id", "from_station_id", "from_station_name", "from_voltage_kv",
             "to_node_id", "to_station_id", "to_station_name", "to_voltage_kv", "resistance_ohm", "reactance_ohm",
             "resistance_pu", "reactance_pu", "susceptance_pu_half", "susceptance_pu_total", "edge_type",
             "length_m", "max_current_a", "sn_mva", "source"]
TRACE_COLS = ["record_status", "ip26_objectids", "ip26_n_nummer", "ip26_project", "ip26_werkzaamheden",
              "ip26_in_service", "network_action", "coverage", "split_from", "manual_copy_of", "branch_length_m",
              "upgraded_length_m", "unchanged_length_m", "upgraded_share", "upgraded_length_source", "section_types",
              "sections", "base_type", "base_length_m", "base_resistance_ohm", "base_reactance_ohm",
              "base_susceptance_pu_total", "base_max_current_a", "base_sn_mva", "new_resistance_ohm_per_km",
              "new_reactance_ohm_per_km", "new_susceptance_pu_per_km", "new_max_current_a", "change_note"]
LOG_COLS = ["edge_id", "applied", "ip26_objectids", "ip26_n_nummer", "ip26_project", "ip26_werkzaamheden",
            "ip26_in_service", "network_action", "applies_to_listed_branches", "coverage", "from_station_id",
            "to_station_id", "voltage_kv", "type", "base_length_m", "final_length_m", "upgraded_length_m",
            "upgraded_share", "upgraded_length_source", "base_resistance_ohm", "final_resistance_ohm",
            "base_reactance_ohm", "final_reactance_ohm", "base_susceptance_pu_total", "final_susceptance_pu_total",
            "base_max_current_a", "final_max_current_a", "base_sn_mva", "final_sn_mva", "change_note"]


# --------------------------------------------------------------------------- reading
def read_tab_values(path, tab):
    """Values of one tab (formulas evaluated) as a DataFrame with the first row as header."""
    book = Workbook(path)
    ws = book.wb[tab]
    rows = [[book.value(tab, c, r) for c in range(1, ws.max_column + 1)] for r in range(1, ws.max_row + 1)]
    rows = [r for r in rows if any(v not in (None, "") for v in r)]
    return pd.DataFrame(rows[1:], columns=rows[0])


def read_line_types(path):
    """Per-km parameters and ratings per (kV, line/cable) from the Parameters tab of a horizon workbook."""
    book = Workbook(path)
    ws = book.wb["Parameters"]
    out = {}
    for r in range(1, ws.max_row + 1):
        kv, typ = book.value("Parameters", 2, r), book.value("Parameters", 3, r)
        if isinstance(kv, (int, float)) and typ in ("line", "cable"):
            out[(float(kv), typ)] = {k: book.value("Parameters", c, r) for k, c in
                                     (("r", 4), ("x", 5), ("b_uS", 6), ("i", 7))}
    return out


def project_info(path):
    """OBJECTID -> project number, name, type, commissioning year, over/underground (scenario workbook)."""
    df = pd.read_excel(path, sheet_name="1", usecols=lambda c: c in (
        "OBJECTID", "n_nummer", "n_projectnaam", "n_werkzaamheden_ip", "N_ibn_jaar_ip2026", "bovengronds_ondergrond"))
    df = df.dropna(subset=["OBJECTID"])
    return df.set_index(df["OBJECTID"].astype(int)).to_dict("index")


def ids(text):
    if text is None or (isinstance(text, float) and math.isnan(text)):
        return []
    return [x.strip() for x in str(text).split(";") if x.strip()]


def fnum(x, default=None):
    try:
        v = float(x)
        return default if math.isnan(v) else v
    except (TypeError, ValueError):
        return default


def circuit_tag(edge_id):
    s = re.sub(r":seg\d+$", "", str(edge_id))
    return re.split(r"[ \-]", s)[-1]


def station_code(station_id):
    return re.sub(r"\d+$", "", str(station_id))


def manual_copies(base):
    """edge_id of a manual: copy -> edge_id of the real circuit it repeats (same stations, same letter)."""
    real = {}
    for r in base.itertuples(index=False):
        if "manual:" not in r.edge_id:
            real.setdefault((frozenset((r.from_station_id, r.to_station_id)), circuit_tag(r.edge_id)), r.edge_id)
    out = {}
    for r in base.itertuples(index=False):
        if "manual:" in r.edge_id:
            k = (frozenset((r.from_station_id, r.to_station_id)), circuit_tag(r.edge_id))
            if k in real:
                out[r.edge_id] = real[k]
    return out


# --------------------------------------------------------------------------- geometry (for the decisions)
def project_on_line(pt, a, b):
    """Fraction t of the projection of pt on the straight line a-b, and the offset (m)."""
    vx, vy = b[0] - a[0], b[1] - a[1]
    L2 = vx * vx + vy * vy
    t = ((pt[0] - a[0]) * vx + (pt[1] - a[1]) * vy) / L2
    off = abs(vx * (pt[1] - a[1]) - vy * (pt[0] - a[0])) / math.sqrt(L2)
    return t, off


def row_ends(endpoints, oid):
    e = endpoints[endpoints["OBJECTID"] == oid]
    return [(r.x_start, r.y_start) for r in e.itertuples()] + [(r.x_end, r.y_end) for r in e.itertuples()]


# --------------------------------------------------------------------------- upgraded length per branch
def upgraded_lengths(row, branches, threshold):
    """Upgraded length of every listed (unsplit) branch for one IP26 row.
    Branches between the IP26 from/to stations are 'direct' routes (each is its own route); the other branches
    form a multi-station route whose length is the sum of its sections (shortest circuit per section). The IP26
    length is spread over a route in proportion to the branch lengths (the location of the upgraded part is not
    in the data). Ratio >= threshold: the whole branch counts as upgraded (difference = geometry only)."""
    a, b = row["from_station_id"], row["to_station_id"]
    l_ip = fnum(row["length_m"], 0.0)
    direct = {e["edge_id"] for e in branches if {e["from_station_id"], e["to_station_id"]} == {a, b}}
    sec = {}
    for e in branches:
        if e["edge_id"] not in direct:
            k = frozenset((e["from_station_id"], e["to_station_id"]))
            sec[k] = min(sec.get(k, float("inf")), e["length_m"])
    chain_len = sum(sec.values())
    out = {}
    for e in branches:
        is_direct = e["edge_id"] in direct
        route = e["length_m"] if is_direct else chain_len
        ratio = l_ip / route if route else 1.0
        full = ratio >= threshold
        share = 1.0 if full else min(1.0, ratio)
        kind = "direct branch" if is_direct else f"route of {len(sec)} section(s)"
        src = (f"IP26 OBJECTID {int(row['OBJECTID'])}: length_m {l_ip:.1f} m (IP2026 line geometry, Shape__Length) "
               f"vs {kind} in full_network.csv ({route:.1f} m), ratio {ratio:.3f}; ")
        src += (f"ratio >= {threshold}: whole branch counted as upgraded" if full else
                f"ratio < {threshold}: partial, upgraded length = branch length x {share:.3f}")
        out[e["edge_id"]] = (share * e["length_m"], src)
    return out


# --------------------------------------------------------------------------- sections
def base_section(b):
    L = fnum(b["length_m"], 0.0)
    km = L / 1000
    return {"len": L, "r": fnum(b["resistance_ohm"], 0.0) / km if km else 0.0,
            "x": fnum(b["reactance_ohm"], 0.0) / km if km else 0.0,
            "b": fnum(b["susceptance_pu_total"], 0.0) / km if km else 0.0,
            "i": fnum(b["max_current_a"], 0.0), "type": b["type"], "src": "base"}


def replace_base(sections, length, new):
    """Replaces 'length' metres of the base (old-line) sections by a new section; returns the length replaced."""
    rest = length
    for s in sections:
        if s["src"] == "base" and rest > 1e-9:
            take = min(s["len"], rest)
            s["len"] -= take
            rest -= take
    done = length - rest
    if done > 1e-9:
        sections.append(dict(new, len=done))
    sections[:] = [s for s in sections if s["len"] > 1e-9 or s["src"] != "base"]
    return done


# --------------------------------------------------------------------------- build one network
def build(cfg, dec, base, horizon_df, info, line_types, geo, scenario, horizon):
    m = cfg.get("modify") or {}
    thr = float(m.get("full_coverage_threshold", 0.7))
    sbase = float(m.get("sbase_mva", 100))
    rs = cfg.get("record_status") or {}
    net = base.copy()
    for c in TRACE_COLS:
        net[c] = None
    net = net.astype({c: object for c in TRACE_COLS})
    net["record_status"] = rs.get("base", "base")
    copies = manual_copies(base)
    if dec.get("manual_copies", "never_change") == "never_change":
        for e, real in copies.items():
            net.loc[net.edge_id == e, "manual_copy_of"] = real
    rows = {e: net.loc[i, BASE_COLS].to_dict() for i, e in enumerate(net["edge_id"])}
    if len(rows) != len(net):
        raise ValueError("edge_id is not unique in the base network")
    state = {}          # edge_id -> {"row": base row, "sections": [...], "changes": [...], "split_from": ..}
    splits_done = {}    # original edge_id -> {"parts": [(edge_id, km_from, km_to)], "a": station}
    log, new_rows = [], []

    def meta_of(r):
        oid = int(r["OBJECTID"])
        p = info.get(oid, {})
        return {"ip26_objectids": str(oid), "ip26_n_nummer": p.get("n_nummer"), "ip26_project": p.get("n_projectnaam"),
                "ip26_werkzaamheden": p.get("n_werkzaamheden_ip"), "ip26_in_service": p.get("N_ibn_jaar_ip2026"),
                "network_action": r["network_action"], "applies_to_listed_branches": r.get("applies_to_listed_branches")}

    def new_values(r):
        """Per-km values (r, x in ohm/km, b in pu/km), rating per circuit and type of an IP26 row."""
        oid = int(r["OBJECTID"])
        l_km = fnum(r["length_m"], 0.0) / 1000
        nv = {"r": fnum(r["per_circuit_resistance_ohm"]) / l_km, "x": fnum(r["per_circuit_reactance_ohm"]) / l_km,
              "b": fnum(r["per_circuit_susceptance_pu_total"]) / l_km, "i": fnum(r["per_circuit_max_current_a"]),
              "type": r["type"], "src": f"IP26 {oid}", "basis": "IP26 row values"}
        p = info.get(oid, {})
        if (dec.get("verkabelen_uses_cable_parameters", True) and p.get("n_werkzaamheden_ip") == "Verkabelen"
                and r["type"] != "cable"):
            kv = float(r["from_voltage_kv"])
            t = line_types[(kv, "cable")]
            nv.update(r=t["r"], x=t["x"], b=t["b_uS"] * 1e-6 * kv ** 2 / sbase, i=t["i"], type="cable",
                      basis=f"cable parameters {kv:g} kV of the {scenario} Parameters tab (Verkabelen row marked "
                            f"overhead in IP26; decision verkabelen_uses_cable_parameters)")
        return nv

    def get_state(e):
        if e not in state:
            state[e] = {"row": rows[e], "sections": [base_section(rows[e])], "changes": [], "split_from": None}
        return state[e]

    excluded = {int(k): v for k, v in (dec.get("exclude_rows") or {}).items()}
    hdf = horizon_df.copy()
    hdf["_order"] = (hdf["network_action"] != "split existing branch").astype(int)   # splits first
    for _, r in hdf.sort_values(["_order", "OBJECTID"]).iterrows():
        oid = int(r["OBJECTID"])
        meta = meta_of(r)
        act = str(r["network_action"])
        applies = str(r.get("applies_to_listed_branches") or "")
        note = str(r.get("action_note") or "")
        listed = ids(r.get("full_network_edge_ids"))
        missing = [e for e in listed if e not in rows]
        if missing:
            raise ValueError(f"OBJECTID {oid}: branch ids not in full_network.csv: {missing}")
        if oid in excluded:
            for e in [r["edge_id"]] + listed:
                log.append(dict(meta, edge_id=e, applied=f"not applied: excluded for now ({excluded[oid]})",
                                change_note=note))
            continue
        skip = [e for e in listed if e in copies]
        for e in skip:
            log.append(dict(meta, edge_id=e, applied=f"not applied: manual copy of {copies[e]} (never changed)",
                            change_note=note))
        listed = [e for e in listed if e not in copies]

        if act == "split existing branch":
            d = (dec.get("splits") or {}).get(oid)
            if d is None or not d.get("enabled", True):
                raise ValueError(f"OBJECTID {oid}: split row without an entry in config_decisions.yaml splits")
            a, b = d["line"]
            st = d["station"]
            nv = new_values(r)
            loop = fnum(r["length_m"], 0.0) if d.get("loop_in_length_m", "ip26") == "ip26" else float(d["loop_in_length_m"])
            st_name = r["from_station_name"] if r["from_station_id"] == st else r["to_station_name"]
            st_kv = r["from_voltage_kv"] if r["from_station_id"] == st else r["to_voltage_kv"]
            for e in listed:
                br = rows[e]
                L = fnum(br["length_m"], 0.0)
                if d.get("tap_position_km", "auto") == "auto":
                    pa, pb = geo["stations"][a], geo["stations"][b]
                    cand = [project_on_line(pt, pa, pb) for pt in row_ends(geo["endpoints"], oid)]
                    t, off = min(cand, key=lambda c: c[1])
                    tap = min(max(t, 0.0), 1.0) * L
                    tap_src = (f"tap at {tap / 1000:.3f} km from {a}: IP26 line end of OBJECTID {oid} projected on "
                               f"{a}-{b} (t = {t:.4f}, {off:.0f} m from the straight line), scaled to Juan's length "
                               f"{L / 1000:.3f} km")
                else:
                    tap = float(d["tap_position_km"]) * 1000
                    tap_src = f"tap at {tap / 1000:.3f} km from {a} (config_decisions.yaml)"
                tag = circuit_tag(e)
                kv = int(float(br["from_voltage_kv"]))
                parts = []
                for (x, y, km0, km1, base_len) in ((a, st, 0.0, tap, tap), (st, b, tap, L, L - tap)):
                    pid = f"branch:{station_code(x)}-{station_code(y)}{kv} {tag}"
                    prow = dict(br)
                    for side, sid in (("from", x), ("to", y)):
                        if sid == st:
                            prow.update({f"{side}_node_id": f"node:{st}", f"{side}_station_id": st,
                                         f"{side}_station_name": st_name, f"{side}_voltage_kv": st_kv})
                        else:
                            src_side = "from" if br["from_station_id"] == sid else "to"
                            for k in ("node_id", "station_id", "station_name", "voltage_kv"):
                                prow[f"{side}_{k}"] = br[f"{src_side}_{k}"]
                    prow["edge_id"] = pid
                    secs = [dict(base_section(br), len=base_len)]
                    if loop > 0:
                        secs.append(dict(nv, len=loop))
                    rows[pid] = prow
                    state[pid] = {"row": prow, "sections": secs, "split_from": e, "base_row": br,
                                  "changes": [dict(meta, kind="split", src=(
                                      f"split of {e} at {st} (OBJECTID {oid}): {tap_src}; part {x}-{y} = old line "
                                      f"{base_len / 1000:.3f} km (km {km0 / 1000:.3f}-{km1 / 1000:.3f} from {a}) + "
                                      f"loop-in {loop / 1000:.3f} km with the IP26 row values"), new=nv, note=note)]}
                    parts.append((pid, km0, km1))
                splits_done[e] = {"parts": parts, "a": a, "b": b, "L": L}
                log.append(dict(meta, edge_id=e, applied=f"split into {parts[0][0]} and {parts[1][0]} (replaced)",
                                branch_length_m=L, change_note=note))
            continue

        if act == "modify existing branch":
            if applies != "yes":
                for e in listed:
                    log.append(dict(meta, edge_id=e, applied="not applied: " + applies.replace("no - ", "", 1),
                                    change_note=note))
                continue
            nv = new_values(r)
            plain = [e for e in listed if e not in splits_done]
            lens = upgraded_lengths(r, [rows[e] for e in plain], thr) if plain else {}
            for e in plain:
                up, src = lens[e]
                get_state(e)["changes"].append(dict(meta, kind="modify", up=up, src=src, new=nv, note=note))
            for e in listed:
                if e not in splits_done:
                    continue
                sd = splits_done[e]
                L, a, b = sd["L"], sd["a"], sd["b"]
                l_ip = fnum(r["length_m"], 0.0)
                loc = ((dec.get("section_location") or {}).get(oid) or {}).get("location", "proportional")
                if loc == "auto":
                    pa, pb = geo["stations"][a], geo["stations"][b]
                    ts = [min(max(project_on_line(pt, pa, pb)[0], 0.0), 1.0) for pt in row_ends(geo["endpoints"], oid)]
                    s0, s1 = min(ts) * L, max(ts) * L
                    how = (f"section located from the IP26 geometry of OBJECTID {oid}: km {s0 / 1000:.3f}-{s1 / 1000:.3f} "
                           f"from {a} on the original {e} ({L / 1000:.3f} km); the overlap with each part is scaled "
                           f"to the IP26 length ({l_ip / (s1 - s0) if s1 > s0 else 1:.4f})")
                elif isinstance(loc, (list, tuple)):
                    s0, s1 = float(loc[0]) * 1000, float(loc[1]) * 1000
                    how = f"section km {s0 / 1000:.3f}-{s1 / 1000:.3f} from {a} (config_decisions.yaml)"
                else:
                    s0, s1 = None, None
                    how = "section spread over the split parts in proportion to their lengths"
                for pid, km0, km1 in sd["parts"]:
                    if s0 is None:
                        up = min(l_ip, L) * (km1 - km0) / L
                    else:
                        up = max(0.0, min(s1, km1) - max(s0, km0))
                        if s1 > s0:
                            up = min(up * l_ip / (s1 - s0), km1 - km0)
                    src = (f"IP26 OBJECTID {oid}: length_m {l_ip:.1f} m on split line {e}; {how}; on {pid} "
                           f"(km {km0 / 1000:.3f}-{km1 / 1000:.3f}): upgraded {up:.1f} m")
                    if up > 1e-9:
                        state[pid]["changes"].append(dict(meta, kind="modify", up=up, src=src, new=nv, note=note))
                    else:
                        log.append(dict(meta, edge_id=pid, applied="not applied: the section lies on the other part",
                                        upgraded_length_m=0.0, upgraded_length_source=src, change_note=note))
            continue

        if act.startswith("new edge"):
            add = bool(cfg.get("add_new_edges", True))
            if add:
                row = {c: r.get(c) for c in BASE_COLS}
                if row["edge_id"] in rows:
                    raise ValueError(f"new edge id {row['edge_id']} already in the network")
                row.update({k: v for k, v in meta.items() if k in TRACE_COLS},
                           record_status=rs.get("new", "new (IP26)"), coverage="new edge",
                           upgraded_length_source=f"IP26 OBJECTID {oid}: edge of the {scenario} scenario workbook",
                           change_note=note)
                new_rows.append(row)
            log.append(dict(meta, edge_id=r["edge_id"], applied="added as new edge" if add
                            else "not added (add_new_edges = false)", coverage="new edge",
                            from_station_id=r["from_station_id"], to_station_id=r["to_station_id"],
                            voltage_kv=r["from_voltage_kv"], type=r["type"], final_length_m=r["length_m"],
                            final_resistance_ohm=r["resistance_ohm"], final_reactance_ohm=r["reactance_ohm"],
                            final_susceptance_pu_total=r["susceptance_pu_total"], final_max_current_a=r["max_current_a"],
                            final_sn_mva=r["sn_mva"], change_note=note))
            for e in listed:
                log.append(dict(meta, edge_id=e, applied="not applied: " + applies.replace("no - ", "", 1),
                                change_note=note))
            continue

        for e in listed or [None]:
            log.append(dict(meta, edge_id=e, applied="no change - already in full_network", change_note=note))

    # ------------------------------------------------------------------ apply the sections
    out_rows = {}
    for e, s in state.items():
        br = s["row"]
        orig = s.get("base_row", br)
        secs = s["sections"]
        mods = [c for c in s["changes"] if c["kind"] == "modify"]
        overlap = 1.0
        base_len = sum(x["len"] for x in secs if x["src"] == "base")
        up_req = sum(c["up"] for c in mods)
        if up_req > base_len + 1e-9:            # overlapping upgrades cannot exceed the old line
            overlap = base_len / up_req
        for c in mods:
            c["done"] = replace_base(secs, c["up"] * overlap, c["new"])
        L = sum(x["len"] for x in secs)
        R = sum(x["r"] * x["len"] / 1000 for x in secs)
        X = sum(x["x"] * x["len"] / 1000 for x in secs)
        B = sum(x["b"] * x["len"] / 1000 for x in secs)
        old_left = sum(x["len"] for x in secs if x["src"] == "base")
        up_len = sum(x["len"] for x in secs if x["src"] != "base")
        full = old_left <= 1e-9
        i_old = fnum(orig["max_current_a"], 0.0)
        I = min(x["i"] for x in secs)
        if full and m.get("rating_full", "new") == "min":
            I = min(I, i_old)
        kv = fnum(br["from_voltage_kv"])
        zb = kv ** 2 / sbase
        sn = fnum(orig["sn_mva"], 0.0) * I / i_old if (m.get("sn_mva", "scale") == "scale" and i_old) \
            else math.sqrt(3) * kv * I / 1000
        types = {x["type"] for x in secs}
        typ = orig["type"]
        if full and len(types) == 1 and m.get("type_on_full_coverage", "ip26") == "ip26":
            typ = types.pop()
        split = s.get("split_from")
        status = rs.get("derived", "derived") + (" (split)" if split else "")
        sect_txt = " + ".join(f"{x['type']} {x['len'] / 1000:.3f} km ({'unchanged' if x['src'] == 'base' else x['src']})"
                              for x in secs)
        chg = (f"derived = full_network.csv + IP26 ({scenario}, {horizon}); sections in series: {sect_txt}; "
               f"R, X, B = sum of per-km value x section length; rating = min over sections"
               + (" (fully upgraded: new rating)" if full and m.get("rating_full", "new") == "new" else "")
               + (f"; type {orig['type']} -> {typ}" if typ != orig["type"] else "")
               + (f"; overlapping upgrades scaled to the old-line length (x{overlap:.3f})" if overlap != 1 else "")
               + ". " + " | ".join(c["src"] for c in s["changes"])
               + ". IP26 note: " + " | ".join(dict.fromkeys(c["note"] for c in s["changes"])))
        rec = dict(br)
        rec.update({"resistance_ohm": R, "reactance_ohm": X, "susceptance_pu_total": B, "susceptance_pu_half": B / 2,
                    "resistance_pu": R / zb, "reactance_pu": X / zb, "max_current_a": I, "sn_mva": sn,
                    "type": typ, "edge_type": typ, "length_m": L})
        news = [c["new"] for c in s["changes"]]
        rec.update({"record_status": status,
                    "ip26_objectids": "; ".join(dict.fromkeys(c["ip26_objectids"] for c in s["changes"])),
                    "ip26_n_nummer": "; ".join(dict.fromkeys(str(c["ip26_n_nummer"]) for c in s["changes"])),
                    "ip26_project": "; ".join(dict.fromkeys(str(c["ip26_project"]) for c in s["changes"])),
                    "ip26_werkzaamheden": "; ".join(dict.fromkeys(str(c["ip26_werkzaamheden"]) for c in s["changes"])),
                    "ip26_in_service": "; ".join(dict.fromkeys(str(c["ip26_in_service"]) for c in s["changes"])),
                    "network_action": "; ".join(dict.fromkeys(c["network_action"] for c in s["changes"])),
                    "coverage": "full" if full else ("partial" if mods else "split only"),
                    "split_from": split, "branch_length_m": L, "upgraded_length_m": sum(c["done"] for c in mods),
                    "unchanged_length_m": old_left, "upgraded_share": up_len / L if L else 1.0,
                    "upgraded_length_source": " | ".join(c["src"] for c in s["changes"]),
                    "section_types": sect_txt,
                    "sections": json.dumps([{k: x[k] for k in ("len", "r", "x", "b", "i", "type", "src")} for x in secs]),
                    "base_type": orig["type"], "base_length_m": orig["length_m"],
                    "base_resistance_ohm": orig["resistance_ohm"], "base_reactance_ohm": orig["reactance_ohm"],
                    "base_susceptance_pu_total": orig["susceptance_pu_total"], "base_max_current_a": orig["max_current_a"],
                    "base_sn_mva": orig["sn_mva"],
                    "new_resistance_ohm_per_km": "; ".join(repr(float(n["r"])) for n in news),
                    "new_reactance_ohm_per_km": "; ".join(repr(float(n["x"])) for n in news),
                    "new_susceptance_pu_per_km": "; ".join(repr(float(n["b"])) for n in news),
                    "new_max_current_a": "; ".join(repr(float(n["i"])) for n in news),
                    "change_note": chg + " Parameter basis: " + " | ".join(dict.fromkeys(n["basis"] for n in news)),
                    "manual_copy_of": None})
        out_rows[e] = rec
        for c in s["changes"]:
            log.append({"edge_id": e, "applied": "split part (derived)" if c["kind"] == "split" else "modified (derived)",
                        **{k: c.get(k) for k in ("ip26_objectids", "ip26_n_nummer", "ip26_project", "ip26_werkzaamheden",
                                                 "ip26_in_service", "network_action", "applies_to_listed_branches")},
                        "coverage": rec["coverage"], "upgraded_length_m": c.get("done"),
                        "upgraded_share": (c.get("done") or 0) / L if L else None, "upgraded_length_source": c["src"],
                        "from_station_id": br["from_station_id"], "to_station_id": br["to_station_id"],
                        "voltage_kv": br["from_voltage_kv"], "type": typ,
                        "base_length_m": orig["length_m"], "final_length_m": L,
                        "base_resistance_ohm": orig["resistance_ohm"], "final_resistance_ohm": R,
                        "base_reactance_ohm": orig["reactance_ohm"], "final_reactance_ohm": X,
                        "base_susceptance_pu_total": orig["susceptance_pu_total"], "final_susceptance_pu_total": B,
                        "base_max_current_a": i_old, "final_max_current_a": I, "base_sn_mva": orig["sn_mva"],
                        "final_sn_mva": sn, "change_note": chg})

    # assemble: base rows (changed ones replaced, split originals removed, parts inserted after them)
    final = []
    for _, row in net.iterrows():
        e = row["edge_id"]
        if e in splits_done:
            for pid, _, _ in splits_done[e]["parts"]:
                final.append(out_rows[pid])
        elif e in out_rows:
            final.append(out_rows[e])
        else:
            final.append(row.to_dict())
    final += new_rows
    out = pd.DataFrame(final, columns=BASE_COLS + TRACE_COLS)
    return out, pd.DataFrame(log, columns=LOG_COLS), splits_done, copies


# --------------------------------------------------------------------------- checks
def checks(cfg, dec, base, net, horizon_df, splits_done, copies, scenario, horizon):
    """Independent checks of the result."""
    m = cfg.get("modify") or {}
    der = net[net.record_status.astype(str).str.startswith("derived")]
    out = {"scenario": scenario, "horizon": horizon, "edges": len(net),
           "buses": len(set(net.from_node_id) | set(net.to_node_id)),
           "base (unchanged)": int((net.record_status == "base").sum()),
           "derived": int(len(der)),
           "derived partial": int((der.coverage == "partial").sum()),
           "derived full": int((der.coverage == "full").sum()),
           "derived by split": int(der.split_from.notna().sum()),
           "new (IP26)": int(net.record_status.astype(str).str.startswith("new").sum()),
           "IP26 rows applied (modify)": int(((horizon_df.network_action == "modify existing branch") &
                                              (horizon_df.applies_to_listed_branches == "yes")).sum()),
           "IP26 rows split": int((horizon_df.network_action == "split existing branch").sum()),
           "IP26 rows partial": int(der.loc[der.coverage == "partial", "ip26_objectids"].nunique())}
    b = base.set_index("edge_id")
    keep = net[net.record_status == "base"].set_index("edge_id")[BASE_COLS[1:]]
    diff = (keep.fillna("~").astype(str) != b.loc[keep.index, BASE_COLS[1:]].fillna("~").astype(str)).any(axis=1)
    out["base rows differing from full_network.csv (0)"] = int(diff.sum())
    out["base edges missing, other than split originals (0)"] = len(set(base.edge_id) - set(net.edge_id) - set(splits_done))
    out["manual copies changed (0)"] = int(net[net.edge_id.isin(list(copies))].record_status.ne("base").sum())
    out["manual copies marked"] = int(net.manual_copy_of.notna().sum())
    # every applying branch changed (or split) exactly once
    exp = set()
    for _, r in horizon_df[horizon_df.applies_to_listed_branches.astype(str).str.startswith("yes")].iterrows():
        exp |= set(ids(r.full_network_edge_ids)) - set(copies)
    got = set(der.edge_id) | set(splits_done)
    got -= {p for sd in splits_done.values() for p, _, _ in sd["parts"]}
    out["changed branches = branches of applying rows (True)"] = exp == got
    # recompute from the sections: R, X, B, rating, length; base sections carry Juan's per-km values
    err, bad_rating, bad_len = 0.0, 0, 0
    for _, r in der.iterrows():
        secs = json.loads(r.sections)
        R = sum(s["r"] * s["len"] / 1000 for s in secs)
        X = sum(s["x"] * s["len"] / 1000 for s in secs)
        B = sum(s["b"] * s["len"] / 1000 for s in secs)
        zb = r.from_voltage_kv ** 2 / float(m.get("sbase_mva", 100))
        for got_v, exp_v in ((r.resistance_ohm, R), (r.reactance_ohm, X), (r.susceptance_pu_total, B),
                             (r.resistance_pu, R / zb), (r.susceptance_pu_half, B / 2)):
            err = max(err, abs(got_v - exp_v) / max(abs(exp_v), 1e-15))
        for s in secs:
            if s["src"] == "base":
                for k, col in (("r", "base_resistance_ohm"), ("x", "base_reactance_ohm"), ("b", "base_susceptance_pu_total")):
                    err = max(err, abs(s[k] - r[col] / (r.base_length_m / 1000)) / max(abs(s[k]), 1e-15))
        full = all(s["src"] != "base" for s in secs)
        i_exp = min(s["i"] for s in secs)
        if full and m.get("rating_full", "new") == "min":
            i_exp = min(i_exp, r.base_max_current_a)
        bad_rating += abs(r.max_current_a - i_exp) > 1e-9
        bad_len += abs(sum(s["len"] for s in secs) - r.length_m) > 1e-6
    out["max relative error R, X, B, pu vs sections (independent recompute)"] = err
    out["rating not equal to min over sections (0)"] = int(bad_rating)
    out["length not equal to sum of sections (0)"] = int(bad_len)
    for e, sd in splits_done.items():
        parts = net[net.edge_id.isin([p for p, _, _ in sd["parts"]])]
        old = sum(sum(s["len"] for s in json.loads(x) if s["src"] == "base") for x in parts.sections)
        upg = parts.upgraded_length_m.astype(float).sum()
        out.setdefault("split: old line + upgraded length = original length (True)", True)
        if abs(old + upg - sd["L"]) > 1e-6:
            out["split: old line + upgraded length = original length (True)"] = False
    # connectivity
    adj = {}
    for r in net.itertuples():
        adj.setdefault(r.from_station_id, set()).add(r.to_station_id)
        adj.setdefault(r.to_station_id, set()).add(r.from_station_id)
    seen, comps = set(), []
    for n in adj:
        if n in seen:
            continue
        stack, comp = [n], set()
        while stack:
            x = stack.pop()
            if x not in comp:
                comp.add(x)
                stack.extend(adj[x] - comp)
        seen |= comp
        comps.append(comp)
    base_nodes = set(base.from_station_id) | set(base.to_station_id)
    out["islands with IP26 stations"] = "; ".join(
        ",".join(sorted(c)) for c in sorted(comps, key=len)[:-1] if c - base_nodes) or "none"
    return out


# --------------------------------------------------------------------------- new stations
def new_stations(base, net, points, info, scenario, horizon):
    """Buses of the final network that are not in full_network.csv: degree, connecting IP26 row(s), and what the
    IP2026 point file says about the project (type of work, congestion = demand/supply, MIEK)."""
    base_nodes = set(base.from_station_id) | set(base.to_station_id)
    rows = []
    for st in sorted((set(net.from_station_id) | set(net.to_station_id)) - base_nodes):
        e = net[(net.from_station_id == st) | (net.to_station_id == st)]
        others = sorted((set(e.from_station_id) | set(e.to_station_id)) - {st})
        oids = sorted({int(float(o)) for o in e.ip26_objectids.dropna().astype(str).str.split(";").explode()})
        nn = sorted({str(info.get(o, {}).get("n_nummer")) for o in oids})
        pt = points[points["nummer"].isin(nn)]
        cong = "; ".join(sorted(set(pt["congestie"].astype(str)))) if len(pt) else ""
        name = (e.from_station_name.where(e.from_station_id == st).dropna().tolist()
                + e.to_station_name.where(e.to_station_id == st).dropna().tolist())[0]
        kind = ("DSO substation (Liander): load connection" if "Liander" in name else
                "IP26 congestion type: demand and generation (Productie & Afname)" if "Productie" in cong and "Afname" in cong else
                "IP26 congestion type: demand (Afname)" if "Afname" in cong else
                "IP26 congestion type: generation (Productie)" if "Productie" in cong else
                "not stated in IP26 (congestie n.v.t.)")
        same_site = sorted(x for x in (set(net.from_station_id) | set(net.to_station_id))
                           if x != st and re.sub(r"\d+$", "", x) == re.sub(r"\d+$", "", st))
        if same_site:
            kind += f"; same site at another voltage: {', '.join(same_site)} (transformer not in the data)"
        rows.append({"scenario": scenario, "horizon": horizon, "station_id": st, "station_name": name,
                     "edges": len(e), "connected_to": ", ".join(others), "dead_end": len(others) == 1,
                     "ip26_objectids": ", ".join(map(str, oids)), "ip26_n_nummer": ", ".join(nn),
                     "ip26_project": "; ".join(sorted({str(info.get(o, {}).get("n_projectnaam")) for o in oids})),
                     "ip26_point_werkzaamheden": "; ".join(sorted(set(pt["werkzaamheden"].astype(str)))) if len(pt) else "",
                     "ip26_point_congestie": cong,
                     "ip26_point_miek": "; ".join(sorted(set(pt["p_nmiek"].astype(str)))) if len(pt) else "",
                     "what_connects_there": kind + ". Loads / generators (MW) are not in the IP26 data: to be "
                                                   "provided (Juan / TenneT / DSO)"})
    return rows


# --------------------------------------------------------------------------- output
def _exact_float_string(value):
    """openpyxl writes numbers with 16 significant digits ("%.16g"), which can change the last digit of a
    value (e.g. 235471.44819740244 -> 235471.4481974024). The final workbooks are written with the shortest
    exact representation (repr), so every value is stored exactly as computed / as in full_network.csv."""
    if isinstance(value, float):
        return "" if (math.isnan(value) or math.isinf(value)) else repr(value)
    return _openpyxl_safe_string(value)


import openpyxl.cell._writer as _ox_writer  # noqa: E402
_openpyxl_safe_string = _ox_writer.safe_string


def write_workbook(path, net, log):
    _ox_writer.safe_string = _exact_float_string
    try:
        with pd.ExcelWriter(path, engine="openpyxl") as xw:
            net.to_excel(xw, sheet_name="network", index=False)
            log.to_excel(xw, sheet_name="change_log", index=False)
            for ws in xw.book.worksheets:
                ws.freeze_panes = "B2"
                ws.auto_filter.ref = ws.dimensions
                for col in ws.columns:
                    ws.column_dimensions[col[0].column_letter].width = 16
    finally:
        _ox_writer.safe_string = _openpyxl_safe_string


def main(config_path=CONFIG_FILE):
    config_path = Path(config_path).resolve()
    with open(config_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    root = config_path.parent
    p = cfg["paths"]
    dec = {}
    if p.get("decisions_config"):
        with open(root / p["decisions_config"], encoding="utf-8") as f:
            dec = yaml.safe_load(f) or {}
    base = pd.read_csv(root / p["base_network"], float_precision="round_trip")
    st = pd.read_csv(root / p["stations_file"], float_precision="round_trip")
    geo = {"stations": {r.station_id: (r.x_rd, r.y_rd) for r in st.itertuples()},
           "endpoints": pd.read_csv(root / p["endpoints_file"], float_precision="round_trip")}
    points = pd.read_excel(root / p["points_file"])
    out_root = root / p["output_folder"]
    out_root.mkdir(parents=True, exist_ok=True)
    summary, stations = [], []
    for sc in cfg["scenarios"]:
        info = project_info(root / p["scenario_folder"] / p["scenario_pattern"].format(scenario=sc))
        for hz in cfg["horizons"]:
            hpath = root / p["horizon_folder"] / p["horizon_pattern"].format(scenario=sc, horizon=hz)
            if not hpath.exists():
                raise FileNotFoundError(f"{hpath} not found - run ip26_horizon_filter.py first")
            hdf = read_tab_values(hpath, str(p.get("horizon_tab", "1")))
            if "applies_to_listed_branches" not in hdf.columns:
                raise ValueError(f"{hpath.name} has no column applies_to_listed_branches - rerun ip26_horizon_filter.py")
            hdf["OBJECTID"] = hdf["edge_id"].str.extract(r"IP26-(\d+)")[0].astype(int)
            net, log, splits_done, copies = build(cfg, dec, base, hdf, info, read_line_types(hpath), geo, sc, hz)
            od = out_root / sc
            od.mkdir(parents=True, exist_ok=True)
            write_workbook(od / f"full_network_final_{sc}_{hz}.xlsx", net, log)
            chk = checks(cfg, dec, base, net, hdf, splits_done, copies, sc, hz)
            ns = new_stations(base, net, points, info, sc, hz)
            chk["new buses"] = len(ns)
            chk["new buses with one connection only"] = ", ".join(x["station_id"] for x in ns if x["dead_end"]) or "none"
            summary.append(chk)
            stations += ns
            print(f"{sc} {hz}: {chk['edges']} edges, {chk['buses']} buses = {chk['base (unchanged)']} base + "
                  f"{chk['derived']} derived ({chk['derived partial']} partial, {chk['derived by split']} from splits) + "
                  f"{chk['new (IP26)']} new; checks: base diff {chk['base rows differing from full_network.csv (0)']}, "
                  f"copies changed {chk['manual copies changed (0)']}, "
                  f"recompute err {chk['max relative error R, X, B, pu vs sections (independent recompute)']:.1e}, "
                  f"rating {chk['rating not equal to min over sections (0)']}, "
                  f"applied once {chk['changed branches = branches of applying rows (True)']}")
    m = cfg.get("modify") or {}
    rules = pd.DataFrame({"item": [
        "final network", "sections", "modify existing branch", "split (loop-in)", "one row per circuit",
        "route choice", "manual copies", "Verkabelen rows", "upgraded length", "full coverage", "rating", "type",
        "per-unit", "sn_mva", "new edges", "traceability"], "rule": [
        "Juan's full_network.csv + IP26 changes of the horizon workbook; untouched rows identical to full_network.csv",
        "every changed branch = sections in series; R, X, B = sum per-km x length; rating = min over sections",
        "rows with applies_to_listed_branches = yes: upgraded length of the old line replaced by the IP26 values; "
        "no new branch",
        "config_decisions.yaml splits: line cut at the new station (tap position, loop-in length), done before upgrades; "
        "the row's own edge is the loop-in and is not added",
        "config_decisions.yaml circuit_assignment (e.g. 290 -> G, 303 -> W)",
        "config_decisions.yaml route_choice (e.g. 302 via Nieuwe Meer)",
        "manual: copies of a real circuit are never changed; marked in manual_copy_of",
        f"Verkabelen rows marked overhead use the cable parameters: {dec.get('verkabelen_uses_cable_parameters', True)}",
        "IP26 length_m spread over the listed route in proportion to branch lengths; on split lines from the IP26 "
        "geometry (section_location); source per branch",
        f"IP26 length / route length >= {m.get('full_coverage_threshold', 0.7)}: whole branch upgraded",
        f"partial: min(old, new); full: {m.get('rating_full', 'new')}",
        f"fully upgraded branch: type = IP26 type ({m.get('type_on_full_coverage', 'ip26')}); otherwise Juan's type, "
        f"sections in section_types",
        f"Zbase = kV^2 / {m.get('sbase_mva', 100)} MVA; susceptance_pu_half = total / 2",
        str(m.get("sn_mva", "scale")) + " (scale = Juan's sn_mva x new rating / old rating)",
        f"new connection / extra circuits added: {cfg.get('add_new_edges', True)} (record_status new (IP26))",
        "record_status, ip26_* columns, split_from, manual_copy_of, base_* values, upgraded_length_m / _source, "
        "section_types, sections (JSON), change_note; change_log tab"]})
    with pd.ExcelWriter(out_root / "IP26_final_network_summary.xlsx", engine="openpyxl") as xw:
        pd.DataFrame(summary).to_excel(xw, sheet_name="Summary", index=False)
        pd.DataFrame(stations).to_excel(xw, sheet_name="New_stations", index=False)
        rules.to_excel(xw, sheet_name="Rules", index=False)
    print(f"\nResults in {out_root}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent / CONFIG_FILE)
