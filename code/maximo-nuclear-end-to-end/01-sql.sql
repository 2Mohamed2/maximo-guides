-- tech spec actions as Maximo computes with them
select tsid, revisionnum, conditionid, actionid, duration, durationunits, isrepetitive, repetfreq, repetfrequnits, logicalcon
  from plustsaction order by revisionnum, actionid;

-- the LCO clock: entry, due, completion, exit per action
select lconum, actionid, enter, actstart, nextreqdcomp, complete, exitdate, exitlco
  from pluslcoaction where lconum = '1002' order by actionid;

-- the clearance and its tags in application order, with signatures
select c.clearnum, c.status, t.tagnum, t.location, t.appposition, t.resposition, t.status,
       t.applier, t.applierdate, t.appverifier, t.restorer, t.resverifier
  from plusclearance c join pluscltaglink l on l.clearnum = c.clearnum and l.revisionnum = c.revisionnum
                       join plustag t on t.tagnum = l.tagnum
 where c.clearnum = '1002' order by l.appseqnum;

-- allowed positions and the normal line-up per component
select p.location, p.position, p.appivreq, p.resivreq, r.restcond
  from pluslocpos p left join pluslocposrc r on r.location = p.location and r.position = p.position
 where p.location like '2RHR-%' order by p.location, p.position;

-- the condition report's screening data
select ticketid, status, pluscalevel, pluscategory, plusaction, plusopsshiftreview, pluslco, targetfinish
  from plusca where ticketid = '1171';

-- the retest: completion code and the PM's new dates
select w.wonum, w.worktype, w.pmnum, w.pluswocompletioncode, p.lastcompdate, p.nextdate
  from workorder w join pm p on p.pmnum = w.pmnum and p.siteid = w.siteid where w.wonum = '1202';
