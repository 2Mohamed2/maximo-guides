select wonum, status, convert(varchar(16), changedate, 120), changeby
from wostatus
where wonum in ('1378', '1379')
order by wonum, changedate
