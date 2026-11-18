"""Float Glass Line 1: Monitor dashboards, in Monitor's own dashboard format.

    python monitor_dashboards.py --key-file ~/.mas-control-room/monitor-api.properties \
        --api https://wsp.api.monitor.<mas-domain>

  FG_LINE   "Line 1 - live on the line drawing": IMAGE card on img/line.jpg, one marker per area (from the L1-LINE roll-up)
  FG_LINE   "Line 1 - production efficiency": yield, packed tonnes, loss, line state, 14 days
  FG_FURNACE / FG_TINBATH / FG_LEHR / FG_COLDEND: one dashboard per area
Re-runnable: dashboards are updated in place by title. Raw metrics carry their MQTT event name; calculated ones do not.
"""
import argparse
import json
import os
import ssl
import sys
import urllib.request
import uuid as _uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tic40-demo"))
from monitor_setup import Monitor, items  # noqa: E402

HERE = Path(__file__).parent
NS = _uuid.UUID("5a0e3f2c-1b7d-4c8e-9f60-2d4b8a1c7e31")
EV = {"FG_FURNACE": "furnace", "FG_TINBATH": "tinbath", "FG_LEHR": "lehr", "FG_COLDEND": "coldend", "FG_LINE": "line", "FG_RIBBON": "ribbon"}
CALC = {"SPEC_ENERGY", "LOSS_TPD", "O2_ANOMALY", "O2_EXPECTED", "AIR_INGRESS", "P_EXPECTED", "P_DEFICIT", "RIBBON_TPD", "MASS_GAP"}
DAYS = 14
DT = None
GREEN = {"color": "#24a148", "icon": "Checkmark"}
RED = {"color": "#da1e28", "icon": "Warning"}
AMBER = {"color": "#f1c21b", "icon": "Warning"}


def _id(k):
    return str(_uuid.uuid5(NS, k))


def _attr(m, a, dt=None):
    x = {"id": f"{m}_{a}", "attribute": m, "aggregator": a}
    if m not in CALC:
        x["eventName"] = EV[dt or DT]
    return x


def value(k, title, its, size="MEDIUMWIDE"):
    return {"id": _id(k), "title": title, "size": size, "type": "VALUE", "timeRange": "lastHour",
            "content": {"attributes": [{"dataSourceId": f"{m}_{a}", "label": lb, "unit": u, "precision": p} for m, a, lb, u, p in its]},
            "dataSource": {"range": {"interval": "hour", "count": -1, "type": "rolling"}, "attributes": [_attr(m, a) for m, a, *_ in its]}}


def trend(k, title, series, ylabel, days=DAYS, grain="hour", size="LARGEWIDE"):
    rng = {"interval": "day", "count": -days, "type": "rolling"} if days > 1 else {"interval": "hour", "count": -24, "type": "rolling"}
    return {"id": _id(k), "title": title, "size": size, "type": "TIMESERIES",
            "timeRange": "last7Days" if days > 1 else "last24Hours",
            "content": {"series": [{"dataSourceId": f"{m}_{a}", "label": lb} for m, a, lb in series],
                        "xLabel": "Time", "yLabel": ylabel, "includeZeroOnYaxis": False, "timeDataSourceId": "timestamp"},
            "dataSource": {"range": rng, "timeGrain": grain, "attributes": [_attr(m, a) for m, a, _ in series]}}


def recent(k, title, series, ylabel, hours=3, size="LARGEWIDE"):
    """Trend over the last few hours, raw points (no time grain) (the twins' calculated metrics start when they were created)."""
    return {"id": _id(k), "title": title, "size": size, "type": "TIMESERIES", "timeRange": "last24Hours",
            "content": {"series": [{"dataSourceId": f"{m}_{a}", "label": lb} for m, a, lb in series],
                        "xLabel": "Time", "yLabel": ylabel, "includeZeroOnYaxis": False, "timeDataSourceId": "timestamp"},
            "dataSource": {"range": {"interval": "hour", "count": -hours, "type": "rolling"},
                           "attributes": [_attr(m, a) for m, a, _ in series]}}


