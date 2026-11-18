select recordkey, class, relatedreckey, relatedrecclass, relatetype
from plusgrelatedrec
where class = 'PLUSGLOGENTRY' and recordkey in ('52', '53')
