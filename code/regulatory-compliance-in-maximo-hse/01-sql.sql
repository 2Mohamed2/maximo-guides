select plusgregulationid, regulationid, revisionnum, status, orgid, siteid, appliesto, type, num, subsection, techauthid, convert(varchar(10), validfrom, 120), revisionby, revisioncom
from plusgregulation
where regulationid in ('OSHA-CS', 'OSHA-LO')
order by regulationid, revisionnum
