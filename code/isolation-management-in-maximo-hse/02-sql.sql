select p.permitworknum, p.status, o.applyseq,
       coalesce(o.location, o.devicedescription) as point,
       o.requiredstate, o.locknumber, o.isocomplete, o.deisocomplete
from plusgpermitwork p
join plusgptwlcktgop o on o.plusgpermitworkid = p.plusgpermitworkid
where p.ptwclass = 'ISOLATION'
  and p.status in ('ISOLATION INPRG', 'ISOLATION COMP', 'ISOLATION PENDREMOVE')
order by p.permitworknum, o.applyseq;
