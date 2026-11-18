select a.auditnum, a.status, a.description, g.regulationid, g.revisionnum
from plusgaudit a
join plusgregulation g on g.plusgregulationid = a.plusgregulationid
order by a.auditnum
