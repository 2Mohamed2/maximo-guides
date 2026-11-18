select s.shiftnum, t.personid, t.role
from plusgshiftteam t
join plusgshiftlog s on s.plusgshiftlogid = t.shiftlogid
where s.shiftnum like 'V31-%'
