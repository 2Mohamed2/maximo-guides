"""Find SQL Server-only SQL stored inside a Maximo database (run against the SOURCE SQL Server database).

Created by Mohamed Chihaoui.

Same idea as find_oracle_sql.py, for Maximo on Microsoft SQL Server. SQL Server 2022 has no regular
expressions, so it works in two steps:

  python find_tsql.py extract > extract.sql
  sqlcmd -C -S <host> -U maximo -P <password> -d <database> -y 0 -s "~" -i extract.sql -o extract.txt
  python find_tsql.py classify extract.txt > findings.csv

Classes:
  FAILS   - Db2 11.5 rejects it (tested on Db2 11.5.8)
  SILENT  - Db2 runs it and can return different rows. On SQL Server, Maximo databases normally use a
            case- and accent-insensitive collation (here Latin1_General_CI_AI): 'appr' finds APPR.
            On Db2 the comparison is exact.
Output (classify): class~rule~table.column~record key~first 300 characters~what to do on Db2
"""
import re
import sys

# (table, readable record key as T-SQL, SQL-bearing column)
SOURCES = [
    ("QUERY", "APP+':'+CLAUSENAME", "CLAUSE"),
    ("MAXRELATIONSHIP", "PARENT+'.'+NAME", "WHERECLAUSE"),
    ("CONDITION", "CONDITIONNUM", "EXPRESSION"),
    ("ESCALATION", "ESCALATION", "CONDITION"),
    ("WFCONDITION", "PROCESSNAME+':'+CAST(NODEID AS VARCHAR(10))", "CONDITION"),
    ("WFACTION", "PROCESSNAME+':'+CAST(ACTIONID AS VARCHAR(10))", "CONDITION"),
    ("WFASSIGNMENT", "PROCESSNAME+':'+CAST(NODEID AS VARCHAR(10))+':'+CAST(ASSIGNID AS VARCHAR(10))", "CONDITION"),
    ("KPIMAIN", "KPINAME", "CLAUSE"),
    ("KPIMAIN", "KPINAME", "SELECTSTMT"),
    ("MAXINTOBJECT", "INTOBJECTNAME", "RESTRICTWHERE"),
    ("MAXIFACEEXPORT", "IFACENAME", "EXPORTWHERE"),
    ("OSLCQUERY", "INTOBJECTNAME+':'+CLAUSENAME", "CLAUSE"),
    ("OSLCINTQUERY", "PROVIDERNAME+':'+QUERYNUM", "WHERECLAUSE"),
    ("MAXTABLEDOMAIN", "DOMAINID+':'+OBJECTNAME", "VALIDTNWHERECLAUSE"),
    ("MAXTABLEDOMAIN", "DOMAINID+':'+OBJECTNAME", "LISTWHERECLAUSE"),
    ("MAXDYNAMICDOMLINK", "OBJECTNAME+'.'+ATTRIBUTENAME", "DOMAINWHERE"),
    ("MAXVIEW", "VIEWNAME", "VIEWWHERE"),
    ("MAXVIEW", "VIEWNAME", "VIEWSELECT"),
    ("SCRIPTLAUNCHPOINT", "LAUNCHPOINTNAME", "CONDITION"),
    ("SLA", "SLANUM", "CONDITION"),
    ("REPORTADHOC", "REPORTNAME", "WHERECLAUSE"),
    ("PLUSGSEQOFEVENTS", "TICKETID+':'+NAME", "CONDITION"),
    ("SKDQUERY", "OBJECTNAME+':'+QUERYNAME", "WHERECLAUSE"),
    ("AUTOSCRIPT", "AUTOSCRIPT", "SOURCE"),
    ("REPORTDESIGN", "REPORTNAME", "DESIGN"),
]
LONG = {("AUTOSCRIPT", "SOURCE"), ("REPORTDESIGN", "DESIGN")}   # scripts and BIRT XML: the noisy rules are skipped

