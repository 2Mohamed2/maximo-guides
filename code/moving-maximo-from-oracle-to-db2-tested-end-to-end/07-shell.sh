python ibm_db2_text_fix.py ibm_platform_diff.csv ibm_db2_text_fix.sql
db2 connect to MAXDB; db2 set schema MAXIMO; db2 -tvf ibm_db2_text_fix.sql
