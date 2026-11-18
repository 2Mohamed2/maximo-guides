select status, convert(varchar(16), changedate, 120), changeby, memo
from tkstatus
where ticketid = '1222' and class in ('DEFECT','INCIDENT')
order by changedate
