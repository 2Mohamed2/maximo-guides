insert into autoscript (autoscript, description, status, createddate, statusdate, changedate, changeby,
       autoscriptid, hasld, langcode, scriptlanguage, userdefined, loglevel, interface, active, aitool, version, source)
values ('RUNSQLQUERY', 'Run a read-only SQL SELECT on the Maximo database and return the rows (max 200).',
       'Active', current timestamp, current timestamp, current timestamp, 'MAXADMIN',
       autoscriptseq.nextval, 0, 'EN', 'jython', 1, 'ERROR', 0, 1, 1, '1.0', <script source>);

insert into autoscriptvars (autoscriptvarsid, autoscript, varname, varbindingtype, vartype, description,
       allowoverride, literaldatatype, accessflag)
values (autoscriptvarsseq.nextval, 'RUNSQLQUERY', 'query', 'LITERAL', 'IN',
       'The SQL SELECT statement to run, exactly as the user wrote it. One statement, no semicolon.', 1, 'ALN', 0);

insert into mcptool (name, type, mcpreadonly, title, queryapiasresp, userdefined, mcptoolid, mcpdml)
values ('RUNSQLQUERY', 'AUTOSCRIPT', 1, 'Run SQL query', 0, 1, mcptoolseq.nextval, 0);
