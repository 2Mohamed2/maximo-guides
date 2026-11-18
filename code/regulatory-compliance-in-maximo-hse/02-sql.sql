select g.regulationid, g.revisionnum, s.status, convert(varchar(16), s.changedate, 120), s.changeby, s.memo
from plusgregstat s
join plusgregulation g on g.plusgregulationid = s.plusgregulationid
where g.regulationid in ('OSHA-CS', 'OSHA-LO')
order by s.changedate
