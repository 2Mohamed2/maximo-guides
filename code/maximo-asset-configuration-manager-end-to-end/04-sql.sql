-- the position tree of a model (Lab 4)
select b.lcn, b.indenture, b.indicator, i.name as builditem, b.position, b.label
from plusacmbuild b join plusacmbuilditem i on i.plusacmbuilditemid = b.builditemid
join plusacmmodel m on m.plusacmmodelid = b.modelid
where m.model = 'TP70' order by b.lcn;

-- approved parts per build item (Lab 3)
select i.name, c.part, x.isdefault
from plusacmbuilditem i join plusacmxcat x on x.builditemid = i.plusacmbuilditemid
join plusacacat c on c.plusacacatid = x.catid;

-- configuration and revision gates (Lab 5)
select variation, abstract, status from plusacmconfig;
select revision, draft, activedate from plusacmrevision;

-- the real structure (Labs 6-10)
select assetnum, parent, serialnum, status from asset
where assetnum like 'TP%' or assetnum like 'SPR-%' order by assetnum;

-- every BDI validation (Lab 7)
select assetnum, status, startdate, enddate, timetaken, servername
from plusaantran order by plusaantranid;
