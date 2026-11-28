"""List the Maximo records IBM's update scripts write differently per database (DBC files with a target).

Created by Mohamed Chihaoui.

The maxdemo files (diff_ibm_platform_rows.py) only hold what the demo database contained when IBM unloaded
it. Records added later by update scripts are not in them. Those scripts are DBC files, and when a record
needs different SQL per database IBM ships two scripts: one with target="sqlserver" (or "oracle") and one
with target="not_sqlserver" (or "not_oracle"), inserting the same record with different text. Example in
Manage 9.3: V9300_44.dbc (sqlserver) inserts condition DLJOBITEMS with "select top 1 1 ...", V9300_45.dbc
(not_sqlserver) inserts it with "... fetch first 1 row only".

A third form lives in add-on content files (.isc): one text in "new" plus per-database substitution
rules, e.g. <ATTRIBUTE name="SELECTSTMT" new="select avg(sysdate-reportdate) from workorder"
db2value="{sysdate -> current timestamp}" sqsvalue="{sysdate -> getdate()}"/> (Nuclear KPIs).

This script pairs them by table and natural key and writes the same CSV as diff_ibm_platform_rows.py
(table,key,column,oracle_text,db2_text; the first text column holds the source platform's text), so
ibm_db2_text_fix.py turns it into guarded updates.

Usage: python diff_ibm_targeted_dbc.py <SMP>/maximo sqlserver|oracle <out.csv>
"""
import csv
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from diff_ibm_platform_rows import KEYS

SQL_COLS = {"QUERY": "CLAUSE", "MAXRELATIONSHIP": "WHERECLAUSE", "CONDITION": "EXPRESSION", "ESCALATION": "CONDITION",
            "KPIMAIN": "CLAUSE", "MAXINTOBJECT": "RESTRICTWHERE", "OSLCQUERY": "CLAUSE", "MAXTABLEDOMAIN": "LISTWHERECLAUSE",
            "SCRIPTLAUNCHPOINT": "CONDITION", "SLA": "CONDITION", "WFCONDITION": "CONDITION"}

def target_of(path):
    head = path.read_text(encoding="utf-8", errors="replace")[:600]
    m = re.search(r'<script[^>]*\btarget="([a-z_,]+)"', head, re.S | re.I)
    return m.group(1).lower() if m else None

def records(path):
    """(table, key, column) -> text for every insertrow / update of a SQL-bearing column in one DBC file."""
    out = {}
    try:
        # IBM's DBC files carry Maximo binds such as :&USERNAME& unescaped, which is not valid XML
        text = re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", "&amp;", path.read_text(encoding="utf-8", errors="replace"))
        root = ET.fromstring(text)
    except ET.ParseError:
        return out
    for ins in root.iter("insert"):
        tb = (ins.get("table") or "").upper()
        if tb not in SQL_COLS or tb not in KEYS:
            continue
        for row in ins.iter("insertrow"):
            vals = {cv.get("column", "").upper(): cv.get("string") for cv in row.iter("columnvalue")}
            col = SQL_COLS[tb]
            if vals.get(col) is None:
                continue
            key = "|".join(str(vals.get(k)) for k in KEYS[tb])
            out[(tb, key, col)] = vals[col]
    return out

PLATFORM_ATTR = {"sqlserver": "sqsvalue", "oracle": "oravalue", "db2": "db2value"}

def apply_rules(text, rules):
    """Apply '{a -> b}' substitution rules (one or more) as IBM's .isc files write them."""
    for a, b in re.findall(r"\{\s*(.+?)\s*->\s*(.*?)\s*\}", rules or ""):
        text = text.replace(a, b)
    return text

def isc_records(path, source):
    """(table, key, column) -> (source text, db2 text) for .isc attributes that carry per-database values."""
    out = {}
    try:
        root = ET.fromstring(re.sub(r"&(?!amp;|lt;|gt;|quot;|apos;|#)", "&amp;", path.read_text(encoding="utf-8", errors="replace")))
    except ET.ParseError:
        return out
    for tb_el in root:
        tb = (tb_el.get("tbname") or "").upper()
        if tb not in KEYS:
            continue
        for key_el in tb_el.iter("KEY"):
            attrs = {a.get("name", "").upper(): a for a in key_el.iter("ATTRIBUTE")}
            key = "|".join(str(key_el.get(k) or (attrs[k].get("new") if k in attrs else None)) for k in KEYS[tb])
            for col, a in attrs.items():
                if not any(a.get(v) for v in PLATFORM_ATTR.values()):
                    continue
                base = a.get("new") or ""
                src = apply_rules(base, a.get(PLATFORM_ATTR[source])) if source != "oracle" or a.get("oravalue") else base
                tgt = apply_rules(base, a.get("db2value"))
                if src != tgt:
                    out[(tb, key, col)] = (src, tgt)
    return out

def main(smp, source, out_csv):
    files = [p for p in Path(smp).rglob("*.dbc")]
    src, other = {}, {}
    for p in files:
        t = target_of(p)
        if not t:
            continue
        recs = records(p)
        if t == source:
            src.update(recs)
        elif t in (f"not_{source}", "db2"):
            other.update(recs)
    isc = {}
    for p in Path(smp).rglob("*.isc"):
        isc.update(isc_records(p, source))
    n = 0
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["table", "key", "column", "oracle_text", "db2_text"])
        for k, text in sorted(src.items()):
            if k in other and other[k] != text:
                w.writerow([k[0], k[1], k[2], text, other[k]]); n += 1
        for k, (a, b) in sorted(isc.items()):
            w.writerow([k[0], k[1], k[2], a, b]); n += 1
    print(f"{len(files)} DBC files; {len(src)} records in target={source} scripts; {len(isc)} .isc values with per-database text; "
          f"{n} rows with a different Db2 text -> {out_csv}")

if __name__ == "__main__":
    main(*sys.argv[1:4])
