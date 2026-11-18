select c.trainingnum, c.isrequired, p.person, p.iscomplete
from plusgmoccourse c
join plusgmoccosper p on p.wonum = c.wonum and p.trainingnum = c.trainingnum
where c.wonum = '1379'
order by p.person
