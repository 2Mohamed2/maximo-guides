"""Float Glass Line 1 simulator: SCADA / PLC / inspection readings for every Monitor device in line.json, as a
function of time, so the history in the data lake and the live feed tell the same story.

    python sim.py live [--every 10] [--tin-every 1] [--http 8080]   publish over MQTT as each device (device tokens)
    python sim.py sql --days 14 --step 300 --out backfill            Db2 INSERT files for the Monitor data lake
    python sim.py print                                              one reading of every device, no publish

A 600 t/day float line making clear glass, mostly 4 mm. What drives the variation in pack-to-melt yield over the
14 days before ANCHOR (all demo data, invented):
  - job changes (thickness 4 -> 6 -> 4 -> 8 -> 4 mm): about 4.5 hours of low yield each
  - three dips of the gas supply pressure: the burners lose about 8 % of gas, the crown cools 15-20 °C and,
    a few hours later, inspection counts several times more bubbles (refining is short of heat)
  - five cold-end stops (cutting bridge, stacker): the ribbon goes to cullet, yield 0, the furnace keeps melting
  - a tin bath side-seal leak: bath pressure falls, O2 in the bath atmosphere rises, tin defects follow
  - night shift a little lower
Live (after ANCHOR) the line runs 4 mm; scenarios switched on the control page (POST /api/scenario with the demo
key) replay two of the stories: "tin_o2" (side-seal leak) and "gas_dip" (gas supply pressure), plus
"weigher_drift" (batch weigher reads 1.5 % high), found by the ribbon mass-balance twin.
"""
import argparse
import hashlib
import json
import math
import os
import ssl
import threading
import time
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

