select r.riskassessnum, h.hazardid, c.consqnum, hr.likelihood, l.riskrank, l.riskpriority, hr.mitlikelihood, m.riskrank as mitrank, m.riskpriority as mitprio, hr.alarp
 from plusghazrisk hr join plusgriskassess r on r.plusgriskassessid=hr.plusgriskassessid join hazard h on h.hazarduid=hr.hazarduid
 left join plusgconsq c on c.plusgconsqid=hr.plusgconsqid
 left join plusgrisklist l on l.plusgconsqid=hr.plusgconsqid and l.likelihood=hr.likelihood
 left join plusgrisklist m on m.plusgconsqid=hr.plusgconsqid and m.likelihood=hr.mitlikelihood
 where r.riskassessnum in ('1005','1006') order by r.riskassessnum, l.riskpriority, h.hazardid
