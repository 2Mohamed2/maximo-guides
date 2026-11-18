select r.recordkey, r.class, r.relatedreckey, r.relatedrecclass, w.status, w.description
from plusgrelatedrec r
join workorder w on w.wonum = r.relatedreckey
where r.class = 'PLUSGAUDIT'
