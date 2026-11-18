"""End-to-end test of the contractor API through the API Connect gateway.

Reads the apps' client ID and secret from contractor_apps.env (one line per value, KEY=value), which you fill in
and never commit. Prints status code and body of every call; never prints the credentials.

    python test_gateway.py https://<gateway-host>/<provider-org>/<catalog>
"""
import json
import os
import sys
import urllib.error
import urllib.request

BASE = sys.argv[1].rstrip("/") + "/contractor/v1" if len(sys.argv) > 1 else sys.exit(__doc__)
ENV = {}
for line in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "contractor_apps.env"), encoding="utf-8"):
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.strip().split("=", 1)
        ENV[k.strip()] = v.strip()

def call(who, method, path, body=None):
    h = {"Accept": "application/json", "Content-Type": "application/json"}
    if who:
        h["X-IBM-Client-Id"] = ENV[who + "_CLIENT_ID"]
        h["X-IBM-Client-Secret"] = ENV[who + "_CLIENT_SECRET"]
    r = urllib.request.Request(BASE + path, method=method, headers=h,
                               data=json.dumps(body).encode() if body is not None else None)
    try:
        with urllib.request.urlopen(r, timeout=30) as f:
            code, text = f.status, f.read().decode()
    except urllib.error.HTTPError as e:
        code, text = e.code, e.read().decode()
    print(f"\n### {who or 'no credentials'}  {method} {path}" + (f"  {json.dumps(body)}" if body else ""))
    print(code, text[:1500])

who = [w for w in ("NORTHAIR", "VOLTPRO", "LIFTCARE") if ENV.get(w + "_CLIENT_ID")]
call(None, "GET", "/workorders")
for w in who:
    call(w, "GET", "/workorders")
if "NORTHAIR" in who:
    call("NORTHAIR", "GET", "/workorders?status=done")
    call("NORTHAIR", "GET", "/workorders/8839")
    call("NORTHAIR", "GET", "/workorders/8844")          # VOLTPRO's work order
    call("NORTHAIR", "GET", "/workorders/88%3B44")       # fails the number pattern
    call("NORTHAIR", "POST", "/workorders/8841/completion", {"completedAt": "2026-11-11T10:30:00+03:00"})
    call("NORTHAIR", "POST", "/workorders/8844/completion",
         {"completedAt": "2026-11-11T10:30:00+03:00", "note": "Trying another contractor's job"})
    call("NORTHAIR", "POST", "/workorders/8841/completion",
         {"completedAt": "2026-11-11T10:30:00+03:00",
          "note": "Fan rebalanced and both bearings replaced. Vibration down from 7.4 to 1.9 mm/s."})
    call("NORTHAIR", "POST", "/workorders/8841/completion",
         {"completedAt": "2026-11-11T10:35:00+03:00", "note": "Second report for the same job"})
