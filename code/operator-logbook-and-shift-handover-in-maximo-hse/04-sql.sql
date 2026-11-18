select recordkey, plusgshftlogentryid, logtype, location, convert(varchar(16), createdate, 120), convert(varchar(16), eventdate, 120), carryover, carryoverstatus, carryoverflag, revcreated, description
from plusgshftlogentry
where recordkey like 'V31-%'
order by recordkey, plusgshftlogentryid
