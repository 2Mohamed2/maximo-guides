"""Esri-compatible routing endpoints for Maximo, backed by OSRM (OpenStreetMap).

Maximo Spatial / Scheduler / Graphical Assignment call three Esri network services.
This service answers them in Esri's JSON shapes, using a self-hosted OSRM router,
so no ArcGIS Online routing licence or credits are needed:

  Map Manager field          Maximo caller                         Endpoint here
  SPATIALROUTE               browser RouteTask (route line on map)  .../NAServer/Route/solve
                             ResourceFinder (live GPS travel time)
  SPATIALDISTANCEMATRIX      SpatialTravelTimeMatrix (<=10 points)  .../NAServer/ODCostMatrix/solveODCostMatrix
  SPATIALJOBMATRIX           SpatialTravelTimeMatrix (>10 points)   .../GPServer/GenerateOriginDestinationCostMatrix/submitJob
                             SpatialTravelTimeMatrixJobHandler      .../jobs/<id>, .../jobs/<id>/results/...
  (token discovery)          getTokenServiceFromEsri                /arcgis/rest/info

Env: OSRM_URL (default http://osrm:5000), PORT (default 8080).
Standard library only.
"""
import json
import math
import os
import threading
import time
import urllib.parse
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

OSRM = os.environ.get("OSRM_URL", "http://osrm:5000").rstrip("/")
PORT = int(os.environ.get("PORT", "8080"))
BASE = "/arcgis/rest/services/World"
JOBS = {}            # jobId -> {"status", "lines", "created"}
JOB_TTL = 3600

# ---------------------------------------------------------------- geometry ---

R = 6378137.0

def to_wgs84(x, y, wkid):
    if wkid in (102100, 102113, 3857, 900913) or abs(x) > 180 or abs(y) > 90:
        lon = math.degrees(x / R)
        lat = math.degrees(2 * math.atan(math.exp(y / R)) - math.pi / 2)
        return lon, lat
    return x, y

def from_wgs84(lon, lat, wkid):
    if wkid in (102100, 102113, 3857, 900913):
        x = R * math.radians(lon)
        y = R * math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
        return x, y
    return lon, lat

def b32(n):
    digits = "0123456789abcdefghijklmnopqrstuv"
    if n == 0:
        return "0"
    s = ""
    while n:
        n, r = divmod(n, 32)
        s = digits[r] + s
    return s

def compress(points, wkid):
    """Esri compressed geometry (the classic '+mult+dx+dy...' form the 3.x JS API decodes)."""
    mult = 1000000 if wkid == 4326 else 10
    out = ["+" + b32(mult)]
    lx = ly = 0
    for x, y in points:
        ix, iy = int(round(x * mult)), int(round(y * mult))
        dx, dy = ix - lx, iy - ly
        lx, ly = ix, iy
        out.append(("+" if dx >= 0 else "-") + b32(abs(dx)))
        out.append(("+" if dy >= 0 else "-") + b32(abs(dy)))
    return "".join(out)

def envelope(points, wkid):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return {"xmin": min(xs), "ymin": min(ys), "xmax": max(xs), "ymax": max(ys), "spatialReference": {"wkid": wkid}}

# ------------------------------------------------------------------ inputs ---

def parse_wkid(v, default=4326):
    if v in (None, ""):
        return default
    if isinstance(v, (int, float)):
        return int(v)
    try:
        j = json.loads(v)
        if isinstance(j, dict):
            return int(j.get("latestWkid") or j.get("wkid") or default)
        return int(j)
    except Exception:
        return default

