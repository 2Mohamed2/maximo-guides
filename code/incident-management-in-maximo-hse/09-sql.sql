select wonum, status, convert(varchar(16), changedate, 120), memo
from wostatus
where wonum = '1374' and siteid = 'BEDFORD'
order by changedate
