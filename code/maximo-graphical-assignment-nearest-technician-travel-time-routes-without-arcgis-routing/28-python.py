# GISNTEMRES - correct travel time on Graphical Assignment emergency recommendations.
#
# Object launch point: SKDEMAVAILRES, before save, on add.
#
# Why: Scheduler 9.2 (ResourceFinder.getWOandTravelTimeForResoureList +
# SKDAppService.saveSuggestResourceListtoEMWO) stores ONE shared map of travel
# times under every technician, so every recommendation gets the same TRAVELTIME
# and the list cannot be used to pick the nearest technician.
#
# This recomputes TRAVELTIME per technician, from where that technician really is:
#   1. live position (LBSLOCATION, refobject LABOR) if newer than MAXAGE minutes
#   2. else the work order they are working on now (active timer / assignment now)
#   3. else their start location (LABOR.STARTLOCATION -> service address)
# and the road travel time to the emergency work order:
#   a. SKDORIGINDESTMATRIX row FROM -> TO (filled by Scheduler from the routing service)
#   b. else ask the routing service (Map Manager SPATIALROUTE /solve) directly
# and DISTANCEKM, the road distance for the same trip, from the routing service
# (the travel-time matrix stores time only). Needs dbc/gisnt_emres_distance_1.0.0.dbc.
from psdi.server import MXServer
from psdi.mbo import SqlFormat
from java.net import URL, URLEncoder
from java.io import BufferedReader, InputStreamReader
from java.util import Date

MAXAGE = 30  # minutes a GPS fix stays "live"

mx = MXServer.getMXServer()
ui = mx.getSystemUserInfo()

def one(obj, where):
    s = mx.getMboSet(obj, ui)
    s.setWhere(where)
    s.reset()
    m = s.getMbo(0)
    return s, m

def q(v):
    return "'" + str(v).replace("'", "''") + "'"

def lonlat(addressable):
    """WGS84 (lon, lat) of a work order / location, converted by Maximo itself
    (honours the org's COORDINATE setting and the base map's projection)."""
    try:
        c = mx.lookup("SRVAD").getLatLngFromAddressableMbo(addressable)
    except:
        c = None
    if c is None or c.get("lat") is None or c.get("lng") is None:
        return None
    return (float(str(c.get("lng"))), float(str(c.get("lat"))))

def wo_point(wo):
    s, w = one("WOSERVICEADDRESS", "wonum=%s and siteid=%s" % (q(wo.getString("WONUM")), q(wo.getString("SITEID"))))
    if w is None:
        return None, None
    pt = lonlat(wo)
    if pt is None:
        return None, None
    key = ("SA", w.getString("SADDRESSCODE")) if w.getString("SADDRESSCODE") else ("WO", str(wo.getLong("WORKORDERID")))
    return key, pt

def route_url():
    s, m = one("MAPMANAGER", "active=1 and mapprovider='SPATIAL' and spatialroute is not null")
    return m.getString("SPATIALROUTE") if m is not None else None

def num_after(txt, name):
    i = txt.find('"%s"' % name)
    if i < 0:
        return None
    j = txt.find(":", i) + 1
    k = j
    while k < len(txt) and txt[k] in "0123456789.eE- ":
        k += 1
    try:
        return float(txt[j:k])
    except:
        return None

def road_trip(a, b):
    """(hours, km) for the road trip a -> b from the routing service; either may be None."""
    base = route_url()
    if not base:
        return None, None
    stops = '{"features":[{"geometry":{"x":%f,"y":%f}},{"geometry":{"x":%f,"y":%f}}],"spatialReference":{"wkid":4326}}' % (a[0], a[1], b[0], b[1])
    u = URL(base + "/solve?f=json&returnDirections=true&stops=" + URLEncoder.encode(stops, "UTF-8"))
    c = u.openConnection()
    c.setConnectTimeout(5000)
    c.setReadTimeout(20000)
    r = BufferedReader(InputStreamReader(c.getInputStream(), "UTF-8"))
    body = []
    line = r.readLine()
    while line is not None:
        body.append(line)
        line = r.readLine()
    r.close()
    txt = "".join(body)
    mins = num_after(txt, "totalTime")
    km = num_after(txt, "totalLength")   # directionsLengthUnits = kilometres
    return (None if mins is None else mins / 60.0), km

