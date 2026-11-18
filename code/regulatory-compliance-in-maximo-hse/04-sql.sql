select r.referencenum, r.regulationid, r.plusgregulationid, g.revisionnum, g.status, r.refapp, r.regappliestowo
from plusgworeg r
join plusgregulation g on g.plusgregulationid = r.plusgregulationid
where r.referencenum in ('1382', '1383')
order by r.referencenum, r.regulationid, r.refapp
