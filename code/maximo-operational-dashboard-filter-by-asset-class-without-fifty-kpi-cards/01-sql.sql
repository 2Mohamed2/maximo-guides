status not in (select value from synonymdomain
               where domainid='LOCASSETSTATUS' and maxvalue='DECOMMISSIONED')
and classstructureid in (select classstructureid from classancestor
                         where ancestorclassid='PUMP')
