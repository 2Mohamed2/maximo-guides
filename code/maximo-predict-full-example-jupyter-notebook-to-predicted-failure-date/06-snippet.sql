select ENTITY_ID, KEY, VALUE_N, VALUE_T, TIMESTAMP
from WSP_MAM.DM_DEVICE_TYPE_NEW_AFMGRP_3_0L
where KEY in ('predicted_time_to_failure', 'predicted_failure_date')
order by ENTITY_ID, TIMESTAMP desc;
