select a.permitworknum, b.permitworknum as shares_with,
       coalesce(x.location, x.devicedescription) as point
from plusgptwlcktgop x
join plusgpermitwork a on a.plusgpermitworkid = x.plusgpermitworkid
join plusgptwlcktgop y on (y.location = x.location or y.devicedescription = x.devicedescription)
                      and y.plusgpermitworkid <> x.plusgpermitworkid
join plusgpermitwork b on b.plusgpermitworkid = y.plusgpermitworkid
where a.permitworknum = '1005'
order by x.applyseq;
