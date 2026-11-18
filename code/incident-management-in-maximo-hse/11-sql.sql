select l.ticketid, s.solution, s.status, s.plusgislesslearned, s.description
from plusgsolutionlst l
join solution s on s.solution = l.solution
where l.ticketid = '1129'
