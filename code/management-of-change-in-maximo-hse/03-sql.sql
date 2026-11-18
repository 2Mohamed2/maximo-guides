select r.riskassessnum, r.status, r.location, h.hazardid
from workorder w
join plusgriskassess r on r.plusgriskassessid = w.plusgriskassessid
join plusghazrisk z on z.plusgriskassessid = r.plusgriskassessid
join hazard h on h.hazarduid = z.hazarduid
where w.wonum = '1379'
