select shiftnum, description, status, logbooknum, orgshiftnum, convert(varchar(16), startdate, 120), convert(varchar(16), finishdate, 120), period, supervisor, plantmode
from plusgshiftlog
where shiftnum like 'V31-%'
order by startdate
