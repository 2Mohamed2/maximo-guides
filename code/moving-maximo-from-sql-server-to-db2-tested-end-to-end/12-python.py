"""Dual-run check: run every saved query on the Oracle or SQL Server source and on the Db2 target, compare row counts.

Created by Mohamed Chihaoui.

A rewritten clause is only "converted" when Db2 returns what Oracle returned. This script reads the
saved queries (QUERY) from the source, turns each into
    select count(*) from <application main table> where <clause>
and runs it on both databases. On Db2 it uses the clause stored in the Db2 database, or the rewrite
from --rewrites (CSV: app,clausename,owner,db2_clause,why) when you are testing a draft.

It drives the two command-line clients, so it runs on any host that has them:
  --src         oracle (default) or sqlserver
  --ora-shell   a command that runs a bash script where sqlplus (or sqlcmd) works  (default: bash)
  --db2-shell   a command that runs a bash script where the db2 CLP works  (default: bash)
  --ora-conn    sqlplus connect string, e.g. maximo/<password>@//<host>:1521/<service>   (required)
  --ss-conn     sqlcmd options for a SQL Server source, e.g. "-S <host> -U maximo -P <password> -d MAXDB"  (with --src sqlserver)
  --db2-db / --db2-schema                          (default: MAXDB / MAXIMO)
Example, from a jump host:
  python dual_run.py --ora-shell "ssh oracle-host bash -s" --db2-shell "ssh db2inst1@db2-host bash -s" \\
                     --ora-conn "maximo/<password>@//<host>:1521/<service>" --rewrites db2_rewrites.csv --out dual_run.csv

Bind variables: :USER becomes 'MAXADMIN'; clauses with other Maximo binds (:&...&, :siteid ...) are
reported as SKIPPED, test those in the application.
"""
import argparse
import csv
import re
import shlex
import subprocess

SEP = "~"
A = None   # parsed arguments

def sh(shell, script):
    """Run a bash script through a shell command (local bash, ssh, ...).
    The script is written to a temp file before it runs: the db2 command line processor reads
    stdin and would swallow the rest of a script piped into bash. Carriage returns are removed."""
    wrapped = ("f=$(mktemp); cat > \"$f\" <<'__DUALRUN__'\n" + script.replace("\r", "")
               + "\n__DUALRUN__\nbash \"$f\"; rm -f \"$f\"\n")
    # bytes, not text: on Windows a text-mode pipe turns every \n into \r\n
    out = subprocess.run(shlex.split(shell), input=wrapped.encode("utf-8"), capture_output=True).stdout
    return out.decode("utf-8", errors="replace").replace("\r", "")

def sqlplus(body):
    return ("sqlplus -s " + A.ora_conn + " <<'EOF'\nset pagesize 0 linesize 32767 trimspool on feedback off heading off\n"
            + body + "\nexit\nEOF\n")

def db2_head():
    return [". ~/sqllib/db2profile 2>/dev/null", f"db2 connect to {A.db2_db} > /dev/null", f"db2 set schema {A.db2_schema} > /dev/null"]

def sqlcmd(body, sep=False):
    """sqlcmd script for a SQL Server source. Each statement is its own batch (go), so one error does not stop the rest."""
    opts = '-h -1 -W -s "~"' if sep else "-h -1 -W"
    return f"{A.sqlcmd} -C {A.ss_conn} {opts} -i /dev/stdin <<'EOF'\nset nocount on\ngo\n{body}\nEOF\n"

def queries():
    if A.src == "sqlserver":
        sql = ("select q.app, q.clausename, q.owner, a.maintbname, replace(replace(q.clause, char(10), ' '), char(13), ' ') "
               "from query q join maxapps a on a.app = q.app where a.maintbname is not null order by 1, 2, 3\ngo")
        return [l.split(SEP) for l in sh(A.ora_shell, sqlcmd(sql, sep=True)).splitlines() if l.count(SEP) >= 4]
    sql = ("set markup csv on quote off delimiter ~\n"
           "select q.app, q.clausename, q.owner, a.maintbname, replace(replace(q.clause, chr(10), ' '), chr(13), ' ') "
           "from query q join maxapps a on a.app = q.app where a.maintbname is not null order by 1, 2, 3;")
    return [l.split(SEP) for l in sh(A.ora_shell, sqlplus(sql)).splitlines() if SEP in l]

def db2_clauses():
    lines = db2_head() + ["db2 -x \"select app || '~' || clausename || '~' || owner || '~' || "
                          "replace(replace(clause, chr(10), ' '), chr(13), ' ') from query\""]
    d = {}
    for l in sh(A.db2_shell, "\n".join(lines)).splitlines():
        p = l.rstrip().split(SEP, 3)
        if len(p) == 4:
            d[tuple(p[:3])] = p[3]
    return d

