select a.auditnum, s.status, convert(varchar(16), s.changedate, 120)
from plusgauditstatus s
join plusgaudit a on a.plusgauditid = s.plusgauditid
order by a.auditnum, s.changedate
