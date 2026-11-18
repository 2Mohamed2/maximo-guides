select ticketid, class, status, plusgincidentgroup, plusginctype, reportedby, plusgreportedto, plusghazardid, plusgpotenconsq, plusgpotenconsqsevr, plusgactconsq, plusgactconsqsevr, plusgreportable, plusgrecordable, plusginvestreqd
from incident
where ticketid = '1222'
