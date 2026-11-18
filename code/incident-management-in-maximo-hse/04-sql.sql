select sequencenumber, convert(varchar(16), eventdatetime, 120), witness, description
from plusgseqofevents
where ticketid = '1129'
order by sequencenumber
