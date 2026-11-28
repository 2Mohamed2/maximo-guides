#!/bin/bash
# Runs SQL Server (T-SQL) constructs that Maximo users write in saved queries against Db2 11.5
# and prints OK / the SQL error code. Created by Mohamed Chihaoui.
. ~/sqllib/db2profile
db2 connect to MAXDB >/dev/null
db2 "create table t_tsql (id int, s varchar(20), d timestamp, n decimal(10,2))" >/dev/null 2>&1
db2 "delete from t_tsql" >/dev/null
db2 "insert into t_tsql values (1,'APPR',current timestamp,10.5),(2,null,current timestamp - 400 days,null),(3,'',current timestamp,0),(4,'B ',current timestamp,1)" >/dev/null
# the CLP back end is tied to this shell: run db2 here, never inside $( )
t(){ db2 -x "$2" > /tmp/_o 2>&1; code=$(grep -oE "SQL[0-9]+N" /tmp/_o | head -1); printf '%-24s %-8s %s\n' "$1" "${code:-OK}" "$(head -1 /tmp/_o | tr -s ' ' | cut -c1-60)"; }
t "TOP n"                "select top 1 id from t_tsql"
t "ISNULL(x,y)"          "select isnull(s,'x') from t_tsql where id=2"
t "GETDATE()"            "select getdate() from sysibm.sysdummy1"
t "GETUTCDATE()"         "select getutcdate() from sysibm.sysdummy1"
t "SYSDATETIME()"        "select sysdatetime() from sysibm.sysdummy1"
t "DATEADD(day,-7,d)"    "select dateadd(day,-7,d) from t_tsql where id=1"
t "DATEDIFF(day,a,b)"    "select datediff(day,d,current timestamp) from t_tsql where id=2"
t "DATEPART(year,d)"     "select datepart(year,d) from t_tsql where id=1"
t "YEAR(d)"              "select year(d) from t_tsql where id=1"
t "string + string"      "select s + 'x' from t_tsql where id=1"
t "CONCAT(a,b)"          "select concat(s,'x') from t_tsql where id=1"
t "LEN(s)"               "select len(s) from t_tsql where id=1"
t "CHARINDEX"            "select charindex('P',s) from t_tsql where id=1"
t "CONVERT(varchar,d,120)" "select convert(varchar(20),d,120) from t_tsql where id=1"
t "CAST AS DATETIME"     "select cast('2026-01-01' as datetime) from sysibm.sysdummy1"
t "CAST AS NVARCHAR"     "select cast(s as nvarchar(10)) from t_tsql where id=1"
t "[bracket] names"      "select [id] from t_tsql"
t "dbo. prefix"          "select count(*) from dbo.t_tsql"
t "WITH (NOLOCK)"        "select count(*) from t_tsql with (nolock)"
t "IIF"                  "select iif(id=1,'a','b') from t_tsql where id=1"
t "STRING_AGG"           "select string_agg(s, ',') from t_tsql"
t "NEWID()"              "select newid() from sysibm.sysdummy1"
t "EOMONTH"              "select eomonth(d) from t_tsql where id=1"
t "FORMAT"               "select format(d,'yyyy-MM-dd') from t_tsql where id=1"
t "LIKE '[A-C]%'"        "select count(*) from t_tsql where s like '[A-C]%'"
t "SELECT no FROM"       "select 1"
t "!= operator"          "select count(*) from t_tsql where id != 1"
t "OFFSET/FETCH"         "select id from t_tsql order by id offset 1 rows fetch next 1 rows only"
t "date - number"        "select count(*) from t_tsql where d > current timestamp - 30"
# silent differences (SQL Server results noted in the post)
t "case: s='appr'"       "select count(*) from t_tsql where s = 'appr'"
t "case: upper"          "select count(*) from t_tsql where upper(s) = 'APPR'"
t "'' = ''"              "select count(*) from t_tsql where s = ''"
t "'' IS NULL"           "select count(*) from t_tsql where s is null"
t "trailing blank ="     "select count(*) from t_tsql where s = 'B'"
t "LIKE trailing blank"  "select count(*) from t_tsql where s like 'B'"
t "NULL concat"          "select coalesce(s || 'x','<null>') from t_tsql where id=2"
t "int / int"            "select 7/2 from sysibm.sysdummy1"
t "LENGTH('B ')"         "select length(s) from t_tsql where id=4"
t "ORDER BY nulls"       "select coalesce(s,'<null>') from t_tsql order by s fetch first 1 rows only"
db2 get db cfg for MAXDB | grep -iE "varchar2|database collating" | sed 's/^/dbcfg: /'
db2 "drop table t_tsql" >/dev/null
