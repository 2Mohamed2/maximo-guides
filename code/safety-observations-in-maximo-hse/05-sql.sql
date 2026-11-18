select ticketid, status, convert(varchar(16), changedate, 120), changeby
from tkstatus
where ticketid in ('1236', '1238')
order by ticketid, changedate
