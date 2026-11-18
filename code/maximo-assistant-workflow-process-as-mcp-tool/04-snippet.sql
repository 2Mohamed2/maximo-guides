select i.wfid, i.processname, i.active, i.originator, a.assigncode, a.assignstatus, a.description
  from wfinstance i left join wfassignment a on a.wfid = i.wfid
 where i.ownertable = 'WORKORDER' and i.ownerid = 2205;

WFID  PROCESSNAME  ACTIVE  ORIGINATOR  ASSIGNCODE  ASSIGNSTATUS  DESCRIPTION
106   TEST_WF_1    1       MXINTADM    MXINTADM    ACTIVE        TASK 3
