#!/usr/bin/env python3
"""
A8_build_patch_hv_150_110.py — patch that adds the Dutch 150 and 110 kV grid (2035) below the 380/220 kV workbook.

STEP  A8 in run_all_hv.sh (HANDOVER.md section 9). FIRST VERSION, to be checked.

WHAT IT DOES
  Reads the 2035 network written by the IP26 project matching code (hv_ip26/, step 5: GridAware's full_network.csv + the IP2026
  projects in service by 2035, study phase left out) and writes a patch with:
    nodes         every 150 and 110 kV bus that is connected to the 380/220 kV grid through a transformer. Bus name
                  HV-<station>_<kV>, e.g. HV-DIEMEN_150; zone NL; not a representative bus (eliminated in the reduction);
                  coordinates from TenneT's station layer (RD -> WGS84, published approximation).
    lines         every 150 and 110 kV line and cable between two such buses: X (ohm) and current (A) as in the 2035 network,
                  R = B = 0 (DC power flow), Capacity_MW = sqrt(3) x nominal kV x current (ASSUMPTION: JAO's convention uses the
                  operating voltage, 400 / 225 kV, and has no rule for 150 / 110 kV).
    transformers  every 380/150, 380/110 and 220/110 kV transformer of the 2035 network. The 380/220 kV side is matched to the
                  workbook bus of the same station (table node_diff.csv of patch jao2026_nl). X from the transformer's per-unit
                  reactance (100 MVA) referred to 380 or 220 kV as JAO does (Voltage_level = the high side), current from its
                  MVA rating with JAO's operating voltage (400 / 225 kV), so Capacity_MW = the MVA rating.
  Left out, and listed in dropped.csv: 380/220 kV lines and transformers (these come from JAO 2026 and our patches), 150/110 kV
  elements in pieces of grid without a transformer to 380/220 kV (they would be islands), transformers whose 380/220 kV station
  is not in the workbook.
  check_transformers.csv lists every Dutch 380/220 kV workbook bus whose station also has a 150 or 110 kV bus in the 2035 network
  but no transformer between them: likely missing transformers.

WHY
  The 150/110 kV grid runs in parallel to the 380/220 kV grid between the 380/150 kV stations, so part of the power between two
  380 kV stations flows over it. Without it the model sends all of that power over the 380/220 kV lines.

READS   <2035 network.csv> (hv_ip26/output_final_csv/<scenario>/full_network_final_<scenario>_2035/network.csv),
        hv_ip26/DATA/stations_tennet_arcgis.csv, inputs/patches/jao2026_nl/node_diff.csv, inputs/derived/jao_core_<base>/
WRITES  inputs/patches/<patch name>/ nodes_add.csv, lines_add.csv, transformers_add.csv, patch_metadata.csv, dropped.csv,
        check_transformers.csv, CHANGELOG.md, manifest.json. Aborts if it exists. Apply it with A5_apply_patches.py.

USAGE   python scripts/A8_build_patch_hv_150_110.py <2035 network.csv> <base version> <patch name>
        e.g. python scripts/A8_build_patch_hv_150_110.py hv_ip26/output_final_csv/median/full_network_final_median_2035/network.csv \\
                 v29-vvltr2-2035-tennet-tlb3-rt4k hv_150_110_2035

HISTORY New for the handover (3 Nov 2026).
"""
import datetime, hashlib, json, math, re, sys
from collections import defaultdict
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
LINE_COLS = ["Line_name", "EIC_Code", "From_node", "To_node", "Voltage_level", "Currrent_(A)", "R", "X", "B", "Length_km", "Capacity_MW"]
NODE_COLS = ["Bus", "IsRepresentative", "Type", "PD", "QD", "GS", "BS", "Area", "Vm", "Va", "baseKV", "Zone", "Vmax", "Vmin", "Latitude", "Longitude"]
K_OP = {380: 400.0, 220: 225.0}          # JAO's operating voltage per nominal level (MW = sqrt(3) x K x kA)
HV = (150, 110)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def rd_to_wgs84(x, y):
    """RD New (EPSG:28992) -> WGS84, the published approximation (accurate to about 1 m in the Netherlands)."""
    dx, dy = (x - 155000) * 1e-5, (y - 463000) * 1e-5
    K = {(0, 1): 3235.65389, (2, 0): -32.58297, (0, 2): -0.2475, (2, 1): -0.84978, (0, 3): -0.0665, (2, 2): -0.01709,
         (1, 0): -0.00738, (4, 0): 0.0053, (2, 3): -0.00039, (4, 1): 0.00033, (1, 1): -0.00012}
    L = {(1, 0): 5260.52916, (1, 1): 105.94684, (1, 2): 2.45656, (3, 0): -0.81885, (1, 3): 0.05594, (3, 1): -0.05607,
         (0, 1): 0.01199, (3, 2): -0.00256, (1, 4): 0.00128, (0, 2): 0.00022, (2, 0): -0.00022, (5, 0): 0.00026}
    lat = 52.15517440 + sum(c * dx ** p * dy ** q for (p, q), c in K.items()) / 3600
    lon = 5.38720621 + sum(c * dx ** p * dy ** q for (p, q), c in L.items()) / 3600
    return round(lat, 4), round(lon, 4)


