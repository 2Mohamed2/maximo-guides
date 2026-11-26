select table_name || '.' || column_name from user_tab_columns
 where data_type = 'BLOB' and nullable = 'N'
   and table_name in (select tablename from maxtable);   -- 30 columns in Manage 9.3

python fix_not_null_blobs.py Unlcvt.db2 Unlcvt.fixed.db2 REPORTOUTPUTCNT.CONTENT MAFAPPDATA.APP ...
