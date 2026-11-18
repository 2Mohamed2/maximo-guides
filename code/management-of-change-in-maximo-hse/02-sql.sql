select recordkey, class, relatedreckey, relatedrecclass, relatetype
from relatedrecord
where recordkey in ('1378', '1379')
order by recordkey
