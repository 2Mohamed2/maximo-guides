select status, plusgeditmocrev, plusgeditmocprelist, plusgeditmocauth, plusgeditmocpostlist, plusgeditmocpssr
from wpeditsetting
where orgid = 'EAGLENA' and status in ('WAPPR', 'APPR', 'INPRG', 'COMP')
order by status
