class Monitor:
    def __init__(self, api, props):
        self.base = api.rstrip("/")
        self.h = {"x-api-key": props["key"], "x-api-token": props["token"], "tenantId": props["tenant"],
                  "mam_user_email": "monitor-api@example.com", "Content-Type": "application/json", "Accept": "application/json"}

    def call(self, method, path, body=None, ok_fail=False):
        r = urllib.request.Request(self.base + path, method=method, headers=self.h,
                                   data=json.dumps(body).encode() if body is not None else None)
        try:
            with urllib.request.urlopen(r, context=CTX, timeout=120) as f:
                t = f.read()
                return json.loads(t) if t else {}
        except urllib.error.HTTPError as e:
            msg = f"{method} {path}: HTTP {e.code} {e.read()[:400]!r}"
            if ok_fail:
                return {"error": msg}
            raise SystemExit(msg)


def items(x):
    if isinstance(x, list):
        return x
    for k in ("results", "data", "items", "content", "deviceTypes", "devices"):
        if isinstance(x, dict) and isinstance(x.get(k), list):
            return x[k]
    return []
