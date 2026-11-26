"""Patch an Unlcvt DB2 script so rows with a NOT NULL BLOB column load.

Created by Mohamed Chihaoui.

Unlcvt does not unload BLOB data: it writes null for every BLOB value. Where the column is
NOT NULL (REPORTOUTPUTCNT.CONTENT, MAFAPPDATA.APP ...), maxinst stops on DB2 with
SQLCODE=-407. This script rewrites those nulls to an empty BLOB, BLOB(X''), so the load
finishes; blob_copy (CvtTool.java blobs) then copies the real bytes from the source.

Usage: python fix_not_null_blobs.py <in Unlcvt.db2> <out Unlcvt.db2> TABLE.COLUMN [TABLE.COLUMN ...]
"""
import re
import sys

INS = re.compile(r"^\s*insert\s+into\s+(\w+)", re.I)

def split_top(s):
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
        elif c in "()":
            depth += 1 if c == "(" else -1; cur.append(c)
        elif c == "," and depth == 0:
            out.append("".join(cur)); cur = []
        else:
            cur.append(c)
        i += 1
    out.append("".join(cur))
    return out

def patch(stmt, cols_to_fix):
    m = re.match(r"(\s*insert\s+into\s+\w+\s*)\((.*?)\)(\s*values\s*)\((.*)\)(\s*)$", stmt, re.S | re.I)
    if not m:
        return stmt, False
    cols = [c.strip().upper() for c in m.group(2).replace("\n", " ").split(",")]
    vals = split_top(m.group(4))
    if len(cols) != len(vals):
        return stmt, False
    changed = False
    for i, c in enumerate(cols):
        if c in cols_to_fix and vals[i].strip().lower() == "null":
            vals[i] = vals[i].lower().replace("null", "blob(x'')"); changed = True
    if not changed:
        return stmt, False
    return f"{m.group(1)}({m.group(2)}){m.group(3)}({','.join(vals)}){m.group(5)}", True

def main(src, dst, *targets):
    fix = {}
    for t in targets:
        tb, col = t.upper().split(".")
        fix.setdefault(tb, set()).add(col)
    n = 0
    with open(src, encoding="utf-8", errors="surrogateescape") as f, \
         open(dst, "w", encoding="utf-8", errors="surrogateescape", newline="") as o:
        buf, table = [], None
        for line in f:
            if table is None:
                m = INS.match(line)
                if m and m.group(1).upper() in fix:
                    table, buf = m.group(1).upper(), [line]
                else:
                    o.write(line)
                continue
            if line.strip() == ";":
                stmt, ok = patch("".join(buf), fix[table])
                n += ok
                o.write(stmt); o.write(line)
                table, buf = None, []
            else:
                buf.append(line)
    print(f"{n} inserts patched -> {dst}")

if __name__ == "__main__":
    main(*sys.argv[1:])
