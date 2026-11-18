select c.consqnum, c.severity, r.likelihood, r.riskrank, r.riskpriority
from plusgconsq c join plusgrisklist r on r.plusgconsqid = c.plusgconsqid
where c.status = 'ACTIVE'
order by c.displaysequence, r.rowsequence;
