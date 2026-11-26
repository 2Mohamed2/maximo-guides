#!/bin/bash
# Runs each Oracle construct against DB2 and prints OK / the SQL error code.
. ~/sqllib/db2profile
db2 connect to MAXDB >/dev/null
db2 "create table t_dialect (id int, s varchar(20), d timestamp)" >/dev/null 2>&1
db2 "delete from t_dialect" >/dev/null
db2 "insert into t_dialect values (1,'a',current timestamp),(2,null,current timestamp)" >/dev/null
# the CLP back end is tied to this shell: run db2 here, never inside $( )
t(){ db2 -x "$2" > /tmp/_o 2>&1; code=$(grep -oE "SQL[0-9]+N" /tmp/_o | head -1); printf '%-22s %-8s %s\n' "$1" "${code:-OK}" "$(head -1 /tmp/_o | tr -s ' ' | cut -c1-60)"; }
t "NVL"            "select nvl(s,'x') from t_dialect where id=2"
t "NVL2"           "select nvl2(s,'y','n') from t_dialect where id=2"
t "DECODE"         "select decode(id,1,'one','other') from t_dialect where id=1"
t "SYSDATE"        "select sysdate from sysibm.sysdummy1"
t "FROM DUAL"      "select 1 from dual"
t "ROWNUM"         "select id from t_dialect where rownum <= 1"
t "(+) outer join" "select a.id from t_dialect a, t_dialect b where a.id = b.id(+)"
t "TO_CHAR(date)"  "select to_char(d,'YYYY-MM-DD') from t_dialect where id=1"
t "TO_DATE"        "select to_date('2026-11-26','YYYY-MM-DD') from sysibm.sysdummy1"
t "TRUNC(date)"    "select trunc(d) from t_dialect where id=1"
t "ADD_MONTHS"     "select add_months(d,1) from t_dialect where id=1"
t "MONTHS_BETWEEN" "select months_between(d,d) from t_dialect where id=1"
t "date - number"  "select d - 1 from t_dialect where id=1"
t "INSTR"          "select instr(s,'a') from t_dialect where id=1"
t "MINUS"          "select id from t_dialect minus select id from t_dialect where id=2"
t "CONNECT BY"     "select id from t_dialect start with id=1 connect by prior id = id+1"
t "LISTAGG"        "select listagg(s, ',') within group (order by id) from t_dialect"
t "SUBSTR"         "select substr(s,1,1) from t_dialect where id=1"
t "LENGTH('')"     "select length('') from sysibm.sysdummy1"
t "''=NULL rows"   "select count(*) from t_dialect where s = ''"
t "'' IS NULL"     "select case when '' is null then 'NULL' else 'NOT NULL' end from sysibm.sysdummy1"
t "NULL||'x'"      "select coalesce(s||'x','<null>') from t_dialect where id=2"

t "TO_NUMBER"      "select to_number('42') from sysibm.sysdummy1"
t "REGEXP_LIKE"    "select count(*) from t_dialect where regexp_like(s,'^a')"
t "ROWID"          "select rowid from t_dialect where id=1"
t "CAST VARCHAR2"  "select cast(s as varchar2(5)) from t_dialect where id=1"
t "NUMBER type"    "select cast(id as number(10)) from t_dialect where id=1"
t "LPAD"           "select lpad(id,4,'0') from t_dialect where id=1"
t "SUBSTR(s,-1)"   "select substr('abc',-1) from sysibm.sysdummy1"
t "GREATEST"       "select greatest(1,2) from sysibm.sysdummy1"
t "SYSTIMESTAMP"   "select systimestamp from sysibm.sysdummy1"
t "INTERVAL"       "select d - interval '1' day from t_dialect where id=1"
t "DATE literal"   "select count(*) from t_dialect where d > date '2020-01-01'"
t "TRUNC(sysdate)-7" "select count(*) from t_dialect where d > trunc(sysdate) - 7"
t "NVL(s,'')"      "select count(*) from t_dialect where nvl(s,'') = ''"
t "MOD"            "select mod(7,3) from sysibm.sysdummy1"
t "INSTR 4 args"   "select instr('a,b,c', ',', 1, 2) from sysibm.sysdummy1"
t "TO_CHAR(num)"   "select to_char(1234.5,'9999.99') from sysibm.sysdummy1"
t "FETCH FIRST"    "select id from t_dialect fetch first 1 rows only"
t "WM_CONCAT"      "select wm_concat(s) from t_dialect"
t "SYS_GUID"       "select sys_guid() from sysibm.sysdummy1"
t "USER pseudo"    "select user from sysibm.sysdummy1"
t "date - date"     "select (current timestamp - (current timestamp - 400 days)) from sysibm.sysdummy1"
t "days(d)-days(d)"  "select days(current timestamp) - days(current timestamp - 400 days) from sysibm.sysdummy1"
t "(a,b)=(select)"   "select count(*) from t_dialect where (id, s) = (select id, s from t_dialect where id = 1)"
t "rownum subquery"  "select id from (select id from t_dialect order by d desc) where rownum <= 1"
db2set -all 2>/dev/null | grep -i COMPAT | sed 's/^/registry: /'
db2 get db cfg for MAXDB | grep -iE "varchar2|date_compat|number_compat" | sed 's/^/dbcfg: /'
db2 "drop table t_dialect" >/dev/null
