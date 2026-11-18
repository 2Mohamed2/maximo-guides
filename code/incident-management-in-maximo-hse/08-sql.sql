select wonum, woclass, status, plusgactiontype, actcategory, plusgactionprior, origrecordclass, origrecordid, description
from workorder
where origrecordid = '1129'
order by wonum
