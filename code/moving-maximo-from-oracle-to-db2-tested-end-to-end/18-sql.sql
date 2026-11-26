-- Typical customer-written saved queries on an Oracle Maximo (Work Order Tracking).
-- Seeded into the SOURCE before conversion so they travel through Unlcvt like real ones.
-- Created by Mohamed Chihaoui.
set define off feedback on
delete from query where app = 'WOTRACK' and clausename like 'CVT_%';
insert into query (app, clausename, owner, description, clause, ispublic, queryid, langcode, isuserlist, rowstamp)
select 'WOTRACK', c, 'MAXADMIN', d, w, 1, queryseq.nextval, 'EN', 0, '0' from (
  select 'CVT_OVERDUE7' c, 'Approved or in progress, 7+ days past target' d,
         'woclass = ''WORKORDER'' and status in (''APPR'',''INPRG'') and targcompdate < sysdate - 7' w from dual union all
  select 'CVT_NOCREW_SAFE', 'No crew assigned (written for both databases)',
         'woclass = ''WORKORDER'' and (crewid is null or crewid = '''')' from dual union all
  select 'CVT_TOP10_WAPPR', 'First 10 waiting for approval',
         'woclass = ''WORKORDER'' and status = ''WAPPR'' and rownum <= 10' from dual union all
  select 'CVT_LAST30', 'Reported in the last 30 days',
         'woclass = ''WORKORDER'' and reportdate > systimestamp - interval ''30'' day' from dual union all
  select 'CVT_UNDER_11430', 'Work on asset 11430 and everything below it',
         'assetnum in (select assetnum from asset where siteid = ''BEDFORD'' start with assetnum = ''11430'' connect by prior assetnum = parent and prior siteid = siteid)' from dual union all
  select 'CVT_NOCREW_NVL', 'No crew assigned (NVL style)',
         'woclass = ''WORKORDER'' and nvl(crewid, '''') = ''''' from dual union all
  select 'CVT_PUMP_TEXT', 'Pump work by description or location',
         'woclass = ''WORKORDER'' and upper(description || '' '' || location) like ''%PUMP%''' from dual union all
  select 'CVT_BLANK_LEAD', 'Lead left blank',
         'woclass = ''WORKORDER'' and lead = ''''' from dual
);
commit;
select clausename, clause from query where app = 'WOTRACK' and clausename like 'CVT_%' order by 1;
exit
