-- Typical customer-written saved queries on a SQL Server Maximo (Work Order Tracking).
-- Seeded into the SOURCE before conversion so they travel through Unlcvt like real ones.
-- Created by Mohamed Chihaoui.
set nocount on;
delete from dbo.query where app = 'WOTRACK' and clausename like 'SSQ_%';
insert into dbo.query (app, clausename, owner, description, clause, ispublic, queryid, langcode, isuserlist)
select 'WOTRACK', c, 'MAXADMIN', d, w, 1, next value for queryseq, 'EN', 0 from (values
 ('SSQ_OVERDUE7', 'Approved or in progress, 7+ days past target',
  'woclass = ''WORKORDER'' and status in (''APPR'',''INPRG'') and targcompdate < dateadd(day, -7, getdate())'),
 ('SSQ_TOP10_WAPPR', 'First 10 waiting for approval',
  'woclass = ''WORKORDER'' and workorderid in (select top 10 workorderid from workorder where status = ''WAPPR'')'),
 ('SSQ_LAST30', 'Reported in the last 30 days',
  'woclass = ''WORKORDER'' and datediff(day, reportdate, getdate()) < 30'),
 ('SSQ_LONG_DESC', 'Description longer than 40 characters',
  'woclass = ''WORKORDER'' and len(description) > 40'),
 ('SSQ_PUMP_TEXT', 'Pump work by description or location',
  'woclass = ''WORKORDER'' and upper(description + '' '' + location) like ''%PUMP%'''),
 ('SSQ_WAITING_LOWER', 'Waiting for approval (typed in lower case)',
  'woclass = ''WORKORDER'' and status = ''wappr'''),
 ('SSQ_BR_RANGE', 'Bedford buildings 100 to 400',
  'woclass = ''WORKORDER'' and location like ''BR[1-4]%'''),
 ('SSQ_NO_LEAD', 'No lead (written for both databases)',
  'woclass = ''WORKORDER'' and (lead is null or lead = '''')')
) v(c, d, w);
select clausename, clause from dbo.query where app = 'WOTRACK' and clausename like 'SSQ_%' order by 1;
