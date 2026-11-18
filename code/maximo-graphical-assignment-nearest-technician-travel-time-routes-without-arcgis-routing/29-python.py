"""Generate dbc/gisnt_emres_traveltime_<ver>.dbc from emres_traveltime.py.

Ships automation script GISNTEMRES and its object launch point (SKDEMAVAILRES,
before save on add) as a guarded, re-runnable DBC for DB2, Oracle and SQL Server.
"""
import os
import sys

VER = sys.argv[1] if len(sys.argv) > 1 else "1.0.2"
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = open(os.path.join(HERE, "emres_traveltime.py"), encoding="utf-8").read().replace("\r\n", "\n")
OUT = os.path.join(HERE, "..", "dbc", "gisnt_emres_traveltime_%s.dbc" % VER)
NAME, LP, DESC = "GISNTEMRES", "GISNTEMRES", "Correct travel time on GA emergency recommendations"

def lit(s):
    return "'" + s.replace("'", "''") + "'"

import re

# DBC freeform collapses every whitespace run, even inside string literals, so the
# source is rebuilt from pieces: newline = NL function, runs of 2+ spaces = SP(n).
DIALECT = {
    "db2":       {"cat": " || ", "nl": "CHR(10)",  "sp": "REPEAT(' ', %d)", "head": "CAST(%s AS CLOB)"},
    "oracle":    {"cat": " || ", "nl": "CHR(10)",  "sp": "RPAD(' ', %d)",   "head": "TO_CLOB(%s)"},
    "sqlserver": {"cat": " + ",  "nl": "CHAR(10)", "sp": "SPACE(%d)",       "head": "CAST(%s AS NVARCHAR(MAX))"},
}

def source_expr(src, db):
    d = DIALECT[db]
    parts = []
    for i, line in enumerate(src.split("\n")):
        if i:
            parts.append(d["nl"])
        for tok in re.split(r"( {2,})", line):
            if not tok:
                continue
            if tok.startswith("  ") and tok.strip() == "":
                parts.append(d["sp"] % len(tok))
            else:
                parts.append(lit(tok))
    if db == "oracle":   # keep each literal under Oracle's 4000-char limit and CLOB-typed
        parts = ["TO_CLOB(%s)" % p if p.startswith("'") else p for p in parts]
    else:
        parts[0] = d["head"] % parts[0]
    return d["cat"].join(parts)

now = {"db2": "current timestamp", "oracle": "sysdate", "sqlserver": "getdate()"}
seq = {"db2": "nextval for %s", "oracle": "%s.nextval", "sqlserver": "next value for %s"}
src = {db: source_expr(SRC, db) for db in ("db2", "oracle", "sqlserver")}
dual = {"db2": " from sysibm.sysdummy1", "oracle": " from dual", "sqlserver": ""}

blocks = []
for db in ("db2", "oracle", "sqlserver"):
    blocks.append('      <sql target="%s"><![CDATA[insert into autoscript (autoscript, status, createddate, statusdate, changedate, changeby, '
                  'autoscriptid, hasld, langcode, scriptlanguage, userdefined, loglevel, interface, active, description, version, source) '
                  'select %s, \'Active\', %s, %s, %s, \'MAXADMIN\', %s, 0, \'EN\', \'jython\', 1, \'ERROR\', 0, 1, %s, %s, %s%s]]></sql>'
                  % (db, lit(NAME), now[db], now[db], now[db], seq[db] % "autoscriptseq", lit(DESC), lit(VER), src[db],
                     dual[db] + " where not exists (select 1 from autoscript where autoscript=%s)" % lit(NAME)))
script_sql = "\n".join(blocks)

# Upgrade an older install in place (keeps the launch point and its settings).
upd = []
for db in ("db2", "oracle", "sqlserver"):
    upd.append('      <sql target="%s"><![CDATA[update autoscript set source = %s, version = %s, changedate = %s, '
               'changeby = \'MAXADMIN\' where autoscript = %s]]></sql>' % (db, src[db], lit(VER), now[db], lit(NAME)))
upd_sql = "\n".join(upd)

lp = []
for db in ("db2", "oracle", "sqlserver"):
    lp.append('      <sql target="%s"><![CDATA[insert into scriptlaunchpoint (launchpointname, autoscript, launchpointtype, objectname, objectevent, '
              'active, description, scriptlaunchpointid) select %s, %s, \'OBJECT\', \'SKDEMAVAILRES\', 2, 1, \'Before save on add\', %s%s]]></sql>'
              % (db, lit(LP), lit(NAME), seq[db] % "scriptlaunchpointseq",
                 dual[db] + " where not exists (select 1 from scriptlaunchpoint where launchpointname=%s)" % lit(LP)))
lp_sql = "\n".join(lp)

dbc = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE script SYSTEM "script.dtd">

<!--
  Nearest-technician fix for Graphical Assignment emergency work.

  Scheduler 9.2 (ResourceFinder.getWOandTravelTimeForResoureList and
  SKDAppService.saveSuggestResourceListtoEMWO) stores one shared map of travel
  times under every technician, so every row of "Emergency Work Resource
  Availability" shows the same Travel Time and the list cannot be used to pick
  the nearest technician.

  GISNTEMRES runs before each recommendation row is saved and replaces its
  TRAVELTIME with the road travel time from where that technician really is:
  live GPS (LBSLOCATION, under 30 minutes old), else the work order they are on,
  else their start location; taken from SKDORIGINDESTMATRIX, or asked of the
  routing service configured in Map Manager (SPATIALROUTE) when the pair is
  missing. It also sets DISTANCEKM (road kilometres for the same trip, from the
  routing service) once dbc/gisnt_emres_distance_1.0.0.dbc has added that field.

  Generated from gis-nearest-tech/emres_traveltime.py by gen_dbc.py.
  Guarded: installs, or upgrades an older version in place; does nothing when
  this version is already installed.
-->
<script author="mc" scriptname="gisnt_emres_traveltime_%(ver)s">
  <description>GISNTEMRES - correct travel time and distance on emergency recommendations</description>
  <check tag="INFO" group="scriptrun" key="ScriptNotNeeded" default="GISNTEMRES %(ver)s already installed; skipped." skip_script="true">
    <check_query query="select 1 from autoscript where autoscript='%(name)s' and version='%(ver)s'"/>
  </check>
  <statements>
    <freeform description="upgrade autoscript %(name)s">
%(upd_sql)s
    </freeform>
    <freeform description="autoscript %(name)s">
%(script_sql)s
    </freeform>
    <freeform description="launch point %(lp)s (SKDEMAVAILRES, before save on add)">
%(lp_sql)s
    </freeform>
  </statements>
</script>
""" % {"ver": VER, "name": NAME, "lp": LP, "script_sql": script_sql, "upd_sql": upd_sql, "lp_sql": lp_sql}

open(OUT, "w", encoding="utf-8", newline="\n").write(dbc)
print("wrote", os.path.normpath(OUT), len(dbc), "bytes")