def bus_name(station_name, node_id, kv):
    """HV-<STATION>_<kV> from 'Station Diemen 150' (or from the node code when there is no proper name)."""
    s = re.sub(r"^Station\s+", "", str(station_name)).strip()
    s = re.sub(rf"\s*{kv}(\s*kV)?$", "", s).strip()
    if not s or s.upper().replace(" ", "") == node_id.upper():
        s = node_id[: -len(str(kv))] if node_id.endswith(str(kv)) else node_id
    s = re.sub(r"[^A-Za-z0-9 /.-]", "", s).upper().replace("/", "-")
    return f"HV-{s}_{kv}"


def main():
    if len(sys.argv) != 4:
        sys.exit(__doc__)
    net_f, base, name = Path(sys.argv[1]).resolve(), sys.argv[2], sys.argv[3]
    out = ROOT / "inputs" / "patches" / name
    if out.exists():
        sys.exit(f"ABORT: {out} exists")
    wb_f = ROOT / "inputs" / "derived" / f"jao_core_{base}" / "jao_core.xlsx"
    st_f, nd_f = ROOT / "hv_ip26" / "DATA" / "stations_tennet_arcgis.csv", ROOT / "inputs" / "patches" / "jao2026_nl" / "node_diff.csv"
    net = pd.read_csv(net_f)
    wb_buses = set(pd.read_excel(wb_f, sheet_name="Nodes").Bus)
    st = pd.read_csv(st_f).set_index("station_id")
    nd = pd.read_csv(nd_f)

    # 380/220 kV station of GridAware -> workbook bus (follow "merged into X" of the builder)
    ehv_bus = {}
    for r in nd.itertuples():
        b = r.jao_bus
        m = re.search(r"merged into (\S+)", str(r.status))
        if isinstance(b, str) and b not in wb_buses and m:
            b = m.group(1)
        if isinstance(b, str) and b in wb_buses:
            ehv_bus[r.station_id] = b

    node = lambda s: str(s).replace("node:", "")
    net["a"], net["b"] = net.from_node_id.map(node), net.to_node_id.map(node)
    lo, hi = net[["from_voltage_kv", "to_voltage_kv"]].min(axis=1), net[["from_voltage_kv", "to_voltage_kv"]].max(axis=1)
    is_tr = net.type.eq("transformer")
    lines = net[~is_tr & lo.isin(HV) & hi.isin(HV) & net.manual_copy_of.isna()].copy()
    trs = net[is_tr & lo.isin(HV) & hi.isin(K_OP)].copy()
    dropped = [dict(edge_id=r.edge_id, reason="380/220 kV element: taken from JAO 2026 and our patches") for r in net[hi.isin(K_OP) & ~(is_tr & lo.isin(HV))].itertuples()]
    dropped += [dict(edge_id=r.edge_id, reason="manual copy of another circuit") for r in net[~is_tr & lo.isin(HV) & net.manual_copy_of.notna()].itertuples()]

    # transformers whose 380/220 kV side is in the workbook
    hv_side = lambda r: (r.a, r.b) if r.from_voltage_kv > r.to_voltage_kv else (r.b, r.a)      # (high side, low side)
    keep_tr = []
    for r in trs.itertuples():
        h, l = hv_side(r)
        if h in ehv_bus:
            keep_tr.append((r, ehv_bus[h], l))
        else:
            dropped.append(dict(edge_id=r.edge_id, reason=f"380/220 kV station {h} not in the workbook"))

    # pieces of the 150/110 kV grid that reach a kept transformer
    adj = defaultdict(set)
    for r in lines.itertuples():
        adj[r.a].add(r.b); adj[r.b].add(r.a)
    reach, todo = set(), [l for _, _, l in keep_tr]
    while todo:
        n = todo.pop()
        if n not in reach:
            reach.add(n); todo += list(adj[n])
    island = ~(lines.a.isin(reach) & lines.b.isin(reach))
    dropped += [dict(edge_id=r.edge_id, reason="150/110 kV piece without a transformer to 380/220 kV") for r in lines[island].itertuples()]
    lines = lines[~island]

    # buses
    kv_of, name_of = {}, {}
    for r in net.itertuples():
        kv_of[r.a], name_of[r.a] = int(r.from_voltage_kv), r.from_station_name
        kv_of[r.b], name_of[r.b] = int(r.to_voltage_kv), r.to_station_name
    sid_of = dict(zip(net.a, net.from_station_id)) | dict(zip(net.b, net.to_station_id))
    bus, nodes, seen = {}, [], set()
    for n in sorted(reach):
        b = bus_name(name_of[n], n, kv_of[n])
        if b in seen or b in wb_buses:
            b = f"HV-{n}_{kv_of[n]}"
        seen.add(b); bus[n] = b
        sid = sid_of.get(n)
        lat, lon = rd_to_wgs84(st.loc[sid, "x_rd"], st.loc[sid, "y_rd"]) if sid in st.index else (math.nan, math.nan)
        nodes.append([b, 0, 1, 0, 0, 0, 0, "NL", 1, 0, kv_of[n], "NL", 1.1, 0.9, lat, lon])

    # buses without a station in TenneT's layer (wind parks, DSO substations): coordinates of the nearest connected bus with
    # coordinates (breadth-first over the 150/110 kV lines); used for maps only, not by any calculation
    have = {r[0]: (r[14], r[15]) for r in nodes if not math.isnan(r[14])}
    inv = {v: k for k, v in bus.items()}
    approx = []
    for r in nodes:
        if not math.isnan(r[14]):
            continue
        seen_b, front = {inv[r[0]]}, [inv[r[0]]]
        while front:
            nxt = []
            for n in front:
                for m in adj[n]:
                    if m in seen_b or m not in bus:
                        continue
                    seen_b.add(m); nxt.append(m)
                    if bus[m] in have and math.isnan(r[14]):
                        r[14], r[15] = have[bus[m]]
            front = nxt
            if not math.isnan(r[14]):
                break
        if math.isnan(r[14]):
            hb = next((h for _, h, l in keep_tr if bus[l] == r[0]), None)
            sid = next((g for g, b2 in ehv_bus.items() if b2 == hb), None)
            if sid in st.index:
                r[14], r[15] = rd_to_wgs84(st.loc[sid, "x_rd"], st.loc[sid, "y_rd"])
        approx.append(r[0])

    rows_l, rows_t, meta = [], [], []
    for k, r in enumerate(lines.itertuples(), start=1):
        kv = int(r.from_voltage_kv); eic = f"GA35-HV-{k:04d}"; cur = float(r.max_current_a)
        rows_l.append([r.edge_id.replace("branch:", ""), eic, bus[r.a], bus[r.b], kv, cur, 0.0, float(r.reactance_ohm), 0.0,
                       float(r.length_m) / 1000, round(math.sqrt(3) * kv * cur / 1000, 3)])
        meta.append(dict(patch_id=eic, sheet="Lines", row=r.edge_id, source="2035 network of the IP26 project matching (GridAware + IP2026)",
                         conversion="X and current copied; R = B = 0; MW = sqrt(3) x nominal kV x A", record_status=r.record_status,
                         ip26_project=r.ip26_project if isinstance(r.ip26_project, str) else ""))
    for k, (r, hb, l) in enumerate(keep_tr, start=1):
        kv = 380 if hb.endswith("_380") else 220; eic = f"GA35-TR-{k:04d}"
        x = float(r.reactance_pu) * kv ** 2 / 100.0
        cur = float(r.sn_mva) / (math.sqrt(3) * K_OP[kv]) * 1000
        rows_t.append([f"TR {hb.rsplit('_', 1)[0].title()} {kv}/{kv_of[l]}", eic, hb, bus[l], kv, round(cur, 2), 0.0, round(x, 6), 0.0, 0.0,
                       round(math.sqrt(3) * K_OP[kv] * cur / 1000, 3)])
        meta.append(dict(patch_id=eic, sheet="Transformers", row=r.edge_id, source="2035 network of the IP26 project matching (GridAware)",
                         conversion=f"X = {r.reactance_pu} pu x {kv}^2/100; current = {r.sn_mva} MVA / (sqrt(3) x {K_OP[kv]:g} kV)",
                         record_status=r.record_status, ip26_project=""))

    # stations with a 380/220 kV workbook bus and a 150/110 kV bus of the same name but no transformer
    tr_pairs = {(hb, bus[l]) for _, hb, l in keep_tr}
    code = lambda n: re.sub(r"\d+$", "", n)
    chk = []
    for g, hb in ehv_bus.items():
        if not isinstance(g, str) or not hb.endswith(("_380", "_220")) or not g[-3:].isdigit():
            continue
        for n in reach:
            if code(n) == code(g) and not any(p[0] == hb and p[1] == bus[n] for p in tr_pairs):
                chk.append(dict(workbook_bus=hb, hv_bus=bus[n], note="same station code, no transformer in the 2035 network"))

    out.mkdir(parents=True)
    pd.DataFrame(nodes, columns=NODE_COLS).to_csv(out / "nodes_add.csv", index=False)
    pd.DataFrame(rows_l, columns=LINE_COLS).to_csv(out / "lines_add.csv", index=False)
    pd.DataFrame(rows_t, columns=LINE_COLS).to_csv(out / "transformers_add.csv", index=False)
    pd.DataFrame(meta).to_csv(out / "patch_metadata.csv", index=False)
    pd.DataFrame(dropped).to_csv(out / "dropped.csv", index=False)
    pd.DataFrame(chk, columns=["workbook_bus", "hv_bus", "note"]).to_csv(out / "check_transformers.csv", index=False)
    n150, n110 = sum(1 for x in nodes if x[10] == 150), sum(1 for x in nodes if x[10] == 110)
    (out / "CHANGELOG.md").write_text(
        f"# Patch `{name}` (base {base}): the Dutch 150/110 kV grid of 2035, FIRST VERSION\n\n"
        f"Built {datetime.date.today()} by `scripts/{Path(__file__).name}` from `{net_f.name}` "
        f"({net_f.parent.name}).\n\n"
        f"- buses added: {len(nodes)} ({n150} at 150 kV, {n110} at 110 kV)\n- lines and cables added: {len(rows_l)}\n"
        f"- transformers added: {len(rows_t)}\n- left out: {len(dropped)} elements (dropped.csv)\n"
        f"- stations to check for a missing transformer: {len(chk)} (check_transformers.csv)\n"
        f"- buses with approximate coordinates (nearest connected bus; not in TenneT's station layer): {len(approx)}: {', '.join(approx)}\n")
    (out / "manifest.json").write_text(json.dumps({
        "status": "finished", "finished": datetime.datetime.now().isoformat(timespec="seconds"),
        "config": {"script": Path(__file__).name, "base_version": base, "network": str(net_f)},
        "inputs_sha256": {"network.csv": sha(net_f), "stations": sha(st_f), "node_diff.csv": sha(nd_f), "jao_core.xlsx": sha(wb_f)},
        "outputs_sha256": {p.name: sha(p) for p in sorted(out.iterdir())}}, indent=1))
    print(f"written {out}: {len(nodes)} buses, {len(rows_l)} lines, {len(rows_t)} transformers, {len(dropped)} left out, {len(chk)} to check")


if __name__ == "__main__":
    main()
