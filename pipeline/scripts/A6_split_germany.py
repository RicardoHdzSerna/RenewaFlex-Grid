#!/usr/bin/env python3
"""
A6_split_germany.py — copy of a workbook in which Germany is two zones, north (DE_N) and south (DE_S).

STEP  A6 in run_all.sh (HANDOVER.md section 2.7). Only for the network variants with Germany split ("-de2").

WHAT IT DOES
  Gives every German bus the zone DE_N or DE_S (column Zone of the Nodes sheet) and marks one representative bus per half.
  Rule, following ACER Decision 11/2022, Annex VI, "Nodes to BZ - DE2 - German TSOs" (J1 = north, J2 = south; copy in
  inputs/external/acer_decision_11_2022/). ACER's node names are model codes without coordinates, so buses are matched by TSO:
    1. the TSO of a German bus = the TSO of most JAO rows touching it (raw JAO file, matched on EIC);
    2. 50Hertz -> north; Amprion and TransnetBW -> south; TenneT Germany -> north at latitude >= 51.79 (between Elsen 51.77 and
       Voerden 51.81), else south; Niederlangen -> south (ACER code NLAN in J2, assumed to be Niederlangen);
    3. any other German bus -> the zone of most of its German neighbours (repeated until nothing changes).
  Representative buses: south keeps ROMMERSKIRCHEN_380 (the German representative of every earlier network); north gets the
  north 380 kV bus with the smallest mean electrical distance to all north 380 kV buses, border buses excluded (WOLMIRSTEDT_380).
  No line, rating or reactance is changed.

READS   inputs/derived/jao_core_<source>/, inputs/raw/202603_Core Static Grid Model_External.xlsx (TSO of each row),
        inputs/external/acer_decision_11_2022/
WRITES  inputs/derived/jao_core_<new>/  byte copies of the source + jao_core.xlsx with the new zones, de2_bus_zones.csv,
        sha256.txt, manifest.json. Aborts if it exists.

USAGE   python scripts/A6_split_germany.py <source version> <new version>
        e.g. python scripts/A6_split_germany.py v29-vvltr2-2035-tennet-tlb3-rt4k v29-vvltr2-2035-tennet-tlb3-rt4k-de2

HISTORY Same code as core_grid_dcopf/scripts/29_de2_split_workbook.py (25 Oct 2026); only this header was rewritten.
"""
import collections, datetime, glob, hashlib, json, shutil, sys
from pathlib import Path

import numpy as np, openpyxl, pandas as pd
import scipy.sparse as sp, scipy.sparse.linalg as sla

DCOPF = Path(__file__).resolve().parents[1]
RAW = DCOPF / "inputs" / "raw" / "202603_Core Static Grid Model_External.xlsx"
ACER = DCOPF / "inputs" / "external" / "acer_decision_11_2022"
TENNET_LAT = 51.79
TENNET_SOUTH_EXCEPTIONS = {"NIEDERLANGEN_380", "Y-NIEDERLANGEN_380"}
NORTH_TSO, SOUTH_TSO = {"50HERTZ"}, {"AMPRION GMBH", "TRANSNETBW"}


def sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def same(a, b):
    try:
        return abs(float(a) - float(b)) <= 1e-9 * max(1.0, abs(float(b)))
    except (TypeError, ValueError):
        return str(a) == str(b)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    SRC_V, NEW_V = args
    SRC, OUT = DCOPF / "inputs" / "derived" / f"jao_core_{SRC_V}", DCOPF / "inputs" / "derived" / f"jao_core_{NEW_V}"
    if OUT.exists():
        sys.exit(f"ABORT: {OUT} exists — never overwritten")
    acer_file = Path(glob.glob(str(ACER / "annex_vi" / "*" / "2. Nodes to BZ - DE2*.xlsx"))[0])
    w = pd.read_excel(SRC / "jao_core.xlsx", sheet_name=None); N = w["Nodes"]
    raw = pd.read_excel(RAW, sheet_name=None, header=1)
    tso_by_eic = {}
    for s in ("Lines", "Tielines", "Transformers"):
        tso_by_eic.update(dict(zip(raw[s]["EIC_Code"].astype(str), raw[s]["TSO"].astype(str))))
    sm = pd.read_csv(SRC / "substation_map.csv").set_index("bus")
    de = set(N[N.Zone == "DE"].Bus)
    if not de:
        sys.exit("ABORT: no German buses (Zone == DE) in the source")
    votes = collections.defaultdict(collections.Counter); nbr = collections.defaultdict(set); edges = []
    for s in ("Lines", "Tielines", "Transformers"):
        for r in w[s].itertuples():
            t = tso_by_eic.get(str(r.EIC_Code))
            for b in (r.From_node, r.To_node):
                if b in de and t:
                    votes[b][t] += 1
            nbr[r.From_node].add(r.To_node); nbr[r.To_node].add(r.From_node); edges.append((r.From_node, r.To_node))
    tso = {b: (votes[b].most_common(1)[0][0] if votes[b] else "NONE") for b in de}
    lat = {b: (float(sm.lat[b]) if b in sm.index and pd.notna(sm.lat[b]) else np.nan) for b in de}
    zone, rule = {}, {}
    for b in sorted(de):
        if tso[b] in NORTH_TSO:
            zone[b], rule[b] = "DE_N", "TSO 50Hertz"
        elif tso[b] in SOUTH_TSO:
            zone[b], rule[b] = "DE_S", f"TSO {tso[b]}"
        elif tso[b] == "TENNETGMBH" and b in TENNET_SOUTH_EXCEPTIONS:
            zone[b], rule[b] = "DE_S", "TenneT, ACER code NLAN in J2 (assumed Niederlangen)"
        elif tso[b] == "TENNETGMBH" and np.isfinite(lat[b]):
            zone[b], rule[b] = ("DE_N", f"TenneT, lat >= {TENNET_LAT}") if lat[b] >= TENNET_LAT else ("DE_S", f"TenneT, lat < {TENNET_LAT}")
    for _ in range(50):                                               # rule 3: majority of German neighbours
        new = {}
        for b in sorted(de - set(zone)):
            c = collections.Counter(zone[n] for n in nbr[b] if n in zone)
            if c and c.most_common(1)[0][1] > sum(c.values()) / 2:
                new[b] = c.most_common(1)[0][0]
        if not new:
            break
        for b, z in new.items():
            zone[b], rule[b] = z, f"neighbours (TSO {tso[b]})"
    left = de - set(zone)
    if left:
        sys.exit(f"ABORT: German buses without a zone: {sorted(left)}")
    # DE_N representative: most central DE_N 380 kV bus, not a border terminal (DC, p.u. on nominal kV)
    zall = dict(zip(N.Bus, N.Zone)); zall.update(zone)
    br = pd.concat([w[s] for s in ("Lines", "Tielines", "Transformers")], ignore_index=True)
    br = br[(br.From_node != br.To_node) & (br.X.astype(float) > 0)]
    vl = br.Voltage_level.astype(float).where(br.Voltage_level.astype(float) > 0, 380.0); y = 1.0 / (br.X.astype(float) / (vl ** 2 / 100.0)).to_numpy()
    buses = sorted(set(br.From_node) | set(br.To_node)); ix = {b: i for i, b in enumerate(buses)}; nb = len(buses)
    f = br.From_node.map(ix).to_numpy(); t = br.To_node.map(ix).to_numpy()
    B = sp.coo_matrix((np.r_[y, y, -y, -y], (np.r_[f, t, f, t], np.r_[f, t, t, f])), shape=(nb, nb)).tocsc()
    gnd = ix["ROMMERSKIRCHEN_380"]; keep = [i for i in range(nb) if i != gnd]; Br = B[keep][:, keep].tocsc(); lu = sla.splu(Br)
    north380 = [b for b in buses if zall.get(b) == "DE_N" and b.endswith("_380")]
    border = {b for b, c in edges for b in (b,) if False}                 # placeholder, filled below
    border = {a for a, c in edges if zall.get(a) != zall.get(c)} | {c for a, c in edges if zall.get(a) != zall.get(c)}
    cols = {}
    for b in north380:
        e = np.zeros(nb - 1); e[keep.index(ix[b])] = 1.0; cols[b] = lu.solve(e)
    kpos = {b: keep.index(ix[b]) for b in north380}
    Zd = lambda i, j: cols[i][kpos[i]] + cols[j][kpos[j]] - 2 * cols[i][kpos[j]]
    cand = [b for b in north380 if b not in border and not b.startswith("Y-")]
    dist = {b: float(np.mean([Zd(b, j) for j in north380])) for b in cand}
    rep_n = min(dist, key=dist.get)
    # ---- write
    src_hashes = {p.name: sha(p) for p in sorted(SRC.iterdir()) if p.is_file()}
    OUT.mkdir(parents=False)
    for p in sorted(SRC.iterdir()):
        if p.is_file():
            shutil.copyfile(p, OUT / p.name)
    xl = openpyxl.load_workbook(OUT / "jao_core.xlsx"); ws = xl["Nodes"]; hdr = {c.value: c.column for c in ws[1]}
    changes = []
    for r in range(2, ws.max_row + 1):
        bus = ws.cell(r, hdr["Bus"]).value
        if bus in zone:
            ws.cell(r, hdr["Zone"]).value = zone[bus]; changes.append(("Zone", bus))
            if "Area" in hdr and ws.cell(r, hdr["Area"]).value == "DE":
                ws.cell(r, hdr["Area"]).value = zone[bus]; changes.append(("Area", bus))
        if bus == rep_n:
            ws.cell(r, hdr["IsRepresentative"]).value = 1; changes.append(("IsRepresentative", bus))
    xl.save(OUT / "jao_core.xlsx")
    back = pd.read_excel(OUT / "jao_core.xlsx", sheet_name=None)
    for s in w:
        a, b = w[s], back[s]
        if a.shape != b.shape or list(a.columns) != list(b.columns):
            sys.exit(f"ABORT: read-back: sheet {s} changed shape")
        for col in a.columns:
            x, yv = a[col].astype(str).to_numpy(), b[col].astype(str).to_numpy()
            bad = [int(i) for i in np.flatnonzero(x != yv) if not same(x[i], yv[i])]
            allowed = {bb for c, bb in changes if c == col} if s == "Nodes" else set()
            if bad and (s != "Nodes" or set(a.Bus.iloc[bad]) - allowed):
                sys.exit(f"ABORT: read-back: unexpected change in {s}.{col}")
    reps = back["Nodes"][back["Nodes"].IsRepresentative == 1][["Bus", "Zone"]]
    if set(reps[reps.Zone.isin(["DE_N", "DE_S"])].Bus) != {rep_n, "ROMMERSKIRCHEN_380"}:
        sys.exit(f"ABORT: German representatives are {sorted(reps[reps.Zone.str.startswith('DE')].Bus)}")
    zt = pd.DataFrame({"bus": sorted(de)}); zt["kv"] = zt.bus.str.rsplit("_", n=1).str[1]; zt["tso"] = zt.bus.map(tso); zt["lat"] = zt.bus.map(lat)
    zt["zone"] = zt.bus.map(zone); zt["rule"] = zt.bus.map(rule); zt.to_csv(OUT / "de2_bus_zones.csv", index=False)
    with open(OUT / "sha256.txt", "w") as fh:
        for p in sorted(OUT.iterdir()):
            if p.name not in ("sha256.txt", "manifest.json"):
                fh.write(f"{sha(p)}  {p.name}\n")
    if (SRC / "manifest.json").exists():
        shutil.copyfile(SRC / "manifest.json", OUT / "manifest_source.json")
    top = sorted(dist.items(), key=lambda kv: kv[1])[:5]
    man = {"status": "finished", "written": datetime.datetime.now().isoformat(timespec="seconds"), "script": Path(__file__).name, "script_sha256": sha(Path(__file__)),
           "source_version": SRC_V, "source_sha256": src_hashes, "acer_node_list": str(acer_file.relative_to(DCOPF)), "acer_node_list_sha256": sha(acer_file), "raw_sgm_sha256": sha(RAW),
           "rules": {"50HERTZ": "DE_N", "AMPRION GMBH, TRANSNETBW": "DE_S", "TENNETGMBH": f"DE_N if lat >= {TENNET_LAT} else DE_S; exceptions -> DE_S: {sorted(TENNET_SOUTH_EXCEPTIONS)}", "other": "majority of German neighbours"},
           "counts": dict(collections.Counter(zone.values())), "counts_380kV": dict(collections.Counter(z for b, z in zone.items() if b.endswith("_380"))),
           "by_rule": dict(collections.Counter(rule.values())), "rep_DE_N": rep_n, "rep_DE_N_mean_distance_pu": dist[rep_n], "rep_DE_N_top5": top, "rep_DE_S": "ROMMERSKIRCHEN_380 (kept from the source)",
           "n_changes": len(changes), "validation_data_read": "none"}
    (OUT / "manifest.json").write_text(json.dumps(man, indent=1))
    print(json.dumps({k: man[k] for k in ("counts", "counts_380kV", "by_rule", "rep_DE_N", "rep_DE_N_top5")}, indent=1)); print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
