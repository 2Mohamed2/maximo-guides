select domainid, value, description
from synonymdomain
where domainid in ('PLUSGINCIDENTGROUP', 'PLUSGINCSFTYTYPE') and value in ('OBSERVATION', 'HAZARD_REPORT', 'INTERVENTION', 'UNSAFE_ACT', 'UNSAFE_WORK_CONDITIONS')
union all select domainid, value, description
from synonymdomain
where domainid = 'PLUSGINCIDENTTYPE'
order by 1, 2
