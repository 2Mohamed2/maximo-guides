"""Float Glass Line 1: Maximo Monitor configuration from line.json. Monitor only: no Manage assets, no meters.

    python monitor_setup.py --key-file ~/.mas-control-room/monitor-api.properties \
        --api https://wsp.api.monitor.<mas-domain> [--step types|functions|all]

  types     device types FG_FURNACE, FG_TINBATH, FG_LEHR, FG_COLDEND, FG_LINE: one metric per SCADA / PLC /
            inspection tag (jsonPath d.<tag lower case>), dimensions LINE / AREA / SOURCE, one device per area;
            FG_RIBBON: inputs of the ribbon mass-balance twin
  functions SPEC_ENERGY (GJ per tonne melted) and LOSS_TPD (tonnes per day not packed), PythonExpression;
            O2_ANOMALY (KMeansAnomalyScore on the tin bath O2); the twins (tin bath atmosphere: O2_EXPECTED,
            AIR_INGRESS L/min, P_EXPECTED, P_DEFICIT; ribbon: RIBBON_TPD, MASS_GAP %); alert rules (AlertExpression)
Re-runnable. Device tokens (issued once) go to ~/.mas-control-room/floatglass-devices.json, outside git.
"""
import argparse
import json
import os
import ssl
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "tic40-demo"))
from monitor_setup import Monitor, items  # noqa: E402

HERE = Path(__file__).parent
DEV_FILE = Path(os.path.expanduser(os.environ.get("FG_DEV_FILE") or "~/.mas-control-room/floatglass-devices.json"))
SCHEDULE = {"starting_at": "00:00:00", "every": "5T"}

TIN_FLOW = "df['N2_FLOW'] + df['H2_FLOW']"
TIN_O2_EXP = "2.0 * df['N2_FLOW'] / (df['N2_FLOW'] + df['H2_FLOW'])"
TIN_O2_GAP = f"df['ATM_O2'] - {TIN_O2_EXP}"
RIBBON_TPD = "df['RIBBON_SPEED'] * df['RIBBON_WIDTH'] * df['THICKNESS'] * 2.5 * 1.44"     # m/min x m x mm x t/m3 -> t/day
CALCS = [  # device type, output metric, expression
    ("FG_FURNACE", "SPEC_ENERGY", "(df['GAS_FLOW'] * 24 * 0.036 / df['PULL_RATE']).round(2)"),
    ("FG_LINE", "LOSS_TPD", "(df['PULL_RATE'] * (100 - df['YIELD']) / 100).round(1)"),
    # tin bath atmosphere twin: a sealed bath holds the O2 of its N2 supply (about 2 ppm), diluted by the H2;
    # anything above that is air getting in. Bath pressure follows the protective gas flow; a leak lets it fall.
    ("FG_TINBATH", "O2_EXPECTED", f"({TIN_O2_EXP}).round(2)"),
    ("FG_TINBATH", "AIR_INGRESS", f"(({TIN_O2_GAP}) * ({TIN_FLOW}) / 209000 * 1000 / 60).clip(lower=0).round(2)"),
    ("FG_TINBATH", "P_EXPECTED", f"(25 * ({TIN_FLOW}) / 1850).round(1)"),
    ("FG_TINBATH", "P_DEFICIT", f"(25 * ({TIN_FLOW}) / 1850 - df['BATH_PRESSURE']).round(1)"),
    # ribbon mass balance twin: glass carried by the ribbon (speed x width x thickness x density) against the weigher
    ("FG_RIBBON", "RIBBON_TPD", f"({RIBBON_TPD}).round(1)"),
    ("FG_RIBBON", "MASS_GAP", f"(100 * (df['WEIGHER_TPD'] / ({RIBBON_TPD}) - 1)).round(2)"),
]
ANOMALY = [("FG_TINBATH", "ATM_O2", "O2_ANOMALY", 12)]
ALERTS = [  # device type, alert name, expression, severity
    ("FG_TINBATH", "TIN_O2_HIGH", "df['ATM_O2'] > 8", "High"),
    ("FG_TINBATH", "TIN_O2_ANOMALY", "df['O2_ANOMALY'] > 3", "Medium"),
    ("FG_FURNACE", "CROWN_TEMP_LOW", "df['CROWN_TEMP'] < 1575", "Medium"),
    ("FG_FURNACE", "GAS_PRESSURE_LOW", "df['GAS_PRESSURE'] < 260", "High"),
    ("FG_COLDEND", "TIN_DEFECTS_HIGH", "df['TIN_DEFECTS'] > 0.3", "Medium"),
    ("FG_COLDEND", "BUBBLES_HIGH", "df['BUBBLES'] > 0.5", "Medium"),
    ("FG_TINBATH", "TIN_AIR_INGRESS", f"({TIN_O2_GAP}) * ({TIN_FLOW}) / 209000 * 1000 / 60 > 1", "High"),
    ("FG_RIBBON", "MASS_BALANCE_GAP", f"(100 * (df['WEIGHER_TPD'] / ({RIBBON_TPD}) - 1)).abs() > 1", "Medium"),
    ("FG_LINE", "YIELD_LOW", "(df['YIELD'] < 82) & (df['STATE'] == 2)", "High"),
]


