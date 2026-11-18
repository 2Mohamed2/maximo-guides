-- As-found failure rate per data sheet template, completed work only
select d.dsplannum, count(*) as sheets,
       sum(case when d.asfoundcalstatus = 'FAIL' then 1 else 0 end) as asfound_fail
from pluscwods d
join workorder w on w.wonum = d.wonum and w.siteid = d.siteid
where w.status in ('COMP','CLOSE') and w.siteid = 'BEDFORD'
group by d.dsplannum;
-- lab result: DS-0300 1 / 1, DS-4101 3 / 1, DS-4102 2 / 0

-- Calibration PMs due in the next 180 days
select p.pmnum, p.assetnum, p.location, p.nextdate
from pm p
where p.status = 'ACTIVE' and p.siteid = 'BEDFORD'
  and p.worktype in (select worktype from worktype where type = 'CAL' and orgid = 'EAGLENA')
  and p.nextdate <= dateadd(day, 180, getdate())
order by p.nextdate;

-- Reverse traceability with the sheet results: where was STD-0300 used?
select t.rotassetnum as standard, t.transdate, coalesce(w.parent, w.wonum) as wo,
       d.assetnum, d.dsplannum, d.asfoundcalstatus, d.asleftcalstatus
from tooltrans t
join workorder w on w.wonum = t.refwo and w.siteid = t.siteid
join pluscwods d on d.wonum = coalesce(w.parent, w.wonum) and d.siteid = w.siteid
where t.rotassetnum = 'STD-0300'
order by t.transdate;
