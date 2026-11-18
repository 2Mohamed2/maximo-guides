select locknum, type, status, inuse from plusgmasterlockbox order by locknum;

select locknum, inuse, changedate, changeby
from plusglockdetailinuse
where locknum = 'LK-0701'
order by changedate;