def matrix_hours(frm, to, orgid):
    def col(key, side):
        if key[0] == "SA":
            return "%sserviceaddress=%s" % (side, q(key[1]))
        return "%sworkorder=%s" % (side, key[1])
    s, m = one("SKDORIGINDESTMATRIX", "orgid=%s and %s and %s" % (q(orgid), col(frm, "from"), col(to, "to")))
    return None if m is None else m.getDouble("TRAVELTIME")

def where_is(laborcode, orgid):
    """(origin key or None, (lon, lat) or None, how)"""
    s = mx.getMboSet("LBSLOCATION", ui)
    s.setWhere("refobject='LABOR' and key1=%s" % q(laborcode))
    s.setOrderBy("lastupdate desc")
    s.reset()
    p = s.getMbo(0)
    if p is not None and not p.isNull("LATITUDE") and not p.isNull("LONGITUDE"):
        when = p.getDate("LASTUPDATE")
        if when is not None and (Date().getTime() - when.getTime()) / 60000.0 <= MAXAGE:
            return None, (p.getDouble("LONGITUDE"), p.getDouble("LATITUDE")), "live GPS"
    s, lt = one("LABTRANS", "laborcode=%s and orgid=%s and timerstatus in (select value from synonymdomain where domainid='TIMERSTATUS' and maxvalue='ACTIVE')" % (q(laborcode), q(orgid)))
    cur = None
    if lt is not None:
        s, cur = one("WORKORDER", "wonum=%s and siteid=%s" % (q(lt.getString("REFWO")), q(lt.getString("SITEID"))))
    if cur is None:
        sf = SqlFormat("laborcode=:1 and orgid=:2 and status in (select value from synonymdomain where domainid='ASSTAT' and maxvalue in ('ASSIGNED','STARTED')) and scheduledate <= :3 and finishdate >= :3")
        sf.setObject(1, "ASSIGNMENT", "LABORCODE", laborcode)
        sf.setObject(2, "ASSIGNMENT", "ORGID", orgid)
        sf.setTimestamp(3, mx.getDate())
        s, a = one("ASSIGNMENT", sf.format())
        if a is not None:
            s, cur = one("WORKORDER", "wonum=%s and siteid=%s" % (q(a.getString("WONUM")), q(a.getString("SITEID"))))
    if cur is not None:
        key, pt = wo_point(cur)
        if pt is not None:
            return key, pt, "current WO " + cur.getString("WONUM")
    s, lab = one("LABOR", "laborcode=%s and orgid=%s" % (q(laborcode), q(orgid)))
    if lab is not None and lab.getString("STARTLOCATION"):
        s, loc = one("LOCATIONS", "location=%s and siteid=%s" % (q(lab.getString("STARTLOCATION")), q(lab.getString("STARTLOCSITEID"))))
        if loc is not None and loc.getString("SADDRESSCODE"):
            pt = lonlat(loc)
            if pt is not None:
                return ("SA", loc.getString("SADDRESSCODE")), pt, "start " + lab.getString("STARTLOCATION")
    return None, None, "unknown"

laborcode = mbo.getString("LABORCODE")
if laborcode:
    s, asg = one("ASSIGNMENT", "assignmentid=%d" % mbo.getLong("ASSIGNMENTID"))
    if asg is not None:
        s, wo = one("WORKORDER", "wonum=%s and siteid=%s" % (q(asg.getString("WONUM")), q(asg.getString("SITEID"))))
        to_key, to_pt = wo_point(wo) if wo is not None else (None, None)
        if to_pt is not None:
            orgid = wo.getString("ORGID")
            frm_key, frm_pt, how = where_is(laborcode, orgid)
            hrs = None
            km = None
            if frm_key is not None:
                hrs = matrix_hours(frm_key, to_key, orgid)
            if frm_pt is not None:
                try:
                    r_hrs, km = road_trip(frm_pt, to_pt)
                except:
                    r_hrs, km = None, None
                if hrs is None:
                    hrs = r_hrs
            if hrs is not None:
                mbo.setValue("TRAVELTIME", hrs, 11L)
            if km is not None and mbo.getThisMboSet().getMboSetInfo().getAttribute("DISTANCEKM") is not None:
                mbo.setValue("DISTANCEKM", round(km, 2), 11L)
            service.log("GISNTEMRES %s -> WO %s: %s h, %s km (%s)" % (laborcode, wo.getString("WONUM"), hrs, km, how))
