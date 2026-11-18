update wfprocess
   set description = 'Start the review workflow on a work order: creates a review task for the person who starts it.'
 where processname = 'TEST_WF_1';

insert into mcptool (name, type, mcpreadonly, title, queryapiasresp, userdefined, mcptoolid, mcpdml)
values ('TEST_WF_1', 'WFPROCESS', 0, 'Start work order review', 0, 1, mcptoolseq.nextval, 1);