def types(m):
    return {t["name"]: t["uuid"] for t in items(m.call("POST", "/api/v2/core/deviceTypes/search", {"pageSize": 100, "pageNumber": 0}))}


def step_types(m, d):
    found = types(m)
    devs = json.load(open(DEV_FILE, encoding="utf-8")) if DEV_FILE.is_file() else {"devices": {}}
    for name, t in d["device_types"].items():
        if name not in found:
            r = m.call("POST", "/api/v2/core/deviceTypes", {
                "name": name, "description": t["desc"],
                "dataItemDto": [{"name": x, "type": "METRIC", "columnType": "NUMBER", "eventName": t["event"],
                                 "jsonPath": f"d.{x.lower()}", "description": desc} for x, desc in t["metrics"].items()]})
            found[name] = r["uuid"]
            m.call("POST", f"/api/v2/core/deviceTypes/{r['uuid']}/dimensions",
                   [{"name": k, "columnType": "LITERAL"} for k in ("LINE", "AREA", "SOURCE")])
            print(f"device type {name}: created ({len(t['metrics'])} metrics)")
        u = found[name]
        have = {x.get("deviceId") or x.get("name") for x in items(m.call("GET", f"/api/v2/core/deviceTypes/{u}/devices"))}
        new = [x for x in t["devices"] if x not in have]
        if new:
            for x in items(m.call("POST", f"/api/v2/deviceTypes/{u}/devices", [{"name": n, "alias": n} for n in new])):
                if x.get("authToken"):
                    devs["devices"][x["name"]] = {"type": name, "token": x["authToken"]}
        dims = [{"id": n, "name": k, "type": "LITERAL", "value": v} for n in t["devices"]
                for k, v in (("LINE", d["dims"]["LINE"]), ("AREA", d["area"][n]), ("SOURCE", d["dims"]["SOURCE"][n]))]
        m.call("POST", f"/api/v2/core/deviceTypes/{u}/devices/dimensions", dims)
        print(f"  {name}: {len(t['devices'])} devices ({len(new)} new), dimensions set")
    devs.update({"tenant": m.h["tenantId"], "types": {k: found[k] for k in d["device_types"]},
                 "host": m.base.replace("https://", "").replace(".api.monitor.", ".messaging.iot.")})
    DEV_FILE.write_text(json.dumps(devs, indent=1), encoding="utf-8")
    print(f"tokens in {DEV_FILE}")


def ensure_fn(m, uuid, out, body):
    have = items(m.call("GET", f"/api/v2/core/deviceTypes/{uuid}/kpiFunctions"))
    k = next((k for k in have if out in (k.get("output") or {}).values()), None)
    if k and k.get("input") == body["input"]:
        return "exists"
    if k:                     # expression changed: update in place (path takes the function's uuid "name"; reply is plain text)
        upd = {**k, "input": body["input"]}
        upd.pop("catalogFunctionDto", None)
        req = urllib.request.Request(f"{m.base}/api/v2/core/deviceTypes/{uuid}/kpiFunctions/{k['name']}", method="PUT",
                                     headers=m.h, data=json.dumps(upd).encode())
        try:
            with urllib.request.urlopen(req, context=ssl._create_unverified_context(), timeout=120):
                return "updated"
        except urllib.error.HTTPError as e:
            return f"update failed: HTTP {e.code} {e.read()[:200]!r}"
    r = m.call("POST", f"/api/v2/core/deviceTypes/{uuid}/kpiFunctions",
               {**body, "enabled": True, "schedule": SCHEDULE, "backtrack": {}, "outputMeta": {out: {"transient": False}}}, ok_fail=True)
    return r["error"][:300] if "error" in r else "created"


def step_functions(m, d):
    t = types(m)
    for dt, out, expr in CALCS:
        print(dt, out, ensure_fn(m, t[dt], out, {"catalogFunctionName": "PythonExpression", "description": expr,
                                                 "input": {"expression": expr}, "output": {"output_name": out}}))
    for dt, src, out, win in ANOMALY:
        print(dt, out, ensure_fn(m, t[dt], out, {"catalogFunctionName": "KMeansAnomalyScore", "description": f"{src} anomaly score",
                                                 "input": {"input_item": src, "windowsize": win}, "output": {"output_item": out}}))
    for dt, out, expr, sev in ALERTS:
        print(dt, out, ensure_fn(m, t[dt], out, {"catalogFunctionName": "AlertExpression", "description": expr,
                                                 "input": {"expression": expr, "Severity": sev, "Status": "New"},
                                                 "output": {"alert_name": out}}))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key-file", required=True)
    ap.add_argument("--api", required=True)
    ap.add_argument("--step", default="all")
    a = ap.parse_args()
    props = dict(l.split("=", 1) for l in open(os.path.expanduser(a.key_file), encoding="utf-8").read().splitlines()
                 if "=" in l and not l.startswith("#"))
    m = Monitor(a.api, props)
    d = json.load(open(HERE / "line.json", encoding="utf-8"))
    for s, fn in [("types", step_types), ("functions", step_functions)]:
        if a.step in (s, "all"):
            print(f"== {s}")
            fn(m, d)


if __name__ == "__main__":
    main()
