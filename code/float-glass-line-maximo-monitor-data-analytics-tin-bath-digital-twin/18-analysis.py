"""Offline analytics on the Monitor data lake: where did the tonnes go over the 14 days of history on Line 1 (up to sim.ANCHOR)?

    python analysis.py [--days 14]      -> analysis.json (read by the video's loss panel)

Reads the line roll-up (IOT_FG_LINE_*) and the inspection results (IOT_FG_COLDEND_*) from Db2 (BLUDB, schema WSP_MAM)
through `oc exec` in the shared Db2 pod, joins them per 5 minutes, and puts every tonne melted but not packed in one
bucket: cold-end stop (line state 0), job change (state 1), bubbles (furnace refining), tin defects (tin bath),
or the normal edge trim and cut loss.
"""
import argparse
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).parent
POD = ["oc", "exec", "-n", "db2u", "<data-lake-db2-pod>", "-c", "db2u", "--"]
BASE_YIELD = 88.6          # the line's normal pack-to-melt yield at 4 mm (edge trim and cut loss)


def query(sql):
    r = subprocess.run(POD + ["su", "-", "db2inst1", "-c", f'db2 connect to BLUDB >/dev/null; db2 -x "{sql}"'],
                       capture_output=True, text=True)
    return [l.split() for l in r.stdout.splitlines() if l.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--days", type=int, default=14)
    a = ap.parse_args()
    t = json.load(open(HERE / "lake_tables.json", encoding="utf-8"))
    ln, ce = t["FG_LINE"], t["FG_COLDEND"]
    c = lambda tb, m: tb["cols"][m]
    from datetime import datetime, timezone
    import sim
    fmt = lambda x: datetime.fromtimestamp(x, timezone.utc).strftime("%Y-%m-%d-%H.%M.%S")
    start, end = fmt(sim.ANCHOR - a.days * 86400), fmt(sim.ANCHOR)
    sql = (f"select varchar_format(l.rcv_timestamp_utc,'YYYY-MM-DD-HH24:MI'), l.{c(ln,'PULL_RATE')}, l.{c(ln,'YIELD')}, l.{c(ln,'STATE')}, "
           f"c.{c(ce,'BUBBLES')}, c.{c(ce,'TIN_DEFECTS')} from {ln['schema']}.{ln['table']} l join {ce['schema']}.{ce['table']} c "
           f"on c.rcv_timestamp_utc = l.rcv_timestamp_utc where l.rcv_timestamp_utc >= timestamp('{start}') and l.rcv_timestamp_utc < timestamp('{end}') "
           f"and mod(minute(l.rcv_timestamp_utc), 5) = 0 and second(l.rcv_timestamp_utc) = 0")
    rows = query(sql)
    b = {"Cold-end stops": 0.0, "Job changes": 0.0, "Bubbles (furnace)": 0.0, "Tin defects (tin bath)": 0.0, "Normal trim and cut loss": 0.0}
    melted = packed = 0.0
    for ts, pull, yld, state, bub, tin in rows:
        pull, yld, state, bub, tin = float(pull), float(yld), int(float(state)), float(bub), float(tin)
        m = pull / 288                        # tonnes melted in 5 minutes
        lost = m * (1 - yld / 100)
        melted, packed = melted + m, packed + m - lost
        if state == 0:
            b["Cold-end stops"] += lost
        elif state == 1:
            b["Job changes"] += lost
        else:
            normal = min(lost, m * (1 - BASE_YIELD / 100))
            extra = lost - normal
            b["Normal trim and cut loss"] += normal
            if bub > 0.3 and tin > 0.2:
                b["Bubbles (furnace)"] += extra / 2; b["Tin defects (tin bath)"] += extra / 2
            elif bub > 0.3:
                b["Bubbles (furnace)"] += extra
            elif tin > 0.2:
                b["Tin defects (tin bath)"] += extra
            else:
                b["Normal trim and cut loss"] += extra
    out = {"days": a.days, "rows": len(rows), "melted_t": round(melted), "packed_t": round(packed),
           "yield_pct": round(100 * packed / melted, 1) if melted else None,
           "lost_t": {k: round(v) for k, v in sorted(b.items(), key=lambda x: -x[1])}}
    (HERE / "analysis.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(json.dumps(out, indent=1))


if __name__ == "__main__":
    main()
