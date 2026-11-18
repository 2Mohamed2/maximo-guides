select wonum, woclass, status, plusgactiontype, actcategory, plusgactionprior, origrecordid, origrecordclass, plusgactionsumm
from workorder
where woclass = 'ACTTRACK' and origrecordid in ('1236', '1238')
order by wonum
