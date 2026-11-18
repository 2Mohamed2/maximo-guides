# CONTRACTOR_COMPLETE: Maximo REST endpoint POST /maximo/api/script/contractor_complete
# Called only by API Connect. Body: {"wonum": "...", "completedAt": "...", "note": "..."}
# Header x-contractor-vendor: set by the gateway from the caller's consumer organization.
# Implicit variables (script with no launch point, called over REST): request, requestBody, responseBody, userInfo
from psdi.server import MXServer
from psdi.mbo import SqlFormat
from psdi.util import MXException
from com.ibm.json.java import JSONObject
from java.util.regex import Pattern  # Maximo's Jython has no Python standard library

def obj(d):
    o = JSONObject()
    for k, v in d.items():
        o.put(k, obj(v) if isinstance(v, dict) else v)
    return o

def reply(d):
    global responseBody
    responseBody = obj(d).serialize()

def error(code, message):
    reply({"Error": {"reasonCode": code, "message": message}})

vendor = request.getHeader("x-contractor-vendor") or ""
body = JSONObject.parse(requestBody or "{}")
wonum = body.get("wonum") or ""
note = (body.get("note") or "")[:2000]
completedAt = (body.get("completedAt") or "")[:30]

mx = MXServer.getMXServer()
woSet = mx.getMboSet("WORKORDER", userInfo)
try:
    if not woSet.getProfile().getAppOptionAuth("CONTRWO", "COMPLETE", None):
        error("FORBIDDEN", "User " + userInfo.getUserName() + " lacks CONTRWO COMPLETE")
    elif not Pattern.matches("[A-Z0-9]{1,12}", vendor) or not Pattern.matches("[A-Z0-9-]{1,25}", wonum):
        error("BADINPUT", "Missing or invalid vendor or work order number")
    else:
        # Bind variables, never string concatenation: the vendor check is part of the query
        sf = SqlFormat(userInfo, "wonum = :1 and vendor = :2 and istask = 0")
        sf.setObject(1, "WORKORDER", "WONUM", wonum)
        sf.setObject(2, "WORKORDER", "VENDOR", vendor)
        woSet.setWhere(sf.format())
        wo = woSet.moveFirst()
        if wo is None:
            error("NOTFOUND", "Not found")
        else:
            try:
                # The status memo holds 50 characters, so the contractor's note goes into a work log entry
                wo.changeStatus("COMP", mx.getDate(), ("Completed by contractor " + vendor)[:50])
                if note or completedAt:
                    log = wo.getMboSet("WORKLOG").add()
                    log.setValue("LOGTYPE", "CLIENTNOTE")
                    log.setValue("DESCRIPTION", ("Contractor " + vendor + " completion report")[:100])
                    log.setValue("DESCRIPTION_LONGDESCRIPTION", "Completed at (contractor time): " + (completedAt or "not given") + "\n" + note)
                woSet.save()
                reply({"number": wonum, "state": "done", "maximoStatus": wo.getString("STATUS")})
            except MXException, e:
                error("NOTALLOWED", e.getMessage())
finally:
    woSet.close()