W = r"(^|[^a-z0-9_.])"   # word start
RULES = [
    ("TOP n", "FAILS", W + r"top\s*\(?\s*[0-9]", "FETCH FIRST n ROWS ONLY"),
    ("GETDATE / SYSDATETIME", "FAILS", W + r"(getdate|getutcdate|sysdatetime|sysutcdatetime)\s*\(", "CURRENT TIMESTAMP"),
    ("DATEADD", "FAILS", W + r"dateadd\s*\(", "labelled duration: d - 7 DAYS, d + 3 MONTHS"),
    ("DATEDIFF", "FAILS", W + r"datediff\s*\(", "DAYS(b) - DAYS(a), or TIMESTAMPDIFF"),
    ("DATEPART", "FAILS", W + r"datepart\s*\(", "YEAR(d), MONTH(d), DAY(d), HOUR(d)"),
    ("LEN", "FAILS", W + r"len\s*\(", "LENGTH(RTRIM(x)) (LEN ignores trailing blanks)"),
    ("CHARINDEX", "FAILS", W + r"charindex\s*\(", "LOCATE(find, s) or INSTR(s, find)"),
    ("CONVERT", "FAILS", W + r"convert\s*\(", "CAST, VARCHAR_FORMAT(d, 'YYYY-MM-DD')"),
    ("IIF / STRING_AGG / NEWID / EOMONTH / FORMAT", "FAILS", W + r"(iif|string_agg|newid|eomonth|format)\s*\(",
     "CASE, LISTAGG, GENERATE_UNIQUE(), LAST_DAY, VARCHAR_FORMAT"),
    # Maximo's own :&synonymlist&_DOMAIN[VALUE] syntax is not a bracket identifier
    ("[bracket] identifier", "FAILS", r"(^|[^a-z0-9_&'])\[[a-z_][a-z0-9_ ]*\]", "plain or double-quoted identifier"),
    ("dbo. prefix", "FAILS", W + r"dbo\.", "drop the schema prefix (Maximo sets the current schema)"),
    ("NOLOCK hint", "FAILS", r"(with\s*\(\s*nolock|\bnolock\b)", "remove the hint (Db2 Maximo uses currently committed reads)"),
    ("string + string", "FAILS", r"('\s*\+|\+\s*')", "|| or CONCAT(); + on strings is SQL0420N"),
    ("LIKE '[...]' range", "SILENT", r"like\s+n?'[^']*\[[^\]]+\][^']*'", "SQL Server reads [A-C] as a range, Db2 as text: use OR / BETWEEN"),
    # matched on the ORIGINAL text: a literal holding a lowercase letter, compared to a column
    ("lowercase literal compare", "SILENT", r"(?i:=|<>|!=|\bin\s*\(|like)\s*[nN]?'[^']*[a-z][^']*'",
     "SQL Server compares without case or accents, Db2 exactly: match the stored case or wrap with UPPER()"),
]
SKIP_LONG = {"lowercase literal compare", "string + string", "[bracket] identifier"}

def extract():
    """One result set; tables of add-ons that are not installed are skipped (dynamic SQL per table)."""
    parts = []
    for table, key, col in SOURCES:
        q = (f"select '{table}.{col}', cast({key} as nvarchar(200)), "
             f"replace(replace(replace(cast({col} as nvarchar(max)), char(13), ' '), char(10), ' '), '~', '-') "
             f"from dbo.{table.lower()} where {col} is not null").replace("'", "''")
        parts.append(f"if object_id('dbo.{table.lower()}') is not null insert into #f exec('{q}');")
    return ("-- Generated by find_tsql.py (Created by Mohamed Chihaoui)\nset nocount on;\n"
            "create table #f (w nvarchar(100), k nvarchar(200), t nvarchar(max));\n"
            + "\n".join(parts) + "\nselect w, k, t from #f order by w, k;\n")

def classify(path):
    out = []
    for line in open(path, encoding="utf-8", errors="replace"):
        p = line.rstrip("\n").split("~", 2)
        if len(p) < 3:
            continue
        where, key, text = p
        low = text.lower()
        tc = tuple(where.split("."))
        for rid, cls, rx, fix in RULES:
            if tc in LONG and rid in SKIP_LONG:
                continue
            if re.search(rx, text if rid == "lowercase literal compare" else low):
                out.append("~".join([cls, rid, where, key.strip(), text[:300], fix]))
    out.sort()
    print("\n".join(out))

if __name__ == "__main__":
    if sys.argv[1] == "extract":
        sys.stdout.write(extract())
    else:
        classify(sys.argv[2])