def dashboards():
    global DT
    out = {}
    DT = "FG_LINE"
    out["line_eff"] = (DT, {"title": "Line 1 - production efficiency", "cards": [
        value("ln-now", "Line 1 now", [("YIELD", "last", "Pack-to-melt yield", "%", 1), ("PACKED_TPD", "last", "Packed", "t/day", 0),
                                       ("THICKNESS", "last", "Product", "mm", 0),
                                       ("STATE", "last", "State (2 production)", "", 0)]),
        trend("ln-yield", f"Pack-to-melt yield, last 7 days", [("YIELD", "mean", "Yield %"), ("YIELD", "min", "Lowest")], "%"),
        trend("ln-tpd", f"Pull rate and packed glass, last 7 days", [("PULL_RATE", "mean", "Melted t/day"), ("PACKED_TPD", "mean", "Packed t/day")], "t/day"),
        trend("ln-drivers", f"Defects and furnace crown, last 7 days", [("DEFECTS", "max", "Defects /10 m²")], "/10 m²", size="MEDIUMWIDE"),
        trend("ln-state", f"Line state and product, last 7 days", [("STATE", "min", "State (0 stop, 1 job change, 2 production)"),
                                                                       ("THICKNESS", "max", "Thickness mm")], "", size="MEDIUMWIDE"),
    ]})
    DT = "FG_FURNACE"
    out["furnace"] = (DT, {"title": "Furnace - melting and energy", "cards": [
        value("fu-now", "Furnace now", [("CROWN_TEMP", "last", "Crown", "°C", 0), ("GAS_FLOW", "last", "Gas", "Nm³/h", 0),
                                        ("GAS_PRESSURE", "last", "Gas supply", "mbar", 0), ("PULL_RATE", "last", "Pull", "t/day", 0),
                                        ("SPEC_ENERGY", "last", "Energy", "GJ/t", 2)]),
        trend("fu-crown", f"Crown temperature, last 7 days", [("CROWN_TEMP", "mean", "Crown °C"), ("CROWN_TEMP", "min", "Lowest")], "°C"),
        trend("fu-gas", f"Gas supply pressure, last 7 days", [("GAS_PRESSURE", "min", "Supply mbar (lowest)")], "mbar", size="MEDIUMWIDE"),
        trend("fu-flow", f"Gas flow, last 7 days", [("GAS_FLOW", "mean", "Nm³/h")], "Nm³/h", size="MEDIUMWIDE"),
        trend("fu-regen", "Regenerator tops, last 24 h (firing reversal every 20 min)", [("REGEN_LEFT", "mean", "Left"), ("REGEN_RIGHT", "mean", "Right")],
              "°C", days=1, grain="hour"),
    ]})
    DT = "FG_TINBATH"
    out["tinbath"] = (DT, {"title": "Tin bath - atmosphere and ribbon", "cards": [
        value("tb-now", "Tin bath now", [("ATM_O2", "last", "O2", "ppm", 1), ("ATM_H2", "last", "H2", "%", 1), ("BATH_PRESSURE", "last", "Pressure", "Pa", 1),
                                         ("RIBBON_SPEED", "last", "Ribbon", "m/min", 1), ("O2_ANOMALY", "max", "O2 anomaly score", "", 2)]),
        trend("tb-o2", f"Bath atmosphere O2, last 7 days", [("ATM_O2", "max", "O2 ppm (highest)"), ("ATM_O2", "mean", "O2 ppm")], "ppm"),
        trend("tb-p", f"Bath pressure, last 7 days", [("BATH_PRESSURE", "min", "Pa (lowest)")], "Pa", size="MEDIUMWIDE"),
        trend("tb-h2", f"Hydrogen flow, last 7 days", [("H2_FLOW", "mean", "Nm³/h")], "Nm³/h", size="MEDIUMWIDE"),
        trend("tb-anom", "O2 anomaly score, last 24 h", [("O2_ANOMALY", "max", "Score")], "score", days=1),
    ]})
    out["tin_twin"] = (DT, {"title": "Tin bath twin - atmosphere", "cards": [
        value("tt-now", "Measured against the twin", [("ATM_O2", "last", "O2 measured", "ppm", 1), ("O2_EXPECTED", "last", "O2 the twin expects", "ppm", 1),
                                                     ("AIR_INGRESS", "last", "Air getting in", "L/min", 1),
                                                     ("BATH_PRESSURE", "last", "Pressure measured", "Pa", 1), ("P_EXPECTED", "last", "Pressure the twin expects", "Pa", 1)]),
        value("tt-what", "What the twin concludes", [("AIR_INGRESS", "last", "Air getting in", "L/min", 1),
                                                    ("P_DEFICIT", "last", "Pressure below expected", "Pa", 1), ("O2_ANOMALY", "max", "O2 anomaly score", "", 1)]),
        # calculated metrics have history only from the day their function was created, and render at hourly grain
        trend("tt-air", "Air getting in (twin), hourly", [("AIR_INGRESS", "max", "L/min (highest)"), ("AIR_INGRESS", "mean", "L/min")], "L/min"),
        trend("tt-o2", "O2: measured against what a sealed bath holds", [("ATM_O2", "mean", "Measured ppm"), ("O2_EXPECTED", "mean", "Twin expects ppm")],
              "ppm", size="MEDIUMWIDE"),
        trend("tt-p", "Bath pressure: measured against the gas flow", [("BATH_PRESSURE", "mean", "Measured Pa"), ("P_EXPECTED", "mean", "Twin expects Pa")],
              "Pa", size="MEDIUMWIDE"),
    ]})
    DT = "FG_RIBBON"
    out["ribbon_twin"] = (DT, {"title": "Ribbon twin - mass balance", "cards": [
        value("rt-now", "Glass in, glass out", [("WEIGHER_TPD", "last", "Batch weigher", "t/day", 0), ("RIBBON_TPD", "last", "Ribbon carries (twin)", "t/day", 0),
                                                ("MASS_GAP", "last", "Gap", "%", 1), ("THICKNESS", "last", "Thickness measured", "mm", 2)]),
        trend("rt-tpd", "Glass in and glass out, hourly", [("WEIGHER_TPD", "mean", "Batch weigher t/day"), ("RIBBON_TPD", "mean", "Ribbon carries t/day")], "t/day"),
        trend("rt-gap", "Mass balance gap, hourly (alert above 1 %)", [("MASS_GAP", "mean", "Gap %")], "%", size="MEDIUMWIDE"),
    ]})
    DT = "FG_LEHR"
    out["lehr"] = (DT, {"title": "Annealing lehr - zones and stress", "cards": [
        value("lh-now", "Lehr now", [("ZONE_A", "last", "Zone A", "°C", 0), ("ZONE_B", "last", "Zone B", "°C", 0), ("ZONE_C", "last", "Zone C", "°C", 0),
                                     ("ZONE_D", "last", "Zone D", "°C", 0), ("STRESS", "last", "Exit stress", "nm/cm", 0)]),
        trend("lh-stress", f"Residual stress at the lehr exit, last 7 days", [("STRESS", "max", "nm/cm (highest)"), ("STRESS", "mean", "nm/cm")], "nm/cm"),
        trend("lh-zones", "Zone temperatures, last 24 h", [("ZONE_A", "mean", "A"), ("ZONE_B", "mean", "B"), ("ZONE_C", "mean", "C"), ("ZONE_D", "mean", "D")],
              "°C", days=1),
    ]})
    DT = "FG_COLDEND"
    out["coldend"] = (DT, {"title": "Cold end - inspection and cutting", "cards": [
        value("ce-now", "Inspection now (per 10 m²)", [("BUBBLES", "last", "Bubbles", "", 2), ("INCLUSIONS", "last", "Stones", "", 2),
                                                      ("TIN_DEFECTS", "last", "Tin defects", "", 2), ("DISTORTION", "last", "Zebra angle", "°", 0),
                                                      ("CUT_YIELD", "last", "Cutting yield", "%", 1)]),
        trend("ce-def", f"Defects found by inspection, last 7 days",
              [("BUBBLES", "max", "Bubbles"), ("TIN_DEFECTS", "max", "Tin defects"), ("INCLUSIONS", "max", "Stones")], "per 10 m²"),
        trend("ce-run", f"Cold end running, last 7 days (0 = ribbon to cullet)", [("RUNNING", "min", "Running")], "", size="MEDIUMWIDE"),
        trend("ce-thk", f"Measured thickness, last 7 days", [("THICKNESS", "mean", "mm")], "mm", size="MEDIUMWIDE"),
    ]})
    return out


