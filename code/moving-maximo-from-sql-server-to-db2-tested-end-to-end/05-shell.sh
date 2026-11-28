python diff_ibm_platform_rows.py <SMP>/maximo/tools/maximo/en/maxdemo.sqs <SMP>/maximo/tools/maximo/en/maxdemo.db2 demo.csv
python diff_ibm_targeted_dbc.py <SMP>/maximo sqlserver scripts.csv      # run where the add-ons are unpacked
python ibm_db2_text_fix.py all.csv ibm_db2_text_fix.sql                     # all.csv = demo.csv + scripts.csv
db2 connect to MAXDB; db2 set schema MAXIMO; db2 -tvf ibm_db2_text_fix.sql
