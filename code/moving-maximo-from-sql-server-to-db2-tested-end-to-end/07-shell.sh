python dual_run.py --src sqlserver --ora-shell 'ssh sqlhost bash -s' --sqlcmd /opt/mssql-tools18/bin/sqlcmd \
       '--ss-conn=-S <host> -U maximo -P <password> -d MAXDB' \
       --db2-shell 'ssh db2inst1@db2-host bash -s' --rewrites db2_rewrites_sqlserver.csv --out dual_run.csv