HERE = Path(__file__).parent
DEV_FILE = Path(os.environ.get("DEV_FILE") or os.path.expanduser("~/.mas-control-room/floatglass-devices.json"))
# history ends here, live starts; FG_ANCHOR (UTC yyyy-mm-ddThh:mm) moves it for another cluster
ANCHOR = (datetime.strptime(os.environ["FG_ANCHOR"], "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).timestamp()
          if os.environ.get("FG_ANCHOR") else datetime(2026, 11, 10, 7, 0, tzinfo=timezone.utc).timestamp())
DAY = 86400.0
PULL = 600.0                                         # t/day
WIDTH = 3.8                                          # gross ribbon width, m
JOBS = [(-14.0, 4.0), (-12.6, 6.0), (-9.2, 4.0), (-5.4, 8.0), (-3.1, 4.0)]      # (day, thickness mm) from ANCHOR
JOB_H = 4.5                                          # hours of transition after a job change
GAS_DIPS = [(-11.3, 5.0), (-6.6, 4.0), (-1.8, 3.0)]   # (day, hours)
STOPS = [(-12.2, 70), (-8.45, 45), (-4.1, 110), (-1.35, 35), (-0.6, 25)]        # (day, minutes)
SEAL = [(-2.6, 6.0)]                                 # tin bath side-seal leak (day, hours)
SCEN_NAMES = ("tin_o2", "gas_dip", "weigher_drift")


def rnd(*k):
    return int(hashlib.md5("|".join(map(str, k)).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def noise(key, t, amp, period=300):
    """Smooth noise in -amp..amp: stable random points every `period` seconds, interpolated."""
    i, f = divmod(t / period, 1)
    a, b = rnd(key, int(i)) - .5, rnd(key, int(i) + 1) - .5
    return 2 * amp * (a + (b - a) * (3 * f * f - 2 * f * f * f))


def hour(t):                                          # plant local time (UTC+4)
    d = datetime.fromtimestamp(t, timezone.utc)
    return (d.hour + 4) % 24 + d.minute / 60


def window(t, start_s, dur_s, rise_s=1800.0, fall_s=3600.0):
    """0 outside, 1 inside, smooth edges: an event from start_s lasting dur_s."""
    if t < start_s - 1 or t > start_s + dur_s + fall_s:
        return 0.0
    up = min(1.0, max(0.0, (t - start_s) / rise_s))
    down = min(1.0, max(0.0, 1 - (t - start_s - dur_s) / fall_s))
    x = min(up, down)
    return x * x * (3 - 2 * x)


def scen(sc, name, t):
    """How far a live scenario has pushed its story: 0 when off, rising to 1 over its ramp."""
    s = (sc or {}).get(name) or {}
    if not s.get("active") or not s.get("since"):
        return 0.0
    return max(0.0, min(1.0, (t - s["since"]) / 60 / max(1, s.get("ramp_min", 10))))


def thickness(t):
    """(thickness mm, previous thickness, hours since the last job change or None)."""
    d = (t - ANCHOR) / DAY
    cur, prev, since = JOBS[0][1], JOBS[0][1], None
    for i, (day, th) in enumerate(JOBS):
        if d >= day:
            cur, prev = th, (JOBS[i - 1][1] if i else th)
            since = (d - day) * 24 if i else None
    return cur, prev, since


def readings(t, sc=None):
    """{device: {metric lower: value}} for every device at time t."""
    th, prev, since = thickness(t)
    jc = since is not None and since < JOB_H               # in a job change
    jc_p = 1 - since / JOB_H if jc else 0.0                # 1 at the change, 0 when done
    th_now = prev + (th - prev) * (1 - jc_p ** 2) if jc else th
    # gas supply dips (history + live scenario)
    gd = max([window(t, ANCHOR + d * DAY, h * 3600, 900, 2400) for d, h in GAS_DIPS] + [scen(sc, "gas_dip", t)])
    # the crown follows the gas with a lag; bubbles follow the crown a few hours later (refining)
    crown_drop = max([window(t, ANCHOR + d * DAY + 2400, h * 3600, 3600, 5400) for d, h in GAS_DIPS]
                     + [scen(sc, "gas_dip", t - 300)])
    bub = max([window(t, ANCHOR + d * DAY + 3 * 3600, h * 3600 + 3 * 3600, 3600, 4 * 3600) for d, h in GAS_DIPS]
              + [scen(sc, "gas_dip", t - 900)])
    seal = max([window(t, ANCHOR + d * DAY, h * 3600, 1200, 2400) for d, h in SEAL] + [scen(sc, "tin_o2", t)])
    tin = max([window(t, ANCHOR + d * DAY + 1800, h * 3600, 1800, 3600) for d, h in SEAL] + [scen(sc, "tin_o2", t - 240)])
    stop = any(ANCHOR + d * DAY <= t < ANCHOR + d * DAY + m * 60 for d, m in STOPS)
    h = hour(t)
    night = 1.0 if (h >= 22 or h < 6) else 0.0

    pull = PULL + noise("pull", t, 6, 3600) + (15 if th >= 8 else 0)
    gas = pull * 6.25 / 24 / 0.036 * (1 + noise("gasf", t, .012, 900)) * (1 - 0.08 * gd)
    crown = 1586 + noise("crown", t, 2.5, 600) - 18 * crown_drop
    reversal = (t // 1200) % 2                             # firing side changes every 20 minutes
    ph = (t % 1200) / 1200
    regen_hot, regen_cold = 1335 + 25 * ph, 1290 - 35 * ph
    furnace = {"crown_temp": crown, "bottom_temp": 1352 + noise("bot", t, 2, 1800) - 6 * crown_drop,
               "regen_left": regen_hot if reversal else regen_cold, "regen_right": regen_cold if reversal else regen_hot,
               "gas_flow": gas, "gas_pressure": 300 + noise("gp", t, 4, 300) - 72 * gd,
               "comb_air": gas * 10.15 * (1 + noise("air", t, .01, 600)), "flue_o2": 2.2 + noise("o2f", t, .25, 600) + 0.6 * gd,
               "glass_level": noise("lvl", t, .25, 240), "furnace_pressure": 3 + noise("fp", t, 1.0, 120),
               "pull_rate": pull, "cullet_pct": 22 + noise("cul", t, 1.5, 7200)}

    o2 = 1.8 + noise("o2", t, .35, 120) + 16.5 * seal + (1.2 if jc else 0)
    h2_flow = 130 + noise("h2f", t, 3, 600) + 42 * seal
    speed = pull * 1000 / 1440 / 2500 / (th_now / 1000) / WIDTH
    tinbath = {"lip_temp": 1100 + noise("lip", t, 2, 600) - 4 * crown_drop, "entry_temp": 1042 + noise("ent", t, 3, 600),
               "mid_temp": 905 + noise("mid", t, 3, 600) + (8 if th >= 8 else 0), "exit_temp": 612 + noise("ext", t, 2.5, 600),
               "atm_o2": max(0.4, o2), "atm_h2": 7.0 + noise("h2", t, .15, 900) - 0.8 * seal, "n2_flow": 1720 + noise("n2", t, 20, 900),
               "h2_flow": h2_flow, "bath_pressure": 25 + noise("bp", t, 1.2, 180) - 10 * seal,
               "ribbon_speed": speed, "ribbon_width": WIDTH + noise("rw", t, .006, 300), "thickness_sp": th}

    stress = {4.0: 22, 6.0: 28, 8.0: 35}.get(th, 24) + noise("str", t, 2.5, 900) + 24 * jc_p
    lehr = {"zone_a": 560 + noise("za", t, 3, 600), "zone_b": 518 + noise("zb", t, 3, 600), "zone_c": 452 + noise("zc", t, 3, 600),
            "zone_d": 298 + noise("zd", t, 4, 600), "exit_temp": 66 + noise("lx", t, 3, 900), "stress": stress,
            "roller_speed": speed * 1.008, "drive_current": 84 + noise("dc", t, 2, 300) + 4 * (th >= 8)}

    bubbles = max(0.02, 0.12 + noise("bub", t, .04, 900) + 0.85 * bub + 0.25 * jc_p)
    incl = max(0.0, 0.07 + noise("inc", t, .03, 1800) + (0.22 if rnd("incl", int(t // 7200)) > 0.97 else 0))
    tind = max(0.0, 0.05 + noise("tin", t, .02, 900) + 0.62 * tin)
    distortion = 60 - 2.5 * (th < 5) * 0 + noise("dist", t, 1.2, 900) - 9 * jc_p - (2 if th >= 8 else 0)
    yld = (88.6 + noise("yld", t, .6, 1800) - 9.5 * (bubbles - 0.12) - 14 * (tind - 0.05) - 6 * max(0, incl - 0.07)
           - 0.9 * max(0, stress - 38) - 1.2 * night - 52 * jc_p)
    yld = 0.0 if stop else max(20.0, min(91.0, yld))
    state = 0 if stop else 1 if jc else 2
    coldend = {"thickness": th_now + noise("thk", t, .015, 120), "bubbles": bubbles, "inclusions": incl, "tin_defects": tind,
               "distortion": distortion, "cut_speed": 0.0 if stop else speed * 1.01, "cut_yield": yld, "running": 0 if stop else 1}
    line = {"pull_rate": pull, "packed_tpd": pull * yld / 100, "yield": yld, "state": state, "thickness": th,
            "crown_temp": crown, "tin_o2": tinbath["atm_o2"], "stress": stress, "defects": bubbles + incl + tind, "gas_flow": gas}
    # the batch weigher reads high when its calibration drifts (live scenario "weigher_drift", +1.5 %)
    ribbon = {"weigher_tpd": pull * (1 + 0.015 * scen(sc, "weigher_drift", t)) + noise("wg", t, 1.5, 300),
              "ribbon_speed": speed, "ribbon_width": tinbath["ribbon_width"], "thickness": coldend["thickness"]}
    r = {"L1-FURNACE": furnace, "L1-TINBATH": tinbath, "L1-LEHR": lehr, "L1-COLDEND": coldend, "L1-LINE": line, "L1-RIBBON": ribbon}
    return {d: {k: round(v, DEC.get(k, 1)) if isinstance(v, float) else v for k, v in x.items()} for d, x in r.items()}


# decimals per tag (as a SCADA historian would store them)
DEC = {"glass_level": 2, "flue_o2": 2, "ribbon_speed": 2, "ribbon_width": 3, "thickness": 3, "thickness_sp": 1, "roller_speed": 2,
       "cut_speed": 2, "weigher_tpd": 1, "bubbles": 3, "inclusions": 3, "tin_defects": 3, "defects": 3, "atm_h2": 2, "atm_o2": 2, "tin_o2": 2,
       "gas_flow": 0, "comb_air": 0, "n2_flow": 0}


# ── live: MQTT + control page ───────────────────────────────────────────────────────────────
class State:
    lock = threading.Lock()
    scenarios, latest, published, path = {}, {}, 0, None

    @classmethod
    def set(cls, name, active, ramp_min=None):
        with cls.lock:
            s = cls.scenarios.setdefault(name, {})
            s["active"] = bool(active)
            if ramp_min:
                s["ramp_min"] = max(1, min(120, int(ramp_min)))
            s["since"] = time.time() if active else None
            if cls.path:
                Path(cls.path).write_text(json.dumps(cls.scenarios), encoding="utf-8")
            return dict(cls.scenarios)


class Http(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            return self.send(200, (HERE / "page.html").read_bytes(), "text/html; charset=utf-8")
        if self.path == "/api/latest":
            with State.lock:
                return self.send(200, {"ts": time.time(), "published": State.published, "scenarios": State.scenarios,
                                       "devices": State.latest})
        if self.path == "/healthz":
            return self.send(200, {"ok": True})
        self.send(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/api/scenario":
            return self.send(404, {"error": "not found"})
        key = os.environ.get("DEMO_KEY", "")
        if not key or self.headers.get("X-Demo-Key") != key:
            return self.send(403, {"error": "demo key required"})
        b = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0)) or 0) or b"{}")
        if b.get("name") not in SCEN_NAMES:
            return self.send(400, {"error": "unknown scenario"})
        self.send(200, State.set(b["name"], b.get("active"), b.get("ramp_min")))


def live(a):
    import paho.mqtt.client as mqtt
    devs = json.load(open(DEV_FILE, encoding="utf-8"))
    spec = json.load(open(HERE / "line.json", encoding="utf-8"))
    event = {n: s["event"] for s in spec["device_types"].values() for n in s["devices"]}
    State.path = os.environ.get("SCENARIO_STATE")
    if State.path and Path(State.path).is_file():
        State.scenarios = json.loads(Path(State.path).read_text(encoding="utf-8"))
    if a.http:
        threading.Thread(target=ThreadingHTTPServer(("0.0.0.0", a.http), Http).serve_forever, daemon=True).start()
        print(f"control page on :{a.http}", flush=True)
    clients = {}
    for name, x in devs["devices"].items():
        kw = dict(client_id=f"d:{devs['tenant']}:{x['type']}:{name}")
        c = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, **kw) if hasattr(mqtt, "CallbackAPIVersion") else mqtt.Client(**kw)
        c.username_pw_set("use-token-auth", x["token"])
        c.tls_set_context(ssl._create_unverified_context())      # the cluster's router certificate; demo only
        c.reconnect_delay_set(5, 60)
        c.connect(devs["host"], 443, keepalive=60)
        c.loop_start()
        clients[name] = c
    print(f"connected {len(clients)} devices to {devs['host']}", flush=True)
    last, n = {}, 0
    while True:
        t = time.time()
        with State.lock:
            sc = json.loads(json.dumps(State.scenarios))
        r = readings(t, sc)
        for name, c in clients.items():
            every = a.tin_every if name == "L1-TINBATH" else a.every
            if t - last.get(name, 0) >= every:
                c.publish(f"iot-2/evt/{event[name]}/fmt/json", json.dumps({"d": r[name]}), qos=0)
                last[name] = t
                n += 1
        with State.lock:
            State.latest, State.published = r, n
        if n % 600 < len(clients):
            on = [k for k, s in sc.items() if s.get("active")]
            print(datetime.now(timezone.utc).strftime("%H:%M:%S"), "published", n, "scenarios on:", ", ".join(on) or "none", flush=True)
        time.sleep(max(0.05, 1 - (time.time() - t)))


def sql(a):
    spec = json.load(open(HERE / "line.json", encoding="utf-8"))
    tables = json.load(open(a.tables, encoding="utf-8"))          # {devtype: {schema, table, uids: {dev: uid}, cols: {metric: column}}}
    out = Path(a.out)
    out.mkdir(exist_ok=True)
    end = min(time.time() - 120, datetime.strptime(a.until, "%Y-%m-%dT%H:%M").replace(tzinfo=timezone.utc).timestamp()
              if a.until else ANCHOR)
    start = ANCHOR - a.days * DAY
    for dt, s in spec["device_types"].items():
        tb = tables[dt]
        metrics = list(s["metrics"])
        cols = ", ".join(tb["cols"][m] for m in metrics)
        rows, t = [], start - start % a.step
        while t < end:
            r = readings(t)
            ts = datetime.fromtimestamp(t, timezone.utc).strftime("%Y-%m-%d-%H.%M.%S.000000")
            for dev in s["devices"]:
                vals = ", ".join(str(r[dev][m.lower()]) for m in metrics)
                rows.append(f"({tb['uids'][dev]}, '{dev}', '{ts}', '{ts}', {vals})")
            t += a.step
        with open(out / f"{dt}.sql", "w", encoding="utf-8") as fh:
            day = datetime.fromtimestamp(start, timezone.utc).date()
            while a.partitions and day.isoformat() < a.partitions_from:     # tables are partitioned from creation day - 7
                fh.write(f"ALTER TABLE {tb['schema']}.{tb['table']} ADD PARTITION \"{day:%Y%m%d}\" STARTING FROM "
                         f"'{day}-00.00.00.000000' INCLUSIVE ENDING AT '{day}-23.59.59.999999' INCLUSIVE;\n")
                day = day.fromordinal(day.toordinal() + 1)
            for i in range(0, len(rows), 60):
                fh.write(f"INSERT INTO {tb['schema']}.{tb['table']} (DEVICE_UID, DEVICEID, RCV_TIMESTAMP_UTC, DEFAULT_TIMESTAMP_UTC, {cols}) VALUES\n"
                         + ",\n".join(rows[i:i + 60]) + ";\n")
        print(dt, len(rows), "rows")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    lv = sub.add_parser("live")
    lv.add_argument("--every", type=float, default=10)
    lv.add_argument("--tin-every", type=float, default=1)
    lv.add_argument("--http", type=int)
    sq = sub.add_parser("sql")
    sq.add_argument("--days", type=float, default=14)
    sq.add_argument("--step", type=int, default=300)
    sq.add_argument("--until", help="UTC yyyy-mm-ddThh:mm: write up to here (the start of `live`), default ANCHOR")
    sq.add_argument("--partitions", action="store_true", help="first add the missing daily partitions")
    sq.add_argument("--partitions-from", default="2026-11-03",
                    help="first day the table already has a partition for (its creation day - 7), yyyy-mm-dd")
    sq.add_argument("--tables", default=str(HERE / "lake_tables.json"))
    sq.add_argument("--out", default=str(HERE / "backfill"))
    sub.add_parser("print")
    a = ap.parse_args()
    if a.cmd == "live":
        live(a)
    elif a.cmd == "sql":
        sql(a)
    else:
        print(json.dumps(readings(time.time()), indent=1))
