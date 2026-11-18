select wonum, woclass, status, description, origrecordid, origrecordclass, plusgmoctype
from workorder
where wonum in ('1325','1326','1327','1328')
order by wonum;
