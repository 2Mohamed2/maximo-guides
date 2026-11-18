select p.personid, p.personrole, p.followupreqd, p.followupaction, i.injorillid, i.injorilltype, i.injorillbodypart, i.poisoning, o.outcome, o.injorilldays, o.mostserious
from plusgincperson p
join plusginjorill i on i.plusgincpersonid = p.plusgincpersonid
join plusgoutcome o on o.plusgincpersonid = p.plusgincpersonid
where p.ticketid = '1222'
