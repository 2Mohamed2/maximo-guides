"""Demo data for the contractor API: three contractor companies and the BEDFORD work orders assigned to them.

Re-runnable: companies are created only if missing; work orders are created only if no open work order with
the same description and vendor exists. Uses the Manage REST API (MXAPIVENDORMSTR, MXAPIVENDOR, MXAPIWODETAIL).

    set MAXIMO_API=https://<manage-host>/maximo/api
    set MAXIMO_APIKEY=<an administrator's API key, for the demo data only>
    python seed_demo.py
"""
import datetime as dt
import json
import os
import urllib.error
import urllib.parse
import urllib.request

class m:  # minimal Maximo REST client
    BASE, KEY = os.environ["MAXIMO_API"].rstrip("/"), os.environ["MAXIMO_APIKEY"]

    @staticmethod
    def call(method, path, body=None, headers=None):
        h = {"apikey": m.KEY, "Accept": "application/json", "Content-Type": "application/json"}
        h.update(headers or {})
        r = urllib.request.Request(m.BASE + path, method=method, headers=h,
                                   data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(r, timeout=120) as f:
                t = f.read()
                return f.status, (json.loads(t) if t else {})
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b"{}")

    @staticmethod
    def find(os_name, where, select="*"):
        q = urllib.parse.urlencode({"lean": 1, "oslc.select": select, "oslc.where": where, "oslc.pageSize": 100})
        code, r = m.call("GET", f"/os/{os_name}?{q}")
        if code != 200:  # never treat a failed query as "not found"
            raise SystemExit(f"query on {os_name} failed: {code} {json.dumps(r)[:300]}")
        return r.get("member", [])

ORG, SITE = "EAGLENA", "BEDFORD"
VENDORS = {
    "NORTHAIR": "NorthAir HVAC Services",
    "VOLTPRO": "VoltPro Electrical Contractors",
    "LIFTCARE": "LiftCare Cranes and Hoists",
}
# vendor, asset, location, work type, priority, days to due, final status, description
WORK = [
    ("NORTHAIR", "11200", "BR200", "CM", 1, 1, "APPR",  "HVAC unit tripping on high head pressure"),
    ("NORTHAIR", "11210", "BR210", "PM", 3, 6, "APPR",  "Quarterly fan belt and bearing inspection"),
    ("NORTHAIR", "11240", "BR240", "CM", 2, 2, "INPRG", "Circulation fan vibration above 7 mm/s"),
    ("NORTHAIR", "11250", "BR200", "PM", 3, 9, "WSCH",  "Replace filters and clean coils"),
    ("NORTHAIR", "11300", "BR300", "CM", 2, 3, "APPR",  "Compressor short cycling, check refrigerant charge"),
    ("VOLTPRO",  "11220", "ECC210", "CM", 1, 1, "APPR", "HVAC control panel breaker tripping"),
    ("VOLTPRO",  "11230", "BR230", "PM", 2, 5, "APPR",  "Emergency generator monthly load test"),
    ("VOLTPRO",  "11211", "BR210", "CM", 3, 4, "INPRG", "Motor starter contactor chatter"),
    ("VOLTPRO",  "11340", "BR300", "PM", 3, 12, "WSCH", "Thermographic survey of motor starters"),
    ("LIFTCARE", "12200", "SHIPPING", "PM", 2, 3, "APPR", "Overhead crane #1 statutory inspection"),
    ("LIFTCARE", "12210", "SHIPPING", "CM", 1, 1, "APPR", "Crane #1 brake slipping under load"),
    ("LIFTCARE", "12500", "SHIPPING", "PM", 3, 10, "WSCH", "Overhead crane #2 rope and hook check"),
]

def q(params):
    return urllib.parse.urlencode(params)

def ensure_vendor(code, name):
    found = m.find("mxapivendor", f'company="{code}" and orgid="{ORG}"', "company")
    if found:
        return "exists"
    if not m.find("mxapivendormstr", f'company="{code}"', "company"):
        c0, r0 = m.call("POST", "/os/mxapivendormstr?lean=1", {"company": code, "name": name, "type": "V", "companysetid": "COMPSET1"})
        if c0 not in (200, 201):
            return f"master FAILED {c0} {json.dumps(r0)[:300]}"
    code_, r = m.call("POST", "/os/mxapivendor?lean=1", {
        "company": code, "name": name, "type": "V", "orgid": ORG, "companysetid": "COMPSET1", "currencycode": "USD"})
    return f"created {code_}" if code_ in (200, 201) else f"FAILED {code_} {json.dumps(r)[:300]}"

def ensure_wo(vendor, asset, loc, wtype, prio, days, status, desc):
    # oslc.where has no "not in" (BMXAA8744E), so list the statuses that count as existing work
    where = (f'siteid="{SITE}" and vendor="{vendor}" and description="{desc}"'
             ' and status in ["WAPPR","APPR","WSCH","WMATL","INPRG","COMP"]')
    found = m.find("mxapiwodetail", where, "wonum,status,href")
    if found:
        return found[0]["wonum"], "exists"
    due = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=days)).replace(hour=17, minute=0, second=0, microsecond=0)
    body = {"siteid": SITE, "description": desc, "assetnum": asset, "location": loc, "worktype": wtype,
            "wopriority": prio, "vendor": vendor, "targstartdate": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
            "targcompdate": due.isoformat(timespec="seconds")}
    code, r = m.call("POST", "/os/mxapiwodetail?lean=1&" + q({"oslc.properties": "wonum,href"}), body,
                     {"properties": "wonum,href"})
    if code not in (200, 201):
        return None, f"FAILED {code} {json.dumps(r)[:300]}"
    wonum, href = r["wonum"], r["href"]
    rid = href.rsplit("/", 1)[1]
    for st in {"APPR": ["APPR"], "WSCH": ["APPR", "WSCH"], "INPRG": ["APPR", "INPRG"]}[status]:
        c2, r2 = m.call("POST", f"/os/mxapiwodetail/{rid}?lean=1&action=wsmethod:changeStatus",
                        {"status": st, "memo": "Assigned to contractor " + vendor}, {"x-method-override": "PATCH"})
        if c2 not in (200, 204):
            return wonum, f"created, status {st} FAILED {c2} {json.dumps(r2)[:200]}"
    return wonum, "created " + status

if __name__ == "__main__":
    for code, name in VENDORS.items():
        print("vendor", code, ensure_vendor(code, name))
    for row in WORK:
        print("wo", row[0], *ensure_wo(*row))
