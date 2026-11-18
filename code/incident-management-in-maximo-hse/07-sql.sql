select recordkey, class, relatedreckey, relatedrecclass, relatetype
from relatedrecord
where recordkey in ('1222', '1129')
order by recordkey, relatedreckey
