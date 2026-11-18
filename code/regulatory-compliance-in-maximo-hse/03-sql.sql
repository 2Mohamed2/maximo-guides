select 'Asset', assetnum, regulationid, plusgregulationid, wodefault
from plusgassetreg
union all select 'Location', location, regulationid, plusgregulationid, wodefault
from plusglocreg
