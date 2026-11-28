"""Find Oracle-only SQL stored inside a Maximo database (run against the SOURCE Oracle schema).

Created by Mohamed Chihaoui.

Maximo keeps SQL fragments in its own records: saved queries, relationships, conditions,
escalations, workflow, KPIs, object-structure restrictions, table domains, automation
scripts, BIRT report designs...  Unlcvt moves these rows across as data; it does not
rewrite them.  This script writes find_oracle_sql.sql, one SELECT that lists every stored
fragment matching a rule, with the rule's class:

  FAILS   - DB2 11.5 rejects it (tested on DB2 11.5.8, Varchar2 compatibility OFF)
  SILENT  - DB2 runs it but can return different rows (empty string versus NULL)

Usage:  python find_oracle_sql.py  ->  find_oracle_sql.sql
        sqlplus -s <owner>/<password>@<host>:<port>/<service> @find_oracle_sql.sql > findings.csv
Output: one row per finding, fields separated by ~ :
        class ~ rule ~ table.column ~ record key ~ first 300 characters ~ what to do on DB2
"""
from pathlib import Path

# (table, readable record key, SQL-bearing column)
SOURCES = [
    ("QUERY", "APP||':'||CLAUSENAME", "CLAUSE"),
    ("MAXRELATIONSHIP", "PARENT||'.'||NAME", "WHERECLAUSE"),
    ("CONDITION", "CONDITIONNUM", "EXPRESSION"),
    ("ESCALATION", "ESCALATION", "CONDITION"),
    ("WFCONDITION", "PROCESSNAME||':'||NODEID", "CONDITION"),
    ("WFACTION", "PROCESSNAME||':'||ACTIONID", "CONDITION"),
    ("WFASSIGNMENT", "PROCESSNAME||':'||NODEID||':'||ASSIGNID", "CONDITION"),
    ("KPIMAIN", "KPINAME", "CLAUSE"),
    ("KPIMAIN", "KPINAME", "SELECTSTMT"),
    ("MAXINTOBJECT", "INTOBJECTNAME", "RESTRICTWHERE"),
    ("MAXIFACEEXPORT", "IFACENAME", "EXPORTWHERE"),
    ("OSLCQUERY", "INTOBJECTNAME||':'||CLAUSENAME", "CLAUSE"),
    ("OSLCINTQUERY", "PROVIDERNAME||':'||QUERYNUM", "WHERECLAUSE"),
    ("MAXTABLEDOMAIN", "DOMAINID||':'||OBJECTNAME", "VALIDTNWHERECLAUSE"),
    ("MAXTABLEDOMAIN", "DOMAINID||':'||OBJECTNAME", "LISTWHERECLAUSE"),
    ("MAXDYNAMICDOMLINK", "OBJECTNAME||'.'||ATTRIBUTENAME", "DOMAINWHERE"),
    ("MAXVIEW", "VIEWNAME", "VIEWWHERE"),
    ("MAXVIEW", "VIEWNAME", "VIEWSELECT"),
    ("SCRIPTLAUNCHPOINT", "LAUNCHPOINTNAME", "CONDITION"),
    ("SLA", "SLANUM", "CONDITION"),
    ("REPORTADHOC", "REPORTNAME", "WHERECLAUSE"),
    ("PLUSGSEQOFEVENTS", "TICKETID||':'||NAME", "CONDITION"),
    ("SKDQUERY", "OBJECTNAME||':'||QUERYNAME", "WHERECLAUSE"),
    ("AUTOSCRIPT", "AUTOSCRIPT", "SOURCE"),          # CLOB: scripts that build SQL strings
    ("REPORTDESIGN", "REPORTNAME", "DESIGN"),        # CLOB: BIRT data-set SQL
]
CLOBS = {("AUTOSCRIPT", "SOURCE"), ("REPORTDESIGN", "DESIGN"), ("KPIMAIN", "SELECTSTMT"), ("KPIMAIN", "CLAUSE")}

# Oracle regular expressions have no \b word boundary: spell it out
B = r"(^|[^a-z0-9_])"
E = r"([^a-z0-9_]|$)"