def prep(clause):
    # Maximo accepts a stored clause that starts with WHERE or ends with ORDER BY; count(*) does not
    clause = re.sub(r"^\s*where\s+", "", clause, flags=re.I)
    clause = re.sub(r"\s+order\s+by\s+[\w\s,.]+$", "", clause, flags=re.I)
    if re.search(r":&|:[a-z]", re.sub(r":user\b", "", clause, flags=re.I), re.I):
        return None
    return re.sub(r":user\b", "'MAXADMIN'", clause, flags=re.I)

def count_oracle(items):
    if A.src == "sqlserver":
        lines = []
        for i, (tbl, clause) in enumerate(items):
            # the marker gets its own batch: a syntax error stops the whole batch, print included
            lines += [f"print '@@{i}'", "go", f"select count(*) from {tbl} where {clause}", "go"]
        return parse(sh(A.ora_shell, sqlcmd("\n".join(lines))), len(items), r"(Msg \d+)")
    lines = []
    for i, (tbl, clause) in enumerate(items):
        lines += [f"prompt @@{i}", f"select count(*) from {tbl} where {clause};"]
    return parse(sh(A.ora_shell, sqlplus("\n".join(lines))), len(items), r"(ORA-\d+)")

def count_db2(items):
    lines = db2_head()
    for i, (tbl, clause) in enumerate(items):
        stmt = f"select count(*) from {tbl} where {clause}".replace('"', '\\"')
        lines.append(f'echo "@@{i}"; db2 -x "{stmt}" 2>&1')
    return parse(sh(A.db2_shell, "\n".join(lines)), len(items), r"(SQL\d+N)")

def parse(out, n, err):
    res, cur, buf = {}, None, []
    for line in out.splitlines() + ["@@end"]:
        m = re.match(r"^@@(\d+|end)", line.strip())
        if m:
            if cur is not None:
                e = re.search(err, " ".join(buf))
                num = re.search(r"^\s*(\d+)\s*$", "\n".join(buf), re.M)
                res[cur] = e.group(1) if e else (num.group(1) if num else "?")
            cur, buf = (None if m.group(1) == "end" else int(m.group(1))), []
        elif cur is not None:
            buf.append(line)
    return [res.get(i, "?") for i in range(n)]

def main():
    global A
    ap = argparse.ArgumentParser()
    ap.add_argument("--ora-shell", default="bash")
    ap.add_argument("--db2-shell", default="bash")
    ap.add_argument("--src", choices=["oracle", "sqlserver"], default="oracle")
    ap.add_argument("--ora-conn", help="sqlplus connect string (Oracle source)")
    ap.add_argument("--ss-conn", help='sqlcmd connection options (SQL Server source), e.g. "-S host -U maximo -P pw -d MAXDB"')
    ap.add_argument("--sqlcmd", default="sqlcmd", help="path of sqlcmd on the source shell")
    ap.add_argument("--db2-db", default="MAXDB")
    ap.add_argument("--db2-schema", default="MAXIMO")
    ap.add_argument("--rewrites")
    ap.add_argument("--only", help="regexp on clausename")
    ap.add_argument("--out", default="dual_run.csv")
    A = ap.parse_args()
    if (A.src == "oracle" and not A.ora_conn) or (A.src == "sqlserver" and not A.ss_conn):
        ap.error("--ora-conn is required for an Oracle source, --ss-conn for a SQL Server source")
    rew = {}
    if A.rewrites:
        for r in csv.DictReader(open(A.rewrites, encoding="utf-8")):
            rew[(r["app"], r["clausename"], r["owner"])] = r["db2_clause"]
    on_db2 = db2_clauses()
    rows, o_items, d_items = [], [], []
    for app, name, owner, tbl, clause in queries():
        if A.only and not re.search(A.only, name):
            continue
        key = (app, name, owner)
        d_clause = rew.get(key, on_db2.get(key, clause))
        po, pd = prep(clause), prep(d_clause)
        rows.append([app, name, owner, tbl, clause, d_clause, po is None])
        if po is not None:
            o_items.append((tbl, po)); d_items.append((tbl, pd))
    oc, dc = count_oracle(o_items), count_db2(d_items)
    k, tally = 0, {}
    with open(A.out, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["app", "clausename", "owner", "table", "oracle_count", "db2_count", "verdict", "oracle_clause", "db2_clause"])
        for app, name, owner, tbl, clause, d_clause, skipped in rows:
            if skipped:
                o = d = ""; v = "SKIPPED (binds)"
            else:
                o, d = oc[k], dc[k]; k += 1
                v = ("DB2 ERROR" if d.startswith("SQL") else "SOURCE ERROR" if o.startswith(("ORA", "Msg")) else
                     "SAME" if o == d else "DIFFERENT")
            tally[v] = tally.get(v, 0) + 1
            w.writerow([app, name, owner, tbl, o, d, v, clause, d_clause])
    print(tally, "->", A.out)

if __name__ == "__main__":
    main()
