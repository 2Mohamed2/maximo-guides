insert into alerts.status (Identifier, Node, Manager, Agent, AlertGroup, AlertKey, Summary, Severity, Type, OwnerUID, FirstOccurrence, LastOccurrence)
  values ('MTR-4200-0105:Last Gasp', 'MTR-4200-0105', 'SMOCLab', 'nco_sql', 'Last Gasp', '4200-JCS-031500', 'Last Gasp on meter MTR-4200-0105', 5, 1, 65534, getdate, getdate);
go
