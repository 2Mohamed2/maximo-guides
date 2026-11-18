select inceventid, plusgincidentgroup, plusginctype, isprimary, status, description
from plusgincevent
where ticketid = '1222'
order by inceventid
