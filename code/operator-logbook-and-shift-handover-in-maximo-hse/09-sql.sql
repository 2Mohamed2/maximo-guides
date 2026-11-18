select s.shiftnum, h.status, convert(varchar(16), h.changedate, 120), h.changeby
from plusgshlogstatus h
join plusgshiftlog s on s.plusgshiftlogid = h.plusgshiftlogid
where s.shiftnum like 'V31-%'
order by h.changedate