def parse_points(raw, default_wkid=4326):
    """Esri stops/origins/destinations: features JSON, or 'x,y;x,y'. Returns [(lon, lat, attrs)]."""
    if raw is None:
        return []
    if isinstance(raw, str):
        raw = raw.strip()
        if not raw.startswith("{") and not raw.startswith("["):
            pts = []
            for pair in raw.split(";"):
                if pair.strip():
                    x, y = [float(v) for v in pair.split(",")[:2]]
                    lon, lat = to_wgs84(x, y, default_wkid)
                    pts.append((lon, lat, {}))
            return pts
        raw = json.loads(raw)
    feats = raw.get("features", []) if isinstance(raw, dict) else raw
    top = parse_wkid((raw.get("spatialReference") if isinstance(raw, dict) else None) and json.dumps(raw["spatialReference"]), default_wkid)
    pts = []
    for f in feats:
        g = f.get("geometry", f)
        wk = parse_wkid(g.get("spatialReference") and json.dumps(g["spatialReference"]), top)
        lon, lat = to_wgs84(float(g["x"]), float(g["y"]), wk)
        attrs = dict(f.get("attributes") or {})
        for k in ("pointID", "isPointOnTheFly"):
            if k in f:
                attrs[k] = f[k]
        pts.append((lon, lat, attrs))
    return pts

# -------------------------------------------------------------------- OSRM ---

def osrm(path):
    with urllib.request.urlopen(OSRM + path, timeout=60) as r:
        j = json.loads(r.read().decode())
    if j.get("code") != "Ok":
        raise RuntimeError("OSRM: %s %s" % (j.get("code"), j.get("message", "")))
    return j

def coords(pts):
    return ";".join("%.6f,%.6f" % (p[0], p[1]) for p in pts)

def table(origins, dests):
    """Minutes and km for every origin x destination, origin-major."""
    pts = origins + dests
    src = ";".join(str(i) for i in range(len(origins)))
    dst = ";".join(str(len(origins) + i) for i in range(len(dests)))
    j = osrm("/table/v1/driving/%s?sources=%s&destinations=%s&annotations=duration,distance" % (coords(pts), src, dst))
    out = []
    for i in range(len(origins)):
        row = []
        for k in range(len(dests)):
            d = j["durations"][i][k]
            m = j["distances"][i][k]
            row.append((None if d is None else d / 60.0, None if m is None else m / 1000.0))
        out.append(row)
    return out

# ---------------------------------------------------------------- services ---

def maneuver_text(step, i_leg):
    m = step["maneuver"]
    kind, mod = m.get("type", ""), m.get("modifier", "")
    road = step.get("name") or step.get("ref") or "the road"
    if kind == "roundabout" or kind == "rotary":
        return "At the roundabout take exit %s onto %s" % (m.get("exit", ""), road)
    if kind in ("turn", "end of road", "fork", "on ramp", "off ramp", "merge"):
        return "%s %s onto %s" % ("Turn" if kind == "turn" else kind.capitalize(), mod, road)
    if kind == "new name" or kind == "continue":
        return "Continue onto %s" % road
    return "Go %s on %s" % (mod or "straight", road)

