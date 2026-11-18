select findnum, sequence, questionnum, plusgfindcat, safetycrit, regulationid, owner, workorderid, reauditreq, convert(varchar(10), reauditreqdate, 120), description
from plusgaudfind
where plusgauditid = 2
order by findnum
