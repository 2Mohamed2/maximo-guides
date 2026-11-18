select w.wonum, w.risk, r.riskassessnum, w.plusgriskasscat from workorder w left join plusgriskassess r on r.plusgriskassessid=w.plusgriskassessid where w.workorderid=134058