def solve_route(params):
    out_wkid = parse_wkid(params.get("outSR"), 4326)
    stops = parse_points(params.get("stops"))
    if len(stops) < 2:
        return {"error": {"code": 400, "message": "At least two stops are required.", "details": []}}
    j = osrm("/route/v1/driving/%s?overview=full&geometries=geojson&steps=true" % coords(stops))
    route = j["routes"][0]
    path = [from_wgs84(lon, lat, out_wkid) for lon, lat in route["geometry"]["coordinates"]]
    total_min = route["duration"] / 60.0
    total_km = route["distance"] / 1000.0

    feats = []
    for li, leg in enumerate(route["legs"]):
        a = from_wgs84(stops[li][0], stops[li][1], out_wkid)
        b = from_wgs84(stops[li + 1][0], stops[li + 1][1], out_wkid)
        feats.append({"attributes": {"length": 0, "time": 0, "text": "Start at Location %d" % (li + 1),
                                     "ETA": 0, "maneuverType": "esriDMTDepart"},
                      "compressedGeometry": compress([a], out_wkid)})
        for st in leg["steps"]:
            if st["maneuver"]["type"] in ("depart", "arrive"):
                continue
            geom = [from_wgs84(lon, lat, out_wkid) for lon, lat in st["geometry"]["coordinates"]] or [a]
            feats.append({"attributes": {"length": max(st["distance"] / 1000.0, 0.001), "time": st["duration"] / 60.0,
                                         "text": maneuver_text(st, li), "ETA": 0, "maneuverType": "esriDMTStraight"},
                          "compressedGeometry": compress(geom, out_wkid)})
        feats.append({"attributes": {"length": 0, "time": 0, "text": "Arrive at Location %d" % (li + 2),
                                     "ETA": 0, "maneuverType": "esriDMTStop"},
                      "compressedGeometry": compress([b], out_wkid)})

    name = "Location 1 - Location %d" % len(stops)
    stop_feats = []
    for i, (lon, lat, attrs) in enumerate(stops):
        x, y = from_wgs84(lon, lat, out_wkid)
        a = {"ObjectID": i + 1, "Name": attrs.get("Name", "Location %d" % (i + 1)), "RouteName": name, "Sequence": i + 1,
             "Status": 0, "Cumul_TravelTime": 0, "Cumul_Kilometers": 0}
        stop_feats.append({"attributes": a, "geometry": {"x": x, "y": y}})
    return {
        "messages": [],
        "checksum": uuid.uuid4().hex,
        "routes": {"fieldAliases": {}, "geometryType": "esriGeometryPolyline", "spatialReference": {"wkid": out_wkid},
                   "features": [{"attributes": {"ObjectID": 1, "Name": name, "Total_TravelTime": total_min,
                                                "Total_Minutes": total_min, "Total_Kilometers": total_km,
                                                "Total_Miles": total_km / 1.609344, "Shape_Length": total_km * 1000},
                                 "geometry": {"paths": [[list(p) for p in path]]}}]},
        "directions": [{"routeId": 1, "routeName": name,
                        "summary": {"totalLength": total_km, "totalTime": total_min, "totalDriveTime": total_min,
                                    "envelope": envelope(path, out_wkid)},
                        "features": feats}],
        "stops": {"fieldAliases": {}, "geometryType": "esriGeometryPoint", "spatialReference": {"wkid": out_wkid},
                  "features": stop_feats},
    }

def solve_od(params):
    origins = parse_points(params.get("origins"))
    dests = parse_points(params.get("destinations"))
    m = table(origins, dests)
    od = {"costAttributeNames": ["TravelTime", "Kilometers"]}
    for i, row in enumerate(m):
        od[str(i + 1)] = {str(k + 1): [c[0], c[1]] for k, c in enumerate(row) if c[0] is not None}
    return {"odCostMatrix": od, "messages": []}

def submit_job(params):
    job = uuid.uuid4().hex
    JOBS[job] = {"status": "esriJobExecuting", "created": time.time(), "lines": None}

    def run():
        try:
            origins = parse_points(params.get("origins"))
            dests = parse_points(params.get("destinations"))
            m = table(origins, dests)
            lines, oid = [], 1
            for i, row in enumerate(m):
                for k, (mins, km) in enumerate(row):
                    # Maximo's job handler reads Total_Distance and treats it as minutes.
                    lines.append({"attributes": {"ObjectID": oid, "OriginOID": i + 1, "DestinationOID": k + 1,
                                                 "Total_Time": mins, "Total_Distance": mins if mins is not None else 99999,
                                                 "Total_Kilometers": km}})
                    oid += 1
            JOBS[job].update(status="esriJobSucceeded", lines=lines)
        except Exception as e:  # noqa
            JOBS[job].update(status="esriJobFailed", error=str(e))
    threading.Thread(target=run, daemon=True).start()
    return {"jobId": job, "jobStatus": "esriJobSubmitted"}

def job_status(job):
    j = JOBS.get(job)
    if not j:
        return {"error": {"code": 400, "message": "Invalid or missing input parameters.", "details": ["unknown job"]}}
    res = {"jobId": job, "jobStatus": j["status"], "messages": []}
    if j["status"] == "esriJobSucceeded":
        res["results"] = {"Output_Origin_Destination_Lines": {"paramUrl": "results/Output_Origin_Destination_Lines"}}
    if j["status"] == "esriJobFailed":
        res["messages"] = [{"type": "esriJobMessageTypeError", "description": j.get("error", "failed")}]
    return res

def job_result(job):
    j = JOBS.get(job) or {}
    return {"paramName": "Output_Origin_Destination_Lines", "dataType": "GPFeatureRecordSetLayer",
            "value": {"geometryType": "esriGeometryPolyline", "features": j.get("lines") or [], "messages": []}}

