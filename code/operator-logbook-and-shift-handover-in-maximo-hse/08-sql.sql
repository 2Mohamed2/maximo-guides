select r.orgshftlogentryid, r.plusgshiftlogid, case when s.plusgshiftlogid is null then 'deleted' else s.shiftnum end, e.revcreated
from plusgshlgentryrev r
left join plusgshiftlog s on s.plusgshiftlogid = r.plusgshiftlogid
join plusgshftlogentry e on e.plusgshftlogentryid = r.orgshftlogentryid
where r.orgshftlogentryid in (52, 53)