# (rule, class, Oracle regexp matched case-insensitively, regexp that clears the finding or None, DB2 fix)
RULES = [
    ("DUAL", "FAILS", r"from\s+dual" + E, None, "use SYSIBM.SYSDUMMY1 (or VALUES ...)"),
    ("ROWNUM/ROWID", "FAILS", B + r"(rownum|rowid)" + E, None, "FETCH FIRST n ROWS ONLY / ROW_NUMBER() OVER ()"),
    ("CONNECT BY", "FAILS", r"connect\s+by\s+(nocycle\s+)?prior", None, "recursive WITH (common table expression)"),
    ("VARCHAR2/NUMBER type", "FAILS", B + r"(varchar2|nvarchar2|number)\s*\(", None, "VARCHAR(n) / DECIMAL(p,s)"),
    ("SYSTIMESTAMP", "FAILS", B + r"systimestamp" + E, None, "CURRENT TIMESTAMP"),
    ("INTERVAL literal", "FAILS", r"interval\s+'", None, "labelled duration: - 1 DAY, + 3 MONTHS"),
    ("SUBSTR negative start", "FAILS", r"substr\s*\([^,()]+,\s*-\s*[0-9]", None, "RIGHT(s, n)"),
    ("WM_CONCAT", "FAILS", r"wm_concat\s*\(", None, "LISTAGG(x, ',') WITHIN GROUP (ORDER BY ...)"),
    ("SYS_GUID", "FAILS", r"sys_guid\s*\(", None, "GENERATE_UNIQUE() / HEX(GENERATE_UNIQUE())"),
    ("Oracle hint", "FAILS", r"/\*\+", None, "remove the hint"),
    ("(a,b) = (select)", "FAILS", r",[^()]*\)\s*=\s*\(\s*select", None, "EXISTS (select ... where a = x.a and b = x.b)"),
    ("Oracle Text CONTAINS", "FAILS", B + r"contains\s*\(", None, "set up Db2 Text Search for the attribute, or use LIKE"),
    ("date +/- fraction of a day", "FAILS", r"(sysdate|date)\s*[-+]\s*\(?\s*[0-9]*\.[0-9]", None, "labelled duration: - 12 HOURS"),
    # date arithmetic: Oracle date - date = days; DB2 timestamp - timestamp = a yyyymmddhhmmss duration
    ("date - date", "SILENT", r"(sysdate|date)\s*-\s*\(?\s*[a-z_.]*[a-z_]", r"-\s*(interval|[0-9])", "DAYS(a) - DAYS(b), or TIMESTAMPDIFF(16, CHAR(a - b))"),
    # empty string: on Oracle '' IS NULL, on DB2 '' is a real value
    ("= '' alone", "SILENT", r"(=|<>|!=)\s*''", r"is\s+(not\s+)?null", "Oracle: never true. DB2: matches empty strings. Add the IS NULL test"),
    ("NVL(x,'')", "SILENT", r"(nvl|coalesce)\s*\([^()]*,\s*''\s*\)", None, "Oracle returns NULL, DB2 returns ''; compare with IS NULL instead"),
    ("concat ||", "SILENT", r"[|][|]", None, "Oracle skips NULL in ||, DB2 returns NULL: COALESCE(x,'') each nullable part"),
    ("LENGTH", "SILENT", B + r"length\s*\(", None, "LENGTH('') is NULL on Oracle, 0 on DB2"),
]
SKIP_IN_CLOBS = {"concat ||", "LENGTH"}   # far too common inside scripts and BIRT XML to be useful

def q(v):
    """Quote a value for an Oracle string literal."""
    return v.replace("'", "''")

def build():
    parts = []
    for table, key, col in SOURCES:
        clob = (table, col) in CLOBS
        text = f"dbms_lob.substr({col}, 300, 1)" if clob else f"substr({col}, 1, 300)"
        for rid, cls, rx, clear, fix in RULES:
            if clob and rid in SKIP_IN_CLOBS:
                continue
            where = f"regexp_like({col}, '{q(rx)}', 'i')"
            if clear:
                where += f" and not regexp_like({col}, '{q(clear)}', 'i')"
            parts.append(
                f"select '{cls}' cls, '{q(rid)}' rule_id, '{table}.{col}' where_stored, to_char({key}) record_key, "
                f"replace(replace({text}, chr(10), ' '), chr(13), ' ') sql_text, '{q(fix)}' db2_fix "
                f"from {table} where {where}")
    head = ("-- Generated by find_oracle_sql.py (Created by Mohamed Chihaoui)\n"
            "set pagesize 0 linesize 32767 trimspool on feedback off heading off\n"
            "set markup csv on quote off delimiter ~\n")
    body = "\nunion all\n".join(parts)
    return (head + "select cls, rule_id, where_stored, record_key, sql_text, db2_fix from (\n"
            + body + "\n) order by 1, 3, 4;\nexit\n")

if __name__ == "__main__":
    out = Path(__file__).with_name("find_oracle_sql.sql")
    out.write_text(build(), encoding="utf-8", newline="\n")
    print(out, len(SOURCES), "columns x", len(RULES), "rules")
