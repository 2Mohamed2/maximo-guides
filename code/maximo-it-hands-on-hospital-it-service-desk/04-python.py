existing = open_incident_for(alert)          # same CI + title, from an alert, not resolved
if existing:
    mx.worklog("INCIDENT", existing["ticketid"], "Alert fired again: " + alert["title"], alert["detail"])
else:
    mx.create("cduiincident", {
        "description": alert["title"], "description_longdescription": alert["detail"],
        "siteid": "BEDFORD", "cinum": alert["entity"]["cmdbId"],
        "internalpriority": {"critical": 1, "major": 2, "minor": 3}[alert["severity"]],
        "origfromalert": True, "ownergroup": "TIER1"})
