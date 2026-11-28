select d.manufacturer, v.manufacturervar, count(*)
  from deployedasset d join dpacomputer c on c.nodeid = d.nodeid
  join dpammanuvariant v on d.manufacturer = v.manufacturervar
 where d.manufacturer collate Latin1_General_BIN <> v.manufacturervar collate Latin1_General_BIN
 group by d.manufacturer, v.manufacturervar;
-- Sun_microsystems | Sun_Microsystems | 2
