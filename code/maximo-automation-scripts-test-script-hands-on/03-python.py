# BLOGTEST_WOPRIORITY - attribute launch point, WORKORDER.WOPRIORITY, Validate.
# Rule: emergency work (work type EM) must have priority 1 or 2.
# During Validate, mbo already holds the new value the user typed.
wonum = mbo.getString("WONUM")
worktype = mbo.getString("WORKTYPE")
priority = mbo.getString("WOPRIORITY")
service.log("Validating WO " + wonum + ": work type=" + worktype + ", new priority=" + priority)
if worktype == "EM" and (mbo.isNull("WOPRIORITY") or mbo.getInt("WOPRIORITY") > 2):
    service.log("Rule broken: EM work needs priority 1 or 2")
    service.error("configure", "BlankMsg", ["Emergency (EM) work orders need priority 1 or 2."])
service.log("Rule passed")
