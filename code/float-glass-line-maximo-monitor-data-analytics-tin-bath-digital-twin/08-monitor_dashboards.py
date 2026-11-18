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
