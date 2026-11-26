export SRC_URL=jdbc:oracle:thin:@//<oracle-host>:1521/<service> SRC_USER=maximo SRC_PASS=... SRC_SCHEMA=MAXIMO
export TGT_URL='jdbc:db2://<db2-host>:50000/MAXDB' TGT_USER=maximo TGT_PASS=... TGT_SCHEMA=MAXIMO
L=<SMP>/maximo/applications/maximo/lib
java -cp $L/oraclethin.jar:$L/db2jcc.jar CvtTool.java blobs blobs.csv
