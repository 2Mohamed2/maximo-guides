select h.hazardid, p.precautionid, hp.plusgpreconfirm, convert(varchar(16), hp.plusgpreconfirmdate, 120) from plusghazriskprec hp join plusghazrisk hr on hr.plusghazriskid=hp.plusghazriskid
 join hazard h on h.hazarduid=hr.hazarduid join precaution p on p.precautionuid=hp.precautionuid where hr.plusgriskassessid=101 order by 1,2
