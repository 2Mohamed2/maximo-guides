"""List the Maximo records IBM writes differently for Oracle and for DB2.

Created by Mohamed Chihaoui.

Every Maximo release ships tools/maximo/en/maxdemo.ora and maxdemo.db2: the same demo database,
unloaded by Unlcvt from an Oracle and from a DB2 database.  Where IBM had to write a record
differently per database (a relationship with ROWNUM on Oracle and ROW_NUMBER() on DB2, for
example), the two files disagree.  After an Oracle-to-DB2 conversion those records still hold
the Oracle text, because Unlcvt copies rows as data.  This script lists them, with the DB2 text
IBM uses, so they can be set back to IBM's DB2 version.

Usage: python diff_ibm_platform_rows.py <maxdemo.ora> <maxdemo.db2> <out.csv>
"""
import csv
import re
import sys

IGNORE_COLS = {"ROWSTAMP"}
# SQL-bearing Maximo tables and their natural keys (ids differ between the two IBM files)
KEYS = {
    "MAXRELATIONSHIP": ("PARENT", "NAME"),
    "QUERY": ("APP", "CLAUSENAME", "OWNER"),
    "CONDITION": ("CONDITIONNUM",),
    "ESCALATION": ("ESCALATION",),
    "WFCONDITION": ("PROCESSNAME", "PROCESSREV", "NODEID"),
    "WFACTION": ("PROCESSNAME", "PROCESSREV", "ACTIONID"),
    "WFASSIGNMENT": ("PROCESSNAME", "PROCESSREV", "NODEID", "ASSIGNID"),
    "KPIMAIN": ("KPINAME",),
    "MAXINTOBJECT": ("INTOBJECTNAME",),
    "MAXIFACEEXPORT": ("IFACENAME",),
    "OSLCQUERY": ("INTOBJECTNAME", "CLAUSENAME"),
    "MAXTABLEDOMAIN": ("DOMAINID", "OBJECTNAME", "ORGID", "SITEID"),
    "MAXDYNAMICDOMLINK": ("OBJECTNAME", "ATTRIBUTENAME"),
    "MAXVIEW": ("VIEWNAME",),
    "SCRIPTLAUNCHPOINT": ("LAUNCHPOINTNAME",),
    "SLA": ("SLANUM",),
    "REPORTADHOC": ("REPORTNAME",),
    "AUTOSCRIPT": ("AUTOSCRIPT",),
    "MAXPROPVALUE": ("PROPNAME", "SERVERNAME", "SERVERHOST"),
    "MAXPROP": ("PROPNAME",),
    "MAXVARS": ("VARNAME", "ORGID", "SITEID"),
}
INS = re.compile(r"^\s*insert\s+into\s+(\w+)", re.I)

def statements(path):
    """Yield (table, [cols], [values]) for every INSERT in an Unlcvt file."""
    buf, table = [], None
    with open(path, encoding="utf-8", errors="replace") as f:
        for line in f:
            m = INS.match(line)
            if m and table is None:
                table, buf = m.group(1).upper(), [line[m.end():]]
                continue
            if table is None:
                continue
            buf.append(line)
            s = line.rstrip()
            # Oracle files end a statement with ';' or '/', DB2 files with ';'
            if s in (";", "/") or (s.endswith(";") and balanced("".join(buf))):
                text = "".join(buf).strip().rstrip(";/").strip()
                parsed = parse(text)
                if parsed:
                    yield (table,) + parsed
                table, buf = None, []

def balanced(text):
    return text.count("'") % 2 == 0

def split_top(s):
    """Split on commas outside quotes and parentheses."""
    out, cur, depth, q, i = [], [], 0, False, 0
    while i < len(s):
        c = s[i]
        if q:
            cur.append(c)
            if c == "'":
                if i + 1 < len(s) and s[i + 1] == "'":
                    cur.append("'"); i += 1
                else:
                    q = False
        elif c == "'":
            q = True; cur.append(c)
        elif c == "(":
            depth += 1; cur.append(c)
        elif c == ")":
            depth -= 1; cur.append(c)
        elif c == "," and depth == 0:
            out.append("".join(cur).strip()); cur = []
        else:
            cur.append(c)
        i += 1
    out.append("".join(cur).strip())
    return out

def parse(text):
    m = re.match(r"\((.*?)\)\s*values\s*\((.*)\)\s*$", text, re.S | re.I)
    if not m:
        return None
    cols = [c.strip().upper() for c in m.group(1).replace("\n", " ").split(",")]
    vals = split_top(m.group(2))
    if len(cols) != len(vals):
        return None
    return cols, vals

def norm(v):
    v = v.strip()
    if v.startswith("'") and v.endswith("'"):
        return v[1:-1].replace("''", "'").replace("\r", "")
    return None   # number, NULL or a function call: not SQL text

def load(path):
    rows = {}
    for table, cols, vals in statements(path):
        if table not in KEYS:
            continue
        d = dict(zip(cols, vals))
        rows[(table, "|".join(str(norm(d.get(c, "null"))) for c in KEYS[table]))] = d
    return rows

def main(ora, db2, out):
    a, b = load(ora), load(db2)
    n = 0
    with open(out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["table", "key", "column", "oracle_text", "db2_text"])
        for k, ra in a.items():
            rb = b.get(k)
            if not rb:
                continue
            for col, va in ra.items():
                if col in IGNORE_COLS or col not in rb:
                    continue
                ta, tb = norm(va), norm(rb[col])
                if ta is None or tb is None or ta == tb:
                    continue
                w.writerow([k[0], k[1], col, ta, tb]); n += 1
    print(f"{len(a)} Oracle rows, {len(b)} DB2 rows, {n} text columns differ -> {out}")

if __name__ == "__main__":
    main(*sys.argv[1:4])
