# maximo.properties -> the SQL Server source
mxe.db.driver=com.microsoft.sqlserver.jdbc.SQLServerDriver
mxe.db.url=jdbc:sqlserver://<host>:1433;databaseName=MAXDB;encrypt=false
mxe.db.schemaowner=dbo

cd <SMP>/maximo/tools/maximo/internal
./unlcvt.sh -x3
# BMXAA6818I - Unlcvt started for schema dbo, connected to database jdbc:sqlserver://...
# BMXAA6820I - Unlcvt completed without errors.
