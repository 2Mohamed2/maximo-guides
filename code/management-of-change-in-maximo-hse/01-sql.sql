select wonum, woclass, status, plusgmoctype, plusgcategory, plusghighrisk, plusgsafetycrit, reportedby, onbehalfof, location, assetnum, convert(varchar(16), plusgrequireddate, 120), origrecordid, description
from workorder
where wonum in ('1378', '1379')
order by wonum
