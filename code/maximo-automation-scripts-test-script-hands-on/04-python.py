# BLOGTEST_WOINIT - object launch point, WORKORDER, Initialize Value.
# Gives every NEW work order a default priority of 3.
# The Initialize event also fires when an existing record is loaded,
# so the script only acts on records that are being added.
if mbo.toBeAdded():
    mbo.setValue("WOPRIORITY", 3)
    service.log("New work order at site " + mbo.getString("SITEID") + ": default priority 3 set")
else:
    service.log("Existing work order " + mbo.getString("WONUM") + ": nothing to do")