ROUTE_INFO = {"currentVersion": 11.1, "layerName": "Route", "layerType": "esriNAServerRouteLayer",
              "impedance": "TravelTime", "directionsLengthUnits": "esriNAUKilometers",
              "networkDataset": {"name": "OpenStreetMap (OSRM)"}, "supportedTravelModes": [
                  {"name": "Driving Time", "id": "FEgifRtFndKNcJMJ", "type": "AUTOMOBILE", "impedanceAttributeName": "TravelTime"}]}

# ------------------------------------------------------------------- HTTP ---

class H(BaseHTTPRequestHandler):
    server_version = "EsriOSRMAdapter/1.0"

    def log_message(self, fmt, *args):
        print("%s %s" % (self.address_string(), fmt % args), flush=True)

    def _params(self):
        u = urllib.parse.urlparse(self.path)
        p = {k: v[-1] for k, v in urllib.parse.parse_qs(u.query, keep_blank_values=True).items()}
        if self.command == "POST":
            n = int(self.headers.get("Content-Length") or 0)
            body = self.rfile.read(n).decode("utf-8", "replace") if n else ""
            ctype = self.headers.get("Content-Type", "")
            if "json" in ctype and body.strip().startswith("{"):
                p.update(json.loads(body))
            else:
                p.update({k: v[-1] for k, v in urllib.parse.parse_qs(body, keep_blank_values=True).items()})
        return u.path.rstrip("/"), p

    def _send(self, obj, p, code=200):
        body = json.dumps(obj, indent=2 if p.get("f") == "pjson" else None)
        cb = p.get("callback")
        if cb:
            body, ctype = "%s(%s);" % (cb, body), "application/javascript"
        else:
            ctype = "application/json; charset=utf-8"
        data = body.encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin") or "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", self.headers.get("Origin") or "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Credentials", "true")
        self.end_headers()

    def do_GET(self):
        self._route()

    def do_POST(self):
        self._route()

    def _route(self):
        path, p = self._params()
        try:
            if path in ("", "/healthz"):
                return self._send({"ok": True, "osrm": OSRM}, p)
            if path == "/arcgis/rest/info":
                return self._send({"currentVersion": 11.1, "fullVersion": "11.1.0", "owningSystemUrl": "",
                                   "authInfo": {"isTokenBasedSecurity": False}}, p)
            if path.endswith("/NAServer/Route/solve"):
                return self._send(solve_route(p), p)
            if path.endswith("/NAServer/Route"):
                return self._send(ROUTE_INFO, p)
            if path.endswith("/solveODCostMatrix"):
                res = solve_od(p)
                if os.environ.get("DEBUG"):
                    print("OD REQ", json.dumps(p)[:1500], flush=True)
                    print("OD RES", json.dumps(res)[:1500], flush=True)
                return self._send(res, p)
            if path.endswith("/submitJob"):
                return self._send(submit_job(p), p)
            if "/jobs/" in path:
                tail = path.split("/jobs/", 1)[1].split("/")
                if len(tail) == 1:
                    return self._send(job_status(tail[0]), p)
                return self._send(job_result(tail[0]), p)
            if path.endswith("/NAServer/ODCostMatrix") or path.endswith("/GenerateOriginDestinationCostMatrix"):
                return self._send({"currentVersion": 11.1, "name": path.rsplit("/", 1)[1]}, p)
            return self._send({"error": {"code": 404, "message": "Not found: " + path, "details": []}}, p, 404)
        except Exception as e:  # Esri clients expect a 200 with an error body
            return self._send({"error": {"code": 500, "message": str(e), "details": []}}, p)

def reaper():
    while True:
        time.sleep(300)
        now = time.time()
        for k in [k for k, v in JOBS.items() if now - v["created"] > JOB_TTL]:
            JOBS.pop(k, None)

if __name__ == "__main__":
    threading.Thread(target=reaper, daemon=True).start()
    print("Esri-OSRM adapter on :%d -> %s" % (PORT, OSRM), flush=True)
    ThreadingHTTPServer(("0.0.0.0", PORT), H).serve_forever()
