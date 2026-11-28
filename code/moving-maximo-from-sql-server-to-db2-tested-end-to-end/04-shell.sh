L=<SMP>/maximo/applications/maximo/lib
export SRC_URL='jdbc:sqlserver://<host>:1433;databaseName=MAXDB;encrypt=false' SRC_USER=maximo SRC_PASS=... SRC_SCHEMA=dbo
export TGT_URL='jdbc:db2://<db2-host>:50000/MAXDB' TGT_USER=maximo TGT_PASS=... TGT_SCHEMA=MAXIMO
java -cp $L/sqljdbc.jar:$L/db2jcc.jar CvtTool.java blobs   blobs.csv
java -cp $L/sqljdbc.jar:$L/db2jcc.jar CvtTool.java restore restore.csv
java -cp $L/sqljdbc.jar:$L/db2jcc.jar CvtTool.java counts  counts.csv
java -cp $L/sqljdbc.jar:$L/db2jcc.jar CvtTool.java empties empties.csv
