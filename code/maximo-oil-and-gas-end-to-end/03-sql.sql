select w.wonum, w.location, w.plusgsafecrielem, w.targcompdate, w.estdur
from workorder w
where w.woclass = 'BYPASS' and w.status = 'INPRG' and w.plusgsafecrielem is not null
order by w.targcompdate;
