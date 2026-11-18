select 'Pre-Start', stdactnum, actionby, completed
from plusgmocprelist
where wonum = '1379'
union all select 'Post-Start', stdactnum, actionby, completed
from plusgmocpostlist
where wonum = '1379'
union all select 'Safety review', stdactnum, actionby, completed
from plusgmocrevact
where workorderid = 134067
union all select 'Closure', stdactnum, actionby, completed
from plusgmocclosurelist
where workorderid = 134067
