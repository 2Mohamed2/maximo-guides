select ticketid, class, status, plusgincidentgroup, plusgsftyobstype, plusginctype, plusgisdefect, plusxisdefect, reportedby, affectedperson, owner, assetnum, location, plusgactiontaken, description
from ticket
where ticketid in ('1236', '1238')
order by ticketid
