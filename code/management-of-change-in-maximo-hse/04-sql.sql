select 'Reviewer', reviewer, reviewed, convert(varchar(16), signoffdate, 120), comments
from plusgmocrvlst
where wonum = '1379'
union all select 'Approver', approver, approved, convert(varchar(16), signoffdate, 120), comments
from plusgmocapprlist
where wonum = '1379'
union all select 'Authorizer', authorizer, authorized, convert(varchar(16), signoffdate, 120), comments
from plusgmocauthlist
where wonum = '1379'
