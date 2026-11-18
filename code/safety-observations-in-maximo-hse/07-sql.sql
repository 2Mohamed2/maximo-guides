select plusgsftyobstype, class, status, count(*)
from ticket
where plusgincidentgroup = 'OBSERVATION' and siteid = 'BEDFORD' group by plusgsftyobstype, class, status
