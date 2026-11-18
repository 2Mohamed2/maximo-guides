-- the position tree of the model (Lab 4)
select b.lcn, i.name as builditem, b.position
from plusacmbuild b join plusacmbuilditem i on i.plusacmbuilditemid = b.builditemid
join plusacmmodel m on m.plusacmmodelid = b.modelid
where m.model = 'RU20' order by b.lcn;

-- labels and approved parts per build item (Lab 3)
select i.name, l.labelsystem, l.label, c.part
from plusacmbuilditem i join plusacmmodel m on m.plusacmmodelid = i.modelid
left join plusacmlabel l on l.builditemid = i.plusacmbuilditemid
left join plusacmxcat x on x.builditemid = i.plusacmbuilditemid
left join plusacacat c on c.plusacacatid = x.catid
where m.model = 'RU20';

-- the real unit (Lab 6, Lab 10)
select assetnum, parent, serialnum, status from asset where assetnum like 'RU%' order by assetnum;

-- BDI validations of the unit (Lab 7 to Lab 11)
select assetnum, status, createddate, enddate, timetaken, servername
from plusaantran where topassetnum = 'RU20-001' order by plusaantranid;
