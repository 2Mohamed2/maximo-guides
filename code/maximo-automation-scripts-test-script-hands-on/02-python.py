# BLOGTEST_BROKEN - REST API script with a deliberate bug (lab: reading an error).
site = request.getQueryParam("site") or "BEDFORD"
service.log("Starting count for site " + site)
total = woCount + 1      # bug: woCount was never defined
responseBody = '{"total": ' + str(total) + '}'
