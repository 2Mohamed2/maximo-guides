select ticketid, class, status, plusgincidentgroup, plusginctype, plusgsftyobstype, plusgriskassessid, origrecordid, origrecordclass
from ticket
where origrecordid = '1236' and class = 'INVESTIGATION'
