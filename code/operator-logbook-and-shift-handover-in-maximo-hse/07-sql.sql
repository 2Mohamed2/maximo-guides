select s.shiftnum, r.orgshftlogentryid, r.personid1, r.personid2, r.reviewed, r.carryover, r.comments
from plusgshlgentryrev r
join plusgshiftlog s on s.plusgshiftlogid = r.plusgshiftlogid
where s.shiftnum like 'V31-%'