# ── the line drawing with one marker per area ───────────────────────────────────────────────
# (x %, y %) on img/line.jpg (1600x700 drawing): above each unit
SPOTS = [
    ("Furnace", (21.0, 30.0), [("CROWN_TEMP", "last", "Crown °C"), ("GAS_FLOW", "last", "Gas Nm³/h")],
     [("CROWN_TEMP_last", "<", 1575, AMBER), ("CROWN_TEMP_last", ">=", 1575, GREEN)]),
    ("Tin bath", (46.0, 46.0), [("TIN_O2", "last", "Atmosphere O2 ppm")],
     [("TIN_O2_last", ">", 8, RED), ("TIN_O2_last", "<=", 8, GREEN)]),
    ("Annealing lehr", (69.5, 55.0), [("STRESS", "last", "Exit stress nm/cm")],
     [("STRESS_last", ">", 40, AMBER), ("STRESS_last", "<=", 40, GREEN)]),
    ("Cold end", (85.0, 48.0), [("DEFECTS", "last", "Defects /10 m²"), ("YIELD", "last", "Yield %"), ("PACKED_TPD", "last", "Packed t/day")],
     [("YIELD_last", "<", 82, RED), ("YIELD_last", ">=", 82, GREEN)]),
]


def upload(m, type_uuid, path):
    lib = f"/api/v2/core/deviceTypes/{type_uuid}/images"
    have = m.call("GET", lib + "?includeDevices=false", ok_fail=True)
    for im in (have if isinstance(have, list) else []):
        if im.get("fileName") == path.name:
            return str(im.get("id") or im.get("fileName"))
    bnd = "----fgline" + _uuid.uuid4().hex
    body = (f"--{bnd}\r\nContent-Disposition: form-data; name=\"file\"; filename=\"{path.name}\"\r\nContent-Type: image/jpeg\r\n\r\n").encode() \
        + path.read_bytes() + f"\r\n--{bnd}--\r\n".encode()
    h = {k: v for k, v in m.h.items() if k.lower() != "content-type"}
    h["Content-Type"] = f"multipart/form-data; boundary={bnd}"
    req = urllib.request.Request(m.base + lib, data=body, method="POST", headers=h)
    with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=120) as f:
        r = json.loads(f.read() or b"{}")
    r = r[0] if isinstance(r, list) and r else r
    return str(r.get("id") or r.get("fileName") or path.name)


