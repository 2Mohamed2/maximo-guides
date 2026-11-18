select logbooknum, description, status, owner, convert(varchar(16), startdate, 120), convert(varchar(16), finishdate, 120), calnum, calshiftnum
from plusglogbook
where logbooknum = '1002'
