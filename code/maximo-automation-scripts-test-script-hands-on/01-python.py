# BLOGTEST_WOSUMMARY - REST API script (no launch point), read-only.
# Call: GET /maximo/api/script/BLOGTEST_WOSUMMARY?site=BEDFORD&status=APPR
from psdi.server import MXServer
from psdi.mbo import SqlFormat
from com.ibm.json.java import JSONObject, JSONArray
site = request.getQueryParam("site") or "BEDFORD"
status = request.getQueryParam("status") or "APPR"
service.log("Request received: site=" + site + ", status=" + status)
woSet = MXServer.getMXServer().getMboSet("WORKORDER", request.getUserInfo())
try:
    sql = SqlFormat(request.getUserInfo(), "siteid = :1 and status = :2 and istask = 0")
    sql.setObject(1, "WORKORDER", "SITEID", site)
    sql.setObject(2, "WORKORDER", "STATUS", status)
    woSet.setWhere(sql.format())
    woSet.setOrderBy("wonum")
    total = woSet.count()
    service.log("Matching work orders: " + str(total))
    sample = JSONArray()
    wo = woSet.moveFirst()
    while wo is not None and sample.size() < 3:
        row = JSONObject()
        row.put("wonum", wo.getString("WONUM"))
        row.put("description", wo.getString("DESCRIPTION"))
        row.put("priority", wo.getString("WOPRIORITY"))
        sample.add(row)
        wo = woSet.moveNext()
finally:
    woSet.close()
result = JSONObject()
result.put("site", site)
result.put("status", status)
result.put("count", total)
result.put("firstThree", sample)
responseBody = result.serialize(True)