def picture(m, u):
    img = upload(m, u, HERE / "img" / "line.jpg")
    hotspots = [{"locations": [{"x": x, "y": y, "dataFilter": {"deviceid": "L1-LINE"}}], "color": "#0f62fe", "icon": "Location",
                 "content": {"title": title, "attributes": [{"dataSourceId": f"{mt}_{ag}", "label": lb} for mt, ag, lb in cols]},
                 "thresholds": [{"dataSourceId": s, "comparison": c, "value": v, **col} for s, c, v, col in thr]}
                for title, (x, y), cols, thr in SPOTS]
    attrs = {f"{mt}_{ag}": _attr(mt, ag, "FG_LINE") for _, _, cols, _ in SPOTS for mt, ag, _ in cols}
    card = {"id": _id("line-image"), "title": "Float Glass Line 1 - live from SCADA, PLCs and inspection", "size": "LARGEWIDE", "type": "IMAGE",
            "timeRange": "lastHour",
            "content": {"id": img, "alt": "Float Glass Line 1", "hotspots": hotspots, "background": "light", "zoomMax": 4},
            "dataSource": {"range": {"interval": "hour", "count": -1, "type": "rolling"}, "groupBy": ["deviceid"], "attributes": list(attrs.values())}}
    return {"title": "Line 1 - live on the line drawing", "cards": [card]}


def save(m, u, meta, seq):
    path = f"/api/v2/core/deviceTypes/{u}/dashboards"
    have = next((d for d in items(m.call("GET", path)) if d.get("name") == meta["title"]), None)
    body = {"name": meta["title"], "type": "DEVICE_TYPE", "isEnabled": True, "sequenceNumber": seq, "dashboardMetadataJson": meta}
    if have:
        body["dashboardMetaId"] = have["dashboardMetaId"]
        m.call("PUT", f"{path}/{have['dashboardMetaId']}", body)
    else:
        have = m.call("POST", path, body)
    return have.get("dashboardMetaId")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-file", required=True)
    ap.add_argument("--api", required=True)
    ap.add_argument("--out", default="dashboards.json", help="where the dashboard paths are written (one file per cluster)")
    a = ap.parse_args()
    props = dict(l.split("=", 1) for l in open(os.path.expanduser(a.key_file), encoding="utf-8").read().splitlines()
                 if "=" in l and not l.startswith("#"))
    m = Monitor(a.api, props)
    types = {t["name"]: t["uuid"] for t in items(m.call("POST", "/api/v2/core/deviceTypes/search", {"pageSize": 100, "pageNumber": 0}))}
    ids = {"line_pic": ("FG_LINE", save(m, types["FG_LINE"], picture(m, types["FG_LINE"]), 1))}
    for key, (dtype, meta) in dashboards().items():
        ids[key] = (dtype, save(m, types[dtype], meta, 2))
    ui = a.api.rstrip("/").replace(".api.monitor.", ".monitor.")
    for key, (dtype, i) in ids.items():
        print(f"{key}: {ui}/dashboard/{dtype}/dashboards/{i}")
    (HERE / a.out).write_text(json.dumps({k: f"/dashboard/{d}/dashboards/{i}" for k, (d, i) in ids.items()}, indent=1))


if __name__ == "__main__":
    main()
