select s.shiftnum, h.personid, h.reviewed, convert(varchar(16), h.signoffdate, 120)
from plusgshftlghdovrev h
join plusgshiftlog s on s.plusgshiftlogid = h.plusgshiftlogid
where s.shiftnum like 'V31-%'
