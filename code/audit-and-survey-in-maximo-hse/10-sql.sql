select a.auditnum, l.linenum, l.plusgmaxscore, l.plusgweightfactor, l.linescore
from plusgaudline l
join plusgaudit a on a.plusgauditid = l.plusgauditid
where a.auditnum in ('1004','1005')
order by 1, 2
