INSERT INTO applicationauth (groupname, app, optionname, applicationauthid)
SELECT g.varvalue, s.app, s.optionname, NEXT VALUE FOR applicationauthseq
  FROM (SELECT varvalue FROM maxvars WHERE varname = 'ADMINGROUP') g
 CROSS JOIN (SELECT 'PLUSXWO' AS app, 'WMLINEAR' AS optionname
             UNION ALL SELECT 'PLUSXWO', 'LINRPROG'
             UNION ALL SELECT 'PLUSXWO', 'FLTRLASET' /* ... */) s
 WHERE NOT EXISTS (SELECT 1 FROM applicationauth x
                    WHERE x.groupname = g.varvalue AND x.app = s.app
                      AND x.optionname = s.optionname)
